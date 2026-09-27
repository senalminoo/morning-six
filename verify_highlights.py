"""Read public watch-page metadata; do not claim human playback verification."""
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
CACHE = ROOT/'data/sources/watch'
CACHE.mkdir(parents=True, exist_ok=True)

def inspect(video):
    vid = video['id']
    path = CACHE/f'{vid}.json'
    if path.exists():
        cached = json.loads(path.read_text(encoding='utf-8'))
        if not ('--retry-errors' in sys.argv and cached.get('error')):
            return cached
        time.sleep(5)
    url = f'https://www.youtube.com/watch?v={vid}&hl=ko'
    result = {'id':vid, 'url':url, 'checkedAt':datetime.now(timezone.utc).isoformat()}
    try:
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0','Accept-Language':'ko-KR,ko;q=0.9'}),timeout=30) as response:
            html = response.read().decode('utf-8')
            result['httpStatus'] = response.status
        marker = re.search(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*',html)
        if marker:
            data = json.JSONDecoder().raw_decode(html[marker.end():])[0]
            details = data.get('videoDetails',{})
            micro = data.get('microformat',{}).get('playerMicroformatRenderer',{})
            result.update({'channelId':details.get('channelId'), 'title':details.get('title'),
                'durationSeconds':int(details['lengthSeconds']) if details.get('lengthSeconds') else None,
                'publishDate':micro.get('publishDate'), 'uploadDate':micro.get('uploadDate'),
                'availableCountries':micro.get('availableCountries'),
                'playabilityStatus':data.get('playabilityStatus',{}).get('status'),
                'playabilityReason':data.get('playabilityStatus',{}).get('reason'),
                'description':details.get('shortDescription')})
        else:
            result['error'] = 'Public player metadata not exposed'
    except Exception as exc:
        result['error'] = str(exc)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result

if __name__ == '__main__':
    entries = json.loads((ROOT/'data/sources/video-candidates.json').read_text(encoding='utf-8'))['candidates']
    if '--sample' in sys.argv:
        entries = entries[:1]
    with ThreadPoolExecutor(max_workers=1 if '--retry-errors' in sys.argv else 3) as pool:
        for n, row in enumerate(pool.map(inspect,entries),1):
            if n % 20 == 0 or '--sample' in sys.argv:
                print(json.dumps({'completed':n,'total':len(entries),**row} if '--sample' in sys.argv else {'completed':n,'total':len(entries)},ensure_ascii=False),flush=True)
    print('Watch metadata cached',len(entries),flush=True)
