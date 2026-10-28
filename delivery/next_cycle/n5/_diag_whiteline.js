/**
 * Isolate the white dashes on the paving.
 *
 * Four captures of the same frame, each switching off one candidate:
 *   0 baseline | 1 grass hidden | 2 shadows off | 3 all meshes hidden
 * Whatever makes the dashes disappear names the culprit.
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
  p.on('pageerror', (e) => console.log('PAGE_ERROR ' + e.message));
  await p.goto('http://127.0.0.1:8805/', { waitUntil: 'networkidle2', timeout: 60000 });
  await p.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 90000 });
  await p.evaluate(() => {
    window.__courtyard.reset();
    window.__courtyard.resetView();
    window.__courtyard.setUi(false);
  });
  await new Promise((r) => setTimeout(r, 1200));

  const names = await p.evaluate(() => {
    const cc = window.cc;
    const scene = cc.director.getScene();
    const out = [];
    const walk = (n) => {
      const mr = n.components && n.components.find((c) => c.constructor.name === 'MeshRenderer');
      if (mr) out.push(n.name);
      n.children.forEach(walk);
    };
    walk(scene);
    return out;
  });
  console.log('meshes: ' + names.length);
  console.log(names.filter((n) => /grass|paving|leaf|litter|shrub|flower/i.test(n)).join('\n'));

  await captureCanvas(p, `${OUT}/w0_baseline.png`, { hideStats: true });

  await p.evaluate(() => {
    const scene = window.cc.director.getScene();
    const walk = (n) => {
      if (/grass/i.test(n.name)) n.active = false;
      n.children.forEach(walk);
    };
    walk(scene);
  });
  await new Promise((r) => setTimeout(r, 700));
  await captureCanvas(p, `${OUT}/w1_nograss.png`, { hideStats: true });

  await p.evaluate(() => {
    const scene = window.cc.director.getScene();
    scene.globals.shadows.enabled = false;
    const walk = (n) => {
      if (/grass/i.test(n.name)) n.active = true;
      n.children.forEach(walk);
    };
    walk(scene);
  });
  await new Promise((r) => setTimeout(r, 700));
  await captureCanvas(p, `${OUT}/w2_noshadow.png`, { hideStats: true });

  await b.close();
  console.log('done');
})();
