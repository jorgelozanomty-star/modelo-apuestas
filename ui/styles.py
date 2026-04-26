"""
Intelligence Pro — ui/styles.py
Sistema de diseño: editorial sports analytics
Fonts: Fraunces (display) · Outfit (UI) · JetBrains Mono (data)
Palette: crema cálida · verde bosque · señales saturadas
"""

FONTS_URL = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;0,9..144,700;1,9..144,400&family=Outfit:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
"""

CSS = """
<style>
/* ── Variables ─────────────────────────────────────── */
:root {
    --bg:           #F5F2EB;
    --surface:      #FFFFFF;
    --surface-2:    #EDE9DF;
    --surface-3:    #E4DDD1;
    --text:         #1A1714;
    --text-2:       #58534D;
    --text-muted:   #A09890;
    --brand:        #1B4332;
    --brand-light:  #D1FAE5;
    --border:       #DDD8CE;
    --border-focus: #7C7368;

    /* Señales */
    --s-green:  #15803D; --s-green-bg:  #F0FDF4; --s-green-border: #86EFAC;
    --s-amber:  #B45309; --s-amber-bg:  #FFFBEB; --s-amber-border: #FCD34D;
    --s-orange: #C2410C; --s-orange-bg: #FFF7ED; --s-orange-border: #FDBA74;
    --s-red:    #B91C1C; --s-red-bg:    #FEF2F2; --s-red-border:   #FCA5A5;

    --font-display: 'Fraunces', Georgia, serif;
    --font-ui:      'Outfit', system-ui, sans-serif;
    --font-mono:    'JetBrains Mono', 'Fira Code', monospace;

    --radius:    12px;
    --radius-sm: 8px;
    --radius-xs: 5px;
    --shadow:    0 1px 3px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
    --shadow-lg: 0 8px 24px rgba(0,0,0,0.10);
}

/* ── Base ───────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: var(--font-ui) !important;
    color: var(--text) !important;
}

[data-testid="stHeader"] {
    background-color: var(--bg) !important;
    border-bottom: 1px solid var(--border);
}

[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* ── Tipografía global ─────────────────────────────── */
h1, h2, h3, h4 {
    font-family: var(--font-display) !important;
    color: var(--text) !important;
    letter-spacing: -0.02em;
}

h1 { font-size: 2rem !important; font-weight: 700 !important; }
h2 { font-size: 1.4rem !important; font-weight: 600 !important; }
h3 { font-size: 1.1rem !important; font-weight: 600 !important; }

p, li, label, .stMarkdown {
    font-family: var(--font-ui) !important;
    color: var(--text-2);
    line-height: 1.6;
}

/* ── Inputs / Textareas ─────────────────────────────── */
.stTextArea > div > div > textarea,
.stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
    color: var(--text) !important;
    padding: 12px 14px !important;
    transition: border-color 0.15s ease;
}
.stTextArea > div > div > textarea:focus,
.stTextInput > div > div > input:focus {
    border-color: var(--brand) !important;
    box-shadow: 0 0 0 3px rgba(27,67,50,0.08) !important;
    outline: none !important;
}

/* ── Botones ────────────────────────────────────────── */
.stButton > button {
    font-family: var(--font-ui) !important;
    font-weight: 600 !important;
    border-radius: var(--radius-sm) !important;
    transition: all 0.15s ease !important;
    letter-spacing: 0.01em;
}

/* Botón primario */
.stButton > button[kind="primary"],
.stButton > button:not([kind]) {
    background: var(--brand) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: var(--shadow) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button:not([kind]):hover {
    background: #14522A !important;
    box-shadow: var(--shadow-md) !important;
    transform: translateY(-1px);
}

/* Botón secundario */
.stButton > button[kind="secondary"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1.5px solid var(--border) !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--brand) !important;
    color: var(--brand) !important;
}

/* ── Selectbox / Multiselect ───────────────────────── */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-ui) !important;
}

/* ── Métricas (st.metric) ───────────────────────────── */
[data-testid="stMetricValue"] {
    font-family: var(--font-display) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    letter-spacing: -0.03em;
}
[data-testid="stMetricLabel"] {
    font-family: var(--font-ui) !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted) !important;
}
[data-testid="stMetricDelta"] {
    font-family: var(--font-mono) !important;
    font-size: 0.85rem !important;
}

/* ── Expander ────────────────────────────────────────── */
.streamlit-expanderHeader {
    font-family: var(--font-ui) !important;
    font-weight: 600 !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
}

/* ── Tabs ───────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface-2) !important;
    border-radius: var(--radius) !important;
    padding: 4px !important;
    gap: 2px !important;
    border: none !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--font-ui) !important;
    font-weight: 600 !important;
    border-radius: var(--radius-sm) !important;
    border: none !important;
    color: var(--text-2) !important;
    padding: 8px 18px !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    box-shadow: var(--shadow) !important;
}

/* ── Dataframe ──────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden;
}

/* ── Sidebar nav ────────────────────────────────────── */
[data-testid="stSidebarNav"] a {
    font-family: var(--font-ui) !important;
    font-weight: 500 !important;
    color: var(--text-2) !important;
    border-radius: var(--radius-sm) !important;
    padding: 6px 12px !important;
}
[data-testid="stSidebarNav"] a:hover {
    background: var(--surface-2) !important;
    color: var(--text) !important;
}

/* ── Divider ────────────────────────────────────────── */
hr {
    border-color: var(--border) !important;
    margin: 20px 0 !important;
}

/* ── Custom components ───────────────────────────────── */

/* Pipeline stepper */
.ip-pipeline {
    display: flex;
    align-items: center;
    gap: 0;
    margin: 16px 0 28px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 20px;
    box-shadow: var(--shadow);
}
.ip-step {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    position: relative;
}
.ip-step:not(:last-child)::after {
    content: '';
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 1px;
    height: 28px;
    background: var(--border);
}
.ip-step-num {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 0.9rem;
    flex-shrink: 0;
    transition: all 0.2s ease;
}
.ip-step.done .ip-step-num {
    background: var(--brand);
    color: #fff;
    box-shadow: 0 2px 8px rgba(27,67,50,0.3);
}
.ip-step.active .ip-step-num {
    background: var(--s-amber-bg);
    color: var(--s-amber);
    border: 2px solid var(--s-amber-border);
}
.ip-step.pending .ip-step-num {
    background: var(--surface-2);
    color: var(--text-muted);
    border: 2px solid var(--border);
}
.ip-step-info {
    display: flex;
    flex-direction: column;
}
.ip-step-label {
    font-family: var(--font-ui);
    font-weight: 600;
    font-size: 0.82rem;
    color: var(--text);
    line-height: 1.2;
}
.ip-step.pending .ip-step-label { color: var(--text-muted); }
.ip-step-sub {
    font-family: var(--font-ui);
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 1px;
}

/* Tarjeta de partido */
.match-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 18px;
    margin-bottom: 10px;
    box-shadow: var(--shadow);
    transition: box-shadow 0.15s ease, transform 0.1s ease;
    position: relative;
    overflow: hidden;
}
.match-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}
.match-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
    border-radius: var(--radius) 0 0 var(--radius);
}
.match-card.green::before  { background: var(--s-green); }
.match-card.amber::before  { background: var(--s-amber); }
.match-card.orange::before { background: var(--s-orange); }
.match-card.red::before    { background: var(--s-red); }

.match-teams {
    font-family: var(--font-display);
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.01em;
    margin-bottom: 4px;
}
.match-meta {
    font-family: var(--font-ui);
    font-size: 0.73rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
}
.match-market-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 8px;
}
.market-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    border-radius: 999px;
    font-family: var(--font-ui);
    font-size: 0.78rem;
    font-weight: 600;
    border: 1px solid;
}
.market-chip.green  { background: var(--s-green-bg);  color: var(--s-green);  border-color: var(--s-green-border); }
.market-chip.amber  { background: var(--s-amber-bg);  color: var(--s-amber);  border-color: var(--s-amber-border); }
.market-chip.orange { background: var(--s-orange-bg); color: var(--s-orange); border-color: var(--s-orange-border); }
.market-chip.red    { background: var(--s-red-bg);    color: var(--s-red);    border-color: var(--s-red-border); }

.market-ev {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    color: var(--text-muted);
}
.market-odds {
    font-family: var(--font-mono);
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text);
}

/* Bankroll widget sidebar */
.bankroll-widget {
    background: linear-gradient(135deg, var(--brand) 0%, #14522A 100%);
    border-radius: var(--radius);
    padding: 16px;
    color: #fff;
    margin-bottom: 16px;
}
.bankroll-label {
    font-family: var(--font-ui);
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    opacity: 0.7;
    margin-bottom: 4px;
}
.bankroll-amount {
    font-family: var(--font-display);
    font-size: 1.9rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1;
}
.bankroll-delta {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    margin-top: 6px;
    opacity: 0.85;
}
.bankroll-picks {
    font-family: var(--font-ui);
    font-size: 0.75rem;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid rgba(255,255,255,0.2);
    opacity: 0.8;
}

/* Estado de carga de liga */
.liga-status-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px 16px;
    margin-bottom: 8px;
    box-shadow: var(--shadow);
}
.liga-status-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}
.liga-name {
    font-family: var(--font-ui);
    font-weight: 700;
    font-size: 0.9rem;
    color: var(--text);
}
.liga-pct {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-2);
}
.tables-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}
.table-badge {
    font-family: var(--font-ui);
    font-size: 0.68rem;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: var(--radius-xs);
}
.table-badge.ok   { background: var(--s-green-bg); color: var(--s-green); }
.table-badge.miss { background: var(--surface-2); color: var(--text-muted); }

/* Fuzzy match confirm */
.fuzzy-card {
    background: var(--s-amber-bg);
    border: 1px solid var(--s-amber-border);
    border-radius: var(--radius);
    padding: 14px 16px;
    margin-bottom: 8px;
}
.fuzzy-title {
    font-family: var(--font-ui);
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--s-amber);
    margin-bottom: 4px;
}
.fuzzy-match {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    color: var(--text-2);
}

/* Next action CTA */
.next-action {
    background: var(--brand);
    color: #fff;
    border-radius: var(--radius);
    padding: 16px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: var(--shadow-md);
}
.next-action-icon {
    font-size: 1.6rem;
    flex-shrink: 0;
}
.next-action-text {
    font-family: var(--font-ui);
}
.next-action-title {
    font-weight: 700;
    font-size: 0.95rem;
    margin-bottom: 2px;
}
.next-action-sub {
    font-size: 0.78rem;
    opacity: 0.75;
}

/* Progress bar para tablas */
.table-progress-bar {
    height: 4px;
    background: var(--surface-2);
    border-radius: 999px;
    overflow: hidden;
    margin-top: 6px;
}
.table-progress-fill {
    height: 100%;
    background: var(--brand);
    border-radius: 999px;
    transition: width 0.4s ease;
}

/* Picks mini-list */
.pick-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
    font-family: var(--font-ui);
    font-size: 0.82rem;
}
.pick-row:last-child { border-bottom: none; }
.pick-signal {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.pick-signal.green  { background: var(--s-green); }
.pick-signal.amber  { background: var(--s-amber); }
.pick-market {
    font-weight: 600;
    color: var(--text);
    flex: 1;
}
.pick-stake {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--text-2);
}

/* Stats inline */
.stat-row {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    font-size: 0.82rem;
    border-bottom: 1px solid var(--border);
}
.stat-row:last-child { border-bottom: none; }
.stat-label { color: var(--text-2); font-family: var(--font-ui); }
.stat-value { font-family: var(--font-mono); font-weight: 600; color: var(--text); }

/* Toast success/error */
.ip-toast {
    padding: 10px 14px;
    border-radius: var(--radius-sm);
    font-family: var(--font-ui);
    font-size: 0.85rem;
    font-weight: 500;
    margin-bottom: 12px;
}
.ip-toast.success {
    background: var(--s-green-bg);
    color: var(--s-green);
    border: 1px solid var(--s-green-border);
}
.ip-toast.error {
    background: var(--s-red-bg);
    color: var(--s-red);
    border: 1px solid var(--s-red-border);
}
.ip-toast.info {
    background: var(--s-amber-bg);
    color: var(--s-amber);
    border: 1px solid var(--s-amber-border);
}

/* Sección header */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 24px 0 14px;
}
.section-title {
    font-family: var(--font-display);
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.01em;
}
.section-count {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    font-weight: 600;
    background: var(--surface-2);
    color: var(--text-muted);
    padding: 2px 8px;
    border-radius: 999px;
}

/* Número grande con contexto */
.big-number {
    font-family: var(--font-display);
    font-size: 3rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.04em;
    line-height: 1;
}
.big-number-label {
    font-family: var(--font-ui);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-top: 4px;
}

/* Instrucción inline */
.inline-tip {
    background: var(--surface-2);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    font-family: var(--font-ui);
    font-size: 0.8rem;
    color: var(--text-2);
    margin-bottom: 10px;
    line-height: 1.5;
}
.inline-tip strong { color: var(--text); }

/* ── Ajustes finales Streamlit ────────────────────── */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 900px !important;
}

[data-testid="stSidebarContent"] {
    padding: 1.5rem 1rem !important;
}

/* Quitar padding extra en columns */
[data-testid="column"] {
    padding: 0 6px !important;
}

/* Success/warning/error colors en st.success etc */
[data-testid="stNotification"] {
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-ui) !important;
}
</style>
"""


def inject_styles():
    """Inyectar fuentes + CSS en la página. Llamar al inicio de cada página."""
    import streamlit as st
    st.markdown(FONTS_URL, unsafe_allow_html=True)
    st.markdown(CSS, unsafe_allow_html=True)


# Alias para compatibilidad con backtest_page.py y código legacy
inject_css = inject_styles

