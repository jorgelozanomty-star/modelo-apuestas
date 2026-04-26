"""
Intelligence Pro — pages/home.py
Dashboard principal: estado de la semana, pipeline, bankroll, picks activos.
"""
import streamlit as st
from ui.styles import inject_styles
from ui.components import (
    bankroll_sidebar, pipeline_steps, next_action_cta,
    auto_save_indicator, section_header, safe_key
)
from data.leagues import LIGAS


def render():
    inject_styles()

    # ── Sidebar ─────────────────────────────────────────────
    with st.sidebar:
        bankroll_sidebar()
        st.divider()
        auto_save_indicator()

    # ── Header ──────────────────────────────────────────────
    ss = st.session_state
    st.markdown(
        '<h1 style="margin-bottom:4px">Intelligence Pro</h1>'
        '<p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:20px">'
        'Modelo Poisson · Kelly fraccionado · xG Blend</p>',
        unsafe_allow_html=True
    )

    # ── Pipeline semanal ─────────────────────────────────────
    pipeline_steps()

    # ── CTA siguiente paso ───────────────────────────────────
    next_action_cta()

    # ── Resumen de ligas ─────────────────────────────────────
    fbref_data = ss.get("fbref_data", {})
    fixtures_data = ss.get("fixtures_data", {})
    momios_data = ss.get("momios_data", {})

    ligas_activas = [k for k, v in fbref_data.items() if v]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        n_ligas = len(ligas_activas)
        st.markdown(
            f'<div class="big-number">{n_ligas}</div>'
            f'<div class="big-number-label">Ligas cargadas</div>',
            unsafe_allow_html=True
        )
    with col2:
        n_fixtures = sum(
            len(v) for k, v in fixtures_data.items() if v
        ) if fixtures_data else 0
        st.markdown(
            f'<div class="big-number">{n_fixtures}</div>'
            f'<div class="big-number-label">Partidos en fixtures</div>',
            unsafe_allow_html=True
        )
    with col3:
        n_momios = 0
        if isinstance(momios_data, dict):
            for liga_partidos in momios_data.values():
                if isinstance(liga_partidos, dict):
                    n_momios += sum(1 for p in liga_partidos.values() if p)
        st.markdown(
            f'<div class="big-number">{n_momios}</div>'
            f'<div class="big-number-label">Partidos con momios</div>',
            unsafe_allow_html=True
        )
    with col4:
        picks = ss.get("jornada_activa", [])
        st.markdown(
            f'<div class="big-number">{len(picks)}</div>'
            f'<div class="big-number-label">Picks esta jornada</div>',
            unsafe_allow_html=True
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Picks activos ───────────────────────────────────────
    picks = ss.get("jornada_activa", [])
    if picks:
        section_header("🎯 Picks de esta jornada", len(picks))

        from ui.components import signal_emoji, signal_class
        for i, pick in enumerate(picks):
            ev = pick.get("ev", 0)
            prob = pick.get("prob", 0)
            edge = pick.get("edge", 0)
            sig = signal_class(ev, prob, edge)
            emoji = signal_emoji(sig)
            stake = pick.get("stake", 0)
            mercado = pick.get("mercado", "—")
            partido = pick.get("partido", "—")

            col_a, col_b, col_c, col_d = st.columns([1, 4, 2, 2])
            with col_a:
                st.markdown(
                    f'<div style="font-size:1.2rem;padding:8px 0">{emoji}</div>',
                    unsafe_allow_html=True
                )
            with col_b:
                st.markdown(
                    f'<div style="font-family:var(--font-ui);font-weight:600;'
                    f'font-size:0.85rem;padding:8px 0">{partido}<br>'
                    f'<span style="font-weight:400;color:var(--text-muted);font-size:0.75rem">'
                    f'{mercado}</span></div>',
                    unsafe_allow_html=True
                )
            with col_c:
                momio = pick.get("momio", 0)
                st.markdown(
                    f'<div style="font-family:var(--font-mono);font-size:0.9rem;'
                    f'padding:8px 0;font-weight:600">{momio:.2f}</div>',
                    unsafe_allow_html=True
                )
            with col_d:
                bankroll = ss.get("bankroll", 1000)
                st.markdown(
                    f'<div style="font-family:var(--font-mono);font-size:0.85rem;'
                    f'padding:8px 0;color:var(--text-2)">${stake:.0f} MXN</div>',
                    unsafe_allow_html=True
                )

        st.markdown("<br>", unsafe_allow_html=True)
        col_reg, col_clear = st.columns([2, 1])
        with col_reg:
            if st.button("📊 Ver análisis completo", use_container_width=True, key="home_goto_analisis"):
                st.switch_page("pages/analisis.py")
    else:
        # Zero state
        st.markdown("""
        <div style="text-align:center;padding:32px 20px;background:var(--surface);
             border:1px dashed var(--border);border-radius:var(--radius);margin-top:16px">
            <div style="font-size:2rem;margin-bottom:8px">🎯</div>
            <div style="font-family:var(--font-display);font-size:1.1rem;
                 font-weight:600;color:var(--text);margin-bottom:6px">
                No tienes picks esta jornada
            </div>
            <div style="font-family:var(--font-ui);font-size:0.82rem;color:var(--text-muted)">
                Carga ligas y momios, luego ve a Análisis para elegir tus bets 🟢
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Historial reciente ──────────────────────────────────
    historial = ss.get("historial", [])
    recientes = [b for b in historial if b.get("resultado") is not None][-5:]

    if recientes:
        st.markdown("<hr>", unsafe_allow_html=True)
        section_header("📈 Últimas 5 apuestas registradas")

        ganadas = sum(1 for b in recientes if b.get("resultado") == "ganada")
        total_r = len(recientes)
        acierto = ganadas / total_r * 100 if total_r else 0

        profit = sum(
            b.get("ganancia", 0) for b in recientes
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Acierto reciente", f"{acierto:.0f}%", f"{ganadas}/{total_r}")
        c2.metric("P&L últimas 5", f"${profit:+.0f}")
        c3.metric("Racha actual", _racha_str(historial))

        for b in reversed(recientes):
            resultado = b.get("resultado", "")
            icon = "✅" if resultado == "ganada" else "❌" if resultado == "perdida" else "↩️"
            st.markdown(
                f'<div class="pick-row">'
                f'<span style="font-size:0.9rem">{icon}</span>'
                f'<span class="pick-market">{b.get("partido","?")} · {b.get("mercado","?")}</span>'
                f'<span class="pick-stake">${b.get("ganancia", 0):+.0f}</span>'
                f'</div>',
                unsafe_allow_html=True
            )


def _racha_str(historial: list) -> str:
    """Calcula racha actual de ganadas/perdidas."""
    if not historial:
        return "—"
    recientes_con_resultado = [
        b for b in reversed(historial) if b.get("resultado") is not None
    ]
    if not recientes_con_resultado:
        return "—"
    ultimo = recientes_con_resultado[0].get("resultado")
    racha = 0
    for b in recientes_con_resultado:
        if b.get("resultado") == ultimo:
            racha += 1
        else:
            break
    emoji = "🔥" if ultimo == "ganada" else "❄️"
    label = "G" if ultimo == "ganada" else "P"
    return f"{emoji} {racha}{label}"
