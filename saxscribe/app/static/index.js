const horn = segment($('#horn'));
const mix = segment($('#mix'), () => { $('#mixHint').hidden = true; ready(); });
let chosen = null;

function ready() { $('#go').disabled = !(chosen && mix() !== null); }
function choose(f) {
  chosen = f || null;
  $('#dropText').textContent = chosen ? chosen.name : 'Choose an audio file';
  ready();
  $('#title').placeholder = chosen ? chosen.name.replace(/\.[^.]+$/, '') : 'e.g. Pennies from Heaven, Stan Getz';
}
$('#file').addEventListener('change', e => choose(e.target.files[0]));
const drop = $('#drop');
['dragenter', 'dragover'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('over'); }));
['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('over'); }));
drop.addEventListener('drop', e => choose(e.dataTransfer.files[0]));

$('#go').addEventListener('click', () => {
  if (!chosen) return;
  const form = new FormData();
  form.append('file', chosen);
  form.append('horn', horn());
  form.append('mix', mix());
  form.append('title', $('#title').value);
  const xhr = new XMLHttpRequest();
  const bar = $('#upBar'); bar.hidden = false;
  $('#go').disabled = true; $('#upMsg').textContent = 'Uploading…';
  xhr.upload.onprogress = e => { if (e.lengthComputable) bar.firstElementChild.style.width = (100 * e.loaded / e.total) + '%'; };
  xhr.onload = () => {
    bar.hidden = true; bar.firstElementChild.style.width = '0';
    if (xhr.status === 200) {
      $('#upMsg').textContent = 'Uploaded. Transcribing below.';
      $('#title').value = ''; $('#file').value = '';
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
        <button data-dl="/api/takes/${t.id}/file/pdf">PDF</button>
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
        <div class="title">${esc(t.title)}</div>
        <div class="small quiet">${HORN_NAMES[t.horn] || esc(t.horn)} · ${t.mix ? 'with a band' : 'solo'} · ${esc((t.added || '').replace('T', ' ').slice(0, 16))}</div>
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
