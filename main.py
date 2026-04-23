import streamlit as st
import pandas as pd

# Configuración para monitor Wide
st.set_page_config(page_title="Gestor Pro Apuestas - Jorge", layout="wide")

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
st.title("🎯 Estrategia Maestra: Valor + Arbitraje")

# 1. ANÁLISIS DE LA CASA
st.header("1️⃣ Análisis de la Casa")
c1, c2, c3 = st.columns(3)
with c1:
    local = st.text_input("Local", "Tigres")
    m_l = st.number_input(f"Momio {local}", value=2.10, step=0.01)
with c2:
    visita = st.text_input("Visita", "Atlas")
    m_v = st.number_input(f"Momio {visita}", value=3.50, step=0.01)
with c3:
    m_e = st.number_input("Momio Empate", value=3.20, step=0.01)

p_l, p_v, p_e = 1/m_l, 1/m_v, 1/m_e
payout_total = p_l + p_v + p_e
margen = (payout_total - 1) * 100
st.markdown(f"**Margen de la Casa (Vig):** `{margen:.2f}%` {'🔥 ARBITRAJE' if margen < 0 else ''}")

st.markdown("---")

# 2. TU MODELO
st.header("2️⃣ Tu Modelo vs La Casa")
col_l, col_v, col_e = st.columns(3)
with col_l: prob_l = st.number_input(f"% {local}", value=float(f"{(p_l/payout_total)*100:.1f}"))
with col_v: prob_v = st.number_input(f"% {visita}", value=float(f"{(p_v/payout_total)*100:.1f}"))
with col_e: prob_e = st.number_input("% Empate", value=float(f"{(p_e/payout_total)*100:.1f}"))

def get_kelly(p_mia, momio):
    p = p_mia / 100
    b = momio - 1
    f = (b * p - (1 - p)) / b if b > 0 else 0
    return max(0, f * fractional_kelly)

# Almacenar sugerencias para la simulación
stake_l = banca_total * get_kelly(prob_l, m_l)
stake_v = banca_total * get_kelly(prob_v, m_v)
stake_e = banca_total * get_kelly(prob_e, m_e)

if st.button("📊 GENERAR PLAN DE APUESTA"):
    st.markdown("---")
    res_cols = st.columns(3)
    equipos = [(local, prob_l, m_l, stake_l), (visita, prob_v, m_v, stake_v), ("Empate", prob_e, m_e, stake_e)]
    
    for i, (nom, p, m, s) in enumerate(equipos):
        with res_cols[i]:
            ev = (p/100 * (m-1) * 100) - ((1-p/100) * 100)
            if ev > 0:
                st.success(f"✅ {nom}")
                st.metric("EV", f"+${ev:.2f}")
                st.metric("Stake Sugerido", f"${s:.2f}")
            else:
                st.error(f"❌ {nom}")
                st.caption(f"EV: ${ev:.2f}")

    # --- GRÁFICAS ---
    st.markdown("---")
    st.subheader(f"📈 Curva de Rentabilidad ({local})")
    data_plot = []
    for var in range(-10, 11):
        p_var = prob_l + var
        if 0 <= p_var <= 100:
            s_var = banca_total * get_kelly(p_var, m_l)
            ev_var = (p_var/100 * (m_l-1) * 100) - ((1-p_var/100) * 100)
            data_plot.append({"Prob (%)": p_var, "EV ($)": round(ev_var, 2), "Stake ($)": round(s_var, 2)})
    df_plot = pd.DataFrame(data_plot).set_index("Prob (%)")
    c_chart1, c_chart2 = st.columns(2)
    with c_chart1: st.line_chart(df_plot["EV ($)"])
    with c_chart2: st.line_chart(df_plot["Stake ($)"])

# --- 3. SIMULADOR DE RESULTADO FINAL ---
st.markdown("---")
st.header("3️⃣ Simulador de Resultado (Post-Partido)")
resultado_real = st.radio("¿Quién ganó el partido?", [local, visita, "Empate"], horizontal=True)

if st.button("💰 Calcular Utilidad"):
    ganancia = 0
    # Calcular según lo que el modelo sugirió apostar
    if resultado_real == local:
        ganancia = (stake_l * m_l) - stake_l - stake_v - stake_e
    elif resultado_real == visita:
        ganancia = (stake_v * m_v) - stake_v - stake_l - stake_e
    else:
        ganancia = (stake_e * m_e) - stake_e - stake_l - stake_v
    
    if ganancia >= 0:
        st.balloons()
        st.success(f"🎊 ¡Ganancia Neta: +${ganancia:.2f}!")
    else:
        st.error(f"📉 Pérdida Neta: ${ganancia:.2f}")
    
    st.info(f"ROI de la operación: {(ganancia / (stake_l + stake_v + stake_e + 0.000001)) * 100:.2f}%")
