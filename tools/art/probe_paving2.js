/**
 * Second paving probe: the dashes survived removing albedo, normal and shadow
 * reception, so the remaining suspects are a second coplanar surface (the
 * mortar bed) and the shadow pass itself.
 *
 * Steps: base | noMortar | noCanopy | noShadow | mortarOnly
 * Usage: node tools/art/probe_paving2.js [outDir]
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('C:/软件/鼠鼠/tools/capture/canvas_capture.js');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://127.0.0.1:8805/?style=o';
const OUT = process.argv[2] || 'C:/软件/鼠鼠/delivery/next_cycle/n5/T5/probe';

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
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

  await page.evaluate(() => {
    const cc = window.cc;
    window.__byName = (re) => {
      const out = [];
      const walk = (n) => { if (re.test(n.name)) out.push(n); n.children.forEach(walk); };
      walk(cc.director.getScene());
      return out;
    };
  });

  const shoot = async (tag) => {
    const f = path.join(OUT, 'p2_' + tag + '.png');
    await captureCanvas(page, f);
    console.log('shot ' + f);
  };
  const hide = (re, on) => page.evaluate(([src, vis]) => {
    const r = new RegExp(src);
    window.__byName(r).forEach((n) => { n.active = vis; });
  }, [re, on]);

  await shoot('base');

  await hide('paving_mortar', false);
  await page.evaluate(() => new Promise((r) => setTimeout(r, 700)));
  await shoot('noMortar');
  await hide('paving_mortar', true);

  await hide('tree_canopy', false);
  await page.evaluate(() => new Promise((r) => setTimeout(r, 700)));
  await shoot('noCanopy');
  await hide('tree_canopy', true);

  await page.evaluate(() => {
    const cc = window.cc;
    const scene = cc.director.getScene();
    const light = scene.getChildByName('Main Light') ||
      scene.getComponentsInChildren(cc.DirectionalLight)[0].node;
    const dl = (light.components || []).find(
      (c) => cc.js.getClassName(c) === 'cc.DirectionalLight');
    if (dl) { dl.shadowEnabled = false; }
    window.__dl = dl;
  });
  await page.evaluate(() => new Promise((r) => setTimeout(r, 900)));
  await shoot('noShadow');

  await page.evaluate(() => { if (window.__dl) window.__dl.shadowEnabled = true; });

  // Only the mortar bed and the slabs, everything else hidden.
  await page.evaluate(() => {
    const cc = window.cc;
    const keep = /paving|Main Light|Camera/i;
    cc.director.getScene().children.forEach((n) => {
      if (!keep.test(n.name)) n.active = false;
    });
    window.__byName(/^(?!.*paving).*$/).forEach((n) => {
      if (!/paving|Main Light|Camera/i.test(n.name) && n.parent &&
          n.parent.name !== 'Canvas') n.active = false;
    });
  });
  await page.evaluate(() => new Promise((r) => setTimeout(r, 900)));
  await shoot('mortarOnly');

  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
