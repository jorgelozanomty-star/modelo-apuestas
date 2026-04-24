"""
pages/momios.py
Página 2 — Momios
Tabla editable con todos los partidos de todas las ligas.
Incluye lector de momios con Claude Vision.
"""
import streamlit as st
import json
from datetime import date, timedelta

from data.session   import init, get_all_pending_matches, set_momios, get_momios, export_session
from data.leagues   import LEAGUE_NAMES, LEAGUES
from ui.styles      import inject_css

init()
inject_css()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <span class="app-title">② Momios</span>
  <span class="app-sub">Ingresa o escanea los momios de la jornada</span>
</div>
""", unsafe_allow_html=True)

# ── Lector Claude Vision ───────────────────────────────────────────────────────
with st.expander("📋 Cargar momios desde JSON (generado por Claude en el chat)"):
    st.caption(
        "Manda los screenshots de Team Mexico a Claude en el chat → "
        "Claude te entrega el JSON → pégalo aquí."
    )
    st.markdown(
        '<div style="background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;'
        'padding:10px 14px;font-size:0.78rem;color:#92400e;margin-bottom:8px;">'
        '💡 <b>¿Cómo?</b> Pega tus screenshots en esta misma conversación de Claude → '
        'te devuelve el JSON listo → cópialo y pégalo aquí abajo.'
        '</div>',
        unsafe_allow_html=True,
    )
    raw_json = st.text_area(
        "", key="momios_json_paste", height=120,
        label_visibility="collapsed",
        placeholder='{ "partidos": [ { "local": "Sunderland", "visita": "Nottingham Forest", "m_l": 2.75, ... } ] }',
    )
    if raw_json and st.button("📥 Cargar momios", type="primary", key="load_json_btn"):
        try:
            clean = raw_json.replace("```json","").replace("```","").strip()
            parsed = json.loads(clean)
            imported = 0
            skipped  = []
            # Obtener todas las claves de fixtures para fuzzy matching
            all_fixture_keys = list(st.session_state.get("momios_store", {}).keys())
            # También obtener claves de todos los partidos pendientes
            from data.session import get_all_pending_matches
            pending = get_all_pending_matches()
            fixture_keys_map = {m["key"].lower(): m["key"] for m in pending}

            for p in parsed.get("partidos", []):
                local_  = str(p.get("local",  "")).strip()
                visita_ = str(p.get("visita", "")).strip()
                if not local_ or not visita_:
                    continue

                # Intentar coincidencia exacta primero
                key_ = f"{local_} vs {visita_}"
                # Luego fuzzy: buscar fixture que contenga ambos nombres
                best_key = key_
                if key_.lower() not in fixture_keys_map:
                    for fk_lower, fk_real in fixture_keys_map.items():
                        home_fk = fk_lower.split(" vs ")[0] if " vs " in fk_lower else ""
                        away_fk = fk_lower.split(" vs ")[1] if " vs " in fk_lower else ""
                        if (local_.lower() in home_fk or home_fk in local_.lower()) and                            (visita_.lower() in away_fk or away_fk in visita_.lower()):
                            best_key = fk_real
                            break

                existing = get_momios(best_key)
                new_vals = {k: v for k, v in {
                    "m_l":       p.get("m_l",       0),
                    "m_e":       p.get("m_e",       0),
                    "m_v":       p.get("m_v",       0),
                    "linea_ou":  p.get("linea_ou",  2.5),
                    "m_over":    p.get("m_over",    0),
                    "m_under":   p.get("m_under",   0),
                    "m_btts_si": p.get("m_btts_si", 0),
                    "m_btts_no": p.get("m_btts_no", 0),
                }.items() if v and v > 0}
                set_momios(best_key, {**existing, **new_vals})
                imported += 1
            if imported:
                st.success(f"✓ {imported} partido(s) cargados. Revisa y ajusta abajo.")
                st.rerun()
            else:
                st.warning("No se encontraron partidos válidos en el JSON.")
        except json.JSONDecodeError as e:
            st.error(f"JSON inválido: {e}")
        except Exception as e:
            st.error(f"Error: {e}")

# ── Filtros ────────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Filtrar partidos</div>', unsafe_allow_html=True)

f1, f2 = st.columns(2)
with f1:
    ligas_disp = ["Todas las ligas"] + [
        lg for lg in LEAGUE_NAMES
        if st.session_state.get("fixtures_store", {}).get(lg)
    ]
    filtro_liga = st.selectbox("Liga", ligas_disp, key="momios_liga_filter")
with f2:
    filtro_fecha = st.selectbox(
        "Período",
        ["Jornada actual", "Próximos 3 días", "Próximos 7 días", "Todos"],
        key="momios_fecha_filter",
    )

# ── Obtener partidos ───────────────────────────────────────────────────────────
today = date.today()
all_matches = get_all_pending_matches()

# Aplicar filtros
if filtro_liga != "Todas las ligas":
    all_matches = [m for m in all_matches if m["league"] == filtro_liga]

if filtro_fecha == "Jornada actual":
    # Partidos de la jornada con fixtures cargados
    from data.fixtures import get_current_gameweek, get_gameweek_matches
    wk_matches_keys = set()
    for lg in LEAGUE_NAMES:
        from data.session import get_fixtures
        df_fix = get_fixtures(lg)
        if df_fix is None: continue
        wk = get_current_gameweek(df_fix, today)
        if wk is None: continue
        gw = get_gameweek_matches(df_fix, wk, today)
        for _, r in gw.iterrows():
            wk_matches_keys.add(f"{r['home']} vs {r['away']}")
    if wk_matches_keys:
        all_matches = [m for m in all_matches if m["key"] in wk_matches_keys]
elif filtro_fecha == "Próximos 3 días":
    all_matches = [m for m in all_matches if m["date"] <= today + timedelta(days=3)]
elif filtro_fecha == "Próximos 7 días":
    all_matches = [m for m in all_matches if m["date"] <= today + timedelta(days=7)]

if not all_matches:
    st.info("Sin partidos con los filtros actuales. Carga fixtures en la página Datos primero.")
    st.stop()

st.caption(f"{len(all_matches)} partido(s)")

# ── Tabla de momios ────────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Momios por partido</div>', unsafe_allow_html=True)

# Agrupar por liga
from itertools import groupby
all_matches.sort(key=lambda x: (LEAGUE_NAMES.index(x["league"]) if x["league"] in LEAGUE_NAMES else 99, x["date"], x["time"]))

for league_name, group in groupby(all_matches, key=lambda x: x["league"]):
    group_list = list(group)
    cfg = LEAGUES.get(league_name, {})
    flag = cfg.get("flag", "")

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:8px;margin:16px 0 8px 0;'
        f'padding-bottom:8px;border-bottom:1px solid #e7e5e0;">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#1c1917;">{flag} {league_name}</span>'
        f'<span style="font-size:0.65rem;font-family:DM Mono,monospace;color:#a8a29e;">'
        f'{len(group_list)} partidos</span></div>',
        unsafe_allow_html=True,
    )

    for m in group_list:
        key    = m["key"]
        home   = m["home"]
        away   = m["away"]
        saved  = get_momios(key)
        d_str  = f"{m['date'].strftime('%d/%m')} {m['time']}"

        with st.expander(
            f"{'🟢' if saved.get('m_l') else '⚪'} {d_str} · **{home}** vs {away}",
            expanded=not bool(saved.get("m_l"))
        ):
            # 1X2
            c1, c2, c3 = st.columns(3)
            m_l = c1.number_input("Local",  value=float(saved.get("m_l", 0) or 0),
                                  format="%.2f", min_value=0.0, key=f"ml_{key}")
            m_e = c2.number_input("Empate", value=float(saved.get("m_e", 0) or 0),
                                  format="%.2f", min_value=0.0, key=f"me_{key}")
            m_v = c3.number_input("Visita", value=float(saved.get("m_v", 0) or 0),
                                  format="%.2f", min_value=0.0, key=f"mv_{key}")

            # Over/Under + BTTS
            c4, c5, c6, c7, c8 = st.columns(5)
            linea    = c4.selectbox("Línea", [1.5, 2.5, 3.5],
                                    index=[1.5,2.5,3.5].index(saved.get("linea_ou", 2.5))
                                    if saved.get("linea_ou") in [1.5,2.5,3.5] else 1,
                                    key=f"ln_{key}")
            m_over   = c5.number_input("Over",   value=float(saved.get("m_over",   0) or 0),
                                        format="%.2f", min_value=0.0, key=f"mov_{key}")
            m_under  = c6.number_input("Under",  value=float(saved.get("m_under",  0) or 0),
                                        format="%.2f", min_value=0.0, key=f"mun_{key}")
            m_bts    = c7.number_input("BTTS Sí",value=float(saved.get("m_btts_si",0) or 0),
                                        format="%.2f", min_value=0.0, key=f"bts_{key}")
            m_btn    = c8.number_input("BTTS No",value=float(saved.get("m_btts_no",0) or 0),
                                        format="%.2f", min_value=0.0, key=f"btn_{key}")

            if st.button("💾 Guardar", key=f"save_{key}", use_container_width=False):
                set_momios(key, {
                    "m_l": m_l, "m_e": m_e, "m_v": m_v,
                    "linea_ou": linea, "m_over": m_over, "m_under": m_under,
                    "m_btts_si": m_bts, "m_btts_no": m_btn,
                })
                st.rerun()

# ── Guardar sesión ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">Guardar</div>', unsafe_allow_html=True)
st.download_button(
    "⬇️ Exportar sesión con momios",
    data=export_session(),
    file_name=f"intelligence_pro_{date.today()}.json",
    mime="application/json",
    use_container_width=False,
)
