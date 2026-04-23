"""
ui/components.py
Componentes HTML reutilizables para la UI.
Todas las funciones retornan strings HTML listos para st.markdown(..., unsafe_allow_html=True).
"""
from data.parser import safe_float


def fmt_money(v: float) -> str:
    return f"${v:,.2f}"


def prob_bar(label: str, prob: float, color: str,
             implied_vf: float = 0.0) -> str:
    """Barra de probabilidad con etiqueta e implícita vig-free opcional."""
    sub = f'<div class="prob-sub">Casa: {implied_vf:.1f}%</div>' if implied_vf > 0 else ""
    return f"""
    <div class="prob-wrap">
        <div class="prob-top">
            <span class="prob-name">{label}</span>
            <span class="prob-pct">{prob*100:.1f}%</span>
        </div>
        <div class="prob-bar-bg">
            <div class="prob-bar-fill" style="width:{prob*100:.1f}%;background:{color};"></div>
        </div>
        {sub}
    </div>"""


def market_pill(value: str, label: str, color: str = "#1c1917") -> str:
    return f"""
    <div class="mkt-pill">
        <div class="mkt-val" style="color:{color};">{value}</div>
        <div class="mkt-lbl">{label}</div>
    </div>"""


def markets_row(markets: dict) -> str:
    """Fila de pills con los mercados principales."""
    html = '<div class="mkt-grid">'
    html += market_pill(f"{markets['total_xg']:.2f}", "xG Part.")
    html += market_pill(f"{markets['over25']*100:.1f}%",  "Over 2.5",  "#16a34a")
    html += market_pill(f"{markets['under25']*100:.1f}%", "Under 2.5", "#dc2626")
    html += market_pill(f"{markets['over15']*100:.1f}%",  "Over 1.5",  "#0891b2")
    html += market_pill(f"{markets['over35']*100:.1f}%",  "Over 3.5",  "#d97706")
    html += market_pill(f"{markets['btts']*100:.1f}%",    "BTTS",      "#7c3aed")
    html += '</div>'
    return html


def dc_row(markets: dict) -> str:
    """Fila de Double Chance."""
    html = '<div class="mkt-grid">'
    html += market_pill(f"{markets['dc_1x']*100:.1f}%",  "DC 1X")
    html += market_pill(f"{markets['dc_x2']*100:.1f}%",  "DC X2")
    html += market_pill(f"{markets['dc_12']*100:.1f}%",  "DC 12")
    html += market_pill(f"{markets['hdp_neg05_l']*100:.1f}%", "HDP -0.5 L")
    html += market_pill(f"{markets['hdp_neg10_l']*100:.1f}%", "HDP -1 L")
    html += '</div>'
    return html


def exact_scores_row(markets: dict) -> str:
    """Grid de marcadores exactos más probables."""
    html = '<div class="scores-grid">'
    for score, pct in markets["exact"]:
        html += f"""
        <div class="score-pill">
            <div class="score-result">{score}</div>
            <div class="score-prob">{pct}%</div>
        </div>"""
    html += '</div>'
    return html


def pick_card(pick: dict) -> str:
    """Card de un pick individual con EV, edge, stake."""
    ev     = pick["ev"]
    cls    = "pos" if ev > 0 else ("neg" if ev < -3 else "neu")
    ev_cls = "ev-pos" if ev > 0 else "ev-neg"
    return f"""
    <div class="pick-c {cls}">
        <div class="pick-name">{pick['name']}</div>
        <div class="pick-ev {ev_cls}">{ev:+.1f}% EV</div>
        <div class="pick-detail">
            Modelo: <b>{pick['prob']*100:.1f}%</b>
            · Casa: {pick['implied']:.1f}%
            · Edge: <b>{pick['edge']:+.1f}%</b><br>
            Stake: <span class="pick-stake">{fmt_money(pick['stake'])}</span>
            (Kelly {pick['kelly']*100:.1f}%)
        </div>
    </div>"""


def picks_row(picks: list[dict]) -> str:
    html = '<div class="pick-grid">'
    for p in picks:
        html += pick_card(p)
    html += '</div>'
    return html


def stat_row(label: str, val_l: float, val_v: float,
             fmt: str = "{:.2f}", higher_good: bool = True) -> str:
    """Fila de comparación de estadística entre dos equipos."""
    f_l = fmt.format(val_l) if val_l != 0 else "—"
    f_v = fmt.format(val_v) if val_v != 0 else "—"
    cl_l = cl_v = ""
    if val_l > 0 and val_v > 0:
        ratio = val_l / val_v if val_v != 0 else 1
        if higher_good:
            cl_l = "sv-good" if ratio >= 1.0 else ("sv-bad" if ratio < 0.85 else "")
            cl_v = "sv-good" if ratio <= 1.0 else ("sv-bad" if ratio > 1.18 else "")
        else:
            cl_l = "sv-good" if ratio <= 1.0 else ("sv-bad" if ratio > 1.18 else "")
            cl_v = "sv-good" if ratio >= 1.0 else ("sv-bad" if ratio < 0.85 else "")
    return f"""
    <div class="stat-row">
        <span class="sl">{label}</span>
        <span style="display:flex;gap:20px;">
            <span class="sv {cl_l}">{f_l}</span>
            <span class="sv {cl_v}">{f_v}</span>
        </span>
    </div>"""


def team_header(prof: dict, align_right: bool = False) -> str:
    pos = f'<span class="team-pos">#{prof["position"]} · {prof["points"]} pts</span>' \
          if prof["position"] else ""
    wdl = f'<span class="team-wdl">{prof["wdl"]}</span>' if prof["wdl"] else ""
    cls = "team-hdr team-hdr-r" if align_right else "team-hdr"
    if align_right:
        return f'<div class="{cls}">{wdl}{pos}<span class="team-name">{prof["name"]}</span></div>'
    return f'<div class="{cls}"><span class="team-name">{prof["name"]}</span>{pos}{wdl}</div>'


def lam_info(lam_l: float, lam_v: float,
             label_l: str, label_v: str,
             blend_l: str, blend_v: str) -> str:
    return f"""
    <div class="lam-info">
        λ {label_l} = <b>{lam_l:.3f}</b> ({blend_l})
        &nbsp;·&nbsp;
        λ {label_v} = <b>{lam_v:.3f}</b> ({blend_v})
    </div>"""


def vig_info(or_pct: float, m_l: float, m_e: float, m_v: float,
             vf_l: float, vf_e: float, vf_v: float) -> str:
    return f"""
    <div class="vig-info">
        <span>Overround: <b>{or_pct:.1f}%</b></span>
        <span>Implícita s/vig → L:{vf_l:.1f}% · E:{vf_e:.1f}% · V:{vf_v:.1f}%</span>
    </div>"""


def jornada_row(ap: dict) -> str:
    st_cls = {"GANADA": "j-gan", "PERDIDA": "j-per"}.get(ap["estado"], "j-pen")
    return f"""
    <div class="jrow">
        <span class="j-match">{ap['partido']}</span>
        <span class="j-mkt">{ap['pick']}</span>
        <span class="j-momio">@{ap['momio']:.2f}</span>
        <span class="j-stake">{fmt_money(ap['stake'])}</span>
        <span class="{st_cls}">{ap['estado']}</span>
    </div>"""
