"""Independently audit every published highlight against its fixture and cached public metadata."""
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from match_highlights import BIG6, CHANNEL, fixtures, title_key


def main():
    highlights = json.loads((ROOT / 'data/highlights.json').read_text(encoding='utf-8'))
    fixture_by_id = {fixture['match_id']: (key, fixture) for key, fixture in fixtures().items()}
    eligible = {
        fixture['match_id']: key for key, fixture in fixtures().items()
        if key[1] in BIG6 or key[2] in BIG6
    }
    issues = []
    schedule_round_differences = []
    video_ids = []
    status_counts = {}

    for fixture_id, video in highlights.items():
        status = video.get('status')
        status_counts[status] = status_counts.get(status, 0) + 1
        video_ids.append(video.get('videoId'))
        expected = fixture_by_id.get(fixture_id)
        if not expected:
            issues.append({'fixtureId': fixture_id, 'issue': 'unknown-fixture'})
            continue
        key, fixture = expected
        parsed = title_key(video.get('title', ''))
        if not parsed:
            issues.append({'fixtureId': fixture_id, 'issue': 'unparseable-title', 'title': video.get('title')})
        elif parsed[1:] != key[1:]:
            issues.append({'fixtureId': fixture_id, 'issue': 'home-away-mismatch', 'expected': key[1:], 'titlePair': parsed[1:]})
        elif parsed[0] != key[0]:
            # Fixture dates and the video's pair agree. Keep this separately from
            # a match failure because the saved GW source can disagree on round.
            schedule_round_differences.append({
                'fixtureId': fixture_id,
                'sourceGameweek': key[0],
                'officialVideoRound': parsed[0],
                'title': video.get('title'),
            })
        if video.get('channelId') != CHANNEL:
            issues.append({'fixtureId': fixture_id, 'issue': 'wrong-channel'})
        if video.get('url') != f"https://www.youtube.com/watch?v={video.get('videoId')}":
            issues.append({'fixtureId': fixture_id, 'issue': 'url-video-id-mismatch'})
        if not re.fullmatch(r'[\w-]{11}', video.get('videoId') or ''):
            issues.append({'fixtureId': fixture_id, 'issue': 'invalid-video-id'})
        if not 30 <= (video.get('durationSeconds') or 0) <= 300:
            issues.append({'fixtureId': fixture_id, 'issue': 'unexpected-duration'})
        if '2분' not in video.get('title', '') and '2 min' not in video.get('title', '').lower():
            issues.append({'fixtureId': fixture_id, 'issue': 'not-two-minute-title'})

        cache_path = ROOT / 'data/sources/watch' / f"{video.get('videoId')}.json"
        cache = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else None
        if status == 'metadata_verified':
            if not cache or cache.get('httpStatus') != 200 or cache.get('channelId') != CHANNEL:
                issues.append({'fixtureId': fixture_id, 'issue': 'missing-official-watch-metadata'})
            else:
                if cache.get('title') != video.get('title'):
                    issues.append({'fixtureId': fixture_id, 'issue': 'cached-title-differs'})
                if cache.get('playabilityStatus') != 'OK' or 'KR' not in (cache.get('availableCountries') or []):
                    issues.append({'fixtureId': fixture_id, 'issue': 'not-currently-playable-in-kr-cache'})
                published, kickoff = cache.get('publishDate'), fixture.get('kickoff_time')
                if not published or not kickoff:
                    issues.append({'fixtureId': fixture_id, 'issue': 'missing-date-evidence'})
                else:
                    gap = (datetime.fromisoformat(published) - datetime.fromisoformat(kickoff)).total_seconds()
                    if not 0 <= gap <= 3 * 86400:
                        issues.append({'fixtureId': fixture_id, 'issue': 'publication-date-outside-three-days', 'seconds': gap})
        elif status == 'channel_verified':
            if not cache or not cache.get('error'):
                issues.append({'fixtureId': fixture_id, 'issue': 'missing-rate-limit-evidence'})
        else:
            issues.append({'fixtureId': fixture_id, 'issue': 'unexpected-status', 'status': status})

    duplicate_ids = sorted({video_id for video_id in video_ids if video_ids.count(video_id) > 1})
    report = {
        'eligibleFixtures': len(eligible),
        'highlightRecords': len(highlights),
        'missingEligibleFixtures': sorted(set(eligible) - set(highlights)),
        'extraFixtures': sorted(set(highlights) - set(eligible)),
        'duplicateVideoIds': duplicate_ids,
        'statusCounts': status_counts,
        'scheduleRoundDifferences': schedule_round_differences,
        'issues': issues,
        'matchIntegrityPassed': not issues and not duplicate_ids and set(eligible) == set(highlights),
    }
    out = ROOT / 'data/highlight-match-audit.json'
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
