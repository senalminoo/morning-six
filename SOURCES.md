# 데이터와 미디어 출처 장부

## 범위

2025/26 프리미어리그는 20개 팀, 380경기입니다. 하이라이트 대조 대상은 Arsenal, Chelsea, Liverpool, Manchester City, Manchester United, Tottenham Hotspur 중 한 팀 이상이 출전한 198경기입니다.

## 경기 결과와 골 이벤트

| 자료 | 원본 | 사용 방식 |
| --- | --- | --- |
| 최종 결과 380경기 | [DataHub season-2526.csv](https://datahub.io/football/english-premier-league/_r/-/season-2526.csv) | `data/season-2526-source.csv`에 저장. 최종 점수와 홈·원정 대진의 기준 |
| 일정·이벤트 | [FPL-Core-Insights](https://github.com/olbauday/FPL-Core-Insights) 2025/26 Premier League GW별 `fixtures.csv`, `incidents.csv` | 킥오프, 라운드, 골 시각과 득점자에 사용 |
| 경기 상세 링크 | FotMob의 `match_url` | 화면에서 경기 기록을 열 수 있는 외부 링크. 프리미어리그 공식 링크로 표기하지 않음 |

생성기는 결과 CSV의 팀·날짜·스코어를 일정 데이터와 대조합니다. 이벤트가 점수와 맞지 않는 두 경기는 `goalsComplete:false`로 저장하고 화면에 불완전한 타임라인임을 알립니다.

GW 원본에는 일정 변경 경기 네 건의 라운드 값이 실제 프리미어리그 라운드와 다른 사례가 있습니다. 해당 경기의 화면 라운드는 쿠팡플레이 공식 영상 제목의 라운드로 표시합니다: Wolves–Arsenal 31R, Man City–Crystal Palace 31R, Burnley–Man City 34R, Brighton–Chelsea 34R. 각 영상은 대진과 실제 킥오프 직후 게시일을 함께 대조했습니다.

## 실제 팀 엠블럼

팀 ID는 FPL 팀 CSV의 `code`를 사용합니다. `id`나 `pulse_id`를 배지 번호로 사용하면 팀 배지가 섞일 수 있으므로 사용하지 않습니다.

| 자료 | 원본 | 사용 방식 |
| --- | --- | --- |
| 팀 코드 | [FPL-Core-Insights teams.csv](https://raw.githubusercontent.com/olbauday/FPL-Core-Insights/main/data/2025-2026/By%20Tournament/Premier%20League/GW1/teams.csv) | 20개 팀 이름과 `code` 매핑 |
| 배지 이미지 | `https://resources.premierleague.com/premierleague/badges/100/t{code}.png` | `assets/crests/`에 저장하고 `data/crests.json`에 원본 URL 기록 |

빅6의 정확한 코드 매핑은 Arsenal `3`, Chelsea `8`, Liverpool `14`, Manchester City `43`, Manchester United `1`, Tottenham `6`입니다. 20개 로컬 이미지의 파일 존재와 브라우저 렌더링을 확인했습니다.

## 빅6 대표 선수 이미지

상단 에이스 보드에는 팀별 한 명씩을 배치했습니다: Arsenal 사카, Manchester City 홀란, Chelsea 리스 제임스, Liverpool 반다이크, Tottenham 반더벤, Manchester United 브루노 페르난데스. 선수 이미지는 프리미어리그 공개 선수 사진 CDN에서 내려받아 `assets/players/`에 저장했습니다. 매핑과 원본 URL은 `data/players.json`에 기록했습니다.

## 쿠팡플레이 스포츠 2분 하이라이트

| 자료 | 원본 | 사용 방식 |
| --- | --- | --- |
| 공식 업로더 | [Coupang Play Sports YouTube 채널](https://www.youtube.com/channel/UCnBht7BrOx-A328KFXgysqQ) | 채널 ID `UCnBht7BrOx-A328KFXgysqQ`와 일치하는 영상만 후보로 사용 |
| 공개 채널 목록 | YouTube 공개 메타데이터 | 제목, 설명, 길이, 게시일, 라운드를 후보 대진과 대조 |
| 공개 watch 페이지 | `data/sources/watch/{videoId}.json` | 업로더, 제목, 길이, 공개 상태, 한국 이용 가능 정보 확인 |

`data/highlights.json`에는 빅6 대상 198경기 각각에 하나의 실제 YouTube watch URL을 저장했습니다. 같은 영상 ID를 두 경기에 재사용하지 않았습니다.

- 195개: watch 페이지 메타데이터까지 확인한 `metadata_verified`
- 3개: 채널 목록의 제목·설명·라운드·길이는 확인했으나 YouTube HTTP 429로 watch 페이지 읽기가 제한된 `channel_verified`
- 22개: 2026/27 시즌 영상이라 후보에서 제외
- 실제 영상 재생을 끝까지 확인한 경기: 0개

watch 페이지를 읽지 못한 3개 링크는 다음과 같습니다.

| 경기 | 영상 |
| --- | --- |
| Liverpool–Wolves, 18R | [VQE2v06xEF8](https://www.youtube.com/watch?v=VQE2v06xEF8) |
| Crystal Palace–Tottenham, 18R | [_3xax2OXYU8](https://www.youtube.com/watch?v=_3xax2OXYU8) |
| Tottenham–Crystal Palace, 29R | [SCpGX8kCYeA](https://www.youtube.com/watch?v=SCpGX8kCYeA) |

YouTube의 삭제, 비공개 전환, 지역 또는 로그인 조건은 이후 바뀔 수 있습니다. 그래서 화면은 링크 수와 watch 페이지 확인 수를 분리해 표시하며, 위 세 링크에는 재생 상태가 확인 전이라는 표시를 남깁니다.
