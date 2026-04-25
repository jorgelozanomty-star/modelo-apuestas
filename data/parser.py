"""
data/parser.py
Parseo de tablas copiadas desde FBRef y utilidades de extracción de datos.
"""
import io
import pandas as pd

# ── Normalización de nombres de equipos ──────────────────────────────────────
EQUIPOS_MAP: dict = {
    # Liga MX — fixture names
    "UANL": "Tigres", "Tigres UANL": "Tigres",
    "Tigres": "Tigres", "UANL Mazatlán": "Mazatlán",
    "Guadalajara Chivas": "Chivas", "Guadalajara": "Chivas",
    "Xolos de Tijuana": "Xolos", "Club Tijuana": "Xolos",
    "Deportivo Toluca": "Toluca", "Club Leon": "León", "Club León": "León",
    "Juarez Atletico": "Juárez", "FC Juárez": "Juárez", "Juarez": "Juárez",
    "Atletico San Luis": "San Luis", "Atlético San Luis": "San Luis",
    "Pumas UNAM": "Pumas", "America": "América", "CA América": "América",
    "CF Monterrey": "Rayados", "CF Monterrey": "Rayados",
    "Deportivo Toluca FC": "Toluca",
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
    # Premier League (nombres alternativos comunes en FBRef y Team Mexico)
    "Manchester City": "Man City", "Manchester Utd": "Man United",
    "Manchester United": "Man United",
    "Newcastle Utd": "Newcastle", "Newcastle United": "Newcastle",
    "Nott'ham Forest": "Nottm Forest", "Nottingham Forest": "Nottm Forest",
    "Tottenham": "Tottenham Hotspur",
    "Wolverhampton Wanderers": "Wolves", "Wolverhampton": "Wolves",
    "Wolverhampton Wanderers FC": "Wolves",
    "West Ham United": "West Ham", "West Ham United FC": "West Ham",
    "Aston Villa FC": "Aston Villa",
    "Arsenal FC": "Arsenal", "Liverpool FC": "Liverpool",
    "Crystal Palace FC": "Crystal Palace",
    "Brentford FC": "Brentford", "Fulham FC": "Fulham",
    "Chelsea FC": "Chelsea", "Everton FC": "Everton",
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

def _split_wdl_gfga(middle: str, mp: int):
    """Divide W+D+L+GF+GA concatenados donde W+D+L=mp."""
    n = len(middle)
    for wi in range(1, min(3, n-2)):
        try: w = int(middle[:wi])
        except: continue
        if w < 0 or w > mp: continue
        for di in range(1, min(3, n-wi-1)):
            try: d = int(middle[wi:wi+di])
            except: continue
            if d < 0 or w+d > mp: continue
            l = mp - w - d
            ls = str(l); li = len(ls)
            if middle[wi+di:wi+di+li] == ls:
                gfga = middle[wi+di+li:]
                for split in range(1, len(gfga)):
                    gf_s = gfga[:split]; ga_s = gfga[split:]
                    if len(gf_s) > 1 and gf_s[0] == '0': continue
                    if len(ga_s) > 1 and ga_s[0] == '0': continue
                    try:
                        gf = int(gf_s); ga = int(ga_s)
                        if 0 <= gf <= 120 and 0 <= ga <= 120:
                            return w, d, l, gf, ga
                    except: continue
    return None


def _parse_fbref_stats_table(text: str):
    """
    Parser general para cualquier tabla de estadísticas FBRef
    (Standard Squad/Opp, Shooting, Misc, PlayingTime).
    Funciona cuando Streamlit convierte los tabs a espacios.
    Usa el encabezado para mapear columnas automáticamente.
    No sobreescribe columnas duplicadas (conserva la primera aparición = totales).
    """
    lines = [l.strip() for l in text.replace('\r\n','\n').replace('\r','\n').split('\n')]
    # Buscar encabezado
    header_idx = None
    for i, line in enumerate(lines):
        l = line.replace('Club Crest','').strip()
        if 'Squad' in l and any(k in l for k in ('MP','Gls','Sh','Fls','Min','Starts')):
            header_idx = i; break
    if header_idx is None: return None
    # Limpiar encabezado
    hline = (lines[header_idx]
             .replace('Club Crest','')
             .replace('# Pl','#Pl')
             .replace('Last 5','Last5')
             .replace('Pts/MP','PtsMP')
             .strip())
    col_names = [c.strip() for c in hline.split('\t')] if '\t' in hline else hline.split()
    try: sq_idx = col_names.index('Squad')
    except ValueError: sq_idx = 0
    data_cols = col_names[sq_idx + 1:]
    rows = []
    for line in lines[header_idx + 1:]:
        line = line.replace('Club Crest','').strip()
        if not line: continue
        tokens = line.split()
        if not tokens or tokens[0].lower() == 'squad': continue
        # Fin del nombre: primer token puramente numérico
        squad_end = 1
        for j, tok in enumerate(tokens):
            t = tok.replace(',','')
            if t.lstrip('+-').replace('.','',1).isdigit():
                squad_end = j; break
        squad = ' '.join(tokens[:squad_end]).strip()
        if not squad: continue
        # Parsear valores
        vals = []
        for tok in tokens[squad_end:]:
            t = tok.replace(',','')
            try:
                vals.append(float(t) if '.' in t else int(t))
            except ValueError:
                vals.append(None)
        if len(vals) < 3: continue
        row = {'Squad': squad}
        for k, col in enumerate(data_cols):
            if k < len(vals) and vals[k] is not None:
                if col not in row:  # No sobreescribir — conservar primera aparición (totales)
                    row[col] = vals[k]
        rows.append(row)
    if not rows: return None
    import pandas as pd
    df = pd.DataFrame(rows)
    df['Squad'] = df['Squad'].replace(EQUIPOS_MAP)
    bad = {'squad','squads','','nan','rk'}
    df = df[~df['Squad'].str.lower().fillna('').isin(bad)]
    return df.reset_index(drop=True) if len(df) > 0 else None


def _parse_fbref_space_sep(text: str):
    """
    Parser para tabla FBRef donde tabs se convirtieron a espacios.
    Ancla desde el lado derecho: Pts/MP (único decimal <= 3.01),
    luego cuenta 8 campos numéricos hacia la izquierda.
    Ignora la columna Last 5 y Notes automáticamente.
    """
    lines = [l.strip() for l in text.replace('\r\n','\n').replace('\r','\n').split('\n')]
    rows = []
    for line in lines:
        line = line.replace('Club Crest', '').strip()
        if not line: continue
        tokens = line.split()
        if not tokens or tokens[0].lower() in ('rk','rank','squad','w','d','l','notes'): continue
        try: rank = int(tokens[0])
        except ValueError: continue
        # Buscar Pts/MP — único token con punto y valor entre 0 y 3
        pts_mp_idx = None
        for i in range(len(tokens)-1, 0, -1):
            if '.' in tokens[i]:
                try:
                    v = float(tokens[i])
                    if 0.0 <= v <= 3.01:
                        pts_mp_idx = i; break
                except: continue
        if pts_mp_idx is None or pts_mp_idx < 9: continue
        try:
            pts_mp = float(tokens[pts_mp_idx])
            pts    = int(tokens[pts_mp_idx - 1])
            gd     = int(tokens[pts_mp_idx - 2])
            ga     = int(tokens[pts_mp_idx - 3])
            gf     = int(tokens[pts_mp_idx - 4])
            l      = int(tokens[pts_mp_idx - 5])
            d      = int(tokens[pts_mp_idx - 6])
            w      = int(tokens[pts_mp_idx - 7])
            mp     = int(tokens[pts_mp_idx - 8])
        except (ValueError, IndexError): continue
        squad = ' '.join(tokens[1:pts_mp_idx - 8]).strip()
        if not squad: continue
        rows.append({'Rk':rank,'Squad':squad,'MP':mp,'W':w,'D':d,'L':l,
                     'GF':gf,'GA':ga,'GD':gd,'Pts':pts,'Pts/MP':pts_mp})
    if not rows: return None
    df = pd.DataFrame(rows)
    df['Squad'] = df['Squad'].replace(EQUIPOS_MAP)
    bad = {'squad','squads','','nan','rk'}
    df = df[~df['Squad'].str.lower().fillna('').isin(bad)]
    return df.reset_index(drop=True) if len(df) > 0 else None


def _parse_fbref_no_tabs(text: str):
    """
    Parser especializado para texto de FBRef copiado sin tabs.
    FBRef a veces pega la tabla general como texto corrido sin separadores,
    con los resultados del Last 5 en líneas separadas (W/D/L).
    Funciona para la Tabla General — para otras tablas usar el botón Copy de FBRef.
    """
    import re
    lines = [l.strip() for l in text.replace('\r\n','\n').replace('\r','\n').split('\n')]
    rows = []
    for line in lines:
        if not line or line in ('W','D','L','Notes'): continue
        line = line.replace('Club Crest', '').strip()  # FBRef incluye el texto del escudo
        if not line: continue
        if not re.match(r'^\d+\s+[A-Za-záéíóúüñÁÉÍÓÚÜÑ]', line): continue
        m_rank = re.match(r'^(\d+)\s+', line)
        if not m_rank: continue
        rank = int(m_rank.group(1)); rest = line[m_rank.end():]
        nm = re.match(r'^([^\d]+)\s*(\d.+)$', rest)
        if not nm: continue
        squad = nm.group(1).strip(); nums = nm.group(2).strip()
        # Pts/MP siempre <= 3.00 → una cifra antes del punto
        pts_mp_m = re.search(r'([0-3]\.\d{2})$', nums)
        if not pts_mp_m: continue
        pts_mp = float(pts_mp_m.group(1))
        before_dec = nums[:pts_mp_m.start()]
        gd_pos = max(before_dec.rfind('+'), before_dec.rfind('-'))
        if gd_pos < 0: continue
        left = before_dec[:gd_pos]; right = before_dec[gd_pos:]
        sign = right[0]; gd_pts_str = right[1:]
        if len(left) < 3: continue
        mp = int(left[:2]); middle = left[2:]
        pts_approx = round(pts_mp * mp)
        pts, gd = None, None
        for pd_len in [1, 2]:
            if len(gd_pts_str) < pd_len: continue
            try:
                pts_try = int(gd_pts_str[-pd_len:])
                gd_raw  = gd_pts_str[:-pd_len]
                gd_try  = int(sign + gd_raw) if gd_raw else 0
                if abs(pts_try - pts_approx) <= 1:
                    pts, gd = pts_try, gd_try; break
            except: continue
        if pts is None: continue
        parsed = _split_wdl_gfga(middle, mp)
        if not parsed: continue
        w, d, l, gf, ga = parsed
        rows.append({'Rk':rank,'Squad':squad,'MP':mp,'W':w,'D':d,'L':l,
                     'GF':gf,'GA':ga,'GD':gd,'Pts':pts,'Pts/MP':pts_mp})
    if not rows: return None
    df = pd.DataFrame(rows)
    df['Squad'] = df['Squad'].replace(EQUIPOS_MAP)
    return df


def process_fbref_paste(text: str) -> pd.DataFrame | None:
    """
    Parsea una tabla copiada directamente desde FBRef.
    Robusto contra:
    - Columnas duplicadas (xG -> xG.1)
    - Filas de cabecera repetidas
    - Columna "Last 5" con emojis/colores
    - Separadores inconsistentes (tab, espacio múltiple)
    - Líneas vacías al inicio/final
    """
    if not text or len(text) < 10:
        return None
    # Si no hay tabs, intentar parsers alternativos en cascada
    if '\t' not in text:
        for alt_parser in [_parse_fbref_stats_table, _parse_fbref_space_sep, _parse_fbref_no_tabs]:
            result = alt_parser(text)
            if result is not None and len(result) > 0:
                return result
    try:
        # Limpiar caracteres problemáticos de FBRef
        clean = (text
                 .replace("Club Crest", "")
                 .replace("\r\n", "\n")
                 .replace("\r", "\n")
                 .strip())

        # Intentar parsear como TSV primero
        df = None
        for sep in ['\t', ',']:
            try:
                tmp = pd.read_csv(io.StringIO(clean), sep=sep, dtype=str,
                                  on_bad_lines='skip')
                if len(tmp.columns) >= 3 and len(tmp) >= 2:
                    df = tmp
                    break
            except Exception:
                continue

        # Si TSV/CSV falla, intentar con separador automático
        if df is None:
            try:
                df = pd.read_csv(io.StringIO(clean), sep=None,
                                 engine='python', dtype=str,
                                 on_bad_lines='skip')
            except Exception:
                return None

        if df is None or len(df.columns) < 2:
            return None

        # Limpiar nombres de columna
        df.columns = [str(c).strip() for c in df.columns]

        # Si no hay columna Squad, buscar alternativas comunes
        if 'Squad' not in df.columns:
            for alt in ['Team', 'Club', 'Equipo', 'squad']:
                if alt in df.columns:
                    df = df.rename(columns={alt: 'Squad'})
                    break
            else:
                # Intentar detectar columna con nombres de equipos
                for col in df.columns:
                    sample = df[col].dropna().head(5).tolist()
                    if any(str(v) in EQUIPOS_MAP or len(str(v)) > 3 for v in sample):
                        df = df.rename(columns={col: 'Squad'})
                        break
                else:
                    return None

        # Limpiar columna Squad
        df['Squad'] = (df['Squad']
                       .astype(str)
                       .str.replace("Club Crest", "", regex=False)
                       .str.strip())
        df['Squad'] = df['Squad'].replace(EQUIPOS_MAP)

        # Eliminar filas de cabecera repetidas y totales
        bad = {'squad', 'squads', 'team', 'total', 'totals',
               'average', 'avg', '', 'nan', 'none', 'club'}
        df = df[~df['Squad'].str.lower().fillna('').isin(bad)]

        # Eliminar filas donde columna numérica clave tiene el nombre de la col
        for chk in ['MP', 'Rk', '90s', 'Gls', 'GF', 'Pts']:
            if chk in df.columns:
                mask = df[chk].astype(str).str.lower().ne(chk.lower())
                df = df[mask]
                break

        if len(df) < 2:
            return None

        # Convertir columnas numéricas (excluir columnas de texto conocidas)
        for c in df.columns:
            if c not in _SKIP_COLS:
                df[c] = pd.to_numeric(df[c], errors='ignore')

        return df.reset_index(drop=True)

    except Exception:
        for alt_parser in [_parse_fbref_stats_table, _parse_fbref_space_sep, _parse_fbref_no_tabs]:
            try:
                result = alt_parser(text)
                if result is not None and len(result) > 0:
                    return result
            except Exception:
                continue
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




# ── Home / Away split table parser ───────────────────────────────────────────

def _parse_ha_block(s: str) -> dict | None:
    """Parse one home or away stats block. Handles GD=0 (no sign)."""
    import re
    from itertools import product as _product

    pts_mp_m = re.search(r"\d\.\d{2}$", s)
    if not pts_mp_m:
        return None
    pts_mp = float(pts_mp_m.group())
    rest   = s[:pts_mp_m.start()]

    # Case 1: GD has a sign (+ or -)
    sign_m = re.search(r"[+\-]", rest)
    if sign_m:
        sign   = sign_m.group()
        before = rest[:sign_m.start()]
        after  = rest[sign_m.start()+1:]
        for i in range(1, len(after)+1):
            gd_d, pts_s = after[:i], after[i:]
            if not gd_d.isdigit(): continue
            if pts_s and not pts_s.isdigit(): continue
            gd  = int(sign + gd_d)
            pts = int(pts_s) if pts_s else 0
            if not (0 <= pts <= 114 and -60 <= gd <= 60): continue
            n = len(before)
            for widths in _product([1,2], repeat=6):
                if sum(widths) != n: continue
                nums = []; pos = 0
                for w in widths:
                    nums.append(int(before[pos:pos+w])); pos += w
                mp,ww,d,l,gf,ga = nums
                if gf-ga==gd and ww+d+l==mp and mp<=38:
                    return {"MP":mp,"W":ww,"D":d,"L":l,"GF":gf,"GA":ga,
                            "GD":gd,"Pts":pts,"Pts_MP":pts_mp}

    # Case 2: GD=0 (no sign) — rest = MP W D L GF GA 0 Pts
    n = len(rest)
    for widths in _product([1,2], repeat=8):
        if sum(widths) != n: continue
        nums = []; pos = 0
        for w in widths:
            nums.append(int(rest[pos:pos+w])); pos += w
        mp,ww,d,l,gf,ga,gd,pts = nums
        if gd==0 and gf==ga and ww+d+l==mp and mp<=38 and 0<=pts<=114:
            return {"MP":mp,"W":ww,"D":d,"L":l,"GF":gf,"GA":ga,
                    "GD":0,"Pts":pts,"Pts_MP":pts_mp}
    return None


def parse_home_away_table(text: str) -> dict | None:
    """
    Parsea la tabla Home/Away de FBRef.
    Acepta el formato con links markdown: [Nombre](url)
    Retorna dict {squad: {home:{...}, away:{...}, gf_home_pg, ga_home_pg, gf_away_pg, ga_away_pg}}
    """
    import re
    if not text or len(text) < 20:
        return None

    # Encontrar inicio del primer equipo
    m0 = re.search(r"\d+\s+\[", text)
    if not m0:
        return None
    text = text[m0.start():]

    # Dividir en entries por equipo: el límite es X.XX seguido de rank [
    parts = re.split(r"(?<=\d\.\d{2})(?=\d+\s+\[)", text)

    result = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r"\d+\s+\[([^\]]+)\]\([^)]+\)([\s\S]*)", part)
        if not m:
            continue
        name  = m.group(1).strip()
        stats = re.sub(r"[^\d+\-.]", "", m.group(2).strip())

        # Dividir en bloque home/away usando el primer Pts/MP como frontera
        pts_mps = list(re.finditer(r"\d\.\d{2}", stats))
        if len(pts_mps) < 2:
            continue
        split  = pts_mps[0].end()
        home_s = stats[:split]
        away_s = stats[split:]

        h = _parse_ha_block(home_s)
        a = _parse_ha_block(away_s)
        if not h or not a:
            continue

        norm_name = EQUIPOS_MAP.get(name, name)
        result[norm_name] = {
            "home": h, "away": a,
            "gf_home_pg": round(h["GF"] / max(h["MP"],1), 3),
            "ga_home_pg": round(h["GA"] / max(h["MP"],1), 3),
            "gf_away_pg": round(a["GF"] / max(a["MP"],1), 3),
            "ga_away_pg": round(a["GA"] / max(a["MP"],1), 3),
            "pts_home_pg": h["Pts_MP"],
            "pts_away_pg": a["Pts_MP"],
        }

    return result if result else None
