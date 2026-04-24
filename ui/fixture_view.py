"""
ui/fixture_view.py
Vista de jornada: lista de partidos detectados automáticamente.
Click en un partido → precarga los equipos en el analizador.
"""
import streamlit as st
from datetime import date, datetime

from data.fixtures import (
    parse_fixtures, parse_h2h,
    get_current_gameweek, get_gameweek_matches,
)
from data.parser import get_squad_list


_DAYS_ES = {
    'Monday': 'Lun', 'Tuesday': 'Mar', 'Wednesday': 'Mié',
    'Thursday': 'Jue', 'Friday': 'Vie', 'Saturday': 'Sáb', 'Sunday': 'Dom',
}


def _day_es(d: date) -> str:
    return _DAYS_ES.get(d.strftime('%A'), d.strftime('%a'))


def _format_date(d: date) -> str:
    return f"{_day_es(d)} {d.day}/{d.month}"


def render_fixtures_sidebar():
    """
    Renderiza las secciones de Fixtures y H2H en el sidebar.
    Retorna dict con los datos cargados.
    """
    with st.sidebar:
        st.markdown("---")
        st.markdown(
            '<p style="font-size:0.62rem;font-weight:600;color:#44403c;'
            'text-transform:uppercase;letter-spacing:0.10em;">Fixtures · H2H</p>',
            unsafe_allow_html=True,
        )

        # ── Fixtures ─────────────────────────────────────────────────────────
        with st.expander("📅 Scores & Fixtures"):
            raw_fix = st.text_area(
                "", key="in_fixtures", height=70,
                label_visibility="collapsed",
                placeholder="Pega la tabla Scores & Fixtures de FBRef…",
            )
            if raw_fix:
                df_fix = parse_fixtures(raw_fix)
                if df_fix is not None and len(df_fix) > 0:
                    st.session_state.fixtures_df = df_fix
                    total   = len(df_fix)
                    played  = df_fix['played'].sum()
                    pending = total - played
                    st.markdown(
                        f'<div class="tbl-loaded">✓ {total} partidos · {pending} pendientes</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown('<div class="tbl-empty">sin datos</div>', unsafe_allow_html=True)
            elif 'fixtures_df' in st.session_state and st.session_state.fixtures_df is not None:
                df_fix = st.session_state.fixtures_df
                pending = (~df_fix['played']).sum()
                st.markdown(
                    f'<div class="tbl-loaded">✓ {len(df_fix)} partidos · {pending} pendientes (cargada)</div>',
                    unsafe_allow_html=True,
                )

        # ── H2H ──────────────────────────────────────────────────────────────
        with st.expander("⚔️ Head to Head"):
            match_key = st.session_state.get('h2h_match_key', '')
            if match_key:
                st.caption(f"Para: {match_key.replace('_', ' vs ')}")
            raw_h2h = st.text_area(
                "", key="in_h2h", height=70,
                label_visibility="collapsed",
                placeholder="Pega la tabla H2H de FBRef…",
            )
            if raw_h2h:
                h2h_data = parse_h2h(raw_h2h)
                if h2h_data:
                    # Guardar H2H por partido
                    if 'h2h_store' not in st.session_state:
                        st.session_state.h2h_store = {}
                    key = match_key or 'general'
                    st.session_state.h2h_store[key] = h2h_data
                    st.session_state.h2h_data = h2h_data
                    st.markdown(
                        f'<div class="tbl-loaded">✓ {h2h_data["total_matches"]} partidos H2H</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown('<div class="tbl-empty">sin datos</div>', unsafe_allow_html=True)
            elif 'h2h_data' in st.session_state and st.session_state.h2h_data:
                h2h = st.session_state.h2h_data
                st.markdown(
                    f'<div class="tbl-loaded">✓ {h2h["total_matches"]} partidos H2H (cargado)</div>',
                    unsafe_allow_html=True,
                )


def render_jornada_view() -> dict | None:
    """
    Muestra la lista de partidos de la jornada actual.
    Retorna dict con {home, away} si el usuario seleccionó un partido,
    o None si no hay fixtures cargados.
    """
    fixtures_df = st.session_state.get('fixtures_df', None)
    if fixtures_df is None or len(fixtures_df) == 0:
        return None

    today = date.today()
    current_wk = get_current_gameweek(fixtures_df, today)
    matches     = get_gameweek_matches(fixtures_df, current_wk, today)

    if len(matches) == 0:
        return None

    # Selector de jornada manual
    all_wks = sorted(fixtures_df['wk'].dropna().unique().astype(int).tolist())
    st.markdown('<div class="sec-label">00 · Jornada</div>', unsafe_allow_html=True)

    wk_col, info_col = st.columns([2, 5])
    with wk_col:
        selected_wk = st.selectbox(
            "Jornada", all_wks,
            index=all_wks.index(current_wk) if current_wk in all_wks else 0,
            key="wk_selector",
            label_visibility="collapsed",
        )
    with info_col:
        pending_count = (~matches['played']).sum()
        min_date = matches['date'].min()
        max_date = matches['date'].max()
        st.markdown(
            f'<div class="lam-info" style="margin-top:6px;">'
            f'Jornada {selected_wk}  ·  '
            f'{_format_date(min_date)}{"" if min_date == max_date else f" – {_format_date(max_date)}"}  ·  '
            f'{pending_count} partido(s) pendiente(s)'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Si cambió la jornada seleccionada, actualizar
    if selected_wk != current_wk:
        matches = get_gameweek_matches(fixtures_df, selected_wk, today)

    # Lista de partidos
    squads_available = set(get_squad_list(st.session_state.get('data_master', {})))
    selected_match = None

    for _, row in matches.iterrows():
        home  = row['home']
        away  = row['away']
        played = row['played']
        score  = row.get('score', None)
        d      = row['date']

        # Color de fondo según estado
        if played:
            bg = "#fafaf9"; border = "#e7e5e0"; opacity = "0.6"
        elif d == today:
            bg = "#fffbeb"; border = "#fcd34d"; opacity = "1"
        else:
            bg = "#ffffff"; border = "#e7e5e0"; opacity = "1"

        # Indicador de datos disponibles
        home_ok = "🟢" if home in squads_available else "⚪"
        away_ok = "🟢" if away in squads_available else "⚪"

        score_txt = f"<b>{score}</b>" if (score and str(score) != 'nan') else _format_date(d)

        col_match, col_btn = st.columns([5, 1])
        with col_match:
            st.markdown(
                f'<div style="background:{bg};border:1px solid {border};'
                f'border-radius:8px;padding:10px 14px;margin-bottom:6px;opacity:{opacity};">'
                f'<span style="font-size:0.82rem;font-weight:600;color:#1c1917;">'
                f'{home_ok} {home}</span>'
                f'<span style="font-size:0.72rem;color:#a8a29e;font-family:DM Mono,monospace;'
                f'margin:0 10px;">{score_txt}</span>'
                f'<span style="font-size:0.82rem;font-weight:600;color:#1c1917;">'
                f'{away} {away_ok}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_btn:
            if not played:
                if st.button("→", key=f"sel_{home}_{away}_{d}",
                             help=f"Analizar {home} vs {away}"):
                    selected_match = {'home': home, 'away': away}

    if selected_match:
        # Guardar en session_state para que section_encuentro los precargue
        st.session_state['selected_home'] = selected_match['home']
        st.session_state['selected_away'] = selected_match['away']
        # Limpiar H2H del partido anterior
        st.session_state['h2h_data'] = None
        st.session_state['h2h_match_key'] = f"{selected_match['home']}_{selected_match['away']}"
        st.rerun()

    return None


def render_h2h_card(home: str = '', away: str = ''):
    """
    Muestra la card de H2H si hay datos para el partido actual.
    Busca primero en h2h_store por el par home_away, luego usa h2h_data.
    """
    h2h = None
    # Buscar H2H específico del partido actual
    if home and away:
        store = st.session_state.get('h2h_store', {})
        key1 = f"{home}_{away}"
        key2 = f"{away}_{home}"
        h2h = store.get(key1) or store.get(key2)
    # Fallback al H2H global cargado
    if not h2h:
        h2h = st.session_state.get('h2h_data', None)
    if not h2h:
        return

    st.markdown(
        f"""<div class="card" style="margin-top:8px;">
        <div class="stat-sec">⚔️ Head to Head — últimos {h2h['total_matches']} partidos</div>
        <div style="display:flex;gap:8px;margin:8px 0;">
            <div class="mkt-pill" style="flex:1;">
                <div class="mkt-val" style="color:#4f46e5;">{h2h['home_wins']}</div>
                <div class="mkt-lbl">Local gana</div>
            </div>
            <div class="mkt-pill" style="flex:1;">
                <div class="mkt-val" style="color:#78716c;">{h2h['draws']}</div>
                <div class="mkt-lbl">Empates</div>
            </div>
            <div class="mkt-pill" style="flex:1;">
                <div class="mkt-val" style="color:#f59e0b;">{h2h['away_wins']}</div>
                <div class="mkt-lbl">Visita gana</div>
            </div>
            <div class="mkt-pill" style="flex:1;">
                <div class="mkt-val">{h2h['avg_goals']}</div>
                <div class="mkt-lbl">Goles/p</div>
            </div>
            <div class="mkt-pill" style="flex:1;">
                <div class="mkt-val" style="color:#16a34a;">{h2h['over25_pct']}%</div>
                <div class="mkt-lbl">Over 2.5</div>
            </div>
            <div class="mkt-pill" style="flex:1;">
                <div class="mkt-val" style="color:#7c3aed;">{h2h['btts_pct']}%</div>
                <div class="mkt-lbl">BTTS</div>
            </div>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )
