// The play-along: the score scrolls and lights up each note as the recording plays.
// Timing comes from the server's sync pairs (score position in quarter notes <-> seconds),
// built from the exact onsets in notes.json and the beat grid.
const takeId = location.pathname.split('/').pop();
const audio = $('#audio');
let size = 1;
try { size = parseInt(localStorage.getItem('saxscribe-size') ?? '1', 10); } catch (e) {}
if (!(size >= 0 && size <= 3)) size = 1;
let job, view, sync = [], starts = [], measures = [], qOf = {}, lit = [], litMeasure = null, follow = true;

// ---- time <-> score position, straight lines between sync points, extended past both ends
function interp(x, xs, ys) {
  const n = xs.length;
  if (n === 0) return x;
  if (n === 1) return ys[0] + (x - xs[0]);
  let lo = 0, hi = n - 1;
  if (x <= xs[0]) { hi = 1; } else if (x >= xs[n - 1]) { lo = n - 2; }
  else { while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (xs[mid] <= x) lo = mid; else hi = mid; } }
  return ys[lo] + (x - xs[lo]) * (ys[hi] - ys[lo]) / (xs[hi] - xs[lo]);
}
let Q = [], T = [];
const qToT = q => interp(q, Q, T);
const tToQ = t => interp(t, T, Q);

function lastAtOrBefore(list, q) {
  let lo = 0, hi = list.length - 1, best = -1;
  while (lo <= hi) { const mid = (lo + hi) >> 1; if (list[mid].q <= q + 1e-6) { best = mid; lo = mid + 1; } else hi = mid - 1; }
  return best;
}

// ---- loading
async function loadJob() {
  job = await (await fetch(`/api/takes/${takeId}`)).json();
  $('#name').textContent = job.title;
  document.title = `${job.title} · Saxscribe`;
  const views = [job.horn, ...['alto', 'tenor', 'concert'].filter(v => v !== job.horn)];
  $('#view').innerHTML = views.map((v, i) => `<button type="button" data-v="${v}" class="${i ? '' : 'on'}">${HORN_NAMES[v] || v}</button>`).join('');
  segment($('#view'), v => loadScore(v));
  if (job.mix) {
    $('#audioSel').hidden = false;
    segment($('#audioSel'), which => setAudio(which));
  }
  setAudio('source');
  await loadScore(job.horn);
}

function setAudio(which) {
  const at = audio.currentTime || 0, playing = !audio.paused;
  audio.src = `/api/takes/${takeId}/audio/${which}`;
  audio.addEventListener('loadedmetadata', () => {
    audio.currentTime = at; setSpeed();
    if (playing) audio.play();
  }, {once: true});
}

async function loadScore(v) {
  view = v;
  const box = $('#score');
  box.innerHTML = '<div class="loading">Drawing the score…</div>';
  const r = await fetch(`/api/takes/${takeId}/score?view=${v}&size=${size}`);
  if (!r.ok) { box.innerHTML = `<div class="loading">Could not draw the score: ${esc((await r.json()).detail || r.status)}</div>`; return; }
  const data = await r.json();
  box.innerHTML = data.svg;
  Q = data.sync.map(p => p[0]); T = data.sync.map(p => p[1]);
  starts = []; measures = []; qOf = {}; lit = []; litMeasure = null;
  for (const e of data.timemap) {
    if (e.measureOn) measures.push({q: e.qstamp, id: e.measureOn});
    const ids = (e.on || []).filter(id => { const el = document.getElementById(id); return el && el.classList.contains('note'); });
    for (const id of (e.on || [])) qOf[id] = e.qstamp;
    if (ids.length) starts.push({q: e.qstamp, ids});
  }
  update(true);
}

// ---- drawing the playhead
function update(force) {
  const t = audio.currentTime || 0, d = audio.duration || 0;
  $('#time').textContent = `${clock(t)} / ${clock(d)}`;
  if (!seeking) { $('#seek').max = d || 1; $('#seek').value = t; }
  const q = tToQ(t);
  const i = lastAtOrBefore(starts, q);
  const ids = i >= 0 && (audio.currentTime > 0 || !audio.paused) ? starts[i].ids : [];
  if (force || ids !== lit) {
    lit.forEach(id => { const el = document.getElementById(id); if (el) el.classList.remove('now'); });
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.classList.add('now'); });
    lit = ids;
  }
  const m = lastAtOrBefore(measures, q);
  const mid = m >= 0 ? measures[m].id : null;
  if (mid !== litMeasure || force) { litMeasure = mid; if (follow && mid) keepInView(document.getElementById(mid)); }
}
function keepInView(measure) {
  if (!measure) return;
  const system = measure.closest('g.system') || measure;
  const r = system.getBoundingClientRect();
  const head = $('.top').getBoundingClientRect().bottom, foot = $('.transport').getBoundingClientRect().top;
  if (r.top < head + 8 || r.bottom > foot - 8 || r.top > head + (foot - head) * 0.55) {
    window.scrollTo({top: window.scrollY + r.top - head - 16, behavior: 'smooth'});
  }
}
function clock(s) { s = Math.max(0, s || 0); return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`; }
function loop() { update(false); if (!audio.paused) requestAnimationFrame(loop); }

// ---- controls
function setSpeed() {
  audio.playbackRate = parseFloat($('#speed').value);
  audio.preservesPitch = true; audio.webkitPreservesPitch = true; audio.mozPreservesPitch = true;
}
function toggle() { if (audio.paused) audio.play(); else audio.pause(); }
$('#play').addEventListener('click', toggle);
audio.addEventListener('play', () => { $('#play').textContent = '❚❚'; $('#play').setAttribute('aria-label', 'Pause'); requestAnimationFrame(loop); });
audio.addEventListener('pause', () => { $('#play').textContent = '▶'; $('#play').setAttribute('aria-label', 'Play'); update(false); });
audio.addEventListener('timeupdate', () => { if (audio.paused) update(false); });
audio.addEventListener('loadedmetadata', () => update(false));
$('#speed').addEventListener('change', setSpeed);
let seeking = false;
$('#seek').addEventListener('input', () => { seeking = true; audio.currentTime = parseFloat($('#seek').value); update(false); });
$('#seek').addEventListener('change', () => { seeking = false; });
$('#follow').addEventListener('click', () => {
  follow = !follow; $('#follow').classList.toggle('on', follow); $('#follow').setAttribute('aria-pressed', follow);
  $('#follow').classList.toggle('primary', follow);
  if (follow) update(true);
});
$('#follow').classList.add('primary');
// Tap a note to jump there.
$('#score').addEventListener('click', e => {
  const g = e.target.closest('g.note, g.rest, g.chord');
  if (!g || qOf[g.id] === undefined) return;
  audio.currentTime = Math.max(0, qToT(qOf[g.id]) - 0.05);
  update(true);
});
document.addEventListener('keydown', e => {
  if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'SELECT') { e.preventDefault(); toggle(); }
});
function resize(by) {
  const next = Math.max(0, Math.min(3, size + by));
  if (next === size) return;
  size = next;
  try { localStorage.setItem('saxscribe-size', String(size)); } catch (e) {}
  loadScore(view);
}
$('#smaller').addEventListener('click', () => resize(-1));
$('#bigger').addEventListener('click', () => resize(1));
document.addEventListener('click', e => { if (!e.target.closest('#dl')) $('#dl').open = false; });
$('#dl').addEventListener('click', e => { if (e.target.closest('.list button')) $('#dl').open = false; });
$('#pdf').addEventListener('click', () => download(`/api/takes/${takeId}/file/pdf?view=${view}`));
$('#xml').addEventListener('click', () => download(`/api/takes/${takeId}/file/musicxml?view=${view}`));
$('#midi').addEventListener('click', () => download(`/api/takes/${takeId}/file/midi`));

loadJob().catch(err => { $('#score').innerHTML = `<div class="loading">Could not load this take: ${esc(err.message)}</div>`; });
