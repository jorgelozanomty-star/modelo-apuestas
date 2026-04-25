"""
pages/backtest_page.py
Página 4 — Backtest
Valida el modelo con datos históricos reales.
"""
import streamlit as st
import pandas as pd
from datetime import date

from data.session  import init, get_data_master, get_fixtures
from data.leagues  import LEAGUES, LEAGUE_NAMES
from backtest      import ejecutar_backtest, csv_to_df, _resultado_real
from data.profile  import build_team_profile, calc_lambdas
from core.poisson  import calc_all_markets
from ui.styles     import inject_css


def _calibracion_backtest(df, dm, league):
    '''Evalúa calibración del modelo sin momios: predicciones vs resultados reales.'''
    historial = []
    correcto = 0
    total = 0
    for _, row in df.iterrows():
        home  = str(row.get("home","")).strip()
        away  = str(row.get("away","")).strip()
        score = str(row.get("score","")).strip()
        if not home or not away or "-" not in score:
            continue
        try:
            gf, ga = map(int, score.split("-"))
            real = _resultado_real(gf, ga)
            pf_l = build_team_profile(home, dm, league)
            pf_v = build_team_profile(away, dm, league)
            ll, lv = calc_lambdas(pf_l, pf_v, league)
            mkts = calc_all_markets(ll, lv)
            # Predicción: resultado con mayor probabilidad
            probs = {"local": mkts["p_l"], "empate": mkts["p_e"], "visita": mkts["p_v"]}
            pred  = max(probs, key=probs.get)
            ok    = (pred == real)
            if ok: correcto += 1
            total += 1
            historial.append({
                "fecha":      str(row.get("date","")),
                "partido":    home + " vs " + away,
                "score":      score,
                "mercado":    "1X2",
                "pick":       pred,
                "momio":      0.0,
                "prob_modelo": round(probs[pred]*100,1),
                "ev":         0.0,
                "edge":       0.0,
                "stake_pct":  0.0,
                "monto":      0.0,
                "resultado":  real,
                "ganado":     ok,
                "ganancia":   0.0,
                "bankroll":   0.0,
                "lambda_l":   round(ll,3),
                "lambda_v":   round(lv,3),
            })
        except Exception:
            continue

    tasa = round(correcto/total*100,1) if total>0 else 0
    metricas = {
        "bankroll_inicial": 0, "bankroll_final": 0, "beneficio": 0,
        "roi": 0.0, "yield": 0.0,
        "total_apuestas": total, "ganadas": correcto,
        "perdidas": total - correcto, "tasa_acierto": tasa,
        "total_expuesto": 0, "max_drawdown": 0,
        "errores": [],
        "_modo": "calibracion",
    }
    return metricas, historial, [0.0]

init()
inject_css()

st.markdown("""
<div class="app-header">
  <span class="app-title">④ Backtest</span>
  <span class="app-sub">Valida el modelo con datos históricos reales</span>
</div>
""", unsafe_allow_html=True)

# ── Liga ───────────────────────────────────────────────────────────────────────
league = st.selectbox(
    "Liga", LEAGUE_NAMES,
    index=LEAGUE_NAMES.index(st.session_state.get("selected_league", "Liga MX")),
    key="bt_league",
)
dm = get_data_master(league)

if len(dm) < 3:
    st.warning(
        f"Se necesitan al menos 3 tablas FBRef de **{league}** cargadas en Página ① para hacer backtest. "
        f"Actualmente tienes {len(dm)}/9."
    )
    st.stop()

st.caption(f"✓ {len(dm)}/9 tablas cargadas · usando modelo Poisson + xG blend")

# ── Parámetros ─────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Parámetros</div>', unsafe_allow_html=True)

p1, p2, p3 = st.columns(3)
with p1:
    bankroll_ini = st.number_input("Banca inicial $", value=1000.0, min_value=100.0, format="%.0f", key="bt_bank")
    kelly_frac   = st.slider("Fracción Kelly", 0.05, 1.0, 0.25, step=0.05, key="bt_kelly")
with p2:
    min_ev    = st.number_input("EV mínimo %",   value=0.0,  min_value=0.0, max_value=30.0, format="%.1f", key="bt_ev")
    min_prob  = st.number_input("Prob mínima %", value=40.0, min_value=0.0, max_value=80.0, format="%.1f", key="bt_prob")
with p3:
    min_edge  = st.number_input("Edge mínimo %", value=3.0,  min_value=0.0, max_value=20.0, format="%.1f", key="bt_edge")
    linea_ou  = st.selectbox("Línea OU", [1.5, 2.5, 3.5], index=1, key="bt_ou")

mercados_sel = st.multiselect(
    "Mercados a analizar",
    ["1x2", "ou", "btts"],
    default=["1x2", "ou"],
    key="bt_mercados",
)

# ── Datos históricos ───────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Datos históricos</div>', unsafe_allow_html=True)

fuente = st.radio(
    "Fuente",
    ["Fixtures cargados (solo resultados jugados)", "Subir CSV con momios"],
    horizontal=True,
    key="bt_fuente",
)

df_bt = None

if fuente == "Fixtures cargados (solo resultados jugados)":
    fix_df = get_fixtures(league)
    if fix_df is None or len(fix_df) == 0:
        st.warning("No hay fixtures cargados para esta liga. Cárgalos en Página ①.")
        st.stop()

    jugados = fix_df[fix_df["played"] & fix_df["score"].notna()].copy()
    st.caption(f"{len(jugados)} partidos jugados disponibles")

    if len(jugados) == 0:
        st.warning("No hay partidos con resultado en los fixtures.")
        st.stop()

    df_bt = jugados[["date", "home", "away", "score"]].copy()
    for col in ["m_l","m_e","m_v","m_over","m_under","m_btts_si","m_btts_no"]:
        df_bt[col] = 0.0

    st.info(
        f"📊 **{len(jugados)} partidos jugados** disponibles para calibración. "
        "Sin momios históricos el backtest muestra si el modelo predice bien los resultados reales. "
        "Para calcular ROI y yield real sube un CSV con los momios de la casa."
    )
    st.dataframe(df_bt[["date","home","away","score"]].head(10), hide_index=True)

else:
    st.markdown("""
    **Formato del CSV requerido:**
    ```
    date,home,away,score,m_l,m_e,m_v,m_over,m_under,m_btts_si,m_btts_no
    2025-08-15,Liverpool,Bournemouth,4-2,1.40,5.00,7.00,1.55,2.35,1.74,2.05
    ```
    - `score` = resultado jugado en formato **GF-GA** (ej. `2-1`)
    - Momios decimales de la casa en el momento previo al partido
    """)

    uploaded = st.file_uploader("Subir CSV", type=["csv"], key="bt_csv")
    if uploaded:
        text = uploaded.read().decode("utf-8")
        df_bt = csv_to_df(text)
        if df_bt is None:
            st.error("No se pudo leer el CSV. Verifica el formato.")
            st.stop()
        # Validar columnas mínimas
        missing = [c for c in ["date","home","away","score"] if c not in df_bt.columns]
        if missing:
            st.error(f"Faltan columnas: {missing}")
            st.stop()
        # Agregar momios en 0 si no vienen
        for col in ["m_l","m_e","m_v","m_over","m_under","m_btts_si","m_btts_no"]:
            if col not in df_bt.columns:
                df_bt[col] = 0.0
        st.success(f"✓ {len(df_bt)} partidos cargados")
        st.dataframe(df_bt[["date","home","away","score","m_l","m_e","m_v"]].head(10), hide_index=True)

# ── Ejecutar ───────────────────────────────────────────────────────────────────
if df_bt is not None:
    if st.button("🚀 Ejecutar Backtest", type="primary", key="bt_run"):
        has_momios = df_bt.get("m_l", pd.Series([0])).max() > 1

        with st.spinner("Corriendo simulación…"):
            if has_momios:
                metricas, historial, evolucion = ejecutar_backtest(
                    df=df_bt,
                    data_master=dm,
                    league=league,
                    bankroll_inicial=bankroll_ini,
                    kelly_frac=kelly_frac,
                    min_ev=min_ev,
                    min_prob=min_prob,
                    min_edge=min_edge,
                    linea_ou=linea_ou,
                    mercados=mercados_sel,
                )
            else:
                # Modo calibración — sin momios, evaluar predicciones vs resultados reales
                metricas, historial, evolucion = _calibracion_backtest(df_bt, dm, league)

        # ── Resultados ─────────────────────────────────────────────────────────
        st.markdown('<div class="sec-label">Resultados</div>', unsafe_allow_html=True)

        if metricas["errores"]:
            with st.expander(f"⚠️ {len(metricas['errores'])} partido(s) sin datos suficientes"):
                for e in metricas["errores"][:20]:
                    st.caption(e)

        if not historial:
            st.warning("Ningún partido pudo analizarse. Verifica que los nombres de equipos coincidan con las tablas FBRef cargadas.")
            st.stop()

        # Modo calibración — mostrar métricas especiales
        if metricas.get("_modo") == "calibracion":
            st.markdown('<div class="sec-label">Calibración del modelo (sin momios)</div>', unsafe_allow_html=True)
            ca, cb, cc = st.columns(3)
            ca.metric("Partidos analizados", metricas["total_apuestas"])
            cb.metric("Predicciones correctas", metricas["ganadas"])
            cc.metric("Tasa de acierto", str(metricas["tasa_acierto"]) + "%")
            if metricas["tasa_acierto"] >= 45:
                st.success("Modelo bien calibrado — supera el 45% de acierto esperado por azar en 1X2.")
            else:
                st.warning("Calibración mejorable. El modelo predice el resultado más probable — no siempre coincide con el real.")
            st.caption("Para calcular ROI y yield real sube un CSV con los momios históricos de la casa.")
            df_hist = pd.DataFrame(historial)
            df_hist["✓"] = df_hist["ganado"].map({True: "✓", False: "✗"})
            st.dataframe(df_hist[["fecha","partido","score","pick","prob_modelo","resultado","✓"]],
                         hide_index=True, use_container_width=True)
            st.stop()

        # KPIs
        c1, c2, c3, c4, c5 = st.columns(5)
        roi_color = "normal" if metricas["roi"] >= 0 else "inverse"
        c1.metric("ROI", f"{metricas['roi']:+.1f}%", f"${metricas['beneficio']:+.0f}")
        c2.metric("Yield", f"{metricas['yield']:+.1f}%")
        c3.metric("Apuestas", metricas["total_apuestas"],
                  f"{metricas['ganadas']}G / {metricas['perdidas']}P")
        c4.metric("Acierto", f"{metricas['tasa_acierto']:.1f}%")
        c5.metric("Max Drawdown", f"{metricas['max_drawdown']:.1f}%")

        # Evolución del bankroll
        st.markdown('<div class="sec-label">Evolución de banca</div>', unsafe_allow_html=True)
        df_ev = pd.DataFrame({
            "Apuesta #": list(range(len(evolucion))),
            "Banca $": evolucion,
        })
        st.line_chart(df_ev.set_index("Apuesta #"))

        # Tabla de apuestas
        st.markdown('<div class="sec-label">Detalle de apuestas</div>', unsafe_allow_html=True)
        df_hist = pd.DataFrame(historial)
        df_hist["✓"] = df_hist["ganado"].map({True: "✓", False: "✗"})

        cols_show = ["fecha","partido","score","mercado","pick","momio",
                     "prob_modelo","ev","edge","monto","ganancia","bankroll","✓"]
        cols_show = [c for c in cols_show if c in df_hist.columns]

        # Colorear
        st.dataframe(
            df_hist[cols_show].style.apply(
                lambda row: ["background-color: #f0fdf4" if row["✓"] == "✓"
                             else "background-color: #fef2f2"] * len(row),
                axis=1,
            ),
            hide_index=True,
            use_container_width=True,
        )

        # Descargar
        csv_out = df_hist.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar resultados CSV",
            data=csv_out,
            file_name=f"backtest_{league.replace(' ','_')}_{date.today()}.csv",
            mime="text/csv",
        )

        # Calibración del modelo
        st.markdown('<div class="sec-label">Calibración del modelo</div>', unsafe_allow_html=True)

        if len(historial) > 5:
            picks_dist = df_hist["pick"].value_counts()
            c_a, c_b = st.columns(2)
            with c_a:
                st.caption("Picks seleccionados")
                st.bar_chart(picks_dist)
            with c_b:
                st.caption("EV promedio por mercado")
                ev_by_mkt = df_hist.groupby("mercado")["ev"].mean().round(1)
                st.bar_chart(ev_by_mkt)

        # Conclusiones
        st.markdown('<div class="sec-label">Conclusiones</div>', unsafe_allow_html=True)

        if metricas["roi"] > 5:
            st.success(f"✅ Modelo rentable con estos parámetros — ROI {metricas['roi']:+.1f}% · Yield {metricas['yield']:+.1f}%")
        elif metricas["roi"] > 0:
            st.info(f"🟡 Modelo ligeramente rentable — ROI {metricas['roi']:+.1f}%. Considera ajustar filtros.")
        else:
            st.warning(f"🔴 Modelo no rentable con estos parámetros — ROI {metricas['roi']:+.1f}%. Prueba aumentar EV mínimo o Edge mínimo.")

        if metricas["max_drawdown"] > 30:
            st.warning(f"⚠️ Drawdown alto ({metricas['max_drawdown']:.1f}%) — reduce Kelly o stake máximo.")

        if metricas["tasa_acierto"] < 45 and has_momios:
            st.info("💡 Tasa de acierto <45% es normal si apuestas a outsiders con momio alto — lo que importa es el yield.")