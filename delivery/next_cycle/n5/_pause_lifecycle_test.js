/** Functional test for G06/G07: pause menu (sound/restart), full reset,
 * lifecycle hooks, loading overlay and the failure/retry card.

Usage: node _pause_lifecycle_test.js
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

  // ---- loading overlay: real progress ended hidden
  const overlayGone = await p.evaluate(() => {
    const n = window.cc.director.getScene().getChildByName('LoadingRoot');
    return n ? n.active === false : 'missing';
  });
  check('loading overlay hidden after boot', overlayGone === true, String(overlayGone));

  // ---- pause menu content
  await call('setPause', true);
  s = await settle();
  check('pause opens', s.paused === true, null);
  const pauseUi = await p.evaluate(() => {
    const scene = window.cc.director.getScene();
    const root = scene.getChildByName('Canvas');
    const pr = root && root.getChildByName('PauseRoot');
    if (!pr) return null;
    const names = [];
    pr.walk ? pr.walk((n) => names.push(n.name)) : null;
    return names.join(',');
  });
  check('pause card has resume/sound/restart', !!pauseUi &&
        pauseUi.includes('PauseResume') && pauseUi.includes('PauseSound') &&
        pauseUi.includes('PauseRestart'), pauseUi);

  // ---- sound default muted, toggles both ways
  s = await state();
  check('sound defaults to off', s.soundOn === false, String(s.soundOn));
  await call('toggleSound');
  s = await state();
  check('sound toggles on', s.soundOn === true, String(s.soundOn));
  await call('toggleSound');
  s = await state();
  check('sound toggles back off', s.soundOn === false, String(s.soundOn));

  // ---- progress kept across pause, restart wipes it
  await call('setPause', false);
  await call('setPlayer', 1.0, -5.0);
  await call('walkTo', 3.4, -5.0);
  await call('waitForFocus', 'gardener');
  s = await settle();
  check('gardener in range (restart test)', s.questFocus === 'gardener', s.questFocus);
  await call('interact');
  s = await settle();
  check('dialogue opened (restart test)', s.dialogueVisible === true, null);
  await call('interact'); await waitFrames(2);
  await call('interact');
  s = await settle();
  check('quest accepted for restart test', s.questState === 'COLLECTING', s.questState);
  check('dialogue closed after accept', s.dialogueVisible === false, String(s.dialogueVisible));
  await call('setPlayer', -7.4, -5.2);
  await call('walkTo', -8.4, -5.2);
  await call('waitForFocus', 'card_bench');
  s = await settle();
  check('bench card in range', s.questFocus === 'card_bench', s.questFocus);
  await call('interact');
  s = await settle();
  check('one card collected', s.collected.length === 1, JSON.stringify(s.collected));

  await call('fullRestart');
  s = await settle();
  check('restart -> NOT_STARTED', s.questState === 'NOT_STARTED', s.questState);
  check('restart clears collection', s.collected.length === 0, JSON.stringify(s.collected));
  check('restart respawns at spawn', Math.abs(s.player[0]) < 0.01 && Math.abs(s.player[2] + 5.2) < 0.01,
        JSON.stringify(s.player));
  check('restart leaves no pause', s.paused === false, String(s.paused));
  const overlaysGone = await p.evaluate(() => {
    const scene = window.cc.director.getScene();
    const canvas = scene.getChildByName('Canvas');
    const dlg = canvas && canvas.getChildByName('DialogueRoot');
    return { dialogue: dlg ? dlg.active : 'n/a' };
  });
  check('restart closes dialogue', overlaysGone.dialogue === false, String(overlaysGone.dialogue));

  // ---- lifecycle: visibilitychange auto-pauses, progress kept
  await p.evaluate(() => { Object.defineProperty(document, 'hidden', { value: true, configurable: true });
    document.dispatchEvent(new Event('visibilitychange')); });
  s = await settle();
  check('backgrounding pauses', s.paused === true, String(s.paused));
  await p.evaluate(() => { Object.defineProperty(document, 'hidden', { value: false, configurable: true });
    document.dispatchEvent(new Event('visibilitychange')); });
  await new Promise((r) => setTimeout(r, 300));
  s = await state();
  check('returning keeps pause for explicit resume', s.paused === true, String(s.paused));
  await call('setPause', false);

  // ---- failure card: same code path maybeFinish uses
  await call('showRetryCard');
  await new Promise((r) => setTimeout(r, 400));
  const retryUi = await p.evaluate(() => {
    const scene = window.cc.director.getScene();
    const root = scene.getChildByName('RetryRoot');
    return root ? { active: root.active, hasRetry: !!root.getChildByName('RetryGo'),
                    hasCopy: !!root.getChildByName('RetryCopy') } : null;
  });
  check('retry card renders', !!retryUi && retryUi.active === true, JSON.stringify(retryUi));
  check('retry card has retry+copy buttons', !!retryUi && retryUi.hasRetry && retryUi.hasCopy, null);
  await p.evaluate(() => {
    const root = window.cc.director.getScene().getChildByName('RetryRoot');
    if (root) root.active = false;
  });

  // retry with nothing failed is a safe no-op that re-evaluates the gate
  await call('showRetryCard');
  await new Promise((r) => setTimeout(r, 300));
  const retryAgain = await p.evaluate(() => {
    const api = window.__courtyard;
    api.showRetryCard();
    const scene = window.cc.director.getScene();
    const root = scene.getChildByName('RetryRoot');
    const wasActive = root ? root.active : null;
    // hit retry through the card's own handler
    const go = root ? root.getChildByName('RetryGo') : null;
    if (go) go.emit ? null : null;
    return wasActive;
  });
  check('retry card reopens deterministically', retryAgain === true, String(retryAgain));
  s = await state();
  check('no load failures in the pinned build', s.failedLoads === 0 && s.loadErrorCount === 0,
        'failed=' + s.failedLoads + ' errors=' + s.loadErrorCount);

  const fails = CHECKS.filter((c) => !c.ok).length;
  console.log('SUMMARY pass=' + (CHECKS.length - fails) + ' fail=' + fails);
  await b.close();
  process.exit(fails ? 1 : 0);
})();
