import streamlit as st
import pandas as pd
import math
import io

st.set_page_config(
    page_title="Intelligence Pro | Betting Tool",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MAPEO DE EQUIPOS (NORMALIZACIÓN) ---
EQUIPOS_MAP = {
    "UANL": "Tigres", "Tigres UANL": "Tigres", "Club América": "América",
    "CA América": "América", "Guadalajara": "Chivas", "CD Guadalajara": "Chivas",
    "Cruz Azul": "Cruz Azul", "UNAM": "Pumas", "Pumas UNAM": "Pumas",
    "Monterrey": "Rayados", "CF Monterrey": "Rayados", "Toluca": "Toluca",
    "Pachuca": "Pachuca", "León": "León", "Santos": "Santos Laguna",
    "Santos Laguna": "Santos Laguna", "Atlas": "Atlas", "Necaxa": "Necaxa",
    "Querétaro": "Querétaro", "Mazatlán": "Mazatlán", "FC Juárez": "Juárez",
    "Tijuana": "Xolos", "Club Tijuana": "Xolos", "Puebla": "Puebla",
    "Atlético San Luis": "San Luis"
}

# ─── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── BASE ── */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif !important;
}
.stApp {
    background: #0a0c10 !important;
    color: #e2e8f0 !important;
}
section[data-testid="stSidebar"] {
    background: #0f1117 !important;
    border-right: 1px solid #1e2330 !important;
}
section[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

/* ── HEADER ── */
.main-header {
    background: linear-gradient(135deg, #0f1117 0%, #131824 100%);
    border: 1px solid #1e2330;
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 16px;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.main-header h1 {
    font-size: 2rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    margin: 0 !important;
}
.main-header p {
    color: #64748b !important;
    font-size: 0.85rem !important;
    margin: 4px 0 0 0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── SECTION HEADER ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 28px 0 16px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid #1e2330;
}
.section-badge {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white !important;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.1em;
    font-family: 'JetBrains Mono', monospace;
}
.section-title {
    color: #e2e8f0 !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    margin: 0 !important;
}

/* ── CARDS ── */
.stat-card {
    background: #0f1117;
    border: 1px solid #1e2330;
    border-radius: 12px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.stat-card:hover { border-color: #2d3748; }
.stat-card .label {
    font-size: 0.72rem;
    color: #4a5568;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 6px;
}
.stat-card .value {
    font-size: 1.6rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: #e2e8f0;
}
.stat-card .sub {
    font-size: 0.75rem;
    color: #64748b;
    margin-top: 4px;
}

/* ── PICK CARDS ── */
.pick-card {
    border-radius: 14px;
    padding: 20px;
    border: 1px solid;
    position: relative;
    overflow: hidden;
}
.pick-card.positive {
    background: linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(5,150,105,0.04) 100%);
    border-color: rgba(16,185,129,0.25);
}
.pick-card.negative {
    background: linear-gradient(135deg, rgba(239,68,68,0.06) 0%, rgba(220,38,38,0.03) 100%);
    border-color: rgba(239,68,68,0.15);
}
.pick-card .pick-name {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #94a3b8;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 8px;
}
.pick-card .pick-ev {
    font-size: 1.5rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
.pick-card .pick-ev.positive { color: #10b981; }
.pick-card .pick-ev.negative { color: #ef4444; }
.pick-card .pick-details {
    margin-top: 12px;
    display: flex;
    gap: 16px;
}
.pick-card .detail-item .dl { font-size: 0.65rem; color: #4a5568; text-transform: uppercase; letter-spacing: 0.08em; }
.pick-card .detail-item .dv { font-size: 0.95rem; font-weight: 600; color: #cbd5e1; font-family: 'JetBrains Mono', monospace; }

/* ── DATA HUB STATUS ── */
.status-box { padding: 8px; border-radius: 6px; margin-top: 5px; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; text-align: center;}
.loaded { background: rgba(16,185,129,0.15); border: 1px solid #10b981; color: #10b981; }
.empty { background: rgba(148, 163, 184, 0.05); border: 1px solid #334155; color: #64748b; }

/* ── PROB BAR ── */
.prob-bar-wrap { margin: 8px 0; }
.prob-bar-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.72rem;
    color: #94a3b8;
    margin-bottom: 4px;
    font-family: 'JetBrains Mono', monospace;
}
.prob-bar-bg {
    background: #1e2330;
    border-radius: 4px;
    height: 6px;
    overflow: hidden;
}
.prob-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.4s ease;
}

/* ── BANCA SIDEBAR ── */
.banca-display {
    background: linear-gradient(135deg, #131824, #0f1117);
    border: 1px solid #1e2330;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0 16px 0;
    text-align: center;
}
.banca-display .bd-label {
    font-size: 0.65rem;
    color: #4a5568;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-family: 'JetBrains Mono', monospace;
}
.banca-display .bd-value {
    font-size: 1.9rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    background: linear-gradient(135deg, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 4px 0;
}
.banca-display .bd-roi {
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
}
.bd-roi.pos { color: #10b981; }
.bd-roi.neg { color: #ef4444; }
.bd-roi.neu { color: #64748b; }

/* ── JORNADA TABLE ── */
.jornada-row {
    background: #0f1117;
    border: 1px solid #1e2330;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}
.jr-partido { font-weight: 600; font-size: 0.9rem; }
.jr-badge {
    font-size: 0.65rem;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(99,102,241,0.15);
    color: #818cf8;
    border: 1px solid rgba(99,102,241,0.25);
}
.jr-stake { font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #f59e0b; font-size: 1rem; }
.jr-momio { font-family: 'JetBrains Mono', monospace; color: #94a3b8; font-size: 0.85rem; }
.status-gan { color: #10b981 !important; font-weight: 700; }
.status-per { color: #ef4444 !important; font-weight: 700; }
.status-pen { color: #f59e0b !important; }

/* ── OVERUNDER CARD ── */
.ou-card {
    background: #0f1117;
    border: 1px solid #1e2330;
    border-radius: 12px;
    padding: 18px 22px;
    text-align: center;
}
.ou-value { font-size: 2rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #f59e0b; }
.ou-label { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'JetBrains Mono', monospace; margin-top: 4px; }

/* ── INPUTS ── */
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] select {
    background: #131824 !important;
    border-color: #1e2330 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stTextInput"] input:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,0.15) !important;
}

/* ── BUTTONS ── */
.stButton button {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.2s, transform 0.1s !important;
    padding: 0.5rem 1.2rem !important;
}
.stButton button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}
.stButton button:active { transform: translateY(0) !important; }

/* ── METRICS ── */
div[data-testid="metric-container"] {
    background: #0f1117 !important;
    border: 1px solid #1e2330 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
}
div[data-testid="metric-container"] label { color: #64748b !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── SLIDER ── */
div[data-testid="stSlider"] .rc-slider-track { background: #4f46e5 !important; }
div[data-testid="stSlider"] .rc-slider-handle {
    background: #818cf8 !important;
    border-color: #818cf8 !important;
}

/* ── DIVIDER ── */
hr { border-color: #1e2330 !important; }

/* ── RADIO ── */
div[data-testid="stRadio"] label { color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)

# ─── PERSISTENCIA ──────────────────────────────────────────────────────────────
BANCA_INICIAL = 1000.0
for key, val in [
    ('banca_actual', BANCA_INICIAL),
    ('banca_inicial', BANCA_INICIAL),
    ('jornada_pendientes', []),
    ('historial', []),
    ('data_master', {}), # Nueva persistencia para el Data Hub
]:
    if key not in st.session_state:
        st.session_state[key] = val

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def process_fbref_paste(text):
    if not text or len(text) < 10: return None
    try:
        df = pd.read_csv(io.StringIO(text), sep='\t')
        if len(df.columns) < 2: df = pd.read_csv(io.StringIO(text), sep=None, engine='python')
        df.columns = [c.strip() for c in df.columns]
        if 'Squad' in df.columns: df['Squad'] = df['Squad'].replace(EQUIPOS_MAP)
        return df
    except: return None

def calc_poisson(gf_l, gc_l, gf_v, gc_v):
    lam_l = (gf_l + gc_v) / 2
    lam_v = (gf_v + gc_l) / 2
    lam_l = max(0.1, lam_l)
    lam_v = max(0.1, lam_v)
    p_l = p_v = p_e = 0.0
    matrix = {}
    for i in range(8):
        for j in range(8):
            prob = (
                (math.exp(-lam_l) * lam_l**i) / math.factorial(i) *
                (math.exp(-lam_v) * lam_v**j) / math.factorial(j)
            )
            matrix[(i, j)] = prob
            if i > j: p_l += prob
            elif j > i: p_v += prob
            else: p_e += prob
    return p_l, p_v, p_e, lam_l, lam_v, matrix

def get_kelly(prob, momio, fraction):
    if momio <= 1:
        return 0
    edge = ((momio - 1) * prob) - (1 - prob)
    return max(0.0, (edge / (momio - 1)) * fraction)

def fmt_money(v):
    return f"${v:,.2f}"

def ev_pct(prob, momio):
    return (prob * momio - 1) * 100

def roi():
    if st.session_state.banca_inicial == 0:
        return 0
    return ((st.session_state.banca_actual - st.session_state.banca_inicial) / st.session_state.banca_inicial) * 100

def extraer_promedio(fila):
    mp = float(fila.get('MP', 1) or 1)
    mp = max(mp, 1)
    gf = float(fila.get('GF', fila.get('Gls', 1.5)) or 1.5)
    ga = float(fila.get('GA', 1.1) or 1.1)
    return (gf / mp if gf > 5 else gf), (ga / mp if ga > 5 else ga)

# ─── LAYOUT: TRES COLUMNAS ────────────────────────────────────────────────────
col_izq, col_main, col_der = st.columns([0.8, 2.5, 1])

# ─── COLUMNA IZQUIERDA: GESTIÓN DE CAPITAL ────────────────────────────────────
with col_izq:
    st.markdown("### ⚙️ Control")
    roi_val = roi()
    roi_class = "pos" if roi_val > 0 else ("neg" if roi_val < 0 else "neu")
    roi_sign = "+" if roi_val > 0 else ""

    st.markdown(f"""
    <div class="banca-display">
        <div class="bd-label">Banca Actual</div>
        <div class="bd-value">{fmt_money(st.session_state.banca_actual)}</div>
        <div class="bd-roi {roi_class}">ROI: {roi_sign}{roi_val:.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("✏️ Ajustar Banca"):
        nueva_banca = st.number_input("Nueva banca ($)", value=st.session_state.banca_actual, step=50.0)
        if st.button("Aplicar"):
            st.session_state.banca_inicial = nueva_banca
            st.session_state.banca_actual = nueva_banca
            st.rerun()

    riesgo_total = sum(p['stake'] for p in st.session_state.jornada_pendientes)
    pct_riesgo = (riesgo_total / st.session_state.banca_actual * 100) if st.session_state.banca_actual else 0
    st.markdown(f"""
    <div style="background:#131824;border:1px solid #1e2330;border-radius:10px;padding:12px 16px;margin:8px 0;">
        <div style="font-size:0.65rem;color:#4a5568;text-transform:uppercase;letter-spacing:0.1em;font-family:'JetBrains Mono',monospace;">En Riesgo</div>
        <div style="font-size:1.2rem;font-weight:700;font-family:'JetBrains Mono',monospace;color:#f59e0b;">{fmt_money(riesgo_total)}</div>
        <div style="font-size:0.72rem;color:#64748b;font-family:'JetBrains Mono',monospace;">{pct_riesgo:.1f}% de la banca</div>
    </div>
    """, unsafe_allow_html=True)

    fractional_kelly = st.slider("📉 Fracción Kelly", 0.05, 1.0, 0.25, step=0.05)

    if st.button("🗑️ Limpiar Jornada"):
        st.session_state.jornada_pendientes = []
        st.rerun()

# ─── COLUMNA DERECHA: DATA HUB (LOS 9 CUADRITOS) ─────────────────────────────────
with col_der:
    st.markdown("### 📥 Data Hub")
    tablas_hub = [
        "Tabla General", "Standard Squad", "Standard Opp", 
        "Shooting Squad", "Shooting Opp", "PlayingTime Squad", 
        "PlayingTime Opp", "Misc Squad", "Misc Opp"
    ]
    
    for t in tablas_hub:
        with st.expander(f"📄 {t}"):
            input_data = st.text_area("Pegar FBRef", key=f"in_{t}", height=80, label_visibility="collapsed")
            processed = process_fbref_paste(input_data)
            if processed is not None:
                st.session_state.data_master[t] = processed
                st.markdown(f'<div class="status-box loaded">VINCULADA ({len(processed)} eqs)</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-box empty">ESPERANDO DATOS...</div>', unsafe_allow_html=True)

# ─── COLUMNA CENTRAL: ANÁLISIS ────────────────────────────────────────────────
with col_main:
    st.markdown("""
    <div class="main-header">
        <div>
            <h1>📡 Intelligence Pro</h1>
            <p>Análisis Poisson · Kelly Criterion · Gestión de Banca</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1 — ANÁLISIS DEL ENCUENTRO
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class="section-header">
        <span class="section-badge">01</span>
        <span class="section-title">Análisis del Encuentro</span>
    </div>
    """, unsafe_allow_html=True)

    # Obtener lista de equipos del Data Hub si existe
    equipos_lista = ["— sin equipo —"]
    if st.session_state.data_master:
        # Usamos la primera disponible
        first_df = next(iter(st.session_state.data_master.values()))
        equipos_lista += sorted(first_df['Squad'].unique().tolist())

    c1, c2 = st.columns(2)
    l_val_f, l_val_c = 1.5, 1.1
    v_val_f, v_val_c = 1.0, 1.2
    h_xg, v_xg = 0.0, 0.0

    with c1:
        st.markdown("**🏠 Local**")
        local_sel = st.selectbox("Equipo local", equipos_lista, key="local_sel", label_visibility="collapsed")
        if local_sel != "— sin equipo —":
            # Auto-llenado desde Standard Squad
            if "Standard Squad" in st.session_state.data_master:
                df_std = st.session_state.data_master["Standard Squad"]
                try:
                    row_h = df_std[df_std['Squad'] == local_sel].iloc[0].to_dict()
                    l_val_f, l_val_c_ignore = extraer_promedio(row_h)
                    h_xg = float(row_h.get('xG', 0)) / float(row_h.get('MP', 1))
                except: pass
            # Auto-llenado Defensa desde Standard Opp
            if "Standard Opp" in st.session_state.data_master:
                df_opp = st.session_state.data_master["Standard Opp"]
                try:
                    row_h_c = df_opp[df_opp['Squad'].str.contains(local_sel, na=False)].iloc[0].to_dict()
                    l_val_f_ignore, l_val_c = extraer_promedio(row_h_c)
                except: pass

    with c2:
        st.markdown("**✈️ Visitante**")
        visita_sel = st.selectbox("Equipo visitante", equipos_lista, key="visita_sel", label_visibility="collapsed")
        if visita_sel != "— sin equipo —":
            if "Standard Squad" in st.session_state.data_master:
                df_std = st.session_state.data_master["Standard Squad"]
                try:
                    row_v = df_std[df_std['Squad'] == visita_sel].iloc[0].to_dict()
                    v_val_f, v_val_c_ignore = extraer_promedio(row_v)
                    v_xg = float(row_v.get('xG', 0)) / float(row_v.get('MP', 1))
                except: pass
            if "Standard Opp" in st.session_state.data_master:
                df_opp = st.session_state.data_master["Standard Opp"]
                try:
                    row_v_c = df_opp[df_opp['Squad'].str.contains(visita_sel, na=False)].iloc[0].to_dict()
                    v_val_f_ignore, v_val_c = extraer_promedio(row_v_c)
                except: pass

    cp1, cp2 = st.columns(2)
    with cp1:
        local_label = local_sel if local_sel != "— sin equipo —" else "Local"
        g_l_f = st.number_input(f"⚽ Promedio favor — {local_label}", value=float(f"{l_val_f:.2f}"), step=0.1, format="%.2f")
        g_l_c = st.number_input(f"🛡️ Promedio contra — {local_label}", value=float(f"{l_val_c:.2f}"), step=0.1, format="%.2f")
    with cp2:
        visita_label = visita_sel if visita_sel != "— sin equipo —" else "Visitante"
        g_v_f = st.number_input(f"⚽ Promedio favor — {visita_label}", value=float(f"{v_val_f:.2f}"), step=0.1, format="%.2f")
        g_v_c = st.number_input(f"🛡️ Promedio contra — {visita_label}", value=float(f"{v_val_c:.2f}"), step=0.1, format="%.2f")

    p_l, p_v, p_e, lam_l, lam_v, matrix = calc_poisson(g_l_f, g_l_c, g_v_f, g_v_c)
    total_goles_esp = lam_l + lam_v

    # Probabilidades visuales
    st.markdown("&nbsp;", unsafe_allow_html=True)
    pb1, pb2, pb3 = st.columns(3)
    for col, label, prob, color in [(pb1, f"🏠 {local_label}", p_l, "#818cf8"), (pb2, "🤝 Empate", p_e, "#94a3b8"), (pb3, f"✈️ {visita_label}", p_v, "#f59e0b")]:
        with col:
            st.markdown(f"""
            <div class="prob-bar-wrap">
                <div class="prob-bar-label"><span>{label}</span><span style="color:{color};font-weight:600;">{prob*100:.1f}%</span></div>
                <div class="prob-bar-bg"><div class="prob-bar-fill" style="width:{prob*100:.1f}%;background:{color};"></div></div>
            </div>""", unsafe_allow_html=True)

    # Over / Under
    st.markdown("&nbsp;", unsafe_allow_html=True)
    p_over25 = sum(v for (i,j), v in matrix.items() if i+j > 2)
    p_under25 = 1 - p_over25
    p_btts = sum(v for (i,j), v in matrix.items() if i > 0 and j > 0)

    ou1, ou2, ou3, ou4 = st.columns(4)
    with ou1: st.markdown(f'<div class="ou-card"><div class="ou-value">{total_goles_esp:.2f}</div><div class="ou-label">Goles Esperados</div></div>', unsafe_allow_html=True)
    with ou2: st.markdown(f'<div class="ou-card"><div class="ou-value" style="color:#10b981;">{p_over25*100:.1f}%</div><div class="ou-label">Over 2.5</div></div>', unsafe_allow_html=True)
    with ou3: st.markdown(f'<div class="ou-card"><div class="ou-value" style="color:#ef4444;">{p_under25*100:.1f}%</div><div class="ou-label">Under 2.5</div></div>', unsafe_allow_html=True)
    with ou4: st.markdown(f'<div class="ou-card"><div class="ou-value" style="color:#c084fc;">{p_btts*100:.1f}%</div><div class="ou-label">Ambos Anotan</div></div>', unsafe_allow_html=True)
    
    st.caption(f"ℹ️ Referencia xG/partido: {local_label} ({h_xg:.2f}) vs {visita_label} ({v_xg:.2f})")

    # Marcador más probable
    marcadores_top = sorted(matrix.items(), key=lambda x: x[1], reverse=True)[:5]
    with st.expander("🔬 Ver marcadores más probables"):
        col_m = st.columns(5)
        for idx, ((i, j), prob) in enumerate(marcadores_top):
            with col_m[idx]:
                st.markdown(f'<div style="text-align:center;background:#0f1117;border:1px solid #1e2330;border-radius:10px;padding:14px 10px;"><div style="font-size:1.3rem;font-weight:700;font-family:\'JetBrains Mono\',monospace;color:#818cf8;">{i} – {j}</div><div style="font-size:0.75rem;color:#64748b;margin-top:4px;font-family:\'JetBrains Mono\',monospace;">{prob*100:.1f}%</div></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2 — MOMIOS
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-header"><span class="section-badge">02</span><span class="section-title">Mejores Momios</span></div>', unsafe_allow_html=True)
    cm1, cm2, cm3, cm4 = st.columns([1,1,1,1])
    with cm1: m_l = st.number_input("Momio Local", value=2.0, step=0.05, format="%.2f")
    with cm2: m_e = st.number_input("Momio Empate", value=3.0, step=0.05, format="%.2f")
    with cm3: m_v = st.number_input("Momio Visita", value=3.5, step=0.05, format="%.2f")
    with cm4:
        margen = (1/m_l + 1/m_e + 1/m_v - 1) * 100
        st.markdown(f'<div style="background:#0f1117;border:1px solid #1e2330;border-radius:10px;padding:12px 16px;margin-top:28px;"><div style="font-size:0.65rem;color:#4a5568;text-transform:uppercase;letter-spacing:0.1em;font-family:\'JetBrains Mono\',monospace;">Margen Casa</div><div style="font-size:1.3rem;font-weight:700;font-family:\'JetBrains Mono\',monospace;color:#f59e0b;">{margen:.2f}%</div></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3 — PICKS CON VALOR
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-header"><span class="section-badge">03</span><span class="section-title">Picks con Valor</span></div>', unsafe_allow_html=True)
    picks_eval = [(f"Local · {local_label}", p_l, m_l), ("Empate", p_e, m_e), (f"Visita · {visita_label}", p_v, m_v)]
    c_res = st.columns(3)
    for i, (nombre, prob, momio) in enumerate(picks_eval):
        ev = ev_pct(prob, momio); kelly = get_kelly(prob, momio, fractional_kelly); stake = st.session_state.banca_actual * kelly
        clase = "positive" if ev > 0 else "negative"
        with c_res[i]:
            st.markdown(f'<div class="pick-card {clase}"><div class="pick-name">{nombre}</div><div class="pick-ev {"positive" if ev > 0 else "negative"}">{"+" if ev > 0 else ""}{ev:.1f}% EV</div><div class="pick-details"><div class="detail-item"><div class="dl">Prob</div><div class="dv">{prob*100:.1f}%</div></div><div class="detail-item"><div class="dl">Momio</div><div class="dv">×{momio:.2f}</div></div><div class="detail-item"><div class="dl">Stake</div><div class="dv" style="color:#f59e0b;">{fmt_money(stake)}</div></div></div></div>', unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)
    btn_col, info_col = st.columns([1, 2])
    with btn_col: pick_sel = st.selectbox("Pick a agregar", [p[0] for p in picks_eval], key="pick_agregar")
    with info_col:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        if st.button("📥 Agregar a la Jornada", use_container_width=True):
            idx_p = [p[0] for p in picks_eval].index(pick_sel); n_p, prob_p, mom_p = picks_eval[idx_p]
            k_p = get_kelly(prob_p, mom_p, fractional_kelly); s_p = st.session_state.banca_actual * k_p
            st.session_state.jornada_pendientes.append({'partido': f"{local_label} vs {visita_label}", 'pick': n_p.split(" · ")[-1], 'momio': mom_p, 'stake': round(s_p, 2), 'prob': round(prob_p, 4), 'ev': round(ev_pct(prob_p, mom_p), 2), 'estado': 'Pendiente'})
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════════
    # SECCIÓN 4 — GESTIÓN DE JORNADA
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-header" style="margin-top:36px;"><span class="section-badge">04</span><span class="section-title">Gestión de la Jornada</span></div>', unsafe_allow_html=True)
    if not st.session_state.jornada_pendientes:
        st.markdown('<div style="text-align:center;padding:40px;color:#334155;border:1px dashed #1e2330;border-radius:12px;"><div style="font-size:2rem;">📋</div><div style="margin-top:8px;font-size:0.9rem;">No hay apuestas en la jornada</div></div>', unsafe_allow_html=True)
    else:
        for idx_j, ap in enumerate(st.session_state.jornada_pendientes):
            col_est = {"Pendiente": "#f59e0b", "GANADA": "#10b981", "PERDIDA": "#ef4444"}.get(ap['estado'], "#94a3b8")
            st.markdown(f'<div class="jornada-row"><div style="flex:2;"><div class="jr-partido">{ap["partido"]}</div><div style="margin-top:4px;"><span class="jr-badge">{ap["pick"]}</span></div></div><div style="text-align:center;"><div class="jr-stake">{fmt_money(ap["stake"])}</div></div><div style="text-align:center;"><div class="jr-momio">×{ap["momio"]:.2f}</div></div><div style="text-align:center;"><div style="font-size:0.9rem;font-weight:700;color:{col_est};">{ap["estado"]}</div></div></div>', unsafe_allow_html=True)
        with st.expander("💰 Cerrar Apuesta"):
            idx_s = st.selectbox("Selecciona:", range(len(st.session_state.jornada_pendientes)), format_func=lambda i: st.session_state.jornada_pendientes[i]["partido"])
            res = st.radio("Resultado:", ["GANADA", "PERDIDA"], horizontal=True)
            if st.button("✅ Actualizar Banca"):
                ap = st.session_state.jornada_pendientes[idx_s]; st.session_state.banca_actual += (ap['stake'] * (ap['momio'] - 1)) if res == "GANADA" else -ap['stake']
                st.session_state.historial.append({**ap, 'estado': res, 'resultado': (ap['stake'] * (ap['momio'] - 1)) if res == "GANADA" else -ap['stake']})
                st.session_state.jornada_pendientes.pop(idx_s); st.rerun()

    # ══════════════════════════════════════════════════════════════════════════════
    # SECCIÓN 5 — HISTORIAL
    # ══════════════════════════════════════════════════════════════════════════════
    if st.session_state.historial:
        st.markdown('<div class="section-header" style="margin-top:36px;"><span class="section-badge">05</span><span class="section-title">Historial & Estadísticas</span></div>', unsafe_allow_html=True)
        h = st.session_state.historial; g = sum(1 for x in h if x['estado'] == 'GANADA'); r_n = sum(x['resultado'] for x in h)
        h1, h2, h3 = st.columns(3)
        h1.metric("Apuestas", len(h)); h2.metric("Aciertos", f"{(g/len(h)*100):.1f}%"); h3.metric("Neta", fmt_money(r_n))
        st.dataframe(pd.DataFrame(h)[['partido', 'pick', 'momio', 'stake', 'estado', 'resultado']], use_container_width=True, hide_index=True)
