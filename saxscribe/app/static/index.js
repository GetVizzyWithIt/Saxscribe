const horn = segment($('#horn'));
const engine = segment($('#engine'));
const mix = segment($('#mix'), () => { $('#mixHint').hidden = true; ready(); });
let chosen = null;

// Sax sections: rows of from-to times.
const TIME = /^\s*\d+(:\d{1,2}){0,2}\s*$/;
function addSection(a = '', b = '') {
  const row = document.createElement('div'); row.className = 'sec';
  row.innerHTML = `<input type="text" inputmode="decimal" class="t" aria-label="From" placeholder="3:45" value="${esc(a)}">
    <span class="quiet">to</span>
    <input type="text" inputmode="decimal" class="t" aria-label="To" placeholder="4:21" value="${esc(b)}">
    <button type="button" class="x" aria-label="Remove this section">×</button>`;
  $('#sections').append(row);
  row.querySelector('input').focus();
}
$('#addSec').addEventListener('click', () => addSection());
$('#sections').addEventListener('click', e => { const x = e.target.closest('.x'); if (x) x.parentElement.remove(); });
function toSec(t) { return t.trim().split(':').reduce((acc, p) => acc * 60 + Number(p), 0); }
// "3:45-4:21, 5:10-5:40", or throws with a message to show.
function sectionsText() {
  const out = [];
  for (const row of $('#sections').querySelectorAll('.sec')) {
    const [a, b] = [...row.querySelectorAll('input')].map(i => i.value.trim());
    if (!a && !b) continue;
    if (!TIME.test(a) || !TIME.test(b)) throw new Error('Write each sax section as two times, like 3:45 to 4:21.');
    if (toSec(b) <= toSec(a)) throw new Error(`The section ${a} to ${b} ends before it starts.`);
    out.push(`${a}-${b}`);
  }
  return out.join(', ');
}

function ready() { $('#go').disabled = !(chosen && mix() !== null); }
function choose(f) {
  chosen = f || null;
  $('#dropText').textContent = chosen ? chosen.name : 'Choose an audio file';
  ready();

}
$('#file').addEventListener('change', e => choose(e.target.files[0]));
const drop = $('#drop');
['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('over'); }));
['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('over'); }));
drop.addEventListener('drop', e => choose(e.dataTransfer.files[0]));

$('#go').addEventListener('click', () => {
  if (!chosen) return;
  let secs = '';
  try { secs = sectionsText(); } catch (err) { toast(err.message); return; }
  const form = new FormData();
  form.append('sections', secs);
  form.append('file', chosen);
  form.append('horn', horn());
  form.append('mix', mix());
  form.append('engine', engine());
  form.append('title', $('#title').value);
  form.append('artist', $('#artist').value);
  const xhr = new XMLHttpRequest();
  const bar = $('#upBar'); bar.hidden = false;
  $('#go').disabled = true; $('#upMsg').textContent = 'Uploading…';
  xhr.upload.onprogress = e => { if (e.lengthComputable) bar.firstElementChild.style.width = (100 * e.loaded / e.total) + '%'; };
  xhr.onload = () => {
    bar.hidden = true; bar.firstElementChild.style.width = '0';
    if (xhr.status === 200) {
      $('#upMsg').textContent = 'Uploaded. Transcribing below.';
      $('#title').value = ''; $('#artist').value = ''; $('#file').value = ''; $('#sections').replaceChildren();
      $('#mix').querySelectorAll('button').forEach(b => b.classList.remove('on')); $('#mixHint').hidden = false;
      choose(null);
      refresh();
    } else {
      let msg = 'Upload failed.'; try { msg = JSON.parse(xhr.responseText).detail; } catch (e) {}
      $('#upMsg').textContent = ''; toast(msg); $('#go').disabled = false;
    }
  };
  xhr.onerror = () => { bar.hidden = true; $('#upMsg').textContent = ''; toast('Upload failed: the Mac could not be reached.'); $('#go').disabled = false; };
  xhr.open('POST', '/api/takes'); xhr.send(form);
});

function clockOf(s) { const m = Math.floor(s / 60), r = Math.round(s % 60); return `${m}:${String(r).padStart(2, '0')}`; }
function since(stamp) {
  const t = Date.parse(stamp); if (!t) return '';
  const s = Math.max(0, Math.round((Date.now() - t) / 1000));
  return s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, '0')} s`;
}
function status(t) {
  if (t.state === 'done') return '';
  const log = (t.log || []).map(l => esc(l.replace(/^\[saxscribe\]\s*/, ''))).join('<br>');
  if (t.state === 'failed') return `<div class="failed small">Failed: ${esc(t.error || 'unknown error')}</div>${log ? `<div class="log">${log}</div>` : ''}`;
  if (t.state === 'stopped') return `<div class="small quiet">${esc(t.error || 'Stopped.')} Press Run again to start over.</div>`;
  if (t.state === 'queued') return '<div class="small quiet">Waiting its turn</div>';
  const slow = t.mix && t.layers_done === 0 ? ' Separating a band takes a few minutes; Terminal shows its progress.' : '';
  return `<div class="small quiet">Step ${Math.min(4, t.layers_done + 1)} of 4: ${esc(t.stage || 'Starting')}… (${since(t.started)})${slow}</div>
    <div class="bar"><div style="width:${Math.max(4, 25 * t.layers_done)}%"></div></div>
    ${log ? `<div class="log">${log}</div>` : ''}`;
}

function actions(t) {
  const remove = `<button data-act="remove" data-id="${t.id}" data-title="${esc(t.title)}">Remove</button>`;
  if (t.state === 'done') return `<a class="button primary" href="/take/${t.id}">Play along</a>
        <a class="button" href="/take/${t.id}/pdf">PDF</a>
        <button data-dl="/api/takes/${t.id}/file/musicxml">MusicXML</button>${remove}`;
  if (t.state === 'running' || t.state === 'queued') return `<button data-act="stop" data-id="${t.id}">Stop</button>`;
  return `<button class="primary" data-act="retry" data-id="${t.id}">Run again</button>${remove}`;
}

let timer;
async function refresh() {
  clearTimeout(timer);
  let list = [];
  try { list = await (await fetch('/api/takes')).json(); } catch (e) { timer = setTimeout(refresh, 4000); return; }
  const ul = $('#takes');
  if (!list.length) { ul.innerHTML = '<li class="quiet">Nothing yet. Upload a recording above.</li>'; return; }
  ul.innerHTML = list.map(t => `
    <li>
      <div class="info">
        <div class="title">${esc(t.title)}${t.artist ? ` <span class="quiet">· ${esc(t.artist)}</span>` : ''}</div>
        <div class="small quiet">${HORN_NAMES[t.horn] || esc(t.horn)} · ${t.mix ? 'with a band' : 'solo'}${t.engine === 'filosax' || (t.engine === 'auto' && t.mix) ? ' · our sax model' : t.engine === 'standard' && t.mix ? ' · old standard' : ''}${(t.sections || []).length ? ` · sax ${t.sections.map(([a, b]) => `${clockOf(a)}–${clockOf(b)}`).join(', ')}` : ''} · ${esc((t.added || '').replace('T', ' ').slice(0, 16))}</div>
        ${status(t)}
      </div>
      <div class="actions">${actions(t)}</div>
    </li>`).join('');
  if (list.some(t => t.state === 'queued' || t.state === 'running')) timer = setTimeout(refresh, 2000);
}
$('#takes').addEventListener('click', async e => {
  const d = e.target.closest('[data-dl]'); if (d) { download(d.dataset.dl); return; }
  const b = e.target.closest('[data-act]'); if (!b) return;
  const id = b.dataset.id, act = b.dataset.act;
  if (act === 'remove' && !confirm(`Remove "${b.dataset.title}" and its files?`)) return;
  b.disabled = true;
  const r = await fetch(act === 'remove' ? `/api/takes/${id}` : `/api/takes/${id}/${act}`,
                        {method: act === 'remove' ? 'DELETE' : 'POST'});
  if (!r.ok) { try { toast((await r.json()).detail); } catch (err) { toast('That did not work.'); } }
  refresh();
});

fetch('/api/info').then(r => r.json()).then(i => {
  const urls = i.urls.map(u => `<a href="${esc(u)}">${esc(u)}</a>`).join(' or ');
  $('#where').innerHTML = (urls ? `On your iPad (same Wi-Fi): ${urls}<br>` : '') + `Library folder: ${esc(i.library)}`;
}).catch(() => {});
refresh();
