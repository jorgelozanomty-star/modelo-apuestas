"""
data/sofascore.py
Integración con Sofascore via EasySoccerData.
Carga automática de standings, fixtures y stats de equipo.
Sin necesidad de copiar/pegar tablas de FBRef.
"""
import pandas as pd
from datetime import date, datetime


# ── IDs de torneos en Sofascore ───────────────────────────────────────────────
# season_id cambia cada temporada — ponemos el más reciente conocido
SOFASCORE_TOURNAMENTS = {
    "Liga MX": {
        "tournament_id": 11098,   # Liga MX Clausura 2026 (actualizar cada torneo)
        "season_id":     63866,
    },
    "Premier League": {
        "tournament_id": 17,
        "season_id":     62039,   # 2025/26
    },
    "La Liga": {
        "tournament_id": 8,
        "season_id":     61643,
    },
    "Bundesliga": {
        "tournament_id": 35,
        "season_id":     62045,
    },
    "Serie A": {
        "tournament_id": 23,
        "season_id":     62042,
    },
}


def _sofascore_available() -> bool:
    try:
        import esd  # noqa
        return True
    except ImportError:
        return False


def load_standings(league: str) -> pd.DataFrame | None:
    """
    Carga la tabla de posiciones de una liga desde Sofascore.
    Retorna DataFrame compatible con el parser de 'Tabla General'.
    """
    if not _sofascore_available():
        return None
    cfg = SOFASCORE_TOURNAMENTS.get(league)
    if not cfg:
        return None
    try:
        import esd
        client = esd.SofascoreClient()
        standings = client.get_tournament_standing(
            tournament_id=cfg["tournament_id"],
            season_id=cfg["season_id"],
        )
        rows = []
        for row in standings:
            team = row.get("team", {})
            rows.append({
                "Rk":    row.get("position", 0),
                "Squad": team.get("name", ""),
                "MP":    row.get("matches", row.get("played", 0)),
                "W":     row.get("wins", 0),
                "D":     row.get("draws", 0),
                "L":     row.get("losses", 0),
                "GF":    row.get("scoresFor", row.get("goalsFor", 0)),
                "GA":    row.get("scoresAgainst", row.get("goalsAgainst", 0)),
                "GD":    row.get("goalDifference", 0),
                "Pts":   row.get("points", 0),
                "Pts/MP": round(row.get("points", 0) / max(row.get("matches", 1), 1), 2),
            })
        if not rows:
            return None
        df = pd.DataFrame(rows)
        # Normalizar nombres
        from data.parser import EQUIPOS_MAP
        df["Squad"] = df["Squad"].replace(EQUIPOS_MAP)
        return df
    except Exception as e:
        return None


def load_fixtures(league: str) -> pd.DataFrame | None:
    """
    Carga el calendario de partidos desde Sofascore.
    Retorna DataFrame compatible con parse_fixtures.
    """
    if not _sofascore_available():
        return None
    cfg = SOFASCORE_TOURNAMENTS.get(league)
    if not cfg:
        return None
    try:
        import esd
        client = esd.SofascoreClient()
        matches = client.get_tournament_matches(
            tournament_id=cfg["tournament_id"],
            season_id=cfg["season_id"],
        )
        rows = []
        for m in matches:
            home_team = m.get("homeTeam", {}).get("name", "")
            away_team = m.get("awayTeam", {}).get("name", "")
            # Timestamp Unix → date
            ts = m.get("startTimestamp", 0)
            try:
                dt = datetime.fromtimestamp(ts)
                match_date = dt.date()
                time_str   = dt.strftime("%H:%M")
            except Exception:
                match_date = date.today()
                time_str   = ""
            # Status
            status = m.get("status", {}).get("type", "notstarted")
            played = status in ("finished", "afterextratime", "afterpenalties")
            # Score
            score = None
            if played:
                hs = m.get("homeScore", {}).get("current", 0)
                as_ = m.get("awayScore", {}).get("current", 0)
                score = f"{hs}-{as_}"
            # Round / jornada
            wk = None
            rd = m.get("roundInfo", {})
            if rd:
                wk = rd.get("round", None)
            rows.append({
                "wk":     wk,
                "date":   match_date,
                "time":   time_str,
                "home":   home_team,
                "away":   away_team,
                "score":  score,
                "played": played,
            })
        if not rows:
            return None
        df = pd.DataFrame(rows)
        # Normalizar nombres
        from data.parser import EQUIPOS_MAP
        df["home"] = df["home"].replace(EQUIPOS_MAP)
        df["away"] = df["away"].replace(EQUIPOS_MAP)
        df = df.drop_duplicates(subset=["date", "home", "away"])
        return df.reset_index(drop=True)
    except Exception as e:
        return None


def load_team_stats(league: str) -> dict[str, pd.DataFrame] | None:
    """
    Carga estadísticas de equipos desde Sofascore usando los partidos jugados.
    Construye DataFrames compatibles con Standard Squad y Standard Opp.
    Agrega goles, xG (si disponible) y goles en contra por equipo.
    """
    if not _sofascore_available():
        return None
    cfg = SOFASCORE_TOURNAMENTS.get(league)
    if not cfg:
        return None
    try:
        import esd
        client = esd.SofascoreClient()
        matches = client.get_tournament_matches(
            tournament_id=cfg["tournament_id"],
            season_id=cfg["season_id"],
        )
        from data.parser import EQUIPOS_MAP
        team_stats = {}  # {team_name: {gf, ga, xg, xga, mp}}

        for m in matches:
            status = m.get("status", {}).get("type", "notstarted")
            if status not in ("finished", "afterextratime", "afterpenalties"):
                continue
            home = EQUIPOS_MAP.get(m.get("homeTeam", {}).get("name", ""),
                                   m.get("homeTeam", {}).get("name", ""))
            away = EQUIPOS_MAP.get(m.get("awayTeam", {}).get("name", ""),
                                   m.get("awayTeam", {}).get("name", ""))
            hs = m.get("homeScore", {}).get("current", 0) or 0
            as_ = m.get("awayScore", {}).get("current", 0) or 0

            for team, gf, ga in [(home, hs, as_), (away, as_, hs)]:
                if team not in team_stats:
                    team_stats[team] = {"MP": 0, "Gls": 0, "GA": 0, "xG": 0.0, "xGA": 0.0}
                team_stats[team]["MP"]  += 1
                team_stats[team]["Gls"] += gf
                team_stats[team]["GA"]  += ga

        if not team_stats:
            return None

        rows_sq = []
        rows_op = []
        for team, s in team_stats.items():
            mp = max(s["MP"], 1)
            rows_sq.append({
                "Squad": team,
                "MP":    mp,
                "Gls":   round(s["Gls"] / mp, 2),  # per game
                "xG":    round(s["xG"]  / mp, 2),
            })
            rows_op.append({
                "Squad": team,
                "MP":    mp,
                "Gls":   round(s["GA"]  / mp, 2),  # per game
                "xG":    round(s["xGA"] / mp, 2),
            })

        return {
            "Standard Squad": pd.DataFrame(rows_sq),
            "Standard Opp":   pd.DataFrame(rows_op),
        }
    except Exception as e:
        return None


def get_season_ids_hint() -> str:
    """Retorna un hint con los IDs configurados para actualización manual."""
    lines = ["IDs actuales (actualizar cada temporada):"]
    for lg, cfg in SOFASCORE_TOURNAMENTS.items():
        lines.append(f"  {lg}: tournament={cfg['tournament_id']} season={cfg['season_id']}")
    return "\n".join(lines)
