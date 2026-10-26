const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const URL = process.env.SPINE_URL || 'http://127.0.0.1:8173/viewer?anim=Relax&time=0.5';
const OUT = path.resolve(__dirname, '..', 'art', 'phase1', 'reference_character');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: [
      '--use-gl=angle',
      '--use-angle=swiftshader',
      '--enable-webgl',
      '--ignore-gpu-blocklist',
      '--no-sandbox',
      '--disable-dev-shm-usage'
    ],
    defaultViewport: { width: 1024, height: 1024, deviceScaleFactor: 1 }
  });
  const page = await browser.newPage();
  page.on('console', msg => console.log('PAGE', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('PAGEERROR', String(err && err.stack || err)));
  page.on('requestfailed', req => console.log('REQFAIL', req.url(), req.failure() && req.failure().errorText));
  await page.goto(URL, { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForFunction(() => document.title === 'DONE' || document.title === 'ERROR', { timeout: 20000 }).catch(() => {});
  const state = await page.evaluate(() => {
    const app = window.__app;
    const canvas = document.querySelector('canvas');
    let viewData = null;
    let extractData = null;
    try {
      if (app) {
        app.renderer.render(app.stage);
        viewData = app.view.toDataURL('image/png');
        const c = app.renderer.extract.canvas(app.stage, new PIXI.Rectangle(0, 0, app.renderer.width, app.renderer.height), 1);
        extractData = c.toDataURL('image/png');
      }
    } catch (err) {
      return { error: String(err && err.stack || err), title: document.title };
    }
    return {
      title: document.title,
      canvasCount: document.querySelectorAll('canvas').length,
      canvasSize: canvas ? [canvas.width, canvas.height] : null,
      webgl: !!(canvas && (canvas.getContext('webgl2') || canvas.getContext('webgl'))),
      hasApp: !!app,
      hasSpine: !!window.__spine,
      spineChildren: app ? app.stage.children.length : null,
      viewLength: viewData ? viewData.length : 0,
      extractLength: extractData ? extractData.length : 0,
      lastCapture: window.__lastCapture ? {
        inventoryAnimations: window.__lastCapture.inventory.animations,
        images: window.__lastCapture.images.map(x => ({ name: x.name, length: x.data.length })),
        logs: window.__lastCapture.logs
      } : null
    };
  });
  console.log(JSON.stringify(state, null, 2));
  if (state.viewLength) {
    const data = await page.evaluate(() => {
      const app = window.__app;
      app.renderer.render(app.stage);
      return app.view.toDataURL('image/png');
    });
    fs.writeFileSync(path.join(OUT, 'puppeteer_view.png'), Buffer.from(data.split(',')[1], 'base64'));
  }
  if (state.extractLength) {
    const data = await page.evaluate(() => {
      const app = window.__app;
      app.renderer.render(app.stage);
      const c = app.renderer.extract.canvas(app.stage, new PIXI.Rectangle(0, 0, app.renderer.width, app.renderer.height), 1);
      return c.toDataURL('image/png');
    });
    fs.writeFileSync(path.join(OUT, 'puppeteer_extract.png'), Buffer.from(data.split(',')[1], 'base64'));
  }
  await page.screenshot({ path: path.join(OUT, 'puppeteer_page.png'), omitBackground: true });
  await browser.close();
})();
