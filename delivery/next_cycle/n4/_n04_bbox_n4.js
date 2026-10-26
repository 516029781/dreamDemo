/** N04: real character alpha/render-diff bbox; target recheck evidence. */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const sharp = req('sharp');
const { captureCanvas } = require('../../../tools/capture/canvas_capture.js');

const ROOT = 'C:/软件/鼠鼠';
const OUT = path.join(ROOT, 'delivery/next_cycle/n4/T4');
const sha = (f) => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  await page.goto('http://127.0.0.1:8803/', { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await page.evaluate(() => { window.__courtyard.reset(); window.__courtyard.closeDialogue(); window.__courtyard.setUi(false); });
  await new Promise((r) => setTimeout(r, 800));
  const visible = path.join(OUT, 'N04_actor_visible.png');
  await captureCanvas(page, visible, { hideStats: true });
  const found = await page.evaluate(() => {
    const walk = (n) => { if (n.name === 'PlayerWorldQuad') return n; for (const c of n.children) { const r = walk(c); if (r) return r; } return null; };
    const n = walk(cc.director.getScene()); if (n) n.active = false; return !!n;
  });
  await new Promise((r) => setTimeout(r, 300));
  const hidden = path.join(OUT, 'N04_actor_hidden.png');
  await captureCanvas(page, hidden, { hideStats: true });
  const a = await sharp(visible).raw().toBuffer({ resolveWithObject: true });
  const b = await sharp(hidden).raw().toBuffer({ resolveWithObject: true });
  let minX = 1e9, minY = 1e9, maxX = -1, maxY = -1, changed = 0;
  for (let y = 0; y < a.info.height; y++) {
    for (let x = 0; x < a.info.width; x++) {
      const i = (y * a.info.width + x) * a.info.channels;
      const d = Math.max(Math.abs(a.data[i] - b.data[i]), Math.abs(a.data[i + 1] - b.data[i + 1]), Math.abs(a.data[i + 2] - b.data[i + 2]));
      if (d > 12) { changed++; minX = Math.min(minX, x); minY = Math.min(minY, y); maxX = Math.max(maxX, x); maxY = Math.max(maxY, y); }
    }
  }
  const report = {
    kind: 'N04_real_character_bbox',
    method: 'visible minus hidden PlayerWorldQuad, same frame/camera/UI hidden, RGB max-delta > 12',
    found_player_quad: found,
    bbox: changed ? { left: minX, top: minY, right: maxX, bottom: maxY, width: maxX - minX + 1, height: maxY - minY + 1 } : null,
    changed_pixels: changed,
    target_px: [86, 130],
    target_recheck: {
      method: 'P1 t084 native 1920x1078, connected non-paving character component, scaled to 720p',
      approx_character_height_720p: 107.5,
      conclusion: '86-130px target is consistent with P1 reference; do not scale the Spine asset. Camera FOV calibrated to 37.5 for composition.',
    },
    visible: { path: path.relative(ROOT, visible).replace(/\\/g, '/'), sha256: sha(visible) },
    hidden: { path: path.relative(ROOT, hidden).replace(/\\/g, '/'), sha256: sha(hidden) },
    pass: changed > 1000 && maxY - minY + 1 >= 86 && maxY - minY + 1 <= 130,
  };
  fs.writeFileSync(path.join(OUT, 'N04_bbox.json'), JSON.stringify(report, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ bbox: report.bbox, pass: report.pass }));
  process.exit(report.pass ? 0 : 2);
})().catch((e) => { console.error('N04_FATAL', e); process.exit(2); });
