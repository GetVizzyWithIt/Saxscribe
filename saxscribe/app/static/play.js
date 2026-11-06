// The play-along: the score scrolls and lights up each note as the recording plays.
// Timing comes from the server's sync pairs (score position in quarter notes <-> seconds),
// built from the exact onsets in notes.json and the beat grid.
const takeId = location.pathname.split('/').pop();
const audio = $('#audio');
let size = 1;
try { size = parseInt(localStorage.getItem('saxscribe-size') ?? '1', 10); } catch (e) {}
if (!(size >= 0 && size <= 3)) size = 1;
let barOf = {};
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
  $('#name').textContent = job.artist ? `${job.title} · ${job.artist}` : job.title;
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
  starts = []; measures = []; qOf = {}; barOf = {}; lit = []; litMeasure = null;
  for (const e of data.timemap) {
    if (e.measureOn) { measures.push({q: e.qstamp, id: e.measureOn}); barOf[e.measureOn] = Math.floor(e.qstamp / 4 + 1e-6) + 1; }
    const ids = (e.on || []).filter(id => { const el = document.getElementById(id); return el && el.classList.contains('note'); });
    for (const id of (e.on || [])) qOf[id] = e.qstamp;
    if (ids.length) starts.push({q: e.qstamp, ids});
  }
  update(true);
  drawFlags();
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
// Tap a note to jump there (or, in flag mode, tap a bar to flag it: see below).
$('#score').addEventListener('click', e => {
  if (flagMode) { flagClick(e); return; }
  const g = e.target.closest('g.note, g.rest, g.chord');
  if (!g || qOf[g.id] === undefined) return;
  audio.currentTime = Math.max(0, qToT(qOf[g.id]) - 0.05);
  update(true);
});
document.addEventListener('keydown', e => {
  // Space plays and pauses, except while typing (the flag note box) or in the flag panel.
  const typing = e.target.closest && e.target.closest('input, textarea, select, [contenteditable], #sheet');
  if (e.code === 'Space' && !typing) { e.preventDefault(); toggle(); }
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
$('#pdf').addEventListener('click', () => { location.href = `/take/${takeId}/pdf?view=${view}`; });
$('#xml').addEventListener('click', () => download(`/api/takes/${takeId}/file/musicxml?view=${view}`));
$('#midi').addEventListener('click', () => download(`/api/takes/${takeId}/file/midi`));

// ---- flags: mark bars for review. They never change the transcription; they go to
// flags.json next to the take (server: flags.py), with a copy on the Desktop.
let flagMode = false, flags = [], categories = {}, flagsText = '', editing = null, suggested = [];
const getScope = segment($('#scope'), v => { $('#pickHint').hidden = v !== 'notes'; markPicked(); });

async function loadFlags() {
  const r = await fetch(`/api/takes/${takeId}/flags`);
  if (r.ok) gotFlags(await r.json());
}
function gotFlags(data) {
  flags = data.flags; categories = data.categories; flagsText = data.text;
  $('#cats').innerHTML = Object.entries(categories).map(([k, v]) => `<button type="button" data-c="${k}">${esc(v)}</button>`).join('');
  suggested = data.suggested || [];
  const open = suggested.filter(x => !x.answer).length;
  $('#flagCount').textContent = (flags.length ? `Flags (${flags.length})` : 'Flags') + (open ? ` · ${open} to check` : '');
  // Stretches the tool thinks may be another instrument: the notes stay on the score; Austin's
  // answer is stored with the flags (flags.py review) and becomes the test set for hiding them.
  $('#suggestItems').hidden = !suggested.length;
  $('#suggestItems').innerHTML = suggested.length ? '<div class="quiet small">Possibly not sax: the sax track is near-silent while another instrument plays these notes. Listen and answer.</div>' +
    suggested.map((x, i) => {
      const bars = x.bars[0] === x.bars[1] ? `Bar ${x.bars[0]}` : `Bars ${x.bars[0]}–${x.bars[1]}`;
      return `<div class="suggest-item"><button type="button" class="what" data-go="${x.bars[0]}">${bars} · ${x.notes} note${x.notes === 1 ? '' : 's'}</button>` +
        `<button type="button" data-i="${i}" data-a="not_sax" class="${x.answer === 'not_sax' ? 'on' : ''}">Not sax</button>` +
        `<button type="button" data-i="${i}" data-a="sax" class="${x.answer === 'sax' ? 'on' : ''}">It’s sax</button></div>`;
    }).join('') : '';
  $('#flagItems').innerHTML = flags.length ? flags.map(f =>
    `<button type="button" data-id="${f.id}">Bar ${f.bar} · ${esc(f.categories.map(c => categories[c] || c).join(', '))}` +
    `<small>${f.scope === 'notes' ? `${f.picked.length} note${f.picked.length === 1 ? '' : 's'}` : 'whole bar'}${f.text ? ' · ' + esc(f.text) : ''}</small></button>`).join('')
    : '<div class="quiet small">No bars flagged yet. Turn on Flag, then tap a bar.</div>';
  drawFlags();
}
function measureEl(bar) {
  const m = measures.find(x => barOf[x.id] === bar);
  return m ? document.getElementById(m.id) : null;
}
// Boxes over flagged bars (and the one being edited), drawn on top of the score.
function drawFlags() {
  const box = $('#score');
  box.querySelectorAll('.flagbox').forEach(el => el.remove());
  const outer = box.getBoundingClientRect();
  const shown = flags.map(f => ({bar: f.bar, label: f.categories.map(c => categories[c] || c).join(', '), id: f.id}));
  if (editing && !editing.id) shown.push({bar: editing.bar, label: 'New flag', id: null});
  for (const x of suggested) {
    for (let b = x.bars[0]; b <= x.bars[1]; b++) {
      if (shown.some(f => f.bar === b)) continue;
      const label = b !== x.bars[0] ? '' : x.answer === 'not_sax' ? 'Not sax (you said)' : x.answer === 'sax' ? 'Sax (you said)' : 'Possibly not sax?';
      shown.push({bar: b, label, id: null, suggest: true, answered: !!x.answer});
    }
  }
  for (const f of shown) {
    const el = measureEl(f.bar);
    if (!el) continue;
    const staff = el.querySelector('g.staff') || el;
    const r = staff.getBoundingClientRect();
    const d = document.createElement('div');
    d.className = 'flagbox' + (f.suggest ? ' suggest' + (f.answered ? ' answered' : '') : '') +
      (!f.suggest && editing && editing.bar === f.bar && editing.id === f.id ? ' editing' : '');
    Object.assign(d.style, {left: `${r.left - outer.left - 4}px`, top: `${r.top - outer.top - 6}px`,
                            width: `${r.width + 8}px`, height: `${r.height + 12}px`});
    d.innerHTML = f.label ? `<span>${f.suggest ? '' : '⚑ '}${esc(f.label)}</span>` : '';
    box.appendChild(d);
  }
  markPicked();
}
function markPicked() {
  document.querySelectorAll('#score g.picked').forEach(g => g.classList.remove('picked'));
  if (!editing || getScope() !== 'notes') return;
  for (const [id, q] of Object.entries(qOf)) {
    if (editing.picked.some(p => Math.abs(p - q) < 1e-3)) {
      const g = document.getElementById(id);
      if (g && g.classList.contains('note')) g.classList.add('picked');
    }
  }
}
function setFlagMode(on) {
  flagMode = on;
  $('#flagMode').classList.toggle('on', on); $('#flagMode').setAttribute('aria-pressed', on);
  $('#score').classList.toggle('flagging', on);
  if (on) toast('Flag mode: tap a bar to flag it.'); else closeSheet();
}
$('#flagMode').addEventListener('click', () => setFlagMode(!flagMode));
$('#suggestItems').addEventListener('click', async e => {
  const go = e.target.closest('[data-go]');
  if (go) { const el = measureEl(+go.dataset.go); if (el) el.scrollIntoView({behavior: 'smooth', block: 'center'}); $('#flagMenu').open = false; return; }
  const b = e.target.closest('button[data-a]'); if (!b) return;
  const x = suggested[+b.dataset.i];
  const r = await fetch(`/api/takes/${takeId}/suggestions`, {method: 'POST', headers: {'Content-Type': 'application/json'},
                                                             body: JSON.stringify({bars: x.bars, answer: b.dataset.a})});
  if (r.ok) { gotFlags(await r.json()); toast('Saved. Thanks, that answer trains the check.'); }
  else toast('Could not save that answer.');
});

function flagClick(e) {
  const m = e.target.closest('g.measure') || measureAt(e.clientX, e.clientY);
  if (!m || barOf[m.id] === undefined) return;
  const note = e.target.closest('g.note') || noteAt(m, e.clientX, e.clientY);
  const bar = barOf[m.id];
  if (editing && editing.bar === bar && getScope() === 'notes') {
    if (note && qOf[note.id] !== undefined) {  // pick or unpick this note
      const q = qOf[note.id], i = editing.picked.findIndex(p => Math.abs(p - q) < 1e-3);
      if (i >= 0) editing.picked.splice(i, 1); else editing.picked.push(q);
      markPicked();
    }
    return;
  }
  const old = flags.find(f => f.bar === bar);
  openSheet(old || {bar, categories: [], scope: 'bar', picked: [], text: ''});
  if (!old && note && qOf[note.id] !== undefined) {
    // Tapped right on a note: offer it as the first picked note, but keep "Whole bar" until asked.
    editing.firstNote = qOf[note.id];
  }
}
// Fingers are wide: the note in this bar nearest the tap, within about a note's width.
function noteAt(m, x, y) {
  let best = null, bestD = 30;
  for (const g of m.querySelectorAll('g.note')) {
    if (qOf[g.id] === undefined) continue;
    const r = (g.querySelector('.notehead') || g).getBoundingClientRect();
    const d = Math.hypot(Math.max(r.left - x, 0, x - r.right), Math.max(r.top - y, 0, y - r.bottom) / 3);
    if (d < bestD) { best = g; bestD = d; }
  }
  return best;
}
// A tap on the paper between notes lands on the page, not the bar: find the bar under it.
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
function openSheet(f) {
  editing = {id: f.id || null, bar: f.bar, picked: [...(f.picked || [])]};
  $('#sheetTitle').textContent = `Bar ${f.bar}`;
  const t0 = f.start !== undefined ? f.start : qToT((f.bar - 1) * 4), t1 = f.end !== undefined ? f.end : qToT(f.bar * 4);
  $('#sheetTime').textContent = `${clock(t0)} to ${clock(t1)}`;
  $('#cats').querySelectorAll('button').forEach(b => b.classList.toggle('on', f.categories.includes(b.dataset.c)));
  $('#scope').querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.v === (f.scope || 'bar')));
  $('#pickHint').hidden = (f.scope || 'bar') !== 'notes';
  $('#flagText').value = f.text || '';
  $('#deleteFlag').hidden = !f.id;
  $('#sheet').hidden = false;
  document.body.style.paddingBottom = `${$('#sheet').offsetHeight}px`;
  drawFlags();
  const el = measureEl(f.bar);
  if (el) {
    const r = el.getBoundingClientRect(), head = $('.top').getBoundingClientRect().bottom;
    if (r.bottom > $('#sheet').getBoundingClientRect().top - 8 || r.top < head)
      window.scrollTo({top: window.scrollY + r.top - head - 24, behavior: 'smooth'});
  }
}
function closeSheet() {
  editing = null; $('#sheet').hidden = true; document.body.style.paddingBottom = '';
  drawFlags();
}
$('#cats').addEventListener('click', e => { const b = e.target.closest('button'); if (b) b.classList.toggle('on'); });
$('#scope').addEventListener('click', e => {
  const b = e.target.closest('button');
  if (b && b.dataset.v === 'notes' && editing && !editing.picked.length && editing.firstNote !== undefined) {
    editing.picked.push(editing.firstNote); markPicked();
  }
});
$('#cancelFlag').addEventListener('click', closeSheet);
$('#saveFlag').addEventListener('click', async () => {
  const cats = [...$('#cats').querySelectorAll('button.on')].map(b => b.dataset.c);
  if (!cats.length) { toast('Pick at least one category.'); return; }
  const scope = getScope();
  if (scope === 'notes' && !editing.picked.length) { toast('Tap the notes in the bar, or choose Whole bar.'); return; }
  const body = {bar: editing.bar, categories: cats, scope, picked: scope === 'notes' ? editing.picked : [],
                text: $('#flagText').value.trim(), view};
  const r = await fetch(editing.id ? `/api/takes/${takeId}/flags/${editing.id}` : `/api/takes/${takeId}/flags`,
                        {method: editing.id ? 'PUT' : 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  if (!r.ok) { let msg = 'Could not save the flag.'; try { msg = (await r.json()).detail || msg; } catch (e) {} toast(msg); return; }
  const bar = editing.bar;
  editing = null; gotFlags(await r.json()); closeSheet();
  toast(`Bar ${bar} flagged.`);
});
$('#deleteFlag').addEventListener('click', async () => {
  if (!editing || !editing.id || !confirm(`Delete the flag on bar ${editing.bar}?`)) return;
  const r = await fetch(`/api/takes/${takeId}/flags/${editing.id}`, {method: 'DELETE'});
  if (!r.ok) { toast('Could not delete the flag.'); return; }
  editing = null; gotFlags(await r.json()); closeSheet();
});
// The Flags list: tap one to go there and edit it.
$('#flagItems').addEventListener('click', e => {
  const b = e.target.closest('button[data-id]'); if (!b) return;
  const f = flags.find(x => x.id === b.dataset.id); if (!f) return;
  $('#flagMenu').open = false;
  audio.currentTime = Math.max(0, f.start - 0.05); update(true);
  if (!flagMode) setFlagMode(true);
  openSheet(f);
});
// Copy for Claude. Over the home network the page isn't "secure", so Safari has no
// navigator.clipboard; select a hidden text box and copy that instead.
$('#copyFlags').addEventListener('click', () => {
  $('#flagMenu').open = false;
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
// When the browser won't copy: open the summary as plain text to select and copy by hand.
function showText() {
  toast('Select all and copy the text that opened.');
  window.open(`/api/takes/${takeId}/flags.txt`, '_blank');
}
$('#dlFlags').addEventListener('click', () => { $('#flagMenu').open = false; download(`/api/takes/${takeId}/flags.json`); });
document.addEventListener('click', e => { if (!e.target.closest('#flagMenu')) $('#flagMenu').open = false; });
window.addEventListener('resize', () => drawFlags());

loadFlags();
loadJob().catch(err => { $('#score').innerHTML = `<div class="loading">Could not load this take: ${esc(err.message)}</div>`; });
