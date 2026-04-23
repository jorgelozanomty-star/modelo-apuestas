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

/* ── DATA HUB STATUS ── */
.status-box { padding: 8px; border-radius: 6px; margin-top: 5px; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; text-align: center;}
.loaded { background: rgba(16,185,129,0.15); border: 1px solid #10b981; color: #10b981; }
.empty { background: rgba(148, 163, 184, 0.05); border: 1px solid #334155; color: #64748b; }

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
    ('data_master', {}),
]:
    if key not in st.session_state:
        st.session_state[key] = val

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def process_fbref_paste(text):
    if not text or len(text) < 10: return None
    try:
        clean_text = text.replace("Club Crest", "").strip()
        df = pd.read_csv(io.StringIO(clean_text), sep='\t')
        if len(df.columns) < 2: df = pd.read_csv(io.StringIO(clean_text), sep=None, engine='python')
        df.columns = [c.strip() for c in df.columns]
        if 'Squad' in df.columns:
            df['Squad'] = df['Squad'].str.replace("Club Crest", "").str.strip()
            df['Squad'] = df['Squad'].replace(EQUIPOS_MAP)
        return df
    except: return None

def calc_poisson(gf_l, gc_l, gf_v, gc_v):
    lam_l = max(0.1, (gf_l + gc_v) / 2)
    lam_v = max(0.1, (gf_v + gc_l) / 2)
    p_l = p_v = p_e = 0.0
    matrix = {}
    for i in range(8):
        for j in range(8):
            prob = (math.exp(-lam_l) * lam_l**i / math.factorial(i)) * (math.exp(-lam_v) * lam_v**j / math.factorial(j))
            matrix[(i, j)] = prob
            if i > j: p_l += prob
            elif j > i: p_v += prob
            else: p_e += prob
    return p_l, p_v, p_e, lam_l, lam_v, matrix

def get_kelly(prob, momio, fraction):
    if momio <= 1: return 0
    edge = ((momio - 1) * prob) - (1 - prob)
    return max(0.0, (edge / (momio - 1)) * fraction)

def fmt_money(v): return f"${v:,.2f}"
def ev_pct(prob, momio): return (prob * momio - 1) * 100
def roi():
    if st.session_state.banca_inicial == 0: return 0
    return ((st.session_state.banca_actual - st.session_state.banca_inicial) / st.session_state.banca_inicial) * 100

def extraer_promedio(fila):
    mp = float(fila.get('MP', 1) or 1)
    gf = float(fila.get('GF', fila.get('Gls', 1.5)) or 1.5)
    ga = float(fila.get('GA', 1.1) or 1.1)
    return (gf / mp if gf > 5 else gf), (ga / mp if ga > 5 else ga)

# ─── LAYOUT ───────────────────────────────────────────────────────────────────
col_izq, col_main, col_der = st.columns([0.8, 2.5, 1])

# ─── IZQUIERDA: GESTIÓN ───────────────────────────────────────────────────────
with col_izq:
    st.markdown("### ⚙️ Control")
    st.markdown(f"""<div class="banca-display"><div class="bd-label">Banca Actual</div><div class="bd-value">{fmt_money(st.session_state.banca_actual)}</div><div class="bd-roi {'pos' if roi()>0 else 'neg'}">ROI: {roi():.2f}%</div></div>""", unsafe_allow_html=True)
    f_kelly = st.slider("Kelly", 0.05, 1.0, 0.25, step=0.05)
    if st.button("🗑️ Limpiar Jornada"):
        st.session_state.jornada_pendientes = []
        st.rerun()

# ─── DERECHA: DATA HUB ────────────────────────────────────────────────────────
with col_der:
    st.markdown("### 📥 Data Hub")
    tablas = ["Tabla General", "Standard Squad", "Standard Opp", "Shooting Squad", "Shooting Opp", "PlayingTime Squad", "PlayingTime Opp", "Misc Squad", "Misc Opp"]
    for t in tablas:
        with st.expander(f"📄 {t}"):
            input_data = st.text_area("Pegar FBRef", key=f"in_{t}", height=80, label_visibility="collapsed")
            processed = process_fbref_paste(input_data)
            if processed is not None:
                st.session_state.data_master[t] = processed
                st.markdown(f'<div class="status-box loaded">VINCULADA ({len(processed)} eqs)</div>', unsafe_allow_html=True)
            else: st.markdown('<div class="status-box empty">VACÍO</div>', unsafe_allow_html=True)

# ─── CENTRAL: ANÁLISIS ────────────────────────────────────────────────────────
with col_main:
    st.markdown('<div class="main-header"><h1>📡 Intelligence Pro</h1><p>Poisson · Kelly · Data Hub Integration</p></div>', unsafe_allow_html=True)
    
    equipos_lista = ["— sin equipo —"]
    if st.session_state.data_master:
        first_df = next(iter(st.session_state.data_master.values()))
        equipos_lista += sorted(first_df['Squad'].unique().tolist())

    st.markdown('<div class="section-header"><span class="section-badge">01</span><span class="section-title">Análisis del Encuentro</span></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    l_val_f, l_val_c, v_val_f, v_val_c, h_xg, v_xg = 1.5, 1.1, 1.0, 1.2, 0.0, 0.0

    with c1:
        local_sel = st.selectbox("Equipo local", equipos_lista, key="local_sel")
        if local_sel != "— sin equipo —":
            if "Standard Squad" in st.session_state.data_master:
                row = st.session_state.data_master["Standard Squad"][st.session_state.data_master["Standard Squad"]['Squad'] == local_sel].iloc[0]
                l_val_f, _ = extraer_promedio(row); h_xg = float(row.get('xG', 0)) / float(row.get('MP', 1))
            if "Standard Opp" in st.session_state.data_master:
                row_c = st.session_state.data_master["Standard Opp"][st.session_state.data_master["Standard Opp"]['Squad'].str.contains(local_sel, na=False)].iloc[0]
                _, l_val_c = extraer_promedio(row_c)

    with c2:
        visita_sel = st.selectbox("Equipo visitante", equipos_lista, key="visita_sel")
        if visita_sel != "— sin equipo —":
            if "Standard Squad" in st.session_state.data_master:
                row = st.session_state.data_master["Standard Squad"][st.session_state.data_master["Standard Squad"]['Squad'] == visita_sel].iloc[0]
                v_val_f, _ = extraer_promedio(row); v_xg = float(row.get('xG', 0)) / float(row.get('MP', 1))
            if "Standard Opp" in st.session_state.data_master:
                row_c = st.session_state.data_master["Standard Opp"][st.session_state.data_master["Standard Opp"]['Squad'].str.contains(visita_sel, na=False)].iloc[0]
                _, v_val_c = extraer_promedio(row_c)

    cp1, cp2 = st.columns(2)
    g_l_f = cp1.number_input(f"⚽ Favor {local_sel}", value=float(l_val_f), format="%.2f")
    g_l_c = cp1.number_input(f"🛡️ Contra {local_sel}", value=float(l_val_c), format="%.2f")
    g_v_f = cp2.number_input(f"⚽ Favor {visita_sel}", value=float(v_val_f), format="%.2f")
    g_v_c = cp2.number_input(f"🛡️ Contra {visita_sel}", value=float(v_val_c), format="%.2f")

    p_l, p_v, p_e, lam_l, lam_v, matrix = calc_poisson(g_l_f, g_l_c, g_v_f, g_v_c)
    total_goles_esp = lam_l + lam_v

    st.markdown("&nbsp;", unsafe_allow_html=True)
    pb1, pb2, pb3 = st.columns(3)
    for col, label, prob, color in [(pb1, f"🏠 {local_sel}", p_l, "#818cf8"), (pb2, "🤝 Empate", p_e, "#94a3b8"), (pb3, f"✈️ {visita_sel}", p_v, "#f59e0b")]:
        with col:
            st.markdown(f'<div class="prob-bar-wrap"><div class="prob-bar-label"><span>{label}</span><span style="color:{color};">{prob*100:.1f}%</span></div><div class="prob-bar-bg"><div class="prob-bar-fill" style="width:{prob*100:.1f}%;background:{color};"></div></div></div>', unsafe_allow_html=True)

    ou1, ou2, ou3, ou4 = st.columns(4)
    with ou1: st.markdown(f'<div class="ou-card"><div class="ou-value">{total_goles_esp:.2f}</div><div class="ou-label">xG Part</div></div>', unsafe_allow_html=True)
    with ou2: st.markdown(f'<div class="ou-card"><div class="ou-value" style="color:#10b981;">{(sum(v for (i,j),v in matrix.items() if i+j>2))*100:.1f}%</div><div class="ou-label">Over 2.5</div></div>', unsafe_allow_html=True)
    with ou3: st.markdown(f'<div class="ou-card"><div class="ou-value" style="color:#ef4444;">{(1-sum(v for (i,j),v in matrix.items() if i+j>2))*100:.1f}%</div><div class="ou-label">Under 2.5</div></div>', unsafe_allow_html=True)
    with ou4: st.markdown(f'<div class="ou-card"><div class="ou-value" style="color:#c084fc;">{(sum(v for (i,j),v in matrix.items() if i>0 and j>0))*100:.1f}%</div><div class="ou-label">BTTS</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header"><span class="section-badge">02</span><span class="section-title">Momios</span></div>', unsafe_allow_html=True)
    cm1, cm2, cm3 = st.columns(3)
    m_l, m_e, m_v = cm1.number_input("L", 2.0), cm2.number_input("E", 3.0), cm3.number_input("V", 3.0)

    st.markdown('<div class="section-header"><span class="section-badge">03</span><span class="section-title">Picks</span></div>', unsafe_allow_html=True)
    picks_eval = [("Local", p_l, m_l), ("Empate", p_e, m_e), ("Visita", p_v, m_v)]
    c_res = st.columns(3)
    for i, (n, p, m) in enumerate(picks_eval):
        ev = ev_pct(p, m); k = get_kelly(p, m, f_kelly); s_p = st.session_state.banca_actual * k
        with c_res[i]:
            st.markdown(f'<div class="pick-card {"positive" if ev>0 else "negative"}"><div class="pick-name">{n}</div><div class="pick-ev {"positive" if ev>0 else "negative"}">{ev:.1f}% EV</div><div style="font-size:0.8rem;">Stake: {fmt_money(s_p)}</div></div>', unsafe_allow_html=True)

    if st.button("📥 Agregar a Jornada"):
        mejor = max(picks_eval, key=lambda x: ev_pct(x[1], x[2]))
        st.session_state.jornada_pendientes.append({'partido': f"{local_sel} vs {visita_sel}", 'pick': mejor[0], 'momio': mejor[2], 'stake': round(st.session_state.banca_actual * get_kelly(mejor[1], mejor[2], f_kelly), 2), 'estado': 'Pendiente'})
        st.rerun()

    if st.session_state.jornada_pendientes:
        st.markdown('<div class="section-header"><span class="section-badge">04</span><span class="section-title">Gestión de Jornada</span></div>', unsafe_allow_html=True)
        st.table(pd.DataFrame(st.session_state.jornada_pendientes))
        with st.expander("💰 Cerrar Apuesta"):
            idx = st.selectbox("Partido:", range(len(st.session_state.jornada_pendientes)), format_func=lambda i: st.session_state.jornada_pendientes[i]['partido'])
            res = st.radio("Resultado:", ["GANADA", "PERDIDA"], horizontal=True)
            if st.button("✅ Actualizar"):
                ap = st.session_state.jornada_pendientes[idx]
                st.session_state.banca_actual += (ap['stake'] * (ap['momio'] - 1)) if res=="GANADA" else -ap['stake']
                st.session_state.historial.append({**ap, 'estado': res, 'resultado': (ap['stake'] * (ap['momio'] - 1)) if res=="GANADA" else -ap['stake']})
                st.session_state.jornada_pendientes.pop(idx); st.rerun()

    if st.session_state.historial:
        st.markdown('<div class="section-header"><span class="section-badge">05</span><span class="section-title">Historial</span></div>', unsafe_allow_html=True)
        h = pd.DataFrame(st.session_state.historial)
        st.dataframe(h[['partido', 'pick', 'momio', 'stake', 'estado', 'resultado']], use_container_width=True, hide_index=True)
