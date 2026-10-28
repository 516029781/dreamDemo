/**
 * Second pass on the white dashes: hide candidate meshes one at a time, then
 * take a very close look at one dash to see whether it reads as geometry or as
 * a shading artefact.
 */
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('C:/软件/鼠鼠/tools/capture/canvas_capture.js');

const OUT = 'C:/软件/鼠鼠/delivery/next_cycle/n5/T5/ref';

(async () => {
  const b = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl',
           '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1280, height: 720 },
  });
  const p = await b.newPage();
  await p.goto('http://127.0.0.1:8805/', { waitUntil: 'networkidle2', timeout: 60000 });
  await p.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 90000 });
  await p.evaluate(() => {
    window.__courtyard.reset();
    window.__courtyard.resetView();
    window.__courtyard.setUi(false);
  });
  await new Promise((r) => setTimeout(r, 1200));

  const hide = (pattern, on) => p.evaluate((pat, toOn) => {
    const scene = window.cc.director.getScene();
    const hit = [];
    const walk = (n) => {
      if (new RegExp(pat, 'i').test(n.name)) { n.active = toOn; hit.push(n.name); }
      n.children.forEach(walk);
    };
    walk(scene);
    return hit.length;
  }, pattern, on);

  console.log('hide mortar: ' + await hide('paving_mortar', false));
  await new Promise((r) => setTimeout(r, 600));
  await captureCanvas(p, `${OUT}/w3_nomortar.png`, { hideStats: true });
  await hide('paving_mortar', true);

  console.log('hide leaf_drift: ' + await hide('leaf_drift', false));
  await new Promise((r) => setTimeout(r, 600));
  await captureCanvas(p, `${OUT}/w4_nodrift.png`, { hideStats: true });
  await hide('leaf_drift', true);

  // Close-up: park the camera 3 m above a patch of paving and look straight down.
  const moved = await p.evaluate(() => {
    const cc = window.cc;
    const scene = cc.director.getScene();
    const camNode = scene.getChildByName('Main Camera');
    camNode.setPosition(4.0, 3.0, -3.0);
    camNode.lookAt(new cc.Vec3(4.0, 0.0, -3.0));
    camNode.getComponent(cc.Camera).fov = 40;
    return [camNode.worldPosition.x, camNode.worldPosition.y, camNode.worldPosition.z];
  });
  console.log('camera at ' + moved.join(','));
  await new Promise((r) => setTimeout(r, 900));
  await captureCanvas(p, `${OUT}/w5_closeup.png`, { hideStats: true });

  await b.close();
  console.log('done');
})();
