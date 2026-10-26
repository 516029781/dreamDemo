/**
 * V04/F07: measure fixed ROIs on two same-camera images.
 * Reports absolute sRGB luminance, per-ROI contrast, and shadow/lit values.
 * A ratio alone is never interpreted as "brighter"; absolute values are separate.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const [beforePath, afterPath, outPath] = process.argv.slice(2);
if (!beforePath || !afterPath || !outPath) {
  console.error('usage: node tools/measure_lighting.js <before.png> <after.png> <out.json>');
  process.exit(2);
}

const ROIS = {
  paving_lit: { x: 700, y: 430, w: 220, h: 90 },
  paving_shadow: { x: 300, y: 520, w: 150, h: 80 },
  soil_bed: { x: 980, y: 300, w: 120, h: 55 },
  tree_crown: { x: 400, y: 45, w: 220, h: 120 },
  metal_fence: { x: 1120, y: 120, w: 90, h: 70 },
};

function sha256(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

async function stats(file) {
  const { data, info } = await sharp(file).raw().toBuffer({ resolveWithObject: true });
  const result = { file, sha256: sha256(file), width: info.width, height: info.height, rois: {} };
  for (const [name, roi] of Object.entries(ROIS)) {
    let sum = 0, sumSq = 0, count = 0, rs = 0, gs = 0, bs = 0;
    const values = [];
    for (let y = roi.y; y < roi.y + roi.h; y++) {
      for (let x = roi.x; x < roi.x + roi.w; x++) {
        const i = (y * info.width + x) * info.channels;
        const r = data[i], g = data[i + 1], b = data[i + 2];
        const luma = 0.2126 * r + 0.7152 * g + 0.0722 * b;
        values.push(luma);
        sum += luma; sumSq += luma * luma; rs += r; gs += g; bs += b; count++;
      }
    }
    const mean = sum / count;
    const variance = Math.max(0, sumSq / count - mean * mean);
    values.sort((a, b) => a - b);
    result.rois[name] = {
      mean_srgb_luma: +mean.toFixed(2),
      contrast_stddev: +Math.sqrt(variance).toFixed(2),
      p05: +values[Math.floor(values.length * 0.05)].toFixed(2),
      p95: +values[Math.floor(values.length * 0.95)].toFixed(2),
      mean_rgb: [+(rs / count).toFixed(1), +(gs / count).toFixed(1), +(bs / count).toFixed(1)],
    };
  }
  return result;
}

(async () => {
  const before = await stats(beforePath);
  const after = await stats(afterPath);
  const deltas = {};
  for (const name of Object.keys(ROIS)) {
    deltas[name] = {
      delta_mean_luma: +(after.rois[name].mean_srgb_luma - before.rois[name].mean_srgb_luma).toFixed(2),
      before_contrast: before.rois[name].contrast_stddev,
      after_contrast: after.rois[name].contrast_stddev,
    };
  }
  const beforeShadowRatio = before.rois.paving_shadow.mean_srgb_luma / before.rois.paving_lit.mean_srgb_luma;
  const afterShadowRatio = after.rois.paving_shadow.mean_srgb_luma / after.rois.paving_lit.mean_srgb_luma;
  const report = {
    kind: 'fixed_roi_lighting_measurement',
    generated_at: new Date().toISOString(),
    method: 'mean sRGB luma (0.2126R+0.7152G+0.0722B) per fixed ROI; no auto-exposure, same 1280x720 camera',
    camera: 'engine formal camera fov=35 pos=(-2.5,11.5,-14.6); scene ROIs, clip_time=null',
    clip_time: null,
    note: 'Absolute luminance and per-ROI contrast are reported separately. Shadow/lit ratio alone is not evidence of "brighter"; ROI means mix material and geometry.',
    before,
    after,
    deltas,
    shadow_lit_ratio: {
      before: +beforeShadowRatio.toFixed(3),
      after: +afterShadowRatio.toFixed(3),
      interpretation: 'Ratio compares shadow ROI to lit paving; use with the absolute values above, not as a standalone brightness claim.',
    },
    limitations: 'Human visual review still decides whether contrast and contact shadows match P1.',
  };
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ out: outPath, deltas, shadow_lit_ratio: report.shadow_lit_ratio }));
})().catch((error) => { console.error('LIGHTING_MEASURE_FATAL', error); process.exit(2); });
