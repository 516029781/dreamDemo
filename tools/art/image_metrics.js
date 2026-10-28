/**
 * Objective look-dev metrics: the same measurements on the reference frame and
 * on our render, so "looks wrong" becomes a number we can chase.
 *
 * Measures, per region:
 *   edgeDensity  share of pixels with a Sobel gradient above threshold (reads as
 *                "how busy / how fine-grained" the surface is)
 *   lum P10/P50/P90, saturation mean       (value + chroma)
 *   valueBands   share of pixels in dark / mid / light bands
 * plus, where meaningful:
 *   gapShare     tree crowns only: flat + bright/desaturated pixels seen through
 *                the canopy (sky and far background behind the leaves)
 *   mortar       paving only: median joint width in px and joint/face contrast
 *
 * Usage: node tools/art/image_metrics.js <out.json> <label>:<path>:<region> ...
 * Region is one of: tree | grass | paving | frame
 */
const fs = require('fs');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const REGIONS = {
  tree: null, grass: null, paving: null, frame: null,
};

function lum(r, g, b) { return 0.299 * r + 0.587 * g + 0.114 * b; }
function sat(r, g, b) {
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b);
  return mx === 0 ? 0 : (mx - mn) / mx;
}
function pct(arr, p) { return arr[Math.min(arr.length - 1, Math.floor(arr.length * p))]; }

function analyse(data, w, h, channels, region) {
  const gray = new Float32Array(w * h);
  const sats = new Float32Array(w * h);
  for (let i = 0, p = 0; i < w * h; i++, p += channels) {
    gray[i] = lum(data[p], data[p + 1], data[p + 2]);
    sats[i] = sat(data[p], data[p + 1], data[p + 2]);
  }
  const sorted = Array.from(gray).sort((a, b) => a - b);
  const p10 = pct(sorted, 0.10), p50 = pct(sorted, 0.50), p90 = pct(sorted, 0.90);
  let sSum = 0;
  for (let i = 0; i < w * h; i++) sSum += sats[i];

  // Sobel magnitude, interior pixels only.
  let edge = 0, interior = 0;
  const grad = new Float32Array(w * h);
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const i = y * w + x;
      const gx = -gray[i - w - 1] - 2 * gray[i - 1] - gray[i + w - 1]
               + gray[i - w + 1] + 2 * gray[i + 1] + gray[i + w + 1];
      const gy = -gray[i - w - 1] - 2 * gray[i - w] - gray[i - w + 1]
               + gray[i + w - 1] + 2 * gray[i + w] + gray[i + w + 1];
      const m = Math.sqrt(gx * gx + gy * gy) / 4;
      grad[i] = m;
      interior++;
      if (m > 22) edge++;
    }
  }

  let dark = 0, mid = 0, light = 0;
  for (let i = 0; i < w * h; i++) {
    if (gray[i] < 30 * 2.55) dark++;
    else if (gray[i] < 55 * 2.55) mid++;
    else light++;
  }
  const out = {
    edgeDensity: +(100 * edge / Math.max(1, interior)).toFixed(2),
    lumP10: Math.round(p10), lumP50: Math.round(p50), lumP90: Math.round(p90),
    lumMean: +(Array.from(gray).reduce((a, b) => a + b, 0) / (w * h)).toFixed(1),
    satMean: +(100 * sSum / (w * h)).toFixed(1),
    bandDark: +(100 * dark / (w * h)).toFixed(1),
    bandMid: +(100 * mid / (w * h)).toFixed(1),
    bandLight: +(100 * light / (w * h)).toFixed(1),
  };

  if (region === 'tree') {
    // Canopy gaps: flat neighbourhood + (bright or desaturated) => seen-through.
    let gap = 0;
    for (let i = 0; i < w * h; i++) {
      const flat = grad[i] > 0 ? grad[i] < 6 : true;
      if (flat && (gray[i] > p90 * 0.92 || sats[i] < 0.10)) gap++;
    }
    out.gapShare = +(100 * gap / (w * h)).toFixed(1);
  }

  if (region === 'paving') {
    // Joint width: on each row, dark runs shorter than 14 px are joints.
    const widths = [];
    const contrasts = [];
    for (let y = 2; y < h - 2; y += 2) {
      let rowMean = 0;
      for (let x = 0; x < w; x++) rowMean += gray[y * w + x];
      rowMean /= w;
      let run = 0, runSum = 0;
      for (let x = 0; x < w; x++) {
        const i = y * w + x;
        if (grad[i] > 8 && gray[i] < rowMean - 4) { run++; runSum += gray[i]; }
        else {
          if (run >= 1 && run <= 14) { widths.push(run); contrasts.push(rowMean - runSum / run); }
          run = 0; runSum = 0;
        }
      }
    }
    widths.sort((a, b) => a - b);
    contrasts.sort((a, b) => a - b);
    out.jointWidthPx = widths.length ? +pct(widths, 0.5).toFixed(1) : null;
    out.jointContrast = contrasts.length ? +pct(contrasts, 0.5).toFixed(1) : null;
    out.jointSamples = widths.length;
  }
  return out;
}

(async () => {
  const outPath = process.argv[2];
  const jobs = process.argv.slice(3).map((s) => {
    const [label, path, region, box] = s.split('|');
    return { label, path, region, box };
  });
  const result = { generated_at: new Date().toISOString(), runs: [] };
  for (const job of jobs) {
    const img = sharp(job.path);
    const meta = await img.metadata();
    let box = { left: 0, top: 0, width: meta.width, height: meta.height };
    if (job.box) {
      const [left, top, width, height] = job.box.split(',').map(Number);
      box = { left, top, width, height };
    }
    const { data, info } = await sharp(job.path)
      .extract(box).removeAlpha().raw().toBuffer({ resolveWithObject: true });
    const metrics = analyse(data, info.width, info.height, info.channels, job.region);
    result.runs.push({ label: job.label, region: job.region, size: [info.width, info.height], ...metrics });
    console.log(job.label.padEnd(22), job.region.padEnd(7), JSON.stringify(metrics));
  }
  fs.writeFileSync(outPath, JSON.stringify(result, null, 2) + '\n');
})();
