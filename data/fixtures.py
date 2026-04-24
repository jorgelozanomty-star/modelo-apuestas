"""
data/fixtures.py
Parser para tablas de Scores & Fixtures y Head-to-Head de FBRef.
Detecta automáticamente los partidos de la jornada actual según la fecha de hoy.
"""
import re
import pandas as pd
from datetime import date, datetime, timedelta


# ── Normalización de nombres ──────────────────────────────────────────────────
from data.parser import EQUIPOS_MAP, safe_float


def _norm(name: str) -> str:
    """Normaliza nombre de equipo."""
    n = str(name).strip()
    return EQUIPOS_MAP.get(n, n)


# ── Parser de Scores & Fixtures ───────────────────────────────────────────────

def parse_fixtures(text: str) -> pd.DataFrame | None:
    """
    Parsea la tabla Scores & Fixtures copiada de FBRef.
    Columnas esperadas: Wk, Day, Date, Time, Home, Score, Away, ...
    Retorna DataFrame con columnas: wk, date, time, home, away, score, played
    """
    if not text or len(text) < 20:
        return None
    try:
        lines = [l.strip() for l in text.replace('\r\n', '\n').replace('\r', '\n').split('\n')]
        rows = []
        header_found = False

        for line in lines:
            line = line.replace('Club Crest', '').strip()
            if not line:
                continue

            # Detectar encabezado
            if not header_found:
                if 'Home' in line and 'Away' in line and ('Date' in line or 'Wk' in line):
                    header_found = True
                continue

            # Saltar sub-encabezados repetidos
            if 'Home' in line and 'Away' in line:
                continue

            tokens = line.split()
            if len(tokens) < 5:
                continue

            # Buscar fecha con formato YYYY-MM-DD
            date_str = None
            date_idx = None
            for i, tok in enumerate(tokens):
                if re.match(r'^\d{4}-\d{2}-\d{2}$', tok):
                    date_str = tok
                    date_idx = i
                    break

            if date_str is None:
                continue

            try:
                match_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                continue

            # Jornada (Wk) — puede ser el primer token si es número
            wk = None
            try:
                wk = int(tokens[0])
            except ValueError:
                pass

            # Buscar Score (formato N-N) o "Head-to-Head"
            score = None
            score_idx = None
            home = None
            away = None

            for i, tok in enumerate(tokens):
                if re.match(r'^\d+[–\-]\d+$', tok):
                    score = tok.replace('–', '-')
                    score_idx = i
                    break

            if score_idx is not None:
                # Home está antes del score, Away después
                # Tokens entre date y score = time + home
                between = tokens[date_idx + 1: score_idx]
                # Primer token es hora (HH:MM)
                if between and re.match(r'^\d{1,2}:\d{2}$', between[0]):
                    time_str = between[0]
                    home_tokens = between[1:]
                else:
                    time_str = ""
                    home_tokens = between
                home = _norm(' '.join(home_tokens))
                away_tokens = tokens[score_idx + 1:]
                # Quitar tokens que son venue/referee info (números grandes = attendance)
                away_clean = []
                for t in away_tokens:
                    if t.replace(',', '').isdigit() and int(t.replace(',', '')) > 1000:
                        break
                    if re.match(r'^\d{4}-\d{2}-\d{2}$', t):
                        break
                    away_clean.append(t)
                away = _norm(' '.join(away_clean))
                played = True
            else:
                # Partido sin resultado todavía — buscar "Head-to-Head" o solo equipos
                played = False
                score = None
                # Tokens entre date y fin (antes de venue info)
                after_date = tokens[date_idx + 1:]
                # Primer token puede ser hora
                time_str = ""
                start = 0
                if after_date and re.match(r'^\d{1,2}:\d{2}$', after_date[0]):
                    time_str = after_date[0]
                    start = 1
                # Resto es Home [venue info] Away — difícil sin Score como separador
                # Usar heurística: si encontramos "Head-to-Head" al final, ignorarlo
                rest = [t for t in after_date[start:] if t not in ('Head-to-Head', 'Match', 'Report')]
                # Intentar dividir por nombre de venue conocido o por la mitad
                # Estrategia: buscar token que sea nombre de equipo conocido desde la derecha
                home_tokens = []
                away_tokens_list = []
                found_split = False
                for split_i in range(len(rest) - 1, 0, -1):
                    candidate_away = _norm(' '.join(rest[split_i:]))
                    candidate_home = _norm(' '.join(rest[:split_i]))
                    if candidate_away != ' '.join(rest[split_i:]):  # fue normalizado = es equipo
                        home = candidate_home
                        away = candidate_away
                        found_split = True
                        break
                if not found_split:
                    # Dividir por la mitad como fallback
                    mid = len(rest) // 2
                    home = _norm(' '.join(rest[:mid]))
                    away = _norm(' '.join(rest[mid:]))

            if not home or not away or home == away:
                continue
            # Filtrar basura
            if len(home) < 2 or len(away) < 2:
                continue

            rows.append({
                'wk':     wk,
                'date':   match_date,
                'time':   time_str if 'time_str' in dir() else '',
                'home':   home,
                'away':   away,
                'score':  score,
                'played': played,
            })

        if not rows:
            return None

        df = pd.DataFrame(rows)
        df = df.drop_duplicates(subset=['date', 'home', 'away'])
        return df.reset_index(drop=True)

    except Exception as e:
        return None


def get_current_gameweek(fixtures_df: pd.DataFrame, today: date = None) -> int | None:
    """
    Detecta la jornada actual o próxima.
    Lógica:
    - Si hay partidos pendientes esta semana → esa jornada
    - Si no → la jornada de la próxima fecha con partidos
    """
    if fixtures_df is None or len(fixtures_df) == 0:
        return None
    if today is None:
        today = date.today()

    # Partidos no jugados desde hoy en adelante
    pending = fixtures_df[
        (~fixtures_df['played']) & (fixtures_df['date'] >= today)
    ]
    if len(pending) == 0:
        return None

    # La fecha más próxima con partidos pendientes
    next_date = pending['date'].min()

    # Ventana de ±3 días alrededor de esa fecha (jornadas pueden durar varios días)
    window_start = next_date - timedelta(days=1)
    window_end   = next_date + timedelta(days=4)

    week_matches = fixtures_df[
        (~fixtures_df['played']) &
        (fixtures_df['date'] >= window_start) &
        (fixtures_df['date'] <= window_end)
    ]

    # Jornada (wk) más frecuente en esa ventana
    if 'wk' in week_matches.columns and week_matches['wk'].notna().any():
        wk = week_matches['wk'].dropna().mode()
        return int(wk.iloc[0]) if len(wk) > 0 else None
    return None


def get_gameweek_matches(fixtures_df: pd.DataFrame,
                         wk: int = None,
                         today: date = None) -> pd.DataFrame:
    """
    Retorna los partidos de una jornada específica.
    Si wk=None, usa la jornada actual detectada automáticamente.
    """
    if fixtures_df is None or len(fixtures_df) == 0:
        return pd.DataFrame()
    if today is None:
        today = date.today()
    if wk is None:
        wk = get_current_gameweek(fixtures_df, today)
    if wk is None:
        # Fallback: próximos 7 días
        return fixtures_df[
            (~fixtures_df['played']) &
            (fixtures_df['date'] >= today) &
            (fixtures_df['date'] <= today + timedelta(days=7))
        ].copy()

    return fixtures_df[fixtures_df['wk'] == wk].copy()


# ── Parser de H2H ─────────────────────────────────────────────────────────────

def parse_h2h(text: str) -> dict | None:
    """
    Parsea la tabla Head-to-Head de FBRef.
    Retorna dict con:
    - total: {team1_wins, draws, team2_wins, total_matches}
    - recent: lista de últimos N partidos (solo misma competición si es posible)
    - avg_goals: promedio de goles por partido
    - btts_pct: % de partidos ambos anotan
    - over25_pct: % de partidos con más de 2.5 goles
    """
    if not text or len(text) < 20:
        return None
    try:
        lines = [l.strip() for l in text.replace('\r\n', '\n').replace('\r', '\n').split('\n')]
        matches = []
        header_found = False

        for line in lines:
            line = line.replace('Club Crest', '').strip()
            if not line:
                continue
            if not header_found:
                if 'Home' in line and ('Score' in line or 'Away' in line):
                    header_found = True
                continue
            if 'Home' in line and 'Away' in line:
                continue

            tokens = line.split()
            if len(tokens) < 4:
                continue

            # Buscar Score N-N
            score_m = None
            score_idx = None
            for i, tok in enumerate(tokens):
                m = re.match(r'^(\d+)[–\-](\d+)$', tok)
                if m:
                    score_m = m
                    score_idx = i
                    break
            if score_m is None:
                continue

            gf = int(score_m.group(1))
            ga = int(score_m.group(2))
            total_goals = gf + ga

            # Fecha
            date_str = None
            for tok in tokens:
                if re.match(r'^\d{4}-\d{2}-\d{2}$', tok):
                    date_str = tok
                    break

            # Determinar ganador
            if gf > ga:
                winner = 'home'
            elif ga > gf:
                winner = 'away'
            else:
                winner = 'draw'

            matches.append({
                'date':        date_str,
                'gf':          gf,
                'ga':          ga,
                'total_goals': total_goals,
                'winner':      winner,
            })

        if not matches:
            return None

        # Calcular estadísticas — usar solo Premier League si hay mezcla
        # (FBRef incluye todas las competiciones en H2H)
        recent = matches[:10]  # Más recientes primero

        total = len(recent)
        if total == 0:
            return None

        home_wins  = sum(1 for m in recent if m['winner'] == 'home')
        draws      = sum(1 for m in recent if m['winner'] == 'draw')
        away_wins  = sum(1 for m in recent if m['winner'] == 'away')
        avg_goals  = sum(m['total_goals'] for m in recent) / total
        btts       = sum(1 for m in recent if m['gf'] > 0 and m['ga'] > 0) / total
        over25     = sum(1 for m in recent if m['total_goals'] > 2) / total
        over15     = sum(1 for m in recent if m['total_goals'] > 1) / total

        return {
            'total_matches': total,
            'home_wins':     home_wins,
            'draws':         draws,
            'away_wins':     away_wins,
            'avg_goals':     round(avg_goals, 2),
            'btts_pct':      round(btts * 100, 1),
            'over25_pct':    round(over25 * 100, 1),
            'over15_pct':    round(over15 * 100, 1),
            'recent':        recent,
        }
    except Exception:
        return None


def h2h_lambda_adjustment(h2h: dict, lam_l: float, lam_v: float,
                           weight: float = 0.15) -> tuple[float, float]:
    """
    Ajusta ligeramente los lambdas según el historial H2H.
    El ajuste es conservador (weight=15%) — el modelo base sigue dominando.

    Si en el H2H el local gana más de lo esperado por el modelo,
    sube levemente su lambda y baja el del visitante, y viceversa.
    """
    if h2h is None or h2h['total_matches'] < 3:
        return lam_l, lam_v

    total = h2h['total_matches']
    h2h_home_rate = h2h['home_wins'] / total
    h2h_away_rate = h2h['away_wins'] / total

    # Tasas implícitas del modelo actual
    model_total = lam_l + lam_v
    model_home_share = lam_l / model_total if model_total > 0 else 0.5

    # Diferencia entre H2H y modelo
    h2h_share = h2h_home_rate / (h2h_home_rate + h2h_away_rate) if (h2h_home_rate + h2h_away_rate) > 0 else 0.5
    delta = h2h_share - model_home_share

    # Ajuste suave
    adj = delta * weight
    new_lam_l = max(0.1, lam_l * (1 + adj))
    new_lam_v = max(0.1, lam_v * (1 - adj))

    return round(new_lam_l, 3), round(new_lam_v, 3)
