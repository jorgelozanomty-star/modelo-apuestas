import streamlit as st

# Configuración de la página para que se vea de lujo en tu monitor de 34"
st.set_page_config(page_title="Modelo de Valor - Kelly Criterion", layout="wide")

st.title("📊 Análisis de Valor y Gestión de Banca")
st.markdown("---")

# --- SECCIÓN 1: DATOS DE ENTRADA ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Datos del Partido")
    equipo_local = st.text_input("Equipo Local", value="Tigres")
    equipo_visita = st.text_input("Equipo Visita", value="Atlas")
    banca_total = st.number_input("💰 Tu Banca Total (Bankroll)", min_value=0, value=1000, step=100)

with col2:
    st.subheader("⚖️ Momios de la Casa")
    momio_local = st.number_input(f"Momio {equipo_local}", min_value=1.01, value=2.10, step=0.01)
    momio_visita = st.number_input(f"Momio {equipo_visita}", min_value=1.01, value=3.50, step=0.01)
    momio_empate = st.number_input("Momio Empate", min_value=1.01, value=3.20, step=0.01)

# Cálculo de probabilidades implícitas de la casa
prob_casa_l = (1 / momio_local) * 100
prob_casa_v = (1 / momio_visita) * 100
prob_casa_e = (1 / momio_empate) * 100

st.markdown("---")

# --- SECCIÓN 2: TUS PROBABILIDADES ---
st.subheader("🧠 Tus Probabilidades Reales (Tu Modelo)")
col3, col4, col5 = st.columns(3)

with col3:
    prob_real_l = st.number_input(f"% Real {equipo_local}", min_value=0.0, max_value=100.0, value=float(f"{prob_casa_l:.1f}"))
with col4:
    prob_real_v = st.number_input(f"% Real {equipo_visita}", min_value=0.0, max_value=100.0, value=float(f"{prob_casa_v:.1f}"))
with col5:
    prob_real_e = st.number_input("% Real Empate", min_value=0.0, max_value=100.0, value=float(f"{prob_casa_e:.1f}"))

# --- SECCIÓN 3: LÓGICA DE CÁLCULO (EV Y KELLY) ---
def analizar_resultado(nombre, p_mia, momio, banca):
    p = p_mia / 100
    q = 1 - p
    b = momio - 1 # Ganancia neta por cada peso apostado
    
    # Cálculo de EV (Expected Value)
    ev = (p * b * 100) - (q * 100)
    
    # Criterio de Kelly: f* = (bp - q) / b
    if b > 0:
        f_kelly = (b * p - q) / b
    else:
        f_kelly = 0
        
    if ev > 0:
        st.success(f"✅ **HAY VALOR EN: {nombre}**")
        c1, c2 = st.columns(2)
        c1.metric("EV Esperado", f"${ev:.2f}", delta=f"{ev:.1f}%")
        
        # Usamos Fractional Kelly (0.25) para reducir varianza, como en el Poker
        stake_recomendado = banca * f_kelly * 0.25
        c2.metric("Stake Sugerido (1/4 Kelly)", f"${max(0, stake_recomendado):.2f}", f"{max(0, f_kelly*25):.2f}%")
    else:
        st.error(f"❌ **SIN VALOR EN: {nombre}** (EV: ${ev:.2f})")

st.markdown("---")
if st.button("🚀 EJECUTAR ANÁLISIS MAESTRO"):
    st.header("🎯 Resultados del Análisis")
    analizar_resultado(equipo_local, prob_real_l, momio_local, banca_total)
    analizar_resultado(equipo_visita, prob_real_v, momio_visita, banca_total)
    analizar_resultado("Empate", prob_real_e, momio_empate, banca_total)

st.sidebar.info("Tip: El Criterio de Kelly te ayuda a maximizar el crecimiento de tu banca a largo plazo, controlando el riesgo de quiebra.")
