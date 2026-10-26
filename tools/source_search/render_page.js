// Screenshot a local HTML page with Chrome (no AI). Usage:
// node tools/source_search/render_page.js <html> <out.png> <width> <height>
const path = require('path');
const fs = require('fs');
const ROOT = path.resolve(__dirname, '..', '..');
const puppeteer = require(path.join(ROOT, '.tooling', 'node_modules', 'puppeteer-core'));

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const [html, out, w = '1600', h = '900'] = process.argv.slice(2);
const page_url = 'file:///' + path.resolve(ROOT, html).split(path.sep).join('/');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars'],
    defaultViewport: { width: Number(w), height: Number(h), deviceScaleFactor: 1 }
  });
  const page = await browser.newPage();
  await page.goto(page_url, { waitUntil: 'load', timeout: 30000 });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(Array.from(document.images).map(img => img.complete ? null : new Promise(r => { img.onload = img.onerror = r; })));
  });
  await new Promise(r => setTimeout(r, 250));
  await page.screenshot({ path: path.resolve(ROOT, out), fullPage: false });
  await browser.close();
  console.log(out, fs.statSync(path.resolve(ROOT, out)).size);
})();
