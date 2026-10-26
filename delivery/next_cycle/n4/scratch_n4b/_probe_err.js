const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
(async () => {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new',
    args: ['--use-gl=angle','--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage'],
  });
  const page = await browser.newPage();
  const errs = [], logs = [];
  page.on('pageerror', e => errs.push(String(e)));
  page.on('console', m => { const t = m.text(); if (m.type()==='error' || t.includes('[COURTYARD]')) logs.push(m.type()+': '+t); });
  await page.goto('http://127.0.0.1:8803/', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 15000));
  console.log('PAGEERRORS:', JSON.stringify(errs.slice(0,8), null, 1));
  console.log('LOGS:', JSON.stringify(logs.slice(-25), null, 1));
  await browser.close();
})();
