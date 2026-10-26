const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('../../../tools/capture/canvas_capture.js');

const URL = 'http://127.0.0.1:8803/';
const OUT = 'C:/软件/鼠鼠/delivery/next_cycle/n4/T5';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const dist = (a, b) => +Math.hypot(b[0] - a[0], b[2] - a[2]).toFixed(4);

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1, hasTouch: true },
  });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1, hasTouch: true });
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await page.evaluate(() => {
    window.__courtyard.reset();
    window.__courtyard.closeDialogue();
    window.__courtyard.setUi(true);
    window.__courtyard.resetView();
  });
  await sleep(900);

  const state = () => page.evaluate(() => window.__courtyard.state());
  const keyboardMove = async (ms = 900) => {
    await page.click('#GameCanvas');
    await page.keyboard.down('KeyD');
    await sleep(ms);
    await page.keyboard.up('KeyD');
    await sleep(250);
  };
  const touchMove = async (ms = 900) => {
    const rect = await page.evaluate(() => {
      const c = document.querySelector('#GameCanvas');
      const r = c.getBoundingClientRect();
      return { x: r.x, y: r.y, width: r.width, height: r.height };
    });
    const x = rect.x + rect.width * 110 / 1280;
    const y = rect.y + rect.height * 572 / 720;
    await page.touchscreen.touchStart(x, y);
    await page.touchscreen.touchMove(x + 60 * rect.width / 1280, y);
    await sleep(ms);
    await page.touchscreen.touchEnd();
    await sleep(250);
  };
  const shot = async (name) => captureCanvas(page, path.join(OUT, name + '.png'), { hideStats: true });

  async function movedPause(mode, move) {
    await page.evaluate(() => {
      window.__courtyard.reset();
      window.__courtyard.resetView();
      window.__courtyard.setUi(true);
    });
    await sleep(500);
    await move();
    const before = await state();
    const posBefore = before.player;
    const cameraBefore = before.camera;
    await page.evaluate(() => window.__courtyard.setPause(true));
    await sleep(400);
    const paused = await state();
    await shot('q04_pause_from_moved_' + mode);
    await move();
    const afterPauseMove = await state();
    const posDuringPause = afterPauseMove.player;
    await page.evaluate(() => window.__courtyard.setPause(false));
    await sleep(500);
    const resumed = await state();
    const posAfterResume = resumed.player;
    await shot('q04_resume_from_moved_' + mode);
    await move();
    const afterNewInput = await state();
    return {
      input_mode: mode,
      start_player: posBefore,
      start_camera: cameraBefore,
      move_before_pause_m: dist([0, 0, -5.2], posBefore),
      paused: paused.paused,
      input_locked_during_pause: paused.inputLocked,
      displacement_during_pause_m: dist(posDuringPause, posBefore),
      resumed_paused_flag: resumed.paused,
      displacement_on_resume_m: dist(posAfterResume, posDuringPause),
      displacement_after_new_input_m: dist(afterNewInput.player, posAfterResume),
      camera_delta_on_resume: +Math.hypot(
        resumed.camera[0] - cameraBefore[0],
        resumed.camera[1] - cameraBefore[1],
        resumed.camera[2] - cameraBefore[2]).toFixed(4),
      board_state: resumed.boardState,
      dialogue_visible: resumed.dialogueVisible,
      anim: resumed.anim,
      new_input_player: afterNewInput.player,
    };
  }

  const keyboard = await movedPause('keyboard', () => keyboardMove(1100));
  const touch = await movedPause('touch', () => touchMove(1100));

  // Portrait return from a moved position.
  await page.evaluate(() => {
    window.__courtyard.reset();
    window.__courtyard.resetView();
    window.__courtyard.setUi(true);
  });
  await sleep(500);
  await keyboardMove(1000);
  const beforePortrait = await state();
  await page.setViewport({ width: 720, height: 1280, deviceScaleFactor: 1, hasTouch: true });
  await sleep(1200);
  const portrait = await state();
  await shot('q04_portrait_from_moved');
  await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1, hasTouch: true });
  await sleep(1200);
  const afterPortrait = await state();
  await shot('q04_landscape_return_from_moved');

  const result = {
    kind: 'n4_q04_pause_resume_non_spawn',
    generated_at: new Date().toISOString(),
    url: URL,
    keyboard,
    touch,
    portrait: {
      before_player: beforePortrait.player,
      before_camera: beforePortrait.camera,
      portrait_player: portrait.player,
      portrait_blocked: portrait.portraitBlocked,
      portrait_input_locked: portrait.inputLocked,
      portrait_canvas: portrait.metrics ? portrait.metrics.canvas : null,
      after_player: afterPortrait.player,
      after_camera: afterPortrait.camera,
      after_blocked: afterPortrait.portraitBlocked,
      after_input_locked: afterPortrait.inputLocked,
      after_camera_mode: afterPortrait.cameraMode,
      displacement_portrait_m: dist(portrait.player, beforePortrait.player),
      displacement_return_m: dist(afterPortrait.player, beforePortrait.player),
      player_preserved: dist(afterPortrait.player, beforePortrait.player) <= 0.02,
    },
    page_errors: errors,
  };
  fs.writeFileSync(path.join(OUT, 'q04_behavior_moved.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify({
    keyboard_resume: keyboard.displacement_on_resume_m,
    touch_resume: touch.displacement_on_resume_m,
    portrait_return: result.portrait.displacement_return_m,
    player_preserved: result.portrait.player_preserved,
    errors: errors.length,
  }));
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch((e) => { console.error('N3_Q04_FATAL', e); process.exit(2); });
