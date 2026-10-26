const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

// Tone report for the formal camera: how many distinct luminance steps the
// frame actually uses, and how much of it is crushed into the highlights.
// The rework spec asks for "grey >= 9 steps"; this counts 16-level bins that
// hold at least 0.5% of the pixels, which is the stricter reading.

async function tone(file) {
  const { data, info } = await sharp(file).raw().toBuffer({ resolveWithObject: true });
  const ch = info.channels;
  const bins = new Array(16).fill(0);
  let n = 0;
  let sum = 0;
  let sum2 = 0;
  let blown = 0;
  let dark = 0;
  for (let i = 0; i < data.length; i += ch) {
    const l = 0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2];
    bins[Math.min(15, Math.floor(l / 16))]++;
    sum += l;
    sum2 += l * l;
    if (l >= 240) blown++;
    if (l <= 24) dark++;
    n++;
  }
  const mean = sum / n;
  const sd = Math.sqrt(sum2 / n - mean * mean);
  const used = bins.filter((c) => c / n >= 0.005).length;
  return {
    file: path.basename(file),
    mean: +mean.toFixed(1),
    sd: +sd.toFixed(1),
    steps_used: used,
    near_white_pct: +((100 * blown) / n).toFixed(1),
    near_black_pct: +((100 * dark) / n).toFixed(1),
    hist: bins.map((c) => +(100 * c / n).toFixed(1)),
  };
}

(async () => {
  const files = process.argv.slice(2);
  for (const f of files) {
    console.log(JSON.stringify(await tone(f)));
  }
})();
