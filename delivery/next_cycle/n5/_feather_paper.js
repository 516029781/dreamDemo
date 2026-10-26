/**
 * Feather the paper sheet's alpha edge.
 *
 * A nine-slice stretch keeps the 1px-wide border strip's alpha profile, so a
 * feathered edge survives stretching while a torn silhouette does not. Feathering
 * is therefore the only edge treatment that reads as "a sheet lying on the scene"
 * at every panel size.
 *
 * The sheet is 512x256 with a 44 px inset, so a 10 px feather stays inside the
 * border strip and never touches the nine-slice centre.
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const SRC = 'C:/软件/鼠鼠/demo_n5/assets/resources/ui/paper_panel_wash.png';
const FEATHER = 10;   // px of alpha ramp from the outer edge inward
const EDGE_TINT = 0.965; // how much darker the last 30 px of paper reads

(async () => {
  const { data, info } = await sharp(SRC).raw().toBuffer({ resolveWithObject: true });
  const { width: w, height: h, channels: ch } = info;
  if (ch !== 4) throw new Error('expected RGBA, got ' + ch);

  const smooth = (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t * t * (3 - 2 * t));
  const out = Buffer.from(data);
  for (let y = 0; y < h; y++) {
    const dy = Math.min(y, h - 1 - y);
    for (let x = 0; x < w; x++) {
      const dx = Math.min(x, w - 1 - x);
      const d = Math.min(dx, dy);
      const i = (y * w + x) * ch;
      // alpha ramp
      const k = smooth(d / FEATHER);
      out[i + 3] = Math.round(data[i + 3] * k);
      // a slight inward darkening so the sheet has a lip instead of a cut edge
      const t = smooth(Math.min(1, d / 30));
      const g = EDGE_TINT + (1 - EDGE_TINT) * t;
      out[i] = Math.round(data[i] * g);
      out[i + 1] = Math.round(data[i + 1] * g);
      out[i + 2] = Math.round(data[i + 2] * g);
    }
  }
  const buf = await sharp(out, { raw: { width: w, height: h, channels: 4 } }).png().toBuffer();
  fs.writeFileSync(SRC, buf);
  console.log(JSON.stringify({ feather: FEATHER, size: `${w}x${h}`, bytes: buf.length }));
})();
