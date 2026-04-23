import streamlit as st
import pandas as pd
import math
import io

st.set_page_config(page_title="Jorge - Betting Intelligence", layout="wide")

if 'banca_actual' not in st.session_state:
    st.session_state.banca_actual = 1000.0
if 'historial_partidos' not in st.session_state:
    st.session_state.historial_partidos = []

# --- SIDEBAR ---
st.sidebar.header("⚙️ Configuración")
banca_base = st.sidebar.number_input("💰 Banca Inicial", value=1000.0)
st.sidebar.metric("🏦 Banca Actual", f"${st.session_state.banca_actual:.2f}")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Pegado de FBRef")
raw_data = st.sidebar.text_area("Pega la tabla aquí (Ctrl+V)", height=150)

df_stats = None
equipos_lista = ["Selecciona equipo..."]

if raw_data:
    try:
        # FBRef usa tabuladores (\t). Usamos 'sep=None' para que detecte automáticamente
        df_stats = pd.read_csv(io.StringIO(raw_data), sep=None, engine='python')
        
        # LIMPIEZA: Eliminar columnas completamente vacías o con nombres 'Unnamed'
        df_stats = df_stats.loc[:, ~df_stats.columns.str.contains('^Unnamed')]
        
        # Identificar qué columna tiene los nombres (buscamos la primera que sea texto)
        columna_nombres = st.sidebar.selectbox("Columna de Equipos", df_stats.columns)
        
        equipos_lista = ["Selecciona equipo..."] + df_stats[columna_nombres].dropna().unique().tolist()
        st.sidebar.success(f"✅ {len(equipos_lista)-1} equipos detectados")
    except Exception as e:
        st.sidebar.error(f"Error: Intenta copiar solo desde los nombres de los equipos.")

fractional_kelly = st.sidebar.slider("📉 Agresividad Kelly", 0.05, 1.0, 0.25)

# --- CUERPO PRINCIPAL ---
st.title("🚀 Betting Intelligence Tool")

st.header("1️⃣ Selección de Partido")
c1, c2 = st.columns(2)

# Valores temporales para el auto-llenado
l_gf, l_gc = 1.5, 1.1
v_gf, v_gc = 1.0, 1.2

with c1:
    local_sel = st.selectbox("Local", equipos_lista)
    if df_stats is not None and local_sel != "Selecciona equipo...":
        # Buscamos la fila del equipo
        row = df_stats[df_stats[columna_nombres] == local_sel].iloc[0]
        # Intentamos buscar xG, Gls, etc. Si no, dejamos manual.
        l_gf = float(row.get('xG', row.get('Gls', 1.5)))
        l_gc = float(row.get('GA', 1.1))

with c2:
    visita_sel = st.selectbox("Visita", equipos_lista)
    if df_stats is not None and visita_sel != "Selecciona equipo...":
        row = df_stats[df_stats[columna_nombres] == visita_sel].iloc[0]
        v_gf = float(row.get('xG', row.get('Gls', 1.0)))
        v_gc = float(row.get('GA', 1.2))

st.markdown("---")

# 2. POISSON
st.header("2️⃣ Poisson")
cp1, cp2 = st.columns(2)
g_l_f = cp1.number_input(f"Goles Favor {local_sel}", value=float(l_gf))
g_l_c = cp1.number_input(f"Goles Contra {local_sel}", value=float(l_gc))
g_v_f = cp2.number_input(f"Goles Favor {visita_sel}", value=float(v_gf))
g_v_c = cp2.number_input(f"Goles Contra {visita_sel}", value=float(v_gc))

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
st.success(f"Prob: L {p_l_p*100:.1f}% | E {p_e_p*100:.1f}% | V {p_v_p*100:.1f}%")

# 3. MOMIOS Y GUARDADO
st.header("3️⃣ Mercado")
cm1, cm2, cm3 = st.columns(3)
m_l = cm1.number_input("Momio L", value=2.0)
m_e = cm2.number_input("Momio E", value=3.0)
m_v = cm3.number_input("Momio V", value=3.0)

if st.button("📥 GUARDAR EN BITÁCORA"):
    # Cálculo de Kelly para el guardado
    def get_k(p, m):
        b = m - 1
        return max(0, ((b * p - (1 - p)) / b) * fractional_kelly) if b > 0 else 0
    
    st.session_state.historial_partidos.append({
        "Partido": f"{local_sel} vs {visita_sel}",
        "EV L": f"{(p_l_p * m_l - 1)*100:.1f}%",
        "Stake": f"${st.session_state.banca_actual * get_k(p_l_p, m_l):.2f}"
    })
    st.rerun()

if st.session_state.historial_partidos:
    st.table(pd.DataFrame(st.session_state.historial_partidos))
