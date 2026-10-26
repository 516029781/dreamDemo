/**
 * P06/F05: capture the real game canvas (never the page shell).
 * Records viewport, canvas CSS rect, backing size, DPR, capture method and hashes.
 * Use within one browser session for multiple related shots.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const puppeteer = req('puppeteer-core');
const sharp = req('sharp');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

function sha256(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function pngSize(file) {
  const buffer = fs.readFileSync(file);
  if (buffer.slice(0, 8).toString('hex') !== '89504e470d0a1a0a') throw new Error('Not a PNG: ' + file);
  return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) };
}

async function collectCanvasInfo(page, selector = '#GameCanvas') {
  const info = await page.evaluate((sel) => {
    const canvas = document.querySelector(sel) || document.querySelector('canvas');
    if (!canvas) throw new Error('No canvas found for selector ' + sel);
    const rect = canvas.getBoundingClientRect();
    return {
      matched_selector: canvas.id ? '#' + canvas.id : canvas.tagName.toLowerCase(),
      css_rect: { x: rect.x + window.scrollX, y: rect.y + window.scrollY, width: rect.width, height: rect.height },
      backing_width: canvas.width,
      backing_height: canvas.height,
      device_pixel_ratio: window.devicePixelRatio,
      viewport: {
        browser_width: window.innerWidth,
        browser_height: window.innerHeight,
        scroll_x: window.scrollX,
        scroll_y: window.scrollY,
      },
      page_shell_visible: Boolean(document.querySelector('h1.header, p.footer')),
    };
  }, selector);
  if (!info.css_rect.width || !info.css_rect.height) throw new Error('Canvas has zero CSS size');
  return info;
}

async function captureCanvas(page, outputPath, options = {}) {
  const selector = options.selector || '#GameCanvas';
  const hideStats = options.hideStats !== false;
  if (hideStats && options.statsApi !== false) {
    await page.evaluate(() => {
      try { window.__courtyard && window.__courtyard.enableStats(false); } catch (_) {}
    }).catch(() => {});
  }
  const info = await collectCanvasInfo(page, selector);
  const element = await page.$(info.matched_selector);
  if (!element) throw new Error('Canvas element not found: ' + info.matched_selector);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  await element.screenshot({ path: outputPath });
  const size = pngSize(outputPath);
  const output = { path: outputPath, sha256: sha256(outputPath), width: size.width, height: size.height };
  if (size.width !== info.backing_width || size.height !== info.backing_height) {
    throw new Error(`Canvas capture ${size.width}x${size.height} != backing ${info.backing_width}x${info.backing_height}`);
  }
  return {
    capture_method: 'element_screenshot',
    page_screenshot: false,
    selector: info.matched_selector,
    css_rect: info.css_rect,
    backing_width: info.backing_width,
    backing_height: info.backing_height,
    device_pixel_ratio: info.device_pixel_ratio,
    viewport: info.viewport,
    page_shell_visible: info.page_shell_visible,
    stats_hidden: hideStats,
    output,
  };
}

async function selfTest(outDir) {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 800, height: 600, deviceScaleFactor: 2 },
  });
  try {
    const page = await browser.newPage();
    await page.setContent(`<!doctype html><html><body style="margin:0;background:#222">
      <h1 class="header">page shell must not be captured</h1>
      <canvas id="GameCanvas" width="640" height="360" style="width:320px;height:180px;display:block"></canvas>
      <script>
        const c = document.getElementById('GameCanvas'); const g = c.getContext('2d');
        g.fillStyle = '#cc2233'; g.fillRect(0, 0, 640, 360);
        g.fillStyle = '#22cc55'; g.fillRect(0, 0, 320, 180);
      </script></body></html>`);
    await new Promise((resolve) => setTimeout(resolve, 300));
    const outFile = path.join(outDir, 'canvas_selftest.png');
    const meta = await captureCanvas(page, outFile, { hideStats: false, statsApi: false });
    const { data } = await sharp(outFile).raw().toBuffer({ resolveWithObject: true });
    const center = (Math.floor(meta.output.height / 2) * meta.output.width + Math.floor(meta.output.width / 2)) * 4;
    const pixel = { r: data[center], g: data[center + 1], b: data[center + 2] };
    const result = {
      kind: 'p06_canvas_capture_selftest',
      metadata: meta,
      center_pixel: pixel,
      pixel_is_canvas_content: ((pixel.r > 150 && pixel.g < 100) || (pixel.g > 150 && pixel.r < 150)) && pixel.b < 120,
      page_shot_used: false,
      css_differs_from_backing: meta.css_rect.width !== meta.backing_width,
      meaning: 'Synthetic canvas only; proves canvas capture + metadata, not game visual approval.',
    };
    fs.writeFileSync(path.join(outDir, 'canvas_selftest.json'), JSON.stringify(result, null, 2) + '\n');
    return result;
  } finally {
    await browser.close();
  }
}

module.exports = { captureCanvas, collectCanvasInfo, selfTest, pngSize, sha256 };

if (require.main === module) {
  const args = process.argv.slice(2);
  const outIndex = args.indexOf('--out');
  const outDir = outIndex >= 0 ? args[outIndex + 1] : path.join(__dirname, '../../delivery/next_cycle/T0/_p06_canvas');
  selfTest(outDir).then((result) => {
    console.log(JSON.stringify(result));
    process.exit(result.pixel_is_canvas_content && result.metadata.output.width === result.metadata.backing_width ? 0 : 1);
  }).catch((error) => {
    console.error('CANVAS_SELFTEST_FATAL', error);
    process.exit(2);
  });
}
