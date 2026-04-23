import streamlit as st
import pandas as pd
import math
import io

st.set_page_config(page_title="Jorge - Betting Intelligence Pro", layout="wide")

# --- PERSISTENCIA ---
if 'banca_actual' not in st.session_state:
    st.session_state.banca_actual = 1000.0
if 'jornada_analizada' not in st.session_state:
    st.session_state.jornada_analizada = []

# --- SIDEBAR ---
st.sidebar.header("⚙️ Gestión de Capital")
banca_base = st.sidebar.number_input("💰 Banca Inicial", value=1000.0)
st.sidebar.metric("🏦 Banca Actual", f"${st.session_state.banca_actual:.2f}")

if st.sidebar.button("🗑️ Limpiar Toda la Jornada"):
    st.session_state.jornada_analizada = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Datos FBRef")
raw_data = st.sidebar.text_area("Pega la tabla aquí", height=100)

df_stats = None
equipos_lista = ["Selecciona equipo..."]
col_name = None

if raw_data:
    try:
        df_stats = pd.read_csv(io.StringIO(raw_data), sep=None, engine='python')
        df_stats = df_stats.loc[:, ~df_stats.columns.str.contains('^Unnamed')]
        col_name = st.sidebar.selectbox("Columna de Nombres", df_stats.columns)
        equipos_lista = ["Selecciona equipo..."] + df_stats[col_name].dropna().unique().tolist()
    except:
        st.sidebar.error("Error al leer datos.")

fractional_kelly = st.sidebar.slider("📉 Agresividad Kelly", 0.05, 1.0, 0.25)

# --- CUERPO PRINCIPAL ---
st.title("🚀 Betting Intelligence Tool")

# 1. ANÁLISIS
st.header("1️⃣ Análisis del Encuentro")
c1, c2 = st.columns(2)

l_gf, l_gc, v_gf, v_gc = 1.5, 1.1, 1.0, 1.2

with c1:
    local_sel = st.selectbox("Local", equipos_lista)
    if df_stats is not None and local_sel != "Selecciona equipo...":
        row = df_stats[df_stats[col_name] == local_sel].iloc[0]
        l_gf = float(row.get('xG', row.get('Gls', 1.5)))
        l_gc = float(row.get('GA', 1.1))

with c2:
    visita_sel = st.selectbox("Visita", equipos_lista)
    if df_stats is not None and visita_sel != "Selecciona equipo...":
        row = df_stats[df_stats[col_name] == visita_sel].iloc[0]
        v_gf = float(row.get('xG', row.get('Gls', 1.0)))
        v_gc = float(row.get('GA', 1.2))

cp1, cp2 = st.columns(2)
g_l_f = cp1.number_input(f"Goles Favor {local_sel}", value=float(l_gf))
g_l_c = cp1.number_input(f"Goles Contra {local_sel}", value=float(l_gc))
g_v_f = cp2.number_input(f"Goles Favor {visita_sel}", value=float(v_gf))
g_v_c = cp2.number_input(f"Goles Contra {visita_sel}", value=float(v_gc))

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

prob_l, prob_v, prob_e = calc_poisson(g_l_f, g_l_c, g_v_f, g_v_c)

# 2. MOMIOS
st.header("2️⃣ Mejores Momios")
cm1, cm2, cm3 = st.columns(3)
m_l = cm1.number_input("Momio Local", value=2.0)
m_e = cm2.number_input("Momio Empate", value=3.0)
m_v = cm3.number_input("Momio Visita", value=3.0)

# 3. VALOR (CORREGIDO)
st.header("3️⃣ Picks con Valor")
def get_k(p, m):
    b = m - 1
    return max(0, ((b * p - (1 - p)) / b) * fractional_kelly) if b > 0 else 0

picks = [("Local", prob_l, m_l), ("Empate", prob_e, m_e), ("Visita", prob_v, m_v)]
c_res = st.columns(3)

for i, (nombre, p, m) in enumerate(picks):
    ev = (p * m - 1) * 100 # FÓRMULA CORREGIDA
    stake = st.session_state.banca_actual * get_k(p, m)
    with c_res[i]:
        if ev > 0:
            st.success(f"✅ {nombre}: EV +{ev:.1f}%")
            st.metric("Stake Sugerido", f"${stake:.2f}")
        else:
            st.error(f"❌ {nombre}: EV {ev:.1f}%")

if st.button("📥 AGREGAR A LA JORNADA"):
    # Guardamos el estado actual para cobrar después
    st.session_state.jornada_analizada.append({
        "Partido": f"{local_sel} vs {visita_sel}",
        "Pick": "Local", # Por defecto
        "Momio": m_l,
        "Stake": stake,
        "Prob": p,
        "Estado": "Pendiente"
    })
    st.rerun()

# 4. EXPLICACIÓN PASO 4: LA BITÁCORA DE CIERRE
st.markdown("---")
st.header("4️⃣ Gestión de la Jornada (Cobro)")
st.info("Aquí se guardan tus análisis. El lunes, selecciona el resultado y dale a 'Cerrar Jornada'.")

if st.session_state.jornada_analizada:
    df_jornada = pd.DataFrame(st.session_state.jornada_analizada)
    st.table(df_jornada)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        idx = st.selectbox("Selecciona Partido para Cerrar", range(len(st.session_state.jornada_analizada)), 
                           format_func=lambda i: st.session_state.jornada_analizada[i]["Partido"])
        resultado = st.radio("¿Qué pasó?", ["Ganada", "Perdida"])
    
    with col_c2:
        if st.button("💰 Procesar Resultado"):
            partido = st.session_state.jornada_analizada[idx]
            if resultado == "Ganada":
                ganancia = (partido["Stake"] * partido["Momio"]) - partido["Stake"]
                st.session_state.banca_actual += ganancia
            else:
                st.session_state.banca_actual -= partido["Stake"]
            
            st.session_state.jornada_analizada.pop(idx)
            st.success("Banca actualizada.")
            st.rerun()
