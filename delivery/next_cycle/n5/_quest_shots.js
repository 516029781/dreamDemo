/** Evidence shots for the G01 quest loop: one frame per quest state, driven
 * through the same harness hooks the functional test uses. */
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('C:/软件/鼠鼠/tools/capture/canvas_capture.js');

const OUT = 'C:/软件/鼠鼠/delivery/next_cycle/n5/T3';

(async () => {
  const b = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl',
           '--ignore-gpu-blocklist', '--no-sandbox', '--disable-gpu-sandbox'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const p = await b.newPage();
  await p.goto('http://127.0.0.1:8805/', { waitUntil: 'networkidle2', timeout: 60000 });
  await p.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 90000 });
  await new Promise((r) => setTimeout(r, 800));
  const call = (fn, ...args) => p.evaluate((f, ...a) => window.__courtyard[f](...a), fn, ...args);
  const shot = (name) => captureCanvas(p, OUT + '/quest_' + name + '.png', { hideStats: false });
  const settle = async () => {
    for (let i = 0; i < 12; i++) await new Promise((r) => setTimeout(r, 150));
  };

  // NOT_STARTED: gardener in range, talk button up
  await call('setPlayer', 3.4, -5.0);
  await settle();
  await shot('not_started');

  // accept -> COLLECTING, stand next to the bench card
  await call('interact');
  await settle();
  await call('interact');
  await new Promise((r) => setTimeout(r, 250));
  await call('interact');
  await settle();
  await call('setPlayer', -7.6, -5.2);
  await settle();
  await shot('collecting');

  // pick two, then the third flips to READY
  await call('interact');
  await settle();
  await call('setPlayer', 4.4, -6.0);
  await settle();
  await call('walkTo', 5.2, -6.4);
  await settle();
  await call('interact');
  await settle();
  await shot('collecting_two');

  await call('setPlayer', 5.4, 5.4);
  await settle();
  await call('walkTo', 6.2, 6.2);
  await settle();
  await call('interact');
  await settle();
  await shot('ready');

  // submit
  await call('setPlayer', 3.4, 5.4);
  await settle();
  await call('walkTo', 0.5, 5.8);
  await settle();
  await call('interact');
  await new Promise((r) => setTimeout(r, 1600));
  await shot('done');

  const s = await p.evaluate(() => window.__courtyard.state());
  console.log('final state ' + s.questState + ' board=' + s.boardState +
              ' collected=' + JSON.stringify(s.collected));
  await b.close();
})();
