/** I01: full-scene formal camera / occlusion / stance regression on the candidate build. */
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('../../tools/capture/canvas_capture.js');

const ROOT = 'C:/软件/鼠鼠';
const OUT = path.join(ROOT, 'delivery/next_cycle/T7');
const sha = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const rel = (file) => path.relative(ROOT, file).replace(/\\/g, '/');

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
  await page.goto('http://127.0.0.1:8801/', { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await page.evaluate(() => { window.__courtyard.reset(); window.__courtyard.closeDialogue(); });
  const cases = [
    ['front_default', [0, -5.2]],
    ['behind_tree', [0, 2.0]],
    ['west_lane', [-7, -3]],
    ['east_lane', [7, 5]],
  ];
  const rows = [];
  for (const [name, pos] of cases) {
    await page.evaluate((p) => window.__courtyard.setPlayer(p[0], p[1]), pos);
    await new Promise((r) => setTimeout(r, 800));
    await page.evaluate(() => window.__courtyard.setUi(false));
    await new Promise((r) => setTimeout(r, 300));
    const meta = await captureCanvas(page, path.join(OUT, `I01_${name}.png`), { hideStats: true });
    const state = await page.evaluate(() => {
      const sc = cc.director.getScene();
      const cam = sc.getChildByName('Main Camera').getComponent(cc.Camera);
      const st = window.__courtyard.state();
      const p = st.player;
      let shadow = null;
      const walk = (n) => { if (n.name === 'ContactShadow') shadow = n.worldPosition; for (const c of n.children) walk(c); };
      walk(sc);
      const feet = cam.worldToScreen(new cc.Vec3(p[0], p[1], p[2]));
      const head = cam.worldToScreen(new cc.Vec3(p[0], p[1] + 1.75, p[2]));
      return { player: p, metrics_px: st.metrics.px, feet_screen: [feet.x, 720 - feet.y], head_screen: [head.x, 720 - head.y],
        shadow: shadow ? [shadow.x, shadow.y, shadow.z] : null,
        shadow_drift_m: shadow ? Math.hypot(shadow.x - p[0], shadow.z - p[2]) : null,
        camera: { position: [cam.node.position.x, cam.node.position.y, cam.node.position.z], fov: cam.fov } };
    });
    rows.push({ name, requested: pos, state, capture: meta, path: rel(path.join(OUT, `I01_${name}.png`)), sha256: meta.output.sha256 });
  }
  const report = {
    kind: 'I01_full_scene_regression',
    build_glb_sha256: sha(path.join(ROOT, 'art/full/source/layout/MAP001_courtyard.glb')),
    camera: rows[0].state.camera,
    cases: rows,
    occlusion: { front: 'character visible', behind: 'character occluded by tree canopy; see q03 head-region metric 1321 -> 110' },
    page_errors: errors,
    note: 'Four stances captured on the candidate build; camera follows the player. Full-scene regression only, not independent approval.',
  };
  fs.writeFileSync(path.join(OUT, 'I01_full_scene.json'), JSON.stringify(report, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ cases: rows.length, errors: errors.length }));
  process.exit(errors.length ? 1 : 0);
})().catch((e) => { console.error('I01_FATAL', e); process.exit(2); });
