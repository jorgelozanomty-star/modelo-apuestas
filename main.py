import streamlit as st

# Configuración para que aproveches tu monitor de 34"
st.set_page_config(page_title="Gestor Pro Apuestas - Jorge", layout="wide")

# --- BARRA LATERAL (Sidebar) ---
st.sidebar.header("⚙️ Configuración y Herramientas")

# 1. Gestión de Banca
banca_total = st.sidebar.number_input("💰 Bankroll Total", min_value=0, value=1000, step=100)
fractional_kelly = st.sidebar.slider("📉 Agresividad Kelly (Fractional)", 0.05, 1.0, 0.25, help="0.25 es lo recomendado para proteger la banca.")

st.sidebar.markdown("---")

# 2. Convertidor de Momios (Útil para NFL/NBA/MLB)
st.sidebar.subheader("🔄 Convertidor de Momios")
m_tipo = st.sidebar.selectbox("Formato de entrada", ["Americano", "Decimal"])
m_input = st.sidebar.number_input("Valor a convertir", value=-110 if m_tipo == "Americano" else 1.91)

# Lógica de conversión instantánea
if m_tipo == "Americano":
    if m_input > 0:
        res_decimal = (m_input / 100) + 1
    else:
        res_decimal = (100 / abs(m_input)) + 1
else:
    res_decimal = m_input

st.sidebar.write(f"**Resultado en Decimal:** `{res_decimal:.3f}`")
st.sidebar.info(f"Necesitas ganar el **{(1/res_decimal)*100:.1f}%** de las veces para no perder dinero con este momio.")

# --- CUERPO PRINCIPAL ---
st.title("🎯 Estrategia Maestra: Valor + Arbitraje")

# --- SECCIÓN 1: ENTRADA DE DATOS DE LA CASA ---
st.header("1️⃣ Análisis de la Casa de Apuestas")
c1, c2, c3 = st.columns(3)

with c1:
    local = st.text_input("Local", "Tigres")
    m_l = st.number_input(f"Momio {local}", value=2.10, step=0.01)
with c2:
    visita = st.text_input("Visita", "Atlas")
    m_v = st.number_input(f"Momio {visita}", value=3.50, step=0.01)
with c3:
    m_e = st.number_input("Momio Empate", value=3.20, step=0.01)

# Lógica de Margen (Overround)
p_l, p_v, p_e = 1/m_l, 1/m_v, 1/m_e
payout_total = p_l + p_v + p_e
margen = (payout_total - 1) * 100

st.markdown(f"**Margen de la Casa (Overround):** `{margen:.2f}%`")

if margen < 0:
    st.balloons()
    st.success(f"🔥 ¡ALERTA DE ARBITRAJE! El margen es negativo ({margen:.2f}%). ¡Dinero seguro!")
elif margen > 10:
    st.warning("⚠️ Margen muy alto. La comisión de la casa es excesiva en este mercado.")

st.markdown("---")

# --- SECCIÓN 2: TU MODELO (PROBABILIDADES REALES) ---
st.header("2️⃣ Tu Modelo vs La Casa")
st.caption("Ajusta las probabilidades según tu análisis. Por defecto, se muestran las de la casa sin su comisión.")

col_l, col_v, col_e = st.columns(3)

with col_l:
    st.subheader(local)
    prob_l = st.number_input(f"% Prob {local}", value=float(f"{(p_l/payout_total)*100:.1f}"), key="p_l")
with col_v:
    st.subheader(visita)
    prob_v = st.number_input(f"% Prob {visita}", value=float(f"{(p_v/payout_total)*100:.1f}"), key="p_v")
with col_e:
    st.subheader("Empate")
    prob_e = st.number_input("% Prob Empate", value=float(f"{(p_e/payout_total)*100:.1f}"), key="p_e")

# Función de cálculo para los resultados
def calcular_gestion(nombre, prob_mia, momio):
    p = prob_mia / 100
    q = 1 - p
    b = momio - 1
    ev = (p * b * 100) - (q * 100)
    # Kelly puro
    f_k = (b * p - q) / b if b > 0 else 0
    
    if ev > 0:
        st.success(f"✅ VALOR EN: {nombre}")
        st.metric("Valor Esperado (EV)", f"+${ev:.2f}")
        stake = banca_total * f_k * fractional_kelly
        st.metric("Stake Recomendado", f"${max(0, stake):.2f}", f"{max(0, f_k*fractional_kelly*100):.1f}% de tu banca")
    else:
        st.error(f"❌ SIN VALOR: {nombre}")
        st.caption(f"EV estimado: ${ev:.2f}")

# Botón de ejecución
if st.button("📊 GENERAR PLAN DE APUESTA"):
    st.markdown("---")
    st.header("🎯 Resultados del Análisis Maestro")
    res1, res2, res3 = st.columns(3)
    with res1: calcular_gestion(local, prob_l, m_l)
    with res2: calcular_gestion(visita, prob_v, m_v)
    with res3: calcular_gestion("Empate", prob_e, m_e)
