import streamlit as st
import pandas as pd
import math
import io

# Configuración para tu monitor de 34"
st.set_page_config(page_title="Jorge - Betting Intelligence", layout="wide")

# --- PERSISTENCIA DE DATOS ---
if 'banca_actual' not in st.session_state:
    st.session_state.banca_actual = 1000.0
if 'historial_partidos' not in st.session_state:
    st.session_state.historial_partidos = []

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Gestión de Capital")
banca_base = st.sidebar.number_input("💰 Banca Inicial", min_value=0.0, value=1000.0)
st.sidebar.metric("🏦 Banca Actual", f"${st.session_state.banca_actual:.2f}")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Fuente: FBRef")
raw_data = st.sidebar.text_area("Pegar Tabla de FBRef", height=150, help="Copia las filas de FBRef y pégalas aquí.")

# Procesar pegado para obtener lista de equipos
equipos_lista = ["Selecciona equipo..."]
df_stats = None
if raw_data:
    try:
        # Intentamos detectar si viene con encabezados o solo datos
        df_stats = pd.read_csv(io.StringIO(raw_data), sep='\t')
        if len(df_stats.columns) > 1:
            # La primera columna suele ser el nombre del equipo en FBRef
            equipos_lista = equipos_lista + df_stats.iloc[:, 0].tolist()
            st.sidebar.success(f"✅ {len(df_stats)} equipos listos")
    except:
        st.sidebar.error("Formato no reconocido. Asegúrate de copiar filas completas.")

fractional_kelly = st.sidebar.slider("📉 Agresividad Kelly", 0.05, 1.0, 0.25)

# --- CUERPO PRINCIPAL ---
st.title("🚀 Intelligence Tool: Liga MX & Global")

# 1. ARMADO DEL PARTIDO
st.header("1️⃣ Configuración del Partido")
col_sel1, col_sel2 = st.columns(2)

with col_sel1:
    local_btn = st.selectbox("Equipo Local", equipos_lista)
with col_sel2:
    visita_btn = st.selectbox("Equipo Visita", equipos_lista)

st.markdown("---")

# 2. MODELO POISSON (Goles Esperados)
st.header("2️⃣ Variables de Goles (xG / Gls)")
cp1, cp2 = st.columns(2)
with cp1:
    g_l_f = st.number_input(f"Goles Favor {local_btn}", value=1.5, step=0.1)
    g_l_c = st.number_input(f"Goles Contra {local_btn}", value=1.1, step=0.1)
with cp2:
    g_v_f = st.number_input(f"Goles Favor {visita_btn}", value=1.0, step=0.1)
    g_v_c = st.number_input(f"Goles Contra {visita_btn}", value=1.2, step=0.1)

def calc_poisson(gf_l, gc_l, gf_v, gc_v):
    lam_l, lam_v = (gf_l + gc_v)/2, (gf_v + gc_l)/2
    p_l, p_v, p_e = 0, 0, 0
    for i in range(10):
        for j in range(10):
            prob = ((math.exp(-lam_l)*lam_l**i)/math.factorial(i)) * ((math.exp(-lam_v)*lam_v**j)/math.factorial(j))
            if i > j: p_l += prob
            elif j > i: p_v += prob
            else: p_e += prob
    return p_l, p_v, p_e

p_l_p, p_v_p, p_e_p = calc_poisson(g_l_f, g_l_c, g_v_f, g_v_c)
st.info(f"Probabilidad Calculada: **{local_btn}** {p_l_p*100:.1f}% | **Empate** {p_e_p*100:.1f}% | **{visita_btn}** {p_v_p*100:.1f}%")

# 3. MOMIOS Y VALOR
st.header("3️⃣ Momios de Mercado")
cm1, cm2 = st.columns(2)
m_l = cm1.number_input(f"Mejor Momio {local_btn}", value=2.0)
m_v = cm2.number_input(f"Mejor Momio {visita_btn}", value=3.0)
m_e = st.number_input("Mejor Momio Empate", value=3.2)

def get_k(p, m):
    p_dec = p/100
    b = m - 1
    return max(0, ((b * p_dec - (1 - p_dec)) / b) * fractional_kelly) if b > 0 else 0

# 4. BOTÓN GUARDAR Y CONSULTAR
st.markdown("---")
if st.button("📥 GUARDAR ANÁLISIS DEL PARTIDO"):
    nuevo_partido = {
        "Partido": f"{local_btn} vs {visita_btn}",
        "Prob_L": f"{p_l_p*100:.1f}%",
        "Prob_V": f"{p_v_p*100:.1f}%",
        "Momio_L": m_l,
        "Momio_V": m_v,
        "Stake_L": f"${st.session_state.banca_actual * get_k(p_l_p*100, m_l):.2f}",
        "Stake_V": f"${st.session_state.banca_actual * get_k(p_v_p*100, m_v):.2f}"
    }
    st.session_state.historial_partidos.append(nuevo_partido)
    st.success("Partido guardado en la bitácora de la sesión.")

# MOSTRAR BITÁCORA
if st.session_state.historial_partidos:
    st.header("📋 Bitácora de Análisis (Sesión Actual)")
    df_historial = pd.DataFrame(st.session_state.historial_partidos)
    st.table(df_historial)
