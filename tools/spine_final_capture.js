const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');
const sharp = require('sharp');
const { GIFEncoder, quantize, applyPalette } = require('gifenc');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'art', 'phase1', 'reference_character');
const RAW = path.join(OUT, 'capture_raw');
const FRAMES = path.join(OUT, 'move_frames');
const FRAMES_512 = path.join(OUT, 'move_frames_512');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const SIZE = 1024;
const FPS = 30;
const MOVE_COUNT = 30;
const IDLE_ANIM = 'Relax';
const MOVE_ANIM = 'Move';
const IDLE_TIME = 0.5;
const KEY = [255, 0, 255];
const ALPHA_CLEAR = 32;
const ALPHA_OPAQUE = 150;

function chromeVersion() {
  try {
    return fs.readdirSync('C:/Program Files/Google/Chrome/Application').filter(x => /^d+.d+.d+.d+$/.test(x)).sort().pop() || 'unknown';
  } catch { return 'unknown'; }
}

function keyMagenta(rgba, w, h) {
  const out = Buffer.alloc(w * h * 4);
  for (let i = 0; i < w * h; i++) {
    const o = i * 4;
    let r = rgba[o], g = rgba[o + 1], b = rgba[o + 2];
    const dist = Math.hypot(r - KEY[0], g - KEY[1], b - KEY[2]);
    let a;
    if (dist <= ALPHA_CLEAR) a = 0;
    else if (dist >= ALPHA_OPAQUE) a = 255;
    else a = Math.round(255 * (dist - ALPHA_CLEAR) / (ALPHA_OPAQUE - ALPHA_CLEAR));
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
  for (let y = 0; y < info.height; y++) {
    for (let x = 0; x < info.width; x++) {
      const a = keyed[(y * info.width + x) * 4 + 3];
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

(async () => {
  fs.mkdirSync(RAW, { recursive: true });
  fs.mkdirSync(FRAMES, { recursive: true });
  fs.mkdirSync(FRAMES_512, { recursive: true });

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
  await page.goto(`http://127.0.0.1:8173/viewer?size=${SIZE}`, { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForFunction(() => window.__ready === true, { timeout: 30000 });
  await new Promise(resolve => setTimeout(resolve, 300));

  const inventory = await page.evaluate(() => window.__inventory);
  const camera = await page.evaluate(() => window.__setFixedCamera());
  const idle = await page.evaluate(({ anim, time }) => window.__renderFixed(anim, time), { anim: IDLE_ANIM, time: IDLE_TIME });
  const move = [];
  const moveDuration = inventory.animations.find(a => a.name === MOVE_ANIM).duration;
  const roots = [];
  for (let i = 0; i < MOVE_COUNT; i++) {
    const time = (i / MOVE_COUNT) * moveDuration;
    const frame = await page.evaluate(({ anim, time }) => window.__renderFixed(anim, time), { anim: MOVE_ANIM, time });
    const rawPath = path.join(RAW, `move_${String(i).padStart(3, '0')}_magenta.png`);
    fs.writeFileSync(rawPath, Buffer.from(frame.extract.split(',')[1], 'base64'));
    move.push({ index: i, time, rawPath, root: frame.root });
    roots.push({ index: i, time, root: frame.root });
  }
  const idleRaw = path.join(RAW, 'idle_magenta.png');
  fs.writeFileSync(idleRaw, Buffer.from(idle.extract.split(',')[1], 'base64'));
  await browser.close();

  const idleKeyed = await keyedFrame(idleRaw, path.join(OUT, 'idle_keyed_full.png'));
  const moveKeyed = [];
  for (const item of move) {
    const keyed = await keyedFrame(item.rawPath, path.join(RAW, `move_${String(item.index).padStart(3, '0')}_keyed.png`));
    moveKeyed.push({ ...item, ...keyed });
  }

  const allBoxes = [idleKeyed.bbox, ...moveKeyed.map(x => x.bbox)];
  const union = {
    left: Math.max(0, Math.min(...allBoxes.map(b => b.left)) - 24),
    top: Math.max(0, Math.min(...allBoxes.map(b => b.top)) - 24),
    right: Math.min(SIZE - 1, Math.max(...allBoxes.map(b => b.right)) + 24),
    bottom: Math.min(SIZE - 1, Math.max(...allBoxes.map(b => b.bottom)) + 24)
  };
  union.width = union.right - union.left + 1;
  union.height = union.bottom - union.top + 1;

  async function cropResize(src, width, height, background) {
    let img = sharp(src).extract({ left: union.left, top: union.top, width: union.width, height: union.height }).resize(width, height, { fit: 'contain', background: background || { r: 0, g: 0, b: 0, alpha: 0 } });
    if (background) img = img.flatten({ background });
    return img.png().toBuffer();
  }

  const idlePreview = await cropResize(idleKeyed.path, 768, 768, { r: 0, g: 0, b: 0, alpha: 0 });
  fs.writeFileSync(path.join(OUT, 'idle_preview.png'), idlePreview);
  const paper = { r: 232, g: 225, b: 211, alpha: 1 };
  const idlePaper = await cropResize(idleKeyed.path, 768, 768, paper);
  fs.writeFileSync(path.join(OUT, 'idle_on_paper.png'), idlePaper);

  const move512 = [];
  for (let i = 0; i < moveKeyed.length; i++) {
    const src = moveKeyed[i].path;
    const transparent = await cropResize(src, 512, 512);
    fs.writeFileSync(path.join(FRAMES_512, `frame_${String(i).padStart(3, '0')}.png`), transparent);
    const flat = await cropResize(src, 512, 512, paper);
    fs.writeFileSync(path.join(FRAMES_512, `frame_${String(i).padStart(3, '0')}_paper.png`), flat);
    move512.push(flat);
  }
  const fullFrames = [];
  for (let i = 0; i < moveKeyed.length; i++) {
    const transparent = await cropResize(moveKeyed[i].path, SIZE, SIZE);
    fs.writeFileSync(path.join(FRAMES, `frame_${String(i).padStart(3, '0')}.png`), transparent);
    fullFrames.push(transparent);
  }

  const gif = GIFEncoder();
  for (let i = 0; i < move512.length; i++) {
    const { data, info } = await sharp(move512[i]).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
    const palette = quantize(data, 256, { format: 'rgb' });
    const index = applyPalette(data, palette, 'rgb');
    gif.writeFrame(index, info.width, info.height, { palette, delay: Math.round(1000 / FPS), repeat: i === 0 ? 0 : undefined });
  }
  gif.finish();
  const gifPath = path.join(OUT, 'move_preview.gif');
  fs.writeFileSync(gifPath, Buffer.from(gif.bytes()));

  const contactIndexes = [0, 5, 10, 15, 20, 25];
  const contactTiles = [];
  for (let j = 0; j < contactIndexes.length; j++) {
    const buf = await sharp(move512[contactIndexes[j]]).resize(220, 220, { fit: 'contain', background: paper }).png().toBuffer();
    contactTiles.push({ input: buf, left: j * 220, top: 0 });
  }
  await sharp({ create: { width: contactIndexes.length * 220, height: 220, channels: 3, background: '#E8E1D3' } })
    .composite(contactTiles).png().toFile(path.join(OUT, 'move_contact.png'));

  const animations = inventory.animations.filter(a => a.duration > 0);
  const clipInventory = {
    source_skeleton_sha256: inventory.source_skeleton_sha256,
    source_files: inventory.source_files,
    runtime: inventory.runtime,
    extraction_method: 'runtime_parse',
    skeleton_version: inventory.skeleton_version,
    native_fps: inventory.fps,
    native_size: { width: inventory.width, height: inventory.height },
    skins: inventory.skins,
    setup_clip: inventory.animations.find(a => a.duration === 0) || null,
    animations,
    mapping: { idle: IDLE_ANIM, move: MOVE_ANIM, interact: 'Interact' },
    bones: inventory.bones,
    slots: inventory.slots,
    render_contract: {
      capture_runtime: 'Chromium headless + PixiJS 6.5.10 + pixi-spine 3.0.16 (Spine 3.8 runtime)',
      capture_size: [SIZE, SIZE],
      fixed_camera: camera,
      move_fps: FPS,
      move_frames: MOVE_COUNT,
      idle_time_seconds: IDLE_TIME,
      background: 'magenta #FF00FF capture matte; transparent PNG/GIF produced by deterministic key + despill',
      foot_baseline_note: '固定机位按 setup bounds 居中；Move 帧不重新缩放，保留真实骨骼运动'
    },
    identity_check: {
      reference_frames: ['reference/_raw_screenshots/P1/t044s.jpg', 'reference/_raw_screenshots/P1/t084s.jpg'],
      observed_skin: 'default',
      same_character_id_candidate: true,
      same_skin_as_p1: false,
      h09: 'fail_candidate_only',
      differences: [
        'P1 t044/t084 是红黑制服与大型红黑武器；291 default 是白色长外套、黑色内搭和黑白长枪。',
        'P1 发色偏红粉；291 default 发色偏灰褐。',
        '红发带、兽耳和 Q 版比例相近，但服装/装备不是同一皮肤。'
      ],
      action: '需控制器提供/批准与 P1 匹配的 skin 资源，或书面更新来源合同；不得生成新造型替代。'
    },
    notes: [
      'Default 是 0 秒 setup pose，不作为 idle 播放；idle 采用经实际查看的 Relax。',
      'Move 为真实 1 秒循环；30 帧按 30fps 采样，输出 GIF 与透明帧。',
      '未做 Cocos 引擎导入；本阶段仅为角色播放证据。'
    ]
  };
  fs.writeFileSync(path.join(OUT, 'clip_inventory.json'), JSON.stringify(clipInventory, null, 2) + '\n');

  const version = chromeVersion();
  const nodeVersion = process.version;
  const log = [
    '291_aglina character_playback capture log',
    'generated_at: ' + new Date().toISOString(),
    'command: node tools/spine_final_capture.js',
    'node: ' + nodeVersion,
    'chrome: ' + version,
    'chrome_path: ' + CHROME,
    'runtime: PixiJS 6.5.10 + pixi-spine 3.0.16 (Spine 3.8 runtime)',
    'renderer: WebGL2 / ANGLE SwiftShader (headless Chromium)',
    'source_skeleton_sha256: ' + inventory.source_skeleton_sha256,
    'skeleton_version: ' + inventory.skeleton_version,
    'skins: ' + JSON.stringify(inventory.skins),
    'animations: ' + JSON.stringify(inventory.animations),
    'mapping: idle=' + IDLE_ANIM + ', move=' + MOVE_ANIM,
    'camera: ' + JSON.stringify(camera),
    'idle_capture: ' + IDLE_ANIM + ' @ ' + IDLE_TIME + 's, keyed alpha=' + JSON.stringify(idleKeyed.bbox),
    'move_capture: ' + MOVE_COUNT + ' frames @ ' + FPS + 'fps, duration=' + moveDuration + 's',
    'union_crop: ' + JSON.stringify(union),
    'outputs:',
    '  idle_preview.png (768x768 RGBA, alpha keyed)',
    '  move_preview.gif (512x512, 30 frames, loop)',
    '  move_frames/frame_000..029.png (1024x1024 RGBA)',
    '  move_frames_512/frame_000..029.png (512x512 RGBA)',
    '  move_contact.png, idle_on_paper.png',
    '  clip_inventory.json',
    'page_errors: ' + JSON.stringify(pageErrors),
    'identity: DEFAULT SKIN MISMATCH vs P1 t044/t084 -> H09 fail candidate; controller must approve a matching skin or update source contract. No replacement art was generated.',
    'limits: no Cocos import, no engine scene, no full-art approval; capture matte is not part of the asset; fixed camera is a preview contract.'
  ].join('\n') + '\n';
  fs.writeFileSync(path.join(OUT, 'runtime_log.txt'), log);

  const submission = {
    character_mode: 'reference_spine',
    artifacts: [
      { role: 'clip_inventory', path: 'art/phase1/reference_character/clip_inventory.json' },
      { role: 'idle_preview', path: 'art/phase1/reference_character/idle_preview.png' },
      { role: 'move_preview', path: 'art/phase1/reference_character/move_preview.gif' },
      { role: 'reference_comparison', path: 'art/phase1/reference_character/reference_comparison.png' },
      { role: 'runtime_log', path: 'art/phase1/reference_character/runtime_log.txt' }
    ],
    production_methods: ['reference_spine']
  };
  fs.writeFileSync(path.join(OUT, 'submission_character_playback.json'), JSON.stringify(submission, null, 2) + '\n');

  fs.writeFileSync(path.join(OUT, 'capture_summary.json'), JSON.stringify({
    inventory, camera, union, idleKeyed, moveKeyed, roots, gifPath, idlePreviewBytes: idlePreview.length, pageErrors
  }, null, 2) + '\n');
  console.log(JSON.stringify({ ok: true, camera, union, idle: idleKeyed.bbox, frames: moveKeyed.length, gif: gifPath, errors: pageErrors }, null, 2));
})();
