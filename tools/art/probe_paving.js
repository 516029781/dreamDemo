/**
 * Isolate the white dashes on the flagstones.
 *
 * Rebuilding the map costs ~3 minutes per answer, so this probe drives the
 * already-built preview and flips one suspect at a time on the live scene,
 * capturing the same crop after each step. Whichever step removes the dashes
 * names the cause.
 *
 * Steps:
 *   base    as shipped
 *   noRcv   paving meshes stop receiving shadows      -> shadow acne
 *   noNrm   stone normal map removed (recompiled)     -> normal-map aliasing
 *   noTex   stone albedo map removed                  -> albedo tiling
 *   flat    albedo flat colour + no normal            -> geometry splits
 *
 * Usage: node tools/art/probe_paving.js [outDir]
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('C:/软件/鼠鼠/tools/capture/canvas_capture.js');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://127.0.0.1:8805/?style=o';
const OUT = process.argv[2] ||
  'C:/软件/鼠鼠/delivery/next_cycle/n5/T5/probe';

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl',
           '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 90000 });
  await page.evaluate(() => new Promise((r) => setTimeout(r, 1500)));

  const shoot = async (tag) => {
    const file = path.join(OUT, 'probe_' + tag + '.png');
    await captureCanvas(page, file);
    console.log('shot ' + file);
  };

  // cc.MeshRenderer is not exposed on the global in this build, so components
  // are matched by class name instead of by constructor.
  const paving = await page.evaluate(() => {
    const cc = window.cc;
    const mrOf = (n) => (n.components || []).find(
      (c) => cc.js.getClassName(c) === 'cc.MeshRenderer');
    const scene = cc.director.getScene();
    const found = [];
    const walk = (n) => {
      const mr = mrOf(n);
      if (mr && /paving/i.test(n.name)) {
        found.push(n.name);
        window.__paving = window.__paving || [];
        window.__paving.push(n);
      }
      n.children.forEach(walk);
    };
    walk(scene);
    return found;
  });
  console.log('paving nodes: ' + JSON.stringify(paving));

  await shoot('base');

  const setRcv = (v) => page.evaluate((on) => {
    const cc = window.cc;
    const mrOf = (n) => (n.components || []).find(
      (c) => cc.js.getClassName(c) === 'cc.MeshRenderer');
    (window.__paving || []).forEach((n) => {
      const mr = mrOf(n);
      if (mr) mr.receiveShadow = on;
    });
  }, v);

  await setRcv(false);
  await page.evaluate(() => new Promise((r) => setTimeout(r, 800)));
  await shoot('noRcv');
  await setRcv(true);

  // Drop the normal map and recompile the effect so the shader really loses it.
  const dropNormal = () => page.evaluate(() => {
    const cc = window.cc;
    const mrOf = (n) => (n.components || []).find(
      (c) => cc.js.getClassName(c) === 'cc.MeshRenderer');
    (window.__paving || []).forEach((n) => {
      const mr = mrOf(n);
      if (!mr) return;
      const count = mr.materials.length;
      for (let i = 0; i < count; i++) {
        const m = mr.getMaterial(i);
        if (!m) continue;
        m.setProperty('normalMap', null);
        m.recompileShaders({ USE_NORMAL_MAP: false, USE_PBR_MAP: false });
      }
    });
  });
  await dropNormal();
  await page.evaluate(() => new Promise((r) => setTimeout(r, 1200)));
  await shoot('noNrm');

  const dropAlbedo = () => page.evaluate(() => {
    const cc = window.cc;
    const mrOf = (n) => (n.components || []).find(
      (c) => cc.js.getClassName(c) === 'cc.MeshRenderer');
    (window.__paving || []).forEach((n) => {
      const mr = mrOf(n);
      if (!mr) return;
      const count = mr.materials.length;
      for (let i = 0; i < count; i++) {
        const m = mr.getMaterial(i);
        if (!m) continue;
        m.setProperty('mainTexture', null);
        m.setProperty('mainColor', new cc.Color(190, 178, 160, 255));
      }
    });
  });
  await dropAlbedo();
  await page.evaluate(() => new Promise((r) => setTimeout(r, 1200)));
  await shoot('flat');

  console.log('errors=' + errors.length);
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
