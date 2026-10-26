const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');
const sharp = require('sharp');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const OUT = path.resolve(__dirname, '..', 'art', 'phase1', 'reference_character', 'animation_probe');
const SIZE = 512;
const ANIMS = ['Default', 'Interact', 'Move', 'Relax', 'Sit', 'Sleep'];
const TIMES = [0, 0.25, 0.5, 1.0, 1.5, 2.0];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: SIZE, height: SIZE, deviceScaleFactor: 1 }
  });
  const page = await browser.newPage();
  page.on('pageerror', err => console.log('PAGEERROR', String(err && err.stack || err)));
  await page.goto(`http://127.0.0.1:8173/viewer?size=${SIZE}`, { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForFunction(() => window.__ready === true, { timeout: 30000 });
  const inventory = await page.evaluate(() => window.__inventory);
  console.log(JSON.stringify({ version: inventory.skeleton_version, skin: inventory.skins, animations: inventory.animations }, null, 2));

  const results = [];
  for (const anim of ANIMS) {
    const animInfo = inventory.animations.find(a => a.name === anim);
    if (!animInfo || animInfo.duration <= 0) {
      results.push({ anim, skipped: 'zero duration' });
      continue;
    }
    for (const time of TIMES) {
      if (time > animInfo.duration + 0.001) continue;
      const res = await page.evaluate(({ anim, time }) => window.__render(anim, time), { anim, time });
      const b64 = res.extract.split(',')[1];
      const safe = `probe_${anim}_` + String(time).replace('.', 'p');
      fs.writeFileSync(path.join(OUT, safe + '.png'), Buffer.from(b64, 'base64'));
      results.push({ anim, time, eyes: res.eyes, pose: res.pose, localBounds: res.fit.localBounds, scale: res.fit.scale, file: safe + '.png' });
      console.log('captured', anim, time, JSON.stringify(res.eyes));
    }
  }
  fs.writeFileSync(path.join(OUT, 'probe_results.json'), JSON.stringify({ inventory, results }, null, 2) + '\n');
  const thumbW = 160;
  const cols = Math.min(5, TIMES.length);
  const rows = Math.ceil(results.filter(r => !r.skipped).length / cols);
  const tiles = results.filter(r => !r.skipped);
  const composite = [];
  for (let i = 0; i < tiles.length; i++) {
    const img = await sharp(path.join(OUT, tiles[i].file)).resize(thumbW, thumbW, { fit: 'cover' }).png().toBuffer();
    composite.push({ input: img, left: (i % cols) * thumbW, top: Math.floor(i / cols) * thumbW });
  }
  await sharp({ create: { width: cols * thumbW, height: rows * thumbW, channels: 3, background: '#222222' } })
    .composite(composite).png().toFile(path.join(OUT, 'contact_sheet.png'));
  console.log('contact sheet written', cols * thumbW + 'x' + rows * thumbW);
  await browser.close();
})();
