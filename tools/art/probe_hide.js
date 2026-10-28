/**
 * Generic live-scene hide probe.
 *
 * Usage: node tools/art/probe_hide.js <outDir> <tag>:<regex>:<0|1> ...
 *   e.g. node tools/art/probe_hide.js out groundOff:^MAP001_ground$:0 base:::1
 * Nodes whose name matches <regex> are shown (1) or hidden (0); 1 is assumed
 * when omitted. A shot is taken after each step.
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
  const [outDir, ...steps] = process.argv.slice(2);
  if (!outDir || !steps.length) {
    console.error('usage: probe_hide.js <outDir> <tag>:<regex>:<0|1> ...');
    process.exit(2);
  }
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

  for (const step of steps) {
    const [tag, src, vis] = step.split(':');
    if (src) {
      const applied = await page.evaluate(([s, v]) => {
        const cc = window.cc;
        const re = new RegExp(s);
        const hit = [];
        const walk = (n) => {
          if (re.test(n.name)) { n.active = v; hit.push(n.name); }
          n.children.forEach(walk);
        };
        walk(cc.director.getScene());
        return hit;
      }, [src, vis !== '0']);
      console.log(tag + ' -> ' + (vis === '0' ? 'hide ' : 'show ') +
                  JSON.stringify(applied));
      await page.evaluate(() => new Promise((r) => setTimeout(r, 900)));
    }
    const f = path.join(outDir, 'hide_' + tag + '.png');
    await captureCanvas(page, f);
    console.log('shot ' + f);
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
