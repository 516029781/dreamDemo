/**
 * Normalise a detail texture's mean value without touching its pattern.
 *
 * tex_leaf_detail.png had a mean of 125/255 (0.49). It is used as the albedo
 * map for every leaf, flag and grass blade, so it multiplied all of them by
 * ~0.5 before the per-material colour was even applied - which is why the
 * leaves could never be made light, no matter what colour they were given.
 * This rescales the map around its own mean to a target mean and leaves the
 * contrast structure intact.
 *
 * Usage: node tools/art/normalize_texture.js <file> <targetMean> [contrast]
 *   contrast 1.0 keeps the original spread (default), <1 flattens it.
 */
const fs = require('fs');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const [file, meanArg, contrastArg] = process.argv.slice(2);
if (!file || !meanArg) {
  console.error('usage: normalize_texture.js <file> <targetMean> [contrast]');
  process.exit(2);
}
const target = Number(meanArg);
const contrast = contrastArg ? Number(contrastArg) : 1.0;

(async () => {
  const { data, info } = await sharp(file).removeAlpha().raw()
    .toBuffer({ resolveWithObject: true });
  const ch = info.channels;
  const n = info.width * info.height;
  let sum = 0;
  for (let i = 0; i < data.length; i += ch) {
    sum += (data[i] + data[i + 1] + data[i + 2]) / 3;
  }
  const mean = sum / n;
  const out = Buffer.alloc(data.length);
  for (let i = 0; i < data.length; i += ch) {
    for (let c = 0; c < 3; c++) {
      const v = target + (data[i + c] - mean) * contrast;
      out[i + c] = Math.max(0, Math.min(255, Math.round(v)));
    }
  }
  const tmp = file + '.tmp.png';
  await sharp(out, { raw: { width: info.width, height: info.height, channels: ch } })
    .png({ compressionLevel: 9 }).toFile(tmp);
  fs.renameSync(tmp, file);
  console.log(file + ' mean ' + mean.toFixed(1) + ' -> ' + target +
              ' (contrast x' + contrast + ')');
})().catch((e) => { console.error(e); process.exit(1); });
