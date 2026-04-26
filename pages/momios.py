"""
Intelligence Pro — pages/momios.py  v4.1
Editor inline como camino principal. JSON como opción secundaria.
Fuzzy matching con confirmación explícita.
"""
import json
import datetime
import streamlit as st
from typing import Optional
from ui.styles import inject_styles
from ui.components import (
    bankroll_sidebar, pipeline_steps, section_header,
    fuzzy_confirm_block, momios_inline_editor, inline_tip,
    toast, auto_save_indicator, mark_modified, safe_key,
)
from data.leagues import LEAGUES, LEAGUE_NAMES


# ── Conversión momios ──────────────────────────────────────────

def _to_decimal(valor) -> Optional[float]:
    try:
        s = str(valor).strip().replace(",", ".")
        if not s or s == "0":
            return None
        f = float(s)
        if abs(f) >= 100:
            return round(f / 100 + 1, 4) if f > 0 else round(100 / abs(f) + 1, 4)
        if f > 1.0:
            return round(f, 4)
        return None
    except (ValueError, TypeError):
        return None


def _parse_momios_dict(d: dict) -> dict:
    return {k: _to_decimal(v) for k, v in d.items()
            if isinstance(v, (int, float, str)) and _to_decimal(v)}


# ── Fuzzy ─────────────────────────────────────────────────────

def _fuzzy_score(a: str, b: str) -> float:
    a, b = a.lower().strip(), b.lower().strip()
    if a == b:
        return 1.0
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _best_match(nombre: str, candidatos: list):
    scores = sorted([(c, _fuzzy_score(nombre, c)) for c in candidatos],
                    key=lambda x: x[1], reverse=True)
    best, score = scores[0] if scores else (None, 0)
    alts = [n for n, s in scores[1:4] if s > 0.2]
    return best, score, alts


# ── Session helpers ────────────────────────────────────────────

def _momios():
    st.session_state.setdefault("momios_data", {})
    return st.session_state["momios_data"]


def _all_equipo_names():
    nombres = set()
    for lp in st.session_state.get("fixtures_data", {}).values():
        if lp:
            for p in lp:
                nombres.add(p.get("home", ""))
                nombres.add(p.get("away", ""))
    return [n for n in nombres if n]


def _all_partidos():
    partidos = []
    for liga_key, lp in st.session_state.get("fixtures_data", {}).items():
        if not lp:
            continue
        for p in lp:
            if not p.get("jugado", False):
                partidos.append({**p, "liga": liga_key, "liga_key": liga_key})
    return partidos


# ── Render ─────────────────────────────────────────────────────

def render():
    inject_styles()
    with st.sidebar:
        bankroll_sidebar()
        st.divider()
        auto_save_indicator()

    st.markdown('<h1>💰 Momios</h1>', unsafe_allow_html=True)
    pipeline_steps()

    ss = st.session_state
    momios_data = _momios()
    todos = _all_partidos()

    if not todos:
        st.markdown(
            '<div style="text-align:center;padding:40px;background:var(--surface);'
            'border:1px dashed var(--border);border-radius:var(--radius)">'
            '<div style="font-size:2rem;margin-bottom:8px">📋</div>'
            '<div style="font-family:var(--font-display);font-size:1.1rem;font-weight:600">'
            'Primero carga fixtures en ① Cargar Ligas</div></div>',
            unsafe_allow_html=True,
        )
        return

    tab_inline, tab_json = st.tabs(["✏️ Editor directo", "📋 Cargar JSON"])

    with tab_inline:
        _inline(todos, momios_data)
    with tab_json:
        _json_loader(todos, momios_data)

    st.divider()
    _guardados(momios_data)


def _inline(todos, momios_data):
    ss = st.session_state
    ligas = list({p["liga"] for p in todos})

    cf1, cf2 = st.columns([2, 2])
    with cf1:
        liga_f = st.selectbox("Liga", ["Todas"] + sorted(ligas), key="mm_liga")
    with cf2:
        periodo = st.selectbox("Período",
                               ["Próximos 3 días", "Esta semana", "Próximas 2 semanas", "Todo"],
                               key="mm_periodo")

    hoy   = datetime.date.today()
    dias  = {"Próximos 3 días": 3, "Esta semana": 7, "Próximas 2 semanas": 14, "Todo": 9999}[periodo]
    limite = hoy + datetime.timedelta(days=dias)

    def pf(f):
        try:
            return datetime.datetime.strptime(str(f), "%Y-%m-%d").date()
        except Exception:
            return hoy + datetime.timedelta(days=1)

    filtrados = [
        p for p in todos
        if (liga_f == "Todas" or p["liga"] == liga_f) and pf(p.get("fecha", "")) <= limite
    ][:30]

    if not filtrados:
        inline_tip("Sin partidos en el período seleccionado.")
        return

    section_header("Partidos", len(filtrados))
    inline_tip("<strong>Formato:</strong> Americano <code>-110</code>/<code>+200</code> o Decimal <code>1.90</code>. Deja en blanco lo que no quieras apostar.")

    for p in filtrados:
        pk = f"{p.get('home','')}_{p.get('away','')}_{p.get('fecha','')}"
        p["momios"] = momios_data.get(pk, {})

    editados = momios_inline_editor(filtrados)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Guardar momios", use_container_width=True, key="btn_save_inline"):
        guardados = 0
        for pk, vals in editados.items():
            hv = _to_decimal(vals.get("home", ""))
            dv = _to_decimal(vals.get("draw", ""))
            av = _to_decimal(vals.get("away", ""))
            if any([hv, dv, av]):
                momios_data[pk] = {"home": hv, "draw": dv, "away": av, "meta": vals.get("meta", {})}
                guardados += 1
        ss["momios_data"] = momios_data
        mark_modified()
        toast(f"✅ {guardados} partidos guardados", "success")
        st.rerun()


def _json_loader(todos, momios_data):
    ss = st.session_state
    inline_tip(
        "<strong>Flujo Team Mexico:</strong> Screenshots → Claude → JSON → pegar aquí"
    )

    raw = st.text_area("JSON de momios", height=200, key="mm_json",
                       placeholder='{"partidos": [{"home": "América", "away": "Chivas", '
                                   '"fecha": "2026-04-27", "momios": {"home": "-130", '
                                   '"draw": "+240", "away": "+380"}}]}',
                       label_visibility="collapsed")
    if not raw.strip():
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        toast(f"❌ JSON inválido: {e}", "error")
        return

    partidos_json = data.get("partidos", data if isinstance(data, list) else [])
    if not partidos_json:
        toast("⚠️ JSON sin partidos.", "info")
        return

    nombres_fbref = _all_equipo_names()
    pending, seen = [], set()
    for p in partidos_json:
        for campo in ["home", "away"]:
            nombre = p.get(campo, "")
            if nombre and nombre not in seen and nombres_fbref:
                best, score, alts = _best_match(nombre, nombres_fbref)
                if best and score < 1.0 and score >= 0.4:
                    pending.append({"json_name": nombre, "fbref_name": best,
                                    "score": score, "alternativas": alts})
                    seen.add(nombre)

    confirmaciones = {}
    if pending:
        st.markdown("<br>", unsafe_allow_html=True)
        confirmaciones = fuzzy_confirm_block(pending)
        n_pend = len([f for f in pending if f["json_name"] not in confirmaciones])
        if n_pend:
            st.warning(f"⚠️ Confirma los {n_pend} nombres pendientes.")
            return

    # Preview
    section_header("Vista previa", len(partidos_json))
    import pandas as pd
    rows = []
    for p in partidos_json[:10]:
        h = confirmaciones.get(p.get("home", ""), p.get("home", ""))
        a = confirmaciones.get(p.get("away", ""), p.get("away", ""))
        m = p.get("momios", {})
        rows.append({"Partido": f"{h} vs {a}", "Fecha": p.get("fecha", "—"),
                     "Liga": p.get("liga", "—"),
                     "Local": m.get("home", "—"), "Empate": m.get("draw", "—"),
                     "Visit.": m.get("away", "—")})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✅ Confirmar y cargar", use_container_width=True, key="btn_load_json"):
        cargados = 0
        for p in partidos_json:
            home  = confirmaciones.get(p.get("home", ""), p.get("home", ""))
            away  = confirmaciones.get(p.get("away", ""), p.get("away", ""))
            fecha = p.get("fecha", "")
            pk    = f"{home}_{away}_{fecha}"
            try:
                md = _parse_momios_dict(p.get("momios", {}))
                if md:
                    momios_data[pk] = {**md, "meta": {"home": home, "away": away,
                                                        "fecha": fecha, "liga": p.get("liga", "")}}
                    cargados += 1
            except Exception:
                pass
        ss["momios_data"] = momios_data
        mark_modified()
        toast(f"✅ {cargados} partidos cargados", "success")
        st.rerun()


def _guardados(momios_data):
    if not momios_data:
        return
    section_header("📋 Momios guardados", len(momios_data))
    import pandas as pd
    rows = []
    for pk, vals in momios_data.items():
        meta = vals.get("meta", {})
        parts = pk.split("_")
        rows.append({
            "Partido": f"{meta.get('home', parts[0])} vs {meta.get('away', parts[1] if len(parts)>1 else '?')}",
            "Fecha":   meta.get("fecha", parts[-1] if len(parts)>2 else "—"),
            "Liga":    meta.get("liga", "—"),
            "Local":   f"{vals['home']:.2f}" if vals.get("home") else "—",
            "Empate":  f"{vals['draw']:.2f}" if vals.get("draw") else "—",
            "Visit.":  f"{vals['away']:.2f}" if vals.get("away") else "—",
        })
    st.dataframe(pd.DataFrame(rows).sort_values("Fecha"), use_container_width=True,
                 hide_index=True, height=300)
    if st.button("🗑 Limpiar todos", key="btn_clear_momios"):
        st.session_state["momios_data"] = {}
        mark_modified()
        st.rerun()

render()
