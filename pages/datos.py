"""
Intelligence Pro — pages/datos.py
Carga de tablas FBRef: UN solo textarea por liga → auto-detección de 9 tablas.
Fixtures: textarea separado (igual que antes, sin cambios en el parser).
"""
import streamlit as st
import re
from ui.styles import inject_styles
from ui.components import (
    bankroll_sidebar, pipeline_steps, section_header,
    liga_status_card, inline_tip, toast, auto_save_indicator,
    mark_modified, safe_key, TABLA_NOMBRES
)
from data.leagues import LEAGUES, LEAGUE_NAMES
from data import parser, fixtures as fixtures_mod, session


# ── Detección automática de tablas FBRef ──────────────────────────────────────

# Columnas distintivas por tipo de tabla (subconjunto robusto)
TABLE_SIGNATURES = {
    "standard":    {"xG", "npxG", "xAG"},
    "shooting":    {"SoT%", "G/Sh", "Dist"},
    "passing":     {"TotDist", "PrgDist", "KP"},
    "passtypes":   {"Live", "Dead", "TB", "Sw"},
    "gca":         {"SCA", "GCA", "SCA90"},
    "defense":     {"TklW", "Blocks", "Int", "Tkl+Int"},
    "possession":  {"Touches", "Att 3rd", "Mid 3rd"},
    "playingtime": {"Mn/MP", "PPM", "onxG"},
    "misc":        {"CrdY", "CrdR", "Fls", "Fld"},
    "ha":          {"Home", "Away"},  # tabla #10 tiene ambas columnas de sección
}


def _score_table_type(header_line: str) -> tuple[str, int]:
    """
    Dado el header de una tabla (tab-separated o space-separated),
    retorna (tipo_mejor, score).
    """
    tokens = set(re.split(r'\s+|\t', header_line.strip()))
    best_type, best_score = "unknown", 0
    for ttype, sig in TABLE_SIGNATURES.items():
        score = len(sig & tokens)
        if score > best_score:
            best_type, best_score = ttype, score
    return best_type, best_score


def auto_detect_tables(raw_text: str) -> dict[str, str]:
    """
    Divide el texto pegado en bloques y detecta qué tabla es cada uno.
    Retorna {tipo: texto_crudo}.
    """
    # Separar bloques por 2+ líneas en blanco
    blocks = re.split(r'\n{2,}', raw_text.strip())
    detected: dict[str, str] = {}
    scores: dict[str, int] = {}

    for block in blocks:
        lines = [l for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 3:  # Muy corto, ignorar
            continue
        # Usar las primeras 2 líneas como posible header
        for header_line in lines[:2]:
            ttype, score = _score_table_type(header_line)
            if score >= 2:  # Umbral mínimo de confianza
                if ttype not in detected or score > scores.get(ttype, 0):
                    detected[ttype] = block
                    scores[ttype] = score
                break

    return detected


def _try_parse_all(liga_key: str, raw_text: str):
    """
    Auto-detecta y parsea todas las tablas de un texto.
    Guarda resultados en session_state.
    Retorna (tablas_detectadas: dict, errores: list)
    """
    ss = st.session_state
    if "fbref_data" not in ss:
        ss["fbref_data"] = {}
    if liga_key not in ss["fbref_data"]:
        ss["fbref_data"][liga_key] = {}

    detected = auto_detect_tables(raw_text)
    errores = []
    cargadas = {}

    for ttype, block in detected.items():
        try:
            if ttype == "ha":
                result = parser.parse_home_away_table(block)
                if "ha_store" not in ss:
                    ss["ha_store"] = {}
                ss["ha_store"][liga_key] = result
            else:
                result = parser.parse_fbref_table(block, table_type=ttype)

            ss["fbref_data"][liga_key][ttype] = result
            cargadas[ttype] = result
        except Exception as e:
            errores.append(f"{TABLA_NOMBRES.get(ttype, ttype)}: {e}")

    mark_modified()
    return cargadas, errores


# ── Render principal ──────────────────────────────────────────────────────────

def render():
    inject_styles()

    with st.sidebar:
        bankroll_sidebar()
        st.divider()
        auto_save_indicator()

    st.markdown('<h1>📋 Cargar Ligas</h1>', unsafe_allow_html=True)

    pipeline_steps()

    ss = st.session_state

    # ── Tabs por liga ─────────────────────────────────────────────────────────
    liga_keys = list(LIGAS.keys())
    liga_displays = [LIGAS[k]["display"] for k in liga_keys]
    tabs = st.tabs(liga_displays)

    for i, (tab, liga_key) in enumerate(zip(tabs, liga_keys)):
        liga_info = LIGAS[liga_key]
        with tab:
            _render_liga_tab(liga_key, liga_info)

    st.divider()

    # ── Sesión multi-liga status ───────────────────────────────────────────────
    section_header("📊 Estado actual de todas las ligas")
    fbref_data = ss.get("fbref_data", {})

    any_loaded = False
    for liga_key in liga_keys:
        tablas = fbref_data.get(liga_key, {})
        if tablas:
            any_loaded = True
            liga_status_card(liga_key, LIGAS[liga_key]["display"], tablas)

    if not any_loaded:
        st.markdown("""
        <div style="text-align:center;padding:32px;background:var(--surface);
             border:1px dashed var(--border);border-radius:var(--radius)">
            <div style="font-size:2rem;margin-bottom:8px">📋</div>
            <div style="font-family:var(--font-display);font-size:1rem;
                 font-weight:600;color:var(--text-muted)">
                Ninguna liga cargada todavía
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_liga_tab(liga_key: str, liga_info: dict):
    ss = st.session_state
    fbref_data = ss.get("fbref_data", {})
    tablas_actuales = fbref_data.get(liga_key, {})

    # Status de esta liga
    if tablas_actuales:
        liga_status_card(liga_key, liga_info["display"], tablas_actuales)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── Sección FBRef ─────────────────────────────────────────────────────────
    section_header("📈 Tablas estadísticas FBRef")

    inline_tip(f"""
        <strong>Cómo hacerlo:</strong><br>
        1. Abre <code>fbref.com/en/comps/{liga_info.get('fbref_id','...')}/stats/</code><br>
        2. Selecciona <strong>todo el contenido estadístico</strong> de la página (Ctrl+A en la sección)<br>
        3. Pega aquí abajo — el sistema detecta automáticamente las 9 tablas
    """)

    key_fbref = safe_key("fbref_paste", liga_key)
    raw_fbref = st.text_area(
        f"Pega aquí TODAS las tablas de {liga_info['display']}",
        height=220,
        key=key_fbref,
        placeholder=(
            "Pega el contenido copiado de FBRef...\n"
            "El sistema reconoce automáticamente: Estándar, Disparos, Pases,\n"
            "Tipo de Pase, GCA/SCA, Defensa, Posesión, Minutos, Misc.\n\n"
            "Si tienes la tabla Casa/Visitante, inclúyela también."
        ),
        label_visibility="collapsed"
    )

    col_parse, col_reset = st.columns([2, 1])

    with col_parse:
        if st.button(
            f"🔍 Detectar y cargar tablas",
            key=safe_key("btn_parse_fbref", liga_key),
            use_container_width=True,
            disabled=not raw_fbref.strip()
        ):
            with st.spinner("Detectando tablas..."):
                cargadas, errores = _try_parse_all(liga_key, raw_fbref)

            if cargadas:
                nombres = [TABLA_NOMBRES.get(t, t) for t in cargadas]
                toast(f"✅ {len(cargadas)} tablas detectadas: {', '.join(nombres)}", "success")
                # Mostrar tablas no encontradas
                faltantes = [
                    TABLA_NOMBRES[t] for t in TABLE_SIGNATURES
                    if t not in cargadas
                ]
                if faltantes:
                    toast(
                        f"ℹ️ No detectadas: {', '.join(faltantes)} — "
                        f"puedes pegarlas por separado abajo",
                        "info"
                    )
            else:
                toast("❌ No se detectó ninguna tabla. ¿Pegaste el contenido correcto?", "error")

            if errores:
                with st.expander("⚠️ Errores de parseo"):
                    for e in errores:
                        st.text(e)

            st.rerun()

    with col_reset:
        if tablas_actuales:
            if st.button(
                "🗑 Limpiar",
                key=safe_key("btn_reset_fbref", liga_key),
                use_container_width=True
            ):
                if "fbref_data" in ss:
                    ss["fbref_data"][liga_key] = {}
                mark_modified()
                st.rerun()

    # ── Tablas individuales (fallback) ────────────────────────────────────────
    tablas_faltantes = [t for t in TABLE_SIGNATURES if t not in tablas_actuales]
    if tablas_faltantes and tablas_actuales:
        with st.expander(f"📌 Cargar tablas faltantes individualmente ({len(tablas_faltantes)})"):
            inline_tip("Si una tabla no se detectó automáticamente, pégala aquí de forma individual.")

            sel_tabla = st.selectbox(
                "Tabla a cargar",
                options=tablas_faltantes,
                format_func=lambda t: TABLA_NOMBRES.get(t, t),
                key=safe_key("sel_tabla_individual", liga_key)
            )

            raw_individual = st.text_area(
                f"Pegar tabla: {TABLA_NOMBRES.get(sel_tabla, sel_tabla)}",
                height=150,
                key=safe_key("ta_individual", liga_key, sel_tabla),
                label_visibility="visible"
            )

            if st.button(
                "Cargar esta tabla",
                key=safe_key("btn_individual", liga_key, sel_tabla),
                disabled=not raw_individual.strip()
            ):
                try:
                    if sel_tabla == "ha":
                        result = parser.parse_home_away_table(raw_individual)
                        if "ha_store" not in ss:
                            ss["ha_store"] = {}
                        ss["ha_store"][liga_key] = result
                    else:
                        result = parser.parse_fbref_table(raw_individual, table_type=sel_tabla)

                    if "fbref_data" not in ss:
                        ss["fbref_data"] = {}
                    if liga_key not in ss["fbref_data"]:
                        ss["fbref_data"][liga_key] = {}
                    ss["fbref_data"][liga_key][sel_tabla] = result
                    mark_modified()
                    toast(f"✅ {TABLA_NOMBRES.get(sel_tabla, sel_tabla)} cargada", "success")
                    st.rerun()
                except Exception as e:
                    toast(f"❌ Error: {e}", "error")

    st.divider()

    # ── Sección Fixtures ──────────────────────────────────────────────────────
    section_header("📅 Fixtures de la temporada")

    fixtures_data = ss.get("fixtures_data", {})
    fixtures_liga = fixtures_data.get(liga_key)
    n_fixtures = len(fixtures_liga) if fixtures_liga else 0

    if n_fixtures > 0:
        toast(f"✅ {n_fixtures} partidos cargados en fixtures", "success")
    else:
        inline_tip(
            f"<strong>Cómo hacerlo:</strong> FBRef → {liga_info['display']} → "
            f"<em>Scores & Fixtures</em> → selecciona toda la tabla → pega aquí"
        )

    key_fix = safe_key("fixtures_paste", liga_key)
    raw_fix = st.text_area(
        "Pegar Scores & Fixtures",
        height=150,
        key=key_fix,
        placeholder=(
            "Pega aquí la tabla Scores & Fixtures completa de FBRef...\n"
            "Incluye partidos pasados y futuros de toda la temporada."
        ),
        label_visibility="collapsed"
    )

    col_fix, col_fix_reset = st.columns([2, 1])

    with col_fix:
        if st.button(
            "📅 Cargar fixtures",
            key=safe_key("btn_parse_fix", liga_key),
            use_container_width=True,
            disabled=not raw_fix.strip()
        ):
            with st.spinner("Parseando fixtures..."):
                try:
                    result = fixtures_mod.parse_fixtures(raw_fix)
                    if "fixtures_data" not in ss:
                        ss["fixtures_data"] = {}
                    ss["fixtures_data"][liga_key] = result
                    mark_modified()
                    n = len(result) if result else 0
                    toast(f"✅ {n} partidos cargados", "success")
                    st.rerun()
                except Exception as e:
                    toast(f"❌ Error en fixtures: {e}", "error")

    with col_fix_reset:
        if fixtures_liga:
            if st.button(
                "🗑 Limpiar",
                key=safe_key("btn_reset_fix", liga_key),
                use_container_width=True
            ):
                ss.get("fixtures_data", {}).pop(liga_key, None)
                mark_modified()
                st.rerun()

    # ── Preview de fixtures ───────────────────────────────────────────────────
    if fixtures_liga and n_fixtures > 0:
        with st.expander(f"👁 Ver próximos partidos ({min(5, n_fixtures)} de {n_fixtures})"):
            proximos = [p for p in fixtures_liga if not p.get("jugado", True)][:5]
            if proximos:
                import pandas as pd
                df = pd.DataFrame(proximos)[
                    [c for c in ["fecha", "home", "away", "hora"] if c in pd.DataFrame(proximos).columns]
                ]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.caption("Sin partidos futuros en los fixtures.")
