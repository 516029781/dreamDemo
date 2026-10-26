/** N07: record real idle/move runtime frames and GIFs (500ms cadence). */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const sharp = req('sharp');
const { GIFEncoder, quantize, applyPalette } = req('gifenc');
const { captureCanvas } = require('../../../tools/capture/canvas_capture.js');

const ROOT = 'C:/软件/鼠鼠';
const OUT = path.join(ROOT, 'delivery/next_cycle/n4/T6/character_n');
const sha = (f) => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function skstate(page) {
  return page.evaluate(() => {
    const n = cc.director.getScene().getChildByName('CharRTCanvas')?.getChildByName('PlayerSpineRT');
    const sk = (n?.getComponents(cc.Component) || []).find((c) => typeof c.setAnimation === 'function');
    let current = null;
    try { const t = sk?.getCurrent(0); current = t ? { animation: t.animation?.name, trackTime: t.trackTime } : null; } catch (e) { current = { error: String(e) }; }
    return { found: !!sk, current, bones: sk?._skeleton?.bones?.slice(0, 5).map((b) => ({ x: b.worldX, y: b.worldY })) };
  });
}

async function gifFor(frames, out) {
  const gif = GIFEncoder();
  const W = 640, H = 360;
  for (let i = 0; i < frames.length; i++) {
    const rgba = await sharp(frames[i]).resize(W, H).ensureAlpha().raw().toBuffer();
    const pal = quantize(rgba, 256, { format: 'rgb' });
    const idx = applyPalette(rgba, pal, 'rgb');
    gif.writeFrame(idx, W, H, { palette: pal, delay: 500, repeat: i === 0 ? 0 : undefined });
  }
  gif.finish();
  fs.writeFileSync(out, Buffer.from(gif.bytes()));
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto('http://127.0.0.1:8803/', { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await page.evaluate(() => { window.__courtyard.reset(); window.__courtyard.closeDialogue(); window.__courtyard.setUi(false); window.__courtyard.setMoving(false); });
  await sleep(1000);
  const capture = async (tag, count = 6) => {
    const frames = [], states = [], hashes = [];
    for (let i = 0; i < count; i++) {
      const file = path.join(OUT, `${tag}_${String(i).padStart(2, '0')}.png`);
      await captureCanvas(page, file, { hideStats: true });
      frames.push(file); hashes.push(sha(file)); states.push(await skstate(page));
      await sleep(500);
    }
    return { frames, states, hashes, unique: new Set(hashes).size };
  };
  const idle = await capture('idle');
  await page.evaluate(() => window.__courtyard.setMoving(true));
  await sleep(300);
  const move = await capture('move');
  await gifFor(idle.frames, path.join(OUT, 'char_idle.gif'));
  await gifFor(move.frames, path.join(OUT, 'char_move.gif'));
  const report = {
    kind: 'N07_runtime_animation',
    method: 'element canvas capture every 500ms; Spine trackTime/bones recorded; no Spine rebuild',
    idle: { unique_frames: idle.unique, hashes: idle.hashes, states: idle.states, gif: 'delivery/next_cycle/T6/character_n/char_idle.gif', gif_sha256: sha(path.join(OUT, 'char_idle.gif')) },
    move: { unique_frames: move.unique, hashes: move.hashes, states: move.states, gif: 'delivery/next_cycle/T6/character_n/char_move.gif', gif_sha256: sha(path.join(OUT, 'char_move.gif')) },
    page_errors: errors,
    pass: idle.unique > 1 && move.unique > 1 && sha(path.join(OUT, 'char_idle.gif')) !== sha(path.join(OUT, 'char_move.gif')),
  };
  fs.writeFileSync(path.join(OUT, 'N07_animation.json'), JSON.stringify(report, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ pass: report.pass, idle_unique: idle.unique, move_unique: move.unique, errors: errors.length, idle_track: idle.states.map(s => s.current?.trackTime), move_track: move.states.map(s => s.current?.trackTime) }));
  process.exit(report.pass ? 0 : 2);
})().catch((e) => { console.error('N07_FATAL', e); process.exit(2); });
