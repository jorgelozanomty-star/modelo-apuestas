"""
core/poisson.py
Modelo Poisson para predicción de goles en fútbol.
Sin dependencias de Streamlit — matemáticas puras.
"""
import math

MAX_GOALS = 9  # Límite de goles para la matriz (P(x>=9) es despreciable)


def goal_prob(lam: float, k: int) -> float:
    """P(X=k) para distribución Poisson con media lam."""
    if lam <= 0 or k < 0:
        return 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def calc_matrix(lam_l: float, lam_v: float, n: int = MAX_GOALS) -> dict:
    """
    Calcula la matriz de probabilidades de marcadores (i, j).
    Retorna el dict con (goles_local, goles_visita) -> probabilidad.
    """
    lam_l = max(0.10, lam_l)
    lam_v = max(0.10, lam_v)
    matrix = {}
    for i in range(n):
        for j in range(n):
            matrix[(i, j)] = goal_prob(lam_l, i) * goal_prob(lam_v, j)
    return matrix


def calc_1x2(matrix: dict) -> tuple[float, float, float]:
    """Probabilidades de Local / Empate / Visita."""
    p_l = p_e = p_v = 0.0
    for (i, j), p in matrix.items():
        if i > j:   p_l += p
        elif i < j: p_v += p
        else:       p_e += p
    return p_l, p_e, p_v


def calc_ou(matrix: dict, line: float) -> tuple[float, float]:
    """Over / Under para una línea dada (ej. 2.5, 1.5, 3.5)."""
    over = sum(p for (i, j), p in matrix.items() if i + j > line)
    return over, 1.0 - over


def calc_btts(matrix: dict) -> tuple[float, float]:
    """Ambos marcan / No ambos marcan."""
    btts = sum(p for (i, j), p in matrix.items() if i > 0 and j > 0)
    return btts, 1.0 - btts


def calc_double_chance(p_l: float, p_e: float, p_v: float) -> dict:
    """Double Chance: 1X, X2, 12."""
    return {
        "1X": p_l + p_e,
        "X2": p_e + p_v,
        "12": p_l + p_v,
    }


def calc_asian_hdp(matrix: dict, hdp: float) -> tuple[float, float]:
    """
    Handicap asiático para el local.
    hdp negativo = local favorito (ej. -0.5, -1, -1.5).
    hdp positivo = local underdog (ej. +0.5, +1).
    Retorna (p_local_gana_hdp, p_visita_gana_hdp).
    Nota: líneas enteras (-1, -2) generan push (devolucion) en empate ajustado.
    """
    p_local = p_visita = p_push = 0.0
    for (i, j), p in matrix.items():
        diff = i - j + hdp      # diferencia ajustada
        if abs(diff) < 1e-9:    # empate ajustado → push
            p_push += p
        elif diff > 0:
            p_local += p
        else:
            p_visita += p
    # En líneas .5 no hay push; en líneas enteras se redistribuye
    if p_push > 1e-6:
        # Mercado de cuarto de línea: mitad gana, mitad push
        p_local  += p_push / 2
        p_visita += p_push / 2
    return p_local, p_visita


def calc_exact_scores(matrix: dict, top_n: int = 6) -> list[tuple]:
    """Top N marcadores exactos ordenados por probabilidad."""
    scores = sorted(matrix.items(), key=lambda x: x[1], reverse=True)
    return [(f"{i}-{j}", round(p * 100, 1)) for (i, j), p in scores[:top_n]]


def calc_all_markets(lam_l: float, lam_v: float) -> dict:
    """
    Calcula todos los mercados de una vez.
    Retorna un dict con todas las probabilidades listas para consumir en la UI.
    """
    matrix = calc_matrix(lam_l, lam_v)
    p_l, p_e, p_v = calc_1x2(matrix)
    over25, under25 = calc_ou(matrix, 2.5)
    over15, under15 = calc_ou(matrix, 1.5)
    over35, under35 = calc_ou(matrix, 3.5)
    btts, no_btts   = calc_btts(matrix)
    dc              = calc_double_chance(p_l, p_e, p_v)
    hdp_neg05_l, hdp_neg05_v = calc_asian_hdp(matrix, -0.5)
    hdp_neg10_l, hdp_neg10_v = calc_asian_hdp(matrix, -1.0)
    hdp_pos05_l, hdp_pos05_v = calc_asian_hdp(matrix, +0.5)
    exact           = calc_exact_scores(matrix, top_n=8)
    total_xg        = lam_l + lam_v

    return {
        "matrix":    matrix,
        "lam_l":     lam_l,
        "lam_v":     lam_v,
        "total_xg":  total_xg,
        # 1X2
        "p_l": p_l, "p_e": p_e, "p_v": p_v,
        # Over/Under
        "over15": over15, "under15": under15,
        "over25": over25, "under25": under25,
        "over35": over35, "under35": under35,
        # BTTS
        "btts": btts, "no_btts": no_btts,
        # Double Chance
        "dc_1x": dc["1X"], "dc_x2": dc["X2"], "dc_12": dc["12"],
        # Asian Handicap
        "hdp_neg05_l": hdp_neg05_l, "hdp_neg05_v": hdp_neg05_v,
        "hdp_neg10_l": hdp_neg10_l, "hdp_neg10_v": hdp_neg10_v,
        "hdp_pos05_l": hdp_pos05_l, "hdp_pos05_v": hdp_pos05_v,
        # Exact scores
        "exact": exact,
    }
