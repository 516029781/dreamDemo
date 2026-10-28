/**
 * Crop a region out of a screenshot and normalise it to a fixed pixel size so
 * image_metrics numbers are comparable between the 1920x1078 reference frame
 * and our 1280x720 capture.
 *
 * Usage:
 *   node tools/art/region_crop.js <outDir> <label> <path> <x,y,w,h> [...]
 * Writes <outDir>/<label>.png at 300x150 and prints the path.
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const W = 300, H = 150;

(async () => {
  const [outDir, ...rest] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  // Groups of three: label, path, box
  for (let i = 0; i + 2 < rest.length; i += 3) {
    const [label, file, boxStr] = [rest[i], rest[i + 1], rest[i + 2]];
    const [left, top, width, height] = boxStr.split(',').map(Number);
    const dst = path.join(outDir, label + '.png');
    const meta = await sharp(file).metadata();
    const l = Math.max(0, Math.min(left, meta.width - 2));
    const t = Math.max(0, Math.min(top, meta.height - 2));
    const w = Math.min(width, meta.width - l);
    const h = Math.min(height, meta.height - t);
    await sharp(file).extract({ left: l, top: t, width: w, height: h })
      .resize(W, H, { fit: 'fill' }).png().toFile(dst);
    console.log(dst + '  from ' + path.basename(file) + ' [' + [l, t, w, h].join(',') + ']');
  }
})().catch((e) => { console.error(e); process.exit(1); });
