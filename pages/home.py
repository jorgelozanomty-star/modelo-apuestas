"""
Intelligence Pro — pages/home.py  v4.1
Dashboard principal: estado de la semana, pipeline, bankroll, picks activos.
"""
import streamlit as st
from ui.styles import inject_styles
from ui.components import (
    bankroll_sidebar, pipeline_steps, next_action_cta,
    auto_save_indicator, section_header, safe_key,
    signal_class, signal_emoji,
)
from data.leagues import LEAGUES, LEAGUE_NAMES


def render():
    inject_styles()

    with st.sidebar:
        bankroll_sidebar()
        st.divider()
        auto_save_indicator()

    ss = st.session_state

    st.markdown(
        '<h1 style="margin-bottom:4px">Intelligence Pro</h1>'
        '<p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:20px">'
        'Modelo Poisson · Kelly fraccionado · xG Blend</p>',
        unsafe_allow_html=True,
    )

    pipeline_steps()
    next_action_cta()

    fbref_data   = ss.get("fbref_data", {})
    fixtures_data = ss.get("fixtures_data", {})
    momios_data  = ss.get("momios_data", {})

    n_ligas    = sum(1 for v in fbref_data.values() if v)
    n_fixtures = sum(len(v) for v in fixtures_data.values() if v)
    n_momios   = sum(
        1 for lp in momios_data.values()
        for p in (lp.values() if isinstance(lp, dict) else []) if p
    )
    picks = ss.get("jornada_activa", [])

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, n_ligas,    "Ligas cargadas"),
        (c2, n_fixtures, "Partidos fixtures"),
        (c3, n_momios,   "Con momios"),
        (c4, len(picks), "Picks jornada"),
    ]:
        col.markdown(
            f'<div class="big-number">{val}</div>'
            f'<div class="big-number-label">{label}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(("<hr>").strip(), unsafe_allow_html=True)

    if picks:
        section_header("🎯 Picks de esta jornada", len(picks))
        bankroll = ss.get("bankroll", 1000)
        for pick in picks:
            ev   = pick.get("ev", 0)
            prob = pick.get("prob", 0)
            edge = pick.get("edge", 0)
            sig  = signal_class(ev, prob, edge)
            emoji = signal_emoji(sig)
            ca, cb, cc, cd = st.columns([1, 4, 2, 2])
            ca.markdown(f'<div style="font-size:1.2rem;padding:8px 0">{emoji}</div>', unsafe_allow_html=True)
            cb.markdown(
                f'<div style="font-weight:600;font-size:0.85rem;padding:8px 0">'
                f'{pick.get("partido","?")} — {pick.get("mercado","?")}</div>',
                unsafe_allow_html=True,
            )
            cc.markdown(
                f'<div style="font-family:var(--font-mono);font-size:0.9rem;padding:8px 0;font-weight:600">'
                f'{pick.get("momio",0):.2f}</div>',
                unsafe_allow_html=True,
            )
            cd.markdown(
                f'<div style="font-family:var(--font-mono);font-size:0.85rem;padding:8px 0">'
                f'${pick.get("stake",0):.0f} MXN</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown("""
        <div style="text-align:center;padding:32px 20px;background:var(--surface);
             border:1px dashed var(--border);border-radius:var(--radius);margin-top:16px">
            <div style="font-size:2rem;margin-bottom:8px">🎯</div>
            <div style="font-family:var(--font-display);font-size:1.1rem;
                 font-weight:600;color:var(--text);margin-bottom:6px">
                No tienes picks esta jornada
            </div>
            <div style="font-size:0.82rem;color:var(--text-muted)">
                Carga ligas y momios, luego ve a Análisis para elegir tus bets 🟢
            </div>
        </div>
        """, unsafe_allow_html=True)

    historial = ss.get("historial", [])
    recientes = [b for b in historial if b.get("resultado") is not None][-5:]
    if recientes:
        st.markdown(("<hr>").strip(), unsafe_allow_html=True)
        section_header("📈 Últimas 5 apuestas")
        ganadas = sum(1 for b in recientes if b.get("resultado") == "ganada")
        profit  = sum(b.get("ganancia", 0) for b in recientes)
        r1, r2, r3 = st.columns(3)
        r1.metric("Acierto reciente", f"{ganadas/len(recientes)*100:.0f}%", f"{ganadas}/{len(recientes)}")
        r2.metric("P&L últimas 5", f"${profit:+.0f}")
        r3.metric("Racha", _racha_str(historial))
        for b in reversed(recientes):
            res = b.get("resultado", "")
            icon = "✅" if res == "ganada" else "❌" if res == "perdida" else "↩️"
            st.markdown(
                f'<div class="pick-row">'
                f'<span style="font-size:.9rem">{icon}</span>'
                f'<span class="pick-market">{b.get("partido","?")} · {b.get("mercado","?")}</span>'
                f'<span class="pick-stake">${b.get("ganancia",0):+.0f}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _racha_str(historial):
    resueltos = [b for b in reversed(historial) if b.get("resultado")]
    if not resueltos:
        return "—"
    ultimo = resueltos[0]["resultado"]
    racha  = sum(1 for b in resueltos if b["resultado"] == ultimo and resueltos.index(b) == 0
                 or b["resultado"] == ultimo)
    # simplificado
    count = 0
    for b in resueltos:
        if b["resultado"] == ultimo:
            count += 1
        else:
            break
    emoji = "🔥" if ultimo == "ganada" else "❄️"
    return f"{emoji} {count}{'G' if ultimo == 'ganada' else 'P'}"

render()
