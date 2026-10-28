/** Diagnose whether COLOR_0 reached the engine and whether the vertex-colour macro is on. */
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://127.0.0.1:8805/';

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await new Promise((r) => setTimeout(r, 1500));
  const report = await page.evaluate(() => {
    const cc = window.cc;
    const out = { meshes: [], mats: [] };
    const scene = cc.director.getScene();
    const walk = (n) => {
      const mr = n.getComponent && n.getComponent(cc.MeshRenderer);
      if (mr && mr.model && mr.model.mesh) {
        const mesh = mr.model.mesh;
        const attrs = {};
        for (const vb of mesh.struct.vertexBundles) {
          for (const a of vb.attributes) attrs[a.name] = attrs[a.name] || a.format;
        }
        out.meshes.push({ node: n.name, attrs: Object.keys(attrs) });
      }
      const mat = n.getComponent && n.getComponent(cc.MeshRenderer);
      for (const c of n.children) walk(c);
    };
    walk(scene);
    // material macros on the map model
    const mapNode = scene.getChildByName('MapRoot') || scene.getChildByName('Map');
    out.matSample = [];
    const collect = (n) => {
      const mr = n.getComponent && n.getComponent(cc.MeshRenderer);
      if (mr && mr.getMaterial && mr.getMaterial(0)) {
        const m = mr.getMaterial(0);
        out.matSample.push({ node: n.name, effect: m.effectName,
          macros: Object.keys(m.passes[0].defines || {}).filter((k) => /VERTEX|NORMAL_MAP|PBR_MAP/.test(k)) });
      }
      for (const c of n.children) collect(c);
    };
    collect(scene);
    out.matSample = out.matSample.slice(0, 8);
    out.meshes = out.meshes.slice(0, 200);
    return out;
  });
  const withColor = report.meshes.filter((m) => m.attrs.includes('a_color'));
  console.log(JSON.stringify({
    meshCount: report.meshes.length,
    meshesWithAColor: withColor.length,
    sampleMesh: report.meshes.slice(0, 3),
    mats: report.matSample,
    errors,
  }, null, 1));
  await browser.close();
})();
