"""
ui/styles.py
Todo el CSS de la aplicación en un solo lugar.
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Mono:ital,wght@0,400;0,500;1,400&display=swap');

/* ── BASE ── */
html, body, [class*="css"] { font-family: 'Outfit', sans-serif !important; }
.stApp { background: #f4f3ef !important; color: #1c1917 !important; }
.block-container { padding-top: 1.8rem !important; max-width: 1200px !important; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e7e5e0 !important;
}
section[data-testid="stSidebar"] * { color: #1c1917 !important; }

/* ── HEADER ── */
.app-header {
    display: flex; align-items: baseline; gap: 14px;
    margin-bottom: 28px; padding-bottom: 16px;
    border-bottom: 1px solid #e7e5e0;
}
.app-title { font-size: 1.4rem; font-weight: 700; color: #1c1917; letter-spacing: -0.03em; }
.app-sub   { font-size: 0.75rem; color: #a8a29e; font-family: 'DM Mono', monospace; }
.app-tag   {
    margin-left: auto; font-size: 0.62rem;
    font-family: 'DM Mono', monospace; color: #a8a29e;
    background: #f0ede8; border: 1px solid #e7e5e0;
    padding: 3px 10px; border-radius: 20px;
}

/* ── SECTION LABELS ── */
.sec-label {
    font-size: 0.62rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.14em; color: #a8a29e; font-family: 'DM Mono', monospace;
    margin: 22px 0 10px 0; padding-bottom: 8px; border-bottom: 1px solid #e7e5e0;
}

/* ── CARDS ── */
.card {
    background: #ffffff; border: 1px solid #e7e5e0;
    border-radius: 10px; padding: 16px 20px;
}

/* ── BANKROLL BOX ── */
.banca-box {
    background: #ffffff; border: 1px solid #e7e5e0;
    border-left: 3px solid #1c1917; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 12px;
}
.banca-lbl {
    font-size: 0.60rem; text-transform: uppercase; letter-spacing: 0.12em;
    color: #a8a29e; font-family: 'DM Mono', monospace;
}
.banca-val {
    font-size: 1.65rem; font-weight: 700;
    font-family: 'DM Mono', monospace; color: #1c1917; margin: 4px 0 2px 0;
}
.banca-roi { font-size: 0.70rem; font-family: 'DM Mono', monospace; }
.roi-pos { color: #16a34a; } .roi-neg { color: #dc2626; } .roi-neu { color: #a8a29e; }

/* ── TABLE STATUS ── */
.tbl-loaded {
    background: #f0fdf4; border: 1px solid #86efac; color: #15803d;
    font-size: 0.65rem; padding: 3px 10px; border-radius: 4px;
    font-family: 'DM Mono', monospace; text-align: center; margin-top: 4px;
}
.tbl-empty {
    color: #c4b9b2; font-size: 0.65rem; font-family: 'DM Mono', monospace;
    margin-top: 4px; text-align: center;
}

/* ── TEAM HEADER ── */
.team-hdr { display: flex; align-items: center; gap: 8px; padding: 8px 0 12px 0; }
.team-hdr-r { justify-content: flex-end; }
.team-name { font-size: 1rem; font-weight: 700; color: #1c1917; }
.team-pos  {
    font-size: 0.62rem; font-family: 'DM Mono', monospace;
    background: #f0ede8; border: 1px solid #e7e5e0;
    padding: 2px 8px; border-radius: 20px; color: #78716c;
}
.team-wdl { font-size: 0.62rem; font-family: 'DM Mono', monospace; color: #a8a29e; }

/* ── STAT ROWS ── */
.stat-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 0; border-bottom: 1px solid #f4f3ef; font-size: 0.80rem;
}
.stat-row:last-child { border-bottom: none; }
.sl { color: #78716c; font-weight: 400; }
.sv { font-family: 'DM Mono', monospace; font-weight: 500; color: #1c1917; font-size: 0.82rem; }
.sv-good { color: #16a34a !important; }
.sv-bad  { color: #dc2626 !important; }
.stat-sec {
    font-size: 0.60rem; font-weight: 600; color: #a8a29e;
    text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 6px;
}

/* ── PROB BARS ── */
.prob-wrap { margin: 5px 0; }
.prob-top  { display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 0.78rem; }
.prob-name { color: #44403c; font-weight: 500; }
.prob-pct  { font-family: 'DM Mono', monospace; font-weight: 600; color: #1c1917; }
.prob-sub  { font-size: 0.62rem; color: #a8a29e; font-family: 'DM Mono', monospace; text-align: right; }
.prob-bar-bg   { background: #f0ede8; border-radius: 3px; height: 5px; }
.prob-bar-fill { height: 100%; border-radius: 3px; }

/* ── MARKET PILLS ── */
.mkt-grid { display: flex; gap: 7px; flex-wrap: wrap; margin: 10px 0; }
.mkt-pill {
    flex: 1; min-width: 75px;
    background: #ffffff; border: 1px solid #e7e5e0;
    border-radius: 8px; padding: 9px 8px; text-align: center;
}
.mkt-val { font-size: 1.1rem; font-weight: 700; font-family: 'DM Mono', monospace; color: #1c1917; }
.mkt-lbl { font-size: 0.58rem; text-transform: uppercase; letter-spacing: 0.10em; color: #a8a29e; margin-top: 2px; font-family: 'DM Mono', monospace; }

/* ── EXACT SCORES ── */
.scores-grid { display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0; }
.score-pill {
    background: #f9f8f6; border: 1px solid #e7e5e0;
    border-radius: 6px; padding: 6px 12px; text-align: center; min-width: 60px;
}
.score-result { font-size: 0.90rem; font-weight: 700; font-family: 'DM Mono', monospace; color: #1c1917; }
.score-prob   { font-size: 0.60rem; color: #a8a29e; font-family: 'DM Mono', monospace; }

/* ── PICK CARDS ── */
.pick-grid { display: flex; gap: 9px; margin: 8px 0; flex-wrap: wrap; }
.pick-c    { flex: 1; min-width: 160px; border-radius: 10px; padding: 14px 16px; border: 1px solid; }
.pick-c.pos { background: #f0fdf4; border-color: #86efac; }
.pick-c.neg { background: #fef2f2; border-color: #fca5a5; }
.pick-c.neu { background: #fafaf9; border-color: #e7e5e0; }
.pick-name   { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.10em; color: #a8a29e; font-family: 'DM Mono', monospace; margin-bottom: 5px; }
.pick-ev     { font-size: 1.25rem; font-weight: 700; font-family: 'DM Mono', monospace; }
.ev-pos { color: #16a34a; } .ev-neg { color: #dc2626; }
.pick-detail { font-size: 0.70rem; color: #78716c; margin-top: 6px; line-height: 1.5; }
.pick-stake  { font-family: 'DM Mono', monospace; font-weight: 600; color: #1c1917; }

/* ── JORNADA ROWS ── */
.jrow {
    display: flex; align-items: center; gap: 10px;
    background: #ffffff; border: 1px solid #e7e5e0;
    border-radius: 8px; padding: 11px 15px; margin-bottom: 7px; font-size: 0.80rem;
}
.j-match  { flex: 2; font-weight: 600; color: #1c1917; }
.j-mkt    { flex: 1; font-size: 0.70rem; color: #78716c; }
.j-momio  { font-family: 'DM Mono', monospace; color: #44403c; }
.j-stake  { font-family: 'DM Mono', monospace; font-weight: 600; color: #d97706; }
.j-pen    { color: #d97706; font-weight: 600; font-size: 0.75rem; }
.j-gan    { color: #16a34a; font-weight: 700; font-size: 0.75rem; }
.j-per    { color: #dc2626; font-weight: 700; font-size: 0.75rem; }

/* ── LAMBDA INFO ── */
.lam-info {
    font-size: 0.68rem; font-family: 'DM Mono', monospace;
    color: #a8a29e; background: #fafaf9; border: 1px solid #f0ede8;
    border-radius: 6px; padding: 6px 12px; margin: 6px 0;
}

/* ── VIG INFO ── */
.vig-info {
    font-size: 0.65rem; font-family: 'DM Mono', monospace; color: #a8a29e;
    display: flex; gap: 16px; margin-top: 4px; flex-wrap: wrap;
}

/* ── INPUTS ── */
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    background: #fafaf9 !important; border-color: #e7e5e0 !important;
    color: #1c1917 !important; border-radius: 7px !important;
    font-family: 'Outfit', sans-serif !important;
}
div[data-testid="stNumberInput"] input:focus { border-color: #a78bfa !important; }
div[data-baseweb="select"] { background: #fafaf9 !important; }

/* ── BUTTONS ── */
.stButton button {
    background: #1c1917 !important; color: #fafaf9 !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 500 !important; font-family: 'Outfit', sans-serif !important;
    transition: background 0.15s !important;
}
.stButton button:hover { background: #292524 !important; }

/* ── METRICS ── */
div[data-testid="metric-container"] {
    background: #ffffff !important; border: 1px solid #e7e5e0 !important;
    border-radius: 8px !important; padding: 10px 14px !important;
}
div[data-testid="metric-container"] label { color: #78716c !important; font-size: 0.72rem !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #1c1917 !important; font-family: 'DM Mono', monospace !important;
}

/* ── SLIDER ── */
div[data-testid="stSlider"] .rc-slider-track { background: #7c3aed !important; }
div[data-testid="stSlider"] .rc-slider-handle { background: #7c3aed !important; border-color: #7c3aed !important; }

/* ── EXPANDER ── */
details { border: 1px solid #e7e5e0 !important; border-radius: 8px !important; background: #fafaf9 !important; }
details summary { font-size: 0.80rem !important; font-weight: 500 !important; color: #44403c !important; }

hr { border-color: #e7e5e0 !important; }

/* ── DATAFRAME ── */
div[data-testid="stDataFrame"] {
    border: 1px solid #e7e5e0 !important; border-radius: 8px !important; overflow: hidden !important;
}

/* ── RADIO ── */
div[data-testid="stRadio"] label { color: #44403c !important; font-size: 0.82rem !important; }
</style>
"""


def inject_css():
    """Inyecta el CSS en la app Streamlit."""
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)
