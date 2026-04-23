"""
data/parser.py
Parseo de tablas copiadas desde FBRef y utilidades de extracción de datos.
"""
import io
import pandas as pd

# ── Normalización de nombres de equipos ──────────────────────────────────────
EQUIPOS_MAP: dict = {
    # Liga MX
    "UANL": "Tigres", "Tigres UANL": "Tigres",
    "Club América": "América", "CA América": "América",
    "Guadalajara": "Chivas", "CD Guadalajara": "Chivas",
    "Cruz Azul": "Cruz Azul",
    "UNAM": "Pumas", "Pumas UNAM": "Pumas",
    "Monterrey": "Rayados", "CF Monterrey": "Rayados",
    "Toluca": "Toluca", "Pachuca": "Pachuca", "León": "León",
    "Santos": "Santos Laguna", "Santos Laguna": "Santos Laguna",
    "Atlas": "Atlas", "Necaxa": "Necaxa",
    "Querétaro": "Querétaro", "Mazatlán": "Mazatlán",
    "FC Juárez": "Juárez", "Tijuana": "Xolos",
    "Club Tijuana": "Xolos", "Puebla": "Puebla",
    "Atlético San Luis": "San Luis",
    # Premier League (nombres alternativos comunes en FBRef)
    "Manchester City": "Man City", "Manchester Utd": "Man United",
    "Newcastle Utd": "Newcastle", "Nott'ham Forest": "Nottm Forest",
    "Tottenham": "Spurs",
    # Bundesliga
    "Bayer Leverkusen": "Leverkusen", "RB Leipzig": "Leipzig",
    "Borussia Dortmund": "Dortmund", "Borussia M'gladbach": "Gladbach",
    # Serie A
    "Inter Milan": "Inter", "AC Milan": "Milan",
    "Hellas Verona": "Verona",
}

_MISSING = {'', 'nan', 'n/a', 'na', '-', '—', 'none', 'null',
            '#value!', '#n/a', '#ref!', 'inf', '-inf'}

_SKIP_COLS = {
    'Squad', 'Last 5', 'Goalkeeper', 'Top Team Scorer',
    'Notes', 'Country', 'Comp', 'LgRk', 'Attendance',
}


# ── Utilidades de extracción ──────────────────────────────────────────────────

def safe_float(v, default: float = 0.0) -> float:
    try:
        f = float(v)
        return default if f != f else f   # NaN check
    except Exception:
        return default


def fget(row, *keys, default: float = 0.0) -> float:
    """
    Lee la primera columna disponible con valor numérico real.
    Prueba cada key y también su variante pandas-duplicado (key.1, key.2).
    Ignora celdas vacías, NaN, 'N/A', '-', etc.
    """
    for k in keys:
        for candidate in [k, f"{k}.1", f"{k}.2"]:
            if candidate not in row.index:
                continue
            raw = row[candidate]
            if raw is None:
                continue
            if str(raw).strip().lower() in _MISSING:
                continue
            v = safe_float(raw, None)
            if v is not None:
                return v
    return default


def read_mp(row, fallback: int = 1) -> int:
    """Lee partidos jugados. Exige mínimo 3 para considerarlo válido."""
    v = fget(row, 'MP', '90s', 'PJ', 'Matches', default=0)
    return max(int(v), 1) if v >= 3 else max(fallback, 1)


# Umbrales para detectar si un valor es acumulado de temporada o por partido
_PG_THRESHOLDS = {
    'goals':  (5.0,   4.5),    # (umbral_acumulado, max_por_partido)
    'xg':     (4.0,   4.0),
    'shots':  (30.0,  22.0),
    'sot':    (12.0,  9.0),
    'fouls':  (15.0,  18.0),
    'cards':  (4.0,   4.0),
}


def pg(val: float, mp: int, kind: str = 'goals') -> float:
    """Convierte val a por-partido si supera el umbral de acumulado."""
    if val <= 0 or mp < 1:
        return 0.0
    threshold, max_val = _PG_THRESHOLDS.get(kind, (5.0, 99.0))
    result = (val / mp) if val > threshold else val
    return min(result, max_val)


# ── Parseo de tablas FBRef ────────────────────────────────────────────────────

def process_fbref_paste(text: str) -> pd.DataFrame | None:
    """
    Parsea una tabla copiada directamente desde FBRef.
    Maneja:
    - Columnas duplicadas que pandas renombra a .1, .2
    - Filas de cabecera repetidas que FBRef inserta en el HTML
    - Filas de totales/promedios
    - Conversión de columnas numéricas
    """
    if not text or len(text) < 10:
        return None
    try:
        clean = text.replace("Club Crest", "").strip()
        # Leer como string para poder limpiar antes de convertir tipos
        df = pd.read_csv(io.StringIO(clean), sep='\t', dtype=str)
        if len(df.columns) < 2:
            df = pd.read_csv(io.StringIO(clean), sep=None, engine='python', dtype=str)
        df.columns = [str(c).strip() for c in df.columns]
        if 'Squad' not in df.columns:
            return None
        # Limpiar columna Squad
        df['Squad'] = (df['Squad']
                       .str.replace("Club Crest", "", regex=False)
                       .str.strip())
        df['Squad'] = df['Squad'].replace(EQUIPOS_MAP)
        # Eliminar filas de cabecera repetidas y totales
        bad = {'squad', 'squads', 'total', 'average', 'avg', '', 'nan', 'none'}
        df = df[~df['Squad'].str.lower().fillna('').isin(bad)]
        # Eliminar filas donde la primera columna numérica tiene el nombre de la col
        for chk in ['MP', '90s', 'Gls', 'GF', 'Pts']:
            if chk in df.columns:
                df = df[df[chk].str.lower().fillna('').ne(chk.lower())]
                break
        # Convertir columnas numéricas
        for c in df.columns:
            if c not in _SKIP_COLS:
                df[c] = pd.to_numeric(df[c], errors='ignore')
        return df.reset_index(drop=True) if len(df) > 0 else None
    except Exception:
        return None


def get_team_row(data_master: dict, table_name: str, squad_name: str):
    """
    Busca la fila de un equipo en una tabla del data_master.
    Primero busca coincidencia exacta, luego parcial.
    Retorna pandas Series o None.
    """
    if table_name not in data_master:
        return None
    df = data_master[table_name]
    if 'Squad' not in df.columns:
        return None
    exact = df[df['Squad'] == squad_name]
    if not exact.empty:
        return exact.iloc[0]
    partial = df[df['Squad'].str.contains(squad_name, na=False, case=False)]
    return partial.iloc[0] if not partial.empty else None


def get_squad_list(data_master: dict) -> list[str]:
    """Retorna lista de equipos disponibles del primer DataFrame cargado."""
    for df in data_master.values():
        if 'Squad' in df.columns:
            return sorted(df['Squad'].dropna().unique().tolist())
    return []
