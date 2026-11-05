// Results page: scorecard history per test set, with a marker for each model or pipeline change.
// Data: GET /api/results (saxscribe/score/history.py). Charts are plain SVG.

const SERIES = [
  {key: 'note_f1', name: 'Note F1', color: 'var(--s-note)'},
  {key: 'onset_f1', name: 'Onset F1', color: 'var(--s-onset)'},
  {key: 'pitch_accuracy', name: 'Pitch accuracy', color: 'var(--s-pitch)'},
];
const KEY_SERIES = [{key: 'key_accuracy', name: 'Home key right', color: 'var(--s-note)'}];
const SET_INFO = {
  'omnibook': ['Charlie Parker Omnibook', 'Parker solos, sax stems separated from the records'],
  'omnibook-mix': ['Parker band records', 'The same solos from the full records, separated by Demucs'],
  'urmp': ['URMP', 'Classical sax parts, each recorded alone'],
  'urmp-mix': ['URMP in the ensemble', 'The same parts inside the full chamber mix'],
  'bach10': ['Bach10', 'The sax part of 10 Bach chorales, recorded alone'],
  'bach10-mix': ['Bach10 in the quartet', 'The sax part inside the full quartet'],
  'choralebricks': ['ChoraleBricks', 'Alto and baritone chorale parts, recorded alone'],
  'grfia-alto': ['GRFIA RealSax, alto', 'One player, real alto takes of written studies'],
  'grfia-tenor': ['GRFIA RealSax, tenor', 'One player, real tenor takes of written studies'],
  'filosax': ['Filosax', 'Jazz tenor with backing tracks'],
  'pairs': ['Your recordings', 'Your takes paired with their answer keys'],
  'weimar-key': ['Weimar Jazz Database: key', 'Key finding only, on 430 transcribed jazz solos'],
};
const ORDER = ['omnibook', 'omnibook-mix', 'urmp', 'bach10', 'choralebricks', 'grfia-alto', 'grfia-tenor',
               'filosax', 'pairs', 'urmp-mix', 'bach10-mix', 'weimar-key'];
const REPO = 'https://github.com/GetVizzyWithIt/Saxscribe/pull/';

let DATA = null;
const state = {range: 'all', marks: 'scored'};

function pct(v) { return v == null ? '–' : `${(100 * v).toFixed(1)}%`; }
function setName(s) { return (SET_INFO[s] || [s])[0]; }
function seriesFor(set) { return set === 'weimar-key' ? KEY_SERIES : SERIES; }
function isMix(set) { return DATA.mix_sets.includes(set); }
function t(rec) { return Date.parse(rec.when); }
function fmtWhen(ms, withTime = true) {
  const d = new Date(ms);
  const day = d.toLocaleDateString(undefined, {month: 'short', day: 'numeric'});
  return withTime ? `${day}, ${d.toLocaleTimeString(undefined, {hour: 'numeric', minute: '2-digit'})}` : day;
}
function el(tag, attrs = {}, text) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text != null) e.textContent = text;
  return e;
}

function inRange(ms) {
  if (state.range === 'all') return true;
  return ms >= Date.now() - Number(state.range) * 86400e3;
}
function visibleRuns() { return DATA.runs.filter(r => inRange(t(r))); }
function visibleChanges() {
  return DATA.changes.filter(c => c.merged && inRange(Date.parse(c.merged)) &&
    (state.marks === 'all' || (c.sets && c.sets.length)));
}

// ---------- standings ----------
function standings() {
  const table = $('#standings'); table.replaceChildren();
  const head = el('tr');
  for (const h of ['Set', 'Note F1', 'Onset F1', 'Pitch', 'Sax found', 'Sax purity', 'Seconds per minute', 'Note F1 vs the run before', 'Last run'])
    head.append(el('th', {}, h));
  table.append(head);
  const sets = ORDER.filter(s => DATA.runs.some(r => r.set === s))
    .concat([...new Set(DATA.runs.map(r => r.set))].filter(s => !ORDER.includes(s)));
  for (const set of sets) {
    const defaults = DATA.runs.filter(r => r.set === set && r.default);
    const last = defaults[defaults.length - 1] || DATA.runs.filter(r => r.set === set).pop();
    const prev = defaults.slice(0, -1).reverse().find(r => r.metrics.note_f1 != null);
    const tr = el('tr');
    tr.append(el('td', {}, setName(set)));
    const which = isMix(set) ? 'mix' : 'solo';
    const m = last.metrics;
    if (set === 'weimar-key') {
      const td = el('td', {class: 'num'}, `${pct(m.key_accuracy)} home key right`);
      td.colSpan = 6; tr.append(td);
    } else {
      for (const k of ['note_f1', 'onset_f1', 'pitch_accuracy', 'sax_found', 'sax_purity', 'seconds_per_minute']) {
        const v = m[k], target = DATA.targets[k] && DATA.targets[k][which];
        const td = el('td', {class: 'num'});
        if (v == null) { td.textContent = '–'; tr.append(td); continue; }
        const ok = target != null && (k === 'seconds_per_minute' ? v <= target : v >= target);
        td.textContent = k === 'seconds_per_minute' ? `${Math.round(v)} s` : pct(v);
        if (ok) { td.append(' '); td.append(el('span', {class: 'met', title: 'meets the v1 target'}, '✓')); }
        tr.append(td);
      }
    }
    const dtd = el('td', {class: 'num'});
    if (prev && m.note_f1 != null) {
      const d = 100 * (m.note_f1 - prev.metrics.note_f1);
      const regraded = DATA.changes.some(c => c.layer === 'scorecard' && c.merged &&
        Date.parse(c.merged) > t(prev) && Date.parse(c.merged) < t(last));
      dtd.textContent = `${d >= 0 ? '▲ +' : '▼ '}${d.toFixed(1)} points${regraded ? ' (grading changed)' : ''}`;
      dtd.className = `num ${d > 0.05 ? 'up' : d < -0.05 ? 'down' : ''}`;
    } else dtd.textContent = '–';
    tr.append(dtd);
    tr.append(el('td', {class: 'num'}, fmtWhen(t(last), false) + (last.entry ? ` (${last.entry})` : '')));
    table.append(tr);
  }
}

// ---------- legend ----------
function legend() {
  const box = $('#legend'); box.replaceChildren();
  const ns = 'http://www.w3.org/2000/svg';
  const add = (draw, label) => {
    const k = el('span', {class: 'key'});
    const svg = document.createElementNS(ns, 'svg'); svg.setAttribute('width', 22); svg.setAttribute('height', 12);
    svg.innerHTML = draw; k.append(svg, document.createTextNode(label)); box.append(k);
  };
  for (const s of SERIES) add(`<line x1="1" y1="6" x2="21" y2="6" stroke="${s.color}" stroke-width="2" stroke-linecap="round"/>`, s.name);
  add('<circle cx="11" cy="6" r="4" fill="none" stroke="var(--muted)" stroke-width="2"/>', 'Other settings');
  add('<line x1="11" y1="0" x2="11" y2="12" stroke="var(--ink2)" stroke-width="1"/>', 'Change (pull request)');
  add('<line x1="1" y1="6" x2="21" y2="6" stroke="var(--muted)" stroke-dasharray="4 4"/>', 'Note F1 target');
}

// ---------- panels ----------
const H = 220, M = {l: 40, r: 52, t: 26, b: 26};

function timeTicks(lo, hi, width) {
  const steps = [3600e3, 3 * 3600e3, 6 * 3600e3, 12 * 3600e3, 86400e3, 2 * 86400e3, 7 * 86400e3, 14 * 86400e3, 30 * 86400e3, 91 * 86400e3];
  const want = Math.max(2, Math.floor(width / 110));
  const step = steps.find(s => (hi - lo) / s <= want) || steps[steps.length - 1];
  const off = new Date().getTimezoneOffset() * 60e3;  // align ticks to local midnight / hours
  const out = [];
  for (let v = Math.ceil((lo - off) / step) * step + off; v <= hi; v += step) out.push(v);
  return {ticks: out, daily: step >= 86400e3};
}

function clusterMarks(changes, x, minGap) {
  const groups = [];
  for (const c of changes.slice().sort((a, b) => Date.parse(a.merged) - Date.parse(b.merged))) {
    const px = x(Date.parse(c.merged));
    const g = groups[groups.length - 1];
    if (g && px - g.px1 < minGap) { g.items.push(c); g.px1 = px; } else groups.push({px0: px, px1: px, items: [c]});
  }
  return groups;
}

function panel(set, runs, changes, lo, hi) {
  const card = el('section', {class: 'panel'});
  const info = SET_INFO[set] || [set, ''];
  card.append(el('h3', {}, info[0]));
  const items = runs.length ? Math.max(...runs.map(r => r.items || 0)) : 0;
  const which = isMix(set) ? 'full-mix' : 'solo-recording';
  card.append(el('p', {class: 'sub'}, `${info[1]}${info[1] ? '. ' : ''}${items ? items + ' recordings' : ''}${set === 'weimar-key' ? '' : `, ${which} targets`}.`));
  const holder = el('div'); card.append(holder);
  const series = seriesFor(set);

  function draw() {
    const W = Math.max(280, holder.clientWidth || 520);
    const iw = W - M.l - M.r, ih = H - M.t - M.b;
    const span = Math.max(hi - lo, 3600e3);
    const pad = span * 0.04;
    const x0 = lo - pad, x1 = hi + pad;
    const x = ms => M.l + (ms - x0) / (x1 - x0) * iw;
    const y = v => M.t + (1 - v) * ih;
    let s = '';
    for (const v of [0, 0.25, 0.5, 0.75, 1]) {
      s += `<line class="${v ? 'gridline' : 'baseline'}" x1="${M.l}" x2="${M.l + iw}" y1="${y(v)}" y2="${y(v)}"/>`;
      s += `<text x="${M.l - 6}" y="${y(v) + 4}" text-anchor="end">${v * 100}%</text>`;
    }
    const {ticks, daily} = timeTicks(x0, x1, iw);
    for (const tk of ticks) s += `<text x="${x(tk)}" y="${H - 6}" text-anchor="middle">${esc(fmtWhen(tk, !daily))}</text>`;
    // the note F1 target
    const tgt = series === SERIES && DATA.targets.note_f1 ? DATA.targets.note_f1[isMix(set) ? 'mix' : 'solo'] : null;
    if (tgt != null) s += `<line class="target" x1="${M.l}" x2="${M.l + iw}" y1="${y(tgt)}" y2="${y(tgt)}"/>`;
    // change markers: the ones measured on this set stand out
    for (const g of clusterMarks(changes, x, 34)) {
      const mine = g.items.some(c => (c.sets || []).includes(set));
      for (const c of g.items) {
        const px = x(Date.parse(c.merged));
        s += `<line class="marker ${mine ? '' : 'other'}" x1="${px}" x2="${px}" y1="${M.t - 6}" y2="${M.t + ih}"/>`;
      }
      const label = g.items.length > 2 ? `#${g.items[0].pr}–${g.items[g.items.length - 1].pr}` : g.items.map(c => `#${c.pr}`).join(' ');
      s += `<text class="${mine ? 'mark' : ''}" x="${(g.px0 + g.px1) / 2}" y="${M.t - 10}" text-anchor="middle">${esc(label)}</text>`;
    }
    // lines through the default runs, open circles for other settings
    for (const sr of series) {
      const pts = runs.filter(r => r.default && r.metrics[sr.key] != null);
      if (pts.length > 1)
        s += `<polyline fill="none" stroke="${sr.color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" points="${pts.map(r => `${x(t(r))},${y(r.metrics[sr.key])}`).join(' ')}"/>`;
      for (const r of runs) {
        const v = r.metrics[sr.key];
        if (v == null) continue;
        s += r.default
          ? `<circle cx="${x(t(r))}" cy="${y(v)}" r="4" fill="${sr.color}" stroke="var(--card)" stroke-width="2"/>`
          : `<circle cx="${x(t(r))}" cy="${y(v)}" r="4" fill="var(--card)" stroke="${sr.color}" stroke-width="2"/>`;
      }
    }
    // one direct label: the latest default note F1 (or key accuracy)
    const main = series[0];
    const lastPt = runs.filter(r => r.default && r.metrics[main.key] != null).pop();
    if (lastPt) s += `<text class="end" x="${x(t(lastPt)) + 8}" y="${y(lastPt.metrics[main.key]) + 4}">${pct(lastPt.metrics[main.key]).replace('.0%', '%')}</text>`;
    s += `<line class="cross" id="cross" x1="0" x2="0" y1="${M.t}" y2="${M.t + ih}" visibility="hidden"/>`;
    s += `<rect x="${M.l}" y="0" width="${iw}" height="${H}" fill="transparent"/>`;
    holder.innerHTML = `<svg viewBox="0 0 ${W} ${H}" height="${H}" role="img" aria-label="${esc(info[0])}: scores over time"><title>${esc(info[0])}</title>${s}</svg>`;
    hover(holder.querySelector('svg'), x, runs, changes, series);
  }
  card.draw = draw;
  return card;
}

// The crosshair snaps to the nearest run (or change marker); the tip lists everything there.
function hover(svg, x, runs, changes, series) {
  const tip = $('#tip'), cross = svg.querySelector('#cross');
  const spots = [...new Set(runs.map(t))].map(ms => ({ms, runs: runs.filter(r => t(r) === ms)}))
    .concat(changes.map(c => ({ms: Date.parse(c.merged), change: c})));
  function show(ev) {
    const box = svg.getBoundingClientRect();
    const sx = (ev.clientX - box.left) * (svg.viewBox.baseVal.width / box.width);
    let best = null, bd = 1e9;
    for (const sp of spots) { const d = Math.abs(x(sp.ms) - sx); if (d < bd) { bd = d; best = sp; } }
    if (!best || bd > 40) { hide(); return; }
    cross.setAttribute('x1', x(best.ms)); cross.setAttribute('x2', x(best.ms)); cross.setAttribute('visibility', 'visible');
    tip.replaceChildren();
    if (best.change) {
      const c = best.change;
      tip.append(el('div', {class: 'when'}, `${fmtWhen(best.ms)} · merged`));
      tip.append(el('div', {}, `#${c.pr} ${c.title}`));
      tip.append(el('div', {class: 'note'}, `${c.measure}: ${c.before} → ${c.after}${c.kept === false ? ' (not kept)' : ''}`));
    } else {
      for (const r of best.runs) {
        const d = el('div', {class: 'run'});
        d.append(el('div', {class: 'when'}, `${fmtWhen(best.ms)} · ${r.default ? 'default settings' : r.settings}${r.entry ? ' · ' + r.entry : ''}${r.commit ? ' · ' + r.commit : ''}`));
        for (const sr of series) {
          const v = r.metrics[sr.key]; if (v == null) continue;
          const row = el('div', {class: 'row'});
          const k = el('span', {class: r.default ? 'k' : 'ring'});
          if (r.default) k.style.background = sr.color; else k.style.borderColor = sr.color;
          row.append(k, el('b', {}, pct(v)), el('span', {}, sr.name));
          d.append(row);
        }
        if (r.metrics.seconds_per_minute != null) d.append(el('div', {class: 'row'}, `${Math.round(r.metrics.seconds_per_minute)} s per minute of audio`));
        if (r.note) d.append(el('div', {class: 'note'}, r.note));
        tip.append(d);
      }
    }
    tip.hidden = false;
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    let left = ev.clientX + 14; if (left + tw > innerWidth - 8) left = ev.clientX - tw - 14;
    let top = ev.clientY - th - 12; if (top < 8) top = ev.clientY + 16;
    tip.style.left = `${Math.max(8, left)}px`; tip.style.top = `${top}px`;
  }
  function hide() { tip.hidden = true; cross.setAttribute('visibility', 'hidden'); }
  svg.addEventListener('pointermove', show);
  svg.addEventListener('pointerdown', show);
  svg.addEventListener('pointerleave', ev => { if (ev.pointerType === 'mouse') hide(); });
}
document.addEventListener('pointerdown', ev => { if (!ev.target.closest('.panel svg')) $('#tip').hidden = true; });

let panels = [];
function charts() {
  const box = $('#panels'); box.replaceChildren(); panels = [];
  const runs = visibleRuns(), changes = visibleChanges();
  if (!runs.length) { box.append(el('p', {class: 'quiet'}, 'No scorecard runs in this range yet.')); return; }
  const times = runs.map(t).concat(changes.map(c => Date.parse(c.merged)));
  const lo = Math.min(...times), hi = Math.max(...times);
  const sets = ORDER.filter(s => runs.some(r => r.set === s))
    .concat([...new Set(runs.map(r => r.set))].filter(s => !ORDER.includes(s)));
  for (const set of sets) {
    const p = panel(set, runs.filter(r => r.set === set), changes, lo, hi);
    box.append(p); panels.push(p);
  }
  panels.forEach(p => p.draw());
}

function changeTable() {
  const table = $('#changes'); table.replaceChildren();
  const head = el('tr');
  for (const h of ['Change', 'Merged', 'Layer', 'Measured on', 'Before', 'After', 'Kept']) head.append(el('th', {}, h));
  table.append(head);
  const rows = DATA.changes.slice().sort((a, b) => (b.merged || '9') < (a.merged || '9') ? -1 : 1);
  for (const c of rows) {
    const tr = el('tr');
    const td = el('td');
    td.append(el('a', {href: REPO + c.pr, target: '_blank', rel: 'noopener'}, `#${c.pr}`), ` ${c.title}`);
    tr.append(td);
    tr.append(el('td', {class: 'num'}, c.merged ? fmtWhen(Date.parse(c.merged), false) : 'open'));
    tr.append(el('td', {}, c.layer || ''));
    tr.append(el('td', {}, c.measure || ''));
    tr.append(el('td', {class: 'num'}, c.before || ''));
    tr.append(el('td', {class: 'num'}, c.after || ''));
    tr.append(el('td', {}, c.kept == null ? 'pending' : c.kept ? 'yes' : 'no'));
    table.append(tr);
  }
}

function runTable() {
  const table = $('#runs'); table.replaceChildren();
  const head = el('tr');
  for (const h of ['When', 'Set', 'Settings', 'Recordings', 'Note F1', 'Onset F1', 'Pitch', 'Octave errors', 'Sax found', 'Sax purity', 's/min', 'Source'])
    head.append(el('th', {}, h));
  table.append(head);
  for (const r of visibleRuns().slice().reverse()) {
    const m = r.metrics, tr = el('tr');
    tr.append(el('td', {class: 'num'}, fmtWhen(t(r))));
    tr.append(el('td', {}, setName(r.set)));
    tr.append(el('td', {}, r.default ? `default${r.settings !== 'default' ? ' (' + r.settings + ')' : ''}` : r.settings));
    tr.append(el('td', {class: 'num'}, r.items ?? ''));
    tr.append(el('td', {class: 'num'}, r.set === 'weimar-key' ? `key ${pct(m.key_accuracy)}` : pct(m.note_f1)));
    for (const k of ['onset_f1', 'pitch_accuracy', 'octave_errors', 'sax_found', 'sax_purity']) tr.append(el('td', {class: 'num'}, pct(m[k])));
    tr.append(el('td', {class: 'num'}, m.seconds_per_minute != null ? Math.round(m.seconds_per_minute) : '–'));
    tr.append(el('td', {}, r.entry ? `log ${r.entry}` : r.commit ? `scorecard at ${r.commit}${r.dirty ? ' (uncommitted changes)' : ''}` : 'scorecard'));
    table.append(tr);
  }
}

function render() {
  if (typeof renderCompare === 'function') renderCompare();
  standings(); legend(); charts(); changeTable(); runTable();
}

segment($('#range'), v => { state.range = v; charts(); runTable(); });
segment($('#marks'), v => { state.marks = v; charts(); });
let rt; addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => panels.forEach(p => p.draw()), 150); });

(async () => {
  try {
    const r = await fetch('/api/results');
    DATA = await r.json();
  } catch (e) {
    $('#panels').replaceChildren(el('p', {class: 'failed'}, 'Could not load the results.'));
    return;
  }
  render();
  const local = DATA.runs.filter(r => r.source === 'scorecard').length;
  $('#sources').textContent = `${DATA.runs.length} runs: ${DATA.runs.length - local} from the evaluation log, ` +
    `${local} from scorecards run on this Mac. Every python -m saxscribe score run adds itself here.`;
})();
