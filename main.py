import streamlit as st
import pandas as pd
import math
import io

st.set_page_config(page_title="Jorge - Intelligence Pro", layout="wide")

# --- PERSISTENCIA ---
if 'banca_actual' not in st.session_state:
    st.session_state.banca_actual = 1000.0
if 'jornada_pendientes' not in st.session_state:
    st.session_state.jornada_pendientes = []

# --- SIDEBAR ---
st.sidebar.header("⚙️ Gestión de Capital")
st.sidebar.metric("🏦 Banca Actual", f"${st.session_state.banca_actual:,.2f}")

# Calcular riesgo total en juego
riesgo_total = sum(item['Stake'] for item in st.session_state.jornada_pendientes)
st.sidebar.warning(f"⚠️ Riesgo en juego: ${riesgo_total:,.2f}")

if st.sidebar.button("🗑️ Limpiar Historial"):
    st.session_state.jornada_pendientes = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Datos FBRef")
raw_data = st.sidebar.text_area("Pega tabla aquí", height=100)

df_stats = None
equipos_lista = ["Selecciona equipo..."]
col_name = None

if raw_data:
    try:
        df_stats = pd.read_csv(io.StringIO(raw_data), sep=None, engine='python')
        df_stats = df_stats.loc[:, ~df_stats.columns.str.contains('^Unnamed')]
        df_stats.columns = [c.strip() for c in df_stats.columns]
        col_name = st.sidebar.selectbox("Columna Nombres", df_stats.columns)
        equipos_lista = ["Selecciona equipo..."] + df_stats[col_name].dropna().unique().tolist()
    except:
        st.sidebar.error("Error al procesar.")

fractional_kelly = st.sidebar.slider("📉 Agresividad Kelly", 0.05, 1.0, 0.25)

# --- CUERPO PRINCIPAL ---
st.title("🚀 Intelligence Betting Tool")

# 1. ANÁLISIS
st.header("1️⃣ Análisis del Encuentro")
c1, c2 = st.columns(2)

l_val_f, l_val_c, v_val_f, v_val_c = 1.5, 1.1, 1.0, 1.2

def extraer_promedio(fila):
    mp = float(fila.get('MP', 1))
    gf = float(fila.get('GF', fila.get('Gls', 1.5)))
    ga = float(fila.get('GA', 1.1))
    return (gf / mp if gf > 5 else gf), (ga / mp if ga > 5 else ga)

with c1:
    local_sel = st.selectbox("Local", equipos_lista)
    if df_stats is not None and local_sel != "Selecciona equipo...":
        l_val_f, l_val_c = extraer_promedio(df_stats[df_stats[col_name] == local_sel].iloc[0])

with c2:
    visita_sel = st.selectbox("Visita", equipos_lista)
    if df_stats is not None and visita_sel != "Selecciona equipo...":
        v_val_f, v_val_c = extraer_promedio(df_stats[df_stats[col_name] == visita_sel].iloc[0])

cp1, cp2 = st.columns(2)
g_l_f = cp1.number_input(f"Promedio Favor {local_sel}", value=float(l_val_f))
g_l_c = cp1.number_input(f"Promedio Contra {local_sel}", value=float(l_val_c))
g_v_f = cp2.number_input(f"Promedio Favor {visita_sel}", value=float(v_val_f))
g_v_c = cp2.number_input(f"Promedio Contra {visita_sel}", value=float(v_val_c))

def calc_poisson(gf_l, gc_l, gf_v, gc_v):
    lam_l, lam_v = (gf_l + gc_v)/2, (gf_v + gc_l)/2
    p_l, p_v, p_e = 0.0, 0.0, 0.0
    for i in range(10):
        for j in range(10):
            prob = ((math.exp(-lam_l)*lam_l**i)/math.factorial(i)) * ((math.exp(-lam_v)*lam_v**j)/math.factorial(j))
            if i > j: p_l += prob
            elif j > i: p_v += prob
            else: p_e += prob
    return p_l, p_v, p_e

p_l, p_v, p_e = calc_poisson(g_l_f, g_l_c, g_v_f, g_v_c)

# 2. MOMIOS
st.header("2️⃣ Mejores Momios")
cm1, cm2, cm3 = st.columns(3)
m_l = cm1.number_input("Momio Local", value=2.0)
m_e = cm2.number_input("Momio Empate", value=3.0)
m_v = cm3.number_input("Momio Visita", value=3.0)

# 3. VALOR
st.header("3️⃣ Picks con Valor")
def get_k(p, m):
    return max(0, (((m-1) * p - (1 - p)) / (m-1)) * fractional_kelly) if m > 1 else 0

picks_eval = [("Local", p_l, m_l), ("Empate", p_e, m_e), ("Visita", p_v, m_v)]
c_res = st.columns(3)

for i, (nombre, prob, momio) in enumerate(picks_eval):
    ev = (prob * momio - 1) * 100
    stake = st.session_state.banca_actual * get_k(prob, momio)
    with c_res[i]:
        if ev > 0:
            st.success(f"✅ {nombre}: EV +{ev:.1f}%")
            st.metric("Stake", f"${stake:.2f}")
        else:
            st.error(f"❌ {nombre}: EV {ev:.1f}%")

if st.button("📥 AGREGAR A LA JORNADA"):
    mejor = max(picks_eval, key=lambda x: (x[1]*x[2]-1))
    st.session_state.jornada_pendientes.append({
        "Partido": f"{local_sel} vs {visita_sel}",
        "Pick": mejor[0],
        "Momio": mejor[2],
        "Stake": st.session_state.banca_actual * get_k(mejor[1], mejor[2]),
        "Estado": "Pendiente"
    })
    st.rerun()

# 4. GESTIÓN (LIMPIA)
st.markdown("---")
st.header("4️⃣ Gestión de la Jornada (Cobro)")
if st.session_state.jornada_pendientes:
    # Formatear la tabla para que se vea pro
    df_j = pd.DataFrame(st.session_state.jornada_pendientes)
    df_j["Stake"] = df_j["Stake"].map("${:,.2f}".format)
    st.table(df_j)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        idx = st.selectbox("Partido a cerrar:", range(len(st.session_state.jornada_pendientes)), 
                           format_func=lambda i: st.session_state.jornada_pendientes[i]["Partido"])
        status = st.radio("Resultado:", ["GANADA", "PERDIDA"])
    with col_c2:
        if st.button("💰 Actualizar Banca"):
            partido = st.session_state.jornada_pendientes[idx]
            # Convertir el string de stake de vuelta a número
            s_num = float(partido["Stake"].replace('$', '').replace(',', ''))
            if status == "GANADA":
                st.session_state.banca_actual += (s_num * partido["Momio"]) - s_num
            else:
                st.session_state.banca_actual -= s_num
            st.session_state.jornada_pendientes.pop(idx)
            st.rerun()
