"""
main.py
Entry point de Intelligence Pro.
Inicializa el estado, inyecta el CSS y orquesta las secciones.

Estructura del proyecto:
    main.py
    requirements.txt
    core/
        poisson.py   ← modelo matemático (Poisson, todos los mercados)
        kelly.py     ← criterio de Kelly y bankroll
        value.py     ← EV, edge, eliminación de vig
    data/
        leagues.py   ← config por liga (5 ligas, home advantage, blend dinámico)
        parser.py    ← parseo robusto de tablas FBRef
        profile.py   ← construcción del perfil estadístico del equipo
    ui/
        styles.py    ← todo el CSS
        components.py← componentes HTML reutilizables
        sidebar.py   ← Data Hub + Bankroll
        sections.py  ← secciones 01-06 de la app
"""
import streamlit as st

# ── Page config (debe ir antes de cualquier otro st.* ) ──────────────────────
st.set_page_config(
    page_title="Intelligence Pro",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports internos ─────────────────────────────────────────────────────────
from ui.styles   import inject_css
from ui.sidebar  import render_sidebar
from ui.sections import (
    section_encuentro,
    section_comparativa,
    section_probabilidades,
    section_picks,
    section_jornada,
    section_historial,
)

# ── Estado de sesión ──────────────────────────────────────────────────────────
_DEFAULTS = {
    "banca_actual":        1000.0,
    "banca_inicial":       1000.0,
    "jornada_pendientes":  [],
    "historial":           [],
    "data_master":         {},
}
for key, val in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── CSS ───────────────────────────────────────────────────────────────────────
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
cfg = render_sidebar()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""<div class="app-header">
        <span class="app-title">◈ Intelligence Pro</span>
        <span class="app-sub">Poisson · Kelly · xG Blend · 5 Ligas</span>
        <span class="app-tag">{cfg['tables_loaded']}/9 tablas · {cfg['league']}</span>
    </div>""",
    unsafe_allow_html=True,
)

# ── Secciones principales ────────────────────────────────────────────────────
ctx = section_encuentro(cfg)

if ctx:
    section_comparativa(ctx)
    section_probabilidades(ctx)
    section_picks(ctx, cfg)

section_jornada()
section_historial()
