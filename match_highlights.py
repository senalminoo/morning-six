"""Match observed YouTube titles to season fixtures; no guessed video URLs."""
import csv
import json
import re
from pathlib import Path
from fetch_sources import IDS

ROOT = Path(__file__).resolve().parent
CHANNEL = 'UCnBht7BrOx-A328KFXgysqQ'
BIG6 = {'arsenal','chelsea','liverpool','city','united','tottenham'}
ALIASES = {
 'arsenal':['arsenal','아스날','아스널'], 'aston-villa':['aston villa','아스톤 빌라','아스턴 빌라'],
 'bournemouth':['bournemouth','afc bournemouth','본머스'], 'brentford':['brentford','브렌트포드','브렌트퍼드'],
 'brighton':['brighton','brighton & hove albion','브라이튼','브라이턴'], 'burnley':['burnley','번리'],
 'chelsea':['chelsea','첼시'], 'crystal-palace':['crystal palace','크리스탈 팰리스','크리스털 팰리스'],
 'everton':['everton','에버턴','에버튼'], 'fulham':['fulham','풀럼'], 'leeds':['leeds','leeds united','리즈'],
 'liverpool':['liverpool','리버풀'], 'city':['man city','manchester city','맨시티'],
 'united':['man utd','man united','manchester united','맨유'], 'newcastle':['newcastle','newcastle united','뉴캐슬'],
 'nottingham-forest':['nottingham','nottingham forest',"nott'm forest",'노팅엄','노팅엄 포레스트'],
 'sunderland':['sunderland','선덜랜드'], 'tottenham':['tottenham','tottenham hotspur','spurs','토트넘'],
 'west-ham':['west ham','west ham united','웨스트햄'], 'wolves':['wolverhampton','wolverhampton wanderers','wolves','울버햄튼','울버햄프턴']}

def normal(value):
    return re.sub(r'[^a-z가-힣0-9]', '', value.lower())

LOOKUP = {normal(alias): tid for tid, aliases in ALIASES.items() for alias in aliases}

def title_key(title):
    if not re.search(r'\[(?:Premier League|프리미어리그)\]',title,re.I):
        return None
    match = re.search(r'\]\s*(?:(?:Matchweek|Matchday|Round)\s*)?(\d+)(?:R|라운드)?\s*[:\-]?\s*(.*?)\s+vs\.?\s+(.*?)\s+2\s*(?:[-– ]?\s*[Mm]in(?:ute)?s?|분)', title,re.I)
    if not match:
        return None
    gw, home, away = match.groups()
    h, a = LOOKUP.get(normal(home)), LOOKUP.get(normal(away))
    if h and a:
        return int(gw), h, a
    return None

def fixtures():
    rows = csv.DictReader((ROOT/'data/sources/teams-2526.csv').open(encoding='utf-8'))
    codes = {int(r['code']): IDS[r['short_name']] for r in rows}
    result = {}
    for path in (ROOT/'data/sources/gw').glob('*-fixtures.csv'):
        for f in csv.DictReader(path.open(encoding='utf-8')):
            key = int(float(f['gameweek'])), codes[int(float(f['home_team']))], codes[int(float(f['away_team']))]
            result[key] = f
    return result

if __name__ == '__main__':
    season = fixtures()
    pairs = {(key[1],key[2]): (key,f) for key,f in season.items()}
    videos = {}
    unparsed = []
    for path in (ROOT/'data/sources').glob('coupang-*.json'):
        content = json.loads(path.read_text(encoding='utf-8'))
        for v in content.get('entries',[]):
            if v.get('channel_id') != CHANNEL:
                continue
            key = title_key(v['title'])
            pair = pairs.get(key[1:]) if key else None
            if pair and (key[1] in BIG6 or key[2] in BIG6):
                actual_key, fixture = pair
                # Postponed matches retain the original round in the video title.
                # Publication date must be checked before accepting this candidate.
                videos[v['id']] = {**v, 'listedRound':key[0], 'gameweek':actual_key[0], 'home':key[1], 'away':key[2], 'fixtureId':fixture['match_id'], 'kickoff':fixture['kickoff_time']}
            elif 'Premier League' in v['title'] or '프리미어리그' in v['title']:
                unparsed.append(v['title'])
    eligible = {k:f for k,f in season.items() if k[1] in BIG6 or k[2] in BIG6}
    keys = {(v['gameweek'],v['home'],v['away']) for v in videos.values()}
    missing = [{'gameweek':k[0],'home':k[1],'away':k[2],'fixtureId':f['match_id']} for k,f in sorted(eligible.items()) if k not in keys]
    result = {'channelId':CHANNEL, 'candidates':list(videos.values()),'missing':missing}
    (ROOT/'data/sources/video-candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'fixtures':len(season),'targets':len(eligible),'matched':len(eligible)-len(missing),'candidateVideos':len(videos),'missing':missing,'unparsed':unparsed[:20]},ensure_ascii=False,indent=2))
