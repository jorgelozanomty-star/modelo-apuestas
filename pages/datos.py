"""
Intelligence Pro — pages/datos.py  v4.1
Un textarea por liga → auto-detección de 9 tablas FBRef.
"""
import re
import streamlit as st
from ui.styles import inject_styles
from ui.components import (
    bankroll_sidebar, pipeline_steps, section_header,
    liga_status_card, inline_tip, toast,
    auto_save_indicator, mark_modified, safe_key, TABLA_NOMBRES,
)
from data.leagues import LEAGUES, LEAGUE_NAMES
from data import parser, fixtures as fixtures_mod

# Keys = nombres exactos que usa profile.py en get_team_row(data_master, KEY, squad)
TABLE_SIGNATURES = {
    "Tabla General":    {"Pts", "GF", "GA", "GD", "Pts/MP"},
    "Standard Squad":   {"xG", "npxG", "xAG"},
    "Shooting Squad":   {"SoT%", "G/Sh", "Dist"},
    "Passing Squad":    {"TotDist", "PrgDist", "KP"},
    "Pass Types Squad": {"Live", "Dead", "TB", "Sw"},
    "GCA Squad":        {"SCA", "GCA", "SCA90"},
    "Defense Squad":    {"TklW", "Blocks", "Int"},
    "Possession Squad": {"Touches", "Mid 3rd"},
    "PlayingTime Squad":{"Mn/MP", "PPM"},
    "Misc Squad":       {"CrdY", "CrdR", "Fls"},
    "ha":               {"Home", "Away"},
}

# Nombres para mostrar en la UI
TABLA_NOMBRES_LOCAL = {
    "Tabla General":     "Tabla General",
    "Standard Squad":    "Estándar",
    "Shooting Squad":    "Disparos",
    "Passing Squad":     "Pases",
    "Pass Types Squad":  "Tipo Pase",
    "GCA Squad":         "GCA/SCA",
    "Defense Squad":     "Defensa",
    "Possession Squad":  "Posesión",
    "PlayingTime Squad": "Minutos",
    "Misc Squad":        "Misc",
    "ha":                "Casa/Vis",
}


def _detect(raw: str) -> dict:
    blocks = re.split(r'\n{2,}', raw.strip())
    detected, scores = {}, {}
    for block in blocks:
        lines = [l for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 3:
            continue
        for header_line in lines[:2]:
            tokens = set(re.split(r'\s+|\t', header_line.strip()))
            for ttype, sig in TABLE_SIGNATURES.items():
                score = len(sig & tokens)
                if score >= 2 and score > scores.get(ttype, 0):
                    detected[ttype] = block
                    scores[ttype] = score
            break
    return detected


def _parse_all(liga_key: str, raw: str):
    ss = st.session_state
    ss.setdefault("fbref_data", {}).setdefault(liga_key, {})
    detected = _detect(raw)
    cargadas, errores = {}, []
    for ttype, block in detected.items():
        try:
            if ttype == "ha":
                result = parser.parse_home_away_table(block)
                ss.setdefault("ha_store", {})[liga_key] = result
            else:
                result = parser.parse_fbref_table(block, table_type=ttype)
            ss["fbref_data"][liga_key][ttype] = result
            cargadas[ttype] = result
        except Exception as e:
            errores.append(f"{TABLA_NOMBRES.get(ttype, ttype)}: {e}")
    mark_modified()
    return cargadas, errores


def render():
    inject_styles()
    with st.sidebar:
        bankroll_sidebar()
        st.divider()
        auto_save_indicator()

    st.markdown(('<h1>📋 Cargar Ligas</h1>').strip(), unsafe_allow_html=True)
    pipeline_steps()

    ss = st.session_state
    tabs = st.tabs(LEAGUE_NAMES)

    for tab, liga_key in zip(tabs, LEAGUE_NAMES):
        with tab:
            _tab(liga_key)

    st.divider()
    section_header("📊 Estado actual")
    fbref_data = ss.get("fbref_data", {})
    any_loaded = False
    for liga_key in LEAGUE_NAMES:
        tablas = fbref_data.get(liga_key, {})
        if tablas:
            any_loaded = True
            liga_status_card(liga_key, liga_key, tablas)
    if not any_loaded:
        st.markdown(
            '<div style="text-align:center;padding:32px;background:var(--surface);'
            'border:1px dashed var(--border);border-radius:var(--radius);color:var(--text-muted)">'
            'Ninguna liga cargada todavía</div>',
            unsafe_allow_html=True,
        )


def _tab(liga_key: str):
    ss = st.session_state
    tablas = ss.get("fbref_data", {}).get(liga_key, {})

    if tablas:
        liga_status_card(liga_key, liga_key, tablas)
        st.markdown(("<br>").strip(), unsafe_allow_html=True)

    section_header("📈 Tablas estadísticas FBRef")
    inline_tip(
        f"<strong>Cómo hacerlo:</strong> FBRef → <strong>{liga_key}</strong> → estadísticas<br>"
        "Copia todo el bloque de tablas y pégalo aquí. "
        "El sistema detecta automáticamente las 9 tablas."
    )

    raw = st.text_area(
        f"Pega todas las tablas de {liga_key}",
        height=220,
        key=safe_key("fbref_ta", liga_key),
        placeholder="Pega el contenido de FBRef aquí...",
        label_visibility="collapsed",
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("🔍 Detectar y cargar", key=safe_key("btn_parse", liga_key),
                     use_container_width=True, disabled=not raw.strip()):
            with st.spinner("Detectando tablas..."):
                cargadas, errores = _parse_all(liga_key, raw)
            if cargadas:
                nombres = [TABLA_NOMBRES_LOCAL.get(t, t) for t in cargadas]
                toast(f"✅ {len(cargadas)} tablas: {', '.join(nombres)}", "success")
                faltantes = [TABLA_NOMBRES_LOCAL.get(t, t) for t in TABLE_SIGNATURES if t not in cargadas]
                if faltantes:
                    toast(f"ℹ️ No detectadas: {', '.join(faltantes)}", "info")
            else:
                toast("❌ No se detectó ninguna tabla.", "error")
            if errores:
                with st.expander("⚠️ Errores"):
                    for e in errores:
                        st.text(e)
            st.rerun()
    with c2:
        if tablas and st.button("🗑 Limpiar", key=safe_key("btn_reset", liga_key),
                                use_container_width=True):
            ss.get("fbref_data", {}).pop(liga_key, None)
            mark_modified()
            st.rerun()

    # Tablas faltantes individuales
    faltantes = [t for t in TABLE_SIGNATURES if t not in tablas]
    if faltantes and tablas:
        with st.expander(f"📌 Cargar tablas faltantes ({len(faltantes)})"):
            sel = st.selectbox("Tabla", faltantes,
                               format_func=lambda t: TABLA_NOMBRES_LOCAL.get(t, t),
                               key=safe_key("sel_ind", liga_key))
            raw_ind = st.text_area("Pegar tabla", height=140,
                                   key=safe_key("ta_ind", liga_key, sel))
            if st.button("Cargar", key=safe_key("btn_ind", liga_key, sel),
                         disabled=not raw_ind.strip()):
                try:
                    if sel == "ha":
                        result = parser.parse_home_away_table(raw_ind)
                        ss.setdefault("ha_store", {})[liga_key] = result
                    else:
                        result = parser.parse_fbref_table(raw_ind, table_type=sel)
                    ss.setdefault("fbref_data", {}).setdefault(liga_key, {})[sel] = result
                    mark_modified()
                    toast(f"✅ {TABLA_NOMBRES.get(sel, sel)} cargada", "success")
                    st.rerun()
                except Exception as e:
                    toast(f"❌ {e}", "error")

    st.divider()

    # Fixtures
    section_header("📅 Fixtures")
    fixtures_data = ss.get("fixtures_data", {})
    fixtures_liga = fixtures_data.get(liga_key)
    n = len(fixtures_liga) if fixtures_liga else 0

    if n:
        toast(f"✅ {n} partidos cargados", "success")
    else:
        inline_tip(f"FBRef → {liga_key} → <em>Scores &amp; Fixtures</em> → copia toda la tabla → pega aquí")

    raw_fix = st.text_area("Pegar Scores & Fixtures", height=140,
                           key=safe_key("fix_ta", liga_key),
                           placeholder="Pega la tabla Scores & Fixtures de FBRef...",
                           label_visibility="collapsed")

    cf1, cf2 = st.columns([2, 1])
    with cf1:
        if st.button("📅 Cargar fixtures", key=safe_key("btn_fix", liga_key),
                     use_container_width=True, disabled=not raw_fix.strip()):
            try:
                result = fixtures_mod.parse_fixtures(raw_fix)
                ss.setdefault("fixtures_data", {})[liga_key] = result
                mark_modified()
                toast(f"✅ {len(result)} partidos cargados", "success")
                st.rerun()
            except Exception as e:
                toast(f"❌ {e}", "error")
    with cf2:
        if fixtures_liga and st.button("🗑 Limpiar", key=safe_key("btn_fix_reset", liga_key),
                                       use_container_width=True):
            ss.get("fixtures_data", {}).pop(liga_key, None)
            mark_modified()
            st.rerun()

    if fixtures_liga:
        with st.expander(f"👁 Próximos partidos"):
            proximos = [p for p in fixtures_liga if not p.get("jugado", True)][:5]
            if proximos:
                import pandas as pd
                cols = [c for c in ["fecha", "home", "away", "hora"]
                        if c in pd.DataFrame(proximos).columns]
                st.dataframe(pd.DataFrame(proximos)[cols], use_container_width=True, hide_index=True)

render()
