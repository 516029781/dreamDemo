/** Functional test for the G01 quest loop, run against the pinned build.

Walks the whole DEMO_EXECUTION_SPEC §5 state table:
  NOT_STARTED -> talk -> COLLECTING -> pick 3 (dedup) -> READY -> submit -> DONE
  -> early board visit -> restart -> NOT_STARTED

Usage: node _quest_test.js
*/
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');

const CHECKS = [];
function check(name, ok, detail) {
  CHECKS.push({ name, ok, detail });
  console.log((ok ? 'PASS ' : 'FAIL ') + name + (detail !== null && detail !== undefined && detail !== '' ? '  ' + detail : ''));
}

(async () => {
  const b = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl',
           '--ignore-gpu-blocklist', '--no-sandbox', '--disable-gpu-sandbox'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const p = await b.newPage();
  p.on('pageerror', (e) => console.log('PAGE_ERROR ' + e.message));
  await p.goto('http://127.0.0.1:8805/', { waitUntil: 'networkidle2', timeout: 60000 });
  await p.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 90000 });
  await new Promise((r) => setTimeout(r, 700));

  // CDP drops functions when an object crosses the wire, so every call runs
  // inside the page; only serialisable data comes back.
  const state = () => p.evaluate(() => window.__courtyard.state());
  const call = (fn, ...args) => p.evaluate((f, ...a) => window.__courtyard[f](...a), fn, ...args);
  // swiftshader renders a few fps; "two identical polls" can both land before
  // any frame runs, so stability checks lie. Await real update() frames via
  // frameTick, then one more frame so per-frame derives are done.
  const waitFrames = async (n = 2) => {
    const start = (await state()).frameTick;
    for (;;) {
      const s = await state();
      if (s.frameTick >= start + n) return s;
      await new Promise((r) => setTimeout(r, 100));
    }
  };
  const settle = async () => {
    await waitFrames(3);
    return waitFrames(1);
  };

  // 1. fresh state
  let s = await state();
  check('boot state is NOT_STARTED', s.questState === 'NOT_STARTED', s.questState);
  check('board starts empty', s.boardState === 'empty', s.boardState);

  // 2. far from everything: no interaction candidate
  await call('setPlayer', -10, 8);
  await call('waitForFocus', 'null');
  s = await settle();
  check('no candidate far away', s.questFocus === null, s.questFocus);

  // 3. approach along open paving (a straight line from the far corner is
  // correctly blocked by the central flowerbed), then accept the quest
  await call('setPlayer', 1.0, -5.0);
  await call('walkTo', 3.4, -5.0);
  await call('waitForFocus', 'gardener');
  s = await settle();
  check('gardener in range', s.questFocus === 'gardener', s.questFocus);
  await call('interact');
  s = await settle();
  check('dialogue opened', s.dialogueVisible === true, null);
  await call('interact'); // page 1 -> page 2
  await new Promise((r) => setTimeout(r, 250));
  await call('interact'); // accept
  s = await settle();
  check('accepted -> COLLECTING', s.questState === 'COLLECTING', s.questState);
  check('hud shows 0/3', s.questTitle === '找回明信片 0/3', s.questTitle);

  // 4. early board visit: the hint must fire and consume nothing
  await call('setPlayer', 0.5, 5.8);
  await call('waitForFocus', 'board');
  s = await settle();
  check('board in range while COLLECTING', s.questFocus === 'board', s.questFocus);
  await call('interact');
  s = await settle();
  check('early visit keeps NOT collected', s.collected.length === 0, JSON.stringify(s.collected));
  check('early visit keeps COLLECTING', s.questState === 'COLLECTING', s.questState);

  // 5. pick the three cards; the collected one must leave the candidates
  const spots = [[-8.4, -5.2], [5.2, -6.4], [6.2, 6.2]];
  const near = [[-7.4, -5.2], [4.4, -6.0], [5.4, 5.4]];
  const ids = ['card_bench', 'card_flower', 'card_pergola'];
  for (let i = 0; i < spots.length; i++) {
    await call('setPlayer', near[i][0], near[i][1]);
    await call('walkTo', spots[i][0], spots[i][1]);
    await call('waitForFocus', ids[i]);
    s = await settle();
    check('focus ' + ids[i], s.questFocus === ids[i], s.questFocus);
    await call('interact');
    s = await settle();
    check('collected ' + (i + 1) + '/3', s.collected.length === i + 1, JSON.stringify(s.collected));
    // 3/3 flips the state to READY in the same step, so the HUD row changes
    const expect = i < 2 ? (i + 1) + '/3' : '将明信片挂回留言板';
    check('hud after pick ' + (i + 1), s.questTitle.indexOf(expect) >= 0, s.questTitle);
  }
  // dedup: return to the first spot; it must be gone from the candidates
  await call('setPlayer', -7.4, -5.2);
  await call('walkTo', -8.4, -5.2);
  s = await settle();
  check('collected card left the candidates', s.questFocus !== 'card_bench', s.questFocus);

  // 6. READY + submit exactly once
  s = await state();
  check('3/3 -> READY', s.questState === 'READY', s.questState);
  check('hud shows READY row', s.questTitle === '将明信片挂回留言板', s.questTitle);

  await call('setPlayer', 3.4, 5.4);
  await call('walkTo', 0.5, 5.8);
  await call('waitForFocus', 'board');
  s = await settle();
  check('board in range when READY', s.questFocus === 'board', s.questFocus);
  await call('interact');
  await new Promise((r) => setTimeout(r, 1400)); // complete panel opens on a timer
  s = await state();
  check('submit -> DONE', s.questState === 'DONE', s.questState);
  check('board shows 3 cards', s.boardState === 'full', s.boardState);
  await call('interact'); // submit again
  s = await settle();
  check('second submit is a no-op', s.questState === 'DONE' && s.boardState === 'full',
        s.questState + '/' + s.boardState);

  // 7. restart clears everything back to the spec's initial row
  await call('reset');
  s = await settle();
  check('reset -> NOT_STARTED', s.questState === 'NOT_STARTED', s.questState);
  check('reset clears collection', s.collected.length === 0, JSON.stringify(s.collected));

  const fails = CHECKS.filter((c) => !c.ok).length;
  console.log('SUMMARY pass=' + (CHECKS.length - fails) + ' fail=' + fails);
  await b.close();
  process.exit(fails ? 1 : 0);
})();
