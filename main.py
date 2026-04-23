import streamlit as st
import pandas as pd
import math
import io
import numpy as np

# ─── CONFIGURACIÓN E IDENTIDAD ────────────────────────────────────────────────
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

# ─── CUSTOM CSS (TU DISEÑO ORIGINAL) ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif !important; }
.stApp { background: #0a0c10 !important; color: #e2e8f0 !important; }
section[data-testid="stSidebar"] { background: #0f1117 !important; border-right: 1px solid #1e2330 !important; }
.main-header { background: linear-gradient(135deg, #0f1117 0%, #131824 100%); border: 1px solid #1e2330; border-radius: 16px; padding: 28px 36px; margin-bottom: 28px; }
.main-header h1 { background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%); -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; margin: 0 !important; }
.stat-card { background: #0f1117; border: 1px solid #1e2330; border-radius: 12px; padding: 20px 24px; }
.pick-card.positive { background: linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(5,150,105,0.04) 100%); border-color: rgba(16,185,129,0.25); }
.pick-card.negative { background: linear-gradient(135deg, rgba(239,68,68,0.06) 0%, rgba(220,38,38,0.03) 100%); border-color: rgba(239,68,68,0.15); }
.jr-stake { font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #f59e0b; }
.status-box { padding: 10px; border-radius: 8px; margin-top: 5px; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; }
.loaded { background: rgba(16,185,129,0.1); border: 1px solid #10b981; color: #10b981; }
</style>
""", unsafe_allow_html=True)

# ─── PERSISTENCIA ──────────────────────────────────────────────────────────────
if 'banca_actual' not in st.session_state: st.session_state.banca_actual = 1000.0
if 'jornada_pendientes' not in st.session_state: st.session_state.jornada_pendientes = []
if 'data_master' not in st.session_state: st.session_state.data_master = {}

# ─── FUNCIONES DE MOTOR ───────────────────────────────────────────────────────
def process_paste(text):
    if not text or len(text) < 10: return None
    try:
        df = pd.read_csv(io.StringIO(text), sep='\t')
        if len(df.columns) < 2: df = pd.read_csv(io.StringIO(text), sep=None, engine='python')
        df.columns = [c.strip() for c in df.columns]
        if 'Squad' in df.columns: df['Squad'] = df['Squad'].replace(EQUIPOS_MAP)
        return df
    except: return None

def calc_poisson(gf_l, gc_l, gf_v, gc_v):
    lam_l, lam_v = (gf_l + gc_v) / 2, (gf_v + gc_l) / 2
    p_l = p_v = p_e = 0.0
    matrix = {}
    for i in range(9):
        for j in range(9):
            prob = (math.exp(-lam_l) * lam_l**i / math.factorial(i)) * (math.exp(-lam_v) * lam_v**j / math.factorial(j))
            matrix[(i,j)] = prob
            if i > j: p_l += prob
            elif j > i: p_v += prob
            else: p_e += prob
    return p_l, p_v, p_e, lam_l, lam_v, matrix

# ─── LAYOUT: TRES COLUMNAS (IZQ: BANCA, CENTRO: APP, DER: DATAHUB) ────────────
col_izq, col_main, col_der = st.columns([1, 2.5, 1.2])

# ─── COLUMNA IZQUIERDA: GESTIÓN ──────────────────────────────────────────────
with col_izq:
    st.markdown(f"""
    <div class="stat-card" style="text-align:center;">
        <div style="font-size:0.7rem; color:#64748b; letter-spacing:0.1em;">BANCA ACTUAL</div>
        <div style="font-size:2rem; font-weight:700; color:#818cf8;">${st.session_state.banca_actual:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    fractional_kelly = st.slider("Kelly", 0.05, 1.0, 0.25)
    
    if st.button("🗑️ Limpiar Todo"):
        st.session_state.jornada_pendientes = []
        st.session_state.data_master = {}
        st.rerun()

# ─── COLUMNA DERECHA: PANEL DE INSUMOS (LOS 9 CUADRITOS) ──────────────────────
with col_der:
    st.markdown("### 📥 Data Hub")
    tablas = [
        "Tabla General", "Standard Squad", "Standard Opp", 
        "Shooting Squad", "Shooting Opp", "PlayingTime Squad", 
        "PlayingTime Opp", "Misc Squad", "Misc Opp"
    ]
    
    for t in tablas:
        with st.expander(f"📄 {t}"):
            input_data = st.text_area("Pegar FBRef", key=f"in_{t}", height=80, label_visibility="collapsed")
            processed = process_paste(input_data)
            if processed is not None:
                st.session_state.data_master[t] = processed
                st.markdown(f'<div class="status-box loaded">COMPLETA ({len(processed)} eqs)</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-box" style="background:#1e2330;">VACÍO</div>', unsafe_allow_html=True)

# ─── COLUMNA CENTRAL: ANÁLISIS Y PREDICCIÓN ───────────────────────────────────
with col_main:
    st.markdown('<div class="main-header"><h1>📡 Intelligence Pro</h1><p>Sistema de Predicción de Goles Reales</p></div>', unsafe_allow_html=True)
    
    # Obtener lista de equipos de cualquier tabla cargada
    equipos_master = ["— Selecciona —"]
    if st.session_state.data_master:
        first_df = list(st.session_state.data_master.values())[0]
        if 'Squad' in first_df.columns:
            equipos_master += sorted(first_df['Squad'].unique().tolist())

    c1, c2 = st.columns(2)
    with c1: h_team = st.selectbox("🏠 Local", equipos_master)
    with c2: v_team = st.selectbox("✈️ Visitante", equipos_master)

    # AUTO-LLENADO INTELIGENTE (Buscamos en las 9 tablas)
    h_f, h_c, v_f, v_c = 1.5, 1.1, 1.0, 1.2
    h_xg, v_xg = 0.0, 0.0

    if h_team != "— Selecciona —" and v_team != "— Selecciona —":
        # Extraer de Standard Squad
        if "Standard Squad" in st.session_state.data_master:
            df = st.session_state.data_master["Standard Squad"]
            try:
                row_h = df[df['Squad'] == h_team].iloc[0]
                h_f = float(row_h.get('Gls', 1.5)) / (float(row_h.get('MP', 1)) if float(row_h.get('Gls', 0)) > 5 else 1)
                h_xg = float(row_h.get('xG', 0))
                
                row_v = df[df['Squad'] == v_team].iloc[0]
                v_f = float(row_v.get('Gls', 1.0)) / (float(row_v.get('MP', 1)) if float(row_v.get('Gls', 0)) > 5 else 1)
                v_xg = float(row_v.get('xG', 0))
            except: pass

        # Extraer de Standard Opp (Defensa)
        if "Standard Opp" in st.session_state.data_master:
            df_opp = st.session_state.data_master["Standard Opp"]
            try:
                row_h_c = df_opp[df_opp['Squad'].str.contains(h_team, na=False)].iloc[0]
                h_c = float(row_h_c.get('GA', 1.1)) / (float(row_h_c.get('MP', 1)) if float(row_h_c.get('GA', 0)) > 5 else 1)
                
                row_v_c = df_opp[df_opp['Squad'].str.contains(v_team, na=False)].iloc[0]
                v_c = float(row_v_c.get('GA', 1.2)) / (float(row_v_c.get('MP', 1)) if float(row_v_c.get('GA', 0)) > 5 else 1)
            except: pass

        # CALCULO POISSON
        p_l, p_v, p_e, lam_h, lam_v, matrix = calc_poisson(h_f, h_c, v_f, v_c)
        
        # DISPLAY METRICS
        st.markdown("### 📊 Probabilidades")
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Victoria {h_team}", f"{p_l*100:.1f}%")
        m2.metric("Empate", f"{p_e*100:.1f}%")
        m3.metric(f"Victoria {v_team}", f"{p_v*100:.1f}%")
        
        st.caption(f"ℹ️ xG Informativo: {h_team} ({h_xg}) vs {v_team} ({v_xg})")

        # MOMIOS Y KELLY
        st.markdown("---")
        st.markdown("### 💰 Momios de Mercado")
        cm1, cm2, cm3 = st.columns(3)
        mom_l = cm1.number_input("Momio L", value=2.0)
        mom_e = cm2.number_input("Momio E", value=3.0)
        mom_v = cm3.number_input("Momio V", value=3.0)

        # GESTION DE PICK
        def get_ev(p, m): return (p * m - 1) * 100
        ev_l = get_ev(p_l, mom_l)
        
        if st.button("📥 Agregar a Jornada"):
            stake = st.session_state.banca_actual * (( (mom_l-1)*p_l - (1-p_l) )/(mom_l-1)) * fractional_kelly if ev_l > 0 else 0
            st.session_state.jornada_pendientes.append({
                "Partido": f"{h_team} vs {v_team}",
                "Pick": h_team, "Momio": mom_l, "Stake": max(0, stake), "Estado": "Pendiente"
            })
            st.toast("Guardado!")

    # TABLA DE JORNADA
    if st.session_state.jornada_pendientes:
        st.markdown("---")
        st.markdown("### 📋 Jornada en Curso")
        df_j = pd.DataFrame(st.session_state.jornada_pendientes)
        st.table(df_j)
        
        # CIERRE DE JORNADA (LUNES)
        with st.expander("💰 Cobrar Partidos"):
            idx = st.selectbox("Selecciona", range(len(st.session_state.jornada_pendientes)), format_func=lambda i: st.session_state.jornada_pendientes[i]["Partido"])
            res = st.radio("Resultado", ["GANADA", "PERDIDA"], horizontal=True)
            if st.button("Actualizar Banca"):
                p = st.session_state.jornada_pendientes[idx]
                if res == "GANADA": st.session_state.banca_actual += (p["Stake"] * p["Momio"]) - p["Stake"]
                else: st.session_state.banca_actual -= p["Stake"]
                st.session_state.jornada_pendientes.pop(idx)
                st.rerun()
