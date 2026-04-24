"""
ui/sections.py
Secciones principales de la app (01 a 06).
Cada función recibe los datos que necesita y renderiza su sección.
"""
import streamlit as st
import pandas as pd

from data.parser import get_squad_list
from data.profile import build_team_profile, calc_lambdas, blend_label
from data.leagues import get_league
from core.poisson import calc_all_markets
from core.value import evaluate_1x2, evaluate_ou, remove_vig, overround
from core.kelly import update_bankroll
from ui.components import (
    fmt_money, prob_bar, markets_row, dc_row, exact_scores_row,
    picks_row, stat_row, team_header, lam_info, vig_info, jornada_row,
    pick_card,
)

_NONE = "— seleccionar —"
_COLORS = {"local": "#4f46e5", "empate": "#78716c", "visita": "#f59e0b"}


# ─────────────────────────────────────────────────────────────────────────────
# 01 · ENCUENTRO + MOMIOS
# ─────────────────────────────────────────────────────────────────────────────
def section_encuentro(cfg: dict) -> dict:
    """
    Selector de equipos + momios.
    Retorna dict con: local, visita, m_l, m_e, m_v, prof_l, prof_v, markets, picks_1x2
    o None si no hay equipos seleccionados.
    """
    st.markdown('<div class="sec-label">01 · Encuentro</div>', unsafe_allow_html=True)

    equipos = [_NONE] + get_squad_list(st.session_state.data_master)

    # Pre-seleccionar si viene de click en fixture
    # IMPORTANTE: borrar las keys del selectbox para forzar el nuevo index
    pre_home = st.session_state.pop('selected_home', None)
    pre_away = st.session_state.pop('selected_away', None)
    if pre_home is not None:
        # Forzar nuevos valores borrando el estado previo de los selectbox
        for k in ['local_sel', 'visita_sel']:
            if k in st.session_state:
                del st.session_state[k]
        st.session_state['_pre_home'] = pre_home
        st.session_state['_pre_away'] = pre_away

    # Leer pre-selección guardada y limpiarla para no persistir
    saved_home = st.session_state.pop('_pre_home', None)
    saved_away = st.session_state.pop('_pre_away', None)
    idx_home = equipos.index(saved_home) if saved_home in equipos else 0
    idx_away = equipos.index(saved_away) if saved_away in equipos else 0

    # Selectores de equipo
    c_l, c_vs, c_v = st.columns([5, 1, 5])
    with c_l:
        local = st.selectbox("Local", equipos, index=idx_home,
                             key="local_sel", label_visibility="collapsed")
    with c_vs:
        st.markdown(
            "<div style='text-align:center;font-size:0.72rem;"
            "color:#a8a29e;font-family:DM Mono,monospace;padding-top:32px;'>vs</div>",
            unsafe_allow_html=True,
        )
    with c_v:
        visita = st.selectbox("Visita", equipos, index=idx_away,
                              key="visita_sel", label_visibility="collapsed")

    lname = local[:14]  if local  != _NONE else "Local"
    vname = visita[:14] if visita != _NONE else "Visita"

    # Momios (inmediatamente debajo)
    st.markdown('<div style="margin-top:4px;"></div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1: m_l = st.number_input(f"Momio {lname}", value=2.00, format="%.2f", min_value=1.01, key="m_l")
    with m2: m_e = st.number_input("Momio Empate",    value=3.00, format="%.2f", min_value=1.01, key="m_e")
    with m3: m_v = st.number_input(f"Momio {vname}", value=3.00, format="%.2f", min_value=1.01, key="m_v")

    # Vig info
    OR    = overround([m_l, m_e, m_v])
    vf    = remove_vig([m_l, m_e, m_v])
    st.markdown(
        vig_info(OR * 100, m_l, m_e, m_v, vf[0]*100, vf[1]*100, vf[2]*100),
        unsafe_allow_html=True,
    )

    if local == _NONE or visita == _NONE:
        return None

    # Perfiles
    league = cfg["league"]
    prof_l = build_team_profile(local,  st.session_state.data_master, league)
    prof_v = build_team_profile(visita, st.session_state.data_master, league)

    # Lambdas
    lam_l, lam_v = calc_lambdas(prof_l, prof_v, league)
    markets = calc_all_markets(lam_l, lam_v)
    picks_1x2 = evaluate_1x2(
        markets, m_l, m_e, m_v,
        cfg["kelly_fraction"], st.session_state.banca_actual,
        name_l=lname, name_v=vname,
    )

    # Lambda info caption
    st.markdown(
        lam_info(lam_l, lam_v, lname, vname,
                 blend_label(prof_l), blend_label(prof_v)),
        unsafe_allow_html=True,
    )
    cfg_league = get_league(league)
    st.caption(
        f"{cfg_league['flag']} {league}  ·  "
        f"Home adv: +{cfg_league['home_adv']:.2f} goles  ·  "
        f"Tablas cargadas: {cfg['tables_loaded']}/9"
    )

    return {
        "local": local, "visita": visita,
        "lname": lname, "vname":  vname,
        "m_l": m_l, "m_e": m_e, "m_v": m_v,
        "prof_l": prof_l, "prof_v": prof_v,
        "lam_l": lam_l, "lam_v": lam_v,
        "markets": markets,
        "picks_1x2": picks_1x2,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 02 · COMPARATIVA DE ESTADÍSTICAS
# ─────────────────────────────────────────────────────────────────────────────
def section_comparativa(ctx: dict):
    prof_l = ctx["prof_l"]
    prof_v = ctx["prof_v"]
    st.markdown('<div class="sec-label">02 · Comparativa de Estadísticas</div>',
                unsafe_allow_html=True)

    # Headers de equipo
    ch_l, ch_v = st.columns(2)
    with ch_l:
        st.markdown(team_header(prof_l, align_right=False), unsafe_allow_html=True)
    with ch_v:
        st.markdown(team_header(prof_v, align_right=True),  unsafe_allow_html=True)

    cc_l, cc_v = st.columns(2)

    # ── Ataque ───────────────────────────────────────────────────────────────
    with cc_l:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="stat-sec">⚽ Ataque</div>', unsafe_allow_html=True)
        rows = ""
        rows += stat_row("Goles / partido",    prof_l["gf_pg"],    prof_v["gf_pg"])
        rows += stat_row("xG / partido",        prof_l["xg_pg"],    prof_v["xg_pg"])
        rows += stat_row("npxG / partido",      prof_l["npxg_pg"],  prof_v["npxg_pg"])
        rows += stat_row("Tiros / partido",     prof_l["sh_pg"],    prof_v["sh_pg"])
        rows += stat_row("SoT / partido",       prof_l["sot_pg"],   prof_v["sot_pg"])
        rows += stat_row("SoT%",                prof_l["sot_pct"],  prof_v["sot_pct"],  fmt="{:.1f}%")
        rows += stat_row("Eficiencia G/Sh",     prof_l["g_sh"],     prof_v["g_sh"],     fmt="{:.3f}")
        if rows.strip():
            st.markdown(rows, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Defensa + Disciplina ─────────────────────────────────────────────────
    with cc_v:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="stat-sec">🛡️ Defensa · Disciplina</div>',
                    unsafe_allow_html=True)
        rows = ""
        rows += stat_row("Goles recibidos / p",   prof_l["ga_pg"],        prof_v["ga_pg"],        higher_good=False)
        rows += stat_row("xGA / partido",          prof_l["xga_pg"],       prof_v["xga_pg"],       higher_good=False)
        rows += stat_row("Tiros rivales / p",      prof_l["opp_sh_pg"],   prof_v["opp_sh_pg"],    higher_good=False)
        rows += stat_row("SoT rivales / p",        prof_l["opp_sot_pg"],  prof_v["opp_sot_pg"],   higher_good=False)
        rows += stat_row("Faltas cometidas / p",   prof_l["fouls_pg"],    prof_v["fouls_pg"],     higher_good=False)
        rows += stat_row("Tarjetas amarillas / p", prof_l["yellows_pg"],  prof_v["yellows_pg"],   higher_good=False)
        rows += stat_row("% Duelos aéreos",        prof_l["aerials_won_pct"], prof_v["aerials_won_pct"], fmt="{:.1f}%")
        if rows.strip():
            st.markdown(rows, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 03 · PROBABILIDADES + MERCADOS
# ─────────────────────────────────────────────────────────────────────────────
def section_probabilidades(ctx: dict):
    markets = ctx["markets"]
    lname   = ctx["lname"]
    vname   = ctx["vname"]
    picks   = ctx["picks_1x2"]

    st.markdown('<div class="sec-label">03 · Probabilidades y Mercados</div>',
                unsafe_allow_html=True)

    pb_col, mkt_col = st.columns([3, 2])

    with pb_col:
        # Barras 1X2 con implícita vig-free
        bars = [
            (f"🏠 {lname}", markets["p_l"], _COLORS["local"],  picks[0].get("vig_free_impl", 0)),
            ("🤝 Empate",   markets["p_e"], _COLORS["empate"], picks[1].get("vig_free_impl", 0)),
            (f"✈️ {vname}", markets["p_v"], _COLORS["visita"], picks[2].get("vig_free_impl", 0)),
        ]
        for label, prob, color, vf_impl in bars:
            st.markdown(prob_bar(label, prob, color, vf_impl), unsafe_allow_html=True)

    with mkt_col:
        st.markdown(markets_row(markets), unsafe_allow_html=True)

    # Double Chance + Asian HDP
    with st.expander("Double Chance · Hándicap Asiático"):
        st.markdown(dc_row(markets), unsafe_allow_html=True)

    # Marcadores exactos
    with st.expander("Marcadores exactos más probables"):
        st.markdown(exact_scores_row(markets), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 04 · VALOR ESPERADO + PICKS
# ─────────────────────────────────────────────────────────────────────────────
def section_picks(ctx: dict, cfg: dict):
    markets = ctx["markets"]
    lname   = ctx["lname"]
    vname   = ctx["vname"]
    picks   = ctx["picks_1x2"]

    st.markdown('<div class="sec-label">04 · Valor Esperado</div>', unsafe_allow_html=True)

    # Cards 1X2
    st.markdown(picks_row(picks), unsafe_allow_html=True)

    # Over/Under con momios
    ou_picks = []
    with st.expander("➕ Analizar Over / Under"):
        ou_cols = st.columns(3)
        with ou_cols[0]: ou_line = st.selectbox("Línea", [1.5, 2.5, 3.5], index=1, key="ou_line")
        with ou_cols[1]: m_over  = st.number_input("Momio Over",  value=1.90, format="%.2f", min_value=1.01, key="m_over")
        with ou_cols[2]: m_under = st.number_input("Momio Under", value=1.90, format="%.2f", min_value=1.01, key="m_under")
        ou_picks = evaluate_ou(
            markets, ou_line, m_over, m_under,
            cfg["kelly_fraction"], st.session_state.banca_actual,
        )
        st.markdown(picks_row(ou_picks), unsafe_allow_html=True)

    # BTTS con momios
    btts_picks = []
    with st.expander("🎯 Analizar BTTS"):
        bc1, bc2 = st.columns(2)
        with bc1: m_btts_si = st.number_input("Momio Sí anotan", value=1.80, format="%.2f", min_value=1.01, key="m_btts_si")
        with bc2: m_btts_no = st.number_input("Momio No anotan", value=1.95, format="%.2f", min_value=1.01, key="m_btts_no")
        from core.value import evaluate_pick
        btts_picks = [
            evaluate_pick("BTTS Sí", markets["btts"],    m_btts_si, cfg["kelly_fraction"], st.session_state.banca_actual),
            evaluate_pick("BTTS No", markets["no_btts"], m_btts_no, cfg["kelly_fraction"], st.session_state.banca_actual),
        ]
        st.markdown(picks_row(btts_picks), unsafe_allow_html=True)

    # Todos los picks disponibles (1X2 + OU + BTTS)
    all_picks = picks + ou_picks + btts_picks
    st.markdown('<div style="margin-top:8px;"></div>', unsafe_allow_html=True)
    all_picks_labels = [f"{p['name']} (EV: {p['ev']:+.1f}%)" for p in all_picks]
    pa1, pa2 = st.columns([3, 1])
    with pa1:
        pick_idx = st.selectbox("Pick a agregar a jornada", range(len(all_picks)),
                                format_func=lambda i: all_picks_labels[i],
                                key="pick_sel")
    with pa2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("＋ Agregar", use_container_width=True):
            chosen = all_picks[pick_idx]
            st.session_state.jornada_pendientes.append({
                "partido": f"{ctx['local']} vs {ctx['visita']}",
                "pick":    chosen["name"],
                "momio":   chosen["momio"],
                "stake":   round(chosen["stake"], 2),
                "ev":      round(chosen["ev"], 2),
                "prob":    round(chosen["prob"] * 100, 1),
                "edge":    round(chosen["edge"], 1),
                "estado":  "Pendiente",
            })
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# 05 · GESTIÓN DE JORNADA
# ─────────────────────────────────────────────────────────────────────────────
def section_jornada():
    if not st.session_state.jornada_pendientes:
        return

    st.markdown('<div class="sec-label">05 · Jornada Activa</div>', unsafe_allow_html=True)

    total_exp = sum(a["stake"] for a in st.session_state.jornada_pendientes)
    st.caption(
        f"{len(st.session_state.jornada_pendientes)} apuesta(s)  ·  "
        f"Exposición total: {fmt_money(total_exp)}"
    )

    # Inicializar estado de edición
    if "edit_idx" not in st.session_state:
        st.session_state.edit_idx = None

    # Filas de jornada con botón eliminar
    for i, ap in enumerate(st.session_state.jornada_pendientes):
        col_row, col_del = st.columns([11, 1])
        with col_row:
            # Click en el partido abre editor
            st.markdown(jornada_row(ap), unsafe_allow_html=True)
        with col_del:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_{i}", help="Eliminar apuesta"):
                st.session_state.jornada_pendientes.pop(i)
                if st.session_state.edit_idx == i:
                    st.session_state.edit_idx = None
                st.rerun()

    # Editor inline — se activa al hacer click en Editar
    with st.expander("✏️ Editar apuesta"):
        if st.session_state.jornada_pendientes:
            edit_idx = st.selectbox(
                "Seleccionar apuesta",
                range(len(st.session_state.jornada_pendientes)),
                format_func=lambda i: f"{st.session_state.jornada_pendientes[i]['partido']} — {st.session_state.jornada_pendientes[i]['pick']}",
                key="edit_sel",
            )
            ap = st.session_state.jornada_pendientes[edit_idx]
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                new_pick = st.text_input("Pick", value=ap["pick"], key="edit_pick")
            with ec2:
                new_momio = st.number_input("Momio", value=float(ap["momio"]),
                                            format="%.2f", min_value=1.01, key="edit_momio")
            with ec3:
                new_stake = st.number_input("Stake $", value=float(ap["stake"]),
                                            format="%.2f", min_value=0.01, key="edit_stake")
            if st.button("💾 Guardar cambios", use_container_width=True):
                st.session_state.jornada_pendientes[edit_idx]["pick"]  = new_pick
                st.session_state.jornada_pendientes[edit_idx]["momio"] = new_momio
                st.session_state.jornada_pendientes[edit_idx]["stake"] = new_stake
                st.rerun()

    with st.expander("💰 Registrar resultado"):
        idx = st.selectbox(
            "Partido",
            range(len(st.session_state.jornada_pendientes)),
            format_func=lambda i: st.session_state.jornada_pendientes[i]["partido"],
            key="jornada_idx",
        )
        resultado = st.radio("Resultado", ["GANADA", "PERDIDA"], horizontal=True)
        if st.button("✅ Confirmar"):
            ap  = st.session_state.jornada_pendientes[idx]
            won = resultado == "GANADA"
            st.session_state.banca_actual = update_bankroll(
                st.session_state.banca_actual, ap["stake"], ap["momio"], won
            )
            ganancia = ap["stake"] * (ap["momio"] - 1) if won else -ap["stake"]
            st.session_state.historial.append({
                **ap, "estado": resultado, "resultado": round(ganancia, 2),
            })
            st.session_state.jornada_pendientes.pop(idx)
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# 06 · HISTORIAL
# ─────────────────────────────────────────────────────────────────────────────
def section_historial():
    if not st.session_state.historial:
        return

    st.markdown('<div class="sec-label">06 · Historial</div>', unsafe_allow_html=True)

    df = pd.DataFrame(st.session_state.historial)
    ganadas  = (df["estado"] == "GANADA").sum()
    perdidas = (df["estado"] == "PERDIDA").sum()
    total    = ganadas + perdidas
    pl_total = df["resultado"].sum()
    avg_odds = df["momio"].mean()
    yield_pct = (pl_total / df["stake"].sum() * 100) if df["stake"].sum() > 0 else 0

    h1, h2, h3, h4, h5 = st.columns(5)
    h1.metric("Apuestas",  total)
    h2.metric("Ganadas",   ganadas)
    h3.metric("% Acierto", f"{ganadas/total*100:.0f}%" if total else "—")
    h4.metric("Yield",     f"{yield_pct:.1f}%")
    h5.metric("P&L",       fmt_money(pl_total), delta=f"{pl_total:+.2f}")

    # Tabla con color en estado
    def color_estado(v):
        if v == "GANADA":  return "color: #16a34a; font-weight: 600"
        if v == "PERDIDA": return "color: #dc2626; font-weight: 600"
        return ""

    def color_resultado(v):
        return "color: #16a34a" if v > 0 else "color: #dc2626"

    cols_show = ["partido", "pick", "momio", "stake", "ev", "estado", "resultado"]
    cols_show = [c for c in cols_show if c in df.columns]

    st.dataframe(
        df[cols_show].style
            .applymap(color_estado,    subset=["estado"])
            .applymap(color_resultado, subset=["resultado"])
            .format({"stake": "${:.2f}", "resultado": "${:+.2f}",
                     "momio": "{:.2f}", "ev": "{:+.1f}%"}),
        use_container_width=True,
        hide_index=True,
    )

    if st.button("🗑️ Borrar historial"):
        st.session_state.historial = []
        st.rerun()