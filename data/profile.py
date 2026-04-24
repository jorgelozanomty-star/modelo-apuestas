"""
data/profile.py
Construcción del perfil estadístico de un equipo a partir de las 9 tablas FBRef.
"""
from data.parser import fget, read_mp, pg, get_team_row
from data.leagues import blend_weights, apply_home_advantage

# Tablas que acepta el sistema
TABLES = [
    "Tabla General",
    "Standard Squad",
    "Standard Opp",
    "Shooting Squad",
    "Shooting Opp",
    "PlayingTime Squad",
    "PlayingTime Opp",
    "Misc Squad",
    "Misc Opp",
]

_EMPTY_PROFILE = {
    "name": "",
    # Ataque
    "gf_pg": 0.0, "xg_pg": 0.0, "npxg_pg": 0.0,
    "sh_pg": 0.0, "sot_pg": 0.0, "g_sh": 0.0, "sot_pct": 0.0,
    # Defensa
    "ga_pg": 0.0, "xga_pg": 0.0,
    "opp_sh_pg": 0.0, "opp_sot_pg": 0.0, "opp_sot_pct": 0.0,
    # Disciplina
    "fouls_pg": 0.0, "yellows_pg": 0.0, "reds_pg": 0.0,
    "opp_fouls_pg": 0.0,
    # Físico
    "aerials_won_pct": 0.0,
    # Tabla
    "position": None, "points": None, "wdl": "",
    # Modelo
    "lambda_att": 1.5, "lambda_def": 1.1,
    "mp": 1,
    "sources": [],
}


def build_team_profile(squad_name: str, data_master: dict,
                       league_name: str = "Liga MX") -> dict:
    """
    Construye el perfil completo del equipo desde las tablas cargadas.

    Flujo:
    1. Lee cada tabla con fget() (robusto a nombres duplicados/NaN).
    2. Convierte a por-partido con pg() (umbrales fijos por tipo de stat).
    3. Aplica blend dinámico ponderado por jornadas jugadas y liga.
    """
    p = {**_EMPTY_PROFILE, "name": squad_name}

    # ── 1. Tabla General ─────────────────────────────────────────────────────
    row = get_team_row(data_master, "Tabla General", squad_name)
    if row is not None:
        mp_g = read_mp(row, fallback=1)
        if mp_g >= 3:
            p["mp"] = mp_g
        rk = fget(row, "Rk", "Pos", "#", default=0)
        if rk > 0:
            p["position"] = int(rk)
        pts = fget(row, "Pts", default=0)
        if pts > 0:
            p["points"] = int(pts)
        w = int(fget(row, "W", "G", "GW", default=0))
        d = int(fget(row, "D", "E", default=0))
        l = int(fget(row, "L", "P", default=0))
        if w + d + l > 0:
            p["wdl"] = f"{w}G-{d}E-{l}P"
        p["sources"].append("TG")

    # ── 2. Standard Squad ────────────────────────────────────────────────────
    row = get_team_row(data_master, "Standard Squad", squad_name)
    if row is not None:
        mp_s = read_mp(row, fallback=p["mp"])
        if mp_s >= 3:
            p["mp"] = mp_s
        gf_raw = fget(row, "GF", "Gls", default=0)
        if gf_raw > 0:
            p["gf_pg"] = pg(gf_raw, p["mp"], "goals")
        xg_raw = fget(row, "xG", default=0)
        if xg_raw > 0:
            p["xg_pg"] = pg(xg_raw, p["mp"], "xg")
        p["sources"].append("SS")

    # ── 3. Standard Opp ──────────────────────────────────────────────────────
    row = get_team_row(data_master, "Standard Opp", squad_name)
    if row is not None:
        mp_o = read_mp(row, fallback=p["mp"])
        if mp_o >= 3:
            p["mp"] = max(p["mp"], mp_o)
        ga_raw = fget(row, "GA", "Gls", default=0)
        if ga_raw > 0:
            p["ga_pg"] = pg(ga_raw, p["mp"], "goals")
        xga_raw = fget(row, "xGA", "xG", default=0)
        if xga_raw > 0:
            p["xga_pg"] = pg(xga_raw, p["mp"], "xg")
        p["sources"].append("SO")

    # ── 4. Shooting Squad ────────────────────────────────────────────────────
    row = get_team_row(data_master, "Shooting Squad", squad_name)
    if row is not None:
        mp90 = read_mp(row, fallback=p["mp"])
        if mp90 >= 3:
            p["mp"] = max(p["mp"], mp90)
        sh_raw   = fget(row, "Sh",   default=0)
        sot_raw  = fget(row, "SoT",  default=0)
        npxg_raw = fget(row, "npxG", "np:xG", default=0)
        xg_sh    = fget(row, "xG",   default=0)
        g_sh_raw = fget(row, "G/Sh", "G-Sh",  default=0)
        sot_pct  = fget(row, "SoT%", default=0)
        if sh_raw   > 0: p["sh_pg"]   = pg(sh_raw,   p["mp"], "shots")
        if sot_raw  > 0: p["sot_pg"]  = pg(sot_raw,  p["mp"], "sot")
        if npxg_raw > 0: p["npxg_pg"] = pg(npxg_raw, p["mp"], "xg")
        if xg_sh    > 0 and p["xg_pg"] == 0:
            p["xg_pg"] = pg(xg_sh, p["mp"], "xg")
        if g_sh_raw > 0:
            p["g_sh"] = g_sh_raw
        if sot_raw > 0 and sh_raw > 0 and sot_raw <= sh_raw:
            p["sot_pct"] = (sot_raw / sh_raw) * 100.0
        elif sot_pct > 0:
            p["sot_pct"] = sot_pct
        p["sources"].append("ShS")

    # ── 5. Shooting Opp ──────────────────────────────────────────────────────
    row = get_team_row(data_master, "Shooting Opp", squad_name)
    if row is not None:
        mp90o = read_mp(row, fallback=p["mp"])
        opp_sh  = fget(row, "Sh",  default=0)
        opp_sot = fget(row, "SoT", default=0)
        xga_sh  = fget(row, "xG",  default=0)
        if opp_sh  > 0: p["opp_sh_pg"]  = pg(opp_sh,  mp90o, "shots")
        if opp_sot > 0: p["opp_sot_pg"] = pg(opp_sot, mp90o, "sot")
        if opp_sot > 0 and opp_sh > 0 and opp_sot <= opp_sh:
            p["opp_sot_pct"] = (opp_sot / opp_sh) * 100.0
        if xga_sh > 0 and p["xga_pg"] == 0:
            p["xga_pg"] = pg(xga_sh, mp90o, "xg")
        p["sources"].append("ShO")

    # ── 6. Misc Squad ────────────────────────────────────────────────────────
    row = get_team_row(data_master, "Misc Squad", squad_name)
    if row is not None:
        mp90m = read_mp(row, fallback=p["mp"])
        fls   = fget(row, "Fls",  default=0)
        crdy  = fget(row, "CrdY", default=0)
        crdr  = fget(row, "CrdR", default=0)
        aer   = fget(row, "Won%", "Aerial Won%", default=0)
        if fls  > 0: p["fouls_pg"]        = pg(fls,  mp90m, "fouls")
        if crdy > 0: p["yellows_pg"]      = pg(crdy, mp90m, "cards")
        if crdr > 0: p["reds_pg"]         = pg(crdr, mp90m, "cards")
        if aer  > 0: p["aerials_won_pct"] = aer
        p["sources"].append("MiS")

    # ── 7. Misc Opp ──────────────────────────────────────────────────────────
    row = get_team_row(data_master, "Misc Opp", squad_name)
    if row is not None:
        mp90mo  = read_mp(row, fallback=p["mp"])
        opp_fls = fget(row, "Fls", default=0)
        if opp_fls > 0:
            p["opp_fouls_pg"] = pg(opp_fls, mp90mo, "fouls")
        p["sources"].append("MiO")

    # ── Lambda blend dinámico ────────────────────────────────────────────────
    has_xg   = p["xg_pg"]   > 0.05
    has_npxg = p["npxg_pg"] > 0.05
    w = blend_weights(p["mp"], league_name, has_xg, has_npxg)

    gf  = p["gf_pg"]   if p["gf_pg"]   > 0.05 else None
    xg  = p["xg_pg"]   if has_xg               else None
    npx = p["npxg_pg"] if has_npxg             else None

    total_w = (w["goals"] if gf else 0) + (w["xg"] if xg else 0) + (w["npxg"] if npx else 0)
    if total_w > 0:
        lam_att = (
            (w["goals"] * (gf  or 0)) +
            (w["xg"]    * (xg  or 0)) +
            (w["npxg"]  * (npx or 0))
        ) / total_w
    else:
        lam_att = 1.5
    p["lambda_att"] = lam_att

    ga  = p["ga_pg"]  if p["ga_pg"]  > 0.05 else None
    xga = p["xga_pg"] if p["xga_pg"] > 0.05 else None
    if ga and xga:
        p["lambda_def"] = 0.50 * ga + 0.50 * xga
    elif ga:
        p["lambda_def"] = ga
    else:
        p["lambda_def"] = 1.1

    return p


def calc_lambdas(prof_l: dict, prof_v: dict, league_name: str) -> tuple[float, float]:
    """
    Calcula los lambdas finales para el partido.
    λ_l = (att_local + def_visita) / 2 + home_adv
    λ_v = (att_visita + def_local) / 2
    """
    raw_l = max(0.10, (prof_l["lambda_att"] + prof_v["lambda_def"]) / 2.0)
    raw_v = max(0.10, (prof_v["lambda_att"] + prof_l["lambda_def"]) / 2.0)
    lam_l, lam_v = apply_home_advantage(raw_l, raw_v, league_name)
    return lam_l, lam_v


def blend_label(prof: dict) -> str:
    """Etiqueta corta con las fuentes usadas en el blend."""
    parts = []
    if prof["gf_pg"]   > 0.05: parts.append("Goles")
    if prof["xg_pg"]   > 0.05: parts.append("xG")
    if prof["npxg_pg"] > 0.05: parts.append("npxG")
    return "+".join(parts) if parts else "default"
