/** Q07 capture: formal + bench close-up for a given tag. */
const path = require('path');
const fs = require('fs');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('../../tools/capture/canvas_capture.js');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://127.0.0.1:8801/';
const TAG = process.argv[2] || 'edited';
const OUT = 'C:/软件/鼠鼠/delivery/next_cycle/T5';

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await page.evaluate(() => { window.__courtyard.reset(); window.__courtyard.closeDialogue(); window.__courtyard.setUi(false); });
  await new Promise((r) => setTimeout(r, 900));
  const formal = await captureCanvas(page, path.join(OUT, `q07_${TAG}_formal.png`), { hideStats: true });
  await page.evaluate(() => window.__courtyard.focusAsset('PROP001'));
  await new Promise((r) => setTimeout(r, 900));
  const bench = await captureCanvas(page, path.join(OUT, `q07_${TAG}_bench.png`), { hideStats: true });
  const cam = await page.evaluate(() => {
    const c = cc.director.getScene().getChildByName('Main Camera');
    const e = c.eulerAngles;
    return { position: [c.position.x, c.position.y, c.position.z], euler: [e.x, e.y, e.z], fov: c.getComponent(cc.Camera).fov };
  });
  fs.writeFileSync(path.join(OUT, `q07_${TAG}_capture.json`), JSON.stringify({ tag: TAG, formal, bench, camera: cam, page_errors: errors }, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ tag: TAG, errors: errors.length }));
  process.exit(errors.length ? 1 : 0);
})().catch((e) => { console.error('Q07_CAPTURE_FATAL', e); process.exit(2); });
