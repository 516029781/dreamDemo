const path = require('path');
const puppeteer = require('puppeteer-core');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const ROOT = path.resolve(__dirname, '..');
const PAGE = path.join(ROOT, 'art', 'phase1', 'reference_character', 'reference_comparison.html');
const OUT = path.join(ROOT, 'art', 'phase1', 'reference_character', 'reference_comparison.png');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars'],
    defaultViewport: { width: 1600, height: 1100, deviceScaleFactor: 1 }
  });
  const page = await browser.newPage();
  await page.goto('file:///' + PAGE.replace(/\\/g, '/'), { waitUntil: 'load', timeout: 30000 });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(Array.from(document.images).map(img => img.complete ? null : new Promise(r => { img.onload = img.onerror = r; })));
  });
  await page.screenshot({ path: OUT, fullPage: false });
  await browser.close();
  console.log(OUT);
})();
