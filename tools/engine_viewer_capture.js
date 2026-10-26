const path = require('path'); const fs = require('fs');
const { createRequire } = require('module'); const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const OUT = 'C:/软件/鼠鼠/art/full/previews/engine';
const UI_OUT = path.join(OUT, 'ui_states');
const ASSET_OUT = path.join(OUT, 'assets');
const URL = 'http://127.0.0.1:8801/';

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

(async () => {
  fs.mkdirSync(UI_OUT, { recursive: true });
  fs.mkdirSync(ASSET_OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage(); const logs = [];
  page.on('console', m => logs.push('CONSOLE ' + m.type() + ' ' + m.text()));
  page.on('pageerror', e => logs.push('PAGEERROR ' + String(e && e.stack || e)));
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.addStyleTag({ content: 'html,body{overflow:hidden;background:#1c1b18;margin:0;padding:0}h1.header,p.footer{display:none!important}#GameDiv{width:1280px!important;height:720px!important;border:0!important;border-radius:0!important;box-shadow:none!important;margin:0!important}#Cocos3dGameContainer,#GameCanvas{width:1280px!important;height:720px!important}' });
  await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1 });
  await page.evaluate(() => window.dispatchEvent(new Event('resize')));
  await new Promise(r => setTimeout(r, 600));
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });

  for (const id of UI_STATES) {
    await page.evaluate(() => window.__courtyard.resetView());
    await new Promise(r => setTimeout(r, 120));
    await page.evaluate(id => window.__courtyard.setUiState(id), id);
    await new Promise(r => setTimeout(r, 320));
    await page.screenshot({ path: path.join(UI_OUT, id + '.png') });
  }

  for (const id of ASSET_IDS) {
    await page.evaluate(() => window.__courtyard.resetView());
    await new Promise(r => setTimeout(r, 150));
    await page.evaluate(id => window.__courtyard.focusAsset(id), id);
    await new Promise(r => setTimeout(r, 550));
    await page.screenshot({ path: path.join(ASSET_OUT, id + '.png') });
  }

  const state = await page.evaluate(() => window.__courtyard.state()).catch(() => null);
  fs.writeFileSync(path.join(OUT, 'viewer_state.json'), JSON.stringify(state, null, 2) + '\n');
  fs.writeFileSync(path.join(OUT, 'viewer_capture.log'), logs.join('\n') + '\n');
  console.log('VIEWER_CAPTURE_DONE', JSON.stringify({ ui: UI_STATES.length, assets: ASSET_IDS.length, errors: state ? state.loadErrors : 'state_unavailable' }));
  await browser.close();
})().catch(e => { console.error('VIEWER_CAPTURE_FATAL', e); process.exit(1); });
