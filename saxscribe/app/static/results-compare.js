// Results page, comparison views: setups compared side by side, two setups head to head, separators alone,
// where the notes go (error breakdown) and along the record (bar by bar).
// Data: DATA.experiments (score/experiments.py), DATA.runs (score/history.py). Plain SVG and tables.

const SEPARATORS = {
  'demucs': 'Demucs', 'demucs-6s': 'Demucs',
  'mega': 'MVSep Mega 53-stem', 'mega-local': 'MVSep Mega 53-stem',
  'rd-filosax-demucs': 'Filosax sax separator',
  'hybrid': 'Mega + Demucs fallback',
  'mvsep-web': 'MVSep website sax',
  'rd-sax': 'Filosax sax separator',
  'filosax': 'Filosax sax separator',
  'mvsep-mega53-sax-on-mix': 'MVSep Mega 53-stem',
  'demucs-lead->mega53-sax': 'Demucs lead, then Mega sax',
  'demucs-lead->mega53-wind->mega53-sax': 'Demucs lead, then Mega wind, then Mega sax',
  'demucs-6s-lead': 'Demucs 6-stem lead',
  'oracle a|b': 'Best of Filosax or Mega, per note (ceiling)',
  'oracle all': 'Best of all stems, per note (ceiling)',
  'audio-only 2s chooser': 'Pick a stem every 2 s by sound',
};
const SEP_ORDER = ['demucs', 'demucs-6s', 'mega', 'mega-local', 'hybrid', 'mvsep-web', 'rd-sax', 'rd-filosax-demucs',
                   'demucs-lead->mega53-sax', 'demucs-lead->mega53-wind->mega53-sax'];
// 'ours' = the standard path (Basic Pitch + CREPE). 'rd-filosax-ft' = our fine-tune of R&D's model (E77),
// shown in the app as "Our sax model".
const FINDERS = {'ours': '', 'rd-filosax': 'R&D note model', 'rd-filosax_25k': 'R&D note model',
                 'rd-filosax-ft': 'our sax model (E77 fine-tune)', 'basic_pitch-plain': 'plain Basic Pitch',
                 'e83a-ft1500': 'E83a fine-tune (not adopted)', 'e83b-ft0': 'E83b fine-tune (kept E77 weights)'};
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
  'tenor-tunes': ['Four tenor tunes', 'pop'],  // the Mac's name for the same set
  'wjd': ['Weimar database solos (written rhythm only)', 'band'],
  'austin-6': ["Austin's six tunes", 'band'],
  'parker-test': ['Parker test records', 'band'],
  'parker-train': ['Parker records used for tuning', 'band'],
  'weimar-test': ['Weimar solos (test)', 'band'],
  'weimar-train': ['Weimar solos used for tuning', 'band'],
  'heldout-players': ['Coltrane, Getz, Potter (picked the E77 checkpoint)', 'band'],
  'benchmark': ['Benchmark songs', 'band'],
};
// Answer keys partly built with a model under test: its scores there are not a clean win.
// The Omnibook's alignment used a Riley & Dixon transcription model (their paper, section 3.1).
// A row can also carry key.favours: [note_finder, ...] itself.
const RD = ['rd-filosax', 'rd-filosax_25k', 'rd-filosax-ft'];
const KEY_FAVOURS = {'parker-band': RD, 'omnibook': RD, 'parker-test': RD, 'parker-train': RD};
function keyFavours(r) {
  const f = (r.key && r.key.favours) || KEY_FAVOURS[r.set] || [];
  return f.includes(r.setup.note_finder) || f.includes(canon(r.setup.note_finder)) || f.includes(r.setup.separator);
}
const TIERS = [['clean', 'Clean sax (recorded alone or pre-separated)'], ['band', 'Jazz band records'],
               ['pop', 'Pop and fusion records']];
const CLEAN_SETS = ['bach10', 'choralebricks', 'grfia-alto', 'grfia-tenor', 'urmp', 'omnibook'];
const GRID_METRICS = [
  ['note_f1', 'Note F1'], ['sax_found', 'Sax found'], ['sax_purity', 'Sax purity'],
  ['onset_recall', 'Onset recall'], ['pitch_accuracy', 'Pitch'], ['sax_found_heard', 'Found, heard key notes'],
  ['short_found', 'Short notes found'], ['bars_right', 'Bars right'], ['notes_in_place', 'Notes in the right spot'],
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
const ALIAS = {'demucs-6s': 'demucs', 'mega-local': 'mega', 'rd-filosax-demucs': 'rd-sax', 'filosax': 'rd-sax',
               'mvsep-mega53-sax-on-mix': 'mega', 'own': 'same', 'rd-filosax_25k': 'rd-filosax',
               'basic_pitch': 'ours', 'basic-pitch': 'ours'};
// Fine-tuned checkpoints are named after their base plus "-ft<step>" (E77: rd-filosax_25k-ft2488).
function canon(v, d) {
  if (v && /^rd-filosax(_25k)?-ft/.test(v)) return 'rd-filosax-ft';
  return ALIAS[v] || v || d;
}
function setupKey(s) { return `${canon(s.separator)}|${canon(s.spans_from, 'same')}|${canon(s.note_finder, 'ours')}|${s.variant || ''}`; }
function setupName(s) {
  let n = SEPARATORS[s.separator] || SEPARATORS[canon(s.separator)] || s.separator;
  if (s.spans_from === 'none') n += ', no sax-rest cuts';
  else if (s.spans_from && !['same', 'own'].includes(s.spans_from)) n += `, rests from ${SEPARATORS[s.spans_from] || s.spans_from}`;
  const f = canon(s.note_finder, 'ours');
  if (f === 'ours') n += ', Basic Pitch';
  else if (FINDERS[f]) n += `, ${FINDERS[f]}`;
  else if (f !== 'ours') n += `, ${s.note_finder}`;
  if (s.variant) n += ` (${VERSIONS[s.variant] || s.variant})`;  // e.g. an open PR's code on the same setup
  return n;
}
// E81 re-scored the benchmark at the commits where the default changed; name those by their pull request.
const VERSIONS = {b3aa715: 'version of PR #9', e01aeef: 'version of PR #35', '50b729a': 'version of PR #57',
                  '80cba98': 'version of PR #81'};
function rowKey(r) { return r.record ? `${r.set}/${r.record}` : r.set; }
// Song facts from docs/evaluation/benchmark_tags.json (player, title, year, album, horn, style, era).
function songTag(r) {
  const t = DATA.tags || {};
  return t[r._record || r.record] || t[r.record] || (!r.record ? t[r.set] : null) || null;
}
function rowInfo(r) {
  const tg = (r._set || r.set) === 'benchmark' ? songTag(r) : null;
  if (tg) return {name: tg.title || r.record, tier: tg.style === 'funk, pop, smooth' ? 'pop' : 'band', sub: false};
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
  const order = s => { const i = SEP_ORDER.indexOf(canon(s.separator)); return (i < 0 ? 99 : i) * 10 + (canon(s.spans_from, 'same') !== 'same') + 2 * (canon(s.note_finder, 'ours') !== 'ours') + 4 * !!s.variant; };
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

// ---------- 2. setups compared ----------
function grid() {
  const table = $('#grid'); table.replaceChildren();
  const L = latest();
  // Only the records and setups that measured this score (rhythm rows carry no note F1, and the reverse).
  // Settings tweaks and PR before/after runs stay hidden unless asked for, or unless they are all
  // this score has (the bar-line rows are all before/after pairs).
  const measured = [...L.values()].filter(r => r.metrics[cmp.metric] != null);
  const plain = measured.filter(r => !r.setup.variant || r.default);
  const has = cmp.tweaks || !plain.length ? measured : plain;
  const allCols = columns(has);
  fillOlder($('#grid-older'), allCols, has, cmp.gridOlder, 'Add an older setup…');
  const cols = shown(allCols, cmp.gridOlder);
  // Rows: the records today's default has scored, plus those of an older setup picked from the dropdown.
  // Records only older setups have scored stay out unless one of those setups is picked.
  const anchor = new Set([cols.some(c => c.k === TODAY_BAND) ? TODAY_BAND : (cols[0] || {}).k, cmp.gridOlder]);
  let rows = recordRows(has.filter(r => anchor.has(setupKey(r.setup))));
  const hiddenRecs = recordRows(has).length - rows.length;
  // The three Parker test records are also benchmark songs: show each song once, as the benchmark row.
  const benchRecs = new Set(rows.filter(r => (r._set || r.set) === 'benchmark').map(r => r._record || r.record));
  rows = rows.filter(r => !(r.set === 'parker-test' && r.record && benchRecs.has(r.record)));
  // Group by collection (the tiers) or by a song tag; "Show" narrows to one group.
  const by = cmp.gridGroup || 'collection';
  const groupOf = r => {
    if (by === 'collection') return (TIERS.find(t => t[0] === rowInfo(r).tier) || [, rowInfo(r).tier])[1];
    const tg = songTag(r); const v = tg && tg[by];
    return v == null || v === '' ? (tg && by === 'player' ? 'Player unknown' : 'Not tagged') : String(v);
  };
  const values = [...new Set(rows.map(groupOf))];
  if (by !== 'collection') values.sort((a, b) => (a === 'Not tagged') - (b === 'Not tagged') || rows.filter(r => groupOf(r) === b).length - rows.filter(r => groupOf(r) === a).length || a.localeCompare(b));
  const only = $('#grid-only');
  if (!values.includes(cmp.gridOnly)) cmp.gridOnly = '';
  only.replaceChildren(el('option', {value: ''}, `All (${values.length} groups)`));
  for (const v of values) { const o = el('option', {value: v}, `${v} (${rows.filter(r => groupOf(r) === v).length})`); if (v === cmp.gridOnly) o.selected = true; only.append(o); }
  if (cmp.gridOnly) rows = rows.filter(r => groupOf(r) === cmp.gridOnly);
  if (by !== 'collection') rows = rows.filter(r => songTag(r) || r.record);   // set averages are not songs
  rows = values.flatMap(v => rows.filter(r => groupOf(r) === v));
  const tagged = rows.some(r => songTag(r));
  $('#grid-hidden').textContent = hiddenRecs > 0 ? `${hiddenRecs} records scored only with older setups are left out; pick one of those setups above to see them.` : '';
  $('#grid-empty').hidden = !!rows.length;
  if (!rows.length) return;
  const head = el('tr');
  head.append(el('th', {}, 'Song or record'));
  if (tagged) for (const h of ['Player', 'Year', 'Album']) head.append(el('th', {}, h));
  const extra = tagged ? 3 : 0;
  for (const c of cols) {
    const th = el('th', {class: 'num'}, setupName(c.s));
    const isToday = cols.some(x => x.k === TODAY_BAND) ? c.k === TODAY_BAND : EXP.some(r => r.default && setupKey(r.setup) === c.k);
    const role = isToday ? 'today’s default' : roleOf(c.k);
    if (role) th.append(el('div', {class: 'small quiet'}, role));
    head.append(th);
  }
  table.append(head);
  let tier = null;
  for (const r of rows) {
    const info = rowInfo(r);
    if (groupOf(r) !== tier) {
      tier = groupOf(r);
      const tr = el('tr', {class: 'tierrow'});
      const td = el('td', {}, tier); td.colSpan = cols.length + 1 + extra;
      tr.append(td); table.append(tr);
      if (by !== 'collection') table.append(groupAverage(rows.filter(x => groupOf(x) === tier), cols, L, extra));
    }
    const all = cols.map(c => L.get(`${rowKey(r)}#${c.k}`)).map(x => x && x.metrics[cmp.metric] != null ? x : null);
    const dk = defaultCol(all.filter(Boolean));
    const base = dk ? L.get(`${rowKey(r)}#${dk}`) : null;
    const tr = el('tr');
    const name = el('td', {class: info.sub ? 'sub' : ''}, info.name);
    const kr = all.find(x => x && x.key);
    if (kr) {
      const draft = /draft|mix/.test(kr.key.version || '');
      name.append(el('div', {class: 'small quiet'},
        [kr.n_key && `${kr.n_key} key notes`, kr.key.heard_ok != null && `key ${Math.round(100 * kr.key.heard_ok)}% heard`, draft && 'draft timing'].filter(Boolean).join(' · ')));
    }
    tr.append(name);
    if (tagged) { const tg = songTag(r) || {}; for (const k of ['player', 'year', 'album']) tr.append(el('td', {class: k === 'year' ? 'num' : 'small'}, tg[k] == null ? '–' : String(tg[k]))); }
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
      const pick = () => {
        cmp.setup = c.k; cmp.record = rowKey(r); breakdown();
        if (typeof showTab === 'function') showTab('songs', false);
        $('#where').scrollIntoView({block: 'start'});
      };
      td.addEventListener('click', pick);
      td.addEventListener('keydown', e => { if (e.key === 'Enter') pick(); });
      tr.append(td);
    });
    table.append(tr);
  }
  // weighted summary: wins and losses per setup against the default, record rows only
  const foot = el('tr', {class: 'foot'});
  foot.append(el('td', {}, 'Better / worse than the default (records)'));
  for (let i = 0; i < extra; i++) foot.append(el('td'));
  for (const c of cols) {
    let up = 0, down = 0, lost = 0;
    for (const r of rows) {
      const x = L.get(`${rowKey(r)}#${c.k}`);
      const all = cols.map(cc => L.get(`${rowKey(r)}#${cc.k}`)).filter(y => y && y.metrics[cmp.metric] != null);
      const dk = defaultCol(all); const base = dk ? L.get(`${rowKey(r)}#${dk}`) : null;
      if (!x || !base || x === base) continue;
      const v = x.metrics[cmp.metric], bv = base.metrics[cmp.metric];
      if (v != null && bv != null) { if (v - bv > 0.005) up++; else if (bv - v > 0.005) down++; }
      if (lostSax(x, base)) lost++;
    }
    foot.append(el('td', {class: 'num'}, c.k === defaultCol(has) ? '' : `${up} ▲ · ${down} ▼${lost ? ` · ${lost} lose sax` : ''}`));
  }
  table.append(foot);
}

// One row with each setup's average over a group's songs (only songs it scored), and how many it scored.
function groupAverage(rows, cols, L, extra) {
  const tr = el('tr', {class: 'avg'});
  tr.append(el('td', {class: 'sub'}, `Average of ${rows.length} song${rows.length > 1 ? 's' : ''}`));
  for (let i = 0; i < extra; i++) tr.append(el('td'));
  for (const c of cols) {
    const vs = rows.map(r => L.get(`${rowKey(r)}#${c.k}`)).filter(x => x && x.metrics[cmp.metric] != null).map(x => x.metrics[cmp.metric]);
    tr.append(el('td', {class: 'num'}, vs.length ? `${pts(vs.reduce((a, b) => a + b, 0) / vs.length)}${vs.length < rows.length ? ` (${vs.length})` : ''}` : '–'));
  }
  return tr;
}

// ---------- 2b. two setups head to head ----------
// Any two setups, on the records both have scored: one row per record, the difference, and the totals.
function pair() {
  const L = latest();
  const measured = [...L.values()].filter(r => r.metrics[cmp.metric] != null);
  const cols = columns(measured);
  const byNew = orderedSetups(cols, measured);
  if (!cols.some(c => c.k === cmp.pairA)) cmp.pairA = (cols.find(c => c.k === TODAY_BAND) || byNew[0] || {}).k;
  if (!cols.some(c => c.k === cmp.pairB) || cmp.pairB === cmp.pairA)
    cmp.pairB = (cols.find(c => c.k === PREV_BAND && c.k !== cmp.pairA) || byNew.find(c => c.k !== cmp.pairA) || {}).k;
  for (const [id, cur] of [['#pair-a', cmp.pairA], ['#pair-b', cmp.pairB]]) {
    const sel = $(id); sel.replaceChildren();
    for (const c of byNew) {
      const role = roleOf(c.k);
      const o = el('option', {value: c.k}, `${setupName(c.s)}${role ? ' (' + role + ')' : ''}`);
      if (c.k === cur) o.selected = true;
      sel.append(o);
    }
  }
  const table = $('#pair'); table.replaceChildren();
  const sum = $('#pair-sum');
  const name = k => { const c = cols.find(x => x.k === k); return c ? setupName(c.s) : '–'; };
  const both = recordRows(measured.filter(r => setupKey(r.setup) === cmp.pairA))
    .map(r => [r, L.get(`${rowKey(r)}#${cmp.pairA}`), L.get(`${rowKey(r)}#${cmp.pairB}`)])
    .filter(([, a, b]) => a && b && b.metrics[cmp.metric] != null);
  if (!both.length) { sum.textContent = 'These two setups have no record in common for this score. Pick another pair or score.'; return; }
  const head = el('tr');
  for (const h of ['Record', 'A', 'B', 'B − A']) head.append(el('th', {class: h === 'Record' ? '' : 'num'}, h));
  table.append(head);
  let up = 0, down = 0, sa = 0, sb = 0;
  for (const [r, a, b] of both) {
    const va = a.metrics[cmp.metric], vb = b.metrics[cmp.metric], d = 100 * (vb - va);
    sa += va; sb += vb; if (d > 0.5) up++; else if (d < -0.5) down++;
    const tr = el('tr');
    tr.append(el('td', {class: rowInfo(r).sub ? 'sub' : ''}, rowInfo(r).name), el('td', {class: 'num'}, pts(va)), el('td', {class: 'num'}, pts(vb)));
    const td = el('td', {class: 'num'}, `${d >= 0 ? '+' : '−'}${Math.abs(d).toFixed(1)}`);
    td.style.background = `color-mix(in oklab, var(${d >= 0 ? '--div-pos' : '--div-neg'}) ${(Math.min(1, Math.abs(d) / 10) * 46).toFixed(0)}%, var(--card))`;
    tr.append(td); table.append(tr);
  }
  const n = both.length;
  sum.textContent = `On the ${n} record${n > 1 ? 's' : ''} both have scored: A averages ${pts(sa / n)}, B ${pts(sb / n)} ` +
    `(${sb >= sa ? '+' : '−'}${Math.abs(100 * (sb - sa) / n).toFixed(1)}). B is better on ${up}, worse on ${down}, ` +
    `within half a point on ${n - up - down}. A: ${name(cmp.pairA)}. B: ${name(cmp.pairB)}.`;
}
// Featured setups first, then the rest newest run first.
function orderedSetups(cols, rows) {
  const last = new Map();
  for (const r of rows) { const k = setupKey(r.setup); if ((r.when || '') > (last.get(k) || '')) last.set(k, r.when || ''); }
  const f = featured(cols), fk = new Set(f.map(c => c.k));
  return f.concat(cols.filter(c => !fk.has(c.k)).sort((a, b) => (last.get(b.k) || '').localeCompare(last.get(a.k) || '')));
}

// ---------- 3. where the notes go ----------
function breakdown() {
  const box = $('#where-bars'); box.replaceChildren();
  const withBd = EXP.filter(r => r.key_notes);
  const all = columns(withBd);
  const seg = $('#where-setup'); seg.replaceChildren();
  if (!withBd.length) { box.append(el('p', {class: 'quiet'}, 'No error counts yet. Experiment rows written with experiments.classify() show here.')); return; }
  // Opens on today's default; the default before and the challenger are one tap away, every other setup
  // ever tried sits in the dropdown, newest first.
  if (!all.some(c => c.k === cmp.setup)) cmp.setup = (all.find(c => c.k === TODAY_BAND) || all[0]).k;
  const main = featured(all);
  const older = main.some(c => c.k === cmp.setup) ? null : cmp.setup;
  for (const c of main) {
    const b = el('button', {type: 'button', 'data-v': c.k, class: c.k === cmp.setup ? 'on' : ''}, buttonName(c));
    seg.append(b);
  }
  fillOlder($('#where-older'), all, withBd, older, 'Older setups…');
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
// Drawn inside a song's history (Songs tab) for the song in cmp.record; false when it has no bar counts.
function along() {
  const box = $('#along'); box.replaceChildren();
  const L = new Map();
  for (const r of EXP) if (r.bars && r.bars.length && rowKey(r) === cmp.record) L.set(setupKey(r.setup), r);
  if (!L.size) return false;
  const cols = columns([...L.values()]);
  const labelW = 200, cell = 6, gap = 1;
  const nb = Math.max(...[...L.values()].map(r => r.bars.length));
  const W = Math.max(560, labelW + nb * (cell + gap) + 8);   // room for the setup name on short songs
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
  return true;
}
function fmtSec(t) { const m = Math.floor(t / 60); return `${m}:${String(Math.floor(t % 60)).padStart(2, '0')}`; }
const RAMP = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b'];
function rampBlue(f) { return RAMP[Math.min(RAMP.length - 1, Math.floor(f * RAMP.length))]; }

// ---------- every experiment row ----------
function expTable() {
  const table = $('#exp-rows'); table.replaceChildren();
  const head = el('tr');
  for (const h of ['When', 'Record', 'Setup', 'Scope', 'Note F1', 'No offsets', 'Onset F1', 'Onset recall', 'Pitch', 'Sax found', 'Sax purity', 'Short found', 'Bars right', 'Notes in spot', 'Source'])
    head.append(el('th', {}, h));
  table.append(head);
  for (const r of EXP.slice().reverse()) {
    const m = r.metrics, tr = el('tr');
    tr.append(el('td', {class: 'num'}, r.when ? fmtWhen(Date.parse(r.when)) : ''));
    tr.append(el('td', {}, rowInfo(r).name));
    tr.append(el('td', {}, setupName(r.setup) + (r.default ? ' (default)' : '')));
    tr.append(el('td', {}, r.scope || ''));
    for (const k of ['note_f1', 'note_f1_no_offset', 'onset_f1', 'onset_recall', 'pitch_accuracy', 'sax_found', 'sax_purity',
                     'short_found', 'bars_right', 'notes_in_place'])
      tr.append(el('td', {class: 'num'}, pts(m[k])));
    tr.append(el('td', {}, [r.entry && `log ${r.entry}`, r.commit].filter(Boolean).join(' · ')));
    table.append(tr);
  }
}

// ---------- 5. separators on their own, and the sax judge ----------
// E73-style rows: how many key notes each separator's stem still holds (no note finder involved).
const STEM_SETS = ['parker-train', 'parker-test', 'pfh', 'walkers-theme', 'weimar'];
const CEILING = ['oracle a|b', 'oracle all'];
function stemGrid() {
  const table = $('#stem-grid'); table.replaceChildren();
  const m = cmp.stemMetric || 'stem_recall';
  const rows = EXP.filter(r => r.metrics.stem_recall != null);
  $('#stem-empty').hidden = !!rows.length;
  if (!rows.length) return;
  const sets = STEM_SETS.filter(s => rows.some(r => r.set === s && r.metrics[m] != null))
    .concat([...new Set(rows.map(r => r.set))].filter(s => !STEM_SETS.includes(s) && rows.some(r => r.set === s && r.metrics[m] != null)));
  const seps = [...new Set(rows.map(r => r.setup.separator))]
    .sort((a, b) => CEILING.includes(a) - CEILING.includes(b));
  const head = el('tr'); head.append(el('th', {}, 'Separator'));
  for (const s of sets) head.append(el('th', {class: 'num'}, (RECORDS[s] || [s])[0]));
  table.append(head);
  const val = (sep, set) => { const r = rows.filter(x => x.setup.separator === sep && x.set === set).pop(); return r ? r.metrics[m] : null; };
  const best = {};
  for (const s of sets) best[s] = Math.max(...seps.filter(x => !CEILING.includes(x)).map(x => val(x, s) ?? -1));
  for (const sep of seps) {
    const tr = el('tr', {class: CEILING.includes(sep) ? 'quiet' : ''});
    tr.append(el('td', {}, SEPARATORS[sep] || sep));
    for (const s of sets) {
      const v = val(sep, s);
      const td = el('td', {class: 'num'}, pts(v));
      if (v != null && !CEILING.includes(sep) && v === best[s]) td.style.fontWeight = '700';
      tr.append(td);
    }
    table.append(tr);
  }
}
// E82 vocal review mark: the pre-registered setting's rows (marks only, no scores).
function vocalGrid() {
  const table = $('#vocal-grid'); table.replaceChildren();
  const rows = EXP.filter(r => r.entry === 'E82' && r.marks && /PRE-REGISTERED MAIN/.test(r.note || ''));
  $('#vocal-empty').hidden = !!rows.length;
  if (!rows.length) return;
  const keyed = rows.filter(r => r.marks.good != null), flagged = rows.filter(r => r.marks.flagged_notes != null);
  const sum = (rs, k) => rs.reduce((a, r) => a + (r.marks[k] || 0), 0);
  const head = el('tr');
  for (const h of ['Test', 'Records', 'Good marks', 'Bad marks', 'Notes checked']) head.append(el('th', {class: h === 'Test' ? '' : 'num'}, h));
  table.append(head);
  const NAMES = {'e82c-austin': 'Your six tunes', 'e82c-pick': 'Five benchmark songs with the most vocals'};
  for (const set of [...new Set(keyed.map(r => r._set || r.set))]) {
    const rs = keyed.filter(r => (r._set || r.set) === set), tr = el('tr');
    tr.append(el('td', {}, NAMES[set] || set), el('td', {class: 'num'}, String(rs.length)), el('td', {class: 'num'}, String(sum(rs, 'good'))),
      el('td', {class: 'num'}, String(sum(rs, 'bad'))), el('td', {class: 'num'}, sum(rs, 'matched').toLocaleString()));
    table.append(tr);
  }
  if (flagged.length) {
    const tr = el('tr', {class: 'tierrow'}); const td = el('td', {}, 'Your flagged takes: marked inside / outside your not-sax flags'); td.colSpan = 5; tr.append(td); table.append(tr);
    for (const r of flagged) {
      const m = r.marks, name = String(r.record).replace(/^\d{8}-\d{6}-/, '').replace(/-/g, ' ').replace(/ feat .*/, '');
      const f = m.flagged_notes ? `${m.flagged_marked} of ${m.flagged_notes} (${Math.round(100 * m.flagged_marked / m.flagged_notes)}%)` : '–';
      const u = m.unflagged_notes ? `${m.unflagged_marked} of ${m.unflagged_notes} (${Math.round(100 * m.unflagged_marked / m.unflagged_notes)}%)` : '–';
      const row = el('tr'); const c = el('td', {}, name.charAt(0).toUpperCase() + name.slice(1)); c.colSpan = 2;
      const a = el('td', {class: 'num'}, f); a.colSpan = 2;
      row.append(c, a, el('td', {class: 'num'}, u)); table.append(row);
    }
  }
}
const JUDGE_ROWS = [
  ['sax present vs not', [['test_all_auc', 'All test windows (AUC)'], ['Austins_tunes_auc', 'Your six tunes (AUC)'],
    ['bloody-well-right_auc', 'Bloody Well Right (AUC)'], ['test_all_bal_acc', 'All test windows (balanced accuracy)']]],
  ['sax type', [['recordings_right', 'Recordings called right'], ['alto_acc', 'Alto windows right'],
    ['tenor_acc', 'Tenor windows right'], ['soprano_acc', 'Soprano windows right']]],
];
function judgeGrid() {
  const table = $('#judge-grid'); table.replaceChildren();
  const rows = EXP.filter(r => r.scope === '2s-windows' && r.setup && r.setup.encoder);
  $('#judge-empty').hidden = !!rows.length;
  if (!rows.length) return;
  const encs = [...new Set(rows.map(r => r.setup.encoder))];
  const head = el('tr'); head.append(el('th', {}, ''));
  const ENC = {mert: 'MERT (m-a-p/MERT-v1-95M)', muq: 'MuQ (OpenMuQ/MuQ-large)'};
  for (const e of encs) head.append(el('th', {class: 'num'}, ENC[e] || rows.find(r => r.setup.encoder === e).setup.model || e));
  table.append(head);
  for (const [task, metrics] of JUDGE_ROWS) {
    const tr = el('tr', {class: 'tierrow'}); const td = el('td', {}, task[0].toUpperCase() + task.slice(1));
    td.colSpan = encs.length + 1; tr.append(td); table.append(tr);
    for (const [k, label] of metrics) {
      const row = el('tr'); row.append(el('td', {}, label));
      const vals = encs.map(e => { const r = rows.filter(x => x.setup.encoder === e && x.setup.task && x.setup.task.startsWith(task)).pop(); return r ? r.metrics[k] : null; });
      const top = Math.max(...vals.map(v => v ?? -1));
      const tied = vals.filter(v => v === top).length > 1;
      vals.forEach(v => { const c = el('td', {class: 'num'}, pts(v)); if (v != null && v === top && !tied) c.style.fontWeight = '700'; row.append(c); });
      table.append(row);
    }
  }
  const notes = [...new Set(rows.map(r => r.note).filter(Boolean))];
  $('#judge-note').textContent = notes.map(n => n.charAt(0).toUpperCase() + n.slice(1).replace(/\.?$/, '.')).join(' ');
}

// The default changes over time, and a row's own flag says what it was when it ran. Where a run also
// scored today's band-record default (TODAY_BAND), that setup is shown as the default instead.
const TODAY_BAND = 'rd-sax|same|rd-filosax-ft|';
// The setups shown by default in "Where the notes go" and the Lab grid; everything else is in a dropdown.
// Update when the default changes (ADR-0041) or a new challenger is being tested.
const PREV_BAND = 'demucs|same|ours|';
const CHALLENGER = 'mega|none|rd-filosax-ft|';
const FEATURED = [[TODAY_BAND, 'today’s default', 'Today'], [PREV_BAND, 'default before (Nov 5–9)', 'Before'],
                  [CHALLENGER, 'challenger', 'Challenger']];
function roleOf(k) { const f = FEATURED.find(x => x[0] === k); return f ? f[1] : ''; }
function buttonName(c) {
  const f = FEATURED.find(x => x[0] === c.k);
  const n = setupName(c.s);
  return f ? `${f[2]}: ${n}` : n;
}
function featured(cols) {
  const f = FEATURED.map(x => cols.find(c => c.k === x[0])).filter(Boolean);
  return f.length ? f : cols.slice(0, 3);
}
function shown(cols, extra) {
  const f = featured(cols);
  const x = extra && !f.some(c => c.k === extra) && cols.find(c => c.k === extra);
  return x ? f.concat([x]) : f;
}
// Every setup not featured, newest run first.
function fillOlder(sel, cols, rows, current, prompt) {
  const main = new Set(featured(cols).map(c => c.k));
  const last = new Map();
  for (const r of rows) { const k = setupKey(r.setup); if ((r.when || '') > (last.get(k) || '')) last.set(k, r.when || ''); }
  const rest = cols.filter(c => !main.has(c.k)).sort((a, b) => (last.get(b.k) || '').localeCompare(last.get(a.k) || ''));
  sel.replaceChildren(el('option', {value: ''}, rest.length ? `${prompt} (${rest.length})` : 'No older setups'));
  for (const c of rest) {
    const w = last.get(c.k);
    const o = el('option', {value: c.k}, `${setupName(c.s)}${w ? ' · ' + w.slice(0, 10) : ''}`);
    if (c.k === current) o.selected = true;
    sel.append(o);
  }
  sel.disabled = !rest.length;
}
function markToday() {
  const runs = new Set(EXP.filter(r => setupKey(r.setup) === TODAY_BAND).map(r => `${r.entry}|${rowKey(r)}`));
  EXP = EXP.map(r => {
    if (!runs.has(`${r.entry}|${rowKey(r)}`)) return r;
    const today = setupKey(r.setup) === TODAY_BAND;
    return today === !!r.default ? r : {...r, default: today, was_default: !!r.default};
  });
}

function renderCompare() {
  // One row per song: "four tenor tunes / walkers-theme" and "pfh / pfh" are the same song as "walkers-theme" and "pfh".
  EXP = (DATA.experiments || []).map(r => r.record && RECORDS[r.record] ? {...r, set: r.record, record: null, _set: r.set, _record: r.record} : r);
  markToday();
  grid(); pair(); breakdown(); stemGrid(); vocalGrid(); judgeGrid(); expTable();
}
$('#grid-tweaks').addEventListener('change', e => { cmp.tweaks = e.target.checked; grid(); });
segment($('#stem-metric'), v => { cmp.stemMetric = v; stemGrid(); });
$('#grid-metric').addEventListener('change', e => { cmp.metric = e.target.value; grid(); pair(); });
$('#grid-group').addEventListener('change', e => { cmp.gridGroup = e.target.value; cmp.gridOnly = ''; grid(); });
$('#grid-only').addEventListener('change', e => { cmp.gridOnly = e.target.value; grid(); });
segment($('#cmp-view'), v => {
  for (const k of ['grid', 'pair', 'stems']) $(`#view-${k}`).hidden = k !== v;
  $('#metric-row').hidden = v === 'stems';
});
$('#pair-a').addEventListener('change', e => { cmp.pairA = e.target.value; pair(); });
$('#pair-b').addEventListener('change', e => { cmp.pairB = e.target.value; pair(); });
segment($('#where-setup'), v => { cmp.setup = v; breakdown(); });
$('#where-older').addEventListener('change', e => { if (e.target.value) { cmp.setup = e.target.value; breakdown(); } });
$('#grid-older').addEventListener('change', e => { cmp.gridOlder = e.target.value || null; grid(); });
