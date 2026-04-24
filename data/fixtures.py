"""
data/fixtures.py - Parser Scores & Fixtures + H2H de FBRef.
"""
import re
import pandas as pd
from datetime import date, datetime, timedelta
from data.parser import EQUIPOS_MAP

def _norm(name):
    n = str(name).strip()
    return EQUIPOS_MAP.get(n, n)

_TEAM_ENDS = {
    'City','United','Rovers','Town','Athletic','FC','AFC','Forest','Palace',
    'Villa','Hotspur','Wanderers','County','Albion','Wednesday','Rangers',
    'Celtic','Burnley','Brentford','Brighton','Fulham','Sunderland','Liverpool',
    'Arsenal','Everton','Chelsea','Bournemouth','Newcastle','Wolves','Leeds',
    'Leicester','Azul','Laguna','Luis','Juárez','Querétaro','Mazatlán',
    'Necaxa','Toluca','Pachuca','Puebla','Atlas','Xolos',
}

_VENUE_WORDS = {
    'Stadium','Park','Road','Lane','Ground','Arena','Cottage','Field','Bridge',
    'Emirates','Anfield','Stamford','Etihad','Molineux','Craven','Elland',
    'Vitality','Selhurst','Goodison','Turf','American','Head-to-Head','Match',
    'Report','Head',
    # Venues españoles / Liga MX
    'Estadio','Azteca','Universitario','Hidalgo','Cuauhtémoc','Jalisco',
    'Akron','BBVA','Nemesio','TSM','Caliente','Olímpico','Victoria',
    'Corregidora','Kraken','Encanto',
}

# Nombres completos de equipos conocidos para mejor split
_KNOWN_TEAMS = set(EQUIPOS_MAP.keys()) | set(EQUIPOS_MAP.values()) | {
    # Liga MX nombres completos
    'Puebla', 'Querétaro', 'Necaxa', 'Toluca', 'Pachuca', 'Atlas',
    'Santos Laguna', 'Cruz Azul', 'América', 'Pumas', 'Tigres', 'Rayados',
    'Chivas', 'Xolos', 'Juárez', 'Mazatlán', 'San Luis', 'León',
    # Premier League
    'Sunderland', 'Fulham', 'Liverpool', 'Arsenal', 'Chelsea', 'Everton',
    'Brentford', 'Brighton', 'Bournemouth', 'Newcastle United',
    'Nottingham Forest', 'Manchester United', 'Manchester City',
    'Crystal Palace', 'Aston Villa', 'West Ham United',
    'Wolverhampton Wanderers', 'Tottenham Hotspur', 'Leeds United',
}

def _split_home_away(tokens):
    # Limpiar venue words del final
    clean = []
    for t in tokens:
        if t in _VENUE_WORDS: break
        if t.replace(',','').isdigit() and len(t.replace(',','')) > 3: break
        clean.append(t)
    if len(clean) < 2: return '', ''

    # Intentar todos los splits — preferir splits donde ambas partes son equipos conocidos
    best = None
    for mid in range(1, len(clean)):
        h = ' '.join(clean[:mid])
        a = ' '.join(clean[mid:])
        h_norm = _norm(h); a_norm = _norm(a)
        h_known = h_norm in _KNOWN_TEAMS or h in _KNOWN_TEAMS or clean[mid-1] in _TEAM_ENDS
        a_known = a_norm in _KNOWN_TEAMS or a in _KNOWN_TEAMS or clean[-1] in _TEAM_ENDS
        if h_known and a_known:
            if best is None:
                best = (h_norm, a_norm)
    if best:
        return best

    # Fallback: último token en TEAM_ENDS
    for mid in range(1, len(clean)):
        if clean[mid-1] in _TEAM_ENDS and clean[-1] in _TEAM_ENDS:
            return _norm(' '.join(clean[:mid])), _norm(' '.join(clean[mid:]))

    # Último fallback: mitad
    mid = len(clean) // 2
    return _norm(' '.join(clean[:mid])), _norm(' '.join(clean[mid:]))

def parse_fixtures(text):
    if not text or len(text) < 20: return None
    try:
        lines = [l.strip() for l in text.replace('\r\n','\n').replace('\r','\n').split('\n')]
        rows = []
        header_found = False
        for line in lines:
            line = line.replace('Club Crest','').strip()
            if not line: continue
            if not header_found:
                if 'Home' in line and 'Away' in line: header_found = True
                continue
            if 'Home' in line and 'Away' in line: continue
            tokens = line.replace('\t',' ').split()
            if len(tokens) < 4: continue
            date_str = date_idx = None
            for i,tok in enumerate(tokens):
                if re.match(r'^\d{4}-\d{2}-\d{2}$', tok):
                    date_str = tok; date_idx = i; break
            if date_str is None: continue
            try: match_date = datetime.strptime(date_str,'%Y-%m-%d').date()
            except: continue
            wk = None
            try: wk = int(tokens[0])
            except: pass
            after = tokens[date_idx+1:]
            time_str = ""; start = 0
            for i,t in enumerate(after):
                if re.match(r'^\d{1,2}:\d{2}$',t): time_str=t; start=i+1
                elif re.match(r'^\(\d+:\d+\)$',t): start=i+1
                else: break
            after = after[start:]
            score_idx = None
            for i,t in enumerate(after):
                if re.match(r'^\d+[-–]\d+$',t): score_idx=i; break
            if score_idx is not None:
                home  = _norm(' '.join(after[:score_idx]))
                score = after[score_idx].replace('–','-')
                rest  = after[score_idx+1:]
                away_t = []
                for t in rest:
                    if t.replace(',','').isdigit() and int(t.replace(',',''))>1000: break
                    if t in _VENUE_WORDS: break
                    away_t.append(t)
                away = _norm(' '.join(away_t)); played = True
            else:
                home, away = _split_home_away(after)
                score = None; played = False
            if not home or not away or home==away: continue
            if len(home)<2 or len(away)<2: continue
            rows.append({'wk':wk,'date':match_date,'time':time_str,
                         'home':home,'away':away,'score':score,'played':played})
        if not rows: return None
        df = pd.DataFrame(rows)
        df = df.drop_duplicates(subset=['date','home','away'])
        return df.reset_index(drop=True)
    except: return None

def get_current_gameweek(fixtures_df, today=None):
    if fixtures_df is None or len(fixtures_df)==0: return None
    if today is None: today = date.today()
    pending = fixtures_df[(~fixtures_df['played'])&(fixtures_df['date']>=today)]
    if len(pending)==0: return None
    next_date = pending['date'].min()
    wm = fixtures_df[(~fixtures_df['played'])&
                     (fixtures_df['date']>=next_date-timedelta(1))&
                     (fixtures_df['date']<=next_date+timedelta(4))]
    if 'wk' in wm.columns and wm['wk'].notna().any():
        wk = wm['wk'].dropna().mode()
        return int(wk.iloc[0]) if len(wk)>0 else None
    return None

def get_gameweek_matches(fixtures_df, wk=None, today=None):
    if fixtures_df is None or len(fixtures_df)==0: return pd.DataFrame()
    if today is None: today = date.today()
    if wk is None: wk = get_current_gameweek(fixtures_df, today)
    if wk is None:
        return fixtures_df[(~fixtures_df['played'])&
                           (fixtures_df['date']>=today)&
                           (fixtures_df['date']<=today+timedelta(7))].copy()
    return fixtures_df[fixtures_df['wk']==wk].copy()

def parse_h2h(text):
    if not text or len(text)<20: return None
    try:
        lines = [l.strip() for l in text.replace('\r\n','\n').replace('\r','\n').split('\n')]
        matches = []; header_found = False
        for line in lines:
            line = line.replace('Club Crest','').strip()
            if not line: continue
            if not header_found:
                if 'Home' in line and ('Score' in line or 'Away' in line): header_found=True
                continue
            if 'Home' in line and 'Away' in line: continue
            tokens = line.replace('\t',' ').split()
            if len(tokens)<4: continue
            score_m = None
            for tok in tokens:
                m = re.match(r'^(\d+)[-–](\d+)$',tok)
                if m: score_m=m; break
            if score_m is None: continue
            gf=int(score_m.group(1)); ga=int(score_m.group(2))
            winner = 'home' if gf>ga else ('away' if ga>gf else 'draw')
            matches.append({'gf':gf,'ga':ga,'total_goals':gf+ga,'winner':winner})
        if not matches: return None
        recent = matches[:10]; total = len(recent)
        if total==0: return None
        return {
            'total_matches': total,
            'home_wins':  sum(1 for m in recent if m['winner']=='home'),
            'draws':      sum(1 for m in recent if m['winner']=='draw'),
            'away_wins':  sum(1 for m in recent if m['winner']=='away'),
            'avg_goals':  round(sum(m['total_goals'] for m in recent)/total,2),
            'btts_pct':   round(sum(1 for m in recent if m['gf']>0 and m['ga']>0)/total*100,1),
            'over25_pct': round(sum(1 for m in recent if m['total_goals']>2)/total*100,1),
            'over15_pct': round(sum(1 for m in recent if m['total_goals']>1)/total*100,1),
            'recent':     recent,
        }
    except: return None

def h2h_lambda_adjustment(h2h, lam_l, lam_v, weight=0.15):
    if h2h is None or h2h['total_matches']<3: return lam_l, lam_v
    total = h2h['total_matches']
    hr = h2h['home_wins']/total; ar = h2h['away_wins']/total
    model_share = lam_l/(lam_l+lam_v) if (lam_l+lam_v)>0 else 0.5
    denom = hr+ar; h2h_share = hr/denom if denom>0 else 0.5
    adj = (h2h_share - model_share)*weight
    return round(max(0.1,lam_l*(1+adj)),3), round(max(0.1,lam_v*(1-adj)),3)
