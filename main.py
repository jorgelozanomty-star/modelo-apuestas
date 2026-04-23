import streamlit as st
import pandas as pd
import math

# Configuración Wide para tu monitor de 34"
st.set_page_config(page_title="Jorge - Betting Intelligence", layout="wide")

# Inicializar sesión
if 'banca_actual' not in st.session_state:
    st.session_state.banca_actual = 1000.0

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Configuración y Datos")
banca_base = st.sidebar.number_input("💰 Banca Inicial", min_value=0.0, value=1000.0)
st.sidebar.metric("🏦 Banca Actual", f"${st.session_state.banca_actual:.2f}")

# NUEVO: Cargador de FBRef
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Importar de FBRef")
uploaded_file = st.sidebar.file_uploader("Sube el CSV de FBRef (Squad Stats)", type=["csv"])

# Procesar datos de FBRef si existen
df_stats = None
if uploaded_file:
    try:
        df_stats = pd.read_csv(uploaded_file)
        st.sidebar.success("✅ Datos cargados")
    except Exception as e:
        st.sidebar.error("Error al leer el archivo")

fractional_kelly = st.sidebar.slider("📉 Agresividad Kelly", 0.05, 1.0, 0.25)

# --- CUERPO PRINCIPAL ---
st.title("🚀 Inteligencia de Apuestas: FBRef + Poisson")

# 1. MODELO POISSON CON AUTO-COMPLETE
st.header("1️⃣ Modelo de Probabilidad (Estadística)")
c_team1, c_team2 = st.columns(2)

# Valores por defecto
l_f, l_c, v_f, v_c = 1.5, 1.1, 1.0, 1.2

if df_stats is not None:
    # Intentar identificar columnas de goles (ajusta según el CSV de FBRef)
    # FBRef suele usar 'Gls' o 'Scored'
    equipos = df_stats.iloc[:, 0].unique() # Primera columna suele ser el nombre del equipo
    
    with c_team1:
        local_sel = st.selectbox("Selecciona Local", equipos)
        row_l = df_stats[df_stats.iloc[:, 0] == local_sel].iloc[0]
        # Asumiendo que buscamos promedios por partido (Gls/90 o similar)
        st.info(f"Datos detectados para {local_sel}")
        
    with c_team2:
        visita_sel = st.selectbox("Selecciona Visita", equipos)
        row_v = df_stats[df_stats.iloc[:, 0] == visita_sel].iloc[0]
        st.info(f"Datos detectados para {visita_sel}")
    
    # Aquí puedes mapear las columnas específicas de tu CSV de FBRef
    # Por ahora dejamos manual pero con la opción de ver los datos cargados
    st.write("**Vista previa de estadísticas cargadas:**")
    st.dataframe(df_stats.head(3))
else:
    st.warning("👈 Sube un CSV de FBRef en la barra lateral para automatizar. Mientras tanto, ingresa datos manuales:")

cp1, cp2 = st.columns(2)
with cp1:
    g_l_f = cp1.number_input("Goles Favor Local", value=1.5)
    g_l_c = cp1.number_input("Goles Contra Local", value=1.1)
with cp2:
    g_v_f = cp2.number_input("Goles Favor Visita", value=1.0)
    g_v_c = cp2.number_input("Goles Contra Visita", value=1.2)

# Cálculo Poisson
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
st.success(f"Probabilidad Sugerida: L {p_l_p*100:.1f}% | V {p_v_p*100:.1f}% | E {p_e_p*100:.1f}%")

st.markdown("---")

# 2. COMPARATIVA DE MOMIOS
st.header("2️⃣ Comparativa de Momios")
col_n, col_c1, col_c2 = st.columns([1, 2, 2])
with col_c1:
    m_l1 = st.number_input("L-Casa A", value=2.10)
    m_v1 = st.number_input("V-Casa A", value=3.50)
    m_e1 = st.number_input("E-Casa A", value=3.20)
with col_c2:
    m_l2 = st.number_input("L-Casa B", value=2.15)
    m_v2 = st.number_input("V-Casa B", value=3.40)
    m_e2 = st.number_input("E-Casa B", value=3.25)

best_l, best_v, best_e = max(m_l1, m_l2), max(m_v1, m_v2), max(m_e1, m_e2)

# 3. MODELO DE VALOR
st.header("3️⃣ Análisis de Valor")
p_l_f = st.number_input("% Local Final", value=float(p_l_p*100))
p_v_f = st.number_input("% Visita Final", value=float(p_v_p*100))
p_e_f = st.number_input("% Empate Final", value=float(p_e_p*100))

def get_k(p, m):
    p_dec = p/100
    b = m - 1
    return max(0, ((b * p_dec - (1 - p_dec)) / b) * fractional_kelly) if b > 0 else 0

s_l, s_v, s_e = st.session_state.banca_actual * get_k(p_l_f, best_l), st.session_state.banca_actual * get_k(p_v_f, best_v), st.session_state.banca_actual * get_k(p_e_f, best_e)

if st.button("📊 ANALIZAR"):
    c_res = st.columns(3)
    for i, (n, p, m, s) in enumerate([("Local", p_l_f, best_l, s_l), ("Visita", p_v_f, best_v, s_v), ("Empate", p_e_f, best_e, s_e)]):
        ev = (p/100 * (m-1) * 100) - ((1-p/100) * 100)
        with c_res[i]:
            if ev > 0: st.success(f"✅ {n}"); st.metric("Stake", f"${s:.2f}")
            else: st.error(f"❌ {n}")

# 4. CIERRE
st.markdown("---")
res_real = st.radio("Resultado Final:", ["Local", "Visita", "Empate"], horizontal=True)
if st.button("💰 Calcular"):
    gan = 0
    if res_real == "Local": gan = (s_l * best_l) - s_l - s_v - s_e
    elif res_real == "Visita": gan = (s_v * best_v) - s_v - s_l - s_e
    else: gan = (s_e * best_e) - s_e - s_l - s_v
    st.session_state.banca_actual += gan
    st.rerun()
