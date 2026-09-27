"""Use the standard public YouTube metadata extractor for unresolved watch pages."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.tools/yt-dlp'))
from yt_dlp import YoutubeDL

missing = {r['fixtureId'] for r in json.loads((ROOT/'data/video-audit.json').read_text(encoding='utf-8'))['missing']}
candidates = json.loads((ROOT/'data/sources/video-candidates.json').read_text(encoding='utf-8'))['candidates']
for video in candidates:
    if video['fixtureId'] not in missing:
        continue
    with YoutubeDL({'skip_download':True, 'quiet':True, 'socket_timeout':25, 'retries':1,
                    'ignore_no_formats_error':True, 'extractor_args':{'youtube':{'lang':['ko']}}}) as ydl:
        try:
            info = ydl.extract_info(video['url'],download=False)
        except Exception as exc:
            print(video['id'],str(exc),flush=True)
            continue
    summary = {k:info.get(k) for k in ['id','title','channel_id','duration','upload_date','timestamp','availability','description','age_limit']}
    summary.update(checkedAt=datetime.now(timezone.utc).isoformat(),formatCount=len(info.get('formats',[])))
    (ROOT/f"data/sources/watch/{video['id']}-details.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k != 'description'},ensure_ascii=False),flush=True)
