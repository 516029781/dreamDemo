const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('C:/软件/鼠鼠/tools/capture/canvas_capture.js');

(async () => {
  const b = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl',
           '--ignore-gpu-blocklist', '--no-sandbox'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const p = await b.newPage();
  await p.goto('http://127.0.0.1:8805/', { waitUntil: 'networkidle2', timeout: 60000 });
  await p.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await new Promise((r) => setTimeout(r, 900));

  // T1: brand-new material with no USE_TEXTURE define, solid red.
  const t1 = await p.evaluate(() => {
    const cc = window.cc;
    const scene = cc.director.getScene();
    let sh = null;
    const walk = (n) => { if (n.name === 'ContactShadow') sh = n; n.children.forEach(walk); };
    walk(scene);
    const mr = sh.components.find((c) => c.constructor.name === 'MeshRenderer');
    const m = new cc.Material();
    m.initialize({ effectName: 'builtin-unlit', technique: 1 });
    m.setProperty('mainColor', new cc.Color(255, 0, 0, 255));
    mr.setMaterial(m, 0);
    sh.setScale(3, 1, 3);
    return { effect: m.effectName, passes: m.passes.length };
  });
  await new Promise((r) => setTimeout(r, 700));
  await captureCanvas(p, 'C:/软件/鼠鼠/delivery/next_cycle/n5/T5/ui/diag_t1_notex.png', { hideStats: true });

  console.log(JSON.stringify(t1));
  await b.close();
})();
