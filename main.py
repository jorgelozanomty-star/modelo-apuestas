import streamlit as st
import pandas as pd
import math
import io

# Configuración para tu monitor de 34"
st.set_page_config(page_title="Jorge - Betting Intelligence", layout="wide")

# Inicializar sesión
if 'banca_actual' not in st.session_state:
    st.session_state.banca_actual = 1000.0

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Gestión de Capital")
banca_base = st.sidebar.number_input("💰 Banca Inicial", min_value=0.0, value=1000.0)
st.sidebar.metric("🏦 Banca Actual", f"${st.session_state.banca_actual:.2f}")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Pegar Datos de FBRef")
st.sidebar.caption("Copia la tabla de FBRef y pégala aquí abajo:")
raw_data = st.sidebar.text_area("Pegar (Ctrl+V)", height=150, help="Copia desde el nombre del equipo hasta el final de la fila.")

# Procesar el pegado manual
df_stats = None
if raw_data:
    try:
        # FBRef al copiar y pegar suele usar tabuladores (\t)
        df_stats = pd.read_csv(io.StringIO(raw_data), sep='\t')
        st.sidebar.success(f"✅ {len(df_stats)} equipos detectados")
    except:
        try:
            # Intento alternativo por espacios si el tabulador falla
            df_stats = pd.read_csv(io.StringIO(raw_data), sep='\s\s+', engine='python')
            st.sidebar.success(f"✅ {len(df_stats)} equipos detectados")
        except:
            st.sidebar.error("Error al procesar el pegado. Intenta copiar de nuevo.")

fractional_kelly = st.sidebar.slider("📉 Agresividad Kelly", 0.05, 1.0, 0.25)

# --- CUERPO PRINCIPAL ---
st.title("🚀 Inteligencia de Apuestas: Poisson + Pegado Directo")

# 1. MODELO POISSON
st.header("1️⃣ Modelo de Probabilidad")
cp1, cp2 = st.columns(2)

# Si hay datos pegados, mostramos los promedios para facilitar
if df_stats is not None:
    st.write("**Datos Pegados (Referencia):**")
    st.dataframe(df_stats.head(5))

with cp1:
    g_l_f = st.number_input("Goles Favor Local (xG o Gls)", value=1.5, step=0.1)
    g_l_c = st.number_input("Goles Contra Local", value=1.1, step=0.1)
with cp2:
    g_v_f = st.number_input("Goles Favor Visita (xG o Gls)", value=1.0, step=0.1)
    g_v_c = st.number_input("Goles Contra Visita", value=1.2, step=0.1)

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
st.success(f"Probabilidad: L {p_l_p*100:.1f}% | V {p_v_p*100:.1f}% | E {p_e_p*100:.1f}%")

st.markdown("---")

# 2. COMPARATIVA DE MOMIOS
st.header("2️⃣ Comparativa de Momios")
col_c1, col_c2 = st.columns(2)
with col_c1:
    m_l1 = st.number_input("L-Casa A", value=2.10)
    m_v1 = st.number_input("V-Casa A", value=3.50)
    m_e1 = st.number_input("E-Casa A", value=3.20)
with col_c2:
    m_l2 = st.number_input("L-Casa B", value=2.15)
    m_v2 = st.number_input("V-Casa B", value=3.40)
    m_e2 = st.number_input("E-Casa B", value=3.25)

best_l, best_v, best_e = max(m_l1, m_l2), max(m_v1, m_v2), max(m_e1, m_e2)

# 3. ANÁLISIS DE VALOR
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
if st.button("💰 Calcular y Actualizar"):
    gan = 0
    if res_real == "Local": gan = (s_l * best_l) - s_l - s_v - s_e
    elif res_real == "Visita": gan = (s_v * best_v) - s_v - s_l - s_e
    else: gan = (s_e * best_e) - s_e - s_l - s_v
    st.session_state.banca_actual += gan
    st.rerun()
