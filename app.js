"use strict";

(() => {
  const data = window.MORNING_SIX_DATA;
  const list = document.querySelector("#match-list");
  if (!data) {
    list.textContent = "경기 데이터를 불러오지 못했어요. data/matches.js 파일이 있는지 확인해주세요.";
    return;
  }

  let selectedDate = "all";
  let selectedRound = "all";
  let viewMode = "date";
  let selectedTeam = "big6";
  let shownMatches = 20;
  const teams = data.teams;
  const auditSeason = data.edition === "2025/26";
  const filters = document.querySelector("#team-filters");
  const filterSelect = document.querySelector("#digest-filter");
  const filterValueLabel = document.querySelector("#filter-value-label");
  const viewSwitch = document.querySelector(".view-switch");
  const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);

  function httpsUrl(value) {
    try {
      const url = new URL(value);
      return url.protocol === "https:" && !url.username && !url.password ? url : null;
    } catch {
      return null;
    }
  }

  // 형식 검증일 뿐, 공식 채널 여부는 데이터를 등록할 때 별도로 확인합니다.
  function videosFor(match) {
    return (match.videos || []).filter((video) => {
      const url = httpsUrl(video.url);
      const source = data.sources[video.source];
      const hasValidUrl = source && url &&
        url.hostname === "www.youtube.com" && url.pathname === "/watch" &&
        /^[A-Za-z0-9_-]{11}$/.test(url.searchParams.get("v") || "");
      if (!hasValidUrl) return false;
      if (!auditSeason) return true;
      return (teams[match.home].bigSix || teams[match.away].bigSix) &&
        ["metadata_verified", "channel_verified"].includes(video.status) && source.official === true &&
        source.channelId && video.channelId === source.channelId &&
        Number.isFinite(video.durationSeconds) && video.durationSeconds > 0 &&
        video.checkedAt && video.evidenceNote;
    });
  }

  function crestMarkup(team, className) {
    const path = team.crestUrl || "";
    const crest = /^assets\/crests\/[a-z-]+\.png$/.test(path) ? path : httpsUrl(path)?.href;
    return crest ? `<img class="${className}" src="${escapeHTML(crest)}" alt="" width="50" height="50" loading="lazy">`
      : `<span class="team-crest" style="--team-color:${team.color}" aria-hidden="true">${escapeHTML(team.short)}</span>`;
  }

  function teamMarkup(id) {
    const team = teams[id];
    return `<div class="team">
      ${crestMarkup(team, "team-crest-image")}
      <strong>${escapeHTML(team.name)}</strong>
    </div>`;
  }

  function goalMarkup(match) {
    if (match.goalsComplete === false) return `<div class="data-note">최종 스코어 ${match.homeScore} : ${match.awayScore} · 득점 상세 기록은 확인 중입니다. 아래 경기 기록에서 확인할 수 있어요.</div>`;
    if (!match.goals.length) return `<div class="no-goals">
      <span aria-hidden="true">—</span><strong>골 없이 마무리된 경기예요.</strong>
      <p>최종 스코어 0 : 0 · 양 팀 무득점</p></div>`;
    const goals = [...match.goals].sort((a, b) => a.minute - b.minute || (a.added || 0) - (b.added || 0));
    let home = 0;
    let away = 0;
    return `<ol class="goal-timeline">${goals.map((goal) => {
      if (goal.team === match.home) home += 1;
      else away += 1;
      const time = `${goal.minute}${goal.added ? `+${goal.added}` : ""}′`;
      const type = goal.type === "penalty" ? " · 페널티킥" : goal.type === "own-goal" ? " · 자책골" : "";
      const playerTeam = teams[goal.playerTeam || goal.team].name;
      const credit = goal.type === "own-goal" ? ` → ${teams[goal.team].name} 득점` : "";
      return `<li>
        <span class="goal-minute">${time}</span>
        <span class="timeline-dot" style="--team-color:${teams[goal.team].color}" aria-hidden="true"></span>
        <div class="goal-player"><strong>${escapeHTML(goal.player)}</strong>
          <span>${escapeHTML(playerTeam + type + credit)}</span></div>
        <span class="running-score" aria-label="득점 후 스코어 ${home} 대 ${away}">${home} <span>:</span> ${away}</span>
      </li>`;
    }).join("")}</ol>`;
  }

  function videoMarkup(match) {
    if (!teams[match.home].bigSix && !teams[match.away].bigSix) return "";
    const videos = videosFor(match);
    if (!videos.length) {
      const states = (match.videos || []).map((video) => video.status);
      const label = auditSeason
        ? states.includes("unavailable") ? "영상 접근 불가"
          : states.includes("missing") ? "공식 하이라이트 미발견"
            : "하이라이트 링크 확인 중"
        : "영상 준비 중";
      return `<div class="match-video">
        <span class="pending"><span aria-hidden="true">◷</span> ${label}</span>
        <span class="pending-note">경기 기록은 먼저 확인할 수 있어요</span></div>`;
    }
    return `<div class="match-video has-videos">
      <div class="video-heading"><strong>공식 하이라이트</strong><span>YouTube · 새 탭에서 재생</span></div>
      ${videos.map((video) => `<a class="official-video" href="${escapeHTML(video.url)}" target="_blank" rel="noopener noreferrer">
        <span class="youtube-mark" aria-hidden="true">▶</span>
        <span><strong>2분 하이라이트 보기 <span class="video-duration">${Math.floor(video.durationSeconds / 60)}:${String(video.durationSeconds % 60).padStart(2, "0")}</span></strong><small>${escapeHTML(data.sources[video.source].name)} · ${escapeHTML(video.title)}</small>${video.status === "channel_verified" ? '<small class="availability-note">공식 채널 영상 · 현재 재생 상태는 확인 전입니다</small>' : ''}</span>
        <span class="external-arrow" aria-hidden="true">↗</span><span class="sr-only"> (새 탭)</span>
      </a>`).join("")}
    </div>`;
  }

  function matchMarkup(match, index) {
    const kickoff = new Intl.DateTimeFormat("ko-KR", {
      timeZone: "Asia/Seoul", year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", hourCycle: "h23"
    }).format(new Date(match.kickoff));
    const report = httpsUrl(match.reportUrl);
    return `<article class="match-card" data-match-id="${escapeHTML(match.id)}">
      <div class="match-meta"><span><i></i> 경기 종료 <span class="meta-divider">/</span> ${escapeHTML(kickoff)} KST</span><span>${match.round}R · PREMIER LEAGUE</span></div>
      <details ${index === 0 ? "open" : ""}>
        <summary aria-label="${escapeHTML(teams[match.home].name)} 대 ${escapeHTML(teams[match.away].name)} 골 기록">
          <div class="scoreboard">${teamMarkup(match.home)}
            <div class="score"><strong>${match.homeScore}<span>:</span>${match.awayScore}</strong><small>FULL TIME</small></div>
            ${teamMarkup(match.away)}</div>
          <div class="expand-row"><span>골 타임라인 <b>${match.homeScore + match.awayScore}</b></span>
            <span class="expand-label"><span class="when-closed">기록 펼치기</span><span class="when-open">기록 접기</span>
            <span class="chevron" aria-hidden="true">⌄</span></span></div>
        </summary>
        <div class="goal-content">${goalMarkup(match)}
          ${report ? `<a class="report-link" href="${escapeHTML(report.href)}" target="_blank" rel="noopener noreferrer">${escapeHTML(match.reportSource || "경기 기록")} 확인 ↗<span class="sr-only"> (새 탭)</span></a>` : ""}
        </div>
      </details>
      ${videoMarkup(match)}
    </article>`;
  }

  function render() {
    const editionBadge = document.querySelector("#edition-badge");
    const noticeTitle = document.querySelector("#edition-notice-title");
    const noticeCopy = document.querySelector("#edition-notice-copy");
    if (editionBadge) editionBadge.textContent = `${data.edition} ARCHIVE`;
    if (auditSeason) {
      if (noticeTitle) noticeTitle.textContent = `${data.edition} 프리미어리그 전체 경기 아카이브입니다.`;
      if (noticeCopy) noticeCopy.textContent = `380경기 기록과 빅6 포함 경기의 쿠팡플레이 스포츠 하이라이트 ${data.coverage.linkedMatches}개를 모았습니다. 영상은 YouTube에서 시청하세요.`;
    } else if (noticeTitle) {
      noticeTitle.textContent = `${data.edition} 실제 경기 모음입니다.`;
    }
    const visible = data.matches
      .filter((match) => (viewMode === "date" ? (selectedDate === "all" || match.digestDate === selectedDate) : (selectedRound === "all" || String(match.round) === selectedRound)) &&
        (selectedTeam === "all" || (selectedTeam === "big6" ? teams[match.home].bigSix || teams[match.away].bigSix : match.home === selectedTeam || match.away === selectedTeam)))
      .sort((a, b) => new Date(b.kickoff) - new Date(a.kickoff));
    document.querySelector("#match-count").textContent = visible.length;
    document.querySelector("#goal-count").textContent = visible.reduce((sum, match) => sum + match.homeScore + match.awayScore, 0);
    const videoTargets = auditSeason ? visible.filter((match) => teams[match.home].bigSix || teams[match.away].bigSix) : [];
    const verifiedTargets = videoTargets.filter((match) => videosFor(match).length > 0).length;
    const activeFilter = viewMode === "date"
      ? (selectedDate === "all" ? "전체 날짜" : `${selectedDate.replaceAll("-", ".")} KST`)
      : (selectedRound === "all" ? "전체 라운드" : `${selectedRound}라운드`);
    document.querySelector("#results-line").textContent = `${selectedTeam === "all" ? "리그 전체" : selectedTeam === "big6" ? "빅6 전체" : teams[selectedTeam].name + " 경기"} ${visible.length}경기 · ${activeFilter} · ${data.edition} · 한국 시간 기준${auditSeason ? ` · 하이라이트 ${verifiedTargets}/${videoTargets.length}` : ""}`;
    filters.querySelectorAll("button").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.team === selectedTeam)));
    filterSelect.value = viewMode === "date" ? selectedDate : selectedRound;
    filterSelect.setAttribute("aria-label", viewMode === "date" ? "날짜 선택" : "라운드 선택");
    filterValueLabel.textContent = viewMode === "date" ? "날짜 선택" : "라운드 선택";
    viewSwitch.querySelectorAll("button").forEach((button) => {
      const active = button.dataset.viewMode === viewMode;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    list.innerHTML = visible.length ? visible.slice(0, shownMatches).map(matchMarkup).join("") + (visible.length > shownMatches ? `<button type="button" id="load-more" class="load-more">다음 ${Math.min(20, visible.length - shownMatches)}경기 보기 <span>${shownMatches} / ${visible.length}</span></button>` : "") : `<div class="empty-state">
      <span aria-hidden="true">☀</span><h3>등록된 경기가 없어요.</h3>
      <p>선택한 날짜와 팀에 해당하는 경기가 없습니다.<br>전체 경기 모음에서 다른 경기를 만나보세요.</p>
      <button id="reset-view" class="reset-button">전체 경기로 돌아가기 ↗</button></div>`;
    const videos = visible.flatMap((match) => videosFor(match).map((video) => ({ match, video })));
    document.querySelector("#video-count").textContent = videos.length;
    document.querySelector("#video-list").innerHTML = videos.length ? videos.slice(0, 6).map(({ match, video }, index) =>
      `<a class="video-item" href="${escapeHTML(video.url)}" target="_blank" rel="noopener noreferrer">
        <span class="video-number">${String(index + 1).padStart(2, "0")}</span>
        <span><strong>${escapeHTML(teams[match.home].name)} vs ${escapeHTML(teams[match.away].name)}</strong>
          <small>${escapeHTML(data.sources[video.source].name)}<br>${escapeHTML(video.title)}</small></span>
        <span aria-hidden="true">↗</span><span class="sr-only"> (새 탭)</span></a>`).join("") :
      '<div class="video-empty"><span aria-hidden="true">▷</span><strong>아직 등록된 영상이 없어요</strong><small>다른 날짜나 팀을 선택해보세요.</small></div>';
  }

  filters.innerHTML = [{ id: "big6", name: "빅6 전체", color: "#203c32" },
    ...["arsenal", "tottenham", "chelsea", "liverpool", "city", "united"].map((id) => ({ id, ...teams[id] })),
    { id: "all", name: "리그 전체", color: "#203c32" }
  ].map((team) => `<button type="button" data-team="${team.id}" aria-pressed="${team.id === selectedTeam}">
    ${team.id === "all" || team.id === "big6" ? '<span aria-hidden="true">▦</span>' : crestMarkup(team, "filter-crest")}
    ${escapeHTML(team.name)}</button>`).join("");

  const dates = [...new Set(data.matches.map((match) => match.digestDate))].sort().reverse();
  const rounds = [...new Set(data.matches.map((match) => Number(match.round)))].sort((a, b) => a - b);
  const dateOptions = '<option value="all">전체 날짜</option>' + dates.map((date) =>
    `<option value="${escapeHTML(date)}">${escapeHTML(date.replaceAll("-", "."))} KST</option>`).join("");
  const roundOptions = '<option value="all">전체 라운드</option>' + rounds.map((round) =>
    `<option value="${round}">${round}라운드</option>`).join("");
  filterSelect.innerHTML = dateOptions;
  filterSelect.addEventListener("change", () => {
    if (viewMode === "date") selectedDate = filterSelect.value;
    else selectedRound = filterSelect.value;
    shownMatches = 20;
    render();
  });
  viewSwitch.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-view-mode]");
    if (!button) return;
    viewMode = button.dataset.viewMode;
    filterSelect.innerHTML = viewMode === "date" ? dateOptions : roundOptions;
    shownMatches = 20;
    render();
  });
  filters.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-team]");
    if (!button) return;
    selectedTeam = button.dataset.team;
    shownMatches = 20;
    render();
  });
  const aceBoard = document.querySelector(".ace-board");
  aceBoard?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-hero-team]");
    if (!button) return;
    selectedTeam = button.dataset.heroTeam;
    selectedDate = "all";
    selectedRound = "all";
    viewMode = "date";
    filterSelect.innerHTML = dateOptions;
    shownMatches = 20;
    render();
    document.querySelector("#matches")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  list.addEventListener("click", (event) => {
    if (event.target.closest("#load-more")) {
      shownMatches += 20;
      render();
      return;
    }
    if (event.target.closest("#reset-view")) {
      selectedDate = "all";
      selectedRound = "all";
      viewMode = "date";
      filterSelect.innerHTML = dateOptions;
      selectedTeam = "big6";
      shownMatches = 20;
      render();
      filters.querySelector("button").focus();
    }
  });

  const chat = document.querySelector("#player-chat");
  const chatLauncher = chat?.querySelector(".chat-launcher");
  const chatPanel = chat?.querySelector(".chat-panel");
  const chatClose = chat?.querySelector(".chat-close");
  const chatForm = chat?.querySelector("#chat-form");
  const chatInput = chat?.querySelector("#chat-input");
  const chatMessages = chat?.querySelector("#chat-messages");
  const chatHistory = [];
  const chatApiUrl = window.MORNING_SIX_CHAT_API || "/api/chat";

  function setChatOpen(open) {
    if (!chat || !chatPanel || !chatLauncher) return;
    chat.classList.toggle("is-open", open);
    chatPanel.hidden = !open;
    chatLauncher.setAttribute("aria-expanded", String(open));
    if (open) window.setTimeout(() => chatInput?.focus(), 80);
    else chatLauncher.focus();
  }

  function appendChatMessage(role, text, sources = []) {
    if (!chatMessages) return null;
    const message = document.createElement("div");
    message.className = `chat-message is-${role}`;
    const copy = document.createElement("p");
    copy.textContent = text;
    message.append(copy);
    const validSources = sources.filter((source) => {
      try {
        return new URL(source.url).hostname.endsWith("namu.wiki");
      } catch {
        return false;
      }
    }).slice(0, 3);
    if (validSources.length) {
      const sourceList = document.createElement("div");
      sourceList.className = "chat-answer-sources";
      validSources.forEach((source, index) => {
        const link = document.createElement("a");
        link.href = source.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = `출처 ${index + 1} ↗`;
        sourceList.append(link);
      });
      message.append(sourceList);
    }
    chatMessages.append(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return message;
  }

  async function askPlayerChat(question) {
    const trimmed = question.trim();
    if (!trimmed || !chatForm || !chatInput) return;
    appendChatMessage("user", trimmed);
    chatHistory.push({ role: "user", content: trimmed });
    chatInput.value = "";
    chatInput.disabled = true;
    const submit = chatForm.querySelector("button[type='submit']");
    submit.disabled = true;
    const loading = appendChatMessage("assistant", "선수 기록을 확인하고 있어요…");
    loading?.classList.add("is-loading");
    try {
      const response = await fetch(chatApiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed, history: chatHistory.slice(-5, -1) })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.error || "답변을 가져오지 못했어요.");
      loading?.remove();
      appendChatMessage("assistant", payload.answer, payload.sources || []);
      chatHistory.push({ role: "assistant", content: payload.answer });
    } catch (error) {
      loading?.remove();
      appendChatMessage("error", error.message || "잠시 후 다시 질문해주세요.");
    } finally {
      chatInput.disabled = false;
      submit.disabled = false;
      chatInput.focus();
    }
  }

  chatLauncher?.addEventListener("click", () => setChatOpen(true));
  chatClose?.addEventListener("click", () => setChatOpen(false));
  chatForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    askPlayerChat(chatInput.value);
  });
  chat?.querySelector(".chat-suggestions")?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-chat-question]");
    if (button) askPlayerChat(button.dataset.chatQuestion);
  });
  render();
})();
