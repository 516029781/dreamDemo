/** N05: natural portrait/landscape behavior, no injected UI state. */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');

const ROOT = 'C:/软件/鼠鼠';
const OUT = path.join(ROOT, 'delivery/next_cycle/n4/T4');
const sha = (f) => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function canvasInfo(page) {
  return page.evaluate(() => {
    const c = document.querySelector('#GameCanvas');
    const r = c.getBoundingClientRect();
    return { width: c.width, height: c.height, css: { x: r.x, y: r.y, width: r.width, height: r.height },
      viewport: [innerWidth, innerHeight], state: window.__courtyard.state() };
  });
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1, hasTouch: true },
  });
  const records = { kind: 'N05_orientation_response', fresh_portrait: {}, resize: {}, restored: {} };
  // Fresh portrait load.
  const p1 = await browser.newPage();
  await p1.setViewport({ width: 720, height: 1280, deviceScaleFactor: 1, hasTouch: true });
  await p1.goto('http://127.0.0.1:8803/', { waitUntil: 'networkidle2', timeout: 60000 });
  await p1.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await sleep(700);
  await (await p1.$('#GameCanvas')).screenshot({ path: path.join(OUT, 'N05_fresh_portrait.png') });
  records.fresh_portrait = await canvasInfo(p1);
  records.fresh_portrait.screenshot = path.relative(ROOT, path.join(OUT, 'N05_fresh_portrait.png')).replace(/\\/g, '/');
  await p1.close();

  // Landscape load, resize to portrait, then restore landscape without injecting state.
  const p2 = await browser.newPage();
  await p2.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1, hasTouch: true });
  await p2.goto('http://127.0.0.1:8803/', { waitUntil: 'networkidle2', timeout: 60000 });
  await p2.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await sleep(500);
  await (await p2.$('#GameCanvas')).screenshot({ path: path.join(OUT, 'N05_landscape_before.png') });
  records.landscape_before = await canvasInfo(p2);
  records.landscape_before.screenshot = path.relative(ROOT, path.join(OUT, 'N05_landscape_before.png')).replace(/\\/g, '/');
  await p2.setViewport({ width: 720, height: 1280, deviceScaleFactor: 1, hasTouch: true });
  await p2.evaluate(() => window.dispatchEvent(new Event('resize')));
  await sleep(900);
  await (await p2.$('#GameCanvas')).screenshot({ path: path.join(OUT, 'N05_resize_portrait.png') });
  records.resize = await canvasInfo(p2);
  records.resize.screenshot = path.relative(ROOT, path.join(OUT, 'N05_resize_portrait.png')).replace(/\\/g, '/');
  await p2.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1, hasTouch: true });
  await p2.evaluate(() => window.dispatchEvent(new Event('resize')));
  await sleep(900);
  await (await p2.$('#GameCanvas')).screenshot({ path: path.join(OUT, 'N05_restored_landscape.png') });
  records.restored = await canvasInfo(p2);
  records.restored.screenshot = path.relative(ROOT, path.join(OUT, 'N05_restored_landscape.png')).replace(/\\/g, '/');
  await p2.close();

  const freshBlocked = records.fresh_portrait.state.viewer === 'rotate_notice' && records.fresh_portrait.state.inputLocked === true;
  const resizeBlocked = records.resize.state.viewer === 'rotate_notice' && records.resize.state.inputLocked === true;
  const restored = records.restored.state.viewer === '' && records.restored.state.inputLocked === false && records.restored.state.uiVisible === true;
  const canvasFits = records.resize.width === 720 && records.resize.height === 1280;
  records.pass = freshBlocked && resizeBlocked && restored && canvasFits;
  records.checks = { freshBlocked, resizeBlocked, restored, canvasFits };
  fs.writeFileSync(path.join(OUT, 'N05_orientation.json'), JSON.stringify(records, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ pass: records.pass, checks: records.checks, resize: { canvas: [records.resize.width, records.resize.height], viewer: records.resize.state.viewer }, restored: records.restored.state }));
  process.exit(records.pass ? 0 : 2);
})().catch((e) => { console.error('N05_FATAL', e); process.exit(2); });
