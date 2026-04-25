"""
main.py - Intelligence Pro v3.0
Navegacion de 3 paginas: Datos · Momios · Analisis
"""
import streamlit as st

st.set_page_config(
    page_title="Intelligence Pro",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from data.session import init
init()

pg_datos    = st.Page("pages/datos.py",    title="① Datos",    icon="📂", default=True)
pg_momios   = st.Page("pages/momios.py",   title="② Momios",   icon="💰")
pg_analisis = st.Page("pages/analisis.py", title="③ Análisis", icon="🔬")

nav = st.navigation([pg_datos, pg_momios, pg_analisis, pg_backtest])

with st.sidebar:
    st.markdown("### ◈ Intelligence Pro")
    st.markdown(
        '<p style="font-size:0.68rem;color:#a8a29e;font-family:DM Mono,monospace;margin-top:-6px;">'
        'v3.0 · Datos · Momios · Análisis</p>',
        unsafe_allow_html=True,
    )
    from ui.styles import inject_css
    inject_css()
    from ui.components import fmt_money
    from core.kelly import roi_pct
    r = roi_pct(st.session_state.banca_actual, st.session_state.banca_inicial)
    roi_cls = "roi-pos" if r > 0 else ("roi-neg" if r < 0 else "roi-neu")
    st.markdown(
        f'<div class="banca-box">'
        f'<div class="banca-lbl">Banca Actual</div>'
        f'<div class="banca-val">{fmt_money(st.session_state.banca_actual)}</div>'
        f'<div class="banca-roi {roi_cls}">ROI: {r:+.2f}%</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    from datetime import date
    from data.session import export_session, import_session
    st.markdown(
        '<p style="font-size:0.62rem;font-weight:600;color:#44403c;text-transform:uppercase;letter-spacing:0.10em;">Sesión</p>',
        unsafe_allow_html=True,
    )
    st.download_button(
        "⬇️ Exportar sesión",
        data=export_session(),
        file_name=f"intelligence_pro_{date.today()}.json",
        mime="application/json",
        use_container_width=True,
    )
    uploaded = st.file_uploader(
        "⬆️ Cargar sesión", type="json",
        label_visibility="collapsed", key="main_upload",
    )
    if uploaded:
        fid = f"{uploaded.name}_{uploaded.size}"
        if st.session_state.get("_main_import") != fid:
            ok, msg = import_session(uploaded.read())
            st.session_state["_main_import"] = fid
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

nav.run()
