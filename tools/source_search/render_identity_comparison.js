// Screenshot the source_search identity comparison page (local Chrome, no AI).
// Usage: node tools/source_search/render_identity_comparison.js
const path = require('path');
const fs = require('fs');
const ROOT = path.resolve(__dirname, '..', '..');
const puppeteer = require(path.join(ROOT, '.tooling', 'node_modules', 'puppeteer-core'));

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const DIR = path.join(ROOT, 'art', 'phase1', 'reference_character', 'source_search');
const PAGE = path.join(DIR, 'identity_comparison.html');
const OUT = path.join(DIR, 'identity_candidate_1015_aglna2.png');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars'],
    defaultViewport: { width: 1700, height: 1250, deviceScaleFactor: 1 }
  });
  const page = await browser.newPage();
  await page.goto('file:///' + PAGE.replace(/\\/g, '/'), { waitUntil: 'load', timeout: 30000 });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(Array.from(document.images).map(img => img.complete ? null : new Promise(r => { img.onload = img.onerror = r; })));
  });
  await new Promise(r => setTimeout(r, 250));
  await page.screenshot({ path: OUT, fullPage: false });
  await browser.close();
  console.log(OUT, fs.statSync(OUT).size);
})();
