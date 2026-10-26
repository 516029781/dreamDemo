// Runtime-parse and capture a downloaded Ark-Models candidate with the local
// pixi-spine 3.0.16 (Spine 3.8 runtime) build. No AI generation is involved.
// Usage: node tools/source_search/capture_candidate.js 291_aglina_boc1
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const ROOT = path.resolve(__dirname, '..', '..');
const NM = path.join(ROOT, '.tooling', 'node_modules');
const puppeteer = require(path.join(NM, 'puppeteer-core'));
const sharp = require(path.join(NM, 'sharp'));

const ID = process.argv[2] || '291_aglina_boc1';
const OUT = path.join(ROOT, 'art', 'phase1', 'reference_character', 'source_search');
const RAW = path.join(OUT, 'capture_raw');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = 8174;
const SIZE = 1024;
const pixiVersion = JSON.parse(fs.readFileSync(path.join(NM, 'pixi.js', 'package.json'), 'utf8')).version;
const spineVersion = JSON.parse(fs.readFileSync(path.join(NM, 'pixi-spine', 'package.json'), 'utf8')).version;
const KEY = [255, 0, 255];

function keyMagenta(rgba, w, h) {
  const out = Buffer.alloc(w * h * 4);
  for (let i = 0; i < w * h; i++) {
    const o = i * 4;
    let r = rgba[o], g = rgba[o + 1], b = rgba[o + 2];
    const dist = Math.hypot(r - KEY[0], g - KEY[1], b - KEY[2]);
    let a;
    if (dist <= 32) a = 0;
    else if (dist >= 150) a = 255;
    else a = Math.round(255 * (dist - 32) / (150 - 32));
    if (a > 0) {
      const spill = Math.min(r, b) - g;
      if (spill > 8 && dist < 240 && a < 250) {
        const cut = Math.min(spill * 0.55, 72);
        r = Math.max(0, r - cut);
        b = Math.max(0, b - cut);
      }
    }
    out[o] = r; out[o + 1] = g; out[o + 2] = b; out[o + 3] = a;
  }
  return out;
}

async function keyed(srcPath, dstPath) {
  const { data, info } = await sharp(srcPath).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const keyedData = keyMagenta(data, info.width, info.height);
  await sharp(keyedData, { raw: { width: info.width, height: info.height, channels: 4 } }).png().toFile(dstPath);
  let minX = info.width, minY = info.height, maxX = -1, maxY = -1, nonzero = 0;
  for (let y = 0; y < info.height; y++) {
    for (let x = 0; x < info.width; x++) {
      const a = keyedData[(y * info.width + x) * 4 + 3];
      if (a > 8) {
        nonzero++;
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }
  return { path: dstPath, width: info.width, height: info.height, bbox: { left: minX, top: minY, right: maxX, bottom: maxY, width: maxX - minX + 1, height: maxY - minY + 1 }, nonzero };
}

function startServer() {
  const child = spawn(process.execPath, [path.join(__dirname, 'candidate_server.js')], { stdio: ['ignore', 'pipe', 'pipe'] });
  child.stdout.on('data', d => process.stdout.write('[server] ' + d));
  child.stderr.on('data', d => process.stderr.write('[server-err] ' + d));
  return child;
}

async function waitHealth() {
  for (let i = 0; i < 40; i++) {
    try {
      const r = await fetch('http://127.0.0.1:' + PORT + '/health');
      if (r.ok) return true;
    } catch {}
    await new Promise(r => setTimeout(r, 150));
  }
  throw new Error('candidate server did not become healthy');
}

(async () => {
  fs.mkdirSync(RAW, { recursive: true });
  const server = startServer();
  try {
    await waitHealth();
    const browser = await puppeteer.launch({
      executablePath: CHROME,
      headless: true,
      args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
      defaultViewport: { width: SIZE, height: SIZE, deviceScaleFactor: 1 }
    });
    const page = await browser.newPage();
    const pageErrors = [];
    page.on('pageerror', err => pageErrors.push(String(err && err.stack || err)));
    page.on('requestfailed', req => pageErrors.push('request failed: ' + req.url()));
    await page.goto('http://127.0.0.1:' + PORT + '/viewer?id=' + encodeURIComponent(ID) + '&size=' + SIZE, { waitUntil: 'networkidle2', timeout: 30000 });
    await page.waitForFunction(() => window.__ready === true || document.title === 'ERROR', { timeout: 30000 });
    const title = await page.title();
    if (title !== 'DONE') {
      const logs = await page.evaluate(() => window.__logs || '');
      throw new Error('viewer did not finish: ' + title + '\n' + logs);
    }
    const inventory = await page.evaluate(() => window.__inventory);
    const logs = await page.evaluate(() => window.__logs || '');
    const camera = await page.evaluate(() => window.__camera);

    const samples = [];
    const wanted = [
      { anim: null, time: 0, label: 'setup' },
      { anim: 'Relax', time: 0.5, label: 'relax_0p5' },
      { anim: 'Move', time: 0.25, label: 'move_0p25' },
      { anim: 'Move', time: 0.75, label: 'move_0p75' }
    ];
    const have = new Set(inventory.animations.map(a => a.name));
    for (const w of wanted) {
      if (w.anim && !have.has(w.anim)) continue;
      const frame = await page.evaluate(({ anim, time }) => window.__renderFixed(anim, time), { anim: w.anim, time: w.time });
      const rawPath = path.join(RAW, ID + '_' + w.label + '_magenta.png');
      fs.writeFileSync(rawPath, Buffer.from(frame.extract.split(',')[1], 'base64'));
      samples.push({ ...w, rawPath });
    }

    // 12-frame Move strip if Move exists.
    let moveStrip = null;
    const move = inventory.animations.find(a => a.name === 'Move');
    if (move) {
      const frames = 12;
      const tiles = [];
      for (let i = 0; i < frames; i++) {
        const time = (i / frames) * move.duration;
        const frame = await page.evaluate(({ anim, time }) => window.__renderFixed(anim, time), { anim: 'Move', time });
        const rawPath = path.join(RAW, ID + '_move_' + String(i).padStart(2, '0') + '_magenta.png');
        fs.writeFileSync(rawPath, Buffer.from(frame.extract.split(',')[1], 'base64'));
        const k = await keyed(rawPath, path.join(RAW, ID + '_move_' + String(i).padStart(2, '0') + '_keyed.png'));
        const cx = Math.max(0, k.bbox.left - 8);
        const cy = Math.max(0, k.bbox.top - 8);
        const cw = Math.min(SIZE - cx, k.bbox.width + 16);
        const ch = Math.min(SIZE - cy, k.bbox.height + 16);
        const buf = await sharp(k.path).extract({ left: cx, top: cy, width: cw, height: ch })
          .resize(200, 200, { fit: 'contain', background: { r: 232, g: 225, b: 211, alpha: 1 } }).flatten({ background: { r: 232, g: 225, b: 211 } }).png().toBuffer();
        tiles.push({ input: buf, left: i * 200, top: 0 });
      }
      moveStrip = path.join(OUT, ID + '_move_strip.png');
      await sharp({ create: { width: frames * 200, height: 200, channels: 3, background: '#E8E1D3' } }).composite(tiles).png().toFile(moveStrip);
    }
    await browser.close();

    const keyedSamples = [];
    for (const s of samples) {
      const k = await keyed(s.rawPath, path.join(OUT, ID + '_' + s.label + '.png'));
      keyedSamples.push({ anim: s.anim, time: s.time, label: s.label, ...k, raw: path.relative(ROOT, s.rawPath).replace(/\\/g, '/') });
    }

    const sourceManifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'tools', 'source_search', 'work', ID, 'runtime_copy_manifest.json'), 'utf8'));
    const inventoryOut = {
      candidate_id: ID,
      source_repository: sourceManifest.repository,
      source_commit: sourceManifest.commit,
      source_files: sourceManifest.files,
      source_skeleton_version_header: sourceManifest.skeleton_version,
      extraction_method: 'runtime_parse',
      runtime: inventory.runtime,
      skeleton_version: inventory.skeleton_version,
      native_size: { width: inventory.width, height: inventory.height },
      native_fps: inventory.fps,
      skins: inventory.skins,
      animations: inventory.animations,
      setup_clip: inventory.animations.find(a => a.duration === 0) || null,
      bones_count: inventory.bones.length,
      slots_count: inventory.slots.length,
      bones: inventory.bones,
      slots: inventory.slots,
      camera,
      rendered_samples: keyedSamples,
      move_strip: moveStrip ? path.relative(ROOT, moveStrip).replace(/\\/g, '/') : null,
      notes: [
        'runtime parse via pixi-spine 3.0.16 in Chromium headless (WebGL2/SwiftShader)',
        'transparent PNGs are deterministic magenta-key previews, not the source asset',
        'skin identity vs P1 is judged visually; names alone are not evidence'
      ]
    };
    fs.writeFileSync(path.join(OUT, ID + '_inventory.json'), JSON.stringify(inventoryOut, null, 2) + '\n');
    const log = [
      ID + ' candidate runtime log',
      'generated_at: ' + new Date().toISOString(),
      'command: node tools/source_search/capture_candidate.js ' + ID,
      'node: ' + process.version,
      'chrome: ' + CHROME,
      'server: http://127.0.0.1:' + PORT + '/viewer?id=' + ID,
      'runtime: PixiJS ' + pixiVersion + ' + pixi-spine ' + spineVersion + ' (Spine 3.8 runtime)',
      'skeleton_version: ' + inventory.skeleton_version,
      'skins: ' + JSON.stringify(inventory.skins),
      'animations: ' + JSON.stringify(inventory.animations),
      'source sha256: ' + JSON.stringify(Object.fromEntries(Object.entries(sourceManifest.files).map(([k, v]) => [k, v.sha256]))),
      'source git blob sha1: ' + JSON.stringify(Object.fromEntries(Object.entries(sourceManifest.files).map(([k, v]) => [k, v.git_blob_sha1]))),
      'camera: ' + JSON.stringify(camera),
      'page_errors: ' + JSON.stringify(pageErrors),
      'viewer_log:',
      logs.trim(),
      'limits: preview render only; no Cocos/WeChat import; no H09/H05 approval claimed.'
    ].join('\n') + '\n';
    fs.writeFileSync(path.join(OUT, ID + '_runtime_log.txt'), log);
    console.log(JSON.stringify({ ok: true, id: ID, version: inventory.skeleton_version, skins: inventory.skins, animations: inventory.animations, samples: keyedSamples.map(s => ({ label: s.label, bbox: s.bbox, nonzero: s.nonzero })), pageErrors }, null, 2));
  } finally {
    server.kill();
  }
})();
