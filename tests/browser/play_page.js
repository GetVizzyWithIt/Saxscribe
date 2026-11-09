// Browser check of the play-along feedback page, on desktop (mouse + keys) and an
// iPad-sized touch screen (real touch events: tap, press-and-hold, hold-and-drag).
//
//   python -m tests.browser.serve_fixture 8799 &      # wait for READY <id>
//   node tests/browser/play_page.js http://127.0.0.1:8799 <take id> [out-folder]
//
// Needs Node with Playwright and Chromium. Not part of pytest (CI has no browser);
// run it before a pull request that touches play.js / play.html / app.css.
const {chromium, devices} = require('playwright');
const [base, takeId, out] = process.argv.slice(2);
if (!base || !takeId) { console.error('usage: node play_page.js <base url> <take id> [out folder]'); process.exit(2); }

let failed = 0;
function check(name, ok, detail) {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail !== undefined ? '  (' + detail + ')' : ''}`);
  if (!ok) failed++;
}
const wait = ms => new Promise(r => setTimeout(r, ms));
const state = page => page.evaluate(() => ({
  t: $('#audio').currentTime, paused: $('#audio').paused, rate: $('#audio').playbackRate,
  flags: flags.map(f => ({id: f.id, bar: f.bar, to: f.to, cats: f.categories})), sheet: !$('#sheet').hidden,
  editing: editing && {bar: editing.bar, to: editing.to, id: editing.id}, loop: loopRange, nBars, scrollY,
}));
async function clearFlags(page) {
  await page.evaluate(async () => { for (const f of flags) await fetch(`/api/takes/${takeId}/flags/${f.id}`, {method: 'DELETE'}); await loadFlags(); });
}
async function seekBar(page, bar, extra = 0) { await page.evaluate(([b, x]) => seekTo(barStart(b) + x), [bar, extra]); }
async function center(page, sel) {
  await page.locator(sel).first().scrollIntoViewIfNeeded();
  const b = await page.locator(sel).first().boundingBox();
  return {x: b.x + b.width / 2, y: b.y + b.height / 2};
}
async function barPoint(page, bar) {
  return page.evaluate(b => { const r = measureEl(b).querySelector('g.staff').getBoundingClientRect(); return {x: r.left + r.width / 2, y: r.top + r.height / 2}; }, bar);
}

async function run(name, ctxOpts, touch) {
  console.log(`\n== ${name}`);
  const browser = await chromium.launch({args: ['--autoplay-policy=no-user-gesture-required']});
  const ctx = await browser.newContext(ctxOpts);
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(`${base}/take/${takeId}`);
  await page.waitForFunction(() => document.querySelector('#score svg') && typeof nBars !== 'undefined' && nBars > 1 && run && run.label);
  await clearFlags(page);
  const cdp = touch ? await ctx.newCDPSession(page) : null;
  const touchAt = (type, p) => cdp.send('Input.dispatchTouchEvent', {type, touchPoints: type === 'touchEnd' ? [] : [{x: p.x, y: p.y}]});
  const tap = async p => { if (touch) await page.touchscreen.tap(p.x, p.y); else await page.mouse.click(p.x, p.y); };
  const press = async (p, ms, moveTo) => {  // press and hold (finger or mouse), optionally moving
    if (touch) {
      await touchAt('touchStart', p); await wait(ms / 2);
      if (moveTo) await touchAt('touchMove', moveTo);
      await wait(ms / 2); await touchAt('touchEnd', moveTo || p);
    } else {
      await page.mouse.move(p.x, p.y); await page.mouse.down(); await wait(ms / 2);
      if (moveTo) await page.mouse.move(moveTo.x, moveTo.y, {steps: 8});
      await wait(ms / 2); await page.mouse.up();
    }
  };

  // Layout: no horn switch, the run label, the title on the chart, one strip cell per bar.
  const s0 = await page.evaluate(() => ({view: !!document.querySelector('#view'), run: $('#runName').textContent,
    title: $('#score svg').textContent.includes('Fixture phrase'), cells: $('#strip').children.length, nBars,
    trackerOpen: $('#tracker').open, overflow: document.documentElement.scrollWidth > innerWidth + 1}));
  check('no Alto/Tenor/Concert switch', !s0.view);
  check('"Flags go to" names the run', /Standard/.test(s0.run), s0.run);
  check('title printed on the chart', s0.title);
  check('bar strip has one cell per bar', s0.cells === s0.nBars, `${s0.cells} cells, ${s0.nBars} bars`);
  check('tracker starts collapsed', !s0.trackerOpen);
  check('no sideways scroll', !s0.overflow);

  // Audio plays and the playhead moves.
  await tap(await center(page, '#play'));
  await wait(1500);
  let st = await state(page);
  const lit = await page.evaluate(() => document.querySelectorAll('#score g.now').length);
  check('audio plays', !st.paused && st.t > 0.8, `t=${st.t.toFixed(2)}`);
  check('current note lights up', lit > 0, lit);
  await tap(await center(page, '#play'));
  check('pause', (await state(page)).paused);

  // Zoom: A+ redraws the score bigger.
  const w0 = await page.evaluate(() => $('#score svg').getBoundingClientRect().height);
  await tap(await center(page, '#bigger'));
  await page.waitForFunction(h => document.querySelector('#score svg') && document.querySelector('#score svg').getBoundingClientRect().height > h + 1, w0, {timeout: 15000}).catch(() => {});
  const w1 = await page.evaluate(() => $('#score svg').getBoundingClientRect().height);
  check('A+ makes the notes bigger', w1 > w0, `${Math.round(w0)} -> ${Math.round(w1)} px`);
  await tap(await center(page, '#smaller'));
  await page.waitForFunction(h => document.querySelector('#score svg') && document.querySelector('#score svg').getBoundingClientRect().height < h - 1, w1, {timeout: 15000}).catch(() => {});
  const w2 = await page.evaluate(() => $('#score svg').getBoundingClientRect().height);
  check('A− makes them smaller again', w2 < w1, `${Math.round(w1)} -> ${Math.round(w2)} px`);

  // Tap ⚑ while playing: flags the bar heard about a second ago, keeps playing, offers Undo.
  await seekBar(page, 3, 0.6);
  await page.evaluate(() => playAudio()); await wait(700);
  const tTap = (await state(page)).t;
  const expect = await page.evaluate(t => barAtTime(t - 1), tTap);
  await tap(await center(page, '#flag'));
  await page.waitForFunction(() => flags.length === 1);
  st = await state(page);
  check('tap flags the bar heard a second ago', st.flags[0].bar === expect && st.flags[0].to === expect, `bar ${st.flags[0].bar}, expected ${expect}`);
  check('music keeps playing', !st.paused);
  check('toast offers Undo', await page.locator('#toast #undo').isVisible());
  await page.locator('#toast #undo').click();
  await page.waitForFunction(() => flags.length === 0);
  check('Undo removes it', (await state(page)).flags.length === 0);

  // Press and hold ⚑ while playing: flags every bar from press to release (finger drifts a bit).
  await page.evaluate(() => { audio.pause(); seekTo(barStart(1) + 1.2); playAudio(); });
  await wait(200);
  const fp = await center(page, '#flag');
  await press(fp, 4300, {x: fp.x + 25, y: fp.y - 20});
  await page.waitForFunction(() => flags.length === 1, null, {timeout: 5000}).catch(() => {});
  st = await state(page);
  check('hold flags a stretch of bars', st.flags.length === 1 && st.flags[0].to > st.flags[0].bar, JSON.stringify(st.flags));
  check('hold did not stop the music', !st.paused);
  // A quick flag inside that stretch merges into it.
  const merged = st.flags[0];
  await page.evaluate(() => { audio.pause(); });
  await page.evaluate(async b => { await post(`/api/takes/${takeId}/flags`, {bar: b, to: b, merge: true}); await loadFlags(); }, merged.to);
  st = await state(page);
  check('overlapping quick flag merges', st.flags.length === 1, JSON.stringify(st.flags));

  // Tap a flagged bar anywhere in its box: opens its flag screen, playing or paused.
  await page.evaluate(() => playAudio());
  const box = await page.locator('#score .flagbox[data-id]').first().boundingBox();
  await tap({x: box.x + box.width * 0.85, y: box.y + box.height * 0.8});
  await page.waitForFunction(() => !$('#sheet').hidden);
  st = await state(page);
  check('tapping a flagged bar opens its flag screen', st.sheet && st.editing.id === merged.id);
  check('its bars loop', st.loop && st.loop[1] > st.loop[0]);
  // Loop: playing past the end goes back to the start.
  await page.evaluate(() => { seekTo(loopRange[1] - 0.15); playAudio(); });
  await wait(900);
  st = await state(page);
  check('loop goes back to the flag\'s start', st.t < st.loop[1] && st.t >= st.loop[0] - 0.01, `t=${st.t.toFixed(2)} loop ${st.loop.map(x => x.toFixed(2))}`);

  // Steppers: − and + on each end.
  const r0 = st.editing;
  await tap(await center(page, '[data-r="to:-1"]'));
  await tap(await center(page, '[data-r="from:1"]'));
  st = await state(page);
  check('steppers change the range', st.editing.to === Math.max(r0.bar + 1, r0.to - 1) || st.editing.to === r0.to - 1, `${r0.bar}-${r0.to} -> ${st.editing.bar}-${st.editing.to}`);
  check('from never passes to', st.editing.bar <= st.editing.to);
  await tap(await center(page, '[data-r="from:-1"]'));
  await tap(await center(page, '[data-r="to:1"]'));
  st = await state(page);
  check('steppers go back', st.editing.bar === r0.bar && st.editing.to === r0.to, `${st.editing.bar}-${st.editing.to}`);
  check('sheet title shows the range', (await page.textContent('#sheetTitle')).includes(`${r0.bar}`));

  // Play controls in the sheet.
  await page.evaluate(() => audio.pause());
  await tap(await center(page, '#sPlay'));
  await wait(400);
  check('sheet ▶ plays', !(await state(page)).paused);
  await tap(await center(page, '#sPlay'));
  check('sheet ❚❚ pauses', (await state(page)).paused);
  await page.evaluate(() => seekTo(loopRange[0] + 1.5));
  const tb = (await state(page)).t;
  await tap(await center(page, '#sBack'));
  check('back 2 s', Math.abs((await state(page)).t - Math.max(0, tb - 2)) < 0.05);
  await tap(await center(page, '#sRestart'));
  check('back to the flag\'s start', Math.abs((await state(page)).t - Math.max(0, st.loop[0])) < 0.06);

  // Resize the sheet by its handle; double-tap shrinks it.
  const h0 = await page.evaluate(() => $('#sheet').offsetHeight);
  const g = await center(page, '#grab');
  if (touch) { await touchAt('touchStart', g); await touchAt('touchMove', {x: g.x, y: g.y - 60}); await touchAt('touchMove', {x: g.x, y: g.y - 120}); await touchAt('touchEnd', {x: g.x, y: g.y - 120}); }
  else { await page.mouse.move(g.x, g.y); await page.mouse.down(); await page.mouse.move(g.x, g.y - 120, {steps: 6}); await page.mouse.up(); }
  const h1 = await page.evaluate(() => $('#sheet').offsetHeight);
  check('drag the handle up: taller sheet', h1 > h0 + 60, `${h0} -> ${h1}`);
  const g2 = await center(page, '#grab');
  await tap(g2); await wait(80); await tap(g2);
  const h2 = await page.evaluate(() => $('#sheet').offsetHeight);
  check('double-tap the handle: shrinks', h2 <= 200, `${h1} -> ${h2}`);
  await tap(g2); await wait(450); await tap(await center(page, '#grab')); await wait(80); await tap(await center(page, '#grab'));
  const h3 = await page.evaluate(() => $('#sheet').offsetHeight);
  check('double-tap again: back to full size', h3 > 300, `${h2} -> ${h3}`);

  // Pick a reason and save.
  if (touch) await tap(await center(page, '#groups [data-g="wrong_notes"]'));
  else await page.keyboard.press('1');
  check('reason picked shows its detail chips', await page.locator('#cats button').count() === 6);
  await tap(await center(page, '#cats [data-c="pitch"]'));
  await page.fill('#flagText', 'a scoop into the note');
  if (touch) await tap(await center(page, '#saveFlag'));
  else { await page.locator('#flagText').blur(); await page.keyboard.press('Enter'); }
  await page.waitForFunction(() => $('#sheet').hidden);
  st = await state(page);
  check('saved with reason and note', JSON.stringify(st.flags[0].cats) === '["pitch"]', JSON.stringify(st.flags));
  check('loop stops when the sheet closes', !st.loop);

  // Sorting: two quick flags to sort, one after the other at 75%.
  await clearFlags(page);
  await page.evaluate(async () => { for (const b of [1, 3]) await post(`/api/takes/${takeId}/flags`, {bar: b, merge: true}); await loadFlags(); });
  check('"Sort 2 flags" button', (await page.textContent('#sortBtn')) === 'Sort 2 flags');
  await tap(await center(page, '#sortBtn'));
  await page.waitForFunction(() => !$('#sheet').hidden);
  st = await state(page);
  check('sorting opens the first, playing at 75%', st.editing.bar === 1 && st.rate === 0.75 && !st.paused, `bar ${st.editing.bar}, rate ${st.rate}`);
  check('Save says how many are left', (await page.textContent('#saveFlag')) === 'Save, next (1 left)');
  await tap(await center(page, '#groups [data-g="rhythm_feel"]'));
  await tap(await center(page, '#saveFlag'));
  await page.waitForFunction(() => editing && editing.bar === 3);
  check('Save moves to the next flag', (await state(page)).editing.bar === 3);
  await tap(await center(page, '#groups [data-g="not_sax"]'));
  await tap(await center(page, '#saveFlag'));
  await page.waitForFunction(() => $('#sheet').hidden);
  st = await state(page);
  check('all sorted: sheet closes, speed back to 100%', st.rate === 1 && (await page.locator('#sortBtn').isHidden()), `rate ${st.rate}`);
  check('reasons stored', JSON.stringify(st.flags.map(f => f.cats)) === '[["rhythm_feel"],["not_sax"]]', JSON.stringify(st.flags.map(f => f.cats)));

  // Tracker: opens, lists the flags, a row opens its flag screen.
  await tap(await center(page, '#tracker summary'));
  check('tracker opens', await page.evaluate(() => $('#tracker').open));
  const rows = await page.locator('#flagItems tr[data-id]').count();
  check('tracker lists this run\'s flags', rows === 2, rows);
  check('tracker shows the model run', (await page.textContent('#flagItems')).includes('Standard'));
  await tap(await center(page, '#flagItems tr[data-id]'));
  await page.waitForFunction(() => !$('#sheet').hidden);
  check('a tracker row opens its flag', (await state(page)).editing.bar === 1);
  await page.evaluate(() => closeSheet());
  await tap(await center(page, '#tracker summary'));

  // Press and drag across bars on the score: opens a new flag over that stretch.
  await clearFlags(page);
  await page.evaluate(() => { audio.pause(); window.scrollTo(0, 0); });
  await wait(300);
  const y0 = (await state(page)).scrollY;
  const a = await barPoint(page, 1), b = await barPoint(page, 2);
  await press(a, 1400, b);
  await page.waitForFunction(() => !$('#sheet').hidden, null, {timeout: 3000}).catch(() => {});
  st = await state(page);
  check('drag across bars opens a flag over them', st.sheet && st.editing && st.editing.bar === 1 && st.editing.to === 2, JSON.stringify(st.editing));
  if (touch) check('the drag did not scroll the page', Math.abs(st.scrollY - y0) < 5, `${y0} -> ${st.scrollY}`);
  await page.evaluate(() => closeSheet());
  // A quick swipe on the score still scrolls (only a hold selects).
  if (touch) {
    await page.evaluate(() => window.scrollTo(0, 0));
    const p = await barPoint(page, 1);
    await touchAt('touchStart', p); await touchAt('touchMove', {x: p.x, y: p.y - 40}); await touchAt('touchEnd', {x: p.x, y: p.y - 40});
    await wait(300);
    check('a quick swipe does not open a flag', (await state(page)).sheet === false);
  }

  // Paused, tap ⚑: opens the flag screen for the current bar.
  await seekBar(page, 2, 0.2);
  await tap(await center(page, '#flag'));
  await page.waitForFunction(() => !$('#sheet').hidden);
  check('paused tap opens the flag screen for this bar', (await state(page)).editing.bar === 2);
  await page.evaluate(() => closeSheet());

  // "Sax?" question as its bars play; one tap answers without stopping.
  const ask = await page.evaluate(() => suggested.length && !suggested[0].answer ? suggested[0].bars : null);
  if (ask) {
    await page.evaluate(b => { seekTo(barStart(b) - 0.6); playAudio(); }, ask[0]);
    await page.waitForFunction(() => !$('#ask').hidden, null, {timeout: 4000}).catch(() => {});
    check('"Sax?" pops up as its bars play', await page.locator('#ask').isVisible());
    if (await page.locator('#ask').isVisible()) {
      await tap(await center(page, '#ask [data-a="sax"]'));
      await page.waitForFunction(() => suggested[0].answer === 'sax');
      check('one tap answers it, music keeps going', !(await state(page)).paused);
    }
    await page.evaluate(() => audio.pause());
  } else console.log('SKIP  "Sax?" (none left unanswered in this take; checked on the first device)');

  // Bars played through count as heard ("looks right").
  await page.evaluate(() => { seekTo(0); audio.playbackRate = 2; playAudio(); });
  await wait(4500);
  await page.evaluate(() => audio.pause());
  await wait(500);
  const heardN = await page.evaluate(async () => (await (await fetch(`/api/takes/${takeId}/flags`)).json()).heard.length);
  check('bars played through are saved as heard', heardN >= 2, heardN);
  await page.evaluate(() => { audio.playbackRate = 1; $('#speed').value = '1'; });

  if (!touch) {
    // Keys: space, F (hold), S, ←, Esc.
    await clearFlags(page);
    await page.evaluate(() => { document.activeElement && document.activeElement.blur(); seekTo(barStart(1)); });
    await page.keyboard.press('Space'); await wait(400);
    check('space plays', !(await state(page)).paused);
    await page.keyboard.press('Space');
    check('space pauses', (await state(page)).paused);
    await page.evaluate(() => { seekTo(barStart(1) + 1.2); playAudio(); }); await wait(200);
    await page.keyboard.down('f'); await wait(2400); await page.keyboard.up('f');
    await page.waitForFunction(() => flags.length === 1, null, {timeout: 3000}).catch(() => {});
    st = await state(page);
    check('hold F flags a stretch', st.flags.length === 1 && st.flags[0].to > st.flags[0].bar, JSON.stringify(st.flags));
    await page.evaluate(() => audio.pause());
    await page.keyboard.press('s');
    await page.waitForFunction(() => !$('#sheet').hidden);
    check('S opens the next flag to sort', (await state(page)).editing.id === st.flags[0].id);
    const was = (await state(page)).paused;  // S starts sorting, which plays
    await page.keyboard.press('Space'); await wait(300);
    check('space plays/pauses inside the flag screen', (await state(page)).paused !== was);
    if (!(await state(page)).paused) await page.keyboard.press('Space');
    const tl = (await state(page)).t;
    await page.keyboard.press('ArrowLeft');
    check('← goes back 2 s', Math.abs((await state(page)).t - Math.max(0, tl - 2)) < 0.05);
    await page.keyboard.press('Escape');
    check('Esc closes', !(await state(page)).sheet);
  }

  if (out) await page.screenshot({path: `${out}/${name.replace(/\W+/g, '-')}.png`});
  check('no errors in the page', errors.length === 0, errors.join(' | '));
  await clearFlags(page);
  await browser.close();
}

(async () => {
  await run('iPad touch', {...devices['iPad Pro 11'], isMobile: true}, true);
  await run('desktop', {viewport: {width: 1280, height: 900}}, false);
  console.log(failed ? `\n${failed} check(s) failed` : '\nAll checks passed');
  process.exit(failed ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
