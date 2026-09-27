"""Fetch public source records and club badges into a reproducible local cache."""
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
IDS = {'ARS':'arsenal', 'AVL':'aston-villa', 'BOU':'bournemouth', 'BRE':'brentford',
       'BHA':'brighton', 'BUR':'burnley', 'CHE':'chelsea', 'CRY':'crystal-palace',
       'EVE':'everton', 'FUL':'fulham', 'LEE':'leeds', 'LIV':'liverpool',
       'MCI':'city', 'MUN':'united', 'NEW':'newcastle', 'NFO':'nottingham-forest',
       'SUN':'sunderland', 'TOT':'tottenham', 'WHU':'west-ham', 'WOL':'wolves'}
BASE = 'https://raw.githubusercontent.com/olbauday/FPL-Core-Insights/main/data/2025-2026/By%20Tournament/Premier%20League'

def download(item):
    url, relative = item
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size:
        return relative
    with urlopen(Request(url, headers={'User-Agent':'MorningSix/1.0'}), timeout=40) as response:
        body = response.read()
    if relative.endswith('.png') and not body.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError(f'Not a PNG: {url}')
    target.write_bytes(body)
    return relative

if __name__ == '__main__':
    rows = list(csv.DictReader((ROOT/'data/sources/teams-2526.csv').open(encoding='utf-8')))
    crests = {IDS[r['short_name']]: {
        'code': int(r['code']), 'name': r['name'],
        'path': f"assets/crests/{IDS[r['short_name']]}.png",
        'sourceUrl': f"https://resources.premierleague.com/premierleague/badges/100/t{r['code']}.png"
    } for r in rows}
    tasks = [(v['sourceUrl'], v['path']) for v in crests.values()]
    tasks += [(f'{BASE}/GW{gw}/{kind}.csv', f'data/sources/gw/GW{gw}-{kind}.csv')
              for gw in range(1,39) for kind in ['fixtures','incidents']]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for relative in pool.map(download, tasks):
            print(relative, flush=True)
    (ROOT/'data/crests.json').write_text(json.dumps(crests,ensure_ascii=False,indent=2),encoding='utf-8')
