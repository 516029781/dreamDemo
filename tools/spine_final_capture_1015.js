const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const puppeteer = require('puppeteer-core');
const sharp = require('sharp');
const { GIFEncoder, quantize, applyPalette } = require('gifenc');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'art', 'phase1', 'character_playback_1015');
const RAW = path.join(OUT, 'capture_raw');
const FRAMES = path.join(OUT, 'move_frames');
const FRAMES_512 = path.join(OUT, 'move_frames_512');
const SRC_SEARCH = path.join(ROOT, 'art', 'phase1', 'reference_character', 'source_search');
const CAND = path.join(ROOT, 'reference', 'character_sources', 'ark_models', '1015_aglna2');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const ID = '1015_aglna2';
const SIZE = 1024;
const FPS = 30;
const MOVE_COUNT = 30;
const IDLE_ANIM = 'Relax';
const MOVE_ANIM = 'Move';
const IDLE_TIME = 0.5;
const KEY = [255, 0, 255];
const ALPHA_CLEAR = 32;
const ALPHA_OPAQUE = 150;
const PORT = 8174;

function keyMagenta(rgba, w, h) {
  const out = Buffer.alloc(w * h * 4);
  for (let i = 0; i < w * h; i++) {
    const o = i * 4;
    let r = rgba[o], g = rgba[o + 1], b = rgba[o + 2];
    const dist = Math.hypot(r - KEY[0], g - KEY[1], b - KEY[2]);
    let a = dist <= ALPHA_CLEAR ? 0 : dist >= ALPHA_OPAQUE ? 255 : Math.round(255 * (dist - ALPHA_CLEAR) / (ALPHA_OPAQUE - ALPHA_CLEAR));
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

async function keyedFrame(srcPath, dstPath) {
  const { data, info } = await sharp(srcPath).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const keyed = keyMagenta(data, info.width, info.height);
  await sharp(keyed, { raw: { width: info.width, height: info.height, channels: 4 } }).png().toFile(dstPath);
  let minX = info.width, minY = info.height, maxX = -1, maxY = -1, nonzero = 0;
  for (let y = 0; y < info.height; y++) for (let x = 0; x < info.width; x++) {
    const a = keyed[(y * info.width + x) * 4 + 3];
    if (a > 8) { nonzero++; if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y; }
  }
  return { path: dstPath, width: info.width, height: info.height, bbox: { left: minX, top: minY, right: maxX, bottom: maxY, width: maxX - minX + 1, height: maxY - minY + 1 }, nonzero };
}

function chromeVersion() {
  try { return fs.readdirSync('C:/Program Files/Google/Chrome/Application').filter(x => /^\d+\.\d+\.\d+\.\d+$/.test(x)).sort().pop() || 'unknown'; }
  catch { return 'unknown'; }
}
function startServer() {
  return spawn(process.execPath, [path.join(ROOT, 'tools', 'source_search', 'candidate_server.js')], { stdio: ['ignore', 'pipe', 'pipe'] });
}
async function waitHealth() {
  for (let i = 0; i < 40; i++) {
    try { const r = await fetch('http://127.0.0.1:' + PORT + '/health'); if (r.ok) return; } catch {}
    await new Promise(r => setTimeout(r, 150));
  }
  throw new Error('candidate server not healthy');
}

(async () => {
  fs.mkdirSync(RAW, { recursive: true });
  fs.mkdirSync(FRAMES, { recursive: true });
  fs.mkdirSync(FRAMES_512, { recursive: true });
  const sourceInventory = JSON.parse(fs.readFileSync(path.join(SRC_SEARCH, '1015_aglna2_inventory.json'), 'utf8'));
  const sourceFiles = sourceInventory.source_files;
  const sourceSkelSha = sourceFiles['.skel'].sha256.toLowerCase();
  const server = startServer();
  let browser;
  try {
    await waitHealth();
    browser = await puppeteer.launch({
      executablePath: CHROME,
      headless: true,
      args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
      defaultViewport: { width: SIZE, height: SIZE, deviceScaleFactor: 1 }
    });
    const page = await browser.newPage();
    const pageErrors = [];
    page.on('pageerror', err => pageErrors.push(String(err && err.stack || err)));
    page.on('requestfailed', req => pageErrors.push('request failed: ' + req.url()));
    await page.goto('http://127.0.0.1:' + PORT + '/viewer?id=' + ID + '&size=' + SIZE, { waitUntil: 'networkidle2', timeout: 30000 });
    await page.waitForFunction(() => window.__ready === true, { timeout: 30000 });
    const inventory = await page.evaluate(() => window.__inventory);
    const camera = await page.evaluate(() => {
      window.__camera.x -= 110;
      const c = window.__camera;
      const f = 0.86;
      c.scale *= f;
      c.x = 512 * (1 - f) + c.x * f;
      c.y = 512 * (1 - f) + c.y * f;
      return { ...c };
    });
    const idle = await page.evaluate(({ anim, time }) => window.__renderFixed(anim, time), { anim: IDLE_ANIM, time: IDLE_TIME });
    fs.writeFileSync(path.join(RAW, 'idle_magenta.png'), Buffer.from(idle.extract.split(',')[1], 'base64'));
    const moveDuration = inventory.animations.find(a => a.name === MOVE_ANIM).duration;
    const move = [];
    for (let i = 0; i < MOVE_COUNT; i++) {
      const time = (i / MOVE_COUNT) * moveDuration;
      const frame = await page.evaluate(({ anim, time }) => window.__renderFixed(anim, time), { anim: MOVE_ANIM, time });
      const raw = path.join(RAW, `move_${String(i).padStart(3, '0')}_magenta.png`);
      fs.writeFileSync(raw, Buffer.from(frame.extract.split(',')[1], 'base64'));
      move.push({ index: i, time, rawPath: raw });
    }
    await browser.close();
    browser = null;

    const idleKeyed = await keyedFrame(path.join(RAW, 'idle_magenta.png'), path.join(RAW, 'idle_keyed.png'));
    const moveKeyed = [];
    for (const m of move) moveKeyed.push({ ...m, ...(await keyedFrame(m.rawPath, path.join(RAW, `move_${String(m.index).padStart(3, '0')}_keyed.png`))) });
    const allBoxes = [idleKeyed.bbox, ...moveKeyed.map(x => x.bbox)];
    const union = {
      left: Math.max(0, Math.min(...allBoxes.map(b => b.left)) - 24),
      top: Math.max(0, Math.min(...allBoxes.map(b => b.top)) - 24),
      right: Math.min(SIZE - 1, Math.max(...allBoxes.map(b => b.right)) + 24),
      bottom: Math.min(SIZE - 1, Math.max(...allBoxes.map(b => b.bottom)) + 24)
    };
    union.width = union.right - union.left + 1;
    union.height = union.bottom - union.top + 1;
    const paper = { r: 232, g: 225, b: 211, alpha: 1 };
    async function cropResize(src, width, height, background) {
      let img = sharp(src).extract({ left: union.left, top: union.top, width: union.width, height: union.height }).resize(width, height, { fit: 'contain', background: background || { r: 0, g: 0, b: 0, alpha: 0 } });
      if (background) img = img.flatten({ background });
      return img.png().toBuffer();
    }
    const idlePreview = await cropResize(idleKeyed.path, 768, 768, { r: 0, g: 0, b: 0, alpha: 0 });
    fs.writeFileSync(path.join(OUT, 'idle_preview.png'), idlePreview);
    const idlePaper = await cropResize(idleKeyed.path, 768, 768, paper);
    fs.writeFileSync(path.join(OUT, 'idle_on_paper.png'), idlePaper);
    const move512 = [];
    for (let i = 0; i < moveKeyed.length; i++) {
      const transparent = await cropResize(moveKeyed[i].path, 512, 512);
      fs.writeFileSync(path.join(FRAMES_512, `frame_${String(i).padStart(3, '0')}.png`), transparent);
      const flat = await cropResize(moveKeyed[i].path, 512, 512, paper);
      fs.writeFileSync(path.join(FRAMES_512, `frame_${String(i).padStart(3, '0')}_paper.png`), flat);
      const full = await cropResize(moveKeyed[i].path, SIZE, SIZE);
      fs.writeFileSync(path.join(FRAMES, `frame_${String(i).padStart(3, '0')}.png`), full);
      move512.push(flat);
    }
    const gif = GIFEncoder();
    for (let i = 0; i < move512.length; i++) {
      const { data, info } = await sharp(move512[i]).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
      const palette = quantize(data, 256, { format: 'rgb' });
      const index = applyPalette(data, palette, 'rgb');
      gif.writeFrame(index, info.width, info.height, { palette, delay: Math.round(1000 / FPS), repeat: i === 0 ? 0 : undefined });
    }
    gif.finish();
    fs.writeFileSync(path.join(OUT, 'move_preview.gif'), Buffer.from(gif.bytes()));
    const contactIndexes = [0, 5, 10, 15, 20, 25];
    const tiles = [];
    for (let j = 0; j < contactIndexes.length; j++) {
      const buf = await sharp(move512[contactIndexes[j]]).resize(220, 220, { fit: 'contain', background: paper }).png().toBuffer();
      tiles.push({ input: buf, left: j * 220, top: 0 });
    }
    await sharp({ create: { width: contactIndexes.length * 220, height: 220, channels: 3, background: '#E8E1D3' } }).composite(tiles).png().toFile(path.join(OUT, 'move_contact.png'));

    const comparisonSrc = path.join(SRC_SEARCH, 'identity_candidate_1015_aglna2.png');
    fs.copyFileSync(comparisonSrc, path.join(OUT, 'reference_comparison.png'));

    const animations = inventory.animations.filter(a => a.duration > 0);
    const clipInventory = {
      source_skeleton_sha256: sourceSkelSha,
      source_files: {
        skeleton: sourceFiles['.skel'].source,
        atlas: sourceFiles['.atlas'].source,
        texture: sourceFiles['.png'].source
      },
      source_repository: sourceInventory.source_repository,
      source_commit: sourceInventory.source_commit,
      runtime: inventory.runtime,
      extraction_method: 'runtime_parse',
      skeleton_version: inventory.skeleton_version,
      native_size: { width: inventory.width, height: inventory.height },
      native_fps: inventory.fps,
      skins: inventory.skins,
      setup_clip: inventory.animations.find(a => a.duration === 0) || null,
      animations,
      mapping: { idle: IDLE_ANIM, move: MOVE_ANIM, interact: 'Interact' },
      bones: inventory.bones,
      slots: inventory.slots,
      render_contract: {
        capture_runtime: 'Chromium 155 + PixiJS 6.5.10 + pixi-spine 3.0.16 (Spine 3.8 runtime)',
        capture_size: [SIZE, SIZE],
        fixed_camera: camera,
        move_fps: FPS,
        move_frames: MOVE_COUNT,
        idle_time_seconds: IDLE_TIME,
        background: 'magenta #FF00FF capture matte; transparent PNG/GIF post-keyed; not part of the asset',
        source_switch_approved_by: 'user/controller 2026-10-24'
      },
      identity_check: {
        reference_frames: ['reference/_raw_screenshots/P1/t044s.jpg', 'reference/_raw_screenshots/P1/t054s.jpg', 'reference/_raw_screenshots/P1/t084s.jpg'],
        candidate_id: ID,
        observed_skin: 'default',
        source_switch_approved_by: 'user/controller 2026-10-24',
        plausible_match: true,
        h09: 'independent_review_pending_not_self_approved',
        notes: [
          '1015_aglna2 is an alter asset, not a 291_aglina skin; the user/controller approved the source switch after the identity comparison.',
          'P1 is warm-lit low-resolution video; colors are not expected to match 1:1.',
          'No AI image or replacement art was generated.'
        ]
      },
      notes: [
        'Default is a 0s setup pose and is not used as idle; idle uses Relax.',
        'Move is a real 1s loop sampled at 30fps; transparent frames are saved.',
        'No Cocos/WeChat import; not an engine capture; independent review pending.'
      ]
    };
    fs.writeFileSync(path.join(OUT, 'clip_inventory.json'), JSON.stringify(clipInventory, null, 2) + '\n');
    const log = [
      '1015_aglna2 character_playback capture log',
      'generated_at: ' + new Date().toISOString(),
      'command: node tools/spine_final_capture_1015.js',
      'node: ' + process.version,
      'chrome: ' + chromeVersion(),
      'chrome_path: ' + CHROME,
      'runtime: PixiJS 6.5.10 + pixi-spine 3.0.16 (Spine 3.8 runtime)',
      'source: reference/character_sources/ark_models/1015_aglna2 (repo isHarryh/Ark-Models e65fb914...)',
      'source_skeleton_sha256: ' + sourceSkelSha,
      'source_switch_approved_by: user/controller 2026-10-24',
      'skeleton_version: ' + inventory.skeleton_version,
      'skins: ' + JSON.stringify(inventory.skins),
      'animations: ' + JSON.stringify(inventory.animations),
      'mapping: idle=' + IDLE_ANIM + ', move=' + MOVE_ANIM,
      'camera: ' + JSON.stringify(camera),
      'idle_capture: ' + IDLE_ANIM + ' @ ' + IDLE_TIME + 's, bbox=' + JSON.stringify(idleKeyed.bbox),
      'move_capture: ' + MOVE_COUNT + ' frames @ ' + FPS + 'fps, duration=' + moveDuration + 's',
      'union_crop: ' + JSON.stringify(union),
      'outputs: idle_preview.png, move_preview.gif, move_frames/, move_frames_512/, move_contact.png, idle_on_paper.png',
      'reference_comparison: copied from source_search/identity_candidate_1015_aglna2.png; H09 independent review still pending',
      'page_errors: ' + JSON.stringify(pageErrors),
      'limits: no Cocos/WeChat import; no independent review/controller attestation; source is an alter approved by user/controller; P1 colors/video compression differ.'
    ].join('\n') + '\n';
    fs.writeFileSync(path.join(OUT, 'runtime_log.txt'), log);
    const submission = {
      character_mode: 'reference_spine',
      artifacts: [
        { role: 'clip_inventory', path: 'art/phase1/character_playback_1015/clip_inventory.json' },
        { role: 'idle_preview', path: 'art/phase1/character_playback_1015/idle_preview.png' },
        { role: 'move_preview', path: 'art/phase1/character_playback_1015/move_preview.gif' },
        { role: 'reference_comparison', path: 'art/phase1/character_playback_1015/reference_comparison.png' },
        { role: 'runtime_log', path: 'art/phase1/character_playback_1015/runtime_log.txt' }
      ],
      production_methods: ['reference_spine']
    };
    fs.writeFileSync(path.join(OUT, 'submission_character_playback.json'), JSON.stringify(submission, null, 2) + '\n');
    fs.writeFileSync(path.join(OUT, 'capture_summary.json'), JSON.stringify({ inventory, camera, union, idleKeyed, moveKeyed, pageErrors }, null, 2) + '\n');
    console.log(JSON.stringify({ ok: true, sourceSkelSha, camera, union, idle: idleKeyed.bbox, frames: moveKeyed.length, pageErrors }, null, 2));
  } finally {
    if (browser) await browser.close().catch(() => {});
    server.kill();
  }
})();
