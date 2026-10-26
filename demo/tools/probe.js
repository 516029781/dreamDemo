const path = require('path');
const fs = require('fs');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = process.env.DEMO_URL || 'http://127.0.0.1:8801/';
const OUT = 'C:/软件/鼠鼠/art/full/engine/probe';
fs.mkdirSync(OUT, { recursive: true });
(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    args: ['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  const logs = [];
  page.on('console', m => { logs.push('CONSOLE ' + m.type() + ' ' + m.text()); console.log(logs[logs.length-1]); });
  page.on('pageerror', e => { logs.push('PAGEERROR ' + String(e && e.stack || e)); console.log(logs[logs.length-1]); });
  page.on('requestfailed', r => { logs.push('REQFAIL ' + r.url() + ' ' + (r.failure()&&r.failure().errorText)); console.log(logs[logs.length-1]); });
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 }).catch(e => logs.push('WAITFAIL ' + e.message));
  await new Promise(r => setTimeout(r, 2500));
  const title = await page.title();
  logs.push('TITLE ' + title);
  const state = await page.evaluate(() => ({
    ready: window.__COURTYARD_READY__ || false,
    canvas: (() => { const c = document.querySelector('canvas'); return c ? [c.width, c.height] : null; })(),
    body: document.body ? document.body.innerText.slice(0,200) : '',
  }));
  logs.push('STATE ' + JSON.stringify(state));
  await page.screenshot({ path: path.join(OUT, 'probe_1280x720.png') });
  fs.writeFileSync(path.join(OUT, 'probe.log'), logs.join('\n'));
  await browser.close();
  console.log('PROBE_DONE');
})().catch(e => { console.error('PROBE_FATAL', e); process.exit(1); });
