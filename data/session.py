"""
data/session.py
Estado de sesión centralizado y persistencia JSON.
El JSON ahora incluye tablas FBRef, fixtures, momios y bankroll.
"""
import json
import datetime
import io
import pandas as pd
import streamlit as st

from data.leagues import LEAGUE_NAMES


# ── Defaults ──────────────────────────────────────────────────────────────────

DEFAULTS = {
    # Bankroll
    "banca_actual":        1000.0,
    "banca_inicial":       1000.0,
    # Apuestas
    "jornada_pendientes":  [],
    "historial":           [],
    # FBRef — dict {liga: {tabla: df}}
    "fbref_store":         {},
    # Fixtures — dict {liga: lista de dicts}
    "fixtures_store":      {},
    # Momios — dict {"Local vs Visita": {m_l, m_e, ...}}
    "momios_store":        {},
    # H2H — dict {"Local_Visita": {...}}
    "h2h_store":           {},
    # Home/Away splits — dict {league: {squad: {home:{...}, away:{...}}}}
    "ha_store":            {},
    # UI state
    "selected_home":       None,
    "selected_away":       None,
    "selected_league":     "Liga MX",
    "h2h_match_key":       "",
}


def init():
    """Inicializa session_state con defaults."""
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            import copy
            st.session_state[k] = copy.deepcopy(v)


# ── Serialización DataFrame ────────────────────────────────────────────────────

def _df_to_dict(df: pd.DataFrame) -> dict:
    """DataFrame → JSON-serializable dict."""
    return {
        "columns": list(df.columns),
        "data": df.where(pd.notnull(df), None).values.tolist(),
    }


def _dict_to_df(d: dict) -> pd.DataFrame:
    """JSON dict → DataFrame."""
    try:
        df = pd.DataFrame(d["data"], columns=d["columns"])
        # Reconvertir columnas numéricas
        for c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="ignore")
        return df
    except Exception:
        return pd.DataFrame()


# ── Export ────────────────────────────────────────────────────────────────────

def export_session() -> str:
    """Serializa el estado completo a JSON string."""
    ss = st.session_state

    # Serializar fbref_store
    fbref_serial = {}
    for liga, tablas in ss.get("fbref_store", {}).items():
        fbref_serial[liga] = {}
        for tabla, df in tablas.items():
            if isinstance(df, pd.DataFrame) and len(df) > 0:
                fbref_serial[liga][tabla] = _df_to_dict(df)

    # Serializar fixtures_store
    fixtures_serial = {}
    for liga, rows in ss.get("fixtures_store", {}).items():
        if rows:
            fixtures_serial[liga] = rows  # ya son listas de dicts

    payload = {
        "version":             "3.0",
        "exported_at":         datetime.datetime.now().isoformat(),
        "banca_actual":        float(ss.get("banca_actual", 1000.0)),
        "banca_inicial":       float(ss.get("banca_inicial", 1000.0)),
        "jornada_pendientes":  ss.get("jornada_pendientes", []),
        "historial":           ss.get("historial", []),
        "fbref_store":         fbref_serial,
        "fixtures_store":      fixtures_serial,
        "momios_store":        ss.get("momios_store", {}),
        "h2h_store":           ss.get("h2h_store", {}),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


# ── Import ────────────────────────────────────────────────────────────────────

def import_session(json_bytes) -> tuple[bool, str]:
    """
    Carga un JSON de sesión.
    Retorna (éxito, mensaje).
    """
    try:
        data = json.loads(json_bytes)
        ss = st.session_state

        ss["banca_actual"]       = float(data.get("banca_actual",       1000.0))
        ss["banca_inicial"]      = float(data.get("banca_inicial",      1000.0))
        ss["jornada_pendientes"] = data.get("jornada_pendientes", [])
        ss["historial"]          = data.get("historial",          [])
        ss["momios_store"]       = data.get("momios_store",       {})
        ss["h2h_store"]          = data.get("h2h_store",          {})

        # Deserializar fbref_store
        fbref_raw = data.get("fbref_store", {})
        ss["fbref_store"] = {}
        for liga, tablas in fbref_raw.items():
            ss["fbref_store"][liga] = {}
            for tabla, df_dict in tablas.items():
                ss["fbref_store"][liga][tabla] = _dict_to_df(df_dict)

        # Deserializar fixtures_store
        ss["fixtures_store"] = data.get("fixtures_store", {})

        n_ligas    = len(ss["fbref_store"])
        n_apuestas = len(ss["jornada_pendientes"])
        n_hist     = len(ss["historial"])
        return True, f"✓ Sesión cargada — {n_ligas} liga(s) · {n_apuestas} apuesta(s) · {n_hist} historial"

    except Exception as e:
        return False, f"Error al cargar: {e}"


# ── Helpers de acceso ─────────────────────────────────────────────────────────

def get_data_master(league: str) -> dict:
    """Retorna el dict de tablas FBRef para una liga específica."""
    return st.session_state.get("fbref_store", {}).get(league, {})


def set_table(league: str, table_name: str, df: pd.DataFrame):
    """Guarda un DataFrame en fbref_store."""
    if "fbref_store" not in st.session_state:
        st.session_state["fbref_store"] = {}
    if league not in st.session_state["fbref_store"]:
        st.session_state["fbref_store"][league] = {}
    st.session_state["fbref_store"][league][table_name] = df


def get_fixtures(league: str):
    """Retorna la lista de fixtures de una liga."""
    rows = st.session_state.get("fixtures_store", {}).get(league, [])
    if not rows:
        return None
    try:
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["played"] = df["played"].astype(bool)
        return df
    except Exception:
        return None


def set_fixtures(league: str, df):
    """Guarda fixtures de una liga."""
    if "fixtures_store" not in st.session_state:
        st.session_state["fixtures_store"] = {}
    rows = []
    for _, row in df.iterrows():
        r = dict(row)
        r["date"] = str(r["date"])
        rows.append(r)
    st.session_state["fixtures_store"][league] = rows


def get_momios(match_key: str) -> dict:
    """Retorna momios para un partido (clave: 'Local vs Visita')."""
    return st.session_state.get("momios_store", {}).get(match_key, {})


def set_momios(match_key: str, momios: dict):
    """Guarda momios para un partido."""
    if "momios_store" not in st.session_state:
        st.session_state["momios_store"] = {}
    st.session_state["momios_store"][match_key] = momios


def get_ha_store(league: str) -> dict:
    """Retorna el dict Home/Away splits para una liga."""
    return st.session_state.get("ha_store", {}).get(league, {})


def set_ha_store(league: str, ha: dict):
    """Guarda el Home/Away store para una liga."""
    if "ha_store" not in st.session_state:
        st.session_state["ha_store"] = {}
    st.session_state["ha_store"][league] = ha


def get_all_leagues_with_data() -> list[str]:
    """Retorna ligas que tienen al menos una tabla FBRef cargada."""
    return [
        lg for lg in LEAGUE_NAMES
        if st.session_state.get("fbref_store", {}).get(lg)
    ]


def get_all_pending_matches() -> list[dict]:
    """
    Retorna todos los partidos pendientes de todas las ligas,
    cada uno con su liga y sus momios si ya fueron cargados.
    """
    from datetime import date
    from data.fixtures import get_gameweek_matches, get_current_gameweek
    today = date.today()
    all_matches = []

    for league in LEAGUE_NAMES:
        df = get_fixtures(league)
        if df is None or len(df) == 0:
            continue
        # Todos los pendientes de la temporada
        pending = df[~df["played"]].copy()
        for _, row in pending.iterrows():
            key = f"{row['home']} vs {row['away']}"
            momios = get_momios(key)
            all_matches.append({
                "league":  league,
                "date":    row["date"],
                "time":    row.get("time", ""),
                "home":    row["home"],
                "away":    row["away"],
                "wk":      row.get("wk"),
                "key":     key,
                "momios":  momios,
                "has_momios": bool(momios.get("m_l")),
            })

    all_matches.sort(key=lambda x: (x["date"], x["time"]))
    return all_matches