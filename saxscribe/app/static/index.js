const horn = segment($('#horn'));
const mix = segment($('#mix'));
let chosen = null;

function choose(f) {
  chosen = f || null;
  $('#dropText').textContent = chosen ? chosen.name : 'Choose an audio file';
  $('#go').disabled = !chosen;
  if (chosen && !$('#title').value) $('#title').placeholder = chosen.name.replace(/\.[^.]+$/, '');
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
      $('#title').value = ''; $('#file').value = ''; choose(null);
      refresh();
    } else {
      let msg = 'Upload failed.'; try { msg = JSON.parse(xhr.responseText).detail; } catch (e) {}
      $('#upMsg').textContent = ''; toast(msg); $('#go').disabled = false;
    }
  };
  xhr.onerror = () => { bar.hidden = true; $('#upMsg').textContent = ''; toast('Upload failed: the Mac could not be reached.'); $('#go').disabled = false; };
  xhr.open('POST', '/api/takes'); xhr.send(form);
});

function status(t) {
  if (t.state === 'done') return '';
  if (t.state === 'failed') return `<div class="failed small">Failed: ${esc(t.error || 'unknown error')}</div>`;
  const words = t.state === 'queued' ? 'Waiting its turn' : `${esc(t.stage || 'Starting')}…`;
  return `<div class="small quiet">${words}</div><div class="bar"><div style="width:${Math.max(4, 25 * t.layers_done)}%"></div></div>`;
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
      ${t.state === 'done' ? `<div class="actions">
        <a class="button primary" href="/take/${t.id}">Play along</a>
        <button data-dl="/api/takes/${t.id}/file/pdf">PDF</button>
        <button data-dl="/api/takes/${t.id}/file/musicxml">MusicXML</button>
      </div>` : ''}
    </li>`).join('');
  if (list.some(t => t.state === 'queued' || t.state === 'running')) timer = setTimeout(refresh, 2000);
}
$('#takes').addEventListener('click', e => { const b = e.target.closest('[data-dl]'); if (b) download(b.dataset.dl); });

fetch('/api/info').then(r => r.json()).then(i => {
  const urls = i.urls.map(u => `<a href="${esc(u)}">${esc(u)}</a>`).join(' or ');
  $('#where').innerHTML = (urls ? `On your iPad (same Wi-Fi): ${urls}<br>` : '') + `Library folder: ${esc(i.library)}`;
}).catch(() => {});
refresh();
