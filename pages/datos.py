"""
Intelligence Pro — pages/datos.py  v4.3
Parser real: process_fbref_paste(text) — una sola función para todas las tablas.
Detección mejorada: revisa las primeras 8 líneas de cada bloque.
Keys de almacenamiento = nombres exactos que usa profile.py.
"""
import re
import streamlit as st
from ui.styles import inject_styles
from ui.components import (
    bankroll_sidebar, pipeline_steps, section_header,
    inline_tip, toast, auto_save_indicator, mark_modified, safe_key,
)
from data.leagues import LEAGUES, LEAGUE_NAMES
from data import parser, fixtures as fixtures_mod

# ── Nombres exactos que usa profile.py en get_team_row(data_master, KEY, squad)
# Columnas distintivas para auto-detección (mínimo 2 deben aparecer)
TABLE_SIGNATURES = {
    "Tabla General":     {"Pts", "GF", "GA", "GD", "Pts/MP"},
    "Standard Squad":    {"xG", "npxG", "xAG"},
    "Standard Opp":      {"xG", "npxG", "GA"},        # Opp tiene GA en lugar de GF
    "Shooting Squad":    {"SoT%", "G/Sh", "Dist", "Sh"},
    "Shooting Opp":      {"SoT%", "G/Sh", "GA"},
    "PlayingTime Squad": {"Mn/MP", "PPM", "onxG"},
    "Misc Squad":        {"CrdY", "CrdR", "Fls", "Fld"},
    "Misc Opp":          {"CrdY", "CrdR", "Fls"},
    "ha":                {"Home", "Away"},
}

TABLA_NOMBRES = {
    "Tabla General":     "Tabla General",
    "Standard Squad":    "Estándar Squad",
    "Standard Opp":      "Estándar Opp",
    "Shooting Squad":    "Disparos Squad",
    "Shooting Opp":      "Disparos Opp",
    "PlayingTime Squad": "Minutos Squad",
    "Misc Squad":        "Misc Squad",
    "Misc Opp":          "Misc Opp",
    "ha":                "Casa/Vis",
}


def _detect(raw: str) -> dict[str, str]:
    """
    Divide el texto en bloques y detecta qué tabla es cada uno.
    Revisa las primeras 8 líneas de cada bloque buscando headers conocidos.
    """
    blocks = re.split(r'\n{2,}', raw.strip())
    if len(blocks) == 1:
        # Sin líneas en blanco: tratar todo como un bloque
        blocks = [raw.strip()]

    detected: dict[str, str] = {}
    scores:   dict[str, int] = {}

    for block in blocks:
        lines = [l for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        # Revisar las primeras 8 líneas buscando headers de columnas
        for header_line in lines[:8]:
            tokens = set(re.split(r'[\s\t]+', header_line.strip()))
            for ttype, sig in TABLE_SIGNATURES.items():
                score = len(sig & tokens)
                if score >= 2 and score > scores.get(ttype, 0):
                    detected[ttype] = block
                    scores[ttype] = score
    return detected


def _parse_all(liga_key: str, raw: str):
    """
    Auto-detecta y parsea todas las tablas del texto pegado.
    Usa parser.process_fbref_paste() para tablas estadísticas.
    Usa parser.parse_home_away_table() para la tabla HA.
    """
    ss = st.session_state
    ss.setdefault("fbref_data", {}).setdefault(liga_key, {})

    detected = _detect(raw)
    cargadas: dict = {}
    errores:  list = []

    for ttype, block in detected.items():
        nombre = TABLA_NOMBRES.get(ttype, ttype)
        try:
            if ttype == "ha":
                result = parser.parse_home_away_table(block)
                if result:
                    ss.setdefault("ha_store", {})[liga_key] = result
                    cargadas[ttype] = result
                else:
                    errores.append(f"{nombre}: no se pudo parsear")
            else:
                result = parser.process_fbref_paste(block)
                if result is not None and len(result) > 0:
                    ss["fbref_data"][liga_key][ttype] = result
                    cargadas[ttype] = result
                else:
                    errores.append(f"{nombre}: resultado vacío")
        except Exception as e:
            errores.append(f"{nombre}: {e}")

    mark_modified()
    return cargadas, errores


def render():
    inject_styles()
    with st.sidebar:
        bankroll_sidebar()
        st.divider()
        auto_save_indicator()

    st.markdown('<h1>📋 Cargar Ligas</h1>', unsafe_allow_html=True)
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
        if tablas is not None and len(tablas) > 0:
            any_loaded = True
            n = len(tablas)
            total = len(TABLA_NOMBRES)
            st.markdown(f"**{liga_key}** — `{n}/{total}` tablas")
            badges = "  ".join(
                f"{'✅' if k in tablas else '⬜'} {v}"
                for k, v in TABLA_NOMBRES.items()
            )
            st.caption(badges)

    if not any_loaded:
        st.info("Ninguna liga cargada todavía")


def _tab(liga_key: str):
    ss = st.session_state
    tablas = ss.get("fbref_data", {}).get(liga_key, {})

    if tablas is not None and len(tablas) > 0:
        n = len(tablas)
        st.success(f"✅ {liga_key}: {n} tablas cargadas — " +
                   ", ".join(TABLA_NOMBRES.get(k, k) for k in tablas if k != "ha"))
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Sección FBRef ────────────────────────────────────────────────────────
    section_header("📈 Tablas estadísticas FBRef")

    st.info(
        f"**Cómo hacerlo:** FBRef → {liga_key} → estadísticas → "
        f"copia todo el bloque de tablas y pégalo aquí. "
        f"El sistema detecta automáticamente las tablas."
    )

    raw = st.text_area(
        f"Pega todas las tablas de {liga_key}",
        height=220,
        key=safe_key("fbref_ta", liga_key),
        placeholder=(
            "Pega el contenido de FBRef aquí...\n\n"
            "Incluye: Tabla General, Squad Standard Stats, Shooting, etc.\n"
            "Puedes pegar cada tabla por separado o todas juntas."
        ),
        label_visibility="collapsed",
    )

    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("🔍 Detectar y cargar", key=safe_key("btn_parse", liga_key),
                     use_container_width=True, disabled=not raw.strip()):
            with st.spinner("Detectando tablas..."):
                cargadas, errores = _parse_all(liga_key, raw)
            if cargadas:
                nombres = [TABLA_NOMBRES.get(t, t) for t in cargadas]
                st.success(f"✅ {len(cargadas)} tablas detectadas: {', '.join(nombres)}")
                faltantes = [TABLA_NOMBRES[t] for t in TABLE_SIGNATURES if t not in ss.get("fbref_data", {}).get(liga_key, {})]
                if faltantes:
                    st.info(f"ℹ️ No detectadas: {', '.join(faltantes)} — puedes pegarlas individualmente abajo")
            else:
                st.error("❌ No se detectó ninguna tabla. Asegúrate de copiar la tabla completa incluyendo el encabezado (Rk, Squad, MP...)")
            if errores:
                with st.expander("⚠️ Detalles de errores"):
                    for e in errores:
                        st.text(e)
            st.rerun()

    with c2:
        if (tablas is not None and len(tablas) > 0) and st.button("🗑 Limpiar", key=safe_key("btn_reset", liga_key),
                                use_container_width=True):
            ss.get("fbref_data", {}).pop(liga_key, None)
            mark_modified()
            st.rerun()

    # ── Cargar tabla individual ───────────────────────────────────────────────
    faltantes_keys = [
        t for t in TABLE_SIGNATURES
        if t not in tablas and t != "ha"
    ]
    if faltantes_keys:
        with st.expander(
            f"📌 Cargar tabla individual ({len(faltantes_keys)} faltantes)",
            expanded=not tablas
        ):
            st.info(
                "Si la detección automática no funcionó para una tabla, "
                "pégala aquí individualmente y selecciona su tipo."
            )
            sel = st.selectbox(
                "¿Qué tabla estás pegando?",
                options=faltantes_keys,
                format_func=lambda t: TABLA_NOMBRES.get(t, t),
                key=safe_key("sel_ind", liga_key)
            )
            raw_ind = st.text_area(
                f"Pegar: {TABLA_NOMBRES.get(sel, sel)}",
                height=160,
                key=safe_key("ta_ind", liga_key, sel),
                placeholder=f"Pega aquí solo la tabla '{TABLA_NOMBRES.get(sel, sel)}' de FBRef..."
            )
            if st.button("Cargar esta tabla", key=safe_key("btn_ind", liga_key, sel),
                         disabled=not raw_ind.strip(), use_container_width=True):
                try:
                    result = parser.process_fbref_paste(raw_ind)
                    if result is not None and len(result) > 0:
                        ss.setdefault("fbref_data", {}).setdefault(liga_key, {})[sel] = result
                        mark_modified()
                        st.success(f"✅ {TABLA_NOMBRES.get(sel, sel)} cargada — {len(result)} equipos")
                        st.rerun()
                    else:
                        st.error("❌ No se pudo parsear. ¿Incluiste el encabezado de columnas?")
                except Exception as e:
                    st.error(f"❌ {e}")

    st.divider()

    # ── Tabla HA ─────────────────────────────────────────────────────────────
    ha_store = ss.get("ha_store", {})
    ha_liga  = ha_store.get(liga_key)

    section_header("🏠 Tabla Casa / Visitante (opcional pero mejora el modelo)")

    if ha_liga is not None and len(ha_liga) > 0:
        st.success(f"✅ Home/Away cargado — {len(ha_liga)} equipos")
    else:
        st.info("Mejora la precisión del modelo con splits reales por condición de juego.")

    raw_ha = st.text_area(
        "Pegar tabla Home/Away",
        height=140,
        key=safe_key("ha_ta", liga_key),
        placeholder="Pega la tabla Home/Away de FBRef (pestaña 'Home/Away' en la liga)...",
        label_visibility="collapsed"
    )
    ch1, ch2 = st.columns([2, 1])
    with ch1:
        if st.button("🏠 Cargar Home/Away", key=safe_key("btn_ha", liga_key),
                     use_container_width=True, disabled=not raw_ha.strip()):
            try:
                result = parser.parse_home_away_table(raw_ha)
                if result:
                    ss.setdefault("ha_store", {})[liga_key] = result
                    mark_modified()
                    st.success(f"✅ {len(result)} equipos cargados")
                    st.rerun()
                else:
                    st.error("❌ No se pudo parsear la tabla H/A.")
            except Exception as e:
                st.error(f"❌ {e}")
    with ch2:
        if (ha_liga is not None and len(ha_liga) > 0) and st.button("🗑 Limpiar", key=safe_key("btn_ha_reset", liga_key),
                                 use_container_width=True):
            ss.get("ha_store", {}).pop(liga_key, None)
            mark_modified()
            st.rerun()

    st.divider()

    # ── Fixtures ─────────────────────────────────────────────────────────────
    section_header("📅 Fixtures de la temporada")
    fixtures_data = ss.get("fixtures_data", {})
    fixtures_liga = fixtures_data.get(liga_key)
    n_fix = len(fixtures_liga) if fixtures_liga is not None and len(fixtures_liga) > 0 else 0

    if n_fix:
        st.success(f"✅ {n_fix} partidos en fixtures")
    else:
        st.info(f"FBRef → {liga_key} → Scores & Fixtures → copia toda la tabla → pega aquí")

    raw_fix = st.text_area(
        "Pegar Scores & Fixtures",
        height=140,
        key=safe_key("fix_ta", liga_key),
        placeholder="Pega la tabla Scores & Fixtures de FBRef...",
        label_visibility="collapsed"
    )
    cf1, cf2 = st.columns([2, 1])
    with cf1:
        if st.button("📅 Cargar fixtures", key=safe_key("btn_fix", liga_key),
                     use_container_width=True, disabled=not raw_fix.strip()):
            try:
                result = fixtures_mod.parse_fixtures(raw_fix)
                ss.setdefault("fixtures_data", {})[liga_key] = result
                mark_modified()
                st.success(f"✅ {len(result)} partidos cargados")
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")
    with cf2:
        if (fixtures_liga is not None and len(fixtures_liga) > 0) and st.button("🗑 Limpiar", key=safe_key("btn_fix_reset", liga_key),
                                       use_container_width=True):
            ss.get("fixtures_data", {}).pop(liga_key, None)
            mark_modified()
            st.rerun()

    if fixtures_liga is not None and len(fixtures_liga) > 0:
        with st.expander("👁 Próximos partidos"):
            import pandas as pd
            # fixtures_liga puede ser DataFrame o lista de dicts
            if isinstance(fixtures_liga, pd.DataFrame):
                df_fix = fixtures_liga.copy()
            else:
                df_fix = pd.DataFrame(fixtures_liga)

            # Filtrar no jugados: si hay col Score, jugados tienen score real
            if "Score" in df_fix.columns:
                proximos_df = df_fix[df_fix["Score"].isna() | (df_fix["Score"] == "")]
            elif "jugado" in df_fix.columns:
                proximos_df = df_fix[~df_fix["jugado"].astype(bool)]
            else:
                proximos_df = df_fix  # mostrar todos si no se puede filtrar

            proximos_df = proximos_df.head(8)
            if len(proximos_df) > 0:
                show_cols = [c for c in ["Date", "fecha", "Home", "home", "Away", "away", "Time", "hora"]
                             if c in proximos_df.columns]
                st.dataframe(proximos_df[show_cols] if show_cols else proximos_df,
                             use_container_width=True, hide_index=True)
            else:
                st.caption("Sin próximos partidos.")


render()
