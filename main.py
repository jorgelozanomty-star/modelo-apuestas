import streamlit as st
import pandas as pd

# Configuración Wide para tu monitor Xiaomi
st.set_page_config(page_title="Jorge - Betting Intelligence", layout="wide")

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Configuración")
banca_total = st.sidebar.number_input("💰 Bankroll Total", min_value=0, value=1000, step=100)
fractional_kelly = st.sidebar.slider("📉 Agresividad Kelly", 0.05, 1.0, 0.25)

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Convertidor de Momios")
m_tipo = st.sidebar.selectbox("Formato", ["Americano", "Decimal"])
m_input = st.sidebar.number_input("Valor", value=-110 if m_tipo == "Americano" else 1.91)

if m_tipo == "Americano":
    res_decimal = (m_input / 100) + 1 if m_input > 0 else (100 / abs(m_input)) + 1
else:
    res_decimal = m_input

st.sidebar.write(f"**Decimal:** `{res_decimal:.3f}` | **Win Rate:** `{(1/res_decimal)*100:.1f}%`")

# --- CUERPO PRINCIPAL ---
st.title("🚀 Inteligencia de Apuestas: Multi-Casa")

# 1. ANÁLISIS MULTI-CASA
st.header("1️⃣ Comparativa de Momios")
col_n, col_c1, col_c2 = st.columns([1, 2, 2])

with col_n:
    st.write("### ") # Espacio
    st.write("**Local**")
    st.write("**Visita**")
    st.write("**Empate**")

with col_c1:
    bookie1 = st.text_input("Casa A (ej. Caliente)", "Caliente")
    m_l1 = st.number_input(f"L - {bookie1}", value=2.10, step=0.01, label_visibility="collapsed")
    m_v1 = st.number_input(f"V - {bookie1}", value=3.50, step=0.01, label_visibility="collapsed")
    m_e1 = st.number_input(f"E - {bookie1}", value=3.20, step=0.01, label_visibility="collapsed")

with col_c2:
    bookie2 = st.text_input("Casa B (ej. Bet365)", "Bet365")
    m_l2 = st.number_input(f"L - {bookie2}", value=2.15, step=0.01, label_visibility="collapsed")
    m_v2 = st.number_input(f"V - {bookie2}", value=3.40, step=0.01, label_visibility="collapsed")
    m_e2 = st.number_input(f"E - {bookie2}", value=3.25, step=0.01, label_visibility="collapsed")

# Escoger el mejor momio disponible
best_l = max(m_l1, m_l2)
best_v = max(m_v1, m_v2)
best_e = max(m_e1, m_e2)

# Cálculo de Margen con los mejores momios
payout_total = (1/best_l) + (1/best_v) + (1/best_e)
margen = (payout_total - 1) * 100

st.info(f"💡 **Mejor Payout Detectado:** Usando lo mejor de ambas casas, el margen es de `{margen:.2f}%`.")

if margen < 0:
    st.balloons()
    st.success(f"🔥 ¡ARBITRAJE DETECTADO! Margen negativo: {margen:.2f}%.")

st.markdown("---")

# 2. TU MODELO
st.header("2️⃣ Tu Modelo vs El Mercado")
col_l, col_v, col_e = st.columns(3)
with col_l: prob_l = st.number_input(f"% Prob Local", value=float(f"{( (1/best_l)/payout_total )*100:.1f}"))
with col_v: prob_v = st.number_input(f"% Prob Visita", value=float(f"{( (1/best_v)/payout_total )*100:.1f}"))
with col_e: prob_e = st.number_input("% Prob Empate", value=float(f"{( (1/best_e)/payout_total )*100:.1f}"))

def get_kelly(p_mia, momio):
    p = p_mia / 100
    b = momio - 1
    f = (b * p - (1 - p)) / b if b > 0 else 0
    return max(0, f * fractional_kelly)

# Stakes calculados sobre los mejores momios
stake_l = banca_total * get_kelly(prob_l, best_l)
stake_v = banca_total * get_kelly(prob_v, best_v)
stake_e = banca_total * get_kelly(prob_e, best_e)

if st.button("📊 ANALIZAR VALOR"):
    st.markdown("---")
    res_cols = st.columns(3)
    datos = [("Local", prob_l, best_l, stake_l), ("Visita", prob_v, best_v, stake_v), ("Empate", prob_e, best_e, stake_e)]
    
    for i, (nom, p, m, s) in enumerate(datos):
        with res_cols[i]:
            ev = (p/100 * (m-1) * 100) - ((1-p/100) * 100)
            if ev > 0:
                st.success(f"✅ {nom} (Momio: {m})")
                st.metric("EV", f"+${ev:.2f}")
                st.metric("Stake Sugerido", f"${s:.2f}")
            else:
                st.error(f"❌ {nom}")
                st.caption(f"Sin valor matemático.")

# 3. SIMULADOR
st.markdown("---")
st.header("3️⃣ Simulador de Cierre")
res_real = st.radio("Resultado Final:", ["Local", "Visita", "Empate"], horizontal=True)

if st.button("💰 Calcular"):
    gan = 0
    if res_real == "Local": gan = (stake_l * best_l) - stake_l - stake_v - stake_e
    elif res_real == "Visita": gan = (stake_v * best_v) - stake_v - stake_l - stake_e
    else: gan = (stake_e * best_e) - stake_e - stake_l - stake_v
    
    if gan >= 0: st.success(f"Utilidad: +${gan:.2f}")
    else: st.error(f"Balance: -${abs(gan):.2f}")
