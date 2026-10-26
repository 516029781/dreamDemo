/**
 * P0b: capture the three independent camera poses required by contract v2.1 3.1.
 *
 * M1 front  : the formal follow camera, held still (identical to game_finalN5_formal_no_ui)
 * M2 side   : 45 deg around the player, eye near the character's height
 * M3 low    : reverse angle from north, near eye level
 *
 * No asset, no build change. The camera is driven through the scene graph after
 * switching the bootstrap into inspect mode, which stops the per-frame follow.
 *
 * Usage: node delivery/next_cycle/n5/_p0b_poses.js [outDir]
 */
const path = require('path');
const fs = require('fs');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('../../../tools/capture/canvas_capture.js');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://127.0.0.1:8805/';
const OUT = process.argv[2] || 'C:/软件/鼠鼠/delivery/next_cycle/n5/T3/poses';

// Player stands at (0, PAVING_TOP, -5.2); PAVING_TOP ~ 0.3.
const PLAYER = [0, 0.3, -5.2];

const POSES = [
  { name: 'm1_front', label: 'M1 正面全景', pos: [-2.5, 11.5, -14.6], look: [-2.5, 3.5, -3.7], fov: 37.5 },
  { name: 'm2_side', label: 'M2 侧向45度', pos: [4.88, 6.5, -13.61], look: [0, 1.0, -5.2], fov: 37.5 },
  { name: 'm2_side_high', label: 'M2b 侧向高位', pos: [6.9, 9.2, -12.2], look: [0, 1.2, -5.2], fov: 37.5 },
  { name: 'm3_east', label: 'M3 东侧低角', pos: [8.5, 3.2, -5.2], look: [0, 1.2, -5.2], fov: 37.5 },
  { name: 'm3_southeast', label: 'M3b 东南中位', pos: [6.2, 4.6, -11.6], look: [0, 1.2, -5.2], fov: 37.5 },
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  const logs = [];
  const pageErrors = [];
  page.on('pageerror', (e) => pageErrors.push(String(e)));
  page.on('console', (m) => { if (m.text().includes('[COURTYARD]')) logs.push(m.text()); });
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await page.evaluate(() => {
    window.__courtyard.reset();
    window.__courtyard.closeDialogue();
  });
  await new Promise((r) => setTimeout(r, 1000));

  const probe = await page.evaluate(() => {
    const cc = window.cc;
    const scene = cc && cc.director && cc.director.getScene();
    const camNode = scene && scene.getChildByName('Main Camera');
    return {
      cc_available: !!cc,
      scene: !!scene,
      camera_node: !!camNode,
      camera_children: camNode ? camNode.children.length : -1,
      fov: camNode ? camNode.getComponent(cc.Camera).fov : null,
    };
  });
  if (!probe.camera_node) {
    console.error('POSE_PROBE_FAILED', JSON.stringify(probe));
    await browser.close();
    process.exit(3);
  }

  const shots = [];
  for (const p of POSES) {
    await page.evaluate((pose) => {
      const cc = window.cc;
      // inspect mode stops the per-frame follow camera in update()
      window.__courtyard.setCameraMode('inspect');
      const camNode = cc.director.getScene().getChildByName('Main Camera');
      camNode.setPosition(pose.pos[0], pose.pos[1], pose.pos[2]);
      camNode.lookAt(new cc.Vec3(pose.look[0], pose.look[1], pose.look[2]));
      const cam = camNode.getComponent(cc.Camera);
      cam.fov = pose.fov;
      window.__courtyard.setUi(false);
    }, p);
    await new Promise((r) => setTimeout(r, 700));
    const meta = await captureCanvas(page, path.join(OUT, `pose_${p.name}_no_ui.png`), { hideStats: true });
    shots.push({ name: `${p.name}_no_ui`, label: p.label, pose: p, meta });

    if (p.name === 'm2_side') {
      await page.evaluate(() => window.__courtyard.setUi(true));
      await new Promise((r) => setTimeout(r, 600));
      shots.push({ name: 'm2_side_ui', label: 'M2 侧向45度 + UI', pose: p, meta: await captureCanvas(page, path.join(OUT, 'pose_m2_side_ui.png'), { hideStats: true }) });
      await page.evaluate(() => window.__courtyard.setUi(false));
    }
  }

  const stats = await page.evaluate(() => window.__courtyard.renderStats()).catch(() => null);
  fs.writeFileSync(path.join(OUT, 'poses.json'), JSON.stringify({
    kind: 'p0b_independent_poses',
    contract: 'PHASE1_ART_ACCEPTANCE.md v2.1 section 3.1',
    generated_at: new Date().toISOString(),
    player_anchor: PLAYER,
    probe, stats, shots, logs: logs.slice(-15), page_errors: pageErrors,
  }, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ shots: shots.length, probe, page_errors: pageErrors.length }));
  process.exit(pageErrors.length ? 1 : 0);
})().catch((error) => { console.error('P0B_POSES_FATAL', error); process.exit(2); });
