import streamlit as st
import pandas as pd
import math
import io

# Optimización para monitor de 34"
st.set_page_config(page_title="Jorge - Betting Intelligence", layout="wide")

# --- PERSISTENCIA ---
if 'banca_actual' not in st.session_state:
    st.session_state.banca_actual = 1000.0
if 'historial_partidos' not in st.session_state:
    st.session_state.historial_partidos = []

# --- BARRA LATERAL: ENTRADA DE DATOS ---
st.sidebar.header("⚙️ Configuración")
banca_base = st.sidebar.number_input("💰 Banca Inicial", value=1000.0)
st.sidebar.metric("🏦 Banca Actual", f"${st.session_state.banca_actual:.2f}")

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Fuente: FBRef")
raw_data = st.sidebar.text_area("Pegar Tabla de FBRef", height=200, help="Copia las filas de FBRef y pégalas aquí.")

df_stats = None
equipos_lista = ["Selecciona equipo..."]

if raw_data:
    try:
        # FBRef suele usar tabuladores al copiar/pegar
        df_stats = pd.read_csv(io.StringIO(raw_data), sep='\t')
        # Limpieza básica de nombres de columnas
        df_stats.columns = [c.strip() for c in df_stats.columns]
        equipos_lista = equipos_lista + df_stats.iloc[:, 0].dropna().tolist()
        st.sidebar.success(f"✅ {len(df_stats)} equipos cargados")
    except:
        st.sidebar.error("Error al procesar datos. Revisa el formato de pegado.")

fractional_kelly = st.sidebar.slider("📉 Agresividad Kelly", 0.05, 1.0, 0.25)

# --- CUERPO PRINCIPAL ---
st.title("🚀 Betting Intelligence Tool")

# 1. SELECCIÓN DE EQUIPOS Y AUTO-LLENADO
st.header("1️⃣ Selección de Partido")
c1, c2 = st.columns(2)

stats_l = {"gf": 1.5, "gc": 1.1}
stats_v = {"gf": 1.0, "gc": 1.2}

with c1:
    local_sel = st.selectbox("Equipo Local", equipos_lista)
    if df_stats is not None and local_sel != "Selecciona equipo...":
        row = df_stats[df_stats.iloc[:, 0] == local_sel].iloc[0]
        # Intentamos detectar columnas comunes de FBRef: 'Gls' o 'xG'
        stats_l["gf"] = float(row.get('xG', row.get('Gls', 1.5)))
        stats_l["gc"] = float(row.get('GA', 1.1)) # GA suele ser Goles en Contra

with c2:
    visita_sel = st.selectbox("Equipo Visita", equipos_lista)
    if df_stats is not None and visita_sel != "Selecciona equipo...":
        row = df_stats[df_stats.iloc[:, 0] == visita_sel].iloc[0]
        stats_v["gf"] = float(row.get('xG', row.get('Gls', 1.0)))
        stats_v["gc"] = float(row.get('GA', 1.2))

st.markdown("---")

# 2. MODELO POISSON (Ajuste Manual si es necesario)
st.header("2️⃣ Variables de Goles (Poisson)")
cp1, cp2 = st.columns(2)
with cp1:
    g_l_f = cp1.number_input(f"Goles Favor {local_sel}", value=stats_l["gf"])
    g_l_c = cp1.number_input(f"Goles Contra {local_sel}", value=stats_l["gc"])
with cp2:
    g_v_f = cp2.number_input(f"Goles Favor {visita_sel}", value=stats_v["gf"])
    g_v_c = cp2.number_input(f"Goles Contra {visita_sel}", value=stats_v["gc"])

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
st.success(f"Probabilidad: L {p_l_p*100:.1f}% | E {p_e_p*100:.1f}% | V {p_v_p*100:.1f}%")

# 3. MOMIOS Y CÁLCULO DE STAKE
st.header("3️⃣ Momios de Mercado")
cm1, cm2, cm3 = st.columns(3)
m_l = cm1.number_input(f"Momio {local_sel}", value=2.0)
m_e = cm2.number_input("Momio Empate", value=3.2)
m_v = cm3.number_input(f"Momio {visita_sel}", value=3.0)

def get_k(p_pct, m):
    p = p_pct / 100
    b = m - 1
    return max(0, ((b * p - (1 - p)) / b) * fractional_kelly) if b > 0 else 0

stake_l = st.session_state.banca_actual * get_k(p_l_p*100, m_l)
stake_v = st.session_state.banca_actual * get_k(p_v_p*100, m_v)

# 4. BOTÓN GUARDAR
if st.button("📥 GUARDAR PARTIDO EN BITÁCORA"):
    if local_sel != "Selecciona equipo..." and visita_sel != "Selecciona equipo...":
        partido = {
            "Encuentro": f"{local_sel} vs {visita_sel}",
            "Prob L": f"{p_l_p*100:.1f}%",
            "Momio L": m_l,
            "Stake Sugerido": f"${max(stake_l, stake_v):.2f}",
            "Pick Sugerido": local_sel if stake_l > stake_v else visita_sel
        }
        st.session_state.historial_partidos.append(partido)
        st.toast("¡Partido guardado con éxito!")
    else:
        st.warning("Selecciona ambos equipos antes de guardar.")

# 5. CONSULTA DE LA JORNADA
if st.session_state.historial_partidos:
    st.markdown("---")
    st.header("📋 Jornada Analizada")
    st.table(pd.DataFrame(st.session_state.historial_partidos))
