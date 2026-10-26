const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');

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

  const out = await p.evaluate(() => {
    const cc = window.cc;
    const scene = cc.director.getScene();
    let sh = null;
    let tree = null;
    const walk = (n) => {
      if (n.name === 'ContactShadow') sh = n;
      if (n.name === 'TreeContactShadow') tree = n;
      n.children.forEach(walk);
    };
    walk(scene);

    const info = (n) => {
      if (!n) return null;
      const mr = n.components.find((c) => c.constructor.name === 'MeshRenderer');
      const wp = n.worldPosition;
      const ws = n.worldScale;
      return {
        worldPos: [+wp.x.toFixed(2), +wp.y.toFixed(2), +wp.z.toFixed(2)],
        worldScale: [+ws.x.toFixed(2), +ws.y.toFixed(2), +ws.z.toFixed(2)],
        layer: n.layer,
        active: n.activeInHierarchy,
        hasMesh: !!(mr && mr.mesh),
        modelEnabled: mr && mr.model ? mr.model.enabled : null,
        subModels: mr && mr.model && mr.model.subModels ? mr.model.subModels.length : -1,
        matUuid: mr && mr.getMaterial(0) ? mr.getMaterial(0).uuid.slice(0, 8) : null,
        parent: n.parent ? n.parent.name : null,
      };
    };

    const cams = [];
    const walkc = (n) => {
      const c = n.getComponent && n.getComponent(cc.Camera);
      if (c) {
        cams.push({ name: n.name, visibility: c.visibility, fov: c.fov,
                    pos: [+n.worldPosition.x.toFixed(1), +n.worldPosition.y.toFixed(1),
                          +n.worldPosition.z.toFixed(1)] });
      }
      n.children.forEach(walkc);
    };
    walkc(scene);
    const probe = (n) => {
      if (!n) return null;
      const mr = n.components.find((c) => c.constructor.name === 'MeshRenderer');
      const m = mr.mesh;
      return { min: [m.minPosition.x, m.minPosition.y, m.minPosition.z],
               max: [m.maxPosition.x, m.maxPosition.y, m.maxPosition.z],
               structLen: m.struct && m.struct.vertexBundles ? m.struct.vertexBundles.length : -1 };
    };
    return { shadow: info(sh), tree: info(tree), cams,
             shadowBounds: probe(sh), treeBounds: probe(tree) };
  });

  console.log(JSON.stringify(out, null, 1));
  await b.close();
})();
