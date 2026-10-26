/**
 * Diagnose whether the character quad / render texture crops the character's feet.
 * Scales the world quad up without rebuilding; if feet appear, the crop is geometric.
 */
const path = require('path');
const fs = require('fs');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('../../../tools/capture/canvas_capture.js');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://127.0.0.1:8805/';
const OUT = 'C:/软件/鼠鼠/delivery/next_cycle/n5/T3/poses';

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await page.evaluate(() => { window.__courtyard.reset(); window.__courtyard.closeDialogue(); });
  await new Promise((r) => setTimeout(r, 900));

  // M3 pose, closest view, so the bottom edge is unambiguous
  await page.evaluate(() => {
    const cc = window.cc;
    window.__courtyard.setCameraMode('inspect');
    const camNode = cc.director.getScene().getChildByName('Main Camera');
    camNode.setPosition(6.2, 4.6, -11.6);
    camNode.lookAt(new cc.Vec3(0, 1.2, -5.2));
    camNode.getComponent(cc.Camera).fov = 37.5;
    window.__courtyard.setUi(false);
  });
  await new Promise((r) => setTimeout(r, 600));

  const info = await page.evaluate(() => {
    const cc = window.cc;
    const scene = cc.director.getScene();
    let quad = null;
    const walk = (n) => { if (n.name === 'PlayerWorldQuad') quad = n; n.children.forEach(walk); };
    walk(scene);
    if (!quad) return { found: false };
    const wp = quad.worldPosition;
    const ws = quad.worldScale;
    return { found: true, name: quad.name, pos: [wp.x, wp.y, wp.z], scale: [ws.x, ws.y, ws.z], active: quad.active };
  });

  await captureCanvas(page, path.join(OUT, 'diag_char_scale100.png'), { hideStats: true });

  const scaled = await page.evaluate(() => {
    const cc = window.cc;
    let quad = null;
    const walk = (n) => { if (n.name === 'PlayerWorldQuad') quad = n; n.children.forEach(walk); };
    walk(cc.director.getScene());
    if (!quad) return null;
    quad.setScale(1.45, 1.45, 1);
    // keep the bottom edge on the ground: quad is centred on the player anchor
    const p = quad.worldPosition;
    return { pos: [p.x, p.y, p.z], scale: [quad.worldScale.x, quad.worldScale.y, quad.worldScale.z] };
  });
  await new Promise((r) => setTimeout(r, 500));
  await captureCanvas(page, path.join(OUT, 'diag_char_scale145.png'), { hideStats: true });

  fs.writeFileSync(path.join(OUT, 'diag_char.json'), JSON.stringify({ info, scaled }, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ info, scaled }));
})().catch((e) => { console.error('DIAG_FATAL', e); process.exit(2); });
