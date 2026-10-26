/**
 * T5: collect Q01/Q03/Q04/Q05/Q06/Q09 evidence on the current build.
 * Real canvas captures only; no page screenshots as evidence.
 */
const path = require('path');
const fs = require('fs');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('../../../tools/capture/canvas_capture.js');

const { assertPinnedBuild } = require('./_n5_pin.js');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://127.0.0.1:8805/';
const OUT = 'C:/软件/鼠鼠/delivery/next_cycle/n5/T5';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const PIN = assertPinnedBuild();
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1, hasTouch: true },
  });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  const reset = async () => {
    await page.evaluate(() => {
      window.__courtyard.resetView();
      window.__courtyard.reset();
      window.__courtyard.closeDialogue();
    });
    await sleep(1200);
  };
  const ui = async (visible) => { await page.evaluate((v) => window.__courtyard.setUi(v), visible); await sleep(300); };
  const player = () => page.evaluate(() => window.__courtyard.state().player);
  const state = () => page.evaluate(() => window.__courtyard.state());
  const shot = (name) => captureCanvas(page, path.join(OUT, name + '.png'), { hideStats: true });

  // Q01 formal camera, three states.
  await reset();
  await ui(false);
  const noUi = await shot('q01_formal_no_ui');
  const cam = await page.evaluate(() => {
    const sc = cc.director.getScene();
    const c = sc.getChildByName('Main Camera');
    const e = c.eulerAngles;
    return { position: [c.position.x, c.position.y, c.position.z], euler: [e.x, e.y, e.z], fov: c.getComponent(cc.Camera).fov };
  });
  const m1 = (await state()).metrics;
  await ui(true);
  const hud = await shot('q01_formal_ui');
  await page.evaluate(() => window.__courtyard.openDialogue(1));
  await sleep(700);
  const dialogue = await shot('q01_dialogue');
  fs.writeFileSync(path.join(OUT, 'q01_camera.json'), JSON.stringify({ camera: cam, metrics: m1, shots: { no_ui: noUi, hud, dialogue } }, null, 2) + '\n');

  // Q03 occlusion: player front/behind with camera-follow.
  await page.evaluate(() => window.__courtyard.closeDialogue());
  await sleep(300);
  const occ = {};
  for (const [name, pos] of [['front', [0, -5.2]], ['behind', [0, 2.0]]]) {
    await page.evaluate((v) => window.__courtyard.setPlayer(v[0], v[1]), pos);
    await sleep(700);
    await ui(false);
    const meta = await shot('q03_' + name);
    const st = await state();
    occ[name] = { player: pos, state_player: st.player, metrics: st.metrics, capture: meta };
  }
  fs.writeFileSync(path.join(OUT, 'q03_occlusion.json'), JSON.stringify({ cases: occ, note: 'camera follows the player; behind tree means the character screen position is same but pixels are canopy' }, null, 2) + '\n');

  // Q04 behavior: keyboard and touch runs are measured separately.
  const runs = [];
  const touchPoint = async () => page.evaluate(() => {
    const c = document.querySelector('#GameCanvas');
    const r = c.getBoundingClientRect();
    return { x: r.x + r.width * 110 / 1280, y: r.y + r.height * 572 / 720, rect: { x: r.x, y: r.y, width: r.width, height: r.height } };
  });
  const touchMove = async (ms = 650) => {
    const p = await touchPoint();
    await page.touchscreen.touchStart(p.x, p.y);
    await page.touchscreen.touchMove(p.x + 55 * p.rect.width / 1280, p.y);
    await sleep(ms);
    await page.touchscreen.touchEnd();
    return p;
  };
  const keyboardMove = async (ms = 650) => {
    await page.click('#GameCanvas');
    await page.keyboard.down('KeyD');
    await sleep(ms);
    await page.keyboard.up('KeyD');
  };
  const attempt = async (mode) => {
    if (mode === 'keyboard') await keyboardMove(500);
    else await touchMove(500);
  };
  const deltaBetween = (a, b) => +Math.hypot(b[0] - a[0], b[2] - a[2]).toFixed(4);
  async function behaviorFor(mode) {
    await reset();
    await ui(true);
    const n0 = await player();
    if (mode === 'keyboard') await keyboardMove(650); else await touchMove(650);
    await sleep(300);
    const normalMove = deltaBetween(n0, await player());

    await reset();
    await ui(true);
    const p0 = await player();
    await page.evaluate(() => window.__courtyard.setPause(true));
    await sleep(300);
    const pauseAnim = (await state()).anim;
    await shot('q04_pause_' + mode);
    await attempt(mode);
    const p1 = await player();
    const pauseDelta = deltaBetween(p0, p1);
    await page.evaluate(() => window.__courtyard.setPause(false));
    await sleep(300);
    const p2 = await player();
    const resumeWithout = deltaBetween(p1, p2);
    await attempt(mode);
    await sleep(300);
    const p3 = await player();
    const resumeAfter = deltaBetween(p2, p3);

    await reset();
    await ui(true);
    const d0 = await player();
    await page.evaluate(() => window.__courtyard.openDialogue(1));
    await sleep(500);
    const dialogueAnim = (await state()).anim;
    await shot('q04_dialogue_' + mode);
    await attempt(mode);
    const d1 = await player();
    const dialogueDelta = deltaBetween(d0, d1);
    await page.evaluate(() => window.__courtyard.closeDialogue());
    await sleep(300);
    return {
      input_mode: mode,
      normal_move_m: normalMove,
      pause_displacement_m: pauseDelta,
      dialogue_displacement_m: dialogueDelta,
      resumed_without_input_m: resumeWithout,
      resumed_after_new_input_m: resumeAfter,
      clip_after_pause: pauseAnim === 'Move' || dialogueAnim === 'Move',
      anim_during_pause: pauseAnim,
      anim_during_dialogue: dialogueAnim,
    };
  }
  runs.push(await behaviorFor('keyboard'));
  runs.push(await behaviorFor('touch'));
  fs.writeFileSync(path.join(OUT, 'q04_behavior.json'), JSON.stringify({ runs }, null, 2) + '\n');

  // Q05 board states.
  await reset();
  await page.evaluate(() => window.__courtyard.focusAsset('FX003'));
  await sleep(800);
  const board = { states: {} };
  for (const s of ['empty', 'full', 'reset']) {
    await page.evaluate((v) => window.__courtyard.setBoardState(v), s);
    await sleep(500);
    const cards = await page.evaluate(() => {
      const a = [];
      const walk = (n) => { if (n.name.indexOf('MAP001_message_board_card_') === 0 && n.active) a.push(n.name); for (const c of n.children) walk(c); };
      walk(cc.director.getScene());
      return a;
    });
    const meta = await shot('q05_board_' + s);
    board.states[s] = { active_cards: cards, count: cards.length, capture: meta };
  }
  board.reset_residue = board.states.reset.count !== 0;
  fs.writeFileSync(path.join(OUT, 'q05_board.json'), JSON.stringify(board, null, 2) + '\n');

  // Q06 stats.
  await reset();
  await page.evaluate(() => window.__courtyard.enableStats(true));
  await sleep(1800);
  const statsUi = await page.evaluate(() => window.__courtyard.renderStats());
  await ui(false);
  await sleep(600);
  const statsNoUi = await page.evaluate(() => window.__courtyard.renderStats());
  const scopes = {};
  for (const asset of ['MAP001', 'CHAR001', 'CHAR002', 'LOOK001']) {
    await page.evaluate((id) => window.__courtyard.focusAsset(id), asset);
    await sleep(900);
    scopes[asset] = await page.evaluate(() => window.__courtyard.renderStats());
  }
  const layout = JSON.parse(fs.readFileSync('C:/软件/鼠鼠/art/full/source/layout/layout.json', 'utf8'));
  const glb = 'C:/软件/鼠鼠/art/full/source/layout/MAP001_courtyard.glb';
  const crypto = require('crypto');
  fs.writeFileSync(path.join(OUT, 'q06_stats.json'), JSON.stringify({
    stats_ui_visible: statsUi, stats_ui_hidden: statsNoUi, scopes,
    final_glb_sha256: crypto.createHash('sha256').update(fs.readFileSync(glb)).digest('hex'),
    glb_bytes: fs.statSync(glb).size,
    layout_tris: layout.stats ? layout.stats.triangles : null,
    layout_instances: layout.stats ? layout.stats.instances : null,
    device: 'desktop Chrome SwiftShader (no phone device tested)',
  }, null, 2) + '\n');

  // Q09 landscape/portrait viewports.
  const viewports = [];
  for (const vp of [{ name: 'landscape_1280x720', w: 1280, h: 720 }, { name: 'portrait_720x1280', w: 720, h: 1280 }]) {
    const p2 = await browser.newPage();
    p2.on('pageerror', (e) => errors.push(String(e)));
    await p2.setViewport({ width: vp.w, height: vp.h, deviceScaleFactor: 1, hasTouch: true });
    await p2.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
    await p2.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
    await p2.evaluate(() => {
      const gd = document.getElementById('GameDiv');
      gd.style.width = window.innerWidth + 'px';
      gd.style.height = window.innerHeight + 'px';
      window.cc.view.resizeWithBrowserSize(true);
      window.dispatchEvent(new Event('resize'));
    });
    await sleep(800);
    if (vp.w < vp.h) {
      await p2.evaluate(() => window.__courtyard.setUiState('rotate_notice'));
    } else {
      await p2.evaluate(() => { window.__courtyard.reset(); window.__courtyard.closeDialogue(); window.__courtyard.setUi(true); });
    }
    await sleep(900);
    const meta = await captureCanvas(p2, path.join(OUT, 'q09_' + vp.name + '.png'), { hideStats: true });
    const st = await p2.evaluate(() => {
      const v = window.cc.view;
      return { canvas: [v.getCanvasSize().width, v.getCanvasSize().height], visible: [v.getVisibleSize().width, v.getVisibleSize().height], state: window.__courtyard.state() };
    });
    viewports.push({ name: vp.name, width: vp.w, height: vp.h, canvas_backing: [meta.backing_width, meta.backing_height], screenshot_dimensions: [meta.output.width, meta.output.height], safe_area: { left: 28, right: 29, top: 29, bottom: 78, unit: 'design_px' }, text_native_size: true, capture: meta, engine_view: st });
    await p2.close();
  }
  fs.writeFileSync(path.join(OUT, 'q09_viewports.json'), JSON.stringify({ viewports, device_tested: false }, null, 2) + '\n');

  fs.writeFileSync(path.join(OUT, 'probe_errors.json'), JSON.stringify({ page_errors: errors, logs: [] }, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ errors: errors.length, outputs: fs.readdirSync(OUT).length }));
  process.exit(errors.length ? 1 : 0);
})().catch((e) => { console.error('T5_PROBE_FATAL', e); process.exit(2); });
