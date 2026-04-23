import streamlit as st
import pandas as pd

# Configuración Wide para tu monitor Xiaomi de 34"
st.set_page_config(page_title="Jorge - Betting Intelligence", layout="wide")

# Inicializar banca en la sesión si no existe
if 'banca_actual' not in st.session_state:
    st.session_state.banca_actual = 1000.0
if 'historial_ganancias' not in st.session_state:
    st.session_state.historial_ganancias = []

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Gestión de Capital")
# Permitir resetear o ajustar la banca base
banca_base = st.sidebar.number_input("💰 Banca Inicial", min_value=0.0, value=1000.0, step=100.0)
if st.sidebar.button("🔄 Resetear Sesión"):
    st.session_state.banca_actual = banca_base
    st.session_state.historial_ganancias = []

st.sidebar.metric("🏦 Banca Actual", f"${st.session_state.banca_actual:.2f}", 
                  f"{st.session_state.banca_actual - banca_base:.2f}")

fractional_kelly = st.sidebar.slider("📉 Agresividad Kelly", 0.05, 1.0, 0.25)

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Convertidor de Momios")
m_tipo = st.sidebar.selectbox("Formato", ["Americano", "Decimal"])
m_input = st.sidebar.number_input("Valor", value=-110 if m_tipo == "Americano" else 1.91)
res_decimal = (m_input / 100) + 1 if m_tipo == "Americano" and m_input > 0 else (100 / abs(m_input)) + 1 if m_tipo == "Americano" else m_input
st.sidebar.write(f"**Decimal:** `{res_decimal:.3f}` | **Win Rate:** `{(1/res_decimal)*100:.1f}%`")

# --- CUERPO PRINCIPAL ---
st.title("🚀 Inteligencia de Apuestas: Multi-Casa")

# 1. COMPARATIVA
st.header("1️⃣ Comparativa de Momios")
col_n, col_c1, col_c2 = st.columns([1, 2, 2])
with col_n:
    st.write("### "); st.write("**Local**"); st.write("**Visita**"); st.write("**Empate**")
with col_c1:
    bookie1 = st.text_input("Casa A", "Caliente")
    m_l1 = st.number_input(f"L-{bookie1}", value=2.10, step=0.01, label_visibility="collapsed")
    m_v1 = st.number_input(f"V-{bookie1}", value=3.50, step=0.01, label_visibility="collapsed")
    m_e1 = st.number_input(f"E-{bookie1}", value=3.20, step=0.01, label_visibility="collapsed")
with col_c2:
    bookie2 = st.text_input("Casa B", "Bet365")
    m_l2 = st.number_input(f"L-{bookie2}", value=2.15, step=0.01, label_visibility="collapsed")
    m_v2 = st.number_input(f"V-{bookie2}", value=3.40, step=0.01, label_visibility="collapsed")
    m_e2 = st.number_input(f"E-{bookie2}", value=3.25, step=0.01, label_visibility="collapsed")

best_l, best_v, best_e = max(m_l1, m_l2), max(m_v1, m_v2), max(m_e1, m_e2)
payout = (1/best_l) + (1/best_v) + (1/best_e)
st.info(f"💡 **Mejor Payout:** Margen de `{ (payout - 1) * 100:.2f}%` usando lo mejor del mercado.")

st.markdown("---")

# 2. MODELO
st.header("2️⃣ Tu Modelo vs El Mercado")
c_l, c_v, c_e = st.columns(3)
p_l = c_l.number_input("% Local", value=float(f"{( (1/best_l)/payout )*100:.1f}"))
p_v = c_v.number_input("% Visita", value=float(f"{( (1/best_v)/payout )*100:.1f}"))
p_e = c_e.number_input("% Empate", value=float(f"{( (1/best_e)/payout )*100:.1f}"))

def get_k(p_m, m):
    p = p_m / 100
    b = m - 1
    return max(0, ((b * p - (1 - p)) / b) * fractional_kelly) if b > 0 else 0

s_l, s_v, s_e = st.session_state.banca_actual * get_k(p_l, best_l), st.session_state.banca_actual * get_k(p_v, best_v), st.session_state.banca_actual * get_k(p_e, best_e)

if st.button("📊 ANALIZAR VALOR"):
    st.markdown("---")
    r_cols = st.columns(3)
    datos = [("Local", p_l, best_l, s_l), ("Visita", p_v, best_v, s_v), ("Empate", p_e, best_e, s_e)]
    for i, (n, p, m, s) in enumerate(datos):
        with r_cols[i]:
            ev = (p/100 * (m-1) * 100) - ((1-p/100) * 100)
            if ev > 0:
                st.success(f"✅ {n} ({m})"); st.metric("EV", f"+${ev:.2f}"); st.metric("Stake", f"${s:.2f}")
            else:
                st.error(f"❌ {n}"); st.caption("Sin valor.")

# 3. CIERRE
st.markdown("---")
st.header("3️⃣ Simulador de Cierre")
res_real = st.radio("Resultado Final:", ["Local", "Visita", "Empate"], horizontal=True)

if st.button("💰 Calcular y Actualizar Banca"):
    gan = 0
    if res_real == "Local": gan = (s_l * best_l) - s_l - s_v - s_e
    elif res_real == "Visita": gan = (s_v * best_v) - s_v - s_l - s_e
    else: gan = (s_e * best_e) - s_e - s_l - s_v
    
    st.session_state.banca_actual += gan
    st.session_state.historial_ganancias.append(gan)
    
    if gan >= 0: st.success(f"¡Ganaste ${gan:.2f}!"); st.balloons()
    else: st.error(f"Perdiste ${abs(gan):.2f}")
    st.rerun()
