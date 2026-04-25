"""
backtest.py
Módulo de backtesting integrado con el modelo real (Poisson + Kelly + FBRef).
Usa core/poisson.py, core/value.py, core/kelly.py y data/profile.py.
"""
import pandas as pd
from typing import Dict, List, Tuple

from core.poisson import calc_all_markets
from core.value   import ev_pct, remove_vig, overround
from core.kelly   import fractional_kelly, stake_amount
from data.profile import build_team_profile, calc_lambdas
from data.leagues import LEAGUES


# ── Funciones auxiliares ───────────────────────────────────────────────────────

def _calcular_drawdown(evolucion: List[float]) -> float:
    """Máximo drawdown como porcentaje desde el pico más alto."""
    if len(evolucion) < 2:
        return 0.0
    pico = evolucion[0]
    max_dd = 0.0
    for v in evolucion:
        if v > pico:
            pico = v
        dd = (pico - v) / pico * 100 if pico > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)


def _resultado_real(gf: int, ga: int) -> str:
    """Convierte marcador a resultado 1X2."""
    if gf > ga:   return "local"
    elif ga > gf: return "visita"
    else:          return "empate"


# ── Backtest principal ────────────────────────────────────────────────────────

def ejecutar_backtest(
    df: pd.DataFrame,
    data_master: dict,
    league: str,
    bankroll_inicial: float = 1000.0,
    kelly_frac: float       = 0.25,
    min_ev: float           = 0.0,    # EV mínimo en % (ej. 5.0 = 5%)
    min_prob: float         = 40.0,   # Prob mínima en % (ej. 40.0 = 40%)
    min_edge: float         = 3.0,    # Edge mínimo en % (ej. 3.0 = 3%)
    stake_max_pct: float    = 0.10,   # Máximo 10% de banca por apuesta
    mercados: list          = None,   # ["1x2", "ou", "btts"] — None = todos
    linea_ou: float         = 2.5,
) -> Tuple[dict, List[dict], List[float]]:
    """
    Ejecuta backtesting sobre partidos históricos usando el modelo real.

    df columnas requeridas:
      - date      : fecha del partido
      - home      : nombre equipo local
      - away      : nombre equipo visitante
      - score     : resultado "GF-GA" (ej. "2-1")
      - m_l, m_e, m_v : momios 1X2 decimales
    
    Columnas opcionales:
      - m_over, m_under : momios Over/Under
      - m_btts_si, m_btts_no : momios BTTS

    Retorna:
      - metricas (dict)
      - historial (list de dicts, una entrada por apuesta)
      - evolucion (list de floats, bankroll tras cada apuesta)
    """
    if mercados is None:
        mercados = ["1x2", "ou", "btts"]

    bankroll = bankroll_inicial
    evolucion = [bankroll]
    historial = []
    errores = []

    apuestas_total = 0
    apuestas_ganad = 0

    for _, row in df.iterrows():
        # ── Validar datos mínimos ─────────────────────────────────────────────
        home  = str(row.get("home", "")).strip()
        away  = str(row.get("away", "")).strip()
        score = str(row.get("score", "")).strip()
        m_l   = float(row.get("m_l", 0) or 0)
        m_e   = float(row.get("m_e", 0) or 0)
        m_v   = float(row.get("m_v", 0) or 0)

        if not home or not away or not score or not m_l:
            continue
        if "-" not in score:
            continue

        # Resultado real
        try:
            gf, ga = map(int, score.split("-"))
            resultado_real = _resultado_real(gf, ga)
        except Exception:
            continue

        # ── Lambdas del modelo real ───────────────────────────────────────────
        try:
            prof_l = build_team_profile(home, data_master, league)
            prof_v = build_team_profile(away, data_master, league)
            lam_l, lam_v = calc_lambdas(prof_l, prof_v, league)
        except Exception as e:
            errores.append(f"{home} vs {away}: {e}")
            continue

        mkts = calc_all_markets(lam_l, lam_v)

        # ── Evaluar candidatos de apuesta ─────────────────────────────────────
        candidatos = []

        if "1x2" in mercados and m_l > 1 and m_e > 1 and m_v > 1:
            vf = remove_vig([m_l, m_e, m_v])
            for prob_m, momio, vf_imp, pick in [
                (mkts["p_l"], m_l, vf[0], "local"),
                (mkts["p_e"], m_e, vf[1], "empate"),
                (mkts["p_v"], m_v, vf[2], "visita"),
            ]:
                ev   = ev_pct(prob_m, momio)
                edge = (prob_m - vf_imp) * 100
                candidatos.append((ev, edge, prob_m * 100, momio, pick, "1X2"))

        m_over  = float(row.get("m_over",    0) or 0)
        m_under = float(row.get("m_under",   0) or 0)
        if "ou" in mercados and m_over > 1 and m_under > 1:
            vf_ou = remove_vig([m_over, m_under])
            key_over = f"over{str(linea_ou).replace('.','')}"
            key_under = key_over.replace("over","under")
            p_over  = mkts.get(key_over,  mkts.get("over25",  0))
            p_under = mkts.get(key_under, mkts.get("under25", 0))
            for prob_m, momio, vf_imp, pick in [
                (p_over,  m_over,  vf_ou[0], f"Over {linea_ou}"),
                (p_under, m_under, vf_ou[1], f"Under {linea_ou}"),
            ]:
                ev   = ev_pct(prob_m, momio)
                edge = (prob_m - vf_imp) * 100
                candidatos.append((ev, edge, prob_m * 100, momio, pick, "OU"))

        m_bts = float(row.get("m_btts_si", 0) or 0)
        m_btn = float(row.get("m_btts_no", 0) or 0)
        if "btts" in mercados and m_bts > 1 and m_btn > 1:
            vf_bt = remove_vig([m_bts, m_btn])
            for prob_m, momio, vf_imp, pick in [
                (mkts["btts"],    m_bts, vf_bt[0], "BTTS Sí"),
                (mkts["no_btts"], m_btn, vf_bt[1], "BTTS No"),
            ]:
                ev   = ev_pct(prob_m, momio)
                edge = (prob_m - vf_imp) * 100
                candidatos.append((ev, edge, prob_m * 100, momio, pick, "BTTS"))

        # ── Filtrar por criterios ─────────────────────────────────────────────
        validos = [
            c for c in candidatos
            if c[0] >= min_ev        # EV mínimo
            and c[1] >= min_edge     # Edge mínimo
            and c[2] >= min_prob     # Probabilidad mínima
        ]

        if not validos:
            continue

        # Elegir el de mayor EV
        ev_, edge_, prob_, momio_, pick_, mercado_ = max(validos, key=lambda x: x[0])

        # ── Kelly + stake ─────────────────────────────────────────────────────
        k = fractional_kelly(prob_ / 100, momio_, kelly_frac)
        stake_pct = min(k, stake_max_pct)
        monto = bankroll * stake_pct

        if monto <= 0:
            continue

        # ── Resultado ─────────────────────────────────────────────────────────
        ganado = (
            (pick_ == "local"   and resultado_real == "local")  or
            (pick_ == "empate"  and resultado_real == "empate") or
            (pick_ == "visita"  and resultado_real == "visita") or
            (pick_.startswith("Over")  and (gf + ga) > linea_ou) or
            (pick_.startswith("Under") and (gf + ga) < linea_ou) or
            (pick_ == "BTTS Sí" and gf > 0 and ga > 0)         or
            (pick_ == "BTTS No" and not (gf > 0 and ga > 0))
        )

        ganancia = monto * (momio_ - 1) if ganado else -monto
        bankroll += ganancia
        evolucion.append(round(bankroll, 2))

        apuestas_total += 1
        if ganado:
            apuestas_ganad += 1

        historial.append({
            "fecha":      str(row.get("date", "")),
            "partido":    f"{home} vs {away}",
            "score":      score,
            "mercado":    mercado_,
            "pick":       pick_,
            "momio":      round(momio_, 2),
            "prob_modelo": round(prob_, 1),
            "ev":         round(ev_, 1),
            "edge":       round(edge_, 1),
            "stake_pct":  round(stake_pct * 100, 1),
            "monto":      round(monto, 2),
            "resultado":  resultado_real,
            "ganado":     ganado,
            "ganancia":   round(ganancia, 2),
            "bankroll":   round(bankroll, 2),
            "lambda_l":   round(lam_l, 3),
            "lambda_v":   round(lam_v, 3),
        })

    # ── Métricas finales ──────────────────────────────────────────────────────
    roi = ((bankroll - bankroll_inicial) / bankroll_inicial) * 100 if bankroll_inicial > 0 else 0
    tasa = (apuestas_ganad / apuestas_total * 100) if apuestas_total > 0 else 0

    # Yield real (ganancia / total expuesto)
    total_exp = sum(abs(h["monto"]) for h in historial)
    yield_ = (bankroll - bankroll_inicial) / total_exp * 100 if total_exp > 0 else 0

    metricas = {
        "bankroll_inicial":  round(bankroll_inicial, 2),
        "bankroll_final":    round(bankroll, 2),
        "beneficio":         round(bankroll - bankroll_inicial, 2),
        "roi":               round(roi, 2),
        "yield":             round(yield_, 2),
        "total_apuestas":    apuestas_total,
        "ganadas":           apuestas_ganad,
        "perdidas":          apuestas_total - apuestas_ganad,
        "tasa_acierto":      round(tasa, 1),
        "total_expuesto":    round(total_exp, 2),
        "max_drawdown":      _calcular_drawdown(evolucion),
        "errores":           errores,
    }

    return metricas, historial, evolucion


def csv_to_df(csv_text: str) -> pd.DataFrame | None:
    """
    Convierte texto CSV a DataFrame con las columnas esperadas.
    El CSV mínimo necesita: date, home, away, score, m_l, m_e, m_v
    """
    import io
    try:
        df = pd.read_csv(io.StringIO(csv_text))
        df.columns = [c.strip().lower() for c in df.columns]
        # Normalizar nombres de columnas comunes
        renames = {
            "fecha": "date", "local": "home", "visitante": "away",
            "resultado": "score", "goles": "score",
            "cuota_local": "m_l", "cuota_empate": "m_e", "cuota_visita": "m_v",
            "over": "m_over", "under": "m_under",
            "btts_si": "m_btts_si", "btts_no": "m_btts_no",
        }
        df = df.rename(columns={k: v for k, v in renames.items() if k in df.columns})
        return df
    except Exception:
        return None
