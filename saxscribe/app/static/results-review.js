// Results page, Needs review tab: the match check's chart/recording pairs (GET /api/review,
// score/review.py). Each pair opens to its recording with the answer key playing along as soft tones,
// and Austin's verdict (good / wrong / not sure, plus a note) is saved back to the Mac.

const VERDICT = {pass: 'Passed', check: 'Check', reject: 'Set aside', pending: 'No key yet'};
const MINE = {good: 'You: good match', wrong: 'You: wrong match', unsure: 'You: not sure'};
const rv = {filter: 'todo', open: null};

// A pair needs a look when the check is unsure (or set it aside) and Austin has not said yet.
function needsLook(e) { return ['check', 'reject'].includes(e.verdict) && !e.austin_verdict; }

function reviewFacts(e) {
  const f = [];
  if (e.heard_agree != null) f.push(`key heard ${Math.round(100 * e.heard_agree)}%`);
  if (e.coverage != null) f.push(`covers ${Math.round(100 * e.coverage)}% of the sax`);
  if (e.length_s != null) f.push(`recording ${fmtSec(e.length_s)}${e.expected_length_s != null ? ` (expected ${fmtSec(e.expected_length_s)})` : ''}`);
  if (e.tempo_jumps) f.push(`${e.tempo_jumps} tempo jump${e.tempo_jumps > 1 ? 's' : ''}`);
  if (e.sax_judge != null) f.push(`sax judge ${typeof e.sax_judge === 'number' ? Math.round(100 * e.sax_judge) + '%' : e.sax_judge}`);
  if (e.in_training) f.push('used in training');
  return f.join(' · ');
}

function renderReview() {
  const R = prog.review;
  const list = $('#review-list'); list.replaceChildren();
  const sum = $('#review-summary');
  const badge = $('#review-count');
  if (!R || !R.exists) {
    badge.hidden = true;
    sum.textContent = '';
    list.append(el('p', {class: 'quiet'}, 'No match report yet. The match check writes ' +
      `${R ? R.report : '~/saxscribe-runs/keys/match_report.jsonl'} on the Mac; pairs show here once it has run.`));
    return;
  }
  const E = R.entries;
  const todo = E.filter(needsLook);
  badge.hidden = !todo.length; badge.textContent = todo.length;
  const by = v => E.filter(e => e.verdict === v).length;
  sum.textContent = `${E.length} pairs: ${by('pass')} passed, ${by('check')} to check, ${by('reject')} set aside` +
    `${by('pending') ? `, ${by('pending')} with no key yet` : ''}. ${E.filter(e => e.benchmark).length} count toward the benchmark.`;
  const shown = E.filter(e => rv.filter === 'all' ? true : rv.filter === 'todo' ? needsLook(e) : e.verdict === rv.filter)
    .sort((a, b) => (a.heard_agree ?? 2) - (b.heard_agree ?? 2));
  if (!shown.length) {
    list.append(el('p', {class: 'quiet'}, rv.filter === 'todo' ? 'Nothing waiting for you.' : 'None.'));
    return;
  }
  for (const e of shown) list.append(pairCard(e));
}

function pairCard(e) {
  const d = el('details', {class: 'pair'});
  if (rv.open === e.id) d.open = true;
  const s = el('summary');
  s.append(el('span', {class: 't'}, [e.tune, e.performer].filter(Boolean).join(' · ') || e.id));
  s.append(el('span', {class: `chip ${e.verdict}`}, VERDICT[e.verdict] || e.verdict || '?'));
  if (e.austin_verdict) s.append(el('span', {class: 'chip mine'}, MINE[e.austin_verdict] || e.austin_verdict));
  if (e.benchmark) s.append(el('span', {class: 'chip pass'}, 'in benchmark'));
  if (e.instrument) s.append(el('span', {class: 'facts'}, e.instrument));
  if (e.reason) s.append(el('span', {class: 'why'}, e.reason));
  s.append(el('span', {class: 'facts', style: 'flex-basis:100%'}, reviewFacts(e)));
  d.append(s);
  d.addEventListener('toggle', () => {
    if (d.open) { rv.open = e.id; if (!d.querySelector('.body')) d.append(pairBody(e)); }
    else { if (rv.open === e.id) rv.open = null; const a = d.querySelector('audio'); if (a) a.pause(); }
  });
  if (d.open) d.append(pairBody(e));
  return d;
}

function pairBody(e) {
  const b = el('div', {class: 'body'});
  const audio = el('audio', {controls: '', preload: 'metadata', src: `/api/review/${encodeURIComponent(e.id)}/audio`});
  audio.addEventListener('error', () => { audio.replaceWith(el('p', {class: 'failed small'}, 'The recording is not where the report says.')); });
  b.append(audio);
  const row = el('div', {class: 'acts'});
  const along = el('label', {class: 'small'});
  const box = el('input', {type: 'checkbox'}); box.checked = true;
  along.append(box, document.createTextNode(' Play the key along (soft tones at the key’s pitches)'));
  row.append(along);
  b.append(row);
  keyAlong(e, audio, box);
  const acts = el('div', {class: 'acts'});
  const note = el('textarea', {placeholder: 'What did you hear? (optional, e.g. "chart starts at the second chorus")'});
  note.value = e.austin_note || '';
  for (const [v, label] of [['good', 'Good match'], ['wrong', 'Wrong match'], ['unsure', 'Not sure']]) {
    const btn = el('button', {type: 'button', class: e.austin_verdict === v ? 'on' : ''}, label);
    btn.addEventListener('click', () => saveVerdict(e, e.austin_verdict === v ? null : v, note.value));
    acts.append(btn);
  }
  b.append(acts, note);
  const meta = [e.id, e.source, e.checked && `checked ${e.checked}`].filter(Boolean).join(' · ');
  b.append(el('p', {class: 'quiet small'}, meta));
  return b;
}

async function saveVerdict(e, verdict, note) {
  try {
    const r = await fetch(`/api/review/${encodeURIComponent(e.id)}`, {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({verdict, note})});
    if (!r.ok) throw new Error(await r.text());
    prog.review = await r.json();
    rv.open = e.id;
    renderReview();
    if (prog.B) benchNote(prog.B);
  } catch (err) {
    alert(`Could not save: ${err.message}`);
  }
}

// Soft sine tones for the key's notes, scheduled against the audio element's clock.
let actx = null;
function keyAlong(e, audio, box) {
  let notes = null, timer = null, voices = [];
  const stop = () => { clearInterval(timer); timer = null; voices.forEach(v => { try { v.stop(); } catch (_) {} }); voices = []; };
  async function start() {
    stop();
    if (!box.checked || audio.paused) return;
    if (!notes) {
      try { notes = (await (await fetch(`/api/review/${encodeURIComponent(e.id)}/key`)).json()).notes || []; } catch (_) { notes = []; }
    }
    actx = actx || new (window.AudioContext || window.webkitAudioContext)();
    if (actx.state === 'suspended') await actx.resume();
    let next = notes.findIndex(n => n.offset > audio.currentTime);
    if (next < 0) return;
    const tick = () => {
      const now = audio.currentTime, ahead = now + 0.6;
      while (next < notes.length && notes[next].onset < ahead) {
        const n = notes[next++];
        const t0 = actx.currentTime + Math.max(0, n.onset - now), t1 = actx.currentTime + Math.max(0.05, n.offset - now);
        const o = actx.createOscillator(), g = actx.createGain();
        o.type = 'sine'; o.frequency.value = 440 * Math.pow(2, (n.pitch - 69) / 12);
        g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(0.12, t0 + 0.02);
        g.gain.setValueAtTime(0.12, Math.max(t0 + 0.02, t1 - 0.04)); g.gain.linearRampToValueAtTime(0, t1);
        o.connect(g).connect(actx.destination); o.start(t0); o.stop(t1 + 0.02);
        voices.push(o); o.onended = () => { voices = voices.filter(v => v !== o); };
      }
    };
    tick(); timer = setInterval(tick, 200);
  }
  audio.addEventListener('play', start);
  audio.addEventListener('seeked', start);
  audio.addEventListener('ratechange', start);
  audio.addEventListener('pause', stop);
  audio.addEventListener('ended', stop);
  box.addEventListener('change', start);
}

segment($('#review-filter'), v => { rv.filter = v; renderReview(); });

async function loadReview() {
  try { prog.review = await (await fetch('/api/review')).json(); } catch (_) { prog.review = null; }
  renderReview();
  if (prog.B) benchNote(prog.B);
}
loadReview();
