/**
 * W2: find the spine pose that fits the 1024x1024 render texture without cropping.
 *
 * The character is drawn into an orthographic RT (orthoHeight 512, so the visible
 * range is -512..512 on both axes) and then mapped onto a 1.75 x 1.75 world quad.
 * PlayerSpineRT sits at y=-500 with scale 2.0, which pushes the weapon and the
 * boots past the RT edge: that is why the silhouette ends in a straight cut.
 *
 * This script reads the real skeleton bounds, computes a fit, and captures each
 * candidate so the choice is made by looking.
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
  fs.mkdirSync(OUT, { recursive: true });
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

  const info = await page.evaluate(() => {
    const cc = window.cc;
    let spineNode = null, quad = null;
    const walk = (n) => {
      if (n.name === 'PlayerSpineRT') spineNode = n;
      if (n.name === 'PlayerWorldQuad') quad = n;
      n.children.forEach(walk);
    };
    walk(cc.director.getScene());
    if (!spineNode) return { found: false };
    const ut = spineNode.getComponent(cc.UITransform);
    return {
      found: true,
      nodePos: [spineNode.position.x, spineNode.position.y, spineNode.position.z],
      scale: [spineNode.scale.x, spineNode.scale.y],
      contentSize: ut ? [ut.width, ut.height] : null,
      anchor: ut ? [ut.anchorX, ut.anchorY] : null,
      quadScale: quad ? [quad.scale.x, quad.scale.y] : null,
    };
  });

  // candidate fits: scale down and lift so the weapon and boots stay inside -512..512
  const CANDIDATES = [
    { name: 'fit_a', scale: 1.45, y: -430 },
    { name: 'fit_b', scale: 1.30, y: -400 },
    { name: 'fit_c', scale: 1.20, y: -430 },
  ];
  const shots = [];
  for (const c of CANDIDATES) {
    await page.evaluate((cfg) => {
      const cc = window.cc;
      let spineNode = null;
      const walk = (n) => { if (n.name === 'PlayerSpineRT') spineNode = n; n.children.forEach(walk); };
      walk(cc.director.getScene());
      spineNode.setScale(cfg.scale, cfg.scale, 1);
      spineNode.setPosition(0, cfg.y, 0);
      // same M3 pose as the contract evidence
      window.__courtyard.setCameraMode('inspect');
      const camNode = cc.director.getScene().getChildByName('Main Camera');
      camNode.setPosition(6.2, 4.6, -11.6);
      camNode.lookAt(new cc.Vec3(0, 1.2, -5.2));
      camNode.getComponent(cc.Camera).fov = 37.5;
      window.__courtyard.setUi(false);
    }, c);
    await new Promise((r) => setTimeout(r, 600));
    const meta = await captureCanvas(page, path.join(OUT, `char_${c.name}.png`), { hideStats: true });
    const after = await page.evaluate(() => {
      const cc = window.cc;
      let spineNode = null;
      const walk = (n) => { if (n.name === 'PlayerSpineRT') spineNode = n; n.children.forEach(walk); };
      walk(cc.director.getScene());
      return { scale: spineNode.scale.x, y: spineNode.position.y };
    });
    shots.push({ ...c, after, meta });
  }

  fs.writeFileSync(path.join(OUT, 'char_fit.json'), JSON.stringify({ info, shots }, null, 2) + '\n');
  await browser.close();
  console.log(JSON.stringify({ info, shots: shots.map((s) => ({ name: s.name, after: s.after })) }, null, 2));
})().catch((e) => { console.error('W2_FATAL', e); process.exit(2); });
