"""
data/leagues.py
Configuración por liga: ventaja local, ajuste de blend xG, nombre de tablas FBRef.

home_adv: goles adicionales sumados al λ del equipo local (modelo aditivo).
          Calibrado empíricamente para cada liga.

blend_jornada_threshold: número de jornadas a partir del cual se le da
          más peso al xG vs goles reales. Antes de ese umbral la muestra
          es muy pequeña.

xg_available: si FBRef suele tener xG para esta liga (todas las top-5 sí).
"""

LEAGUES: dict = {
    "Liga MX": {
        "home_adv":                0.25,   # ~0.25 goles extra jugando en casa
        "blend_jornada_threshold": 10,     # Clausura/Apertura ~17 jornadas
        "xg_available":            True,
        "flag":                    "🇲🇽",
        "fbref_hint":              "Liga MX",
    },
    "Premier League": {
        "home_adv":                0.20,
        "blend_jornada_threshold": 8,      # 38 jornadas, señal más estable
        "xg_available":            True,
        "flag":                    "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "fbref_hint":              "Premier League",
    },
    "La Liga": {
        "home_adv":                0.18,
        "blend_jornada_threshold": 8,
        "xg_available":            True,
        "flag":                    "🇪🇸",
        "fbref_hint":              "La Liga",
    },
    "Bundesliga": {
        "home_adv":                0.22,
        "blend_jornada_threshold": 8,
        "xg_available":            True,
        "flag":                    "🇩🇪",
        "fbref_hint":              "Bundesliga",
    },
    "Serie A": {
        "home_adv":                0.20,
        "blend_jornada_threshold": 8,
        "xg_available":            True,
        "flag":                    "🇮🇹",
        "fbref_hint":              "Serie A",
    },
}

LEAGUE_NAMES = list(LEAGUES.keys())


def get_league(name: str) -> dict:
    return LEAGUES.get(name, LEAGUES["Liga MX"])


def apply_home_advantage(lam_l: float, lam_v: float, league_name: str) -> tuple[float, float]:
    """
    Aplica la ventaja de local al λ del equipo de casa.
    Modelo aditivo: λ_l += home_adv.
    El λ visitante no se modifica (ya está implícita en el modelo).
    """
    cfg = get_league(league_name)
    return lam_l + cfg["home_adv"], lam_v


def blend_weights(jornadas_jugadas: int, league_name: str, has_xg: bool, has_npxg: bool) -> dict:
    """
    Pesos dinámicos del blend según jornadas jugadas y fuentes disponibles.
    En jornadas tempranas (pocos partidos), la muestra de goles es ruidosa:
    damos más peso al xG. Conforme avanza el torneo, los goles reales
    son más representativos.

    Retorna dict con claves 'goals', 'xg', 'npxg'.
    """
    cfg = get_league(league_name)
    threshold = cfg["blend_jornada_threshold"]
    early = jornadas_jugadas < threshold

    if has_xg and has_npxg:
        if early:
            return {"goals": 0.25, "xg": 0.45, "npxg": 0.30}
        else:
            return {"goals": 0.35, "xg": 0.40, "npxg": 0.25}
    elif has_xg:
        if early:
            return {"goals": 0.35, "xg": 0.65, "npxg": 0.0}
        else:
            return {"goals": 0.50, "xg": 0.50, "npxg": 0.0}
    else:
        return {"goals": 1.0, "xg": 0.0, "npxg": 0.0}
