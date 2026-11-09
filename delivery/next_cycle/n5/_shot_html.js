const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new',
    defaultViewport: { width: 1280, height: 1400, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  await page.goto('file:///C:/软件/鼠鼠/planning/art/_corridor_strip_preview.html', { waitUntil: 'load' });
  await new Promise((r) => setTimeout(r, 300));
  await page.screenshot({ path: 'C:/软件/鼠鼠/planning/art/_corridor_strip_preview.png', fullPage: true });
  console.log('shot ok');
  await browser.close();
})();
