const state = {
  data: null,
  filtered: [],
  currentIndex: 0,
  labels: {
    attention: "attentive",
    blouse: "properly_worn",
    sources: new Set(["hand_or_arm"]),
    spatial: "inside_volume",
    eventType: "entered_danger_volume",
    eventRole: "physical_entry",
  },
  segmentStart: null,
  zoneEdit: false,
  dragZoneIndex: null,
  dragEventIndex: null,
  autoReview: false,
  scrubbing: false,
};

const els = {};

function qs(id) {
  return document.getElementById(id);
}

function currentVideo() {
  return state.data?.videos?.[state.currentIndex] ?? null;
}

function videoRows() {
  const segments = new Set(state.data.segments.map((row) => row.video_id));
  const events = new Set(state.data.events.map((row) => row.video_id));
  return { segments, events };
}

function normalizedEventRole(row) {
  if (row.event_type === "no_danger_event") return "no_danger";
  if (row.event_role === "physical_entry") return "physical_entry";
  if (row.event_role === "risk_onset") return "risk_onset";
  return "risk_onset";
}

function eventStatus(videoId) {
  const rows = (state.data?.events || []).filter((row) => row.video_id === videoId);
  const hasNoDanger = rows.some((row) => normalizedEventRole(row) === "no_danger");
  const hasPhysical = rows.some((row) => normalizedEventRole(row) === "physical_entry" && row.event_type !== "no_danger_event");
  const hasRisk = rows.some((row) => normalizedEventRole(row) === "risk_onset");
  return {
    rows,
    hasAny: rows.length > 0,
    hasNoDanger,
    hasPhysical,
    hasRisk,
    complete: hasNoDanger || (hasPhysical && hasRisk),
  };
}

function markerFor(videoId) {
  const { segments: segmentSet } = videoRows();
  const eventHasSegment = segmentSet.has(videoId);
  const status = eventStatus(videoId);
  if (eventHasSegment && status.complete) return "âœ“";
  if (status.hasAny) return "E";
  if (eventHasSegment) return "S";
  return "O";
  const { segments, events } = videoRows();
  const hasSegment = segments.has(videoId);
  const hasEvent = events.has(videoId);
  if (hasSegment && hasEvent) return "✓";
  if (hasEvent) return "E";
  if (hasSegment) return "S";
  return "○";
}

function mediaUrl(video) {
  return `/web-media?path=${encodeURIComponent(video.path)}`;
}

function posterUrl(video) {
  return `/thumb?path=${encodeURIComponent(video.path)}&t=0.2`;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const payload = await response.json();
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || `Request failed: ${path}`);
  }
  if (payload.state) {
    state.data = payload.state;
    renderAll();
  }
  return payload;
}

async function loadState() {
  const response = await fetch("/api/state");
  state.data = await response.json();
  renderAll();
  if (state.data.videos.length) loadVideo(0);
}

function renderAll() {
  renderQueue();
  renderActiveButtons();
  renderSummary();
  drawTimeline();
  drawZone();
}

function renderQueue() {
  if (!state.data) return;
  const search = els.searchInput.value.trim().toLowerCase();
  const filter = els.filterSelect.value;
  state.filtered = [];
  els.videoList.innerHTML = "";

  let reviewed = 0;
  for (const [index, video] of state.data.videos.entries()) {
    const marker = markerFor(video.video_id);
    if (marker === "OK") reviewed += 1;
    if (marker === "✓") reviewed += 1;
    const text = `${video.actor} ${video.coarse_label} ${video.path}`.toLowerCase();
    if (search && !text.includes(search)) continue;
    if ((filter === "safe" || filter === "unsafe") && video.coarse_label !== filter) continue;
    if (filter === "needs_review" && marker === "✓") continue;
    if (filter === "reviewed" && marker !== "✓") continue;

    state.filtered.push(index);
    const row = document.createElement("button");
    row.className = `video-row ${video.coarse_label}${index === state.currentIndex ? " active" : ""}`;
    row.innerHTML = `
      <span>${marker}</span>
      <span class="video-name">${video.actor}/${video.coarse_label} ${Number(video.duration_s).toFixed(1)}s ${video.path.split(/[\\/]/).pop()}</span>
      <span>${index + 1}</span>
    `;
    row.addEventListener("click", () => loadVideo(index));
    els.videoList.appendChild(row);
  }
  els.progressText.textContent = `${reviewed}/${state.data.videos.length} videos fully reviewed`;
}

function loadVideo(index) {
  const video = state.data.videos[index];
  if (!video) return;
  state.currentIndex = index;
  state.segmentStart = null;
  els.video.poster = posterUrl(video);
  els.stageStatus.textContent = "Preparing browser-playable video...";
  els.stageStatus.hidden = false;
  els.video.src = mediaUrl(video);
  els.video.playbackRate = playbackRate();
  els.workspaceTitle.textContent = video.path.split(/[\\/]/).pop();
  els.clipMeta.textContent = `${video.actor} / ${video.coarse_label} · ${video.width}x${video.height} · ${Number(video.duration_s).toFixed(2)}s`;
  renderQueue();
  renderSummary();
  setReviewStatus();
  setTimeout(() => {
    resizeCanvasToVideo();
    drawZone();
    drawTimeline();
  }, 100);
}

function setReviewStatus() {
  const video = currentVideo();
  if (!video) return;
  const marker = markerFor(video.video_id);
  const labels = {
    "✓": "Reviewed",
    E: "Partial: event saved, segment missing",
    S: "Partial: segment saved, event missing",
    "○": "Needs review",
  };
  const status = eventStatus(video.video_id);
  if (marker === "E" && status.hasPhysical && !status.hasRisk) {
    els.reviewStatus.textContent = "Partial: physical entry saved, risk onset missing";
  } else if (marker === "E" && status.hasRisk && !status.hasPhysical) {
    els.reviewStatus.textContent = "Partial: risk onset saved, physical entry missing";
  } else {
    els.reviewStatus.textContent = labels[marker] || "Needs review";
  }
}

function activeRows() {
  const video = currentVideo();
  if (!video) return { segments: [], events: [] };
  return {
    segments: state.data.segments.filter((row) => row.video_id === video.video_id),
    events: state.data.events.filter((row) => row.video_id === video.video_id),
  };
}

function renderSummary() {
  if (!state.data || !currentVideo()) return;
  const { segments, events } = activeRows();
  const lines = [];
  lines.push(segments.length ? "Segments:" : "Segments: none");
  for (const row of segments.slice(-5)) {
    lines.push(`  ${row.start_s}-${row.end_s}s | ${row.attention} | ${row.blouse}`);
  }
  lines.push(events.length ? "Events:" : "Events: none");
  for (const row of events.slice(-5)) {
    const when = row.event_time_s ? `${row.event_time_s}s` : "whole clip";
    const role = normalizedEventRole(row);
    lines.push(`  ${role} @ ${when} | ${row.event_type} | ${row.body_part} | ${row.spatial_relation}`);
  }
  els.savedSummary.textContent = lines.join("\n");
}

function renderActiveButtons() {
  document.querySelectorAll("[data-group='attention'] button").forEach((button) => {
    button.classList.toggle("active", button.dataset.value === state.labels.attention);
  });
  document.querySelectorAll("[data-group='blouse'] button").forEach((button) => {
    button.classList.toggle("active", button.dataset.value === state.labels.blouse);
  });
  document.querySelectorAll("[data-group='eventRole'] button").forEach((button) => {
    button.classList.toggle("active", button.dataset.value === state.labels.eventRole);
  });
  document.querySelectorAll(".sourceCheck").forEach((input) => {
    input.checked = state.labels.sources.has(input.value);
  });
  els.spatialSelect.value = state.labels.spatial;
  els.eventTypeSelect.value = state.labels.eventType;
}

function playbackRate() {
  return Number(els.speedSelect.value.replace("x", "")) || 1;
}

function stepFrame(delta) {
  const video = currentVideo();
  if (!video) return;
  const fps = Number(video.fps || 30);
  const currentFrame = Math.round((els.video.currentTime || 0) * fps);
  seekToFrame(currentFrame + delta);
}

function jumpSeconds(delta) {
  seekToTime((els.video.currentTime || 0) + delta);
}

function clampTime(time) {
  const video = currentVideo();
  const duration = els.video.duration || Number(video?.duration_s || 0);
  return Math.max(0, Math.min(duration, Number(time) || 0));
}

function snapTimeToFrame(time) {
  const video = currentVideo();
  const fps = Number(video?.fps || 30);
  return Math.round(clampTime(time) * fps) / fps;
}

function scrubberTimeFromClientX(clientX) {
  const rect = els.scrubber.getBoundingClientRect();
  const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / Math.max(1, rect.width)));
  const video = currentVideo();
  const duration = els.video.duration || Number(video?.duration_s || 0);
  return ratio * duration;
}

function seekToTime(time) {
  els.video.pause();
  const target = snapTimeToFrame(time);
  els.video.currentTime = target;
  els.scrubber.value = String(target);
  updateTimeReadout(target);
  drawTimelineAtTime(target);
  requestAnimationFrame(() => {
    els.scrubber.value = String(target);
    updateTimeReadout(target);
    drawTimelineAtTime(target);
  });
}

function drawTimelineAtTime(time) {
  const previous = state.previewTime;
  state.previewTime = time;
  drawTimeline();
  state.previewTime = previous;
}

function seekToFrame(frame) {
  const video = currentVideo();
  if (!video) return;
  const fps = Number(video.fps || 30);
  const maxFrame = Math.max(0, Number(video.frames || 1) - 1);
  const targetFrame = Math.max(0, Math.min(maxFrame, Math.round(frame)));
  seekToTime(targetFrame / fps);
}

function updateTimeReadout(time = els.video.currentTime || 0) {
  const duration = els.video.duration || Number(currentVideo()?.duration_s || 0);
  const fps = Number(currentVideo()?.fps || 30);
  const frame = Math.round(time * fps);
  els.timeReadout.textContent = `${time.toFixed(3)}s / ${duration.toFixed(2)}s | frame ${frame}`;
}

function nextVideo(delta) {
  const queue = state.filtered.length ? state.filtered : state.data.videos.map((_, index) => index);
  const pos = queue.indexOf(state.currentIndex);
  const nextPos = Math.max(0, Math.min(queue.length - 1, (pos >= 0 ? pos : 0) + delta));
  loadVideo(queue[nextPos]);
}

function selectedSources() {
  const sources = [...state.labels.sources];
  return sources.length ? sources.join("|") : "hand_or_arm";
}

async function saveWholeSegment() {
  const video = currentVideo();
  if (!video) return;
  await api("/api/segments", {
    method: "POST",
    body: JSON.stringify({
      video_id: video.video_id,
      start_s: "0.000",
      end_s: Number(video.duration_s).toFixed(3),
      attention: state.labels.attention,
      blouse: state.labels.blouse,
      notes: els.notesInput.value.trim(),
    }),
  });
}

function startSegment() {
  state.segmentStart = els.video.currentTime;
  els.savedSummary.textContent = `Segment start: ${state.segmentStart.toFixed(3)}s`;
}

async function endSegment() {
  const video = currentVideo();
  if (!video || state.segmentStart === null) return;
  const start = Math.min(state.segmentStart, els.video.currentTime);
  const end = Math.max(state.segmentStart, els.video.currentTime);
  state.segmentStart = null;
  if (end - start < 0.03) return;
  await api("/api/segments", {
    method: "POST",
    body: JSON.stringify({
      video_id: video.video_id,
      start_s: start.toFixed(3),
      end_s: end.toFixed(3),
      attention: state.labels.attention,
      blouse: state.labels.blouse,
      notes: els.notesInput.value.trim(),
    }),
  });
}

async function markDanger(role = state.labels.eventRole) {
  const video = currentVideo();
  if (!video) return;
  state.labels.eventRole = role;
  const frame = Math.round(els.video.currentTime * Number(video.fps || 30));
  await api("/api/events", {
    method: "POST",
    body: JSON.stringify({
      video_id: video.video_id,
      event_time_s: els.video.currentTime.toFixed(3),
      frame: String(frame),
      event_role: role,
      body_part: selectedSources(),
      event_type: state.labels.eventType,
      zone_id: "machine_danger_volume",
      spatial_relation: state.labels.spatial,
      notes: els.notesInput.value.trim(),
    }),
  });
  renderActiveButtons();
}

async function markNoDanger() {
  const video = currentVideo();
  if (!video) return;
  await api("/api/events", {
    method: "POST",
    body: JSON.stringify({
      video_id: video.video_id,
      event_time_s: "",
      frame: "",
      event_role: "no_danger",
      body_part: "none",
      event_type: "no_danger_event",
      zone_id: "machine_danger_volume",
      spatial_relation: "outside_volume",
      notes: els.notesInput.value.trim(),
    }),
  });
}

async function resetClip() {
  const video = currentVideo();
  if (!video) return;
  const payload = await api("/api/reset-clip", {
    method: "POST",
    body: JSON.stringify({ video_id: video.video_id }),
  });
  state.segmentStart = null;
  els.savedSummary.textContent = `Reset clip: removed ${payload.removed_events} event(s), ${payload.removed_segments} segment(s).`;
  setReviewStatus();
  drawTimeline();
}

function zone() {
  const zones = state.data?.zones?.zones || [];
  if (!zones.length) {
    const video = currentVideo();
    zones.push({
      zone_id: "machine_danger_volume",
      shape: "projected_volume_polygon",
      image_width: Number(video?.width || 1440),
      image_height: Number(video?.height || 720),
      points: [],
    });
    state.data.zones = { zones };
  }
  return zones[0];
}

function resizeCanvasToVideo() {
  const rect = els.video.getBoundingClientRect();
  els.zoneCanvas.style.width = `${rect.width}px`;
  els.zoneCanvas.style.height = `${rect.height}px`;
  els.zoneCanvas.width = Math.max(1, Math.round(rect.width));
  els.zoneCanvas.height = Math.max(1, Math.round(rect.height));
}

function drawZone() {
  if (!els.zoneCanvas || !currentVideo()) return;
  resizeCanvasToVideo();
  const ctx = els.zoneCanvas.getContext("2d");
  const z = zone();
  const video = currentVideo();
  const sx = els.zoneCanvas.width / Number(video.width || 1440);
  const sy = els.zoneCanvas.height / Number(video.height || 720);
  ctx.clearRect(0, 0, els.zoneCanvas.width, els.zoneCanvas.height);
  const points = z.points || [];
  if (points.length >= 2) {
    ctx.beginPath();
    points.forEach(([x, y], index) => {
      const px = x * sx;
      const py = y * sy;
      if (index === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    if (points.length >= 3) ctx.closePath();
    ctx.fillStyle = "rgba(214, 63, 58, 0.18)";
    ctx.strokeStyle = "#f3b64a";
    ctx.lineWidth = 3;
    if (points.length >= 3) ctx.fill();
    ctx.stroke();
  }
  points.forEach(([x, y], index) => {
    const px = x * sx;
    const py = y * sy;
    ctx.beginPath();
    ctx.arc(px, py, 7, 0, Math.PI * 2);
    ctx.fillStyle = "#f3b64a";
    ctx.strokeStyle = "#111";
    ctx.lineWidth = 2;
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#fff";
    ctx.font = "12px Segoe UI";
    ctx.fillText(String(index + 1), px + 10, py - 8);
  });
  if (state.zoneEdit) {
    ctx.fillStyle = "rgba(0,0,0,.65)";
    ctx.fillRect(10, 10, 420, 28);
    ctx.fillStyle = "#fff";
    ctx.font = "13px Segoe UI";
    ctx.fillText("Zone edit: drag points · click empty area add · right-click delete", 18, 29);
  }
}

function canvasPointToVideo(x, y) {
  const video = currentVideo();
  return [
    Math.max(0, Math.min(Number(video.width) - 1, Math.round(x * Number(video.width) / els.zoneCanvas.width))),
    Math.max(0, Math.min(Number(video.height) - 1, Math.round(y * Number(video.height) / els.zoneCanvas.height))),
  ];
}

function nearestZonePoint(x, y) {
  const z = zone();
  const video = currentVideo();
  const sx = els.zoneCanvas.width / Number(video.width || 1440);
  const sy = els.zoneCanvas.height / Number(video.height || 720);
  let nearest = null;
  let best = 13 * 13;
  z.points.forEach(([px, py], index) => {
    const dx = px * sx - x;
    const dy = py * sy - y;
    const dist = dx * dx + dy * dy;
    if (dist < best) {
      best = dist;
      nearest = index;
    }
  });
  return nearest;
}

async function saveZone() {
  const z = zone();
  const video = currentVideo();
  z.image_width = Number(video.width);
  z.image_height = Number(video.height);
  await api("/api/zones", {
    method: "POST",
    body: JSON.stringify(state.data.zones),
  });
  state.zoneEdit = false;
  drawZone();
}

function timelineTimeFromX(x) {
  const rect = els.timelineCanvas.getBoundingClientRect();
  const left = 64;
  const right = rect.width - 16;
  const ratio = Math.max(0, Math.min(1, (x - left) / Math.max(1, right - left)));
  return ratio * (els.video.duration || Number(currentVideo()?.duration_s || 0));
}

function timelineXFromTime(time) {
  const rect = els.timelineCanvas.getBoundingClientRect();
  const left = 64;
  const right = rect.width - 16;
  const duration = els.video.duration || Number(currentVideo()?.duration_s || 1);
  return left + Math.max(0, Math.min(1, time / duration)) * (right - left);
}

function drawTimeline() {
  if (!currentVideo()) return;
  const canvas = els.timelineCanvas;
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.max(1, Math.round(rect.width));
  canvas.height = Math.max(1, Math.round(rect.height));
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  const left = 64;
  const right = w - 16;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, w, h);
  ctx.fillStyle = "#607086";
  ctx.font = "13px Segoe UI";
  ctx.fillText("Entry", 12, 23);
  ctx.fillText("Risk", 12, 50);
  ctx.fillText("Segments", 12, 78);
  ctx.strokeStyle = "#d8dee7";
  ctx.beginPath();
  ctx.moveTo(left, 24);
  ctx.lineTo(right, 24);
  ctx.moveTo(left, 50);
  ctx.lineTo(right, 50);
  ctx.moveTo(left, 78);
  ctx.lineTo(right, 78);
  ctx.stroke();
  const duration = els.video.duration || Number(currentVideo().duration_s || 0);
  for (let i = 0; i <= 4; i++) {
    const x = left + (right - left) * (i / 4);
    ctx.strokeStyle = "#edf1f5";
    ctx.beginPath();
    ctx.moveTo(x, 16);
    ctx.lineTo(x, 92);
    ctx.stroke();
    ctx.fillStyle = "#8490a1";
    ctx.font = "12px Segoe UI";
    ctx.fillText(`${(duration * i / 4).toFixed(1)}s`, x - 12, 108);
  }
  const { segments, events } = activeRows();
  for (const segment of segments) {
    const x1 = timelineXFromTime(Number(segment.start_s || 0));
    const x2 = timelineXFromTime(Number(segment.end_s || 0));
    ctx.fillStyle = segment.attention === "distracted" ? "#d58a00" : segment.blouse === "badly_worn" ? "#12a5b4" : "#168a5b";
    ctx.fillRect(x1, 66, Math.max(3, x2 - x1), 22);
  }
  state.timelineMarkers = [];
  for (const event of events) {
    if (event.event_type === "no_danger_event") continue;
    if (!event.event_time_s) continue;
    const role = normalizedEventRole(event);
    const t = Number(event.event_time_s);
    const x = timelineXFromTime(t);
    const isRisk = role === "risk_onset";
    const color = isRisk ? "#d58a00" : "#d63f3a";
    const labelColor = isRisk ? "#8a5a00" : "#8a1f17";
    const trackY = isRisk ? 50 : 24;
    ctx.fillStyle = color;
    ctx.beginPath();
    if (isRisk) {
      ctx.moveTo(x, trackY - 12);
      ctx.lineTo(x + 8, trackY - 4);
      ctx.lineTo(x, trackY + 4);
      ctx.lineTo(x - 8, trackY - 4);
    } else {
      ctx.moveTo(x, trackY - 15);
      ctx.lineTo(x - 8, trackY - 1);
      ctx.lineTo(x + 8, trackY - 1);
    }
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x, trackY);
    ctx.lineTo(x, 92);
    ctx.stroke();
    ctx.fillStyle = labelColor;
    ctx.font = "12px Segoe UI";
    ctx.fillText(`${isRisk ? "risk" : "entry"} ${event.body_part || ""}`.trim(), x + 8, trackY - 7);
    state.timelineMarkers.push({ x, y: trackY, event });
  }
  const playX = timelineXFromTime(state.previewTime ?? els.video.currentTime ?? 0);
  ctx.strokeStyle = "#1864ff";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(playX, 6);
  ctx.lineTo(playX, h - 10);
  ctx.stroke();
}

async function updateEventTime(rowIndex, time) {
  const video = currentVideo();
  const frame = Math.round(time * Number(video.fps || 30));
  await api(`/api/events/${rowIndex}`, {
    method: "PUT",
    body: JSON.stringify({
      event_time_s: time.toFixed(3),
      frame: String(frame),
    }),
  });
}

function initEvents() {
  Object.assign(els, {
    searchInput: qs("searchInput"),
    filterSelect: qs("filterSelect"),
    videoList: qs("videoList"),
    progressText: qs("progressText"),
    video: qs("video"),
    zoneCanvas: qs("zoneCanvas"),
    timelineCanvas: qs("timelineCanvas"),
    scrubber: qs("scrubber"),
    workspaceTitle: qs("workspaceTitle"),
    clipMeta: qs("clipMeta"),
    reviewStatus: qs("reviewStatus"),
    playBtn: qs("playBtn"),
    speedSelect: qs("speedSelect"),
    autoNext: qs("autoNext"),
    timeReadout: qs("timeReadout"),
    cacheStatus: qs("cacheStatus"),
    spatialSelect: qs("spatialSelect"),
    eventTypeSelect: qs("eventTypeSelect"),
    notesInput: qs("notesInput"),
    savedSummary: qs("savedSummary"),
    stageStatus: qs("stageStatus"),
  });

  els.searchInput.addEventListener("input", renderQueue);
  els.filterSelect.addEventListener("change", renderQueue);
  qs("prevBtn").addEventListener("click", () => nextVideo(-1));
  qs("nextBtn").addEventListener("click", () => nextVideo(1));
  qs("playBtn").addEventListener("click", () => els.video.paused ? els.video.play() : els.video.pause());
  qs("prevFrameBtn").addEventListener("click", () => stepFrame(-1));
  qs("nextFrameBtn").addEventListener("click", () => stepFrame(1));
  qs("backSecBtn").addEventListener("click", () => jumpSeconds(-1));
  qs("fwdSecBtn").addEventListener("click", () => jumpSeconds(1));
  qs("reviewBtn").addEventListener("click", startReview);
  qs("prepareCacheBtn").addEventListener("click", prepareAllClips);
  qs("startSegmentBtn").addEventListener("click", startSegment);
  qs("endSegmentBtn").addEventListener("click", endSegment);
  qs("wholeSegmentBtn").addEventListener("click", saveWholeSegment);
  qs("markPhysicalBtn").addEventListener("click", () => markDanger("physical_entry"));
  qs("markRiskBtn").addEventListener("click", () => markDanger("risk_onset"));
  qs("noDangerBtn").addEventListener("click", markNoDanger);
  qs("resetClipBtn").addEventListener("click", resetClip);
  qs("undoEventBtn").addEventListener("click", () => api("/api/undo-event", { method: "POST", body: JSON.stringify({ video_id: currentVideo().video_id }) }));
  qs("undoSegmentBtn").addEventListener("click", () => api("/api/undo-segment", { method: "POST", body: JSON.stringify({ video_id: currentVideo().video_id }) }));
  qs("zoneEditBtn").addEventListener("click", () => { state.zoneEdit = !state.zoneEdit; drawZone(); });
  qs("saveZoneBtn").addEventListener("click", saveZone);

  document.querySelectorAll("[data-group='attention'] button").forEach((button) => {
    button.addEventListener("click", () => {
      state.labels.attention = button.dataset.value;
      renderActiveButtons();
    });
  });
  document.querySelectorAll("[data-group='blouse'] button").forEach((button) => {
    button.addEventListener("click", () => {
      state.labels.blouse = button.dataset.value;
      renderActiveButtons();
    });
  });
  document.querySelectorAll("[data-group='eventRole'] button").forEach((button) => {
    button.addEventListener("click", () => {
      state.labels.eventRole = button.dataset.value;
      renderActiveButtons();
    });
  });
  document.querySelectorAll(".sourceCheck").forEach((input) => {
    input.addEventListener("change", () => {
      if (input.checked) state.labels.sources.add(input.value);
      else {
        state.labels.sources.delete(input.value);
        if (!state.labels.sources.size) {
          state.labels.sources.add(input.value);
          input.checked = true;
        }
      }
    });
  });
  els.spatialSelect.addEventListener("change", () => state.labels.spatial = els.spatialSelect.value);
  els.eventTypeSelect.addEventListener("change", () => state.labels.eventType = els.eventTypeSelect.value);
  els.speedSelect.addEventListener("change", () => els.video.playbackRate = playbackRate());

  els.video.addEventListener("loadedmetadata", () => {
    els.scrubber.max = String(els.video.duration || 1);
    els.scrubber.step = String(1 / Number(currentVideo()?.fps || 30));
    els.stageStatus.hidden = true;
    resizeCanvasToVideo();
    drawZone();
    drawTimeline();
    updateTimeReadout(els.video.currentTime || 0);
  });
  els.video.addEventListener("error", () => {
    els.stageStatus.hidden = false;
    els.stageStatus.textContent = "Video failed to load. Refresh or try another clip.";
  });
  els.video.addEventListener("timeupdate", () => {
    if (!state.scrubbing) {
      els.scrubber.value = String(els.video.currentTime);
    }
    updateTimeReadout(els.video.currentTime);
    drawTimeline();
  });
  els.video.addEventListener("seeked", () => {
    if (!state.scrubbing) {
      els.scrubber.value = String(els.video.currentTime);
    }
    updateTimeReadout(els.video.currentTime);
    drawTimeline();
  });
  els.video.addEventListener("ended", () => {
    if (els.autoNext.checked) nextVideo(1);
  });
  els.scrubber.addEventListener("pointerdown", (event) => {
    state.scrubbing = true;
    if (els.scrubber.setPointerCapture) els.scrubber.setPointerCapture(event.pointerId);
    seekToTime(scrubberTimeFromClientX(event.clientX));
    event.preventDefault();
  });
  els.scrubber.addEventListener("pointermove", (event) => {
    if (!state.scrubbing) return;
    seekToTime(scrubberTimeFromClientX(event.clientX));
    event.preventDefault();
  });
  els.scrubber.addEventListener("input", () => {
    seekToTime(Number(els.scrubber.value));
  });
  els.scrubber.addEventListener("change", () => {
    seekToTime(Number(els.scrubber.value));
  });
  window.addEventListener("pointerup", () => {
    if (!state.scrubbing) return;
    state.scrubbing = false;
    seekToTime(Number(els.scrubber.value));
  });

  window.addEventListener("resize", () => {
    resizeCanvasToVideo();
    drawZone();
    drawTimeline();
  });

  wireCanvasInteractions();
  wireTimelineInteractions();
  wireShortcuts();
  refreshCacheStatus();
}

async function refreshCacheStatus() {
  try {
    const payload = await api("/api/cache/status");
    renderCacheStatus(payload.cache);
    if (payload.cache.running) {
      setTimeout(refreshCacheStatus, 1500);
    }
  } catch (error) {
    els.cacheStatus.textContent = `Cache status unavailable: ${error.message}`;
  }
}

function renderCacheStatus(cache) {
  if (!cache) return;
  const mb = cache.cached_bytes ? (cache.cached_bytes / 1024 / 1024).toFixed(1) : "0.0";
  if (cache.running) {
    els.cacheStatus.textContent = `Preparing clips ${cache.done}/${cache.total}: ${cache.current || "starting"} (${cache.cached_files} cached, ${mb} MB)`;
  } else {
    els.cacheStatus.textContent = `Browser-playable cache: ${cache.cached_files} clips, ${mb} MB. Use Prepare All Clips once to remove first-open delays.`;
  }
}

async function prepareAllClips() {
  const payload = await api("/api/cache/start", { method: "POST", body: "{}" });
  renderCacheStatus(payload.cache);
  setTimeout(refreshCacheStatus, 1000);
}

function startReview() {
  els.speedSelect.value = "8x";
  els.autoNext.checked = true;
  els.video.playbackRate = 8;
  els.video.play();
}

function wireCanvasInteractions() {
  els.zoneCanvas.addEventListener("pointerdown", (event) => {
    if (!state.zoneEdit) return;
    event.preventDefault();
    const rect = els.zoneCanvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const z = zone();
    const nearest = nearestZonePoint(x, y);
    if (event.button === 2) {
      if (nearest !== null) z.points.splice(nearest, 1);
      drawZone();
      return;
    }
    if (nearest === null) {
      z.points.push(canvasPointToVideo(x, y));
      state.dragZoneIndex = z.points.length - 1;
    } else {
      state.dragZoneIndex = nearest;
    }
    drawZone();
  });
  els.zoneCanvas.addEventListener("pointermove", (event) => {
    if (!state.zoneEdit || state.dragZoneIndex === null) return;
    const rect = els.zoneCanvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    zone().points[state.dragZoneIndex] = canvasPointToVideo(x, y);
    drawZone();
  });
  window.addEventListener("pointerup", () => {
    state.dragZoneIndex = null;
  });
  els.zoneCanvas.addEventListener("contextmenu", (event) => event.preventDefault());
}

function wireTimelineInteractions() {
  els.timelineCanvas.addEventListener("pointerdown", (event) => {
    const rect = els.timelineCanvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const marker = (state.timelineMarkers || []).find((m) => Math.abs(m.x - x) < 10 && Math.abs((m.y || 24) - y) < 18);
    if (marker) {
      state.dragEventIndex = Number(marker.event._row_index);
    } else {
      state.dragEventIndex = null;
    }
    seekToTime(timelineTimeFromX(x));
  });
  els.timelineCanvas.addEventListener("pointermove", (event) => {
    if (state.dragEventIndex === null) return;
    const rect = els.timelineCanvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    seekToTime(timelineTimeFromX(x));
  });
  window.addEventListener("pointerup", async () => {
    if (state.dragEventIndex === null) return;
    const idx = state.dragEventIndex;
    state.dragEventIndex = null;
    await updateEventTime(idx, els.video.currentTime);
  });
}

function wireShortcuts() {
  window.addEventListener("keydown", async (event) => {
    const active = document.activeElement;
    const typingTarget = active && (
      active.tagName === "TEXTAREA" ||
      (active.tagName === "INPUT" && !["range", "checkbox", "button"].includes(active.type))
    );
    if (typingTarget) return;
    let handled = true;
    if (event.key === " ") els.video.paused ? els.video.play() : els.video.pause();
    else if (event.key === "ArrowLeft") event.shiftKey ? jumpSeconds(-1) : stepFrame(-1);
    else if (event.key === "ArrowRight") event.shiftKey ? jumpSeconds(1) : stepFrame(1);
    else if (event.key.toLowerCase() === "n") nextVideo(1);
    else if (event.key.toLowerCase() === "p") nextVideo(-1);
    else if (event.key.toLowerCase() === "f") startReview();
    else if (event.key.toLowerCase() === "a") state.labels.attention = "attentive";
    else if (event.key.toLowerCase() === "d") state.labels.attention = "distracted";
    else if (event.key.toLowerCase() === "r") state.labels.blouse = "properly_worn";
    else if (event.key.toLowerCase() === "b") state.labels.blouse = "badly_worn";
    else if (event.key === "1") toggleSource("hand_or_arm");
    else if (event.key === "2") toggleSource("head");
    else if (event.key.toLowerCase() === "s" && !event.ctrlKey) startSegment();
    else if (event.key.toLowerCase() === "e") await endSegment();
    else if (event.key.toLowerCase() === "w") await saveWholeSegment();
    else if (event.key.toLowerCase() === "m") await markDanger("physical_entry");
    else if (event.key.toLowerCase() === "o") await markDanger("risk_onset");
    else if (event.key.toLowerCase() === "g") await markNoDanger();
    else if (event.key.toLowerCase() === "x") await resetClip();
    else if (event.key.toLowerCase() === "z" && !event.ctrlKey) { state.zoneEdit = !state.zoneEdit; drawZone(); }
    else if (event.key.toLowerCase() === "s" && event.ctrlKey) await saveZone();
    else handled = false;
    if (handled) event.preventDefault();
    renderActiveButtons();
  });
}

function toggleSource(source) {
  if (state.labels.sources.has(source)) state.labels.sources.delete(source);
  else state.labels.sources.add(source);
  if (!state.labels.sources.size) state.labels.sources.add(source);
  renderActiveButtons();
}

initEvents();
loadState();
