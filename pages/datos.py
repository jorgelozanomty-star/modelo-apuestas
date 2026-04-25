"""
pages/datos.py
Página 1 — Datos
Carga tablas FBRef y fixtures por liga.
Todo se guarda en sesión (y en JSON al exportar).
"""
import streamlit as st
import pandas as pd
from datetime import date

from data.session   import init, get_data_master, set_table, set_fixtures, get_fixtures, export_session, import_session, get_ha_store, set_ha_store
from data.parser    import process_fbref_paste, parse_home_away_table
from data.fixtures  import parse_fixtures
from data.leagues   import LEAGUES, LEAGUE_NAMES
from ui.styles import inject_css

init()
inject_css()

TABLES = [
    ("Tabla General",     "🏆"),
    ("Standard Squad",    "⚽"),
    ("Standard Opp",      "🛡️"),
    ("Shooting Squad",    "🎯"),
    ("Shooting Opp",      "🎯"),
    ("PlayingTime Squad", "⏱️"),
    ("PlayingTime Opp",   "⏱️"),
    ("Misc Squad",        "📋"),
    ("Misc Opp",          "📋"),
]

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <span class="app-title">① Datos</span>
  <span class="app-sub">Carga tablas FBRef y fixtures por liga</span>
</div>
""", unsafe_allow_html=True)

# ── Selector de liga ───────────────────────────────────────────────────────────
league = st.selectbox(
    "Liga activa",
    LEAGUE_NAMES,
    index=LEAGUE_NAMES.index(st.session_state.get("selected_league", "Liga MX")),
    key="datos_league",
)
st.session_state["selected_league"] = league
cfg = LEAGUES[league]

# Info de la liga
st.caption(
    f"{cfg['flag']} Home advantage: +{cfg['home_adv']:.2f} goles  ·  "
    f"Blend dinámico activo desde jornada {cfg['blend_jornada_threshold']}"
)



dm = get_data_master(league)
tables_loaded = len(dm)

# ── Estado de tablas ───────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Tablas FBRef cargadas</div>', unsafe_allow_html=True)

cols = st.columns(3)
for i, (nombre, icon) in enumerate(TABLES):
    with cols[i % 3]:
        has = nombre in dm and len(dm[nombre]) > 0
        color = "#f0fdf4" if has else "#fafaf9"
        border = "#86efac" if has else "#e7e5e0"
        txt    = f"✓ {len(dm[nombre])} equipos" if has else "sin datos"
        tcolor = "#15803d" if has else "#a8a29e"
        st.markdown(
            f'<div style="background:{color};border:1px solid {border};border-radius:8px;'
            f'padding:8px 12px;margin-bottom:8px;">'
            f'<span style="font-size:0.72rem;font-weight:500;color:#1c1917;">{icon} {nombre}</span><br>'
            f'<span style="font-size:0.65rem;font-family:DM Mono,monospace;color:{tcolor};">{txt}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Cargar tablas ──────────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Pegar datos de FBRef</div>', unsafe_allow_html=True)

tab_cols = st.columns(2)
for i, (nombre, icon) in enumerate(TABLES):
    with tab_cols[i % 2]:
        with st.expander(f"{icon} {nombre}"):
            raw = st.text_area(
                "", key=f"data_{league}_{nombre}",
                height=65, label_visibility="collapsed",
                placeholder="Pega aquí los datos de FBRef…",
            )
            if raw and len(raw) > 10:
                df = process_fbref_paste(raw)
                if df is not None and len(df) > 0:
                    set_table(league, nombre, df)
                    st.markdown(
                        f'<div style="background:#f0fdf4;border:1px solid #86efac;color:#15803d;'
                        f'font-size:0.65rem;padding:3px 10px;border-radius:4px;font-family:DM Mono,monospace;text-align:center;">'
                        f'✓ {len(df)} equipos cargados</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.warning("No se pudo parsear. Revisa el formato.")

# ── Tabla Home / Away ─────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Tabla Home / Away (opcional)</div>', unsafe_allow_html=True)

ha_store = get_ha_store(league)
ha_loaded = len(ha_store) > 0

if ha_loaded:
    st.markdown(
        f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;'
        f'padding:10px 16px;margin-bottom:8px;">'
        f'<span style="font-size:0.8rem;font-weight:600;color:#1c1917;">✓ Home/Away splits: {len(ha_store)} equipos</span><br>'
        f'<span style="font-size:0.7rem;font-family:DM Mono,monospace;color:#15803d;">el modelo usa goles reales por condición</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

with st.expander("🏠✈️ Cargar tabla Home / Away"):
    st.caption("Copia la tabla de clasificación por Home/Away de FBRef (misma página que Tabla General, pestaña 'Home and Away').")
    raw_ha = st.text_area(
        "", key=f"ha_{league}", height=120,
        label_visibility="collapsed",
        placeholder="Pega aquí la tabla Home / Away de FBRef…",
    )
    if raw_ha and len(raw_ha) > 20:
        ha_data = parse_home_away_table(raw_ha)
        if ha_data and len(ha_data) > 0:
            set_ha_store(league, ha_data)
            st.success(f"✓ {len(ha_data)} equipos con splits Home/Away")
            # Preview
            import pandas as pd
            rows = [{"Equipo": k,
                     "GF/p Casa": v["gf_home_pg"], "GA/p Casa": v["ga_home_pg"],
                     "GF/p Visita": v["gf_away_pg"], "GA/p Visita": v["ga_away_pg"]}
                    for k, v in ha_data.items()]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        else:
            st.warning("No se pudo parsear. Asegúrate de copiar toda la tabla incluyendo los números.")

# ── Fixtures ───────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Scores & Fixtures</div>', unsafe_allow_html=True)

fix_df = get_fixtures(league)
if fix_df is not None:
    pending = (~fix_df["played"]).sum()
    played  = fix_df["played"].sum()
    st.markdown(
        f'<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;'
        f'padding:10px 16px;margin-bottom:12px;">'
        f'<span style="font-size:0.8rem;font-weight:600;color:#1c1917;">{len(fix_df)} partidos cargados</span><br>'
        f'<span style="font-size:0.7rem;font-family:DM Mono,monospace;color:#15803d;">'
        f'{played} jugados · {pending} pendientes</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

with st.expander("📅 Cargar Scores & Fixtures"):
    raw_fix = st.text_area(
        "", key=f"fix_{league}",
        height=80, label_visibility="collapsed",
        placeholder="Pega la tabla Scores & Fixtures de FBRef…",
    )
    if raw_fix and len(raw_fix) > 20:
        df_fix = parse_fixtures(raw_fix)
        if df_fix is not None and len(df_fix) > 0:
            set_fixtures(league, df_fix)
            st.success(f"✓ {len(df_fix)} partidos · {(~df_fix['played']).sum()} pendientes")
        else:
            st.warning("No se pudo parsear. Revisa el formato.")

# ── Resumen multi-liga ─────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Resumen de ligas cargadas</div>', unsafe_allow_html=True)

fbref_store = st.session_state.get("fbref_store", {})
fixtures_store = st.session_state.get("fixtures_store", {})

summary_rows = []
for lg in LEAGUE_NAMES:
    n_tablas = len(fbref_store.get(lg, {}))
    has_fix  = lg in fixtures_store and len(fixtures_store[lg]) > 0
    if n_tablas > 0 or has_fix:
        summary_rows.append({
            "Liga":     f"{LEAGUES[lg]['flag']} {lg}",
            "Tablas":   f"{n_tablas}/9",
            "Fixtures": "✓" if has_fix else "—",
        })

if summary_rows:
    st.dataframe(pd.DataFrame(summary_rows), hide_index=True, use_container_width=True)
else:
    st.caption("Sin datos cargados todavía.")

# ── Limpiar liga ───────────────────────────────────────────────────────────────
if st.button(f"🗑️ Limpiar datos de {league}", type="secondary"):
    if "fbref_store" in st.session_state:
        st.session_state["fbref_store"].pop(league, None)
    if "fixtures_store" in st.session_state:
        st.session_state["fixtures_store"].pop(league, None)
    st.rerun()

# ── Guardar / Cargar sesión ────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Sesión</div>', unsafe_allow_html=True)

s1, s2 = st.columns(2)
with s1:
    today_str = date.today().isoformat()
    st.download_button(
        label="⬇️ Exportar sesión completa",
        data=export_session(),
        file_name=f"intelligence_pro_{today_str}.json",
        mime="application/json",
        use_container_width=True,
    )
with s2:
    uploaded = st.file_uploader(
        "⬆️ Cargar sesión", type="json",
        label_visibility="collapsed",
        key="session_upload_datos",
    )
    if uploaded:
        file_id = f"{uploaded.name}_{uploaded.size}"
        if st.session_state.get("_last_import_datos") != file_id:
            ok, msg = import_session(uploaded.read())
            st.session_state["_last_import_datos"] = file_id
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)