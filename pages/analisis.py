"""
Intelligence Pro — pages/analisis.py
Cards de partidos con semáforo, + Apostar en un click, y análisis completo expandible.
Bankroll siempre visible en sidebar.
"""
import streamlit as st
import datetime
from ui.styles import inject_styles
from ui.components import (
    bankroll_sidebar, pipeline_steps, section_header,
    signal_class, signal_emoji, inline_tip, toast,
    auto_save_indicator, mark_modified, safe_key,
    fmt_momio_americano
)
from data.leagues import LIGAS
from core.poisson import calcular_probabilidades
from core.kelly import kelly_bet
from core.value import calcular_ev
from data.profile import build_team_profile, calc_lambdas


# ── Colores de señal para st.xxx ──────────────────────────────────────────────

SIGNAL_COLORS = {
    "green":  ("#15803D", "#F0FDF4"),
    "amber":  ("#B45309", "#FFFBEB"),
    "orange": ("#C2410C", "#FFF7ED"),
    "red":    ("#B91C1C", "#FEF2F2"),
}

SIGNAL_LABELS = {
    "green":  "Con valor 🟢",
    "amber":  "EV+ prob baja 🟡",
    "orange": "EV neg pequeño 🟠",
    "red":    "Sin valor 🔴",
}


# ── Obtener y calcular análisis de todos los partidos ─────────────────────────

def _calcular_analisis_partido(partido: dict, momios: dict, ss: dict) -> dict | None:
    """
    Construye el análisis completo de un partido.
    Retorna dict con probabilidades, EVs, Kelly, etc.
    """
    liga_key = partido.get("liga_key", "")
    home = partido.get("home", "")
    away = partido.get("away", "")

    fbref_data = ss.get("fbref_data", {}).get(liga_key, {})
    ha_store = ss.get("ha_store", {}).get(liga_key)

    if not fbref_data:
        return None

    try:
        profile_home = build_team_profile(home, fbref_data, ha_store=ha_store, condicion="home")
        profile_away = build_team_profile(away, fbref_data, ha_store=ha_store, condicion="away")
        lambdas = calc_lambdas(profile_home, profile_away, liga=liga_key, ha_store=ha_store)
        probs = calcular_probabilidades(lambdas["lambda_h"], lambdas["lambda_a"])
    except Exception:
        return None

    bankroll = ss.get("bankroll", 1000.0)
    kelly_frac = ss.get("kelly_fraccion", 0.15)

    mercados = []
    mercado_map = {
        "1X2_H": ("Local gana", probs.get("home", 0), momios.get("home")),
        "1X2_D": ("Empate",     probs.get("draw", 0), momios.get("draw")),
        "1X2_A": ("Visitante",  probs.get("away", 0), momios.get("away")),
        "O25":   ("Over 2.5",   probs.get("over25", 0), momios.get("over25")),
        "U25":   ("Under 2.5",  probs.get("under25", 0), momios.get("under25")),
        "BTTS_Y":("BTTS Sí",    probs.get("btts_yes", 0), momios.get("btts_yes")),
        "BTTS_N":("BTTS No",    probs.get("btts_no", 0), momios.get("btts_no")),
        "O15":   ("Over 1.5",   probs.get("over15", 0), momios.get("over15")),
        "DC_1X": ("DC 1X",      probs.get("dc_1x", 0), momios.get("dc_1x")),
        "DC_X2": ("DC X2",      probs.get("dc_x2", 0), momios.get("dc_x2")),
    }

    for key, (nombre, prob_modelo, momio_d) in mercado_map.items():
        if not momio_d or momio_d <= 1.0:
            continue
        try:
            ev_result = calcular_ev(prob_modelo, momio_d)
            ev = ev_result.get("ev", 0)
            edge = ev_result.get("edge", 0)
            prob_imp = ev_result.get("prob_implicita", 0)

            sig = signal_class(ev, prob_modelo, edge)
            kelly_stake = kelly_bet(
                prob_modelo, momio_d, bankroll, kelly_frac
            ) if ev > 0 else 0

            mercados.append({
                "key": key,
                "nombre": nombre,
                "prob_modelo": prob_modelo,
                "prob_implicita": prob_imp,
                "momio": momio_d,
                "ev": ev,
                "edge": edge,
                "stake": kelly_stake,
                "signal": sig,
            })
        except Exception:
            continue

    if not mercados:
        return None

    # Ordenar por EV descendente
    mercados.sort(key=lambda m: m["ev"], reverse=True)
    mejor = mercados[0]

    return {
        "home": home,
        "away": away,
        "fecha": partido.get("fecha", ""),
        "liga": LIGAS.get(liga_key, {}).get("display", liga_key),
        "liga_key": liga_key,
        "lambda_h": lambdas.get("lambda_h", 0),
        "lambda_a": lambdas.get("lambda_a", 0),
        "probs": probs,
        "mercados": mercados,
        "mejor_signal": mejor["signal"],
        "mejor_mercado": mejor,
        "bankroll": bankroll,
    }


# ── Render principal ──────────────────────────────────────────────────────────

def render():
    inject_styles()

    ss = st.session_state

    # ── Sidebar ─────────────────────────────────────────────────────────────
    with st.sidebar:
        bankroll_sidebar()
        st.divider()

        # Jornada activa mini-lista en sidebar
        jornada = ss.get("jornada_activa", [])
        if jornada:
            section_header("🎯 Picks activos", len(jornada))
            for pick in jornada[-5:]:
                sig = signal_class(pick.get("ev", 0), pick.get("prob", 0), pick.get("edge", 0))
                st.markdown(
                    f'<div class="pick-row">'
                    f'<span class="pick-signal {sig}"></span>'
                    f'<span class="pick-market" style="font-size:0.75rem">'
                    f'{pick.get("partido","?")} — {pick.get("mercado","?")}</span>'
                    f'<span class="pick-stake">${pick.get("stake",0):.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        st.divider()

        # Config Kelly
        st.markdown("**Configuración**")
        kelly_frac = st.slider(
            "Kelly fracción",
            min_value=0.05, max_value=0.25, value=ss.get("kelly_fraccion", 0.15),
            step=0.05, format="%.2f",
            key="config_kelly_slider"
        )
        ss["kelly_fraccion"] = kelly_frac

        bankroll_input = st.number_input(
            "Bankroll (MXN)",
            min_value=0.0,
            value=float(ss.get("bankroll", 1000.0)),
            step=100.0,
            key="config_bankroll_input"
        )
        ss["bankroll"] = bankroll_input

        st.divider()
        auto_save_indicator()

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown('<h1>🎯 Análisis de valor</h1>', unsafe_allow_html=True)
    pipeline_steps()

    # ── Verificaciones ───────────────────────────────────────────────────────
    fbref_data = ss.get("fbref_data", {})
    momios_data = ss.get("momios_data", {})
    fixtures_data = ss.get("fixtures_data", {})

    if not any(v for v in fbref_data.values()):
        st.markdown("""
        <div style="text-align:center;padding:40px;background:var(--surface);
             border:1px dashed var(--border);border-radius:var(--radius)">
            <div style="font-size:2rem;margin-bottom:8px">📋</div>
            <div style="font-family:var(--font-display);font-size:1.1rem;font-weight:600;color:var(--text)">
                Carga los datos primero
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    if not momios_data:
        st.markdown("""
        <div style="text-align:center;padding:40px;background:var(--surface);
             border:1px dashed var(--border);border-radius:var(--radius)">
            <div style="font-size:2rem;margin-bottom:8px">💰</div>
            <div style="font-family:var(--font-display);font-size:1.1rem;font-weight:600;color:var(--text)">
                No hay momios cargados
            </div>
            <div style="color:var(--text-muted);font-size:0.82rem;margin-top:6px">
                Ve a Momios y agrega los precios de esta jornada
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Filtros ──────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])

    ligas_con_datos = [k for k, v in fbref_data.items() if v]
    liga_options = ["Todas"] + [LIGAS.get(k, {}).get("display", k) for k in ligas_con_datos]

    with col_f1:
        liga_filtro = st.selectbox("Liga", liga_options, key="analisis_liga_filtro")
    with col_f2:
        periodo = st.selectbox(
            "Período",
            ["Próximos 3 días", "Esta semana", "Próximas 2 semanas", "Todo"],
            key="analisis_periodo_filtro"
        )
    with col_f3:
        solo_valor = st.toggle("Solo 🟢", value=False, key="analisis_solo_valor")

    # ── Construir lista de partidos con momios ──────────────────────────────
    hoy = datetime.date.today()
    dias_map = {"Próximos 3 días": 3, "Esta semana": 7, "Próximas 2 semanas": 14, "Todo": 9999}
    dias = dias_map.get(periodo, 7)
    limite = hoy + datetime.timedelta(days=dias)

    def parse_fecha(f):
        try:
            return datetime.datetime.strptime(str(f), "%Y-%m-%d").date()
        except Exception:
            return hoy + datetime.timedelta(days=1)

    # Reunir partidos con momios
    partidos_analizar = []
    for pk, momios in momios_data.items():
        meta = momios.get("meta", {})
        if not meta:
            parts = pk.split("_")
            meta = {"home": parts[0], "away": parts[1] if len(parts) > 1 else "?", "fecha": parts[-1]}

        fecha_p = parse_fecha(meta.get("fecha", ""))
        if fecha_p > limite:
            continue

        liga_key = meta.get("liga_key") or _find_liga_key(
            meta.get("home", ""), meta.get("away", ""), fixtures_data
        )

        liga_display = LIGAS.get(liga_key, {}).get("display", meta.get("liga", "?"))

        if liga_filtro != "Todas" and liga_display != liga_filtro:
            continue

        partidos_analizar.append({
            **meta,
            "liga_key": liga_key,
            "momios": momios,
            "pk": pk
        })

    partidos_analizar.sort(key=lambda p: parse_fecha(p.get("fecha", "")))

    # ── Calcular análisis ────────────────────────────────────────────────────
    resultados = []
    with st.spinner("Calculando probabilidades..."):
        for p in partidos_analizar:
            analisis = _calcular_analisis_partido(p, p.get("momios", {}), ss)
            if analisis:
                resultados.append(analisis)

    if solo_valor:
        resultados = [r for r in resultados if r["mejor_signal"] == "green"]

    if not resultados:
        st.info("No hay partidos con análisis disponible en el período seleccionado.")
        return

    # Resumen rápido
    n_verde = sum(1 for r in resultados if r["mejor_signal"] == "green")
    n_amarillo = sum(1 for r in resultados if r["mejor_signal"] == "amber")

    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Partidos analizados", len(resultados))
    col_s2.metric("🟢 Con valor", n_verde)
    col_s3.metric("🟡 EV+ prob baja", n_amarillo)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Renderizar cards ─────────────────────────────────────────────────────
    section_header("Partidos", len(resultados))

    for r in resultados:
        _render_partido_card(r, ss)


# ── Card de partido ────────────────────────────────────────────────────────────

def _render_partido_card(r: dict, ss: dict):
    """Card compacta con señal + acción directa + expand para matemáticas."""
    sig = r["mejor_signal"]
    mejor = r["mejor_mercado"]
    home, away = r["home"], r["away"]
    fecha = r["fecha"]
    liga = r["liga"]
    mercados = r["mercados"]

    color_text, color_bg = SIGNAL_COLORS.get(sig, ("#333", "#fff"))
    emoji = signal_emoji(sig)

    card_key = safe_key("card", home, away, fecha)

    # ── Fila principal (siempre visible) ──────────────────────────────────────
    with st.container():
        col_sig, col_main, col_bet = st.columns([1, 6, 2])

        with col_sig:
            st.markdown(
                f'<div style="font-size:1.5rem;padding:12px 0;text-align:center">{emoji}</div>',
                unsafe_allow_html=True
            )

        with col_main:
            st.markdown(
                f'<div style="font-family:var(--font-ui);padding:10px 0">'
                f'<div style="font-family:var(--font-display);font-weight:600;'
                f'font-size:1rem;color:var(--text);letter-spacing:-0.01em">'
                f'{home} <span style="color:var(--text-muted);font-weight:400">vs</span> {away}</div>'
                f'<div style="font-size:0.72rem;color:var(--text-muted);'
                f'text-transform:uppercase;letter-spacing:0.06em;margin-top:2px">'
                f'{liga} · {fecha}</div>'
                f'<div style="margin-top:6px;display:flex;align-items:center;gap:8px">'
                f'<span style="background:{color_bg};color:{color_text};border-radius:999px;'
                f'padding:2px 10px;font-size:0.75rem;font-weight:600">'
                f'{mejor["nombre"]}</span>'
                f'<span style="font-family:var(--font-mono);font-size:0.9rem;font-weight:600">'
                f'{mejor["momio"]:.2f}</span>'
                f'<span style="font-family:var(--font-mono);font-size:0.75rem;color:{color_text}">'
                f'EV {mejor["ev"]*100:+.1f}% · {mejor["prob_modelo"]*100:.0f}% modelo</span>'
                f'</div></div>',
                unsafe_allow_html=True
            )

        with col_bet:
            stake = mejor.get("stake", 0)
            btn_label = f"+ Apostar ${stake:.0f}" if stake > 0 else "+ Apostar"
            if st.button(btn_label, key=f"bet_{card_key}", use_container_width=True):
                _agregar_pick(r, mejor, ss)
                st.rerun()

        # ── Expandir para ver todo el análisis ────────────────────────────────
        with st.expander(f"Ver análisis completo — {home} vs {away}", expanded=False):
            _render_analisis_expandido(r, ss)

    st.markdown('<hr style="margin:6px 0">', unsafe_allow_html=True)


# ── Análisis expandido ────────────────────────────────────────────────────────

def _render_analisis_expandido(r: dict, ss: dict):
    """Análisis detallado dentro del expander."""
    home, away = r["home"], r["away"]
    probs = r["probs"]
    mercados = r["mercados"]
    lh = r.get("lambda_h", 0)
    la = r.get("lambda_a", 0)

    col_m, col_p = st.columns([3, 2])

    with col_m:
        st.markdown("**Todos los mercados**")
        for m in mercados:
            sig = m["signal"]
            emoji = signal_emoji(sig)
            color_text, color_bg = SIGNAL_COLORS.get(sig, ("#333", "#fff"))
            card_key = safe_key("card_exp", home, away, r["fecha"], m["key"])

            bet_col, info_col = st.columns([1, 3])
            with bet_col:
                if st.button(
                    f"+ ${m.get('stake', 0):.0f}",
                    key=f"exp_bet_{card_key}",
                    disabled=m.get("stake", 0) <= 0
                ):
                    _agregar_pick(r, m, ss)
                    st.rerun()
            with info_col:
                st.markdown(
                    f'{emoji} **{m["nombre"]}** — '
                    f'`{m["momio"]:.2f}` · '
                    f'Modelo: `{m["prob_modelo"]*100:.1f}%` · '
                    f'Impl: `{m["prob_implicita"]*100:.1f}%` · '
                    f'EV: `{m["ev"]*100:+.1f}%` · '
                    f'Edge: `{m["edge"]*100:+.1f}%`'
                )

    with col_p:
        st.markdown("**Probabilidades modelo**")
        st.markdown(
            f'<div class="stat-row"><span class="stat-label">λ Local</span>'
            f'<span class="stat-value">{lh:.2f} goles</span></div>'
            f'<div class="stat-row"><span class="stat-label">λ Visitante</span>'
            f'<span class="stat-value">{la:.2f} goles</span></div>'
            f'<div class="stat-row"><span class="stat-label">Local gana</span>'
            f'<span class="stat-value">{probs.get("home",0)*100:.1f}%</span></div>'
            f'<div class="stat-row"><span class="stat-label">Empate</span>'
            f'<span class="stat-value">{probs.get("draw",0)*100:.1f}%</span></div>'
            f'<div class="stat-row"><span class="stat-label">Visitante gana</span>'
            f'<span class="stat-value">{probs.get("away",0)*100:.1f}%</span></div>'
            f'<div class="stat-row"><span class="stat-label">Over 2.5</span>'
            f'<span class="stat-value">{probs.get("over25",0)*100:.1f}%</span></div>'
            f'<div class="stat-row"><span class="stat-label">BTTS</span>'
            f'<span class="stat-value">{probs.get("btts_yes",0)*100:.1f}%</span></div>',
            unsafe_allow_html=True
        )

    # H2H desde session
    h2h = ss.get("h2h_data", {}).get(f"{home}_{away}")
    if h2h:
        st.markdown("**H2H reciente**")
        for enc in h2h[:3]:
            st.caption(
                f"{enc.get('fecha','?')} · {enc.get('resultado','?')}"
            )

    # Parlay helper
    jornada = ss.get("jornada_activa", [])
    if len(jornada) >= 1:
        st.markdown("---")
        mejor = [m for m in mercados if m["signal"] == "green"]
        if mejor and st.button(
            "🔗 Agregar al parlay activo",
            key=safe_key("parlay_add", home, away, r["fecha"])
        ):
            _agregar_pick(r, mejor[0], ss, es_parlay=True)
            st.rerun()


# ── Agregar pick a jornada ────────────────────────────────────────────────────

def _agregar_pick(r: dict, mercado: dict, ss: dict, es_parlay: bool = False):
    """Agrega un pick a la jornada activa."""
    if "jornada_activa" not in ss:
        ss["jornada_activa"] = []

    home, away = r["home"], r["away"]
    fecha = r["fecha"]

    # Evitar duplicados
    existe = any(
        p.get("home") == home and p.get("away") == away
        and p.get("mercado_key") == mercado["key"]
        for p in ss["jornada_activa"]
    )
    if existe:
        toast(f"⚠️ Ya tienes este bet en la jornada", "info")
        return

    pick = {
        "partido": f"{home} vs {away}",
        "home": home,
        "away": away,
        "fecha": fecha,
        "liga": r["liga"],
        "mercado": mercado["nombre"],
        "mercado_key": mercado["key"],
        "momio": mercado["momio"],
        "prob": mercado["prob_modelo"],
        "ev": mercado["ev"],
        "edge": mercado["edge"],
        "stake": mercado.get("stake", 0),
        "es_parlay": es_parlay,
        "resultado": None,
        "ganancia": None,
    }

    ss["jornada_activa"].append(pick)
    mark_modified()
    toast(
        f"✅ {mercado['nombre']} — {home} vs {away} agregado "
        f"(${mercado.get('stake',0):.0f} MXN)",
        "success"
    )


# ── Helper: encontrar liga_key desde fixtures ─────────────────────────────────

def _find_liga_key(home: str, away: str, fixtures_data: dict) -> str:
    """Busca en qué liga están estos equipos."""
    for liga_key, partidos in fixtures_data.items():
        if not partidos:
            continue
        for p in partidos:
            if (p.get("home", "").lower() == home.lower() or
                    p.get("away", "").lower() == away.lower()):
                return liga_key
    return ""
