// Results page, comparison views: where each record stands, setups compared side by side,
// where the notes go (error breakdown) and along the record (bar by bar).
// Data: DATA.experiments (score/experiments.py), DATA.runs (score/history.py). Plain SVG and tables.

const SEPARATORS = {
  'demucs': 'Demucs', 'demucs-6s': 'Demucs',
  'mega': 'MVSep Mega 53-stem', 'mega-local': 'MVSep Mega 53-stem',
  'rd-filosax-demucs': 'Riley & Dixon sax Demucs',
  'hybrid': 'Mega + Demucs fallback',
  'mvsep-web': 'MVSep website sax',
  'rd-sax': 'Riley & Dixon sax Demucs',
};
const SEP_ORDER = ['demucs', 'demucs-6s', 'mega', 'mega-local', 'hybrid', 'mvsep-web', 'rd-sax', 'rd-filosax-demucs'];
const FINDERS = {'ours': '', 'rd-filosax': 'R&D note model', 'rd-filosax_25k': 'R&D note model'};
const RECORDS = {
  'parker-band': ['Parker band records', 'band'],
  'pfh': ['Pennies From Heaven', 'band'],
  'bfmj': ['Blues for Mary Jane', 'band'],
  'resolution': ['Resolution', 'band'],
  'weimar': ['Weimar solos', 'band'],
  'walkers-theme': ["Walker's Theme", 'pop'],
  'isnt-she-lovely': ["Isn't She Lovely (solo)", 'pop'],
  'bloody-well-right': ['Bloody Well Right (solo)', 'pop'],
  'new-tunes': ['Four tenor tunes', 'pop'],
};
// Answer keys partly built with a model under test: its scores there are not a clean win.
// The Omnibook's alignment used a Riley & Dixon transcription model (their paper, section 3.1).
// A row can also carry key.favours: [note_finder, ...] itself.
const KEY_FAVOURS = {'parker-band': ['rd-filosax', 'rd-filosax_25k'], 'omnibook': ['rd-filosax', 'rd-filosax_25k']};
function keyFavours(r) {
  const f = (r.key && r.key.favours) || KEY_FAVOURS[r.set] || [];
  return f.includes(r.setup.note_finder) || f.includes(r.setup.separator);
}
const TIERS = [['clean', 'Clean sax (recorded alone or pre-separated)'], ['band', 'Jazz band records'],
               ['pop', 'Pop and fusion records']];
const CLEAN_SETS = ['bach10', 'choralebricks', 'grfia-alto', 'grfia-tenor', 'urmp', 'omnibook'];
const GRID_METRICS = [
  ['note_f1', 'Note F1'], ['sax_found', 'Sax found'], ['sax_purity', 'Sax purity'],
  ['onset_recall', 'Onset recall'], ['pitch_accuracy', 'Pitch'], ['sax_found_heard', 'Found, heard key notes'],
];
// Where the notes go. Slot order is fixed and validated (adjacent pairs, light and dark); the
// two sides share a colour where the error is the same kind seen from either side.
const KINDS = [
  {k: 'right', key: 'Found', ours: 'Right', c: 'var(--k-right)'},
  {k: 'timing', key: 'Found 50–150 ms off', ours: '50–150 ms off', c: 'var(--k-timing)'},
  {k: 'wrong_pitch', key: 'Wrong pitch', ours: 'Wrong pitch', c: 'var(--k-pitch)'},
  {k: 'merged', ours_k: 'split', key: 'Merged into the note before', ours: 'Split off a held note', c: 'var(--k-bound)'},
  {k: 'missed', ours_k: 'extra', key: 'Missed', ours: 'Extra while the sax plays', c: 'var(--k-miss)'},
  {k: 'hidden', ours_k: 'in_rest', key: 'Hidden: tagged not sax', ours: 'In a rest of the key', c: 'var(--k-rest)'},
];
const FLAG_DROP = 0.03;   // sax found (or onset recall) this much under the default setup: lost sax

const cmp = {metric: 'note_f1', setup: null, record: null};
let EXP = [];

// Names the Mac and the log use for the same thing.
const ALIAS = {'demucs-6s': 'demucs', 'mega-local': 'mega', 'rd-filosax-demucs': 'rd-sax', 'own': 'same',
               'rd-filosax_25k': 'rd-filosax'};
function canon(v, d) { return ALIAS[v] || v || d; }
function setupKey(s) { return `${canon(s.separator)}|${canon(s.spans_from, 'same')}|${canon(s.note_finder, 'ours')}`; }
function setupName(s) {
  let n = SEPARATORS[s.separator] || s.separator;
  if (s.spans_from && !['same', 'own'].includes(s.spans_from)) n += `, rests from ${SEPARATORS[s.spans_from] || s.spans_from}`;
  if (FINDERS[s.note_finder]) n += `, ${FINDERS[s.note_finder]}`;
  else if (s.note_finder && s.note_finder !== 'ours') n += `, ${s.note_finder}`;
  return n;
}
function rowKey(r) { return r.record ? `${r.set}/${r.record}` : r.set; }
function rowInfo(r) {
  if (r.record && RECORDS[r.record]) return {name: RECORDS[r.record][0], tier: RECORDS[r.record][1], sub: false};
  const base = RECORDS[r.set] || [r.set, 'band'];
  if (r.record) return {name: `${base[0].replace(/ records$/, '')}: ${r.record}`, tier: base[1], sub: true};
  return {name: base[0] + (r.n_records ? ` (${r.n_records})` : ''), tier: base[1], sub: false};
}
function pts(v) { return v == null ? '–' : (100 * v).toFixed(1); }

// Latest row per (record, setup).
function latest() {
  const out = new Map();
  for (const r of EXP) out.set(`${rowKey(r)}#${setupKey(r.setup)}`, r);
  return out;
}
function columns(rows) {
  const cols = new Map();
  for (const r of rows) cols.set(setupKey(r.setup), r.setup);
  const order = s => { const i = SEP_ORDER.indexOf(canon(s.separator)); return (i < 0 ? 99 : i) * 10 + (canon(s.spans_from, 'same') !== 'same') + 2 * (canon(s.note_finder, 'ours') !== 'ours'); };
  return [...cols.entries()].sort((a, b) => order(a[1]) - order(b[1])).map(([k, s]) => ({k, s}));
}
function recordRows(rows) {
  const seen = new Map();
  for (const r of rows) if (!seen.has(rowKey(r))) seen.set(rowKey(r), r);
  const tierIx = t => TIERS.findIndex(x => x[0] === t);
  const setIx = s => { const i = Object.keys(RECORDS).indexOf(s); return i < 0 ? 99 : i; };
  return [...seen.values()].sort((a, b) => {
    const A = rowInfo(a), B = rowInfo(b);
    return tierIx(A.tier) - tierIx(B.tier) || setIx(a.set) - setIx(b.set) ||
      setIx(a.record) - setIx(b.record) || (!!a.record - !!b.record) || String(a.record).localeCompare(String(b.record));
  });
}
function defaultCol(rows) {
  const d = rows.find(r => r.default);
  return d ? setupKey(d.setup) : null;
}
function lostSax(r, base) {
  if (!r || !base) return null;
  for (const m of ['sax_found', 'onset_recall']) {
    const a = r.metrics[m], b = base.metrics[m];
    if (a != null && b != null) return b - a >= FLAG_DROP ? {m, a, b} : null;
  }
  return null;
}

// ---------- 1. where each record stands ----------
function stands() {
  const box = $('#stands'); box.replaceChildren();
  const items = [];
  for (const set of CLEAN_SETS) {
    const d = DATA.runs.filter(r => r.set === set && r.default && r.metrics.note_f1 != null).pop();
    if (d) items.push({tier: 'clean', name: setName(set), m: d.metrics, mix: isMix(set), src: d.entry || d.commit || ''});
  }
  const L = latest();
  const defaults = [...L.values()].filter(r => r.default && r.metrics.note_f1 != null);
  for (const r of recordRows(defaults)) {
    const info = rowInfo(r);
    if (info.sub) continue;
    items.push({tier: info.tier, name: info.name, m: r.metrics, mix: true, key: r.key, src: r.entry || r.commit || ''});
  }
  if (!items.length) { box.append(el('p', {class: 'quiet'}, 'No scores yet.')); return; }
  const W = 1000, rowH = 30, labelW = 220, numW = 300, iw = W - labelW - numW;
  let y = 8, s = '';
  const x = v => labelW + v * iw;
  for (const [tier, title] of TIERS) {
    const rows = items.filter(i => i.tier === tier);
    if (!rows.length) continue;
    s += `<text class="tier" x="0" y="${y + 14}">${esc(title)}</text>`;
    y += 24;
    for (const it of rows) {
      const v = it.m.note_f1, tgt = DATA.targets.note_f1 ? DATA.targets.note_f1[it.mix ? 'mix' : 'solo'] : null;
      s += `<text x="0" y="${y + 18}">${esc(it.name)}</text>`;
      s += `<rect class="track" x="${x(0)}" y="${y + 7}" width="${iw}" height="14" rx="4"/>`;
      s += `<rect x="${x(0)}" y="${y + 7}" width="${Math.max(2, v * iw)}" height="14" rx="4" fill="var(--k-right)"><title>${esc(it.name)}: note F1 ${pts(v)}</title></rect>`;
      if (tgt != null) s += `<line class="target" x1="${x(tgt)}" x2="${x(tgt)}" y1="${y + 3}" y2="${y + 25}"/>`;
      const extra = [];
      if (it.m.sax_found != null) extra.push(`found ${pts(it.m.sax_found)}`);
      if (it.m.sax_purity != null) extra.push(`purity ${pts(it.m.sax_purity)}`);
      if (it.key && it.key.heard_ok != null) extra.push(`key ${Math.round(100 * it.key.heard_ok)}% heard`);
      s += `<text class="val" x="${labelW + iw + 10}" y="${y + 18}">${pts(v)}</text>`;
      s += `<text class="side" x="${labelW + iw + 52}" y="${y + 18}">${esc(extra.join(' · '))}</text>`;
      y += rowH;
    }
    y += 8;
  }
  for (const v of [0, 0.25, 0.5, 0.75, 1]) s += `<text class="tick" x="${x(v)}" y="${y + 10}" text-anchor="middle">${v * 100}</text>`;
  y += 16;
  box.innerHTML = `<svg viewBox="0 0 ${W} ${y}" width="${W}" role="img" aria-label="Note F1 by record, current default setup">${s}</svg>`;
}

// ---------- 2. setups compared ----------
function grid() {
  const table = $('#grid'); table.replaceChildren();
  const L = latest();
  const rows = recordRows([...L.values()]);
  const cols = columns([...L.values()]);
  if (!rows.length) { table.append(el('tr', {}, '')); $('#grid-empty').hidden = false; return; }
  const head = el('tr');
  head.append(el('th', {}, 'Record'));
  for (const c of cols) {
    const th = el('th', {class: 'num'}, setupName(c.s));
    if (EXP.some(r => r.default && setupKey(r.setup) === c.k)) th.append(el('div', {class: 'small quiet'}, 'today’s default'));
    head.append(th);
  }
  table.append(head);
  let tier = null;
  for (const r of rows) {
    const info = rowInfo(r);
    if (info.tier !== tier) {
      tier = info.tier;
      const tr = el('tr', {class: 'tierrow'});
      const td = el('td', {}, (TIERS.find(t => t[0] === tier) || [, tier])[1]); td.colSpan = cols.length + 1;
      tr.append(td); table.append(tr);
    }
    const all = cols.map(c => L.get(`${rowKey(r)}#${c.k}`));
    const dk = defaultCol(all.filter(Boolean));
    const base = dk ? L.get(`${rowKey(r)}#${dk}`) : null;
    const tr = el('tr');
    const name = el('td', {class: info.sub ? 'sub' : ''}, info.name);
    const kr = all.find(x => x && x.key);
    if (kr) {
      const draft = /draft|mix/.test(kr.key.version || '');
      name.append(el('div', {class: 'small quiet'},
        `${kr.n_key ? kr.n_key + ' key notes · ' : ''}${kr.key.heard_ok != null ? `key ${Math.round(100 * kr.key.heard_ok)}% heard` : ''}${draft ? ' · draft timing' : ''}`));
    }
    tr.append(name);
    cols.forEach((c, i) => {
      const x = all[i];
      const td = el('td', {class: 'num cell'});
      const v = x ? x.metrics[cmp.metric] : null;
      if (v == null) { td.textContent = '–'; td.classList.add('empty'); tr.append(td); return; }
      td.append(el('span', {class: 'v'}, pts(v)));
      const bv = base ? base.metrics[cmp.metric] : null;
      if (bv != null && x !== base) {
        const d = 100 * (v - bv);
        const w = Math.min(1, Math.abs(d) / 10) * 46;
        td.style.background = `color-mix(in oklab, var(${d >= 0 ? '--div-pos' : '--div-neg'}) ${w.toFixed(0)}%, var(--card))`;
        td.append(el('span', {class: 'd'}, `${d >= 0 ? '+' : '−'}${Math.abs(d).toFixed(1)}`));
      }
      if (keyFavours(x)) {
        td.classList.add('favoured');
        td.append(el('div', {class: 'favour', title: 'This answer key was aligned partly with this model, so the score may flatter it'}, '† key may favour this model'));
      }
      const lost = x !== base ? lostSax(x, base) : null;
      if (lost) td.append(el('div', {class: 'lost', title: 'Loses real sax notes compared with the default'},
        `▼ loses sax: ${lost.m === 'sax_found' ? 'found' : 'onset recall'} ${pts(lost.b)} → ${pts(lost.a)}`));
      if (x.key_notes) td.classList.add('has-bd');
      td.tabIndex = 0;
      td.title = `${info.name}, ${setupName(c.s)}${x.entry ? ' · ' + x.entry : ''}${x.commit ? ' · ' + x.commit : ''}${x.note ? '\n' + x.note : ''}`;
      const pick = () => { cmp.setup = c.k; cmp.record = rowKey(r); breakdown(); along(); $('#where').scrollIntoView({behavior: 'smooth', block: 'start'}); };
      td.addEventListener('click', pick);
      td.addEventListener('keydown', e => { if (e.key === 'Enter') pick(); });
      tr.append(td);
    });
    table.append(tr);
  }
  // weighted summary: wins and losses per setup against the default, record rows only
  const foot = el('tr', {class: 'foot'});
  foot.append(el('td', {}, 'Better / worse than the default (records)'));
  for (const c of cols) {
    let up = 0, down = 0, lost = 0;
    for (const r of rows) {
      const x = L.get(`${rowKey(r)}#${c.k}`);
      const all = cols.map(cc => L.get(`${rowKey(r)}#${cc.k}`)).filter(Boolean);
      const dk = defaultCol(all); const base = dk ? L.get(`${rowKey(r)}#${dk}`) : null;
      if (!x || !base || x === base) continue;
      const v = x.metrics[cmp.metric], bv = base.metrics[cmp.metric];
      if (v != null && bv != null) { if (v - bv > 0.005) up++; else if (bv - v > 0.005) down++; }
      if (lostSax(x, base)) lost++;
    }
    foot.append(el('td', {class: 'num'}, c.k === defaultCol(EXP) ? '' : `${up} ▲ · ${down} ▼${lost ? ` · ${lost} lose sax` : ''}`));
  }
  table.append(foot);
}

// ---------- 3. where the notes go ----------
function breakdown() {
  const box = $('#where-bars'); box.replaceChildren();
  const withBd = EXP.filter(r => r.key_notes);
  const setups = columns(withBd);
  const seg = $('#where-setup'); seg.replaceChildren();
  if (!withBd.length) { box.append(el('p', {class: 'quiet'}, 'No error counts yet. Experiment rows written with experiments.classify() show here.')); return; }
  if (!setups.some(c => c.k === cmp.setup)) cmp.setup = (setups.find(c => c.s.separator === 'demucs') || setups[0]).k;
  for (const c of setups) {
    const b = el('button', {type: 'button', 'data-v': c.k, class: c.k === cmp.setup ? 'on' : ''}, setupName(c.s));
    seg.append(b);
  }
  const lg = $('#where-legend'); lg.replaceChildren();
  for (const k of KINDS) {
    const item = el('span', {class: 'key'});
    const sw = el('span', {class: 'sw'}); sw.style.background = k.c;
    item.append(sw, document.createTextNode(k.key === k.ours ? k.key : `${k.key} / ${k.ours}`));
    lg.append(item);
  }
  const L = new Map();
  for (const r of withBd) if (setupKey(r.setup) === cmp.setup) L.set(rowKey(r), r);
  const rows = recordRows([...L.values()]);
  const W = 1000, labelW = 230, iw = W - labelW - 8, barH = 12;
  let y = 4, s = '';
  for (const r of rows) {
    const info = rowInfo(r);
    s += `<text class="rec${rowKey(r) === cmp.record ? ' sel' : ''}" x="0" y="${y + 12}">${esc(info.name)}</text>`;
    for (const side of ['key', 'ours']) {
      const counts = side === 'key' ? r.key_notes : r.our_notes;
      const total = KINDS.reduce((a, k) => a + (counts[side === 'key' ? k.k : (k.ours_k || k.k)] || 0), 0);
      const label = side === 'key' ? `Key’s ${total} notes` : `Our ${total} notes`;
      s += `<text class="side-l" x="0" y="${y + (side === 'key' ? 32 : 50)}">${label}</text>`;
      let x0 = labelW;
      const yy = y + (side === 'key' ? 22 : 40);
      for (const k of KINDS) {
        const n = counts[side === 'key' ? k.k : (k.ours_k || k.k)] || 0;
        if (!n || !total) continue;
        const w = n / total * iw;
        const name = side === 'key' ? k.key : k.ours;
        s += `<rect class="seg" x="${x0}" y="${yy}" width="${Math.max(1, w - 2)}" height="${barH}" rx="2" fill="${k.c}" data-tip="${esc(`${info.name} · ${side === 'key' ? 'answer key' : 'our sheet'}|${name}: ${n} of ${total} (${(100 * n / total).toFixed(1)}%)`)}"/>`;
        if (w > 44) s += `<text class="in" x="${x0 + 5}" y="${yy + 10}">${Math.round(100 * n / total)}%</text>`;
        x0 += w;
      }
    }
    y += 64;
  }
  box.innerHTML = `<svg viewBox="0 0 ${W} ${y}" width="${W}" role="img" aria-label="Where the notes go, per record">${s}</svg>`;
  segTips(box.querySelector('svg'));
  // table view of the same counts
  const t = $('#where-table'); t.replaceChildren();
  const head = el('tr'); head.append(el('th', {}, 'Record'));
  for (const k of KINDS) head.append(el('th', {class: 'num'}, `${k.key} / ${k.ours}`));
  head.append(el('th', {class: 'num'}, 'Hidden notes not in the key'));
  t.append(head);
  for (const r of rows) {
    const tr = el('tr'); tr.append(el('td', {}, rowInfo(r).name));
    for (const k of KINDS) tr.append(el('td', {class: 'num'}, `${r.key_notes[k.k] ?? 0} / ${r.our_notes[k.ours_k || k.k] ?? 0}`));
    tr.append(el('td', {class: 'num'}, r.hidden_notes ? r.hidden_notes.not_in_key : '–'));
    t.append(tr);
  }
}

function segTips(svg) {
  const tip = $('#tip');
  svg.addEventListener('pointermove', ev => {
    const m = ev.target.closest('[data-tip]');
    if (!m) { tip.hidden = true; return; }
    const [a, b] = m.dataset.tip.split('|');
    tip.replaceChildren(el('div', {class: 'when'}, a), el('div', {}, b));
    tip.hidden = false;
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    let left = ev.clientX + 14; if (left + tw > innerWidth - 8) left = ev.clientX - tw - 14;
    let top = ev.clientY - th - 12; if (top < 8) top = ev.clientY + 16;
    tip.style.left = `${Math.max(8, left)}px`; tip.style.top = `${top}px`;
  });
  svg.addEventListener('pointerleave', () => { tip.hidden = true; });
}

// ---------- 4. along the record ----------
function along() {
  const box = $('#along'); box.replaceChildren();
  const seg = $('#along-record'); seg.replaceChildren();
  const withBars = EXP.filter(r => r.bars && r.bars.length);
  if (!withBars.length) { box.append(el('p', {class: 'quiet'}, 'No bar-by-bar counts yet.')); return; }
  const recs = recordRows(withBars);
  if (!recs.some(r => rowKey(r) === cmp.record)) cmp.record = rowKey(recs[0]);
  for (const r of recs) seg.append(el('button', {type: 'button', 'data-v': rowKey(r), class: rowKey(r) === cmp.record ? 'on' : ''}, rowInfo(r).name));
  const L = new Map();
  for (const r of withBars) if (rowKey(r) === cmp.record) L.set(setupKey(r.setup), r);
  const cols = columns([...L.values()]);
  const labelW = 200, cell = 6, gap = 1;
  const nb = Math.max(...[...L.values()].map(r => r.bars.length));
  const W = labelW + nb * (cell + gap) + 8;
  let y = 4, s = '';
  for (const c of cols) {
    const r = L.get(c.k);
    s += `<text class="rec" x="0" y="${y + 12}">${esc(setupName(c.s))}</text>`;
    const lanes = [['Found', 27], ['Hidden', 46], ['Extra', 62]];
    for (const [nm, dy] of lanes) s += `<text class="side-l" x="${labelW - 8}" y="${y + dy}" text-anchor="end">${nm}</text>`;
    r.bars.forEach((b, i) => {
      const x = labelW + i * (cell + gap);
      const tipTxt = esc(`Bar ${b.bar} · ${fmtSec(b.t0)}|${b.key ? `${b.right} of ${b.key} key notes found` : 'Rest in the key'}${b.hidden ? `, ${b.hidden} hidden` : ''}${b.extra ? `; ${b.extra} extra notes of ours` : ''}${b.cut ? `; ${Math.round(100 * b.cut)}% inside a sax-rest cut` : ''}`);
      // found share: one-hue ramp; rest bars stay surface-grey
      const f = b.key ? b.right / b.key : null;
      s += `<rect x="${x}" y="${y + 16}" width="${cell}" height="14" rx="1" fill="${f == null ? 'var(--grid)' : rampBlue(f)}" data-tip="${tipTxt}"/>`;
      if (b.hidden || b.cut > 0.5) s += `<rect x="${x}" y="${y + 38}" width="${cell}" height="8" rx="1" fill="var(--k-rest)" data-tip="${tipTxt}"/>`;
      if (b.extra) s += `<rect x="${x}" y="${y + 54 + Math.max(0, 8 - Math.min(8, b.extra * 2))}" width="${cell}" height="${Math.min(8, b.extra * 2)}" rx="1" fill="var(--k-miss)" data-tip="${tipTxt}"/>`;
      if (b.bar % 16 === 1 || i === 0) s += `<text class="tick" x="${x}" y="${y + 76}">${b.bar}</text>`;
    });
    y += 88;
  }
  box.innerHTML = `<svg viewBox="0 0 ${W} ${y}" width="${W}" role="img" aria-label="Notes found bar by bar">${s}</svg>`;
  segTips(box.querySelector('svg'));
}
function fmtSec(t) { const m = Math.floor(t / 60); return `${m}:${String(Math.floor(t % 60)).padStart(2, '0')}`; }
const RAMP = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b'];
function rampBlue(f) { return RAMP[Math.min(RAMP.length - 1, Math.floor(f * RAMP.length))]; }

// ---------- every experiment row ----------
function expTable() {
  const table = $('#exp-rows'); table.replaceChildren();
  const head = el('tr');
  for (const h of ['When', 'Record', 'Setup', 'Scope', 'Note F1', 'No offsets', 'Onset F1', 'Onset recall', 'Pitch', 'Sax found', 'Sax purity', 'Source'])
    head.append(el('th', {}, h));
  table.append(head);
  for (const r of EXP.slice().reverse()) {
    const m = r.metrics, tr = el('tr');
    tr.append(el('td', {class: 'num'}, r.when ? fmtWhen(Date.parse(r.when)) : ''));
    tr.append(el('td', {}, rowInfo(r).name));
    tr.append(el('td', {}, setupName(r.setup) + (r.default ? ' (default)' : '')));
    tr.append(el('td', {}, r.scope || ''));
    for (const k of ['note_f1', 'note_f1_no_offset', 'onset_f1', 'onset_recall', 'pitch_accuracy', 'sax_found', 'sax_purity'])
      tr.append(el('td', {class: 'num'}, pts(m[k])));
    tr.append(el('td', {}, [r.entry && `log ${r.entry}`, r.commit].filter(Boolean).join(' · ')));
    table.append(tr);
  }
}

function renderCompare() {
  EXP = DATA.experiments || [];
  stands(); grid(); breakdown(); along(); expTable();
}
segment($('#grid-metric'), v => { cmp.metric = v; grid(); });
segment($('#where-setup'), v => { cmp.setup = v; breakdown(); });
segment($('#along-record'), v => { cmp.record = v; along(); });
