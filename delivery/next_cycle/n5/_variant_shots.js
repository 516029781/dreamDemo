/**
 * Look-dev bench: apply one variant's engine-side light values at runtime and
 * capture the formal no-UI frame. Geometry/palette differences come from the
 * GLB built for that variant, so only lights are touched here.
 *
 * Usage: node _variant_shots.js <TAG> <variants.json>
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const { captureCanvas } = require('C:/软件/鼠鼠/tools/capture/canvas_capture.js');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = 'http://127.0.0.1:8805/';
const TAG = process.argv[2] || 'A';
const VARIANTS = process.argv[3] || 'C:/软件/鼠鼠/planning/art/ART_VARIANTS.json';
const OUT = process.env.N5_SHOT_OUT || 'C:/软件/鼠鼠/delivery/next_cycle/n5/T5/variants';

const cfg = JSON.parse(fs.readFileSync(VARIANTS, 'utf8')).variants[TAG];
if (!cfg) throw new Error('unknown variant ' + TAG);

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
  // The look direction is a runtime choice (colour shift + map on/off), so it
  // rides on the query string; geometry comes from the GLB built for this tag.
  const url = cfg.url_style ? URL + '?style=' + cfg.url_style : URL;
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 90000 });

  const applied = await page.evaluate((L) => {
    const cc = window.cc;
    const scene = cc.director.getScene();
    const lin = (hex) => {
      const n = parseInt(hex.replace('#', ''), 16);
      const f = (v) => { const c = v / 255; return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
      return [f((n >> 16) & 255), f((n >> 8) & 255), f(n & 255)];
    };
    const srgb = (hex) => {
      const n = parseInt(hex.replace('#', ''), 16);
      return new cc.Color((n >> 16) & 255, (n >> 8) & 255, n & 255, 255);
    };
    const g = scene.globals;
    g.ambient.skyIllum = L.ambient;
    const s = lin(L.sky);
    g.ambient.skyColor = new cc.Vec4(s[0], s[1], s[2], 1);
    g.fog.fogColor = new cc.Color(L.fog[0], L.fog[1], L.fog[2], 255);
    g.fog.fogStart = L.fog_start;

    const keyNode = scene.getChildByName('Main Light');
    const key = keyNode && keyNode.getComponent(cc.DirectionalLight);
    if (key) key.illuminance = L.key_illum;
    const fillNode = scene.getChildByName('Fill Light');
    const fill = fillNode && fillNode.getComponent(cc.DirectionalLight);
    if (fill) { fill.color = srgb(L.fill_color); fill.illuminance = L.fill_illum; }
    return {
      ambient: g.ambient.skyIllum,
      fog: [g.fog.fogColor.r, g.fog.fogColor.g, g.fog.fogColor.b],
      key: key ? key.illuminance : null,
      fill: fill ? fill.illuminance : null,
    };
  }, cfg.lights);

  await page.evaluate(() => {
    window.__courtyard.reset();
    window.__courtyard.closeDialogue();
    window.__courtyard.resetView();
    window.__courtyard.setUi(false);
  });
  await new Promise((r) => setTimeout(r, 1400));

  const noUi = path.join(OUT, `variant_${TAG}_no_ui.png`);
  const meta = await captureCanvas(page, noUi, { hideStats: true });

  const stats = await page.evaluate(() => window.__courtyard.renderStats()).catch(() => null);
  fs.writeFileSync(path.join(OUT, `variant_${TAG}_shot.json`), JSON.stringify({
    variant: TAG, label: cfg.label, generated_at: new Date().toISOString(),
    applied_lights: applied, shot: meta, stats, page_errors: errors,
  }, null, 2) + '\n');
  console.log(`SHOT ${TAG} ${path.basename(noUi)} lights=${JSON.stringify(applied)} errors=${errors.length}`);
  await browser.close();
})().catch((e) => { console.error('FAIL ' + e.message); process.exit(1); });
