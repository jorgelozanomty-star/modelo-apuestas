import streamlit as st
import pandas as pd
import math
import io

st.set_page_config(
    page_title="Intelligence Pro",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

EQUIPOS_MAP = {
    "UANL": "Tigres", "Tigres UANL": "Tigres", "Club América": "América",
    "CA América": "América", "Guadalajara": "Chivas", "CD Guadalajara": "Chivas",
    "Cruz Azul": "Cruz Azul", "UNAM": "Pumas", "Pumas UNAM": "Pumas",
    "Monterrey": "Rayados", "CF Monterrey": "Rayados", "Toluca": "Toluca",
    "Pachuca": "Pachuca", "León": "León", "Santos": "Santos Laguna",
    "Santos Laguna": "Santos Laguna", "Atlas": "Atlas", "Necaxa": "Necaxa",
    "Querétaro": "Querétaro", "Mazatlán": "Mazatlán", "FC Juárez": "Juárez",
    "Tijuana": "Xolos", "Club Tijuana": "Xolos", "Puebla": "Puebla",
    "Atlético San Luis": "San Luis"
}

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── BASE ── */
html, body, [class*="css"] { font-family: 'Outfit', sans-serif !important; }

.stApp {
    background: #f4f3ef !important;
    color: #1c1917 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e7e5e0 !important;
}
section[data-testid="stSidebar"] * { color: #1c1917 !important; }
section[data-testid="stSidebar"] .stTextArea textarea {
    font-size: 0.72rem !important;
}

/* Main content */
.block-container { padding-top: 2rem !important; }

/* ── HEADER ── */
.ip-header {
    display: flex;
    align-items: baseline;
    gap: 14px;
    margin-bottom: 32px;
    padding-bottom: 20px;
    border-bottom: 1px solid #e7e5e0;
}
.ip-header-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1c1917;
    letter-spacing: -0.03em;
}
.ip-header-sub {
    font-size: 0.78rem;
    color: #a8a29e;
    font-family: 'DM Mono', monospace;
}
.ip-header-tag {
    margin-left: auto;
    font-size: 0.65rem;
    font-family: 'DM Mono', monospace;
    color: #a8a29e;
    background: #f0ede8;
    border: 1px solid #e7e5e0;
    padding: 3px 10px;
    border-radius: 20px;
}

/* ── SECTION LABELS ── */
.sec-label {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #a8a29e;
    font-family: 'DM Mono', monospace;
    margin: 24px 0 10px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #e7e5e0;
}

/* ── CARDS ── */
.card {
    background: #ffffff;
    border: 1px solid #e7e5e0;
    border-radius: 10px;
    padding: 16px 20px;
}
.card-sm {
    background: #ffffff;
    border: 1px solid #e7e5e0;
    border-radius: 8px;
    padding: 12px 16px;
}

/* ── STAT CHIP ── */
.stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid #f4f3ef;
    font-size: 0.82rem;
}
.stat-row:last-child { border-bottom: none; }
.stat-row .sl { color: #78716c; font-weight: 400; }
.stat-row .sv { font-family: 'DM Mono', monospace; font-weight: 500; color: #1c1917; font-size: 0.85rem; }
.sv-good { color: #16a34a !important; }
.sv-bad  { color: #dc2626 !important; }
.sv-mid  { color: #d97706 !important; }

/* ── PROB BARS ── */
.prob-wrap { margin: 6px 0; }
.prob-top { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 0.78rem; }
.prob-name { color: #44403c; font-weight: 500; }
.prob-pct  { font-family: 'DM Mono', monospace; font-weight: 600; color: #1c1917; }
.prob-bar-bg { background: #f0ede8; border-radius: 3px; height: 5px; }
.prob-bar-fill { height: 100%; border-radius: 3px; }

/* ── OU PILLS ── */
.ou-grid { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0; }
.ou-pill {
    flex: 1;
    min-width: 80px;
    background: #ffffff;
    border: 1px solid #e7e5e0;
    border-radius: 8px;
    padding: 10px 8px;
    text-align: center;
}
.ou-val { font-size: 1.2rem; font-weight: 700; font-family: 'DM Mono', monospace; color: #1c1917; }
.ou-lbl { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.1em; color: #a8a29e; margin-top: 2px; font-family: 'DM Mono', monospace; }

/* ── PICK CARDS ── */
.pick-grid { display: flex; gap: 10px; margin: 8px 0; }
.pick-c {
    flex: 1;
    border-radius: 10px;
    padding: 14px 16px;
    border: 1px solid;
    position: relative;
}
.pick-c.pos { background: #f0fdf4; border-color: #86efac; }
.pick-c.neg { background: #fef2f2; border-color: #fca5a5; }
.pick-c.neu { background: #fafaf9; border-color: #e7e5e0; }
.pick-name { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.1em; color: #a8a29e; font-family: 'DM Mono', monospace; margin-bottom: 6px; }
.pick-ev   { font-size: 1.3rem; font-weight: 700; font-family: 'DM Mono', monospace; }
.ev-pos { color: #16a34a; }
.ev-neg { color: #dc2626; }
.pick-detail { font-size: 0.72rem; color: #78716c; margin-top: 6px; }
.pick-stake  { font-family: 'DM Mono', monospace; font-weight: 600; color: #1c1917; }

/* ── BANCA ── */
.banca-box {
    background: #ffffff;
    border: 1px solid #e7e5e0;
    border-left: 3px solid #1c1917;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 16px;
}
.banca-lbl { font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.12em; color: #a8a29e; font-family: 'DM Mono', monospace; }
.banca-val { font-size: 1.7rem; font-weight: 700; font-family: 'DM Mono', monospace; color: #1c1917; margin: 4px 0 2px 0; }
.banca-roi { font-size: 0.72rem; font-family: 'DM Mono', monospace; }
.roi-pos { color: #16a34a; }
.roi-neg { color: #dc2626; }
.roi-neu { color: #a8a29e; }

/* ── SIDEBAR STATUS ── */
.tbl-loaded { background: #f0fdf4; border: 1px solid #86efac; color: #15803d; font-size: 0.68rem; padding: 3px 10px; border-radius: 4px; font-family: 'DM Mono', monospace; text-align:center; margin-top:4px; }
.tbl-empty  { color: #c4b9b2; font-size: 0.68rem; font-family: 'DM Mono', monospace; margin-top:4px; text-align:center; }

/* ── JORNADA TABLE ── */
.jrow {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #ffffff;
    border: 1px solid #e7e5e0;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 0.82rem;
}
.j-match  { flex: 2; font-weight: 600; color: #1c1917; }
.j-pick   { flex: 1; font-size: 0.72rem; color: #78716c; }
.j-momio  { font-family: 'DM Mono', monospace; color: #44403c; }
.j-stake  { font-family: 'DM Mono', monospace; font-weight: 600; color: #d97706; }
.j-status-pen { color: #d97706; font-weight: 600; }
.j-status-gan { color: #16a34a; font-weight: 700; }
.j-status-per { color: #dc2626; font-weight: 700; }

/* ── TEAM BADGE ── */
.team-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 0 14px 0;
}
.team-name  { font-size: 1rem; font-weight: 700; color: #1c1917; }
.team-pos   { font-size: 0.65rem; font-family: 'DM Mono', monospace; background: #f0ede8; border: 1px solid #e7e5e0; padding: 2px 8px; border-radius: 20px; color: #78716c; }
.team-wdl   { font-size: 0.65rem; font-family: 'DM Mono', monospace; color: #a8a29e; }

/* ── INPUTS override ── */
div[data-testid="stNumberInput"] input,
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] > div > div {
    background: #fafaf9 !important;
    border-color: #e7e5e0 !important;
    color: #1c1917 !important;
    border-radius: 7px !important;
    font-family: 'Outfit', sans-serif !important;
}
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stTextInput"] input:focus {
    border-color: #a78bfa !important;
    box-shadow: 0 0 0 2px rgba(167,139,250,0.15) !important;
}

/* ── BUTTONS ── */
.stButton button {
    background: #1c1917 !important;
    color: #fafaf9 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-family: 'Outfit', sans-serif !important;
    letter-spacing: 0.01em !important;
    transition: background 0.15s !important;
}
.stButton button:hover { background: #292524 !important; }

/* ── METRICS ── */
div[data-testid="metric-container"] {
    background: #ffffff !important;
    border: 1px solid #e7e5e0 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}
div[data-testid="metric-container"] label { color: #78716c !important; font-size: 0.75rem !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #1c1917 !important;
    font-family: 'DM Mono', monospace !important;
}

/* ── SLIDER ── */
div[data-testid="stSlider"] .rc-slider-track { background: #7c3aed !important; }
div[data-testid="stSlider"] .rc-slider-handle { background: #7c3aed !important; border-color: #7c3aed !important; }

/* ── EXPANDER ── */
details summary { font-size: 0.82rem !important; font-weight: 500 !important; color: #44403c !important; }
details { border: 1px solid #e7e5e0 !important; border-radius: 8px !important; background: #fafaf9 !important; }

/* ── SELECTBOX ── */
div[data-testid="stSelectbox"] { color: #1c1917 !important; }
div[data-baseweb="select"] { background: #fafaf9 !important; }

/* ── RADIO ── */
div[data-testid="stRadio"] label { color: #44403c !important; font-size: 0.85rem !important; }

hr { border-color: #e7e5e0 !important; }

/* ── DATAFRAME ── */
div[data-testid="stDataFrame"] { border: 1px solid #e7e5e0 !important; border-radius: 8px !important; overflow: hidden !important; }
</style>
""", unsafe_allow_html=True)

# ─── ESTADO ───────────────────────────────────────────────────────────────────
for key, val in [
    ('banca_actual',       1000.0),
    ('banca_inicial',      1000.0),
    ('jornada_pendientes', []),
    ('historial',          []),
    ('data_master',        {}),
]:
    if key not in st.session_state:
        st.session_state[key] = val

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def safe_float(v, default=0.0):
    try: return float(v)
    except: return default

def fmt_money(v): return f"${v:,.2f}"

def roi():
    if st.session_state.banca_inicial == 0: return 0.0
    return ((st.session_state.banca_actual - st.session_state.banca_inicial) / st.session_state.banca_inicial) * 100

def ev_pct(prob, momio):
    return (prob * momio - 1) * 100

def get_kelly(prob, momio, fraction):
    if momio <= 1: return 0.0
    edge = ((momio - 1) * prob) - (1 - prob)
    return max(0.0, (edge / (momio - 1)) * fraction)

def process_fbref_paste(text):
    if not text or len(text) < 10: return None
    try:
        clean = text.replace("Club Crest", "").strip()
        df = pd.read_csv(io.StringIO(clean), sep='\t')
        if len(df.columns) < 2:
            df = pd.read_csv(io.StringIO(clean), sep=None, engine='python')
        df.columns = [c.strip() for c in df.columns]
        if 'Squad' in df.columns:
            df['Squad'] = df['Squad'].str.replace("Club Crest", "", regex=False).str.strip()
            df['Squad'] = df['Squad'].replace(EQUIPOS_MAP)
        # Remove total/average rows
        if 'Squad' in df.columns:
            df = df[~df['Squad'].str.lower().isin(['squad', 'total', 'average', 'avg', ''])]
        return df if len(df) > 0 else None
    except: return None

def get_team_row(table_name, squad_name):
    dm = st.session_state.data_master
    if table_name not in dm or 'Squad' not in dm[table_name].columns:
        return None
    df = dm[table_name]
    exact = df[df['Squad'] == squad_name]
    if not exact.empty: return exact.iloc[0]
    partial = df[df['Squad'].str.contains(squad_name, na=False, case=False)]
    return partial.iloc[0] if not partial.empty else None

def per_game(raw_val, mp, threshold=4.0):
    """Divide by MP only if raw_val looks like a season total (> threshold)."""
    v = safe_float(raw_val)
    m = max(safe_float(mp, 1), 1)
    return v / m if v > threshold else v

def build_team_profile(squad_name):
    """Construye perfil completo del equipo usando las 9 tablas."""
    p = {
        'name': squad_name,
        # Ataque
        'gf_pg': 1.5,  'xg_pg': 0.0, 'npxg_pg': 0.0,
        'sh_pg': 0.0,   'sot_pg': 0.0, 'g_sh': 0.0, 'sot_pct': 0.0,
        # Defensa
        'ga_pg': 1.1,  'xga_pg': 0.0,
        'opp_sh_pg': 0.0, 'opp_sot_pg': 0.0, 'opp_sot_pct': 0.0,
        # Disciplina
        'fouls_pg': 0.0, 'yellows_pg': 0.0, 'reds_pg': 0.0,
        'opp_fouls_pg': 0.0,
        # Aéreos
        'aerials_won_pct': 0.0,
        # Tabla
        'position': None, 'points': None, 'wdl': '',
        # Derivados
        'lambda_att': 1.5, 'lambda_def': 1.1,
        'mp': 1,
    }

    # ── 1. Tabla General ───────────────────────────────────────────────────────
    row = get_team_row("Tabla General", squad_name)
    if row is not None:
        mp_g = max(safe_float(row.get('MP', row.get('PJ', 1))), 1)
        p['mp'] = int(mp_g)
        rk = row.get('Rk', row.get('Pos', None))
        if rk is not None: p['position'] = int(safe_float(rk))
        pts = row.get('Pts', None)
        if pts is not None: p['points'] = int(safe_float(pts))
        w = int(safe_float(row.get('W', row.get('G', 0))))
        d = int(safe_float(row.get('D', row.get('E', 0))))
        l = int(safe_float(row.get('L', row.get('P', 0))))
        p['wdl'] = f"{w}G-{d}E-{l}P"

    # ── 2. Standard Squad ─────────────────────────────────────────────────────
    row = get_team_row("Standard Squad", squad_name)
    if row is not None:
        mp_s = max(safe_float(row.get('MP', p['mp'])), 1)
        p['mp'] = int(mp_s)
        p['gf_pg'] = per_game(row.get('GF', row.get('Gls', p['gf_pg'] * mp_s)), mp_s)
        xg = safe_float(row.get('xG', 0))
        p['xg_pg'] = xg / mp_s if xg > 4 else xg

    # ── 3. Standard Opp ───────────────────────────────────────────────────────
    row = get_team_row("Standard Opp", squad_name)
    if row is not None:
        mp_o = max(safe_float(row.get('MP', p['mp'])), 1)
        p['ga_pg'] = per_game(row.get('GA', row.get('Gls', p['ga_pg'] * mp_o)), mp_o)
        xga = safe_float(row.get('xGA', row.get('xG', 0)))
        p['xga_pg'] = xga / mp_o if xga > 4 else xga

    # ── 4. Shooting Squad ─────────────────────────────────────────────────────
    row = get_team_row("Shooting Squad", squad_name)
    if row is not None:
        mp90 = max(safe_float(row.get('90s', p['mp'])), 1)
        sh   = safe_float(row.get('Sh', 0))
        sot  = safe_float(row.get('SoT', 0))
        npxg = safe_float(row.get('npxG', 0))
        g_sh = safe_float(row.get('G/Sh', 0))
        p['sh_pg']   = sh  / mp90 if sh  > 4 else sh
        p['sot_pg']  = sot / mp90 if sot > 4 else sot
        p['npxg_pg'] = npxg / mp90 if npxg > 4 else npxg
        p['g_sh']    = g_sh
        p['sot_pct'] = (sot / sh * 100) if sh > 0 else safe_float(row.get('SoT%', 0))

    # ── 5. Shooting Opp ───────────────────────────────────────────────────────
    row = get_team_row("Shooting Opp", squad_name)
    if row is not None:
        mp90o = max(safe_float(row.get('90s', p['mp'])), 1)
        opp_sh  = safe_float(row.get('Sh', 0))
        opp_sot = safe_float(row.get('SoT', 0))
        p['opp_sh_pg']  = opp_sh  / mp90o if opp_sh  > 4 else opp_sh
        p['opp_sot_pg'] = opp_sot / mp90o if opp_sot > 4 else opp_sot
        p['opp_sot_pct'] = (opp_sot / opp_sh * 100) if opp_sh > 0 else safe_float(row.get('SoT%', 0))

    # ── 6. Misc Squad ─────────────────────────────────────────────────────────
    row = get_team_row("Misc Squad", squad_name)
    if row is not None:
        mp90m = max(safe_float(row.get('90s', p['mp'])), 1)
        fls  = safe_float(row.get('Fls', 0))
        crdy = safe_float(row.get('CrdY', 0))
        crdr = safe_float(row.get('CrdR', 0))
        aer  = safe_float(row.get('Won%', row.get('Aerial Won%', 0)))
        p['fouls_pg']    = fls  / mp90m if fls  > 5 else fls
        p['yellows_pg']  = crdy / mp90m if crdy > 3 else crdy
        p['reds_pg']     = crdr / mp90m if crdr > 1 else crdr
        p['aerials_won_pct'] = aer

    # ── 7. Misc Opp ───────────────────────────────────────────────────────────
    row = get_team_row("Misc Opp", squad_name)
    if row is not None:
        mp90mo = max(safe_float(row.get('90s', p['mp'])), 1)
        opp_fls = safe_float(row.get('Fls', 0))
        p['opp_fouls_pg'] = opp_fls / mp90mo if opp_fls > 5 else opp_fls

    # ── PlayingTime Squad/Opp – informacional, no afecta modelo directamente ──
    # (podrías usar % de minutos del top-scorer para ajustar si está lesionado)

    # ── Lambdas para modelo Poisson ───────────────────────────────────────────
    # Blend: 50% goles reales, 30% xG, 20% npxG (cuando están disponibles)
    att_sources = [x for x in [p['gf_pg'], p['xg_pg'], p['npxg_pg']] if x > 0.01]
    weights = [0.5, 0.35, 0.15][:len(att_sources)]
    total_w = sum(weights[:len(att_sources)])
    p['lambda_att'] = sum(a * w for a, w in zip(att_sources, weights)) / total_w if att_sources else p['gf_pg']

    def_sources = [x for x in [p['ga_pg'], p['xga_pg']] if x > 0.01]
    p['lambda_def'] = sum(def_sources) / len(def_sources) if def_sources else p['ga_pg']

    return p

def calc_poisson(lam_l, lam_v):
    p_l = p_v = p_e = 0.0
    matrix = {}
    for i in range(9):
        for j in range(9):
            p = ((math.exp(-lam_l) * lam_l**i / math.factorial(i)) *
                 (math.exp(-lam_v) * lam_v**j / math.factorial(j)))
            matrix[(i, j)] = p
            if i > j:   p_l += p
            elif j > i: p_v += p
            else:        p_e += p
    return p_l, p_v, p_e, matrix

def color_stat(val, good_threshold, bad_threshold, higher_is_better=True):
    """Retorna clase CSS según si el valor es bueno/malo."""
    if val == 0: return ""
    if higher_is_better:
        if val >= good_threshold: return "sv-good"
        if val <= bad_threshold:  return "sv-bad"
    else:
        if val <= good_threshold: return "sv-good"
        if val >= bad_threshold:  return "sv-bad"
    return ""

def stat_row_html(label, val_l, val_v, fmt="{:.2f}", higher_good_l=True):
    """Genera fila HTML de comparación de stats."""
    try:
        f_l = fmt.format(val_l) if val_l != 0 else "—"
        f_v = fmt.format(val_v) if val_v != 0 else "—"
        # Simple color: quién tiene mejor valor
        if val_l > 0 and val_v > 0:
            if higher_good_l:
                cl_l = "sv-good" if val_l >= val_v else ("sv-bad" if val_l < val_v * 0.85 else "")
                cl_v = "sv-good" if val_v >= val_l else ("sv-bad" if val_v < val_l * 0.85 else "")
            else:
                cl_l = "sv-good" if val_l <= val_v else ("sv-bad" if val_l > val_v * 1.15 else "")
                cl_v = "sv-good" if val_v <= val_l else ("sv-bad" if val_v > val_l * 1.15 else "")
        else:
            cl_l = cl_v = ""
        return f"""<div class="stat-row">
            <span class="sl">{label}</span>
            <span style="display:flex;gap:20px;">
                <span class="sv {cl_l}">{f_l}</span>
                <span class="sv {cl_v}">{f_v}</span>
            </span>
        </div>"""
    except:
        return ""

# ─── SIDEBAR: DATA HUB ────────────────────────────────────────────────────────
TABLAS = [
    ("Tabla General",    "🏆"),
    ("Standard Squad",   "⚽"),
    ("Standard Opp",     "🛡️"),
    ("Shooting Squad",   "🎯"),
    ("Shooting Opp",     "🎯"),
    ("PlayingTime Squad","⏱️"),
    ("PlayingTime Opp",  "⏱️"),
    ("Misc Squad",       "📋"),
    ("Misc Opp",         "📋"),
]

with st.sidebar:
    st.markdown("### ◈ Intelligence Pro")
    st.markdown('<p style="font-size:0.7rem;color:#a8a29e;font-family:\'DM Mono\',monospace;margin-top:-6px;">Data Hub · Bankroll</p>', unsafe_allow_html=True)
    st.markdown("---")

    # — Bankroll —
    r = roi()
    roi_class = "roi-pos" if r > 0 else ("roi-neg" if r < 0 else "roi-neu")
    st.markdown(f"""
    <div class="banca-box">
        <div class="banca-lbl">Banca Actual</div>
        <div class="banca-val">{fmt_money(st.session_state.banca_actual)}</div>
        <div class="banca-roi {roi_class}">ROI: {r:+.2f}%</div>
    </div>""", unsafe_allow_html=True)

    col_k, col_btn = st.columns([3, 1])
    with col_k:
        f_kelly = st.slider("Fracción Kelly", 0.05, 1.0, 0.25, step=0.05, label_visibility="collapsed")
        st.caption(f"Kelly ×{f_kelly:.2f}")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️", help="Limpiar jornada"):
            st.session_state.jornada_pendientes = []
            st.rerun()

    banca_edit = st.number_input("Ajustar banca", value=float(st.session_state.banca_actual),
                                  format="%.2f", label_visibility="collapsed")
    if abs(banca_edit - st.session_state.banca_actual) > 0.01:
        st.session_state.banca_actual = banca_edit
        st.rerun()

    st.markdown("---")
    st.markdown('<p style="font-size:0.7rem;font-weight:600;color:#44403c;text-transform:uppercase;letter-spacing:0.1em;">Tablas FBRef</p>', unsafe_allow_html=True)

    tables_loaded = 0
    for nombre, icon in TABLAS:
        with st.expander(f"{icon} {nombre}"):
            raw = st.text_area("", key=f"in_{nombre}", height=70, label_visibility="collapsed",
                               placeholder="Pega aquí los datos copiados de FBRef…")
            df_parsed = process_fbref_paste(raw)
            if df_parsed is not None:
                st.session_state.data_master[nombre] = df_parsed
                st.markdown(f'<div class="tbl-loaded">✓ {len(df_parsed)} equipos</div>', unsafe_allow_html=True)
                tables_loaded += 1
            else:
                if nombre in st.session_state.data_master:
                    st.markdown(f'<div class="tbl-loaded">✓ {len(st.session_state.data_master[nombre])} equipos (cargada)</div>', unsafe_allow_html=True)
                    tables_loaded += 1
                else:
                    st.markdown('<div class="tbl-empty">sin datos</div>', unsafe_allow_html=True)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
tables_loaded_total = len(st.session_state.data_master)
st.markdown(f"""
<div class="ip-header">
    <span class="ip-header-title">◈ Intelligence Pro</span>
    <span class="ip-header-sub">Poisson · Kelly · xG Blend</span>
    <span class="ip-header-tag">{tables_loaded_total}/9 tablas cargadas</span>
</div>""", unsafe_allow_html=True)

# ─── SELECTOR DE EQUIPOS ──────────────────────────────────────────────────────
equipos_lista = ["— seleccionar —"]
if st.session_state.data_master:
    first_df = next(iter(st.session_state.data_master.values()))
    if 'Squad' in first_df.columns:
        equipos_lista += sorted(first_df['Squad'].dropna().unique().tolist())

st.markdown('<div class="sec-label">01 · Encuentro</div>', unsafe_allow_html=True)
col_l, col_vs, col_v = st.columns([5, 1, 5])

with col_l:
    local_sel = st.selectbox("Local", equipos_lista, key="local_sel", label_visibility="collapsed")
with col_vs:
    st.markdown("<br><div style='text-align:center;font-size:0.75rem;color:#a8a29e;font-family:DM Mono,monospace;padding-top:8px;'>vs</div>", unsafe_allow_html=True)
with col_v:
    visita_sel = st.selectbox("Visitante", equipos_lista, key="visita_sel", label_visibility="collapsed")

# ─── PERFILES ─────────────────────────────────────────────────────────────────
prof_l = build_team_profile(local_sel)  if local_sel  != "— seleccionar —" else None
prof_v = build_team_profile(visita_sel) if visita_sel != "— seleccionar —" else None

# ─── COMPARATIVA ──────────────────────────────────────────────────────────────
if prof_l and prof_v:
    st.markdown('<div class="sec-label">02 · Comparativa de Estadísticas</div>', unsafe_allow_html=True)

    # Headers de equipos
    col_hl, col_hv = st.columns(2)
    with col_hl:
        pos_txt = f"#{prof_l['position']}" if prof_l['position'] else ""
        pts_txt = f"{prof_l['points']} pts" if prof_l['points'] else ""
        st.markdown(f"""<div class="team-header">
            <span class="team-name">{prof_l['name']}</span>
            {f'<span class="team-pos">{pos_txt} · {pts_txt}</span>' if pos_txt else ''}
            {f'<span class="team-wdl">{prof_l["wdl"]}</span>' if prof_l["wdl"] else ''}
        </div>""", unsafe_allow_html=True)
    with col_hv:
        pos_txt = f"#{prof_v['position']}" if prof_v['position'] else ""
        pts_txt = f"{prof_v['points']} pts" if prof_v['points'] else ""
        st.markdown(f"""<div class="team-header" style="justify-content:flex-end;">
            {f'<span class="team-wdl">{prof_v["wdl"]}</span>' if prof_v["wdl"] else ''}
            {f'<span class="team-pos">{pos_txt} · {pts_txt}</span>' if pos_txt else ''}
            <span class="team-name">{prof_v['name']}</span>
        </div>""", unsafe_allow_html=True)

    cmp_col1, cmp_col2 = st.columns(2)

    with cmp_col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        atk = ""
        atk += stat_row_html("Goles / partido",     prof_l['gf_pg'],     prof_v['gf_pg'])
        atk += stat_row_html("xG / partido",         prof_l['xg_pg'],     prof_v['xg_pg'])
        atk += stat_row_html("npxG / partido",       prof_l['npxg_pg'],   prof_v['npxg_pg'])
        atk += stat_row_html("Tiros / partido",      prof_l['sh_pg'],     prof_v['sh_pg'])
        atk += stat_row_html("Tiros a puerta / p",   prof_l['sot_pg'],    prof_v['sot_pg'])
        atk += stat_row_html("SoT%",                 prof_l['sot_pct'],   prof_v['sot_pct'], fmt="{:.1f}%")
        atk += stat_row_html("Eficiencia G/Sh",      prof_l['g_sh'],      prof_v['g_sh'],    fmt="{:.3f}")
        if atk.strip():
            st.markdown(f'<p style="font-size:0.65rem;font-weight:600;color:#a8a29e;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">⚽ Ataque</p>{atk}', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with cmp_col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        defn = ""
        defn += stat_row_html("Goles recibidos / p",    prof_l['ga_pg'],      prof_v['ga_pg'],      higher_good_l=False)
        defn += stat_row_html("xGA / partido",           prof_l['xga_pg'],     prof_v['xga_pg'],     higher_good_l=False)
        defn += stat_row_html("Tiros rivales / p",       prof_l['opp_sh_pg'],  prof_v['opp_sh_pg'],  higher_good_l=False)
        defn += stat_row_html("SoT rivales / p",         prof_l['opp_sot_pg'], prof_v['opp_sot_pg'], higher_good_l=False)
        defn += stat_row_html("Faltas cometidas / p",    prof_l['fouls_pg'],   prof_v['fouls_pg'],   higher_good_l=False)
        defn += stat_row_html("Tarjetas amarillas / p",  prof_l['yellows_pg'], prof_v['yellows_pg'], higher_good_l=False)
        defn += stat_row_html("% Duelos aéreos ganados", prof_l['aerials_won_pct'], prof_v['aerials_won_pct'], fmt="{:.1f}%")
        if defn.strip():
            st.markdown(f'<p style="font-size:0.65rem;font-weight:600;color:#a8a29e;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">🛡️ Defensa · Disciplina</p>{defn}', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ─── AJUSTE MANUAL ────────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">03 · Parámetros del Modelo</div>', unsafe_allow_html=True)

default_gf_l = prof_l['gf_pg']   if prof_l else 1.5
default_gc_l = prof_l['ga_pg']   if prof_l else 1.1
default_gf_v = prof_v['gf_pg']   if prof_v else 1.0
default_gc_v = prof_v['ga_pg']   if prof_v else 1.2

# Si tenemos lambdas calculados, usarlos como default
if prof_l and prof_v:
    lam_att_l = prof_l['lambda_att']
    lam_def_l = prof_l['lambda_def']
    lam_att_v = prof_v['lambda_att']
    lam_def_v = prof_v['lambda_def']
    default_gf_l = lam_att_l
    default_gc_l = lam_def_l
    default_gf_v = lam_att_v
    default_gc_v = lam_def_v

mp1, mp2, mp3, mp4 = st.columns(4)
with mp1:
    lname = local_sel if local_sel != "— seleccionar —" else "Local"
    g_l_f = st.number_input(f"Atq {lname[:10]}", value=round(float(default_gf_l), 2), format="%.2f", min_value=0.1, max_value=5.0)
with mp2:
    g_l_c = st.number_input(f"Def {lname[:10]}", value=round(float(default_gc_l), 2), format="%.2f", min_value=0.1, max_value=5.0)
with mp3:
    vname = visita_sel if visita_sel != "— seleccionar —" else "Visita"
    g_v_f = st.number_input(f"Atq {vname[:10]}", value=round(float(default_gf_v), 2), format="%.2f", min_value=0.1, max_value=5.0)
with mp4:
    g_v_c = st.number_input(f"Def {vname[:10]}", value=round(float(default_gc_v), 2), format="%.2f", min_value=0.1, max_value=5.0)

# Lambdas
lam_l = max(0.1, (g_l_f + g_v_c) / 2)
lam_v = max(0.1, (g_v_f + g_l_c) / 2)

if prof_l and prof_v:
    st.caption(
        f"λ Local = {lam_l:.3f}  ·  λ Visita = {lam_v:.3f}"
        + (f"  ·  xG blend: {prof_l['xg_pg']:.2f} / {prof_v['xg_pg']:.2f}" if prof_l['xg_pg'] > 0 else "  ·  sin xG (carga Shooting Squad)")
    )

# ─── POISSON ──────────────────────────────────────────────────────────────────
p_l, p_v, p_e, matrix = calc_poisson(lam_l, lam_v)
total_goles = lam_l + lam_v
over25  = sum(v for (i,j), v in matrix.items() if i+j > 2)
under25 = 1 - over25
btts    = sum(v for (i,j), v in matrix.items() if i > 0 and j > 0)
over15  = sum(v for (i,j), v in matrix.items() if i+j > 1)

st.markdown('<div class="sec-label">04 · Probabilidades</div>', unsafe_allow_html=True)

# Barras de probabilidad
pc1, pc2 = st.columns([3, 2])
with pc1:
    lname_short = local_sel[:15] if local_sel != "— seleccionar —" else "Local"
    vname_short = visita_sel[:15] if visita_sel != "— seleccionar —" else "Visita"
    for label, prob, color in [
        (f"🏠 {lname_short}", p_l, "#4f46e5"),
        ("🤝 Empate",          p_e, "#78716c"),
        (f"✈️ {vname_short}", p_v, "#f59e0b"),
    ]:
        st.markdown(f"""
        <div class="prob-wrap">
            <div class="prob-top">
                <span class="prob-name">{label}</span>
                <span class="prob-pct">{prob*100:.1f}%</span>
            </div>
            <div class="prob-bar-bg">
                <div class="prob-bar-fill" style="width:{prob*100:.1f}%;background:{color};"></div>
            </div>
        </div>""", unsafe_allow_html=True)

with pc2:
    st.markdown(f"""
    <div class="ou-grid">
        <div class="ou-pill"><div class="ou-val">{total_goles:.2f}</div><div class="ou-lbl">xG Part.</div></div>
        <div class="ou-pill"><div class="ou-val" style="color:#16a34a;">{over25*100:.1f}%</div><div class="ou-lbl">Over 2.5</div></div>
        <div class="ou-pill"><div class="ou-val" style="color:#dc2626;">{under25*100:.1f}%</div><div class="ou-lbl">Under 2.5</div></div>
        <div class="ou-pill"><div class="ou-val" style="color:#7c3aed;">{btts*100:.1f}%</div><div class="ou-lbl">BTTS</div></div>
        <div class="ou-pill"><div class="ou-val" style="color:#0891b2;">{over15*100:.1f}%</div><div class="ou-lbl">Over 1.5</div></div>
    </div>""", unsafe_allow_html=True)

# ─── MOMIOS + PICKS ───────────────────────────────────────────────────────────
st.markdown('<div class="sec-label">05 · Momios y Valor Esperado</div>', unsafe_allow_html=True)

mc1, mc2, mc3 = st.columns(3)
with mc1: m_l = st.number_input("Local",  value=2.0, format="%.2f", min_value=1.01)
with mc2: m_e = st.number_input("Empate", value=3.0, format="%.2f", min_value=1.01)
with mc3: m_v = st.number_input("Visita", value=3.0, format="%.2f", min_value=1.01)

picks_data = [
    (lname_short, p_l, m_l),
    ("Empate",    p_e, m_e),
    (vname_short, p_v, m_v),
]

picks_html = '<div class="pick-grid">'
for pname, prob, momio in picks_data:
    ev   = ev_pct(prob, momio)
    k    = get_kelly(prob, momio, f_kelly)
    stk  = st.session_state.banca_actual * k
    cls  = "pos" if ev > 0 else ("neg" if ev < -3 else "neu")
    ev_cls = "ev-pos" if ev > 0 else "ev-neg"
    implied = (1 / momio) * 100
    edge = prob*100 - implied
    picks_html += f"""
    <div class="pick-c {cls}">
        <div class="pick-name">{pname}</div>
        <div class="pick-ev {ev_cls}">{ev:+.1f}% EV</div>
        <div class="pick-detail">
            Prob. modelo: <b>{prob*100:.1f}%</b> · Implícita: {implied:.1f}% · Edge: {edge:+.1f}%<br>
            Stake: <span class="pick-stake">{fmt_money(stk)}</span>
            (Kelly {k*100:.1f}% de banca)
        </div>
    </div>"""
picks_html += '</div>'
st.markdown(picks_html, unsafe_allow_html=True)

# ─── BOTÓN AGREGAR ────────────────────────────────────────────────────────────
if local_sel != "— seleccionar —" and visita_sel != "— seleccionar —":
    ba1, ba2, ba3 = st.columns([2, 1, 3])
    with ba1:
        pick_opciones = [f"{n} (EV: {ev_pct(p,m):+.1f}%)" for n, p, m in picks_data]
        pick_sel_idx = st.selectbox("Pick a agregar", range(3), format_func=lambda i: pick_opciones[i])
    with ba2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("＋ Agregar a jornada"):
            pname, prob, momio = picks_data[pick_sel_idx]
            stk = round(st.session_state.banca_actual * get_kelly(prob, momio, f_kelly), 2)
            st.session_state.jornada_pendientes.append({
                'partido': f"{local_sel} vs {visita_sel}",
                'pick': pname, 'momio': momio, 'stake': stk, 'estado': 'Pendiente'
            })
            st.rerun()

# ─── GESTIÓN DE JORNADA ───────────────────────────────────────────────────────
if st.session_state.jornada_pendientes:
    st.markdown('<div class="sec-label">06 · Jornada Activa</div>', unsafe_allow_html=True)
    total_exp = sum(a['stake'] for a in st.session_state.jornada_pendientes)
    st.caption(f"{len(st.session_state.jornada_pendientes)} apuesta(s) · Exposición total: {fmt_money(total_exp)}")

    for ap in st.session_state.jornada_pendientes:
        sc = "j-status-pen"
        st.markdown(f"""
        <div class="jrow">
            <span class="j-match">{ap['partido']}</span>
            <span class="j-pick">{ap['pick']}</span>
            <span class="j-momio">@{ap['momio']:.2f}</span>
            <span class="j-stake">{fmt_money(ap['stake'])}</span>
            <span class="{sc}">{ap['estado']}</span>
        </div>""", unsafe_allow_html=True)

    with st.expander("💰 Registrar resultado"):
        idx = st.selectbox("Partido", range(len(st.session_state.jornada_pendientes)),
                           format_func=lambda i: st.session_state.jornada_pendientes[i]['partido'])
        res = st.radio("Resultado", ["GANADA", "PERDIDA"], horizontal=True)
        if st.button("✅ Confirmar resultado"):
            ap = st.session_state.jornada_pendientes[idx]
            ganancia = (ap['stake'] * (ap['momio'] - 1)) if res == "GANADA" else -ap['stake']
            st.session_state.banca_actual += ganancia
            st.session_state.historial.append({**ap, 'estado': res, 'resultado': ganancia})
            st.session_state.jornada_pendientes.pop(idx)
            st.rerun()

# ─── HISTORIAL ────────────────────────────────────────────────────────────────
if st.session_state.historial:
    st.markdown('<div class="sec-label">07 · Historial</div>', unsafe_allow_html=True)
    df_h = pd.DataFrame(st.session_state.historial)
    # Colorear estado
    ganadas = (df_h['estado'] == 'GANADA').sum()
    perdidas = (df_h['estado'] == 'PERDIDA').sum()
    total_res = ganadas + perdidas
    beneficio_total = df_h['resultado'].sum()
    
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Apuestas", total_res)
    h2.metric("Ganadas", ganadas)
    h3.metric("% Acierto", f"{ganadas/total_res*100:.0f}%" if total_res else "—")
    h4.metric("P&L Total", fmt_money(beneficio_total), delta=f"{beneficio_total:+.2f}")
    
    st.dataframe(
        df_h[['partido', 'pick', 'momio', 'stake', 'estado', 'resultado']].style.applymap(
            lambda v: 'color: #16a34a; font-weight:600' if v == 'GANADA' else ('color: #dc2626; font-weight:600' if v == 'PERDIDA' else ''),
            subset=['estado']
        ),
        use_container_width=True,
        hide_index=True
    )
