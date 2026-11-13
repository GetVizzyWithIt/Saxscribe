// Results page: the tabs, the Progress front page and the Songs list.
// Progress reads experiment rows (DATA.experiments, flattened into EXP by results-compare.js):
//   - set "benchmark": one row per song per milestone, written by the Mac's re-score (E81). A milestone's
//     rows carry setup.variant = its commit, or (for the last two) the setup itself.
//   - until those exist, an interim benchmark: E80's per-song rows (your six tunes, three Parker test records).

// Changes that became the default, oldest first. `id` matches setup.variant on benchmark rows;
// `setup` matches rows of that setup with no variant.
const MILESTONES = [
  {id: 'b3aa715', pr: 9, when: 'Nov 2', label: ['First version', 'Basic Pitch on Demucs']},
  {id: 'e01aeef', pr: 35, when: 'Nov 3', label: ['Finds the sax stem,', 'writes only where it plays']},
  {id: '50b729a', pr: 57, when: 'Nov 3', label: ['Short notes follow tempo,', 'repeats restored']},
  {id: '80cba98', pr: 81, when: 'Nov 4', label: ['Two Demucs passes,', 'range rules per horn']},
  {id: 'A', setup: 'demucs|same|ours|', when: 'Nov 5–9', label: ['Hides piano bleed,', 'held notes kept whole']},
  {id: 'D', setup: 'rd-sax|same|rd-filosax-ft|', when: 'Nov 10', label: ['Filosax separator +', 'our fine-tuned finder']},
];
const INTERIM_SETS = ['pfh', 'bfmj', 'resolution', 'walkers-theme', 'isnt-she-lovely', 'bloody-well-right'];
const BAND_TARGET = 0.6;

const prog = {};

// ---------- tabs ----------
const TABS = ['progress', 'songs', 'lab', 'log', 'review'];
function showTab(name, scroll = true) {
  if (!TABS.includes(name)) name = 'progress';
  for (const p of document.querySelectorAll('.tab')) p.hidden = p.dataset.tab !== name;
  for (const a of document.querySelectorAll('.tabs a')) a.setAttribute('aria-selected', String(a.dataset.tab === name));
  if (location.hash.slice(1) !== name) history.replaceState(null, '', `#${name}`);
  // charts measure their box, so draw them once they can be seen
  if (name === 'log' && typeof panels !== 'undefined') panels.forEach(p => p.draw());
  if (scroll) scrollTo({top: 0});
}
addEventListener('hashchange', () => showTab(location.hash.slice(1)));
showTab(location.hash.slice(1), false);

// ---------- which rows are the benchmark ----------
function origSet(r) { return r._set || r.set; }
function matches(m, r) {
  if (m.setup) return setupKey(r.setup) === m.setup && !r.setup.variant;
  return !!r.setup.variant && (r.setup.variant === m.id || r.setup.variant.startsWith(m.id));
}
function songOf(r) {
  if (origSet(r) === 'benchmark') return r._record || r.record;
  if (r.entry !== 'E80') return null;
  if (INTERIM_SETS.includes(origSet(r)) && !r._record && !r.record) return origSet(r);
  if (origSet(r) === 'parker-test' && (r._record || r.record)) return `parker-test/${r._record || r.record}`;
  return null;
}
function songName(id, r) {
  const tg = tagOf(id);
  if (tg && tg.title) return tg.title;
  if (r && r.title) return r.title;
  if (RECORDS[id]) return RECORDS[id][0];
  if (id.startsWith('parker-test/')) return `Parker ${id.split('/')[1]}`;
  return id.replace(/_/g, ' ');
}

// {mode, songs: [id], steps: [{m, rows: Map id -> row, value, covered}], today, before}
function benchmark() {
  const bench = EXP.filter(r => origSet(r) === 'benchmark' && r.metrics.note_f1 != null);
  const mode = bench.length ? 'benchmark' : 'interim';
  const pool = (mode === 'benchmark' ? bench : EXP.filter(r => songOf(r) && r.metrics.note_f1 != null));
  const steps = MILESTONES.map(m => {
    const rows = new Map();
    for (const r of pool) if (matches(m, r)) rows.set(songOf(r), r);  // latest wins (EXP is oldest first)
    return {m, rows};
  });
  const todayIx = steps.map(s => s.rows.size > 0).lastIndexOf(true);
  if (todayIx < 0) return {mode, songs: [], steps, today: null, before: null};
  const songs = [...steps[todayIx].rows.keys()];
  for (const s of steps) {
    const have = songs.filter(id => s.rows.has(id));
    s.covered = have.length;
    s.value = have.length === songs.length ? mean(songs.map(id => s.rows.get(id).metrics.note_f1)) : null;
  }
  const today = steps[todayIx];
  const before = steps.slice(0, todayIx).reverse().find(s => s.covered > 0) || null;
  return {mode, songs, steps, today, before};
}
function mean(vs) { const v = vs.filter(x => x != null); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null; }
function signed(d, digits = 1) { return `${d >= 0 ? '▲ +' : '▼ −'}${Math.abs(d).toFixed(digits)}`; }

// ---------- tiles ----------
function tiles(B) {
  const box = $('#tiles'); box.replaceChildren();
  const tile = (lab, big, unit, delta, rows, src) => {
    const t = el('div', {class: 'tile'});
    t.append(el('div', {class: 'lab'}, lab));
    const b = el('div', {class: 'big'}, big); if (unit) b.append(el('small', {}, unit)); t.append(b);
    if (delta) t.append(el('div', {class: `delta ${delta.cls || ''}`}, delta.text));
    if (rows && rows.length) { const r = el('div', {class: 'row'}); rows.forEach(x => r.append(el('span', {}, x))); t.append(r); }
    if (src) t.append(el('div', {class: 'src'}, src));
    box.append(t);
  };
  if (B.today) {
    const ids = B.songs, T = B.today, P = B.before;
    const now = mean(ids.map(id => T.rows.get(id).metrics.note_f1));
    const prevIds = P ? ids.filter(id => P.rows.has(id)) : [];
    const was = prevIds.length ? mean(prevIds.map(id => P.rows.get(id).metrics.note_f1)) : null;
    const nowSame = prevIds.length ? mean(prevIds.map(id => T.rows.get(id).metrics.note_f1)) : null;
    const d = was != null ? 100 * (nowSame - was) : null;
    const ratio = mean(ids.map(id => T.rows.get(id).metrics.count_ratio));
    const noEnds = mean(ids.map(id => T.rows.get(id).metrics.note_f1_no_offset));
    const ratioWas = prevIds.length ? mean(prevIds.map(id => P.rows.get(id).metrics.count_ratio)) : null;
    tile(B.mode === 'benchmark' ? 'Benchmark, band records' : 'Interim benchmark, band records', pts(now), 'note F1',
      d == null ? null : {text: `${signed(d)} since the default before (${P.m.when})`, cls: d > 0.05 ? '' : d < -0.05 ? 'down' : 'flat'},
      [`${ids.length} songs`, noEnds != null ? `Ignoring note ends ${pts(noEnds)} (${(100 * (noEnds - now)).toFixed(0)} points are note ends)` : null, ratio != null ? `Notes written per key note ${ratio.toFixed(2)}${ratioWas != null ? ` (was ${ratioWas.toFixed(2)})` : ''}` : null].filter(Boolean),
      `Average over the songs · today: ${T.m.label.join(' ').replace(/,? \+?$/, '')}`);
    const hit = ids.filter(id => T.rows.get(id).metrics.note_f1 >= BAND_TARGET).length;
    const hitWas = prevIds.filter(id => P.rows.get(id).metrics.note_f1 >= BAND_TARGET).length;
    tile('Songs at the band target', `${hit}`, `of ${ids.length}`,
      prevIds.length ? {text: `was ${hitWas} of ${prevIds.length} before`, cls: 'flat'} : null,
      ['Target: note F1 60 on a band record'], null);
  } else {
    tile('Benchmark, band records', '–', '', null, ['No per-song scores yet'], null);
  }
  // Clean sax: solo takes still use the standard path, scored by the scorecard over time.
  const solo = ['grfia-alto', 'grfia-tenor'].map(s => DATA.runs.filter(r => r.set === s && r.default && r.metrics.note_f1 != null).pop()).filter(Boolean);
  if (solo.length) {
    const a = solo[0], tgt = DATA.targets.note_f1 ? DATA.targets.note_f1.solo : 0.8;
    const gap = 100 * (tgt - a.metrics.note_f1);
    tile(`Clean sax, ${setName(a.set).replace(/^GRFIA RealSax, /, '')} recorded alone`, pts(a.metrics.note_f1), 'note F1',
      {text: gap <= 0 ? `Target ${Math.round(100 * tgt)} met` : `Target ${Math.round(100 * tgt)}: ${gap.toFixed(1)} to go`, cls: gap <= 0 ? '' : 'flat'},
      solo.slice(1).map(r => `${setName(r.set).replace(/^GRFIA RealSax, t/, 'T')} ${pts(r.metrics.note_f1)}`),
      `GRFIA RealSax studies · solo takes use the standard path · ${a.entry || fmtWhen(Date.parse(a.when), false)}`);
  }
}

function benchNote(B) {
  const box = $('#bench-note');
  const rev = prog.review;
  let s = B.mode === 'benchmark'
    ? `Benchmark: ${B.songs.length} songs whose answer key passed the match check (or that you marked good) and that no model trained on.`
    : 'Interim benchmark: your six tunes and the three Parker test records (E80). It becomes every song whose key passes the match check and that no model trained on, once the Mac re-scores each version on them.';
  if (rev && rev.exists) {
    const n = rev.entries.filter(e => e.benchmark).length;
    const todo = rev.entries.filter(needsLook).length;
    s += ` Match check so far: ${n} ${n === 1 ? 'pair qualifies' : 'pairs qualify'}${todo ? `, ${todo} wait for your review` : ''}.`;
  }
  box.textContent = s;
}

// ---------- staircase ----------
function stairs(B) {
  const box = $('#stairs');
  const steps = B.steps;
  const vals = steps.map(s => s.value).filter(v => v != null);
  if (!vals.length) { box.replaceChildren(el('p', {class: 'quiet'}, 'No benchmark scores yet.')); return; }
  const W = 1000, H = 320, L = 44, R = 24, T = 26, Bm = 70, iw = W - L - R, ih = H - T - Bm;
  const lo = Math.max(0, Math.floor(10 * Math.min(...vals, BAND_TARGET) - 1) / 10);
  const hi = Math.min(1, Math.ceil(10 * Math.max(...vals, BAND_TARGET) + 0.5) / 10);
  const x = i => L + iw * (i + 0.5) / steps.length, y = v => T + (1 - (v - lo) / (hi - lo)) * ih;
  let s = '';
  for (let v = lo; v <= hi + 1e-9; v += 0.1) {
    s += `<line class="gridline" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/>`;
    s += `<text x="${L - 8}" y="${y(v) + 4}" text-anchor="end">${Math.round(v * 100)}</text>`;
  }
  s += `<line class="target" x1="${L}" x2="${W - R}" y1="${y(BAND_TARGET)}" y2="${y(BAND_TARGET)}"/>`;
  s += `<text x="${W - R}" y="${y(BAND_TARGET) - 6}" text-anchor="end">band target 60</text>`;
  steps.forEach((st, i) => {
    s += `<text class="ms" x="${x(i)}" y="${H - Bm + 22}" text-anchor="middle">${esc(st.m.label[0])}</text>`;
    s += `<text class="ms" x="${x(i)}" y="${H - Bm + 38}" text-anchor="middle">${esc(st.m.label[1])}</text>`;
    s += `<text x="${x(i)}" y="${H - Bm + 56}" text-anchor="middle">${esc(st.m.when)}${st.m.pr ? ` · #${st.m.pr}` : ''}</text>`;
    if (st.value == null) {
      const msg = st.covered ? `${st.covered} of ${B.songs.length} songs re-scored` : 'Re-score waiting';
      s += `<circle cx="${x(i)}" cy="${T + ih - 14}" r="5" fill="none" stroke="var(--muted)" stroke-dasharray="2 2" stroke-width="1.5"/>`;
      s += `<text x="${x(i)}" y="${T + ih - 26}" text-anchor="middle">${esc(msg)}</text>`;
    }
  });
  let d = '';
  steps.forEach((st, i) => {
    if (st.value == null) return;
    d += d ? `H${x(i)}` : `M${x(i)},${y(st.value)}`;
    const nx = steps[i + 1];
    if (nx && nx.value != null) d += `H${(x(i) + x(i + 1)) / 2}V${y(nx.value)}`;
    else if (d) d += `M${x(i)},${y(st.value)}`;
  });
  s += `<path d="${d}" fill="none" stroke="var(--s-note)" stroke-width="2.5" stroke-linejoin="round"/>`;
  steps.forEach((st, i) => {
    if (st.value == null) return;
    s += `<circle cx="${x(i)}" cy="${y(st.value)}" r="5" fill="var(--s-note)" stroke="var(--card)" stroke-width="2"><title>${esc(st.m.label.join(' '))}: ${pts(st.value)}</title></circle>`;
    s += `<text class="val" x="${x(i)}" y="${y(st.value) - 12}" text-anchor="middle">${pts(st.value)}</text>`;
  });
  box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Average note F1 on the benchmark at each milestone">${s}</svg>`;
}

// ---------- dumbbells ----------
function dumbbells(B) {
  const box = $('#dumbbells');
  if (!B.today) { box.replaceChildren(el('p', {class: 'quiet'}, 'No per-song scores yet.')); return; }
  const T = B.today, P = B.before;
  const rows = B.songs.map(id => ({id, now: T.rows.get(id).metrics.note_f1, was: P && P.rows.has(id) ? P.rows.get(id).metrics.note_f1 : null, r: T.rows.get(id)}))
    .sort((a, b) => a.now - b.now);
  $('#dumb-note').textContent = `Grey dot: the default before${P ? ` (${P.m.when})` : ''}. Blue dot: today. ` +
    'Sorted by how far each song still has to go; the dashed line is the band target. Tap a song to open it on the Songs page.';
  const W = 560, rowH = 30, L = 170, R = 44, Tp = 6, H = Tp + rows.length * rowH + 26, iw = W - L - R;
  const x = v => L + v * iw;
  let s = '';
  for (const v of [0, 0.25, 0.5, 0.75, 1]) {
    s += `<line class="gridline" x1="${x(v)}" x2="${x(v)}" y1="${Tp}" y2="${H - 22}"/>`;
    s += `<text x="${x(v)}" y="${H - 6}" text-anchor="middle">${v * 100}</text>`;
  }
  s += `<line class="target" x1="${x(BAND_TARGET)}" x2="${x(BAND_TARGET)}" y1="${Tp}" y2="${H - 22}"/>`;
  rows.forEach((it, i) => {
    const cy = Tp + i * rowH + rowH / 2;
    const name = songName(it.id, it.r);
    s += `<g class="song" data-id="${esc(it.id)}" tabindex="0" role="link"><rect x="0" y="${cy - rowH / 2}" width="${W}" height="${rowH}" fill="transparent"/>`;
    s += `<text class="lbl" x="0" y="${cy + 4}">${esc(name.length > 24 ? name.slice(0, 23) + '…' : name)}<title>${esc(name)}</title></text>`;
    if (it.was != null) {
      s += `<line x1="${x(Math.min(it.was, it.now))}" x2="${x(Math.max(it.was, it.now))}" y1="${cy}" y2="${cy}" stroke="var(--axis)" stroke-width="3" stroke-linecap="round"/>`;
      s += `<circle cx="${x(it.was)}" cy="${cy}" r="5" fill="var(--muted)"><title>${esc(name)} before: ${pts(it.was)}</title></circle>`;
    }
    s += `<circle cx="${x(it.now)}" cy="${cy}" r="6" fill="var(--s-note)" stroke="var(--card)" stroke-width="1.5"><title>${esc(name)} today: ${pts(it.now)}</title></circle>`;
    s += `<text class="val" x="${W - R + 8}" y="${cy + 4}">${pts(it.now)}</text></g>`;
  });
  box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Note F1 per song, before and today">${s}</svg>`;
  for (const g of box.querySelectorAll('g.song')) {
    const go = () => openSong(g.dataset.id);
    g.addEventListener('click', go);
    g.addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
  }
}

// ---------- remaining errors ----------
function errors(B) {
  const box = $('#errors'); box.replaceChildren();
  const rows = B.today ? B.songs.map(id => B.today.rows.get(id)).filter(r => r.key_notes) : [];
  if (!rows.length) {
    box.append(el('p', {class: 'quiet'}, 'Shown once the Mac re-scores the benchmark with error counts (E81). ' +
      'Then this sums the two bars from each song’s page: what happened to every key note, and where every note we wrote came from.'));
    return;
  }
  const sum = side => { const o = {}; for (const r of rows) for (const [k, v] of Object.entries(r[side] || {})) o[k] = (o[k] || 0) + v; return o; };
  const kn = sum('key_notes'), on = sum('our_notes');
  const lanes = [['Key notes', kn, k => k.k, k => k.key], ['Our notes', on, k => k.ours_k || k.k, k => k.ours]];
  for (const [title, counts, kof, lab] of lanes) {
    const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
    box.append(el('div', {class: 'lane'}, `${title} (${total.toLocaleString()}${rows.length < B.songs.length ? `, ${rows.length} of ${B.songs.length} songs` : ''})`));
    const W = 560, Hh = 26; let x0 = 0, s = '';
    for (const k of KINDS) {
      const n = counts[kof(k)] || 0; if (!n) continue;
      const w = n / total * W;
      s += `<rect x="${x0}" y="0" width="${Math.max(0, w - 1.5)}" height="${Hh}" rx="3" fill="${k.c}"><title>${esc(lab(k))}: ${n} (${(100 * n / total).toFixed(1)}%)</title></rect>`;
      if (w > 44) s += `<text x="${x0 + 6}" y="${Hh / 2 + 4}" style="fill:#fff;font-weight:600">${Math.round(100 * n / total)}%</text>`;
      x0 += w;
    }
    const svg = el('div'); svg.innerHTML = `<svg viewBox="0 0 ${W} ${Hh}" role="img" aria-label="${esc(title)} by what happened">${s}</svg>`;
    box.append(svg);
  }
  const lg = el('div', {class: 'legend'});
  for (const k of KINDS) { const it = el('span', {class: 'key'}); const sw = el('span', {class: 'sw'}); sw.style.background = k.c; it.append(sw, document.createTextNode(k.key === k.ours ? k.key : `${k.key} / ${k.ours}`)); lg.append(it); }
  box.append(lg);
}

// ---------- songs list ----------
// Each column: heading, value used for sorting, cell text, cell class. Tap a heading to sort; tap again to flip.
function songCols(T, P) {
  const kn = r => { const k = r.key_notes, t = k ? Object.values(k).reduce((a, b) => a + b, 0) : 0; return x => t ? (k[x] || 0) / t : null; };
  const pct = v => v == null ? '–' : `${Math.round(100 * v)}%`;
  const delta = it => it.p ? 100 * (it.r.metrics.note_f1 - it.p.metrics.note_f1) : null;
  return [
    {h: 'Song', v: it => songName(it.id, it.r), t: it => songName(it.id, it.r)},
    {h: 'Player', v: it => (tagOf(it.id) || {}).player || '', t: it => (tagOf(it.id) || {}).player || '–'},
    {h: 'Year', num: true, v: it => (tagOf(it.id) || {}).year ?? null, t: it => String((tagOf(it.id) || {}).year ?? '–')},
    {h: 'Horn', v: it => (tagOf(it.id) || {}).horn || '', t: it => { const g = tagOf(it.id); return g ? g.horn + (g.horn_unsure ? '?' : '') : '–'; }},
    {h: 'Style', v: it => (tagOf(it.id) || {}).style || '', t: it => (tagOf(it.id) || {}).style || '–'},
    {h: 'Today', num: true, v: it => it.r.metrics.note_f1, t: it => pts(it.r.metrics.note_f1)},
    {h: 'Before', num: true, v: it => it.p ? it.p.metrics.note_f1 : null, t: it => it.p ? pts(it.p.metrics.note_f1) : '–'},
    {h: 'Change', num: true, v: delta, t: it => { const d = delta(it); return d == null ? '–' : signed(d); },
     c: it => { const d = delta(it); return d == null ? '' : d > 0.05 ? 'up' : d < -0.05 ? 'down' : ''; }},
    {h: 'Ignoring note ends', num: true, v: it => it.r.metrics.note_f1_no_offset, t: it => pts(it.r.metrics.note_f1_no_offset)},
    {h: 'Onset F1', num: true, v: it => it.r.metrics.onset_f1, t: it => pts(it.r.metrics.onset_f1)},
    ...[['missed', 'Missed'], ['timing', 'Timing off'], ['wrong_pitch', 'Wrong pitch'], ['merged', 'Merged']].map(([k, h]) =>
      ({h, num: true, v: it => kn(it.r)(k), t: it => pct(kn(it.r)(k))})),
    {h: 'Notes per key note', num: true, v: it => it.r.metrics.count_ratio, t: it => it.r.metrics.count_ratio != null ? it.r.metrics.count_ratio.toFixed(2) : '–'},
    {h: 'Key heard', num: true, v: it => it.r.key ? it.r.key.heard_ok : null, t: it => pct(it.r.key ? it.r.key.heard_ok : null)},
    {h: 'Source', v: it => it.r.entry || '', t: it => [it.r.entry, it.r.commit].filter(Boolean).join(' · ')},
  ];
}
function songsTable(B) {
  const table = $('#songs'); table.replaceChildren();
  $('#songs-empty').hidden = !!B.songs.length;
  if (!B.today) return;
  const T = B.today, P = B.before, cols = songCols(T, P);
  const sort = prog.sort || {h: 'Song', dir: 1};
  const head = el('tr');
  for (const c of cols) {
    const on = c.h === sort.h;
    const th = el('th', {class: `sort${c.num ? ' num' : ''}`, 'aria-sort': on ? (sort.dir > 0 ? 'ascending' : 'descending') : 'none'});
    const b = el('button', {type: 'button', class: 'th'}, c.h + (on ? (sort.dir > 0 ? ' ▲' : ' ▼') : ''));
    b.addEventListener('click', () => {
      // numbers start high-to-low, words A to Z
      prog.sort = on ? {h: c.h, dir: -sort.dir} : {h: c.h, dir: c.num ? -1 : 1};
      songsTable(B);
    });
    th.append(b); head.append(th);
  }
  table.append(head);
  const col = cols.find(c => c.h === sort.h) || cols[0];
  const items = B.songs.map(id => ({id, r: T.rows.get(id), p: P && P.rows.get(id)}));
  items.sort((a, b) => {
    const x = col.v(a), y = col.v(b);
    if (x == null || x === '') return (y == null || y === '') ? 0 : 1;   // blanks last either way
    if (y == null || y === '') return -1;
    return sort.dir * (typeof x === 'number' ? x - y : String(x).localeCompare(String(y)));
  });
  for (const it of items) {
    const tr = el('tr', {class: `pick${it.id === prog.song ? ' sel' : ''}`, 'data-id': it.id, tabindex: '0'});
    for (const c of cols) tr.append(el('td', {class: `${c.num ? 'num ' : ''}${c.c ? c.c(it) : ''}`.trim()}, c.t(it)));
    const go = () => openSong(it.id);
    tr.addEventListener('click', go);
    tr.addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
    table.append(tr);
  }
}

// ---------- one song across our models ----------
function songRows(id) {
  const rec = r => r._record || r.record;
  return EXP.filter(r => r.metrics.note_f1 != null &&
    (songOf(r) === id || rec(r) === id || (!r.record && r.set === id)));
}
function songHistory(id) {
  const card = $('#song-history');
  const B = prog.B; if (!B) return;
  const tg = tagOf(id) || {};
  const rows = songRows(id);
  card.hidden = false;
  $('#hist-title').textContent = `${songName(id, B.today && B.today.rows.get(id))}: history`;
  $('#hist-meta').textContent = [tg.player, tg.year, tg.album, tg.horn && `${tg.horn}${tg.horn_unsure ? ' (guess)' : ''}`, tg.style].filter(Boolean).join(' · ');
  // the chart: one point per milestone that scored this song on the benchmark
  const pts_ = B.steps.map(st => ({st, r: st.rows.get(id)})).filter(x => x.r);
  const box = $('#hist-chart');
  if (pts_.length) {
    const W = 1000, H = 280, L = 40, R = 20, T = 22, Bm = 62, iw = W - L - R, ih = H - T - Bm;
    const n = B.steps.length;
    const x = i => L + iw * (i + 0.5) / n, y = v => T + (1 - v) * ih;
    let s = '';
    for (const v of [0, 0.25, 0.5, 0.75, 1]) s += `<line class="gridline" x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}"/><text x="${L - 8}" y="${y(v) + 4}" text-anchor="end">${v * 100}</text>`;
    s += `<line class="target" x1="${L}" x2="${W - R}" y1="${y(BAND_TARGET)}" y2="${y(BAND_TARGET)}"/>`;
    B.steps.forEach((st, i) => {
      s += `<text class="ms" x="${x(i)}" y="${H - Bm + 20}" text-anchor="middle">${esc(st.m.label[0])}</text>`;
      s += `<text class="ms" x="${x(i)}" y="${H - Bm + 35}" text-anchor="middle">${esc(st.m.label[1])}</text>`;
      s += `<text x="${x(i)}" y="${H - Bm + 51}" text-anchor="middle">${esc(st.m.when)}</text>`;
    });
    const ix = p => B.steps.indexOf(p.st);
    for (const [k, cls, w] of [['note_f1_no_offset', 'var(--muted)', 1.5], ['note_f1', 'var(--s-note)', 2.5]]) {
      const ps = pts_.filter(p => p.r.metrics[k] != null);
      if (!ps.length) continue;
      s += `<path d="${ps.map((p, j) => `${j ? 'L' : 'M'}${x(ix(p))},${y(p.r.metrics[k])}`).join('')}" fill="none" stroke="${cls}" stroke-width="${w}"${k === 'note_f1' ? '' : ' stroke-dasharray="4 3"'}/>`;
      for (const p of ps) {
        s += `<circle cx="${x(ix(p))}" cy="${y(p.r.metrics[k])}" r="${k === 'note_f1' ? 5 : 3.5}" fill="${cls}" stroke="var(--card)" stroke-width="1.5"><title>${esc(p.st.m.label.join(' '))}: ${k === 'note_f1' ? 'note F1' : 'ignoring note ends'} ${pts(p.r.metrics[k])}</title></circle>`;
        if (k === 'note_f1') s += `<text class="val" x="${x(ix(p))}" y="${y(p.r.metrics[k]) - 10}" text-anchor="middle">${pts(p.r.metrics[k])}</text>`;
      }
    }
    box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Note F1 for this song at each version">${s}</svg>`;
  } else box.replaceChildren(el('p', {class: 'quiet small'}, 'No benchmark versions scored this song yet; the table below has every run.'));
  // the table: every setup ever run on this song
  const t = $('#hist-table'); t.replaceChildren();
  const head = el('tr');
  for (const h of ['Scored on', 'Setup', 'Answer key from', 'Note F1', 'Ignoring note ends', 'Onset F1', 'Pitch', 'Source']) head.append(el('th', {class: ['Note F1', 'Ignoring note ends', 'Onset F1', 'Pitch'].includes(h) ? 'num' : ''}, h));
  t.append(head);
  const ms = r => MILESTONES.find(m => matches(m, r));
  const today = B.today && B.today.rows.get(id);
  // milestones in the order they became the default, then every other run by date
  const order = r => { const i = MILESTONES.findIndex(m => matches(m, r)); return i < 0 ? `9${r.when || ''}` : `${i}`; };
  for (const r of rows.slice().sort((a, b) => order(a).localeCompare(order(b)))) {
    const tr = el('tr', {class: r === today ? 'avg' : ''});
    const m = ms(r);
    const setup = el('td', {}, setupName(r.setup));
    const role = r === today ? 'today’s default' : m ? `milestone: ${m.label.join(' ').replace(/,? \+?$/, '')}` : roleOf(setupKey(r.setup));
    if (role) setup.append(el('div', {class: 'small quiet'}, role));
    tr.append(el('td', {class: 'num'}, r.when ? r.when.slice(0, 10) : '–'), setup,
      el('td', {class: 'small'}, (RECORDS[r._set || r.set] || [r._set || r.set])[0]));
    for (const k of ['note_f1', 'note_f1_no_offset', 'onset_f1', 'pitch_accuracy']) tr.append(el('td', {class: 'num'}, pts(r.metrics[k])));
    tr.append(el('td', {class: 'small'}, [r.entry, r.commit].filter(Boolean).join(' · ')));
    t.append(tr);
  }
}

// ---------- scores by horn and by style ----------
function tagOf(id) { const t = DATA.tags || {}; return t[id] || t[String(id).replace(/^parker-test\//, '')] || null; }
function groups(B) {
  const table = $('#tag-groups'); table.replaceChildren();
  const T = B.today, P = B.before;
  const tagged = T ? B.songs.filter(id => tagOf(id)) : [];
  $('#groups-empty').hidden = !!tagged.length;
  if (!tagged.length) return;
  const field = prog.groupBy || 'horn';
  const head = el('tr');
  const label = {horn: 'Horn', style: 'Style', era: 'Era', player: 'Player'}[field];
  for (const h of [label, 'Songs', 'Today', 'Before', 'Change', 'Ignoring note ends', 'At target 60']) head.append(el('th', {class: h === label ? '' : 'num'}, h));
  table.append(head);
  const by = new Map();
  for (const id of tagged) { const v = tagOf(id)[field] || (field === 'player' ? 'Player unknown' : 'Not tagged'); by.set(v, (by.get(v) || []).concat([id])); }
  for (const [v, ids] of [...by.entries()].sort((a, b) => (a[0] === 'Not tagged') - (b[0] === 'Not tagged') || b[1].length - a[1].length || String(a[0]).localeCompare(String(b[0])))) {
    const now = mean(ids.map(id => T.rows.get(id).metrics.note_f1));
    const pids = P ? ids.filter(id => P.rows.has(id)) : [];
    const was = pids.length ? mean(pids.map(id => P.rows.get(id).metrics.note_f1)) : null;
    const d = was != null ? 100 * (mean(pids.map(id => T.rows.get(id).metrics.note_f1)) - was) : null;
    const row = el('tr');
    row.append(el('td', {}, String(v)), el('td', {class: 'num'}, String(ids.length)), el('td', {class: 'num'}, pts(now)),
      el('td', {class: 'num'}, was == null ? '–' : pts(was)),
      el('td', {class: `num ${d == null ? '' : d > 0.05 ? 'up' : d < -0.05 ? 'down' : ''}`}, d == null ? '–' : signed(d)),
      el('td', {class: 'num'}, pts(mean(ids.map(id => T.rows.get(id).metrics.note_f1_no_offset)))),
      el('td', {class: 'num'}, `${ids.filter(id => T.rows.get(id).metrics.note_f1 >= BAND_TARGET).length} of ${ids.length}`));
    table.append(row);
  }
  const unsure = tagged.filter(id => tagOf(id).horn_unsure).length, unchecked = tagged.filter(id => !tagOf(id).checked).length;
  $('#groups-note').textContent = unchecked ? `Tags are a draft until checked by ear (${unchecked} of ${tagged.length} not checked yet` +
    `${unsure ? `; ${unsure} ${unsure === 1 ? 'horn is a guess' : 'horns are guesses'}, marked ? on the Songs tab` : ''}). Groups with one or two songs move a lot from song to song.` : '';
}
segment($('#tag-by'), v => { prog.groupBy = v; if (prog.B) groups(prog.B); });

// ---------- experiment cards (Log tab) ----------
const CARD_FIELDS = [['problem', 'Problem'], ['hypothesis', 'Hypothesis'], ['changed', 'What changed'], ['measure', 'Measured with'],
                     ['result', 'Result'], ['learned', 'What we learned'], ['decision', 'Decision'], ['revisit', 'Revisit when']];
function cards() {
  const box = $('#cards'); box.replaceChildren();
  const all = (DATA.cards || []).slice().sort((a, b) => parseInt(b.entry.slice(1)) - parseInt(a.entry.slice(1)));
  $('#cards-empty').hidden = !!all.length;
  for (const c of all) {
    const d = el('details', {class: 'xcard'});
    const sum = el('summary');
    sum.append(el('span', {class: 'xid'}, c.entry), el('span', {class: 'xtitle'}, c.title),
      el('span', {class: 'quiet small'}, ` · ${fmtWhen(Date.parse(c.date + 'T12:00:00Z'), false)} · ${c.stage}`));
    sum.append(el('div', {class: 'small xres'}, c.result));
    d.append(sum);
    const dl = el('dl', {class: 'small'});
    for (const [k, lab] of CARD_FIELDS) if (c[k]) dl.append(el('dt', {}, lab), el('dd', {}, c[k]));
    d.append(dl);
    box.append(d);
  }
}

// Open a song on the Songs page: highlight its row, show its history and, where it has bar counts, its bar view.
function openSong(id) {
  showTab('songs', false);
  prog.song = id;
  for (const tr of document.querySelectorAll('#songs tr.pick')) tr.classList.toggle('sel', tr.dataset.id === id);
  if (EXP.some(r => rowKey(r) === id && r.bars && r.bars.length)) { cmp.record = id; along(); }
  songHistory(id);
  $('#song-history').scrollIntoView({block: 'start'});
}

function renderProgress() {
  const B = benchmark();
  prog.B = B;
  tiles(B); benchNote(B); stairs(B); dumbbells(B); errors(B); groups(B); songsTable(B); cards();
}
