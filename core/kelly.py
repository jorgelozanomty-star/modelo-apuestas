"""
core/kelly.py
Criterio de Kelly y gestión de banca.
"""


def kelly_fraction(prob: float, momio: float) -> float:
    """
    Kelly completo: f = (p*(o-1) - (1-p)) / (o-1)
    Donde o = momio decimal, p = probabilidad del modelo.
    Retorna 0 si no hay edge positivo.
    """
    if momio <= 1.0 or prob <= 0.0 or prob >= 1.0:
        return 0.0
    edge = (momio - 1.0) * prob - (1.0 - prob)
    if edge <= 0:
        return 0.0
    return edge / (momio - 1.0)


def fractional_kelly(prob: float, momio: float, fraction: float = 0.25) -> float:
    """Kelly fraccionado. fraction=0.25 → Kelly/4 (recomendado para apuestas deportivas)."""
    return kelly_fraction(prob, momio) * fraction


def stake_amount(prob: float, momio: float, fraction: float, bankroll: float) -> float:
    """Monto a apostar en términos absolutos."""
    return max(0.0, bankroll * fractional_kelly(prob, momio, fraction))


def expected_return(stake: float, prob: float, momio: float) -> float:
    """Retorno esperado de una apuesta."""
    return stake * (prob * momio - 1.0)


def roi_pct(bankroll_actual: float, bankroll_inicial: float) -> float:
    if bankroll_inicial == 0:
        return 0.0
    return (bankroll_actual - bankroll_inicial) / bankroll_inicial * 100.0


def update_bankroll(bankroll: float, stake: float, momio: float, won: bool) -> float:
    """Actualiza la banca según el resultado de una apuesta."""
    if won:
        return bankroll + stake * (momio - 1.0)
    return bankroll - stake
