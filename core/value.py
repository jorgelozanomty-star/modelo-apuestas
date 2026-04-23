"""
core/value.py
Valor esperado, eliminación de vig y evaluación de mercados.
"""
from core.kelly import fractional_kelly, stake_amount


# ── Probabilidad implícita ────────────────────────────────────────────────────

def implied_raw(momio: float) -> float:
    """Probabilidad implícita cruda (con vig incluido)."""
    if momio <= 0:
        return 0.0
    return 1.0 / momio


def overround(momios: list[float]) -> float:
    """Overround (margen de la casa). 1.0 = sin margen."""
    return sum(implied_raw(m) for m in momios if m > 0)


def remove_vig(momios: list[float]) -> list[float]:
    """
    Elimina el vig usando el método multiplicativo.
    Divide cada probabilidad implícita cruda entre el overround.
    Retorna probabilidades limpias que suman 1.0.
    """
    OR = overround(momios)
    if OR <= 0:
        return [1.0 / len(momios)] * len(momios)
    return [implied_raw(m) / OR for m in momios]


# ── Valor Esperado ────────────────────────────────────────────────────────────

def ev_pct(prob: float, momio: float) -> float:
    """EV como porcentaje. >0 = valor positivo."""
    return (prob * momio - 1.0) * 100.0


def edge_pct(prob_modelo: float, momio: float) -> float:
    """Edge = diferencia entre probabilidad del modelo e implícita limpia."""
    return (prob_modelo - implied_raw(momio)) * 100.0


# ── Evaluación de mercados ────────────────────────────────────────────────────

def evaluate_pick(name: str, prob: float, momio: float,
                  fraction: float, bankroll: float) -> dict:
    """
    Evalúa un pick individual.
    Retorna dict con todo lo necesario para mostrarlo en la UI.
    """
    ev   = ev_pct(prob, momio)
    impl = implied_raw(momio) * 100.0
    edg  = prob * 100.0 - impl
    k    = fractional_kelly(prob, momio, fraction)
    stk  = stake_amount(prob, momio, fraction, bankroll)
    return {
        "name":     name,
        "prob":     prob,
        "momio":    momio,
        "ev":       ev,
        "implied":  impl,
        "edge":     edg,
        "kelly":    k,
        "stake":    stk,
        "has_value": ev > 0,
    }


def evaluate_1x2(markets: dict, m_l: float, m_e: float, m_v: float,
                 fraction: float, bankroll: float,
                 name_l: str = "Local", name_v: str = "Visita") -> list[dict]:
    """Evalúa los tres resultados principales."""
    picks = [
        evaluate_pick(name_l,  markets["p_l"], m_l, fraction, bankroll),
        evaluate_pick("Empate", markets["p_e"], m_e, fraction, bankroll),
        evaluate_pick(name_v,  markets["p_v"], m_v, fraction, bankroll),
    ]
    # Calcula vig-free probabilities y lo agrega como referencia
    vf = remove_vig([m_l, m_e, m_v])
    for pick, vf_p in zip(picks, vf):
        pick["vig_free_impl"] = vf_p * 100.0
    return picks


def evaluate_ou(markets: dict, line: float,
                m_over: float, m_under: float,
                fraction: float, bankroll: float) -> list[dict]:
    """Evalúa Over/Under para una línea dada."""
    key_over  = f"over{str(line).replace('.','')}"
    key_under = f"under{str(line).replace('.','')}"
    p_over  = markets.get(key_over,  0.0)
    p_under = markets.get(key_under, 0.0)
    return [
        evaluate_pick(f"Over {line}",  p_over,  m_over,  fraction, bankroll),
        evaluate_pick(f"Under {line}", p_under, m_under, fraction, bankroll),
    ]
