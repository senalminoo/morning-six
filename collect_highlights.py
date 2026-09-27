"""Collect public metadata only; never downloads video or audio."""
import json
import sys
from urllib.parse import quote
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.tools/yt-dlp'))
from yt_dlp import YoutubeDL

if '--teams' in sys.argv:
    for key, name in [('arsenal','아스날'),('chelsea','첼시'),('liverpool','리버풀'),('city','맨시티'),('united','맨유'),('tottenham','토트넘')]:
        url = 'https://www.youtube.com/@coupangplaysports/search?query=' + quote(f'프리미어리그 {name} 2분')
        with YoutubeDL({'extract_flat':True, 'skip_download':True,'socket_timeout':25,'retries':2,'quiet':True,
                        'extractor_args':{'youtube':{'lang':['ko']},'youtubetab':{'lang':['ko']}}}) as ydl:
            info = ydl.extract_info(url, download=False)
            entries = [{k:e.get(k) for k in ['id','title','url','duration','channel','channel_id','upload_date','description']} for e in info['entries'] if e]
        (ROOT/f'data/sources/coupang-{key}.json').write_text(json.dumps({'sourceUrl':url,'channelId':info.get('channel_id'),'entries':entries},ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'{key}: {len(entries)} metadata entries',flush=True)
    raise SystemExit(0)

url = sys.argv[1] if len(sys.argv) > 1 else 'https://www.youtube.com/@coupangplaysports/search?query=프리미어리그%202분'
output = ROOT / (sys.argv[2] if len(sys.argv) > 2 else 'data/sources/coupang-videos.json')
with YoutubeDL({'extract_flat': True, 'skip_download': True, 'ignoreerrors': True,
                'socket_timeout': 25, 'retries': 2, 'quiet': True}) as ydl:
    info = ydl.extract_info(url, download=False)
    if not info:
        raise SystemExit('No metadata returned')
    fields = ['id', 'title', 'url', 'duration', 'channel', 'channel_id', 'uploader',
              'uploader_id', 'timestamp', 'upload_date', 'availability', 'description']
    records = [{k: e.get(k) for k in fields} for e in info.get('entries', []) if e]
    output.write_text(json.dumps({'sourceUrl': url, 'channelId': info.get('channel_id'),
                                'title': info.get('title'), 'entries': records},
                               ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Saved {len(records)} metadata entries to {output.name}', flush=True)
