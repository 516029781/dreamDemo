/**
 * V-cycle game screenshots: real canvas capture via tools/capture/canvas_capture.js.
 * Usage: node delivery/next_cycle/_v06_game_shots.js <tag> [outDir]
 */
const path = require('path');
const fs = require('fs');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('../../../tools/capture/canvas_capture.js');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://127.0.0.1:8803/';
const TAG = process.argv[2] || 'before';
const OUT = process.argv[3] || 'C:/软件/鼠鼠/delivery/next_cycle/n4/T3';

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  const logs = [];
  const pageErrors = [];
  page.on('pageerror', (e) => pageErrors.push(String(e)));
  page.on('console', (m) => { if (m.text().includes('[COURTYARD]')) logs.push(m.text()); });
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await page.evaluate(() => {
    window.__courtyard.reset();
    window.__courtyard.closeDialogue();
    window.__courtyard.resetView();
  });
  await new Promise((r) => setTimeout(r, 1200));

  const shots = [];
  await page.evaluate(() => window.__courtyard.setUi(false));
  await new Promise((r) => setTimeout(r, 500));
  shots.push({ name: 'formal_no_ui', meta: await captureCanvas(page, path.join(OUT, `game_${TAG}_formal_no_ui.png`), { hideStats: true }) });

  await page.evaluate(() => window.__courtyard.setUi(true));
  await new Promise((r) => setTimeout(r, 400));
  shots.push({ name: 'formal_ui', meta: await captureCanvas(page, path.join(OUT, `game_${TAG}_formal_ui.png`), { hideStats: true }) });

  await page.evaluate(() => window.__courtyard.openDialogue(1));
  await new Promise((r) => setTimeout(r, 700));
  shots.push({ name: 'dialogue', meta: await captureCanvas(page, path.join(OUT, `game_${TAG}_dialogue.png`), { hideStats: true }) });

  const stats = await page.evaluate(() => window.__courtyard.renderStats()).catch(() => null);
  const state = await page.evaluate(() => window.__courtyard.state()).catch(() => null);
  fs.writeFileSync(path.join(OUT, `game_${TAG}_shots.json`), JSON.stringify({
    tag: TAG, generated_at: new Date().toISOString(), shots, stats, state,
    logs: logs.slice(-20), page_errors: pageErrors,
    page_shot_used: false,
  }, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ tag: TAG, shots: shots.length, page_errors: pageErrors.length }));
  process.exit(pageErrors.length ? 1 : 0);
})().catch((error) => { console.error('V06_SHOTS_FATAL', error); process.exit(2); });
