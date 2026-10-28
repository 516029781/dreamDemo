/**
 * Replace the paving material with a bare unlit material.
 *
 * Every shader input has already been cleared one at a time (albedo, normal,
 * pbr, shadows) and the dashes survived, so this drops the whole standard
 * effect. If the dots persist under an unlit flat colour they are geometry or
 * vertex data; if they vanish, they were a shader input after all.
 *
 * Usage: node tools/art/probe_material.js <outDir>
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('C:/软件/鼠鼠/tools/capture/canvas_capture.js');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://127.0.0.1:8805/?style=o';

(async () => {
  const outDir = process.argv[2] || 'C:/软件/鼠鼠/delivery/next_cycle/n5/T5/probe';
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl',
           '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 90000 });
  await page.evaluate(() => new Promise((r) => setTimeout(r, 1500)));

  const shoot = async (tag) => {
    const f = path.join(outDir, 'mat_' + tag + '.png');
    await captureCanvas(page, f);
    console.log('shot ' + f);
  };
  await shoot('base');

  const info = await page.evaluate(() => {
    const cc = window.cc;
    const find = (re) => {
      let hit = null;
      const walk = (n) => { if (!hit && re.test(n.name)) hit = n; n.children.forEach(walk); };
      walk(cc.director.getScene());
      return hit;
    };
    const node = find(/^MAP001_paving_slabs$/);
    if (!node) return 'no node';
    const mr = (node.components || []).find(
      (c) => cc.js.getClassName(c) === 'cc.MeshRenderer');
    const slots = mr.materials.length;
    for (let i = 0; i < slots; i++) {
      const m = new cc.Material();
      m.initialize({
        effectName: 'builtin-unlit',
        defines: {},
      });
      m.setProperty('mainColor', new cc.Color(190, 178, 160, 255));
      mr.setMaterial(m, i);
    }
    return 'replaced ' + slots + ' slots, mesh=' + (node.getComponent('cc.Mesh') || {}).name;
  });
  console.log(info);

  await page.evaluate(() => new Promise((r) => setTimeout(r, 1200)));
  await shoot('unlit');

  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
