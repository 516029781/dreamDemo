const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  const logs = [];
  page.on('console', (m) => logs.push(m.text()));
  page.on('pageerror', (e) => logs.push('PAGEERROR ' + String(e) + '\nSTACK ' + ((e && e.stack) || 'none')));
  await page.goto('http://127.0.0.1:8805/', { waitUntil: 'networkidle2', timeout: 60000 });
  try {
    await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 20000 });
    logs.push('READY ok');
  } catch (e) {
    logs.push('NO_READY');
  }
  console.log(logs.slice(-30).join('\n'));
  await browser.close();
})();
