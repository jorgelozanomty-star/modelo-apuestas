"""
ui/sidebar.py
Sidebar: Bankroll, Kelly slider y Data Hub (9 tablas FBRef).
"""
import streamlit as st
from data.parser import process_fbref_paste, get_squad_list
from data.leagues import LEAGUE_NAMES
from core.kelly import roi_pct, update_bankroll
from ui.components import fmt_money

TABLES = [
    ("Tabla General",     "🏆"),
    ("Standard Squad",    "⚽"),
    ("Standard Opp",      "🛡️"),
    ("Shooting Squad",    "🎯"),
    ("Shooting Opp",      "🎯"),
    ("PlayingTime Squad", "⏱️"),
    ("PlayingTime Opp",   "⏱️"),
    ("Misc Squad",        "📋"),
    ("Misc Opp",          "📋"),
]


def render_sidebar() -> dict:
    """
    Renderiza el sidebar completo.
    Retorna dict con los valores de configuración activos:
    {
        'kelly_fraction': float,
        'league': str,
        'tables_loaded': int,
    }
    """
    with st.sidebar:
        st.markdown("### ◈ Intelligence Pro")
        st.markdown(
            '<p style="font-size:0.68rem;color:#a8a29e;'
            'font-family:\'DM Mono\',monospace;margin-top:-6px;">'
            'Data Hub · Bankroll · v2.0</p>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # ── Bankroll ────────────────────────────────────────────────────────
        r = roi_pct(st.session_state.banca_actual, st.session_state.banca_inicial)
        roi_cls = "roi-pos" if r > 0 else ("roi-neg" if r < 0 else "roi-neu")
        st.markdown(
            f"""<div class="banca-box">
                <div class="banca-lbl">Banca Actual</div>
                <div class="banca-val">{fmt_money(st.session_state.banca_actual)}</div>
                <div class="banca-roi {roi_cls}">ROI: {r:+.2f}%</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Ajuste manual de banca
        nueva_banca = st.number_input(
            "Ajustar banca",
            value=float(st.session_state.banca_actual),
            format="%.2f",
            label_visibility="collapsed",
            key="banca_input",
        )
        if abs(nueva_banca - st.session_state.banca_actual) > 0.01:
            st.session_state.banca_actual = nueva_banca
            st.rerun()

        # ── Kelly ────────────────────────────────────────────────────────────
        st.markdown(
            '<p style="font-size:0.62rem;color:#a8a29e;'
            'text-transform:uppercase;letter-spacing:0.10em;'
            'font-family:\'DM Mono\',monospace;margin:10px 0 2px 0;">'
            'Fracción Kelly</p>',
            unsafe_allow_html=True,
        )
        kelly_fraction = st.slider(
            "Kelly", 0.05, 1.0, 0.25, step=0.05,
            label_visibility="collapsed",
        )
        st.caption(f"Kelly ×{kelly_fraction:.2f}  ·  stake máx = {kelly_fraction*100:.0f}% de banca")

        # ── Liga ─────────────────────────────────────────────────────────────
        st.markdown(
            '<p style="font-size:0.62rem;color:#a8a29e;'
            'text-transform:uppercase;letter-spacing:0.10em;'
            'font-family:\'DM Mono\',monospace;margin:10px 0 2px 0;">'
            'Liga</p>',
            unsafe_allow_html=True,
        )
        league = st.selectbox(
            "Liga", LEAGUE_NAMES,
            label_visibility="collapsed",
            key="league_sel",
        )

        # ── Limpiar jornada ───────────────────────────────────────────────────
        if st.button("🗑️ Limpiar jornada", use_container_width=True):
            st.session_state.jornada_pendientes = []
            st.rerun()

        st.markdown("---")

        # ── Guardar / Cargar sesión ───────────────────────────────────────────
        st.markdown(
            '<p style="font-size:0.62rem;font-weight:600;color:#44403c;'            'text-transform:uppercase;letter-spacing:0.10em;">Sesión</p>',
            unsafe_allow_html=True,
        )

        # Exportar
        import json, datetime
        session_data = {
            "version":            "2.0",
            "exported_at":        datetime.datetime.now().isoformat(),
            "banca_actual":       st.session_state.banca_actual,
            "banca_inicial":      st.session_state.banca_inicial,
            "jornada_pendientes": st.session_state.jornada_pendientes,
            "historial":          st.session_state.historial,
        }
        st.download_button(
            label="⬇️ Exportar sesión",
            data=json.dumps(session_data, ensure_ascii=False, indent=2),
            file_name=f"intelligence_pro_{datetime.date.today()}.json",
            mime="application/json",
            use_container_width=True,
        )

        # Importar
        uploaded = st.file_uploader(
            "⬆️ Cargar sesión", type="json",
            label_visibility="collapsed",
            key="session_upload",
        )
        if uploaded is not None:
            try:
                data = json.load(uploaded)
                st.session_state.banca_actual       = float(data.get("banca_actual",       1000.0))
                st.session_state.banca_inicial      = float(data.get("banca_inicial",      1000.0))
                st.session_state.jornada_pendientes = data.get("jornada_pendientes", [])
                st.session_state.historial          = data.get("historial",          [])
                st.success("✓ Sesión restaurada")
                st.rerun()
            except Exception as e:
                st.error(f"Error al cargar: {e}")

        st.markdown("---")

        # ── Data Hub ──────────────────────────────────────────────────────────
        st.markdown(
            '<p style="font-size:0.62rem;font-weight:600;color:#44403c;'
            'text-transform:uppercase;letter-spacing:0.10em;">Tablas FBRef</p>',
            unsafe_allow_html=True,
        )

        tables_loaded = 0
        for nombre, icon in TABLES:
            with st.expander(f"{icon} {nombre}"):
                raw = st.text_area(
                    "", key=f"in_{nombre}", height=65,
                    label_visibility="collapsed",
                    placeholder="Pega aquí los datos de FBRef…",
                )
                df_parsed = process_fbref_paste(raw)
                if df_parsed is not None:
                    st.session_state.data_master[nombre] = df_parsed
                    st.markdown(
                        f'<div class="tbl-loaded">✓ {len(df_parsed)} equipos</div>',
                        unsafe_allow_html=True,
                    )
                    tables_loaded += 1
                else:
                    already = nombre in st.session_state.data_master
                    if already:
                        n = len(st.session_state.data_master[nombre])
                        st.markdown(
                            f'<div class="tbl-loaded">✓ {n} equipos (cargada)</div>',
                            unsafe_allow_html=True,
                        )
                        tables_loaded += 1
                    else:
                        st.markdown(
                            '<div class="tbl-empty">sin datos</div>',
                            unsafe_allow_html=True,
                        )

    return {
        "kelly_fraction": kelly_fraction,
        "league":         league,
        "tables_loaded":  tables_loaded,
    }