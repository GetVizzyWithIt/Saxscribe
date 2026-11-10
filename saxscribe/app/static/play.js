// The play-along: the score scrolls and lights up each note as the recording plays.
// Timing comes from the server's sync pairs (score position in quarter notes <-> seconds),
// built from the exact onsets in notes.json and the beat grid.
// Below the scroller: feedback. Flag bars while it plays, sort the flags afterwards, and
// keep a tracker of what was flagged on which run (server: flags.py).
const takeId = location.pathname.split('/').pop();
const audio = $('#audio');
let size = 1;
try { size = parseInt(localStorage.getItem('saxscribe-size') ?? '1', 10); } catch (e) {}
if (!(size >= 0 && size <= 3)) size = 1;
let barOf = {};
let job, view, starts = [], measures = [], qOf = {}, lit = [], litMeasure = null, follow = true, nBars = 1;
const BEATS = 4;  // quarter notes per bar (layers/notation.py BEATS_PER_BAR)

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
const barStart = b => Math.max(0, qToT((b - 1) * BEATS));
const barEnd = b => qToT(b * BEATS);

function lastAtOrBefore(list, q) {
  let lo = 0, hi = list.length - 1, best = -1;
  while (lo <= hi) { const mid = (lo + hi) >> 1; if (list[mid].q <= q + 1e-6) { best = mid; lo = mid + 1; } else hi = mid - 1; }
  return best;
}

// ---- loading. The chart is always the horn it was made for; transposing will live in the library.
async function loadJob() {
  job = await (await fetch(`/api/takes/${takeId}`)).json();
  document.title = `${job.title} · Saxscribe`;
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
    if (playing) playAudio();
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
  starts = []; measures = []; qOf = {}; barOf = {}; lit = []; litMeasure = null;
  // Verovio's clock can slip by a tuplet note (a tie inside a 16th triplet loses 1/6 beat), which
  // put later bars one number low. Every bar starts on a whole bar in notation.json, so re-anchor
  // each bar to the nearest bar line and carry that correction to the notes inside it.
  let shift = 0;
  for (const e of data.timemap) {
    if (e.measureOn) {
      const at = Math.round(e.qstamp / BEATS) * BEATS;
      shift = at - e.qstamp;
      measures.push({q: at, id: e.measureOn}); barOf[e.measureOn] = at / BEATS + 1;
    }
    const q = e.qstamp + shift;
    const ids = (e.on || []).filter(id => { const el = document.getElementById(id); return el && el.classList.contains('note'); });
    for (const id of (e.on || [])) qOf[id] = q;
    if (ids.length) starts.push({q, ids});
  }
  nBars = Math.max(1, ...Object.values(barOf));
  update(true);
  drawFlags(); drawStrip();
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
  if (mid !== litMeasure || force) { litMeasure = mid; if (follow && mid && !selecting) keepInView(document.getElementById(mid)); }
  tickReview();
}
function keepInView(measure) {
  if (!measure) return;
  const system = measure.closest('g.system') || measure;
  const r = system.getBoundingClientRect();
  const head = $('.top').getBoundingClientRect().bottom, foot = bottomEdge();
  if (r.top < head + 8 || r.bottom > foot - 8 || r.top > head + (foot - head) * 0.55) {
    window.scrollTo({top: window.scrollY + r.top - head - 16, behavior: 'smooth'});
  }
}
// The top of whatever covers the bottom of the page: the flag screen when open, else the transport.
function bottomEdge() { return (!$('#sheet').hidden ? $('#sheet') : $('.transport')).getBoundingClientRect().top; }
function clock(s) { s = Math.max(0, s || 0); return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`; }
function loop() {
  // A loop over the flag's bars while its flag screen is open.
  if (loopRange && audio.currentTime >= loopRange[1]) audio.currentTime = loopRange[0];
  update(false);
  if (!audio.paused) requestAnimationFrame(loop);
}

// ---- controls
function setSpeed() {
  audio.playbackRate = parseFloat($('#speed').value);
  audio.preservesPitch = true; audio.webkitPreservesPitch = true; audio.mozPreservesPitch = true;
}
// play() can be cut short by a pause (or refused before a tap); that's fine, not an error.
function playAudio() { const p = audio.play(); if (p && p.catch) p.catch(() => {}); }
function toggle() { if (audio.paused) playAudio(); else audio.pause(); }
function seekTo(t) { audio.currentTime = Math.max(0, t); update(true); }
$('#play').addEventListener('click', toggle);
audio.addEventListener('play', () => { $('#play').textContent = '❚❚'; $('#play').setAttribute('aria-label', 'Pause'); syncPlay(); requestAnimationFrame(loop); });
audio.addEventListener('pause', () => { $('#play').textContent = '▶'; $('#play').setAttribute('aria-label', 'Play'); syncPlay(); update(false); sendHeard(); });
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
$('#pdf').addEventListener('click', () => { location.href = `/take/${takeId}/pdf?view=${view}`; });
$('#xml').addEventListener('click', () => download(`/api/takes/${takeId}/file/musicxml?view=${view}`));
$('#midi').addEventListener('click', () => download(`/api/takes/${takeId}/file/midi`));

// ---- feedback. Flags never change the transcription; they go to flags.json next to the take,
// with a copy on the Desktop. Each one is saved against the run of the song it was made on.
let flags = [], past = [], categories = {}, GROUPS = {}, suggested = [], run = {}, flagsText = '';
let editing = null, heard = new Set(), heardSent = new Set(), lastUndo = null, loopRange = null, sortSpeed = null;
const groupOf = c => Object.keys(GROUPS).find(g => g === c || GROUPS[g].keys.includes(c));
const barAtTime = t => Math.max(1, Math.min(nBars, Math.floor(tToQ(t) / BEATS + 1e-6) + 1));
const nowBar = () => barAtTime(audio.currentTime || 0);
const flagFor = b => flags.find(f => b >= f.bar && b <= (f.to || f.bar));
const isSorted = f => !!((f.categories && f.categories.length) || f.text);
const rangeName = f => (f.to || f.bar) === f.bar ? `Bar ${f.bar}` : `Bars ${f.bar}–${f.to}`;
const toSort = () => flags.filter(f => !isSorted(f)).sort((a, b) => a.bar - b.bar);
const post = (url, body, method = 'POST') => fetch(url, {method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});

async function loadFlags() { const r = await fetch(`/api/takes/${takeId}/flags`); if (r.ok) gotFlags(await r.json()); }
function gotFlags(data) {
  flags = data.flags; past = data.past || []; categories = data.categories; GROUPS = data.groups || GROUPS;
  suggested = data.suggested || []; run = data.run || {}; flagsText = data.text;
  for (const b of (data.heard || [])) { heard.add(b); heardSent.add(b); }
  $('#runName').textContent = run.label || '…';
  const todo = toSort().length;
  $('#sortBtn').hidden = !todo; $('#sortBtn').textContent = `Sort ${todo} flag${todo === 1 ? '' : 's'}`;
  drawTracker(data.looks_right || []);
  drawFlags(); drawStrip();
  if (editing && editing.sorting) $('#saveFlag').textContent = saveLabel();
}
function label(f) {
  const gs = [...new Set(f.categories.map(groupOf).filter(Boolean))];
  const detail = f.categories.filter(c => !GROUPS[c] && GROUPS[groupOf(c)] && GROUPS[groupOf(c)].keys.length > 1).map(c => categories[c] || c);
  return gs.map(g => GROUPS[g].label).join(', ') + (detail.length ? ' · ' + detail.join(', ') : '');
}

// ---- the tracker: this run's flags, then earlier runs' flags and whether this run changed them
function drawTracker(okBars) {
  const row = f => `<tr data-id="${f.id}"><td class="b">${rangeName(f)}</td>` +
    `<td>${isSorted(f) ? esc(label(f) || 'Note only') : '<span class="quiet">not sorted yet</span>'}</td>` +
    `<td>${f.text ? esc(f.text) : '<span class="quiet">—</span>'}</td><td class="r">${esc(f.run_name || run.label || '')}</td>` +
    `<td>${isSorted(f) ? '<span class="st ok">Saved</span>' : '<span class="st todo">To sort</span>'}</td></tr>`;
  const old = f => `<tr data-t="${f.start}"><td class="b">${rangeName(f)}</td>` +
    `<td>${isSorted(f) ? esc(label(f) || 'Note only') : '<span class="quiet">not sorted</span>'}</td>` +
    `<td>${f.text ? esc(f.text) : '<span class="quiet">—</span>'}</td><td class="r">${esc(f.run_name || '')}</td>` +
    `<td>${f.status === 'changed' ? '<span class="st changed" title="The notes there are different on this run. Listen to check it is fixed.">Changed now</span>'
                                   : '<span class="st same" title="This run wrote the same notes there.">Still the same</span>'}</td></tr>`;
  const asks = suggested.map(x => `<tr data-t="${barStart(x.bars[0])}"><td class="b">${rangeName({bar: x.bars[0], to: x.bars[1]})}</td>` +
    `<td>${x.answer === 'sax' ? 'It’s sax' : x.answer === 'not_sax' ? 'Not sax' : '<span class="quiet">Sax? not answered</span>'}</td>` +
    `<td class="quiet">“Sax?” question</td><td class="r">${esc(run.label || '')}</td>` +
    `<td>${x.answer ? '<span class="st ok">Saved</span>' : '<span class="st ask">Sax?</span>'}</td></tr>`).join('');
  const changed = past.filter(p => p.status === 'changed').length;
  $('#flagItems').innerHTML = `<table><thead><tr><th>Bars</th><th>What’s wrong</th><th>Your note</th><th>Model run</th><th></th></tr></thead><tbody>` +
    `<tr class="grp"><td colspan="5">This run · ${esc(run.label || '')}</td></tr>` +
    ((flags.map(row).join('') + asks) || '<tr><td colspan="5" class="quiet">No flags yet. Tap ⚑ Flag while it plays.</td></tr>') +
    (past.length ? `<tr class="grp"><td colspan="5">Earlier runs · this run changed the notes in ${changed} of ${past.length}</td></tr>${past.map(old).join('')}` : '') +
    `</tbody></table>`;
  const todo = toSort().length;
  $('#trackSum').innerHTML = `<b>Feedback</b> · ${flags.length} flag${flags.length === 1 ? '' : 's'} on ${esc(run.label || 'this run')}` +
    (todo ? ` · <span class="todo">${todo} to sort</span>` : '') +
    (okBars.length ? ` · ${okBars.length} bar${okBars.length === 1 ? '' : 's'} look right` : '') +
    (past.length ? ` · earlier runs: ${changed} of ${past.length} changed` : '');
}
$('#flagItems').addEventListener('click', e => {
  const go = e.target.closest('tr[data-t]');
  if (go) { seekTo(parseFloat(go.dataset.t) - 0.05); const el = measureEl(nowBar()); if (el) el.scrollIntoView({behavior: 'smooth', block: 'center'}); return; }
  const r = e.target.closest('tr[data-id]'); if (!r) return;
  const f = flags.find(x => x.id === r.dataset.id); if (f) openSheet(f, !isSorted(f));
});

function measureEl(bar) { const m = measures.find(x => barOf[x.id] === bar); return m ? document.getElementById(m.id) : null; }

// ---- boxes on the score: one per bar, the label on the first bar of each flag.
// The box is the tap target: tapping anywhere in a flagged bar opens its flag screen.
function drawFlags() {
  const box = $('#score');
  box.querySelectorAll('.flagbox').forEach(el => el.remove());
  const outer = box.getBoundingClientRect();
  const put = (bar, cls, text, data) => {
    const el = measureEl(bar); if (!el) return;
    const r = (el.querySelector('g.staff') || el).getBoundingClientRect();
    const d = document.createElement('div'); d.className = 'flagbox ' + cls;
    Object.assign(d.style, {left: `${r.left - outer.left - 4}px`, top: `${r.top - outer.top - 6}px`, width: `${r.width + 8}px`, height: `${r.height + 12}px`});
    Object.assign(d.dataset, data || {});
    if (text) d.innerHTML = `<span>${text}</span>`;
    box.appendChild(d);
  };
  for (const f of flags) for (let b = f.bar; b <= (f.to || f.bar); b++)
    put(b, (isSorted(f) ? '' : 'todo') + (editing && editing.id === f.id ? ' editing' : ''),
        b === f.bar ? (isSorted(f) ? '⚑ ' + esc(label(f) || 'Note') : '⚑ To sort') : '', {id: f.id});
  if (editing && !editing.id) for (let b = editing.bar; b <= editing.to; b++) put(b, 'editing', b === editing.bar ? 'New flag' : '', {editing: '1'});
  if (sel) for (let b = Math.min(sel.a, sel.b); b <= Math.max(sel.a, sel.b); b++)
    put(b, 'selection', b === Math.min(sel.a, sel.b) ? (sel.a === sel.b ? `Bar ${sel.a}` : `Bars ${Math.min(sel.a, sel.b)}–${Math.max(sel.a, sel.b)}`) : '');
  suggested.forEach((x, i) => { for (let b = x.bars[0]; b <= x.bars[1]; b++) if (!flagFor(b))
    put(b, 'suggest' + (x.answer ? ' answered' : ''), b !== x.bars[0] ? '' : x.answer === 'not_sax' ? 'Not sax (you said)' : x.answer === 'sax' ? 'Sax (you said)' : 'Sax?', {ask: i}); });
  markPicked();
}
function markPicked() {
  document.querySelectorAll('#score g.picked').forEach(g => g.classList.remove('picked'));
  $('#score').classList.toggle('picking', !!(editing && editing.scope === 'notes'));
  if (!editing || editing.scope !== 'notes') return;
  for (const [id, q] of Object.entries(qOf)) if (editing.picked.some(p => Math.abs(p - q) < 1e-3)) {
    const g = document.getElementById(id); if (g && g.classList.contains('note')) g.classList.add('picked');
  }
}
$('#score').addEventListener('click', e => {
  const fb = e.target.closest('.flagbox');
  // A flag's shading covers its bars, but a tap right on a note still means that note:
  // only the flag's label or the space between notes opens the flag.
  const onNote = fb && !e.target.closest('.flagbox span') && noteAt(measureAt(e.clientX, e.clientY), e.clientX, e.clientY, 12);
  if (fb && !onNote) {
    if (fb.dataset.id) { const f = flags.find(x => x.id === fb.dataset.id); if (f) openSheet(f, !isSorted(f)); }
    else if (fb.dataset.ask !== undefined) { seekTo(barStart(suggested[+fb.dataset.ask].bars[0]) - 0.05); showAsk(+fb.dataset.ask); }
    return;
  }
  const m = e.target.closest('g.measure') || measureAt(e.clientX, e.clientY);
  const bar = m ? barOf[m.id] : undefined;
  // Picking notes for "Just these notes".
  if (editing && editing.scope === 'notes' && bar !== undefined && bar >= editing.bar && bar <= editing.to) {
    const n = e.target.closest('g.note') || noteAt(m, e.clientX, e.clientY);
    if (n && qOf[n.id] !== undefined) {
      const q = qOf[n.id], i = editing.picked.findIndex(p => Math.abs(p - q) < 1e-3);
      if (i >= 0) editing.picked.splice(i, 1); else editing.picked.push(q);
      markPicked();
    }
    return;
  }
  // Otherwise a tap on a note jumps there. The notehead nearest the tap wins over whatever
  // SVG shape is on top (a neighbour's stem or beam), and when paused the jump lands just
  // inside the note, so the note lit up is the one tapped, not the one before it.
  const g = noteAt(m, e.clientX, e.clientY) || e.target.closest('g.note, g.rest, g.chord');
  if (g && qOf[g.id] !== undefined) {
    const t = qToT(qOf[g.id]);
    seekTo(audio.paused ? t + 0.01 : t - 0.05);
  }
});
// Fingers are wide: the note in this bar nearest the tap, within about a note's width.
function noteAt(m, x, y, within = 30) {
  if (!m) return null;
  let best = null, bestD = within;
  for (const g of m.querySelectorAll('g.note')) {
    if (qOf[g.id] === undefined) continue;
    const r = (g.querySelector('.notehead') || g).getBoundingClientRect();
    const d = Math.hypot(Math.max(r.left - x, 0, x - r.right), Math.max(r.top - y, 0, y - r.bottom) / 3);
    if (d < bestD) { best = g; bestD = d; }
  }
  return best;
}
// A point on the paper between notes lands on the page, not the bar: find the bar under it.
function measureAt(x, y) {
  let best = null, bestD = Infinity;
  for (const {id} of measures) {
    const el = document.getElementById(id); if (!el) continue;
    const r = el.getBoundingClientRect();
    if (x < r.left || x > r.right) continue;
    const d = y < r.top ? r.top - y : y > r.bottom ? y - r.bottom : 0;
    if (d < bestD && d < 40) { best = el; bestD = d; }
  }
  return best;
}

// ---- press and drag across bars on the score to flag a stretch.
// Mouse: press and drag. Finger: press and hold for a moment, then drag (a quick swipe still scrolls).
let sel = null, selecting = false, selTimer = null, selStart = null;
function barAtPoint(x, y) { const m = measureAt(x, y); return m ? barOf[m.id] : undefined; }
function selBegin(x, y) {
  const b = barAtPoint(x, y); if (b === undefined) return false;
  sel = {a: b, b}; selecting = true; $('#score').classList.add('selecting'); drawFlags();
  return true;
}
function selMove(x, y) { const b = barAtPoint(x, y); if (b !== undefined && b !== sel.b) { sel.b = b; drawFlags(); } }
function selEnd() {
  clearTimeout(selTimer); selStart = null;
  if (!selecting) return;
  const a = Math.min(sel.a, sel.b), b = Math.max(sel.a, sel.b);
  selecting = false; sel = null; $('#score').classList.remove('selecting'); suppressClick = true; setTimeout(() => { suppressClick = false; }, 400);
  const f = flags.find(x => !(b < x.bar || a > (x.to || x.bar)));
  if (f) openSheet({...f, bar: Math.min(f.bar, a), to: Math.max(f.to || f.bar, b)}, false, f);
  else openSheet({bar: a, to: b, categories: [], scope: 'bar', picked: [], text: ''});
}
let suppressClick = false;
$('#score').addEventListener('click', e => { if (suppressClick) { e.stopImmediatePropagation(); e.preventDefault(); } }, true);
$('#score').addEventListener('pointerdown', e => {
  if (e.pointerType !== 'mouse' || e.button !== 0 || (editing && editing.scope === 'notes')) return;
  selStart = {x: e.clientX, y: e.clientY};
});
window.addEventListener('pointermove', e => {
  if (e.pointerType !== 'mouse' || !selStart) return;
  if (!selecting && Math.hypot(e.clientX - selStart.x, e.clientY - selStart.y) > 12) {
    if (!selBegin(selStart.x, selStart.y)) { selStart = null; return; }
  }
  if (selecting) { e.preventDefault(); selMove(e.clientX, e.clientY); }
});
window.addEventListener('pointerup', e => { if (e.pointerType === 'mouse') selEnd(); });
// Touch (iPad): touch events, so the hold can stop the page from scrolling once it starts.
$('#score').addEventListener('touchstart', e => {
  if (e.touches.length !== 1 || (editing && editing.scope === 'notes')) { clearTimeout(selTimer); return; }
  const t = e.touches[0]; selStart = {x: t.clientX, y: t.clientY};
  clearTimeout(selTimer);
  selTimer = setTimeout(() => { if (selStart && selBegin(selStart.x, selStart.y) && navigator.vibrate) navigator.vibrate(10); }, 400);
}, {passive: true});
$('#score').addEventListener('touchmove', e => {
  const t = e.touches[0];
  if (selecting) { e.preventDefault(); selMove(t.clientX, t.clientY); return; }
  if (selStart && Math.hypot(t.clientX - selStart.x, t.clientY - selStart.y) > 10) { clearTimeout(selTimer); selStart = null; }
}, {passive: false});
$('#score').addEventListener('touchend', e => { if (selecting) e.preventDefault(); selEnd(); });
$('#score').addEventListener('touchcancel', () => { clearTimeout(selTimer); selStart = null; if (selecting) { selecting = false; sel = null; $('#score').classList.remove('selecting'); drawFlags(); } });
$('#score').addEventListener('contextmenu', e => { if (selecting || selTimer) e.preventDefault(); });

// ---- the bar strip over the transport: every bar, coloured by what you've done with it
function drawStrip() {
  const strip = $('#strip'); let h = '';
  strip.style.gridTemplateColumns = `repeat(${nBars}, minmax(0, 1fr))`;
  const now = nowBar();
  for (let b = 1; b <= nBars; b++) {
    const f = flagFor(b), s = suggested.find(x => b >= x.bars[0] && b <= x.bars[1]);
    const c = f ? (isSorted(f) ? 'flag' : 'todo') : s && !s.answer ? 'ask' : heard.has(b) ? 'ok' : '';
    h += `<button type="button" class="${c}${b === now ? ' now' : ''}" data-b="${b}" aria-label="Bar ${b}"></button>`;
  }
  strip.innerHTML = h;
  const ok = [...heard].filter(b => !flagFor(b)).length;
  $('#stripNote').textContent = `${ok} bar${ok === 1 ? '' : 's'} heard with no flag (saved as “looks right”)`;
}
$('#strip').addEventListener('click', e => { const b = e.target.closest('button[data-b]'); if (b) seekTo(barStart(+b.dataset.b) - 0.05); });
let lastBar = null;
function tickReview() {
  const b = nowBar();
  if (b !== lastBar) {
    // Played straight through a bar, at any speed: it counts as heard.
    if (!audio.paused && lastBar !== null && b === lastBar + 1 && !loopRange) heard.add(lastBar);
    lastBar = b; drawStrip(); askIfUnsure(b);
    if (heard.size - heardSent.size >= 8) sendHeard();
  }
  if (holdFrom !== null && holding) $('#flag').querySelector('b').textContent = `Bars ${holdFrom}–${Math.max(holdFrom, b)}`;
}
async function sendHeard() {
  const bars = [...heard].filter(b => !heardSent.has(b));
  if (!bars.length) return;
  bars.forEach(b => heardSent.add(b));
  try { const r = await post(`/api/takes/${takeId}/heard`, {bars}); if (r.ok) drawTracker((await r.json()).looks_right || []); }
  catch (e) { bars.forEach(b => heardSent.delete(b)); }
}
window.addEventListener('pagehide', () => {
  const bars = [...heard].filter(b => !heardSent.has(b));
  if (bars.length && navigator.sendBeacon) navigator.sendBeacon(`/api/takes/${takeId}/heard`, new Blob([JSON.stringify({bars})], {type: 'application/json'}));
});

// ---- "Sax?" questions pop up as those bars go by; one tap answers without stopping the music
let askShown = null;
function askIfUnsure(b) {
  const i = suggested.findIndex(x => !x.answer && b >= x.bars[0] && b <= x.bars[1]);
  if (i >= 0 && !audio.paused) { if (askShown !== i) showAsk(i); }  // don't redraw it under a finger
  else if (askShown !== null && !(suggested[askShown] && !suggested[askShown].answer && b >= suggested[askShown].bars[0] && b <= suggested[askShown].bars[1] + 1)) hideAsk();
}
function showAsk(i) {
  const x = suggested[i]; if (!x) return;
  askShown = i;
  const el = $('#ask');
  el.innerHTML = `<span>${x.bars[0] === x.bars[1] ? `Bar ${x.bars[0]}` : `Bars ${x.bars[0]}–${x.bars[1]}`}: is this the sax?</span>` +
    `<button type="button" data-a="sax" data-i="${i}" class="${x.answer === 'sax' ? 'on' : ''}">It’s sax</button>` +
    `<button type="button" data-a="not_sax" data-i="${i}" class="${x.answer === 'not_sax' ? 'on' : ''}">Not sax</button>` +
    `<button type="button" data-a="" aria-label="Close">✕</button>`;
  el.hidden = false;
}
function hideAsk() { askShown = null; $('#ask').hidden = true; }
$('#ask').addEventListener('click', async e => {
  const b = e.target.closest('button[data-a]'); if (!b) return;
  if (!b.dataset.a) { hideAsk(); return; }
  const x = suggested[+b.dataset.i];
  const r = await post(`/api/takes/${takeId}/suggestions`, {bars: x.bars, answer: b.dataset.a});
  if (r.ok) { gotFlags(await r.json()); hideAsk(); toast(b.dataset.a === 'sax' ? 'Saved: it’s sax.' : 'Saved: not sax.'); }
  else toast('Could not save that answer.');
});

// ---- ⚑ Flag: tap = the bar heard about a second ago (you hear it before your thumb moves);
// press and hold = every bar from the press to the release. Paused: opens the flag screen.
// Pointer capture keeps the hold alive while a finger drifts; touch-action: none stops the
// iPad from treating the press as a scroll or a text selection.
let holding = false, holdFrom = null, holdTimer = null, holdPointer = null;
function flagDown() {
  if (holdFrom !== null) return;
  holdFrom = barAtTime((audio.currentTime || 0) - (audio.paused ? 0 : 1 * (audio.playbackRate || 1)));
  holdTimer = setTimeout(() => {
    holding = true; $('#flag').classList.add('holding');
    $('#flag').querySelector('b').textContent = `Bars ${holdFrom}–${Math.max(holdFrom, nowBar())}`;
  }, 350);
}
async function flagUp() {
  if (holdFrom === null) return;
  clearTimeout(holdTimer);
  const from = holdFrom, to = holding ? Math.max(holdFrom, nowBar()) : holdFrom;
  holding = false; holdFrom = null; $('#flag').classList.remove('holding'); $('#flag').querySelector('b').textContent = '⚑ Flag';
  if (audio.paused) {
    const f = flagFor(from);
    if (f) openSheet(f, !isSorted(f)); else openSheet({bar: from, to, categories: [], scope: 'bar', picked: [], text: ''});
    return;
  }
  const r = await post(`/api/takes/${takeId}/flags`, {bar: from, to, categories: [], scope: 'bar', picked: [], text: '', view, merge: true});
  if (!r.ok) { toast('Could not save the flag.'); return; }
  const data = await r.json(); gotFlags(data);
  lastUndo = data.last ? data.last.undo : null;
  const merged = lastUndo && lastUndo.put;
  const msg = merged ? `⚑ Added to the flag on ${rangeName(data.last).toLowerCase()}.` : `⚑ ${rangeName(data.last)} flagged. Sort it later.`;
  toast(msg);
  if (lastUndo) $('#toast').innerHTML = `${esc(msg)} <button type="button" id="undo">Undo</button>`;
}
const fb = $('#flag');
fb.addEventListener('pointerdown', e => {
  if (e.pointerType === 'mouse' && e.button !== 0) return;
  e.preventDefault(); holdPointer = e.pointerId;
  try { fb.setPointerCapture(e.pointerId); } catch (err) {}
  flagDown();
});
fb.addEventListener('pointerup', e => { if (e.pointerId === holdPointer) { holdPointer = null; flagUp(); } });
fb.addEventListener('pointercancel', e => { if (e.pointerId === holdPointer) { holdPointer = null; flagUp(); } });
fb.addEventListener('lostpointercapture', e => { if (e.pointerId === holdPointer) { holdPointer = null; flagUp(); } });
fb.addEventListener('contextmenu', e => e.preventDefault());
fb.addEventListener('click', e => e.preventDefault());
document.addEventListener('click', async e => {
  if (!e.target.closest('#undo') || !lastUndo) return;
  const u = lastUndo; lastUndo = null;
  const r = u.delete ? await fetch(`/api/takes/${takeId}/flags/${u.delete}`, {method: 'DELETE'})
                     : await post(`/api/takes/${takeId}/flags/${u.put}`, u.body, 'PUT');
  if (r.ok) { gotFlags(await r.json()); toast('Undone.'); } else toast('Could not undo that.');
});

// ---- the flag screen. While it is open the flag's bars loop.
function openSheet(f, sorting, existing) {
  const base = existing || f;
  editing = {id: base.id || null, bar: f.bar, to: f.to || f.bar, picked: [...(base.picked || [])], scope: base.scope || 'bar',
             categories: [...(base.categories || [])], sorting: !!sorting};
  // Several big reasons can apply at once (wrong notes and another horn bleeding in).
  editing.groups = [...new Set(editing.categories.map(groupOf).filter(Boolean))];
  $('#flagText').value = base.text || '';
  $('#deleteFlag').hidden = !editing.id;
  $('#saveFlag').textContent = saveLabel();
  drawRange(); drawSheet();
  $('#sheet').hidden = false;
  if (sheetH) { $('#sheet').style.height = sheetH + 'px'; $('#sheet').style.maxHeight = 'none'; }
  document.body.style.paddingBottom = `${$('#sheet').offsetHeight}px`;
  setLoop(true); syncPlay();
  seekTo(barStart(editing.bar) - 0.05);
  showBar(editing.bar);
  drawFlags();
}
function saveLabel() {
  if (!editing || !editing.sorting) return 'Save';
  const left = toSort().filter(x => x.id !== editing.id).length;
  return left ? `Save, next (${left} left)` : 'Save';
}
// Keep the flag's first bar in the part of the page the sheet doesn't cover.
function showBar(bar) {
  const el = measureEl(bar); if (!el) return;
  const r = el.getBoundingClientRect(), head = $('.top').getBoundingClientRect().bottom, foot = bottomEdge();
  if (r.top < head + 8 || r.bottom > foot - 8) window.scrollTo({top: window.scrollY + r.top - head - 24, behavior: 'smooth'});
}
function drawSheet() {
  const gs = editing.groups;
  $('#groups').innerHTML = Object.entries(GROUPS).map(([k, v], i) =>
    `<button type="button" data-g="${k}" aria-pressed="${gs.includes(k)}" class="${gs.includes(k) ? 'on' : ''}"><b>${esc(v.label)}</b><span>${esc(v.hint)}</span><kbd>${i + 1}</kbd></button>`).join('');
  const keys = gs.flatMap(g => GROUPS[g].keys.length > 1 ? GROUPS[g].keys : []);
  $('#detail').hidden = !keys.length;
  $('#cats').innerHTML = keys.map(k => `<button type="button" data-c="${k}" class="${editing.categories.includes(k) ? 'on' : ''}">${esc(categories[k] || k)}</button>`).join('');
  $('#scope').querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.v === editing.scope));
  $('#pickHint').hidden = editing.scope !== 'notes';
  markPicked();
}
function setLoop(on) {
  loopRange = on && editing ? [Math.max(0, barStart(editing.bar) - 0.05), barEnd(editing.to)] : null;
  $('#loopBtn').classList.toggle('on', !!loopRange);
  $('#loopBtn').textContent = loopRange ? '⟲ Looping' : '⟲ Loop';
}
$('#loopBtn').addEventListener('click', () => setLoop(!loopRange));
function pickGroup(g) {
  editing.groups = editing.groups.includes(g) ? editing.groups.filter(x => x !== g) : [...editing.groups, g];
  editing.categories = editing.categories.filter(c => !GROUPS[c] && editing.groups.includes(groupOf(c)) && GROUPS[groupOf(c)].keys.length > 1);
  drawSheet();
}
$('#groups').addEventListener('click', e => { const b = e.target.closest('button[data-g]'); if (b) pickGroup(b.dataset.g); });
$('#cats').addEventListener('click', e => {
  const b = e.target.closest('button[data-c]'); if (!b) return; const c = b.dataset.c;
  editing.categories = editing.categories.includes(c) ? editing.categories.filter(x => x !== c) : [...editing.categories, c];
  drawSheet();
});
$('#scope').addEventListener('click', e => { const b = e.target.closest('button[data-v]'); if (!b) return; editing.scope = b.dataset.v; drawSheet(); });
// Bar range: − and + on each end, like a number picker.
function drawRange() {
  $('#fromBar').value = editing.bar; $('#toBar').value = editing.to; $('#fromBar').max = $('#toBar').max = nBars;
  $('#sheetTitle').textContent = rangeName(editing);
  $('#sheetTime').textContent = `${clock(barStart(editing.bar))} to ${clock(barEnd(editing.to))}`;
}
$('#range').addEventListener('click', e => {
  const b = e.target.closest('button[data-r]'); if (!b || !editing) return;
  const [end, by] = b.dataset.r.split(':'); const n = +by;
  if (end === 'from') editing.bar = Math.max(1, Math.min(editing.to, editing.bar + n));
  else editing.to = Math.max(editing.bar, Math.min(nBars, editing.to + n));
  editing.picked = editing.picked.filter(q => q >= (editing.bar - 1) * BEATS && q < editing.to * BEATS);
  drawRange(); if (loopRange) setLoop(true); drawFlags();
});
// Or type the bar numbers. The other end follows if needed, so 1 then 32 just works.
function typedBar(which) {
  const el = $(which === 'from' ? '#fromBar' : '#toBar'); if (!editing) return;
  const n = Math.round(Number(el.value));
  if (!Number.isFinite(n) || el.value === '') { drawRange(); return; }
  const b = Math.max(1, Math.min(nBars, n));
  if (which === 'from') { editing.bar = b; editing.to = Math.max(editing.to, b); }
  else { editing.to = b; editing.bar = Math.min(editing.bar, b); }
  editing.picked = editing.picked.filter(q => q >= (editing.bar - 1) * BEATS && q < editing.to * BEATS);
  drawRange(); if (loopRange) setLoop(true); drawFlags();
  if (which === 'from') { seekTo(barStart(editing.bar) - 0.05); showBar(editing.bar); }
}
for (const which of ['from', 'to']) {
  const el = $(which === 'from' ? '#fromBar' : '#toBar');
  el.addEventListener('change', () => typedBar(which));
  el.addEventListener('keydown', e => { if (e.key !== 'Escape') e.stopPropagation(); if (e.key === 'Enter') { e.preventDefault(); el.blur(); } });
  el.addEventListener('focus', () => el.select());
}
// Play controls inside the flag screen.
$('#sRestart').addEventListener('click', () => { if (editing) seekTo(barStart(editing.bar) - 0.05); });
$('#sBack').addEventListener('click', () => seekTo((audio.currentTime || 0) - 2));
$('#sPlay').addEventListener('click', toggle);
function syncPlay() { $('#sPlay').textContent = audio.paused ? '▶' : '❚❚'; $('#sPlay').setAttribute('aria-label', audio.paused ? 'Play' : 'Pause'); }
// Pull the flag screen up or down by its handle to see more of the chart. Double-tap shrinks it.
let sheetH = null;
(() => {
  const h = $('#grab'); let y0, h0, id = null, lastTap = 0;
  const set = nh => {
    sheetH = nh;
    $('#sheet').style.height = nh ? nh + 'px' : ''; $('#sheet').style.maxHeight = nh ? 'none' : '';
    document.body.style.paddingBottom = $('#sheet').offsetHeight + 'px';
  };
  h.addEventListener('pointerdown', e => {
    e.preventDefault(); y0 = e.clientY; h0 = $('#sheet').offsetHeight; id = e.pointerId; h.classList.add('dragging');
    try { h.setPointerCapture(e.pointerId); } catch (err) {}
    const now = Date.now(); if (now - lastTap < 350) { set(sheetH && sheetH < 260 ? null : 190); id = null; } lastTap = now;
  });
  h.addEventListener('pointermove', e => { if (e.pointerId === id) set(Math.round(Math.max(150, Math.min(innerHeight * 0.85, h0 + (y0 - e.clientY))))); });
  const up = e => { if (e.pointerId === id) { id = null; h.classList.remove('dragging'); } else h.classList.remove('dragging'); };
  h.addEventListener('pointerup', up); h.addEventListener('pointercancel', up);
})();
function closeSheet() {
  editing = null; setLoop(false); $('#sheet').hidden = true; document.body.style.paddingBottom = '';
  if (sortSpeed !== null) { $('#speed').value = sortSpeed; setSpeed(); sortSpeed = null; }
  drawFlags();
}
$('#cancelFlag').addEventListener('click', () => { audio.pause(); closeSheet(); });
$('#saveFlag').addEventListener('click', saveFlag);
async function saveFlag() {
  if (!editing) return;
  const text = $('#flagText').value.trim();
  // A big reason with no detail picked is saved as the big reason itself.
  // Each big reason picked: its details if any were picked, else the big reason itself.
  const finalCats = editing.groups.flatMap(g => {
    const picked = editing.categories.filter(c => !GROUPS[c] && groupOf(c) === g);
    return picked.length ? picked : GROUPS[g].keys.length === 1 ? GROUPS[g].keys : [g];
  });
  if (!finalCats.length && !text) { toast('Pick a reason, or say it in a few words.'); return; }
  if (editing.scope === 'notes' && !editing.picked.length) { toast('Tap the notes, or choose Whole bar.'); return; }
  const body = {bar: editing.bar, to: editing.to, categories: finalCats, scope: editing.scope,
                picked: editing.scope === 'notes' ? editing.picked : [], text, view};
  const r = await post(editing.id ? `/api/takes/${takeId}/flags/${editing.id}` : `/api/takes/${takeId}/flags`, body, editing.id ? 'PUT' : 'POST');
  if (!r.ok) { let msg = 'Could not save the flag.'; try { msg = (await r.json()).detail || msg; } catch (e) {} toast(msg); return; }
  const was = editing; gotFlags(await r.json());
  const next = was.sorting && toSort()[0];
  if (next) { openSheet(next, true); toast(`Saved. Next: ${rangeName(next).toLowerCase()}.`); if (audio.paused) playAudio(); }
  else { audio.pause(); closeSheet(); toast(was.sorting ? `All flags sorted. Saved to ${run.label || 'this run'}.` : `${rangeName(was)} saved.`); }
}
$('#deleteFlag').addEventListener('click', async () => {
  if (!editing || !editing.id) return;
  const r = await fetch(`/api/takes/${takeId}/flags/${editing.id}`, {method: 'DELETE'});
  if (!r.ok) { toast('Could not delete the flag.'); return; }
  gotFlags(await r.json()); closeSheet(); toast('Flag deleted.');
});
function startSorting() {
  const next = toSort()[0]; if (!next) return false;
  if (sortSpeed === null) sortSpeed = $('#speed').value;
  $('#speed').value = '0.75'; setSpeed();
  openSheet(next, true); playAudio();
  return true;
}
$('#sortBtn').addEventListener('click', startSorting);

// ---- copy and download, in the tracker
// Over the home network the page isn't "secure", so Safari has no navigator.clipboard;
// select a hidden text box and copy that instead.
$('#copyFlags').addEventListener('click', () => {
  const clip = $('#clip'); clip.value = flagsText;
  let ok = false;
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(flagsText).then(() => toast('Flags copied. Paste them into a thread.'), showText);
    return;
  }
  clip.removeAttribute('readonly'); clip.focus(); clip.select(); clip.setSelectionRange(0, flagsText.length);
  try { ok = document.execCommand('copy'); } catch (e) {}
  clip.setAttribute('readonly', ''); clip.blur();
  if (ok) toast('Flags copied. Paste them into a thread.'); else showText();
});
function showText() {
  toast('Select all and copy the text that opened.');
  window.open(`/api/takes/${takeId}/flags.txt`, '_blank');
}
$('#dlFlags').addEventListener('click', () => download(`/api/takes/${takeId}/flags.json`));

// ---- keys (Mac): F flag (hold for a stretch), S open the flag screen (next to sort, else this bar),
// space play/pause (also in the flag screen), ← back 2 s, 1–4 pick a reason, Enter save, Esc close.
const typing = e => e.target.closest && e.target.closest('input, textarea, select, [contenteditable]');
document.addEventListener('keydown', e => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === 'Escape') { if (editing) { e.preventDefault(); closeSheet(); } return; }
  if (typing(e)) return;
  if (e.code === 'Space') { e.preventDefault(); if (!e.repeat) toggle(); return; }
  const k = e.key.toLowerCase();
  if (k === 'f') { e.preventDefault(); if (!e.repeat) flagDown(); return; }
  if (k === 's' && !e.repeat) {
    e.preventDefault();
    if (editing) return;
    if (!startSorting()) { const b = nowBar(), f = flagFor(b); openSheet(f || {bar: b, to: b, categories: [], scope: 'bar', picked: [], text: ''}, false); }
    return;
  }
  if (e.key === 'ArrowLeft') { e.preventDefault(); seekTo((audio.currentTime || 0) - 2); return; }
  if (editing && /^[1-4]$/.test(e.key)) { e.preventDefault(); pickGroup(Object.keys(GROUPS)[+e.key - 1]); return; }
  if (editing && e.key === 'Enter') { e.preventDefault(); saveFlag(); }
});
document.addEventListener('keyup', e => {
  if (e.code === 'Space' && !typing(e)) e.preventDefault();  // a focused button would click again on keyup
  if (e.key.toLowerCase() === 'f') flagUp();
});
window.addEventListener('resize', () => drawFlags());
window.addEventListener('blur', () => { if (holdFrom !== null) flagUp(); });

loadFlags();
loadJob().catch(err => { $('#score').innerHTML = `<div class="loading">Could not load this take: ${esc(err.message)}</div>`; });
