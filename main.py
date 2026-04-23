import streamlit as st
import pandas as pd
import math
import io

# Configuración para tu monitor de 34"
st.set_page_config(page_title="Jorge - Betting Intelligence Pro", layout="wide")

# --- PERSISTENCIA ---
if 'banca_actual' not in st.session_state:
    st.session_state.banca_actual = 1000.0
if 'historial_partidos' not in st.session_state:
    st.session_state.historial_partidos = []

# --- SIDEBAR: CONFIGURACIÓN Y DATOS ---
st.sidebar.header("⚙️ Gestión de Capital")
banca_base = st.sidebar.number_input("💰 Banca Inicial", value=1000.0)
st.sidebar.metric("🏦 Banca Actual", f"${st.session_state.banca_actual:.2f}", 
                  f"{st.session_state.banca_actual - banca_base:.2f}")

if st.sidebar.button("🔄 Resetear Sesión"):
    st.session_state.banca_actual = banca_base
    st.session_state.historial_partidos = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Importar de FBRef")
raw_data = st.sidebar.text_area("Pega la tabla aquí (Ctrl+V)", height=150)

df_stats = None
equipos_lista = ["Selecciona equipo..."]
col_name = None

if raw_data:
    try:
        df_stats = pd.read_csv(io.StringIO(raw_data), sep=None, engine='python')
        df_stats = df_stats.loc[:, ~df_stats.columns.str.contains('^Unnamed')]
        col_name = st.sidebar.selectbox("Columna con Nombres", df_stats.columns)
        equipos_lista = ["Selecciona equipo..."] + df_stats[col_name].dropna().unique().tolist()
        st.sidebar.success(f"✅ {len(equipos_lista)-1} equipos cargados")
    except:
        st.sidebar.error("Formato no reconocido. Prueba copiar solo filas de datos.")

fractional_kelly = st.sidebar.slider("📉 Agresividad Kelly", 0.05, 1.0, 0.25)

# --- CUERPO PRINCIPAL ---
st.title("🚀 Intelligence Betting Tool: Versión Completa")

# 1. SELECCIÓN Y PROBABILIDAD (POISSON)
st.header("1️⃣ Análisis Estadístico (Poisson)")
c1, c2 = st.columns(2)

l_gf, l_gc, v_gf, v_gc = 1.5, 1.1, 1.0, 1.2

with c1:
    local_sel = st.selectbox("Equipo Local", equipos_lista)
    if df_stats is not None and local_sel != "Selecciona equipo...":
        row = df_stats[df_stats[col_name] == local_sel].iloc[0]
        l_gf = float(row.get('xG', row.get('Gls', 1.5)))
        l_gc = float(row.get('GA', 1.1))

with c2:
    visita_sel = st.selectbox("Equipo Visita", equipos_lista)
    if df_stats is not None and visita_sel != "Selecciona equipo...":
        row = df_stats[df_stats[col_name] == visita_sel].iloc[0]
        v_gf = float(row.get('xG', row.get('Gls', 1.0)))
        v_gc = float(row.get('GA', 1.2))

# Inputs Poisson (Auto-llenados)
cp1, cp2 = st.columns(2)
g_l_f = cp1.number_input(f"Goles Favor {local_sel}", value=float(l_gf), step=0.1)
g_l_c = cp1.number_input(f"Goles Contra {local_sel}", value=float(l_gc), step=0.1)
g_v_f = cp2.number_input(f"Goles Favor {visita_sel}", value=float(v_gf), step=0.1)
g_v_c = cp2.number_input(f"Goles Contra {visita_sel}", value=float(v_gc), step=0.1)

def calc_poisson(gf_l, gc_l, gf_v, gc_v):
    lam_l, lam_v = (gf_l + gc_v)/2, (gf_v + gc_l)/2
    p_l, p_v, p_e = 0.0, 0.0, 0.0
    for i in range(10):
        for j in range(10):
            prob = ((math.exp(-lam_l)*lam_l**i)/math.factorial(i)) * ((math.exp(-lam_v)*lam_v**j)/math.factorial(j))
            if i > j: p_l += prob
            elif j > i: p_v += prob
            else: p_e += prob
    return p_l, p_v, p_e

p_l, p_v, p_e = calc_poisson(g_l_f, g_l_c, g_v_f, g_v_c)
st.info(f"📊 Probabilidades Poisson: L {p_l*100:.1f}% | E {p_e*100:.1f}% | V {p_v*100:.1f}%")

st.markdown("---")

# 2. COMPARATIVA DE MOMIOS (MULTI-CASA)
st.header("2️⃣ Comparativa Multi-Casa")
col_bk1, col_bk2 = st.columns(2)

with col_bk1:
    st.subheader("Team Mexico")
    m_l1 = st.number_input("L - Casa A", value=2.0)
    m_e1 = st.number_input("E - Casa A", value=3.2)
    m_v1 = st.number_input("V - Casa A", value=3.0)

with col_bk2:
    st.subheader("Caliente")
    m_l2 = st.number_input("L - Casa B", value=2.05)
    m_e2 = st.number_input("E - Casa B", value=3.1)
    m_v2 = st.number_input("V - Casa B", value=3.15)

best_l, best_e, best_v = max(m_l1, m_l2), max(m_e1, m_e2), max(m_v1, m_v2)
payout = (1/best_l) + (1/best_e) + (1/best_v)
st.success(f"🏆 Mejores momios detectados. Margen: {(payout-1)*100:.2f}%")

st.markdown("---")

# 3. ANÁLISIS DE VALOR Y KELLY
st.header("3️⃣ Análisis de Valor")
def get_k(prob, m):
    b = m - 1
    return max(0, ((b * prob - (1 - prob)) / b) * fractional_kelly) if b > 0 else 0

st_l, st_e, st_v = st.session_state.banca_actual * get_k(p_l, best_l), st.session_state.banca_actual * get_k(p_e, best_e), st.session_state.banca_actual * get_k(p_v, best_v)

c_res = st.columns(3)
picks = [("Local", p_l, best_l, st_l), ("Empate", p_e, best_e, st_e), ("Visita", p_v, best_v, st_v)]

for i, (nombre, prob, momio, stake) in enumerate(picks):
    ev = (prob * momio - 1) * 100
    with c_res[i]:
        if ev > 0:
            st.success(f"✅ {nombre}: EV +{ev:.1f}%")
            st.metric("Stake Sugerido", f"${stake:.2f}")
        else:
            st.error(f"❌ {nombre}: EV {ev:.1f}%")

if st.button("📥 GUARDAR EN BITÁCORA"):
    if local_sel != "Selecciona equipo...":
        mejor_op = max(picks, key=lambda x: x[3])
        st.session_state.historial_partidos.append({
            "Partido": f"{local_sel} vs {visita_sel}",
            "Pick": mejor_op[0],
            "Momio": mejor_op[2],
            "Stake": f"${mejor_op[3]:.2f}"
        })
        st.rerun()

# 4. SIMULADOR DE CIERRE Y TABLA
st.markdown("---")
st.header("4️⃣ Simulador de Cierre y Bitácora")
col_sim, col_hist = st.columns([1, 2])

with col_sim:
    res_final = st.radio("Resultado del partido:", ["Local", "Empate", "Visita"], horizontal=True)
    if st.button("💰 Calcular Ganancia y Actualizar Banca"):
        ganancia = 0
        if res_final == "Local": ganancia = (st_l * best_l) - (st_l + st_e + st_v)
        elif res_final == "Empate": ganancia = (st_e * best_e) - (st_l + st_e + st_v)
        else: ganancia = (st_v * best_v) - (st_l + st_e + st_v)
        
        st.session_state.banca_actual += ganancia
        st.rerun()

with col_hist:
    if st.session_state.historial_partidos:
        st.table(pd.DataFrame(st.session_state.historial_partidos))
