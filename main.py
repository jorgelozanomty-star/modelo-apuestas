import streamlit as st

st.set_page_config(page_title="Gestor Pro Apuestas", layout="wide")

st.title("🎯 Estrategia Maestra: Valor + Arbitraje")
st.sidebar.header("⚙️ Configuración")
banca_total = st.sidebar.number_input("💰 Bankroll Total", min_value=0, value=1000, step=100)
fractional_kelly = st.sidebar.slider("📉 Agresividad Kelly (Fractional)", 0.05, 1.0, 0.25, help="0.25 es lo recomendado para proteger la banca.")

# --- SECCIÓN 1: ENTRADA DE DATOS ---
st.header("1️⃣ Análisis de la Casa de Apuestas")
c1, c2, c3, c4 = st.columns(4)

with c1:
    local = st.text_input("Local", "Tigres")
    m_l = st.number_input(f"Momio {local}", value=2.10)
with c2:
    visita = st.text_input("Visita", "Atlas")
    m_v = st.number_input(f"Momio {visita}", value=3.50)
with c3:
    st.text("") # Espacio
    st.text("")
    m_e = st.number_input("Momio Empate", value=3.20)
with c4:
    st.info("💡 Tip: Ingresa los momios decimales de tu app de apuestas.")

# Lógica de Margen (Overround)
p_l, p_v, p_e = 1/m_l, 1/m_v, 1/m_e
payout_total = p_l + p_v + p_e
margen = (payout_total - 1) * 100

st.markdown(f"**Margen de la Casa (Overround):** `{margen:.2f}%`")

if margen < 0:
    st.balloons()
    st.success(f"🔥 ¡ALERTA DE ARBITRAJE! El margen es negativo ({margen:.2f}%). Puedes ganar dinero seguro apostando a los tres.")
elif margen > 10:
    st.warning("⚠️ Margen muy alto. La casa está cobrando mucha comisión en este mercado.")

st.markdown("---")

# --- SECCIÓN 2: TU MODELO VS LA CASA ---
st.header("2️⃣ Tu Modelo vs La Casa")
col_l, col_v, col_e = st.columns(3)

with col_l:
    st.subheader(local)
    prob_l = st.number_input(f"% Prob {local}", value=float(f"{(p_l/payout_total)*100:.1f}"))
with col_v:
    st.subheader(visita)
    prob_v = st.number_input(f"% Prob {visita}", value=float(f"{(p_v/payout_total)*100:.1f}"))
with col_e:
    st.subheader("Empate")
    prob_e = st.number_input("% Prob Empate", value=float(f"{(p_e/payout_total)*100:.1f}"))

def calcular_gestion(nombre, prob_mia, momio):
    p = prob_mia / 100
    q = 1 - p
    b = momio - 1
    ev = (p * b * 100) - (q * 100)
    f_k = (b * p - q) / b if b > 0 else 0
    
    if ev > 0:
        st.success(f"✅ VALOR: {nombre}")
        st.metric("EV", f"+${ev:.2f}")
        stake = banca_total * f_k * fractional_kelly
        st.metric("Sugerencia Stake", f"${max(0, stake):.2f}", f"{max(0, f_k*fractional_kelly*100):.1f}% de banca")
    else:
        st.error(f"❌ NO VALUE: {nombre}")
        st.caption(f"EV: ${ev:.2f}")

if st.button("📊 GENERAR PLAN DE APUESTA"):
    st.markdown("---")
    res1, res2, res3 = st.columns(3)
    with res1: calcular_gestion(local, prob_l, m_l)
    with res2: calcular_gestion(visita, prob_v, m_v)
    with res3: calcular_gestion("Empate", prob_e, m_e)
