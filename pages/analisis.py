"""
pages/analisis.py
Página 3 — Análisis
Lista de partidos con semáforo de valor.
Filtros: liga + jornada completa / solo hoy.
Click → análisis completo precargado.
"""
import streamlit as st
from datetime import date, timedelta

from data.session   import init, get_all_pending_matches, get_momios, get_data_master, get_fixtures
from data.profile   import build_team_profile, calc_lambdas, blend_label
from data.leagues   import LEAGUES, LEAGUE_NAMES
from data.fixtures  import get_current_gameweek, get_gameweek_matches, parse_h2h, h2h_lambda_adjustment
from core.poisson   import calc_all_markets
from core.value     import evaluate_1x2, evaluate_ou, evaluate_pick, remove_vig, overround
from core.kelly     import roi_pct, update_bankroll
from ui.styles      import inject_css
from ui.components  import (fmt_money, prob_bar, markets_row, dc_row,
                             exact_scores_row, picks_row, stat_row,
                             team_header, lam_info, vig_info, jornada_row, pick_card)

init()
inject_css()

# ── Header ─────────────────────────────────────────────────────────────────────
r = roi_pct(st.session_state.banca_actual, st.session_state.banca_inicial)
roi_cls = "roi-pos" if r > 0 else ("roi-neg" if r < 0 else "roi-neu")
st.markdown(f"""
<div class="app-header">
  <span class="app-title">③ Análisis</span>
  <span class="app-sub">Selecciona un partido para analizarlo</span>
  <span class="app-tag">
    <span class="banca-lbl">Banca</span>
    <b style="font-family:DM Mono,monospace;">{fmt_money(st.session_state.banca_actual)}</b>
    <span class="{roi_cls}"> {r:+.1f}%</span>
  </span>
</div>
""", unsafe_allow_html=True)

# ── Filtros ────────────────────────────────────────────────────────────────────
today = date.today()
f1, f2, f3 = st.columns(3)

with f1:
    ligas_disp = ["Todas las ligas"] + [
        lg for lg in LEAGUE_NAMES
        if st.session_state.get("fixtures_store", {}).get(lg)
           or st.session_state.get("fbref_store", {}).get(lg)
    ]
    filtro_liga = st.selectbox("Liga", ligas_disp, key="an_liga")

with f2:
    filtro_dia = st.selectbox(
        "Período",
        ["Solo hoy", "Próximos 3 días", "Jornada completa", "Todos pendientes"],
        key="an_dia",
    )

with f3:
    filtro_valor = st.selectbox(
        "Mostrar",
        ["Todos", "Solo con valor (EV+)", "Solo con momios"],
        key="an_valor",
    )

kelly_fraction = st.session_state.get("an_kelly", 0.25)

# ── Todos los partidos ─────────────────────────────────────────────────────────
all_matches = get_all_pending_matches()

# Filtro liga
if filtro_liga != "Todas las ligas":
    all_matches = [m for m in all_matches if m["league"] == filtro_liga]

# Filtro período
if filtro_dia == "Solo hoy":
    all_matches = [m for m in all_matches if m["date"] == today]
elif filtro_dia == "Próximos 3 días":
    all_matches = [m for m in all_matches if m["date"] <= today + timedelta(3)]
elif filtro_dia == "Jornada completa":
    # Jornada actual de cada liga
    jornada_keys = set()
    for lg in LEAGUE_NAMES:
        df_fix = get_fixtures(lg)
        if df_fix is None: continue
        wk = get_current_gameweek(df_fix, today)
        if wk is None: continue
        gw = get_gameweek_matches(df_fix, wk, today)
        for _, r in gw.iterrows():
            jornada_keys.add(f"{r['home']} vs {r['away']}")
    if jornada_keys:
        all_matches = [m for m in all_matches if m["key"] in jornada_keys]

# Pre-calcular EV para semáforo
def quick_ev(m):
    """
    EV máximo entre picks que pasan el filtro de probabilidad mínima.
    Retorna (best_ev, best_prob, best_name) o None si no hay momios.
    """
    momios = m["momios"]
    if not momios.get("m_l"):
        return None
    league = m["league"]
    dm = get_data_master(league)
    try:
        prof_l = build_team_profile(m["home"], dm, league)
        prof_v = build_team_profile(m["away"], dm, league)
        lam_l, lam_v = calc_lambdas(prof_l, prof_v, league)
        mkts = calc_all_markets(lam_l, lam_v)

        candidates = []
        if momios.get("m_l"):
            candidates.append((mkts["p_l"], momios["m_l"], m["home"][:12]))
        if momios.get("m_e"):
            candidates.append((mkts["p_e"], momios["m_e"], "Empate"))
        if momios.get("m_v"):
            candidates.append((mkts["p_v"], momios["m_v"], m["away"][:12]))
        if momios.get("m_over"):
            candidates.append((mkts["over25"], momios["m_over"], "Over 2.5"))
        if momios.get("m_btts_si"):
            candidates.append((mkts["btts"], momios["m_btts_si"], "BTTS Sí"))

        best_ev = -99; best_prob = 0; best_name = ""
        for prob, momio, name in candidates:
            ev = (prob * momio - 1) * 100
            if ev > best_ev:
                best_ev = ev; best_prob = prob * 100; best_name = name

        return (best_ev, best_prob, best_name) if best_ev > -99 else None
    except:
        return None

# Calcular EV para todos
for m in all_matches:
    result = quick_ev(m)
    if result:
        m["best_ev"], m["best_prob"], m["best_pick"] = result
    else:
        m["best_ev"] = None; m["best_prob"] = 0; m["best_pick"] = ""

# Filtro valor
if filtro_valor == "Solo con valor (EV+)":
    all_matches = [m for m in all_matches if m.get("best_ev") is not None
                   and m["best_ev"] > 0]
elif filtro_valor == "Solo con momios":
    all_matches = [m for m in all_matches if m["has_momios"]]

if not all_matches:
    st.info("Sin partidos con los filtros actuales.")
    st.stop()

# ── Lista de partidos ──────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Partidos</div>', unsafe_allow_html=True)
st.caption(f"{len(all_matches)} partido(s) · click → para analizar")

# Selección activa
active_key = st.session_state.get("an_active_key", None)

from itertools import groupby
all_matches.sort(key=lambda x: (
    LEAGUE_NAMES.index(x["league"]) if x["league"] in LEAGUE_NAMES else 99,
    x["date"], x["time"]
))

for league_name, group in groupby(all_matches, key=lambda x: x["league"]):
    group_list = list(group)
    cfg = LEAGUES.get(league_name, {})
    flag = cfg.get("flag", "")
    st.markdown(
        f'<span style="font-size:0.72rem;font-weight:600;color:#78716c;">{flag} {league_name}</span>',
        unsafe_allow_html=True,
    )

    for m in group_list:
        key     = m["key"]
        ev      = m.get("best_ev")
        has_mom = m["has_momios"]
        is_active = key == active_key

        prob  = m.get("best_prob", 0)
        pick_name = m.get("best_pick", "")
        min_prob = 40.0  # filtro de probabilidad mínima

                # Semáforo — todos visibles, colores orientativos
        if not has_mom:
            dot = "⚪"; dot_color = "#a8a29e"; tip = "sin momios"
        elif ev is None:
            dot = "🔵"; dot_color = "#0891b2"; tip = "calculando"
        elif ev > 0 and prob >= min_prob:
            dot = "🟢"; dot_color = "#16a34a"; tip = "VALOR {} {:.0f}% EV {:+.1f}%".format(pick_name, prob, ev)
        elif ev > 0 and prob < min_prob:
            dot = "🟡"; dot_color = "#d97706"; tip = "EV+ prob baja {} {:.0f}%".format(pick_name, prob)
        elif ev > -5:
            dot = "🟠"; dot_color = "#ea580c"; tip = "sin valor EV {:+.1f}%".format(ev)
        else:
            dot = "🔴"; dot_color = "#dc2626"; tip = "sin valor EV {:+.1f}%".format(ev)

        ev_txt = tip if ev is not None else "sin momios"
        d_str  = "{} {}".format(m['date'].strftime('%d/%m'), m['time'])

        border = "#4f46e5" if is_active else "#e7e5e0"
        bg     = "#f5f3ff" if is_active else "#ffffff"

        c_row, c_btn = st.columns([8, 1])
        with c_row:
            st.markdown(
                f'<div style="background:{bg};border:1px solid {border};border-radius:8px;'
                f'padding:10px 14px;margin-bottom:6px;cursor:pointer;">'
                f'<span style="font-size:0.75rem;font-family:DM Mono,monospace;color:#a8a29e;">{d_str}</span>'
                f'<span style="font-size:0.85rem;font-weight:600;color:#1c1917;margin:0 8px;">{m["home"]}</span>'
                f'<span style="font-size:0.75rem;color:#a8a29e;">vs</span>'
                f'<span style="font-size:0.85rem;font-weight:600;color:#1c1917;margin:0 8px;">{m["away"]}</span>'
                f'<span style="font-size:0.72rem;color:{dot_color};">{dot} {ev_txt}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("→", key=f"an_{key}", help="Analizar"):
                st.session_state["an_active_key"] = key
                st.session_state["an_active_league"] = league_name
                # Limpiar selectbox keys para forzar nuevo partido
                for k in ["local_sel", "visita_sel", "_pre_home", "_pre_away"]:
                    st.session_state.pop(k, None)
                st.rerun()

# ── Panel de análisis ──────────────────────────────────────────────────────────
if not active_key:
    st.info("Selecciona un partido de la lista para ver el análisis.")
    st.stop()

# Dynamic keys per match handle state isolation

# Encontrar match activo
active_match = next((m for m in get_all_pending_matches() if m["key"] == active_key), None)
if not active_match:
    st.warning("Partido no encontrado.")
    st.stop()

local   = active_match["home"]
visita  = active_match["away"]
league  = st.session_state.get("an_active_league", active_match["league"])
momios  = get_momios(active_key)
dm      = get_data_master(league)
cfg_lg  = LEAGUES.get(league, {})

st.markdown("---")
st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin:16px 0 8px 0;">
  <span style="font-size:1.1rem;font-weight:700;color:#1c1917;">{local}</span>
  <span style="font-size:0.75rem;color:#a8a29e;">vs</span>
  <span style="font-size:1.1rem;font-weight:700;color:#1c1917;">{visita}</span>
  <span style="font-size:0.7rem;font-family:DM Mono,monospace;background:#f0ede8;padding:2px 8px;border-radius:20px;color:#78716c;">{cfg_lg.get('flag','')} {league}</span>
</div>
""", unsafe_allow_html=True)

# ── Momios (editables inline) ──────────────────────────────────────────────────
st.markdown('<div class="sec-label">Momios</div>', unsafe_allow_html=True)

mc1, mc2, mc3 = st.columns(3)
with mc1: m_l = st.number_input(f"Local {local[:12]}", value=float(momios.get("m_l",2.0) or 2.0), format="%.2f", min_value=1.01, key=f"an_ml_{active_key}")
with mc2: m_e = st.number_input("Empate", value=float(momios.get("m_e",3.0) or 3.0), format="%.2f", min_value=1.01, key=f"an_me_{active_key}")
with mc3: m_v = st.number_input(f"Visita {visita[:12]}", value=float(momios.get("m_v",3.0) or 3.0), format="%.2f", min_value=1.01, key=f"an_mv_{active_key}")

OR   = overround([m_l, m_e, m_v])
vf   = remove_vig([m_l, m_e, m_v])
st.markdown(vig_info(OR*100, m_l, m_e, m_v, vf[0]*100, vf[1]*100, vf[2]*100), unsafe_allow_html=True)

# ── Perfiles + lambdas ────────────────────────────────────────────────────────
kelly_fraction = 0.25

try:
    prof_l = build_team_profile(local,  dm, league)
    prof_v = build_team_profile(visita, dm, league)
    lam_l, lam_v = calc_lambdas(prof_l, prof_v, league)

    # Ajuste H2H si disponible
    h2h_store = st.session_state.get("h2h_store", {})
    h2h = h2h_store.get(active_key) or h2h_store.get(f"{visita}_{local}")
    if h2h:
        lam_l, lam_v = h2h_lambda_adjustment(h2h, lam_l, lam_v)

    st.markdown(lam_info(lam_l, lam_v, local[:12], visita[:12], blend_label(prof_l), blend_label(prof_v)), unsafe_allow_html=True)
    st.caption(f"{cfg_lg.get('flag','')} {league}  ·  Home adv: +{cfg_lg.get('home_adv',0.2):.2f}  ·  Tablas: {len(dm)}/9")

    markets = calc_all_markets(lam_l, lam_v)

    # ── H2H card ──────────────────────────────────────────────────────────────
    if h2h:
        st.markdown(f"""
        <div class="card" style="margin:8px 0;">
          <div class="stat-sec">⚔️ H2H — últimos {h2h['total_matches']} partidos</div>
          <div class="mkt-grid">
            <div class="mkt-pill"><div class="mkt-val" style="color:#4f46e5;">{h2h['home_wins']}</div><div class="mkt-lbl">Local</div></div>
            <div class="mkt-pill"><div class="mkt-val" style="color:#78716c;">{h2h['draws']}</div><div class="mkt-lbl">Empates</div></div>
            <div class="mkt-pill"><div class="mkt-val" style="color:#f59e0b;">{h2h['away_wins']}</div><div class="mkt-lbl">Visita</div></div>
            <div class="mkt-pill"><div class="mkt-val">{h2h['avg_goals']}</div><div class="mkt-lbl">Goles/p</div></div>
            <div class="mkt-pill"><div class="mkt-val" style="color:#16a34a;">{h2h['over25_pct']}%</div><div class="mkt-lbl">Over 2.5</div></div>
            <div class="mkt-pill"><div class="mkt-val" style="color:#7c3aed;">{h2h['btts_pct']}%</div><div class="mkt-lbl">BTTS</div></div>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Comparativa ───────────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Comparativa</div>', unsafe_allow_html=True)
    ch_l, ch_v = st.columns(2)
    with ch_l:  st.markdown(team_header(prof_l, align_right=False), unsafe_allow_html=True)
    with ch_v:  st.markdown(team_header(prof_v, align_right=True),  unsafe_allow_html=True)
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="stat-sec">⚽ Ataque</div>', unsafe_allow_html=True)
        rows = ""
        rows += stat_row("Goles / partido",    prof_l["gf_pg"],    prof_v["gf_pg"])
        rows += stat_row("xG / partido",        prof_l["xg_pg"],    prof_v["xg_pg"])
        rows += stat_row("npxG / partido",      prof_l["npxg_pg"],  prof_v["npxg_pg"])
        rows += stat_row("Tiros / partido",     prof_l["sh_pg"],    prof_v["sh_pg"])
        rows += stat_row("SoT / partido",       prof_l["sot_pg"],   prof_v["sot_pg"])
        rows += stat_row("SoT%",                prof_l["sot_pct"],  prof_v["sot_pct"], fmt="{:.1f}%")
        rows += stat_row("Eficiencia G/Sh",     prof_l["g_sh"],     prof_v["g_sh"],    fmt="{:.3f}")
        if rows.strip(): st.markdown(rows, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with cc2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="stat-sec">🛡️ Defensa · Disciplina</div>', unsafe_allow_html=True)
        rows = ""
        rows += stat_row("Goles recibidos / p",   prof_l["ga_pg"],       prof_v["ga_pg"],       higher_good=False)
        rows += stat_row("xGA / partido",          prof_l["xga_pg"],      prof_v["xga_pg"],      higher_good=False)
        rows += stat_row("Tiros rivales / p",      prof_l["opp_sh_pg"],   prof_v["opp_sh_pg"],   higher_good=False)
        rows += stat_row("SoT rivales / p",        prof_l["opp_sot_pg"],  prof_v["opp_sot_pg"],  higher_good=False)
        rows += stat_row("Faltas cometidas / p",   prof_l["fouls_pg"],    prof_v["fouls_pg"],    higher_good=False)
        rows += stat_row("Tarjetas amarillas / p", prof_l["yellows_pg"],  prof_v["yellows_pg"],  higher_good=False)
        rows += stat_row("% Duelos aéreos",        prof_l["aerials_won_pct"], prof_v["aerials_won_pct"], fmt="{:.1f}%")
        if rows.strip(): st.markdown(rows, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Probabilidades ────────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Probabilidades y mercados</div>', unsafe_allow_html=True)
    picks = evaluate_1x2(markets, m_l, m_e, m_v, kelly_fraction,
                         st.session_state.banca_actual,
                         name_l=local[:14], name_v=visita[:14])
    pb_col, mkt_col = st.columns([3, 2])
    with pb_col:
        COLORS = {"local": "#4f46e5", "empate": "#78716c", "visita": "#f59e0b"}
        bars = [
            (f"🏠 {local[:14]}", markets["p_l"], "#4f46e5",  picks[0].get("vig_free_impl",0)),
            ("🤝 Empate",         markets["p_e"], "#78716c", picks[1].get("vig_free_impl",0)),
            (f"✈️ {visita[:14]}", markets["p_v"], "#f59e0b", picks[2].get("vig_free_impl",0)),
        ]
        for label, prob, color, vf_impl in bars:
            st.markdown(prob_bar(label, prob, color, vf_impl), unsafe_allow_html=True)
    with mkt_col:
        st.markdown(markets_row(markets), unsafe_allow_html=True)

    with st.expander("Double Chance · Hándicap Asiático"):
        st.markdown(dc_row(markets), unsafe_allow_html=True)
    with st.expander("Marcadores exactos"):
        st.markdown(exact_scores_row(markets), unsafe_allow_html=True)

    # ── Valor esperado ────────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Valor esperado</div>', unsafe_allow_html=True)
    st.markdown(picks_row(picks), unsafe_allow_html=True)

    ou_picks   = []
    btts_picks = []

    with st.expander("➕ Over / Under"):
        oc1, oc2, oc3 = st.columns(3)
        ou_line = oc1.selectbox("Línea", [1.5, 2.5, 3.5], index=1, key=f"an_ou_line_{active_key}")
        ou_line_val = float(momios.get("linea_ou", 2.5) or 2.5)
        ou_over_def  = float(momios.get("m_over",  1.90) or 1.90)
        ou_under_def = float(momios.get("m_under", 1.90) or 1.90)
        m_over  = oc2.number_input("Over",  value=ou_over_def,  format="%.2f", min_value=1.01, key=f"an_over_{active_key}")
        m_under = oc3.number_input("Under", value=ou_under_def, format="%.2f", min_value=1.01, key=f"an_under_{active_key}")
        from core.value import evaluate_ou
        ou_picks = evaluate_ou(markets, ou_line, m_over, m_under,
                               kelly_fraction, st.session_state.banca_actual)
        st.markdown(picks_row(ou_picks), unsafe_allow_html=True)

    with st.expander("🎯 BTTS"):
        bc1, bc2 = st.columns(2)
        bts_def = float(momios.get("m_btts_si", 1.80) or 1.80)
        btn_def = float(momios.get("m_btts_no", 1.95) or 1.95)
        m_bts = bc1.number_input("BTTS Sí", value=bts_def, format="%.2f", min_value=1.01, key=f"an_bts_{active_key}")
        m_btn = bc2.number_input("BTTS No", value=btn_def, format="%.2f", min_value=1.01, key=f"an_btn_{active_key}")
        btts_picks = [
            evaluate_pick("BTTS Sí", markets["btts"],    m_bts, kelly_fraction, st.session_state.banca_actual),
            evaluate_pick("BTTS No", markets["no_btts"], m_btn, kelly_fraction, st.session_state.banca_actual),
        ]
        st.markdown(picks_row(btts_picks), unsafe_allow_html=True)

    # ── Agregar a jornada ─────────────────────────────────────────────────────
    all_picks = picks + ou_picks + btts_picks
    labels    = [f"{p['name']} (EV: {p['ev']:+.1f}%)" for p in all_picks]

    pa1, pa2 = st.columns([3, 1])
    with pa1:
        pick_idx = st.selectbox("Pick a agregar", range(len(all_picks)),
                                format_func=lambda i: labels[i], key=f"an_pick_{active_key}")
    with pa2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("＋ Agregar", use_container_width=True, key="an_add"):
            chosen = all_picks[pick_idx]
            st.session_state.jornada_pendientes.append({
                "partido": active_key,
                "pick":    chosen["name"],
                "momio":   chosen["momio"],
                "stake":   round(chosen["stake"], 2),
                "ev":      round(chosen["ev"], 2),
                "prob":    round(chosen["prob"] * 100, 1),
                "edge":    round(chosen["edge"], 1),
                "estado":  "Pendiente",
            })
            st.rerun()

except Exception as e:
    st.error(f"Error en el análisis: {e}")
    st.caption("Asegúrate de tener tablas FBRef cargadas en la Página 1.")

# ── Parlay ────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Parlay</div>', unsafe_allow_html=True)

with st.expander("🔗 Armar Parlay (combinada de 2-3 picks)"):
    st.caption("Selecciona picks de distintos partidos. La app calcula prob combinada y EV del parlay.")

    from data.session import get_all_pending_matches
    all_pending_pl = get_all_pending_matches()
    parlay_opts = {}
    for pm in all_pending_pl:
        if not pm["has_momios"]: continue
        pm_momios = pm["momios"]
        pm_dm = get_data_master(pm["league"])
        try:
            from data.profile import build_team_profile, calc_lambdas
            from core.poisson import calc_all_markets
            pf_l = build_team_profile(pm["home"], pm_dm, pm["league"])
            pf_v = build_team_profile(pm["away"], pm_dm, pm["league"])
            ll, lv = calc_lambdas(pf_l, pf_v, pm["league"])
            pm_mkts = calc_all_markets(ll, lv)
            picks_list = []
            if pm_momios.get("m_l",0) > 1:
                picks_list.append((pm["home"][:14], pm_mkts["p_l"], pm_momios["m_l"]))
            if pm_momios.get("m_e",0) > 1:
                picks_list.append(("Empate", pm_mkts["p_e"], pm_momios["m_e"]))
            if pm_momios.get("m_v",0) > 1:
                picks_list.append((pm["away"][:14], pm_mkts["p_v"], pm_momios["m_v"]))
            if pm_momios.get("m_over",0) > 1:
                linea = pm_momios.get("linea_ou", 2.5)
                picks_list.append(("Over " + str(linea), pm_mkts.get("over25",0), pm_momios["m_over"]))
            if pm_momios.get("m_under",0) > 1:
                linea = pm_momios.get("linea_ou", 2.5)
                picks_list.append(("Under " + str(linea), pm_mkts.get("under25",0), pm_momios["m_under"]))
            if picks_list:
                parlay_opts[pm["key"]] = picks_list
        except Exception:
            continue

    if len(parlay_opts) < 2:
        st.info("Necesitas momios en al menos 2 partidos para armar un parlay.")
    else:
        n_legs = st.radio("Selecciones", [2, 3], horizontal=True, key="pl_legs")
        legs = []
        for i in range(n_legs):
            lc1, lc2 = st.columns([3, 2])
            with lc1:
                part_sel = st.selectbox("Partido " + str(i+1),
                                        list(parlay_opts.keys()),
                                        key="pl_partido_" + str(i))
            with lc2:
                opt_picks = parlay_opts[part_sel]
                pl_labels = [p[0] + " @" + str(round(p[2],2)) + " (" + str(round(p[1]*100,0)) + "%)" for p in opt_picks]
                pi = st.selectbox("Pick", range(len(pl_labels)),
                                  format_func=lambda x: pl_labels[x],
                                  key="pl_pick_" + str(i))
                legs.append(opt_picks[pi])

        if legs:
            prob_comb  = 1.0
            momio_comb = 1.0
            for _, prob, momio in legs:
                prob_comb  *= prob
                momio_comb *= momio

            ev_pl = (prob_comb * momio_comb - 1) * 100
            b_val = momio_comb - 1
            kelly_pl = max(0.0, (prob_comb * b_val - (1 - prob_comb)) / b_val) if b_val > 0 else 0.0
            kelly_fr  = st.session_state.get("an_kelly", 0.25)
            stake_pl  = min(kelly_pl * kelly_fr, 0.05)
            monto_pl  = round(st.session_state.banca_actual * stake_pl, 2)

            ev_color = "#16a34a" if ev_pl > 0 else "#dc2626"
            summary = (
                "**Prob combinada:** " + str(round(prob_comb*100,1)) + "%  ·  "
                "**Momio combinado:** @" + str(round(momio_comb,2)) + "  ·  "
                "**EV:** " + ("+" if ev_pl>=0 else "") + str(round(ev_pl,1)) + "%  ·  "
                "**Stake:** $" + str(monto_pl)
            )
            st.markdown(summary)

            if ev_pl > 0:
                if st.button("＋ Agregar parlay a jornada", key="pl_add"):
                    picks_str = " + ".join(l[0] + "@" + str(round(l[2],2)) for l in legs)
                    st.session_state.jornada_pendientes.append({
                        "partido": " | ".join(l[0] for l in legs),
                        "pick":    "PARLAY: " + picks_str,
                        "momio":   round(momio_comb, 2),
                        "stake":   monto_pl,
                        "ev":      round(ev_pl, 2),
                        "prob":    round(prob_comb * 100, 1),
                        "edge":    0.0,
                        "estado":  "Pendiente",
                    })
                    st.rerun()
            else:
                st.warning("EV negativo — este parlay no tiene valor matemático con los parámetros actuales.")

# ── Jornada activa ─────────────────────────────────────────────────────────────
if st.session_state.jornada_pendientes:
    st.markdown('<div class="sec-label">Jornada activa</div>', unsafe_allow_html=True)
    total_exp = sum(a["stake"] for a in st.session_state.jornada_pendientes)
    st.caption(f"{len(st.session_state.jornada_pendientes)} apuesta(s)  ·  Exposición: {fmt_money(total_exp)}")

    for i, ap in enumerate(st.session_state.jornada_pendientes):
        col_row, col_del = st.columns([11, 1])
        with col_row:
            st.markdown(jornada_row(ap), unsafe_allow_html=True)
        with col_del:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"an_del_{i}"):
                st.session_state.jornada_pendientes.pop(i)
                st.rerun()

    with st.expander("💰 Registrar resultado"):
        idx = st.selectbox("Partido", range(len(st.session_state.jornada_pendientes)),
                           format_func=lambda i: st.session_state.jornada_pendientes[i]["partido"],
                           key="an_res_idx")
        resultado = st.radio("Resultado", ["GANADA","PERDIDA"], horizontal=True)
        if st.button("✅ Confirmar"):
            ap  = st.session_state.jornada_pendientes[idx]
            won = resultado == "GANADA"
            st.session_state.banca_actual = update_bankroll(
                st.session_state.banca_actual, ap["stake"], ap["momio"], won)
            ganancia = ap["stake"]*(ap["momio"]-1) if won else -ap["stake"]
            st.session_state.historial.append({**ap, "estado":resultado, "resultado":round(ganancia,2)})
            st.session_state.jornada_pendientes.pop(idx)
            st.rerun()

# ── H2H Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown('<p style="font-size:0.62rem;font-weight:600;color:#44403c;text-transform:uppercase;letter-spacing:0.10em;">Kelly</p>', unsafe_allow_html=True)
    kelly_fraction = st.slider("Kelly", 0.05, 1.0, 0.25, step=0.05,
                               label_visibility="collapsed", key="an_kelly")
    st.caption(f"Kelly ×{kelly_fraction:.2f}")

    st.markdown("---")
    st.markdown('<p style="font-size:0.62rem;font-weight:600;color:#44403c;text-transform:uppercase;letter-spacing:0.10em;">Head to Head</p>', unsafe_allow_html=True)
    if active_key:
        st.caption(f"Para: {active_key}")
    raw_h2h = st.text_area("H2H", key="an_h2h", height=70, label_visibility="collapsed",
                            placeholder="Pega H2H de FBRef…")
    if raw_h2h:
        h2h_data = parse_h2h(raw_h2h)
        if h2h_data and active_key:
            if "h2h_store" not in st.session_state:
                st.session_state.h2h_store = {}
            st.session_state.h2h_store[active_key] = h2h_data
            st.markdown('<div class="tbl-loaded">✓ H2H cargado</div>', unsafe_allow_html=True)
        elif h2h_data:
            st.markdown('<div class="tbl-loaded">✓ H2H cargado</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="tbl-empty">sin datos</div>', unsafe_allow_html=True)