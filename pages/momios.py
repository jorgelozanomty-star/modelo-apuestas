"""
Intelligence Pro — pages/momios.py
Carga de momios: editor inline como camino principal, JSON como opción secundaria.
Fuzzy matching con confirmación EXPLÍCITA antes de cargar.
"""
import streamlit as st
import json
import re
from typing import Optional
from ui.styles import inject_styles
from ui.components import (
    bankroll_sidebar, pipeline_steps, section_header,
    fuzzy_confirm_block, momios_inline_editor, inline_tip,
    toast, auto_save_indicator, mark_modified, safe_key
)
from data.leagues import LIGAS


# ── Conversión de momios ───────────────────────────────────────────────────────

def americano_a_decimal(valor: str) -> Optional[float]:
    """Convierte momio americano (+150, -110) o decimal (2.5) a float decimal."""
    try:
        s = str(valor).strip().replace(",", ".")
        if not s or s == "0":
            return None
        f = float(s)
        if abs(f) >= 100:  # Es americano
            if f > 0:
                return round(f / 100 + 1, 4)
            else:
                return round(100 / abs(f) + 1, 4)
        elif f > 1.0:  # Ya es decimal
            return round(f, 4)
        return None
    except (ValueError, TypeError):
        return None


def _parse_momios_dict(raw: dict) -> dict:
    """
    Convierte un dict de momios (puede ser americanos) a decimales.
    Acepta: {"home": "-110", "draw": "+280", "away": "+200"}
    """
    result = {}
    for k, v in raw.items():
        if isinstance(v, (int, float, str)):
            d = americano_a_decimal(v)
            if d:
                result[k] = d
        elif isinstance(v, dict):
            result[k] = _parse_momios_dict(v)
    return result


# ── Fuzzy matching ────────────────────────────────────────────────────────────

def _fuzzy_score(a: str, b: str) -> float:
    """Score de similitud simple (0-1) entre dos strings."""
    a, b = a.lower().strip(), b.lower().strip()
    if a == b:
        return 1.0
    # Token overlap
    ta = set(a.split())
    tb = set(b.split())
    if not ta or not tb:
        return 0.0
    overlap = len(ta & tb)
    return overlap / max(len(ta), len(tb))


def _find_best_match(nombre: str, candidatos: list[str], threshold: float = 0.5):
    """Encuentra el mejor match con score >= threshold."""
    scores = [(c, _fuzzy_score(nombre, c)) for c in candidatos]
    scores.sort(key=lambda x: x[1], reverse=True)
    best_name, best_score = scores[0] if scores else (None, 0)
    alternativas = [n for n, s in scores[1:4] if s > 0.2]
    return best_name, best_score, alternativas


# ── Persistencia de momios en session_state ───────────────────────────────────

def _get_momios_data():
    if "momios_data" not in st.session_state:
        st.session_state["momios_data"] = {}
    return st.session_state["momios_data"]


def _get_all_equipo_names() -> list[str]:
    """Obtiene todos los equipos de los fixtures cargados."""
    ss = st.session_state
    fixtures = ss.get("fixtures_data", {})
    nombres = set()
    for liga_partidos in fixtures.values():
        if liga_partidos:
            for p in liga_partidos:
                nombres.add(p.get("home", ""))
                nombres.add(p.get("away", ""))
    return [n for n in nombres if n]


def _get_all_partidos() -> list[dict]:
    """Lista todos los partidos de fixtures de todas las ligas."""
    ss = st.session_state
    fixtures = ss.get("fixtures_data", {})
    partidos = []
    for liga_key, liga_partidos in fixtures.items():
        if liga_partidos:
            for p in liga_partidos:
                if not p.get("jugado", False):  # Solo no jugados
                    partidos.append({
                        **p,
                        "liga": LIGAS.get(liga_key, {}).get("display", liga_key),
                        "liga_key": liga_key
                    })
    return partidos


# ── Render principal ──────────────────────────────────────────────────────────

def render():
    inject_styles()

    with st.sidebar:
        bankroll_sidebar()
        st.divider()
        auto_save_indicator()

    st.markdown('<h1>💰 Momios</h1>', unsafe_allow_html=True)
    pipeline_steps()

    ss = st.session_state
    momios_data = _get_momios_data()

    # Verificar que haya fixtures
    todos_partidos = _get_all_partidos()
    if not todos_partidos:
        st.markdown("""
        <div style="text-align:center;padding:40px;background:var(--surface);
             border:1px dashed var(--border);border-radius:var(--radius)">
            <div style="font-size:2rem;margin-bottom:8px">📋</div>
            <div style="font-family:var(--font-display);font-size:1.1rem;
                 font-weight:600;color:var(--text);margin-bottom:6px">
                Primero carga los fixtures
            </div>
            <div style="font-family:var(--font-ui);font-size:0.82rem;color:var(--text-muted)">
                Ve a <strong>Datos</strong> y carga la tabla Scores &amp; Fixtures de tus ligas.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Modo de carga: tabs ────────────────────────────────────────────────────
    tab_inline, tab_json = st.tabs(["✏️ Editor directo", "📋 Cargar JSON (Team Mexico)"])

    # ────────────────────────────────────────────────────────
    with tab_inline:
        _render_inline_editor(todos_partidos, momios_data)

    # ────────────────────────────────────────────────────────
    with tab_json:
        _render_json_loader(todos_partidos, momios_data)

    # ── Vista de momios guardados ──────────────────────────────────────────────
    st.divider()
    _render_momios_guardados(momios_data)


# ── Tab: Editor inline ────────────────────────────────────────────────────────

def _render_inline_editor(todos_partidos: list, momios_data: dict):
    """Editor tipo tabla para captura directa de momios."""
    ss = st.session_state

    # Filtros
    col_f1, col_f2 = st.columns([2, 2])
    ligas_disponibles = list({p["liga"] for p in todos_partidos})

    with col_f1:
        liga_filtro = st.selectbox(
            "Liga", ["Todas"] + sorted(ligas_disponibles),
            key="inline_filtro_liga"
        )
    with col_f2:
        periodo_dias = st.selectbox(
            "Jornada", ["Próximos 3 días", "Esta semana", "Próximas 2 semanas", "Todo"],
            key="inline_filtro_periodo"
        )

    # Filtrar partidos
    partidos_filtrados = todos_partidos
    if liga_filtro != "Todas":
        partidos_filtrados = [p for p in partidos_filtrados if p["liga"] == liga_filtro]

    # Filtro por fecha
    import datetime
    hoy = datetime.date.today()
    dias_map = {"Próximos 3 días": 3, "Esta semana": 7, "Próximas 2 semanas": 14, "Todo": 9999}
    dias = dias_map.get(periodo_dias, 7)
    limite = hoy + datetime.timedelta(days=dias)

    def parse_fecha(f):
        try:
            return datetime.datetime.strptime(str(f), "%Y-%m-%d").date()
        except Exception:
            return hoy + datetime.timedelta(days=1)

    partidos_filtrados = [
        p for p in partidos_filtrados
        if parse_fecha(p.get("fecha", "")) <= limite
    ][:30]  # máximo 30 para no saturar

    if not partidos_filtrados:
        inline_tip("No hay partidos en el período seleccionado.")
        return

    section_header(
        f"Partidos a cargar",
        len(partidos_filtrados)
    )

    inline_tip(
        "<strong>Formato aceptado:</strong> Americano <code>-110</code> / <code>+200</code> "
        "o Decimal <code>1.90</code>. Deja en blanco lo que no quieras."
    )

    # Agregar momios existentes a cada partido
    for p in partidos_filtrados:
        pk = f"{p.get('home','')}_{p.get('away','')}_{p.get('fecha','')}"
        existing = momios_data.get(pk, {})
        p["momios"] = existing

    # Renderizar editor
    momios_editados = momios_inline_editor(partidos_filtrados)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("💾 Guardar momios editados", use_container_width=True, key="btn_save_inline"):
        guardados = 0
        for pk, vals in momios_editados.items():
            home_v = americano_a_decimal(vals.get("home", ""))
            draw_v = americano_a_decimal(vals.get("draw", ""))
            away_v = americano_a_decimal(vals.get("away", ""))

            if any([home_v, draw_v, away_v]):
                momios_data[pk] = {
                    "home": home_v,
                    "draw": draw_v,
                    "away": away_v,
                    "meta": vals.get("meta", {})
                }
                guardados += 1

        ss["momios_data"] = momios_data
        mark_modified()
        toast(f"✅ {guardados} partidos con momios guardados", "success")
        st.rerun()


# ── Tab: JSON loader ──────────────────────────────────────────────────────────

def _render_json_loader(todos_partidos: list, momios_data: dict):
    """Carga desde JSON generado por Claude leyendo screenshots de Team Mexico."""
    ss = st.session_state

    inline_tip(
        "<strong>Flujo Team Mexico:</strong><br>"
        "1. Screenshots de la app → 2. Pegar a Claude → 3. Claude retorna JSON → 4. Pegar aquí"
    )

    raw_json = st.text_area(
        "JSON de momios",
        height=200,
        key="momios_json_input",
        placeholder='''{
  "partidos": [
    {
      "home": "América",
      "away": "Chivas",
      "fecha": "2026-04-27",
      "liga": "Liga MX",
      "momios": {
        "home": "-130",
        "draw": "+240",
        "away": "+380",
        "over25": "-115",
        "under25": "-105"
      }
    }
  ]
}''',
        label_visibility="collapsed"
    )

    if not raw_json.strip():
        return

    # Parsear JSON
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        toast(f"❌ JSON inválido: {e}", "error")
        return

    partidos_json = data.get("partidos", data if isinstance(data, list) else [])
    if not partidos_json:
        toast("⚠️ El JSON no contiene partidos.", "info")
        return

    # Obtener todos los nombres de equipos para fuzzy match
    nombres_fbref = _get_all_equipo_names()

    # Detectar fuzzy matches ambiguos
    pending_fuzzy = []
    exact_matches = []

    for p in partidos_json:
        home_json = p.get("home", "")
        away_json = p.get("away", "")

        home_match, home_score, home_alts = _find_best_match(home_json, nombres_fbref)
        away_match, away_score, away_alts = _find_best_match(away_json, nombres_fbref)

        if home_score < 1.0 and home_score >= 0.4 and nombres_fbref:
            pending_fuzzy.append({
                "json_name": home_json,
                "fbref_name": home_match,
                "score": home_score,
                "alternativas": home_alts
            })
        if away_score < 1.0 and away_score >= 0.4 and nombres_fbref:
            pending_fuzzy.append({
                "json_name": away_json,
                "fbref_name": away_match,
                "score": away_score,
                "alternativas": away_alts
            })

        # Eliminar duplicados en pending_fuzzy
        seen = set()
        pending_fuzzy_unique = []
        for f in pending_fuzzy:
            if f["json_name"] not in seen:
                seen.add(f["json_name"])
                pending_fuzzy_unique.append(f)
        pending_fuzzy = pending_fuzzy_unique

    # Si hay fuzzy matches → mostrar confirmación
    confirmaciones = {}
    if pending_fuzzy:
        st.markdown("<br>", unsafe_allow_html=True)
        confirmaciones = fuzzy_confirm_block(pending_fuzzy)

        # No avanzar hasta que todos los fuzzy estén confirmados
        n_pendientes = len([f for f in pending_fuzzy if f["json_name"] not in confirmaciones])
        if n_pendientes > 0:
            st.warning(f"⚠️ Confirma los {n_pendientes} nombres pendientes para cargar los momios.")
            return

    # Preview de lo que se va a cargar
    section_header("Vista previa", len(partidos_json))

    preview_rows = []
    for p in partidos_json[:10]:
        home = confirmaciones.get(p.get("home", ""), p.get("home", ""))
        away = confirmaciones.get(p.get("away", ""), p.get("away", ""))
        m = p.get("momios", {})
        preview_rows.append({
            "Partido": f"{home} vs {away}",
            "Fecha": p.get("fecha", "—"),
            "Liga": p.get("liga", "—"),
            "1 (Local)": m.get("home", "—"),
            "X (Empate)": m.get("draw", "—"),
            "2 (Visit.)": m.get("away", "—"),
        })

    import pandas as pd
    st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("✅ Confirmar y cargar momios", use_container_width=True, key="btn_load_json"):
        cargados = 0
        errores_carga = []

        for p in partidos_json:
            home = confirmaciones.get(p.get("home", ""), p.get("home", ""))
            away = confirmaciones.get(p.get("away", ""), p.get("away", ""))
            fecha = p.get("fecha", "")
            pk = f"{home}_{away}_{fecha}"

            momios_raw = p.get("momios", {})
            try:
                momios_dec = _parse_momios_dict(momios_raw)
                if momios_dec:
                    momios_data[pk] = {
                        **momios_dec,
                        "meta": {
                            "home": home,
                            "away": away,
                            "fecha": fecha,
                            "liga": p.get("liga", ""),
                        }
                    }
                    cargados += 1
            except Exception as e:
                errores_carga.append(f"{home} vs {away}: {e}")

        ss["momios_data"] = momios_data
        mark_modified()
        toast(f"✅ {cargados} partidos cargados con momios", "success")
        if errores_carga:
            with st.expander("⚠️ Errores"):
                for e in errores_carga:
                    st.text(e)
        st.rerun()


# ── Vista de momios guardados ─────────────────────────────────────────────────

def _render_momios_guardados(momios_data: dict):
    """Muestra tabla resumen de todos los momios guardados con opción de editar."""
    if not momios_data:
        return

    section_header("📋 Momios guardados", len(momios_data))

    import pandas as pd

    rows = []
    for pk, vals in momios_data.items():
        meta = vals.get("meta", {})
        home = meta.get("home") or pk.split("_")[0]
        away = meta.get("away") or (pk.split("_")[1] if len(pk.split("_")) > 1 else "?")
        fecha = meta.get("fecha") or (pk.split("_")[-1] if len(pk.split("_")) > 2 else "?")
        liga = meta.get("liga", "—")
        rows.append({
            "Partido": f"{home} vs {away}",
            "Fecha": fecha,
            "Liga": liga,
            "Local": f"{vals.get('home', '—')}" if vals.get('home') else "—",
            "Empate": f"{vals.get('draw', '—')}" if vals.get('draw') else "—",
            "Visit.": f"{vals.get('away', '—')}" if vals.get('away') else "—",
        })

    if rows:
        df = pd.DataFrame(rows).sort_values("Fecha")
        st.dataframe(df, use_container_width=True, hide_index=True, height=320)

    col_clear, _ = st.columns([1, 3])
    with col_clear:
        if st.button("🗑 Limpiar todos los momios", key="btn_clear_all_momios"):
            st.session_state["momios_data"] = {}
            mark_modified()
            toast("Momios eliminados", "info")
            st.rerun()
