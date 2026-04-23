import streamlit as st

# ESTO ES PARA FORZAR LA CONEXIÓN EN REPLIT
st.set_page_config(page_title="Modelo de Valor", layout="wide")

# Ocultar el menú de Streamlit para que no use recursos extra
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Modelo de Apuestas - Análisis de Valor")

# --- TODO TU CÓDIGO DE ANTES ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Datos del Partido")
    equipo_local = st.text_input("Equipo Local", value="Tigres")
    equipo_visita = st.text_input("Equipo Visita", value="Atlas")

with col2:
    st.subheader("Momios de la Casa")
    momio_local = st.number_input(f"Momio {equipo_local}", min_value=1.01, value=2.10)
    momio_visita = st.number_input(f"Momio {equipo_visita}", min_value=1.01, value=3.50)
    momio_empate = st.number_input("Momio Empate", min_value=1.01, value=3.20)

# Cálculos automáticos de la casa
prob_local = (1 / momio_local) * 100
prob_visita = (1 / momio_visita) * 100
prob_empate = (1 / momio_empate) * 100

st.markdown("---")
st.subheader("Cálculo de Valor Esperado (EV)")

col3, col4, col5 = st.columns(3)
with col3:
    prob_real_local = st.number_input(f"% Real {equipo_local}", value=float(f"{prob_local:.1f}"))
with col4:
    prob_real_visita = st.number_input(f"% Real {equipo_visita}", value=float(f"{prob_visita:.1f}"))
with col5:
    prob_real_empate = st.number_input("% Real Empate", value=float(f"{prob_empate:.1f}"))

if st.button("Calcular Valor (EV)"):
    # EV Local
    ev_local = ((prob_real_local/100) * (momio_local - 1) * 100) - ((1 - (prob_real_local/100)) * 100)
    # EV Visita
    ev_visita = ((prob_real_visita/100) * (momio_visita - 1) * 100) - ((1 - (prob_real_visita/100)) * 100)
    # EV Empate
    ev_empate = ((prob_real_empate/100) * (momio_empate - 1) * 100) - ((1 - (prob_real_empate/100)) * 100)

    st.write("### Resultados")
    def check_ev(name, val):
        if val > 0: st.success(f"✅ {name}: +${val:.2f} (HAY VALOR)")
        else: st.error(f"❌ {name}: ${val:.2f} (Sin valor)")

    check_ev(equipo_local, ev_local)
    check_ev(equipo_visita, ev_visita)
    check_ev("Empate", ev_empate)