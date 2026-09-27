"""Build the offline archive from saved sources. No guessed logos, times, or video IDs.

Run fetch_sources.py to refresh fixtures/crests, then collect_highlights.py,
match_highlights.py, verify_highlights.py, build_highlights.py to refresh videos.
This generator itself does not require the network or yt-dlp.
"""
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from match_highlights import fixtures, LOOKUP, normal, BIG6, CHANNEL

ROOT = Path(__file__).resolve().parent
KST = timezone(timedelta(hours=9))
NAMES = {
    'arsenal':'아스널', 'aston-villa':'아스톤 빌라', 'bournemouth':'본머스',
    'brentford':'브렌트퍼드', 'brighton':'브라이턴', 'burnley':'번리',
    'chelsea':'첼시', 'crystal-palace':'크리스털 팰리스', 'everton':'에버턴',
    'fulham':'풀럼', 'leeds':'리즈', 'liverpool':'리버풀', 'city':'맨시티',
    'united':'맨유', 'newcastle':'뉴캐슬', 'nottingham-forest':'노팅엄 포리스트',
    'sunderland':'선덜랜드', 'tottenham':'토트넘', 'west-ham':'웨스트햄', 'wolves':'울버햄프턴'
}
COLORS = {'arsenal':'#db0007','chelsea':'#034694','liverpool':'#c8102e',
          'city':'#6cabdd','united':'#da291c','tottenham':'#132257'}

def read_json(relative):
    return json.loads((ROOT/relative).read_text(encoding='utf-8'))

def build():
    crests = read_json('data/crests.json')
    links = read_json('data/highlights.json')
    teams = {}
    for row in csv.DictReader((ROOT/'data/sources/teams-2526.csv').open(encoding='utf-8')):
        tid = next(k for k,v in crests.items() if v['code'] == int(row['code']))
        crest = crests[tid]
        if not (ROOT/crest['path']).is_file():
            raise ValueError(f'Missing crest asset: {tid}')
        teams[tid] = {'name':NAMES[tid], 'short':row['short_name'],
                      'color':COLORS.get(tid,'#5c6f64'), 'bigSix':tid in BIG6,
                      'crestUrl':crest['path'], 'crestCode':crest['code'],
                      'crestSource':crest['sourceUrl']}
    schedule = {(k[1],k[2]): (k,f) for k,f in fixtures().items()}
    events = defaultdict(list)
    for path in (ROOT/'data/sources/gw').glob('*-incidents.csv'):
        for event in csv.DictReader(path.open(encoding='utf-8')):
            if event['incident_type'] == 'goal':
                events[event['match_id']].append(event)
    records, discrepancies = [], []
    for row in csv.DictReader((ROOT/'data/season-2526-source.csv').open(encoding='utf-8')):
        home, away = LOOKUP[normal(row['HomeTeam'])], LOOKUP[normal(row['AwayTeam'])]
        key, fixture = schedule[(home,away)]
        kickoff = datetime.fromisoformat(fixture['kickoff_time'])
        if kickoff.date().isoformat() != row['Date']:
            raise ValueError(f'Fixture date disagrees with results: {home} / {away}')
        fid = fixture['match_id']
        goals = []
        for event in sorted(events[fid],key=lambda e:(int(e['minute']),int(e['added_time'] or 0))):
            if event['team_side'] not in ('home','away'):
                raise ValueError(f'Unidentified scoring team: {fid}')
            credited = home if event['team_side'] == 'home' else away
            goal = {'team':credited,'player':event['player_name'],'minute':int(event['minute'])}
            if event['added_time']:
                goal['added'] = int(event['added_time'])
            if event['goal_type'] == 'penalty':
                goal['type'] = 'penalty'
            elif event['goal_type'] == 'ownGoal':
                goal.update(type='own-goal',playerTeam=away if credited == home else home)
            goals.append(goal)
        home_score, away_score = int(row['FTHG']), int(row['FTAG'])
        tally = Counter(g['team'] for g in goals)
        complete = (tally[home],tally[away]) == (home_score,away_score)
        if not complete or (int(float(fixture['home_score'])),int(float(fixture['away_score']))) != (home_score,away_score):
            discrepancies.append({'fixtureId':fid,'result':[home_score,away_score],
                                  'eventTally':[tally[home],tally[away]]})
        videos = [links[fid]] if fid in links else []
        records.append({'id':f'{home}-{away}-{row["Date"].replace("-","")}',
                        'fixtureId':fid,'gameweek':key[0],
                        'round':videos[0]['round'] if videos else key[0],
                        'digestDate':kickoff.astimezone(KST).date().isoformat(),
                        'kickoff':kickoff.isoformat(),'home':home,'away':away,
                        'homeScore':home_score,'awayScore':away_score,'goals':goals,
                        'goalsComplete':complete,'reportUrl':'https://www.fotmob.com'+fixture['match_url'],
                        'reportSource':'FotMob 경기 기록','videos':videos,
                        'videoStatus':'linked' if videos else 'unreviewed' if home in BIG6 or away in BIG6 else 'not-required'})
    appearances = Counter(t for m in records for t in [m['home'],m['away']])
    assert len(records) == 380 and len({m['id'] for m in records}) == 380
    assert len(appearances) == 20 and set(appearances.values()) == {38}
    target_count = sum(m['home'] in BIG6 or m['away'] in BIG6 for m in records)
    assert target_count == 198
    payload = {'edition':'2025/26','sources':{'coupang':{'name':'쿠팡플레이 스포츠',
                'platform':'YouTube','official':True,'channelId':CHANNEL}},
               'teams':teams,'matches':records,
               'coverage':{'targetMatches':target_count,'linkedMatches':sum(bool(m['videos']) for m in records)}}
    (ROOT/'data/matches.js').write_text('// Generated by generate_2526.py from cached public source records.\nwindow.MORNING_SIX_DATA = '+json.dumps(payload,ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
    (ROOT/'data/result-discrepancies.json').write_text(json.dumps(discrepancies,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'matches':len(records),'teams':len(teams),**payload['coverage'],
                      'goals':sum(len(m['goals']) for m in records),'incompleteTimelines':sum(not m['goalsComplete'] for m in records)}))

if __name__ == '__main__':
    build()
