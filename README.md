# SixKicks · 2025/26 프리미어리그 아카이브

2025/26 프리미어리그 결과와 골 타임라인을 모은 정적 웹 프로젝트입니다. 기본 화면은 빅6가 출전한 경기를 표시하고, 각 경기에 쿠팡플레이 스포츠의 실제 YouTube 2분 하이라이트 링크를 제공합니다.

## 현재 데이터

- 시즌 전체: 380경기, 20개 팀
- 빅6 포함 경기: 198경기 (`6 × 38 - 빅6 맞대결 30경기`)
- 하이라이트 링크: 198/198개, 모두 서로 다른 YouTube watch URL
- 엠블럼: 프리미어리그 공개 배지 원본을 내려받아 20개 팀에 로컬 파일로 연결
- 에이스 보드: 사카, 홀란, 리스 제임스, 반다이크, 반더벤, 브루노 페르난데스의 실제 프로필 이미지 연결
- 골 타임라인: 1,043골. 이벤트 원본이 불완전한 2경기는 타임라인을 숨기고 최종 스코어만 표시

198개 중 195개는 YouTube 공개 영상 페이지의 업로더, 제목, 길이, 공개 상태, 한국 이용 가능 정보를 확인했습니다. 나머지 3개는 YouTube의 일시적인 자동 조회 제한(HTTP 429)으로 상세 페이지를 읽지 못했지만, 공식 채널의 목록 제목·라운드·설명·길이로 대진을 확인해 링크를 제공합니다. 화면에는 해당 3개를 `현재 재생 상태 확인 전`으로 표시합니다. 실제 재생을 끝까지 확인한 검수는 수행하지 않았습니다.

## 실행

브라우저에서 `index.html`을 열면 됩니다. 외부 API 키나 서버는 필요하지 않습니다. 엠블럼과 경기 데이터는 프로젝트에 들어 있어 오프라인에서도 화면을 볼 수 있으며, 하이라이트 재생에는 인터넷 연결이 필요합니다.

기본 필터는 빅6 전체(198경기)입니다. 팀별 필터는 각 38경기와 38개 링크를 표시하며, 리그 전체는 380경기를 탐색합니다. 한 화면에는 20경기씩 보여 주고 `다음 20경기 보기`로 이어 볼 수 있습니다.

## 재생성

저장된 원본으로 화면 데이터를 다시 만들려면 Python 표준 라이브러리만으로 아래를 실행합니다.

```powershell
python build_highlights.py
python generate_2526.py
```

온라인 원본을 다시 모으려면 다음 순서로 실행합니다. 영상 수집은 공개 채널 메타데이터만 읽으며 영상 파일은 내려받지 않습니다.

```powershell
python -m pip install --target .tools/yt-dlp -r requirements-collector.txt
python fetch_sources.py
python collect_highlights.py
python collect_highlights.py --teams
python match_highlights.py
python verify_highlights.py
python build_highlights.py
python generate_2526.py
```

## 화면 검증

Playwright와 Edge가 있는 환경에서는 아래 명령으로 데이터 수와 렌더링을 확인할 수 있습니다.

```powershell
$env:MORNING_SIX_PLAYWRIGHT='playwright-core 모듈 경로'
node checks/verify.cjs
```

이 검사는 380경기, 빅6 198개 링크, 20개 엠블럼, 팀별 38경기, 모바일 가로 넘침과 브라우저 오류를 확인합니다. YouTube 원격 재생은 검사하지 않습니다.

## 파일

| 파일 | 역할 |
| --- | --- |
| `index.html`, `style.css`, `app.js` | 정적 화면과 필터 UI |
| `data/matches.js` | 380경기, 득점, 엠블럼 경로, 하이라이트 연결 데이터 |
| `data/highlights.json` | 빅6 198경기의 영상 연결 장부 |
| `data/video-audit.json` | 영상 대조 결과와 상태별 수치 |
| `data/highlight-match-audit.json` | 198개 링크의 대진·라운드·채널·길이·공개 메타데이터 재대조 결과 |
| `data/crests.json`, `assets/crests/` | 실제 팀 엠블럼 매핑과 로컬 이미지 |
| `data/players.json`, `assets/players/` | 빅6 대표 선수 이미지와 원본 URL |
| `data/sources/` | 결과, 일정, 이벤트, 채널 메타데이터 원본 |
| `SOURCES.md` | 출처와 검수 한계 |
| `prd.md` | 범위와 완료 기준 |
