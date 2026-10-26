/** T6: batch current-build UI states, asset previews and character idle/move frames. */
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const sharp = req('sharp');
const { GIFEncoder, quantize, applyPalette } = req('gifenc');
const { captureCanvas } = require('../../../tools/capture/canvas_capture.js');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://127.0.0.1:8803/';
const ROOT = 'C:/软件/鼠鼠';
const OUT = path.join(ROOT, 'delivery/next_cycle/n4/T6');
const UI_OUT = path.join(OUT, 'ui_states');
const ASSET_OUT = path.join(OUT, 'assets');
const CHAR_OUT = path.join(OUT, 'character');

const UI_STATES = [
  'spec_type', 'spec_nine_slice', 'spec_icons',
  'title_initial', 'title_pressed', 'title_loading',
  'loading_progress', 'loading_failure', 'loading_retry_pressed',
  'hud_talk', 'hud_0_3', 'hud_1_3', 'hud_2_3', 'hud_3_3', 'hud_submit', 'hud_done',
  'interact_talk', 'interact_pick', 'interact_place', 'interact_view', 'interact_pressed', 'interact_disabled', 'interact_hidden',
  'joystick_idle', 'joystick_drag', 'joystick_hidden',
  'dialogue_gardener_p1', 'dialogue_player_p2', 'dialogue_accept_pressed',
  'pause_default', 'pause_sound_on', 'pause_restart_pressed',
  'complete_default', 'complete_continue_pressed',
  'toast_pickup', 'toast_task_update', 'toast_error',
  'tip_first_move', 'tip_first_interact',
  'safe_area_landscape', 'rotate_notice',
];
const ASSET_IDS = [
  'MAP001', 'ENV001', 'ENV002', 'ENV003', 'ENV004', 'ENV005', 'ENV006', 'ENV007',
  'ENV008', 'ENV009', 'ENV010', 'ENV011', 'ENV012',
  'PROP001', 'PROP002', 'PROP003', 'PROP004', 'PROP005', 'PROP006',
  'MAT001', 'MAT002', 'MAT003', 'MAT004', 'MAT005', 'LOOK001',
  'CHAR001', 'CHAR002', 'CHAR003', 'CHAR004', 'CHAR005',
  'FX001', 'FX002', 'FX003', 'PACK001',
];
const sha = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const rel = (file) => path.relative(ROOT, file).replace(/\\/g, '/');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  for (const dir of [UI_OUT, ASSET_OUT, CHAR_OUT]) fs.mkdirSync(dir, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  const logs = [];
  const errors = [];
  page.on('console', (m) => logs.push('CONSOLE ' + m.type() + ' ' + m.text()));
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });

  const ui = [];
  for (const id of UI_STATES) {
    await page.evaluate(() => window.__courtyard.resetView());
    await sleep(100);
    await page.evaluate((state) => window.__courtyard.setUiState(state), id);
    await sleep(300);
    const meta = await captureCanvas(page, path.join(UI_OUT, id + '.png'), { hideStats: true });
    ui.push({ id, path: rel(path.join(UI_OUT, id + '.png')), sha256: meta.output.sha256, canvas: [meta.backing_width, meta.backing_height] });
  }

  const assets = [];
  for (const id of ASSET_IDS) {
    await page.evaluate(() => window.__courtyard.resetView());
    await sleep(120);
    await page.evaluate((asset) => window.__courtyard.focusAsset(asset), id);
    await sleep(550);
    const meta = await captureCanvas(page, path.join(ASSET_OUT, id + '.png'), { hideStats: true });
    assets.push({ id, path: rel(path.join(ASSET_OUT, id + '.png')), sha256: meta.output.sha256, canvas: [meta.backing_width, meta.backing_height] });
  }

  await page.evaluate(() => { window.__courtyard.reset(); window.__courtyard.closeDialogue(); window.__courtyard.setUi(false); });
  await sleep(800);
  const captureFrames = async (tag, frames, interval) => {
    const paths = [];
    for (let i = 0; i < frames; i++) {
      const file = path.join(CHAR_OUT, `${tag}_${String(i).padStart(3, '0')}.png`);
      await captureCanvas(page, file, { hideStats: true });
      paths.push(file);
      await sleep(interval);
    }
    return paths;
  };
  const idleFrames = await captureFrames('idle', 12, 90);
  await page.evaluate(() => window.__courtyard.setMoving(true));
  await sleep(300);
  const moveFrames = await captureFrames('move', 12, 90);
  await page.evaluate(() => window.__courtyard.setMoving(false));
  const gifFor = async (paths, out) => {
    const gif = GIFEncoder();
    const W = 640, H = 360;
    for (let i = 0; i < paths.length; i++) {
      const rgba = await sharp(paths[i]).resize(W, H).ensureAlpha().raw().toBuffer();
      const pal = quantize(rgba, 256, { format: 'rgb' });
      const idx = applyPalette(rgba, pal, 'rgb');
      gif.writeFrame(idx, W, H, { palette: pal, delay: 90, repeat: i === 0 ? 0 : undefined });
    }
    gif.finish();
    fs.writeFileSync(out, Buffer.from(gif.bytes()));
  };
  await gifFor(idleFrames, path.join(CHAR_OUT, 'char_idle.gif'));
  await gifFor(moveFrames, path.join(CHAR_OUT, 'char_move.gif'));

  const index = {
    kind: 't6_current_build_state_index',
    generated_at: new Date().toISOString(),
    build: { glb: sha(path.join(ROOT, 'art/candidates/candidate_n4/source/layout/MAP001_courtyard.glb')), bootstrap: sha(path.join(ROOT, 'demo_n4/assets/scripts/CourtyardBootstrap.ts')) },
    ui_states: ui, assets,
    character: {
      idle_gif: { path: rel(path.join(CHAR_OUT, 'char_idle.gif')), sha256: sha(path.join(CHAR_OUT, 'char_idle.gif')) },
      move_gif: { path: rel(path.join(CHAR_OUT, 'char_move.gif')), sha256: sha(path.join(CHAR_OUT, 'char_move.gif')) },
      idle_first: rel(idleFrames[0]), move_first: rel(moveFrames[0]),
    },
    page_errors: errors, logs_tail: logs.slice(-20),
    note: 'All shots are real canvas element captures from the current build; no page screenshots.',
  };
  fs.writeFileSync(path.join(OUT, 'state_index.json'), JSON.stringify(index, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ ui: ui.length, assets: assets.length, frames: idleFrames.length + moveFrames.length, errors: errors.length }));
  process.exit(errors.length ? 1 : 0);
})().catch((e) => { console.error('T6_ALL_STATES_FATAL', e); process.exit(2); });
