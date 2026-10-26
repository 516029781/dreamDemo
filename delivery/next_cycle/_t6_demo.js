/** T6 current-build demo GIF: move the player with a keyboard path, real canvas frames. */
const path = require('path');
const fs = require('fs');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const sharp = req('sharp');
const { GIFEncoder, quantize, applyPalette } = req('gifenc');
const { captureCanvas } = require('../../tools/capture/canvas_capture.js');

const ROOT = 'C:/软件/鼠鼠';
const OUT = path.join(ROOT, 'delivery/next_cycle/T6');
const FRAME_DIR = path.join(OUT, 'demo_frames');

(async () => {
  fs.mkdirSync(FRAME_DIR, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto('http://127.0.0.1:8801/', { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await page.evaluate(() => { window.__courtyard.reset(); window.__courtyard.closeDialogue(); window.__courtyard.setUi(false); });
  await new Promise((r) => setTimeout(r, 900));
  await page.click('#GameCanvas');
  const frames = [];
  await page.keyboard.down('KeyD');
  for (let i = 0; i < 16; i++) {
    await new Promise((r) => setTimeout(r, 110));
    const file = path.join(FRAME_DIR, `demo_${String(i).padStart(3, '0')}.png`);
    await captureCanvas(page, file, { hideStats: true });
    frames.push(file);
  }
  await page.keyboard.up('KeyD');
  const state = await page.evaluate(() => window.__courtyard.state());
  const gif = GIFEncoder();
  const W = 640, H = 360;
  for (let i = 0; i < frames.length; i++) {
    const rgba = await sharp(frames[i]).resize(W, H).ensureAlpha().raw().toBuffer();
    const pal = quantize(rgba, 256, { format: 'rgb' });
    const idx = applyPalette(rgba, pal, 'rgb');
    gif.writeFrame(idx, W, H, { palette: pal, delay: 110, repeat: i === 0 ? 0 : undefined });
  }
  gif.finish();
  const out = path.join(OUT, 'demo_current.gif');
  fs.writeFileSync(out, Buffer.from(gif.bytes()));
  fs.writeFileSync(path.join(OUT, 'demo_current.json'), JSON.stringify({ frames: frames.length, state, page_errors: errors, gif: path.relative(ROOT, out).replace(/\\/g, '/') }, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ frames: frames.length, errors: errors.length, player: state.player }));
  process.exit(errors.length ? 1 : 0);
})().catch((e) => { console.error('DEMO_FATAL', e); process.exit(2); });
