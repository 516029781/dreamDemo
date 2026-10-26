/** V03 plant close-ups on the real engine canvas. */
const path = require('path');
const fs = require('fs');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('../../tools/capture/canvas_capture.js');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://127.0.0.1:8801/';
const TAG = process.argv[2] || 'final4';
const OUT = 'C:/软件/鼠鼠/delivery/next_cycle/T3';

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
  await page.evaluate(() => { window.__courtyard.setUi(false); window.__courtyard.closeDialogue(); });
  await new Promise((r) => setTimeout(r, 800));
  const shots = [];
  for (const id of ['ENV007', 'ENV008', 'ENV009', 'ENV011']) {
    await page.evaluate((asset) => window.__courtyard.focusAsset(asset), id);
    await new Promise((r) => setTimeout(r, 700));
    shots.push({ asset: id, meta: await captureCanvas(page, path.join(OUT, `plant_${TAG}_${id}.png`), { hideStats: true }) });
  }
  fs.writeFileSync(path.join(OUT, `plant_${TAG}_shots.json`), JSON.stringify({ tag: TAG, shots, page_errors: errors }, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ tag: TAG, shots: shots.length, page_errors: errors.length }));
  process.exit(errors.length ? 1 : 0);
})().catch((e) => { console.error('PLANT_SHOTS_FATAL', e); process.exit(2); });
