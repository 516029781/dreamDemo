const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');

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
  await new Promise((r) => setTimeout(r, 800));

  const report = () => p.evaluate(() => {
    const cc = window.cc;
    const scene = cc.director.getScene();
    const names = [];
    const walk = (n, d) => {
      if (d > 2) return;
      names.push('  '.repeat(d) + n.name + (n.active ? '' : ' [inactive]'));
      n.children.forEach((c) => walk(c, d + 1));
    };
    walk(scene, 0);
    const cams = [];
    const walk2 = (n) => {
      const c = n.getComponent && n.getComponent(cc.Camera);
      if (c) cams.push({ node: n.name, fov: c.fov, visibility: c.visibility,
                         pos: [+n.worldPosition.x.toFixed(2), +n.worldPosition.y.toFixed(2), +n.worldPosition.z.toFixed(2)] });
      n.children.forEach(walk2);
    };
    walk2(scene);
    const lights = [];
    const walk3 = (n) => {
      if (n.getComponent(cc.DirectionalLight)) lights.push(n.name);
      n.children.forEach(walk3);
    };
    walk3(scene);
    const s = window.__courtyard.state();
    const camNode = scene.getChildByName('Main Camera');
    const rt = {};
    const walkRT = (n) => { const c = n.getComponent && n.getComponent(cc.Camera);
      if (c) rt[n.name] = { targetTexture: !!c.targetTexture,
        tex: c.targetTexture ? [c.targetTexture.width, c.targetTexture.height] : null, fov: c.fov };
      n.children.forEach(walkRT); };
    walkRT(scene);
    return { cams, lights, cameraMode: s.cameraMode, viewer: s.viewer, studio: s.studioActive,
             player: s.player,
             rot: camNode ? { euler: [+camNode.eulerAngles.x.toFixed(1), +camNode.eulerAngles.y.toFixed(1), +camNode.eulerAngles.z.toFixed(1)],
                              look: (() => { const v = new cc.Vec3(); camNode.getWorldPosition(v); return null; })() } : null,
             rt, top5: names.slice(0, 10) };
  });

  console.log('--- right after load ---');
  console.log(JSON.stringify(await report(), null, 1));

  await p.evaluate(() => { window.__courtyard.reset(); window.__courtyard.resetView(); });
  await new Promise((r) => setTimeout(r, 900));
  console.log('--- after reset+resetView ---');
  console.log(JSON.stringify(await report(), null, 1));
  await b.close();
})();
