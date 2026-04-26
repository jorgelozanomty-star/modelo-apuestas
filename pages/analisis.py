"""
Intelligence Pro — pages/analisis.py  v4.2
Firmas reales:
  core.poisson : calc_matrix(lam_l, lam_v) -> dict, calc_1x2(matrix) -> tuple
  core.kelly   : stake_amount(prob, momio, fraction, bankroll) -> float
  core.value   : evaluate_pick(name, prob, momio, fraction, bankroll) -> dict
                 (ev y edge ya vienen en %, ej: 8.5 significa 8.5%)
  data.profile : build_team_profile(squad_name, data_master, league_name)
                 calc_lambdas(prof_l, prof_v, league_name, ha_store=None) -> (lam_l, lam_v)
"""
import streamlit as st
import datetime
from ui.styles import inject_styles
from ui.components import (
    bankroll_sidebar, pipeline_steps, section_header,
    signal_class, signal_emoji, toast,
    auto_save_indicator, mark_modified, safe_key,
)
from data.leagues import LEAGUES, LEAGUE_NAMES
from core.poisson import calc_matrix, calc_1x2
from core.kelly import stake_amount
from core.value import evaluate_pick
from data.profile import build_team_profile, calc_lambdas

SIGNAL_COLORS = {
    "green":  ("#15803D", "#F0FDF4"),
    "amber":  ("#B45309", "#FFFBEB"),
    "orange": ("#C2410C", "#FFF7ED"),
    "red":    ("#B91C1C", "#FEF2F2"),
}


def _probs_from_matrix(matrix: dict) -> dict:
    """Calcula todas las probabilidades de mercado desde la matriz Poisson."""
    p_l, p_e, p_v = calc_1x2(matrix)
    over15  = sum(p for (i, j), p in matrix.items() if i + j > 1)
    over25  = sum(p for (i, j), p in matrix.items() if i + j > 2)
    over35  = sum(p for (i, j), p in matrix.items() if i + j > 3)
    btts    = sum(p for (i, j), p in matrix.items() if i > 0 and j > 0)
    return {
        "home":     p_l,
        "draw":     p_e,
        "away":     p_v,
        "over15":   over15,
        "over25":   over25,
        "over35":   over35,
        "under25":  1.0 - over25,
        "under15":  1.0 - over15,
        "btts_yes": btts,
        "btts_no":  1.0 - btts,
        "dc_1x":    p_l + p_e,
        "dc_x2":    p_v + p_e,
    }


def _parse_fecha(f):
    try:
        return datetime.datetime.strptime(str(f), "%Y-%m-%d").date()
    except Exception:
        return datetime.date.today() + datetime.timedelta(days=1)


def _calcular_analisis(partido: dict, momios: dict, ss: dict):
    liga_key   = partido.get("liga_key", "")
    home       = partido.get("home", "")
    away       = partido.get("away", "")
    fbref      = ss.get("fbref_data", {}).get(liga_key, {})
    ha_store   = ss.get("ha_store", {}).get(liga_key)
    bankroll   = ss.get("bankroll", 1000.0)
    kelly_frac = ss.get("kelly_fraccion", 0.15)

    if not fbref:
        return None

    try:
        ph      = build_team_profile(home, fbref, league_name=liga_key)
        pa      = build_team_profile(away, fbref, league_name=liga_key)
        lam_h, lam_a = calc_lambdas(ph, pa, liga_key, ha_store=ha_store)
        matrix  = calc_matrix(lam_h, lam_a)
        probs   = _probs_from_matrix(matrix)
    except Exception:
        return None

    # evaluate_pick retorna ev y edge ya en porcentaje (8.5 = 8.5%)
    mercado_map = {
        "1X2_H":  ("Local gana",  probs["home"],     momios.get("home")),
        "1X2_D":  ("Empate",      probs["draw"],      momios.get("draw")),
        "1X2_A":  ("Visitante",   probs["away"],      momios.get("away")),
        "O25":    ("Over 2.5",    probs["over25"],   momios.get("over25")),
        "U25":    ("Under 2.5",   probs["under25"],  momios.get("under25")),
        "BTTS_Y": ("BTTS Sí",     probs["btts_yes"], momios.get("btts_yes")),
        "O15":    ("Over 1.5",    probs["over15"],   momios.get("over15")),
        "DC_1X":  ("DC 1X",       probs["dc_1x"],    momios.get("dc_1x")),
        "DC_X2":  ("DC X2",       probs["dc_x2"],    momios.get("dc_x2")),
    }

    mercados = []
    for key, (nombre, prob_m, momio_d) in mercado_map.items():
        if not momio_d or momio_d <= 1.0:
            continue
        try:
            pick = evaluate_pick(nombre, prob_m, momio_d, kelly_frac, bankroll)
            # ev y edge vienen en porcentaje → convertir a decimal para signal_class
            ev_dec   = pick["ev"]   / 100.0
            edge_dec = pick["edge"] / 100.0
            sig      = signal_class(ev_dec, prob_m, edge_dec)
            mercados.append({
                "key":          key,
                "nombre":       nombre,
                "prob_modelo":  prob_m,
                "prob_impl_pct": pick["implied"],   # ya en %
                "momio":        momio_d,
                "ev_pct":       pick["ev"],         # %
                "edge_pct":     pick["edge"],       # %
                "ev":           ev_dec,             # decimal para signal_class
                "edge":         edge_dec,
                "stake":        pick["stake"],
                "signal":       sig,
            })
        except Exception:
            continue

    if not mercados:
        return None

    mercados.sort(key=lambda m: m["ev"], reverse=True)
    mejor = mercados[0]

    return {
        "home": home, "away": away,
        "fecha": partido.get("fecha", ""),
        "liga":  liga_key,
        "lam_h": lam_h, "lam_a": lam_a,
        "probs": probs,
        "mercados": mercados,
        "mejor_signal": mejor["signal"],
        "mejor_mercado": mejor,
    }


def render():
    inject_styles()
    ss = st.session_state

    # ── Sidebar ─────────────────────────────────────────────────
    with st.sidebar:
        bankroll_sidebar()
        st.divider()
        picks = ss.get("jornada_activa", [])
        if picks:
            section_header("🎯 Picks activos", len(picks))
            for p in picks[-5:]:
                sig = signal_class(p.get("ev", 0), p.get("prob", 0), p.get("edge", 0))
                st.markdown(
                    f'<div class="pick-row">'
                    f'<span class="pick-signal {sig}"></span>'
                    f'<span class="pick-market" style="font-size:.75rem">'
                    f'{p.get("partido","?")} — {p.get("mercado","?")}</span>'
                    f'<span class="pick-stake">${p.get("stake",0):.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.divider()
        st.markdown("**Configuración**")
        kelly_frac = st.slider("Kelly fracción", 0.05, 0.25,
                               float(ss.get("kelly_fraccion", 0.15)), 0.05, key="cfg_kelly")
        ss["kelly_fraccion"] = kelly_frac
        bankroll_v = st.number_input("Bankroll (MXN)", 0.0,
                                     value=float(ss.get("bankroll", 1000.0)),
                                     step=100.0, key="cfg_bankroll")
        ss["bankroll"] = bankroll_v
        st.divider()
        auto_save_indicator()

    # ── Header ───────────────────────────────────────────────────
    st.markdown(('<h1>🎯 Análisis de valor</h1>').strip(), unsafe_allow_html=True)
    pipeline_steps()

    fbref_data    = ss.get("fbref_data", {})
    momios_data   = ss.get("momios_data", {})
    fixtures_data = ss.get("fixtures_data", {})

    if not any(v is not None and len(v) > 0 for v in fbref_data.values()):
        st.info("Carga datos en **① Cargar Ligas** primero.")
        return
    if not momios_data:
        st.info("No hay momios. Ve a **② Momios** y agrega los precios.")
        return

    # ── Filtros ──────────────────────────────────────────────────
    cf1, cf2, cf3 = st.columns([2, 2, 1])
    ligas_con_datos = [k for k, v in fbref_data.items() if v is not None and len(v) > 0]
    with cf1:
        liga_filtro = st.selectbox("Liga", ["Todas"] + ligas_con_datos, key="an_liga")
    with cf2:
        periodo = st.selectbox("Período",
                               ["Próximos 3 días", "Esta semana",
                                "Próximas 2 semanas", "Todo"],
                               key="an_periodo")
    with cf3:
        solo_valor = st.toggle("Solo 🟢", False, key="an_solo")

    hoy    = datetime.date.today()
    dias   = {"Próximos 3 días": 3, "Esta semana": 7,
               "Próximas 2 semanas": 14, "Todo": 9999}[periodo]
    limite = hoy + datetime.timedelta(days=dias)

    # ── Construir lista ──────────────────────────────────────────
    partidos = []
    for pk, momios in momios_data.items():
        meta = momios.get("meta", {})
        if not meta:
            pts = pk.split("_")
            meta = {"home": pts[0], "away": pts[1] if len(pts) > 1 else "?",
                    "fecha": pts[-1]}
        if _parse_fecha(meta.get("fecha", "")) > limite:
            continue
        liga_key = meta.get("liga_key") or _find_liga_key(
            meta.get("home", ""), meta.get("away", ""), fixtures_data
        )
        if liga_filtro != "Todas" and liga_key != liga_filtro:
            continue
        partidos.append({**meta, "liga_key": liga_key, "momios": momios, "pk": pk})

    partidos.sort(key=lambda p: _parse_fecha(p.get("fecha", "")))

    # ── Calcular ─────────────────────────────────────────────────
    resultados = []
    with st.spinner("Calculando..."):
        for p in partidos:
            r = _calcular_analisis(p, p.get("momios", {}), ss)
            if r:
                resultados.append(r)

    if solo_valor:
        resultados = [r for r in resultados if r["mejor_signal"] == "green"]

    if not resultados:
        st.info("Sin partidos con análisis disponible para este período.")
        return

    # ── Resumen ──────────────────────────────────────────────────
    n_verde = sum(1 for r in resultados if r["mejor_signal"] == "green")
    cs1, cs2, cs3 = st.columns(3)
    cs1.metric("Analizados",       len(resultados))
    cs2.metric("🟢 Con valor",     n_verde)
    cs3.metric("🟡 EV+ prob baja", sum(1 for r in resultados if r["mejor_signal"] == "amber"))

    st.markdown(("<hr>").strip(), unsafe_allow_html=True)
    section_header("Partidos", len(resultados))

    for r in resultados:
        _card(r, ss)


def _card(r: dict, ss: dict):
    sig   = r["mejor_signal"]
    mejor = r["mejor_mercado"]
    home, away, fecha, liga = r["home"], r["away"], r["fecha"], r["liga"]
    ct, cb = SIGNAL_COLORS.get(sig, ("#333", "#fff"))
    emoji  = signal_emoji(sig)
    ck     = safe_key("card", home, away, fecha)

    col_s, col_m, col_b = st.columns([1, 6, 2])
    with col_s:
        st.markdown(
            f'<div style="font-size:1.5rem;padding:12px 0;text-align:center">{emoji}</div>',
            unsafe_allow_html=True,
        )
    with col_m:
        st.markdown(
            f'<div style="padding:10px 0">'
            f'<div style="font-family:var(--font-display);font-weight:600;font-size:1rem">'
            f'{home} <span style="color:var(--text-muted);font-weight:400">vs</span> {away}</div>'
            f'<div style="font-size:.72rem;color:var(--text-muted);'
            f'text-transform:uppercase;letter-spacing:.06em;margin-top:2px">'
            f'{liga} · {fecha}</div>'
            f'<div style="margin-top:6px;display:flex;align-items:center;gap:8px">'
            f'<span style="background:{cb};color:{ct};border-radius:999px;'
            f'padding:2px 10px;font-size:.75rem;font-weight:600">{mejor["nombre"]}</span>'
            f'<span style="font-family:var(--font-mono);font-size:.9rem;font-weight:600">'
            f'{mejor["momio"]:.2f}</span>'
            f'<span style="font-family:var(--font-mono);font-size:.75rem;color:{ct}">'
            f'EV {mejor["ev_pct"]:+.1f}% · {mejor["prob_modelo"]*100:.0f}% modelo</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    with col_b:
        stake = mejor.get("stake", 0)
        label = f"+ Apostar ${stake:.0f}" if stake > 0 else "+ Apostar"
        if st.button(label, key=f"bet_{ck}", use_container_width=True):
            _add_pick(r, mejor, ss)
            st.rerun()

    with st.expander(f"Análisis completo — {home} vs {away}"):
        _analisis_expandido(r, ss)

    st.markdown(('<hr style="margin:6px 0">').strip(), unsafe_allow_html=True)


def _analisis_expandido(r: dict, ss: dict):
    probs    = r["probs"]
    mercados = r["mercados"]
    home, away, fecha = r["home"], r["away"], r["fecha"]

    cm, cp = st.columns([3, 2])
    with cm:
        st.markdown("**Todos los mercados**")
        for m in mercados:
            emoji = signal_emoji(m["signal"])
            ct, _ = SIGNAL_COLORS.get(m["signal"], ("#333", "#fff"))
            bk = safe_key("exp", home, away, fecha, m["key"])
            bc, ic = st.columns([1, 3])
            with bc:
                if st.button(f"+ ${m.get('stake',0):.0f}",
                             key=f"xbet_{bk}",
                             disabled=m.get("stake", 0) <= 0):
                    _add_pick(r, m, ss)
                    st.rerun()
            with ic:
                st.markdown(
                    f'{emoji} **{m["nombre"]}** — `{m["momio"]:.2f}` · '
                    f'Modelo `{m["prob_modelo"]*100:.1f}%` · '
                    f'Impl `{m["prob_impl_pct"]:.1f}%` · '
                    f'EV `{m["ev_pct"]:+.1f}%` · '
                    f'Edge `{m["edge_pct"]:+.1f}%`'
                )
    with cp:
        st.markdown("**Probabilidades modelo**")
        for label, val in [
            ("λ Local",     f'{r.get("lam_h", 0):.2f} goles'),
            ("λ Visitante", f'{r.get("lam_a", 0):.2f} goles'),
            ("Local gana",  f'{probs.get("home", 0)*100:.1f}%'),
            ("Empate",      f'{probs.get("draw", 0)*100:.1f}%'),
            ("Visitante",   f'{probs.get("away", 0)*100:.1f}%'),
            ("Over 2.5",    f'{probs.get("over25", 0)*100:.1f}%'),
            ("BTTS Sí",     f'{probs.get("btts_yes", 0)*100:.1f}%'),
        ]:
            st.markdown(
                f'<div class="stat-row">'
                f'<span class="stat-label">{label}</span>'
                f'<span class="stat-value">{val}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _add_pick(r: dict, mercado: dict, ss: dict):
    ss.setdefault("jornada_activa", [])
    home, away, fecha = r["home"], r["away"], r["fecha"]
    if any(p.get("home") == home and p.get("away") == away
           and p.get("mercado_key") == mercado["key"]
           for p in ss["jornada_activa"]):
        toast("⚠️ Ya tienes este bet en la jornada", "info")
        return
    ss["jornada_activa"].append({
        "partido":    f"{home} vs {away}",
        "home": home, "away": away, "fecha": fecha,
        "liga":       r["liga"],
        "mercado":    mercado["nombre"],
        "mercado_key": mercado["key"],
        "momio":      mercado["momio"],
        "prob":       mercado["prob_modelo"],
        "ev":         mercado["ev"],
        "edge":       mercado["edge"],
        "stake":      mercado.get("stake", 0),
        "resultado":  None,
        "ganancia":   None,
    })
    mark_modified()
    toast(
        f'✅ {mercado["nombre"]} — {home} vs {away} '
        f'(${mercado.get("stake", 0):.0f} MXN)',
        "success",
    )


def _find_liga_key(home: str, away: str, fixtures_data: dict) -> str:
    for liga_key, partidos in fixtures_data.items():
        if not partidos:
            continue
        for p in partidos:
            if (p.get("home", "").lower() == home.lower()
                    or p.get("away", "").lower() == away.lower()):
                return liga_key
    return ""

render()
