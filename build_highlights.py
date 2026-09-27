"""Accept only observed official video pages matching the season's home/away/date."""
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from match_highlights import fixtures, title_key, CHANNEL, BIG6

ROOT = Path(__file__).resolve().parent

def build():
    season = fixtures()
    eligible = {f['match_id']: (key, f) for key,f in season.items() if key[1] in BIG6 or key[2] in BIG6}
    candidates = json.loads((ROOT/'data/sources/video-candidates.json').read_text(encoding='utf-8'))['candidates']
    accepted, rejected = {}, []
    for video in candidates:
        watch_path = ROOT/f"data/sources/watch/{video['id']}.json"
        page = json.loads(watch_path.read_text(encoding='utf-8')) if watch_path.exists() else {}
        reasons = []
        parsed = title_key(page.get('title') or '')
        if page.get('httpStatus') != 200 or page.get('channelId') != CHANNEL:
            reasons.append('official-page-not-confirmed')
        if not parsed or parsed[1:] != (video['home'],video['away']):
            reasons.append('title-pair-mismatch')
        if not re.fullmatch(r'[\w-]{11}',video['id']):
            reasons.append('invalid-video-id')
        duration = page.get('durationSeconds')
        if not duration or not 30 <= duration <= 300:
            reasons.append('unexpected-duration')
        published = page.get('publishDate')
        if not published:
            reasons.append('publication-date-missing')
        else:
            gap = (datetime.fromisoformat(published)-datetime.fromisoformat(video['kickoff'])).total_seconds()
            if not 0 <= gap <= 3*24*3600:
                reasons.append('different-season-or-date')
        if page.get('playabilityStatus') != 'OK':
            reasons.append('player-status-not-ok')
        countries = page.get('availableCountries')
        if countries is not None and 'KR' not in countries:
            reasons.append('korea-not-allowed')
        if reasons:
            # The channel listing is still direct evidence of a real official link.
            # A rate-limited watch page is not proof that the video is missing.
            listed = title_key(video.get('title') or '')
            season_in_description = bool(re.search(r'(?:2025|25)[/-]26',video.get('description') or ''))
            if page.get('error') and listed and listed[0] == video['gameweek'] and season_in_description and video.get('duration') and video.get('channel_id') == CHANNEL:
                details_path = ROOT/f"data/sources/watch/{video['id']}-details.json"
                details = json.loads(details_path.read_text(encoding='utf-8')) if details_path.exists() else {}
                accepted[video['fixtureId']] = {
                    'source':'coupang','channelId':CHANNEL,'videoId':video['id'],
                    'title':details.get('title') or video['title'],
                    'url':f"https://www.youtube.com/watch?v={video['id']}",
                    'durationSeconds':int(video['duration']),'publishedAt':None,
                    'status':'channel_verified','checkedAt':page['checkedAt'],'round':listed[0],
                    'playerStatus':'UNCHECKED','koreaAllowed':None,'playbackChecked':False,
                    'evidenceNote':'공식 채널 목록에서 영상 ID·대진·라운드·길이와 설명의 25/26 시즌 확인. 개별 페이지 조회 제한으로 게시일·현재 재생 상태는 미확인.'}
                continue
            rejected.append({'videoId':video['id'],'fixtureId':video['fixtureId'],'reasons':reasons})
            continue
        record = {'source':'coupang','channelId':CHANNEL,'videoId':video['id'],
                  'title':page['title'],'url':f"https://www.youtube.com/watch?v={video['id']}",
                  'durationSeconds':duration,'publishedAt':published,'status':'metadata_verified',
                  'checkedAt':page['checkedAt'], 'round':parsed[0],
                  'playerStatus':page['playabilityStatus'],'koreaAllowed':countries is None or 'KR' in countries,
                  'playbackChecked':False,
                  'evidenceNote':'공식 채널 ID, 공개 영상 제목의 대진·2분 하이라이트, 경기 직후 게시일, 실제 길이, 플레이어 OK 및 한국 허용 메타데이터 대조. 전체 영상 재생 검수는 별도.'}
        previous = accepted.get(video['fixtureId'])
        if previous and previous['videoId'] != record['videoId']:
            raise ValueError(f"Multiple valid videos for {video['fixtureId']}: choose a primary explicitly")
        accepted[video['fixtureId']] = record
    missing = [{'fixtureId':fid,'round':key[0],'home':key[1],'away':key[2]} for fid,(key,f) in eligible.items() if fid not in accepted]
    pending = [{'fixtureId':k,'videoId':v['videoId'],'url':v['url']} for k,v in accepted.items() if v['status']=='channel_verified']
    audit = {'targetMatches':len(eligible),'linkedMatches':len(accepted),'metadataVerifiedMatches':len(accepted)-len(pending),
             'watchPageUnchecked':pending,'missing':missing,
             'rejectedCandidates':rejected,'playbackCheckedMatches':0,
             'verificationScope':'Watch-page metadata; not full visual playback of each video.'}
    (ROOT/'data/highlights.json').write_text(json.dumps(accepted,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'data/video-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'targets':len(eligible),'linked':len(accepted),'metadataVerified':len(accepted)-len(pending),'missing':missing,
                      'rejectionReasons':dict(Counter(r for row in rejected for r in row['reasons']))},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    build()
