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
    import pandas as pd
    nombres = set()
    for lp in st.session_state.get("fixtures_data", {}).values():
        if lp is None or (hasattr(lp, "__len__") and len(lp) == 0):
            continue
        if isinstance(lp, pd.DataFrame):
            for col in ["Home", "home", "Away", "away"]:
                if col in lp.columns:
                    nombres.update(lp[col].dropna().tolist())
        else:
            for p in lp:
                nombres.add(p.get("home", ""))
                nombres.add(p.get("away", ""))
    return [n for n in nombres if n]


def _all_partidos():
    import pandas as pd
    partidos = []
    for liga_key, lp in st.session_state.get("fixtures_data", {}).items():
        if lp is None or (hasattr(lp, "__len__") and len(lp) == 0):
            continue
        # lp puede ser DataFrame o lista de dicts
        if isinstance(lp, pd.DataFrame):
            df = lp.copy()
            # Partidos sin score = futuros
            if "Score" in df.columns:
                df = df[df["Score"].isna() | (df["Score"].astype(str).str.strip() == "")]
            for _, row in df.iterrows():
                partidos.append({
                    "home":  row.get("Home", row.get("home", "")),
                    "away":  row.get("Away", row.get("away", "")),
                    "fecha": row.get("Date", row.get("fecha", "")),
                    "hora":  row.get("Time", row.get("hora", "")),
                    "liga":  liga_key,
                    "liga_key": liga_key,
                })
        else:
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

    st.markdown(('<h1>💰 Momios</h1>').strip(), unsafe_allow_html=True)
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


def _parse_fecha_safe(f):
    import pandas as pd
    if f is None:
        return None
    # Pandas Timestamp
    if hasattr(f, "date"):
        try:
            return f.date()
        except Exception:
            pass
    # pandas NaT
    try:
        if pd.isna(f):
            return None
    except Exception:
        pass
    # String formats - también maneja "2026-05-02 00:00:00"
    s = str(f).strip().split(" ")[0].split("T")[0]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None


def _inline(todos, momios_data):
    ss = st.session_state
    ligas = list({p["liga"] for p in todos})

    cf1, cf2 = st.columns([2, 2])
    with cf1:
        liga_f = st.selectbox("Liga", ["Todas"] + sorted(ligas), key="mm_liga")
    with cf2:
        periodo = st.selectbox("Período",
                               ["Esta semana", "Próximos 3 días", "Próximas 2 semanas", "Todo"],
                               key="mm_periodo")

    hoy   = datetime.date.today()
    dias  = {"Próximos 3 días": 3, "Esta semana": 7, "Próximas 2 semanas": 14, "Todo": 9999}[periodo]
    limite = hoy + datetime.timedelta(days=dias)

    filtrados = []
    for p in todos:
        if liga_f != "Todas" and p["liga"] != liga_f:
            continue
        fecha_raw = p.get("fecha") or p.get("Date") or ""
        fecha_p = _parse_fecha_safe(fecha_raw)
        if fecha_p is None or (hoy <= fecha_p <= limite):
            filtrados.append(p)
    filtrados = filtrados[:40]

    if not filtrados:
        st.info("Sin partidos en el período. Prueba con 'Todo'.")
        return

    section_header("Partidos", len(filtrados))
    st.info("**Formato:** Americano `-110`/`+200` o Decimal `1.90` · Deja en blanco lo que no quieras apostar")

    # Headers
    hc = st.columns([3, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1])
    for col, lbl in zip(hc, ["Partido","Local","Empate","Visit.","O 2.5","U 2.5","BTTS"]):
        col.markdown(f"**{lbl}**")
    st.divider()

    inputs_map = {}
    for i, p in enumerate(filtrados):
        home  = p.get("home") or p.get("Home") or "?"
        away  = p.get("away") or p.get("Away") or "?"
        fecha = p.get("fecha") or p.get("Date") or ""
        pk    = f"{home}_{away}_{fecha}"
        ex    = momios_data.get(pk, {})

        row = st.columns([3, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1])
        with row[0]:
            st.markdown(f"**{home} vs {away}** · {p['liga']} · {fecha}", unsafe_allow_html=True)
        fields = [("home","-130"),("draw","+280"),("away","+350"),
                  ("over25","-115"),("under25","-105"),("btts_yes","-120")]
        row_inputs = {}
        for j, (key, ph) in enumerate(fields):
            with row[j+1]:
                row_inputs[key] = st.text_input(
                    key, value=str(ex[key]) if ex.get(key) else "",
                    placeholder=ph, key=f"mi_{i}_{key}",
                    label_visibility="collapsed"
                )
        inputs_map[pk] = {"inputs": row_inputs, "meta": {
            "home": home, "away": away, "fecha": fecha,
            "liga": p["liga"], "liga_key": p.get("liga_key","")
        }}

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Guardar momios", use_container_width=True, key="btn_save_inline"):
        guardados = 0
        for pk, data in inputs_map.items():
            vals = {k: _to_decimal(v) for k, v in data["inputs"].items()}
            if any(v for v in vals.values() if v):
                momios_data[pk] = {**vals, "meta": data["meta"]}
                guardados += 1
        ss["momios_data"] = momios_data
        mark_modified()
        st.success(f"✅ {guardados} partidos guardados")
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
        st.markdown(("<br>").strip(), unsafe_allow_html=True)
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

    st.markdown(("<br>").strip(), unsafe_allow_html=True)
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
