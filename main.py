"""
Intelligence Pro — main.py v4.0
Navegación con home dashboard como primera página.
Auto-inicialización de session_state.
"""
import streamlit as st

# ── Configuración de la app ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Intelligence Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "Intelligence Pro — Modelo Poisson + Kelly + xG Blend"
    }
)

# ── Inicializar session_state con valores por defecto ─────────────────────────
_DEFAULTS = {
    "fbref_data":       {},   # {liga_key: {tabla_key: DataFrame}}
    "fixtures_data":    {},   # {liga_key: [partidos]}
    "momios_data":      {},   # {partido_key: {home, draw, away, ...}}
    "ha_store":         {},   # {liga_key: ha_splits}
    "h2h_data":         {},   # {home_away: [encuentros]}
    "bankroll":         1000.0,
    "bankroll_inicial": 1000.0,
    "kelly_fraccion":   0.15,
    "jornada_activa":   [],   # [pick_dict]
    "historial":        [],   # [pick_resuelto]
    "parlay_activo":    [],
    "_session_modified": False,
    "_fuzzy_confirmaciones": {},  # cache de confirmaciones fuzzy
}

for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Definición de páginas ──────────────────────────────────────────────────────
home_page = st.Page(
    "pages/home.py",
    title="Inicio",
    icon="🏠",
    default=True,
)
datos_page = st.Page(
    "pages/datos.py",
    title="① Cargar Ligas",
    icon="📋",
)
momios_page = st.Page(
    "pages/momios.py",
    title="② Momios",
    icon="💰",
)
analisis_page = st.Page(
    "pages/analisis.py",
    title="③ Análisis",
    icon="🎯",
)
backtest_page = st.Page(
    "pages/backtest_page.py",
    title="Backtest",
    icon="📊",
)

# ── Navegación ─────────────────────────────────────────────────────────────────
nav = st.navigation(
    {
        "": [home_page],
        "Flujo semanal": [datos_page, momios_page, analisis_page],
        "Herramientas": [backtest_page],
    },
    position="sidebar",
)

nav.run()
