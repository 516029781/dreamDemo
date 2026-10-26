/**
 * Measure the two UI numbers the rework spec asks for, instead of eyeballing them:
 *  - dialogue paper panel height as a share of the 720 design height (spec target 24-27%)
 *  - how much of the frame the HUD occupies
 */
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const ROOT = 'C:/软件/鼠鼠/delivery/next_cycle/n5/T5';

async function load(name) {
  const p = path.join(ROOT, name);
  const { data, info } = await sharp(p).raw().toBuffer({ resolveWithObject: true });
  return { data, w: info.width, h: info.height, ch: info.channels };
}

/** paper = bright, warm-neutral, no dark component: min>165, max-min<45 */
function isPaper(r, g, b) {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b);
  return mx > 195 && mn > 165 && mx - mn < 45;
}

(async () => {
  const out = {};
  for (const name of ['q01_dialogue.png', 'q01_formal_ui.png', 'q01_formal_no_ui.png']) {
    const { data, w, h, ch } = await load(name);
    const rowShare = new Array(h).fill(0);
    let paperTotal = 0;
    for (let y = 0; y < h; y++) {
      let c = 0;
      for (let x = 0; x < w; x++) {
        const i = (y * w + x) * ch;
        if (isPaper(data[i], data[i + 1], data[i + 2])) { c++; paperTotal++; }
      }
      rowShare[y] = c / w;
    }
    // panel top: highest row (smallest y) in the contiguous bottom band where >55% is paper
    let top = null;
    for (let y = h - 1; y >= 0; y--) {
      if (rowShare[y] > 0.55) top = y;
      else if (top !== null && y < top - 8) break;
    }
    out[name] = {
      size: `${w}x${h}`,
      panel_top_y: top,
      panel_height_px: top === null ? null : h - top,
      panel_share_pct: top === null ? null : +(((h - top) / h) * 100).toFixed(1),
      paper_pixels_pct: +((paperTotal / (w * h)) * 100).toFixed(2),
    };
  }
  console.log(JSON.stringify(out, null, 2));
})();
