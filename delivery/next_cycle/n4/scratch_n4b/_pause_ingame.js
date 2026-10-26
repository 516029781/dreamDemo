const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('C:/软件/鼠鼠/tools/capture/canvas_capture.js');
(async () => {
  const b = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new',
    args: ['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(String(e)));
  await p.goto('http://127.0.0.1:8803/', { waitUntil: 'networkidle2', timeout: 60000 });
  await p.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await p.evaluate(() => { window.__courtyard.reset(); window.__courtyard.closeDialogue(); window.__courtyard.resetView(); });
  await new Promise(r => setTimeout(r, 1500));
  await p.click('canvas');
  await new Promise(r => setTimeout(r, 400));
  await p.keyboard.press('p');
  await new Promise(r => setTimeout(r, 900));
  const meta = await captureCanvas(p, 'C:/软件/鼠鼠/delivery/next_cycle/n4/scratch_n4b/pause_ingame.png', { hideStats: true });
  const st = await p.evaluate(() => ({ paused: window.__courtyard.state ? window.__courtyard.state().paused : null }));
  console.log(JSON.stringify({ meta, st, errors: errs.slice(0, 3) }));
  await b.close();
})();
