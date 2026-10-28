/**
 * Stitch the three look directions into one comparison sheet.
 *
 * Usage: node tools/art/compose_styles.js [outPath]
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const ROOT = 'C:/软件/鼠鼠';
const BASE = path.join(ROOT, 'delivery/next_cycle/n5/T5/styles');
const OUT = process.argv[2] || path.join(ROOT, 'delivery/next_cycle/n5/T5/ui/styles_three.png');

const TAGS = [
  ['O', 'O 自有程序化（现状技术）', '#2b2117'],
  ['C', 'C 卡通低模', '#2b2117'],
  ['R', 'R 写实贴图', '#2b2117'],
];

const W = 620, H = 349, PAD = 10, LAB = 34;

function bar(w, text, bg = '#231b13', fg = '#f6f1e6', size = 16) {
  return Buffer.from(
    `<svg width="${w}" height="${LAB}" xmlns="http://www.w3.org/2000/svg">` +
    `<rect width="100%" height="100%" fill="${bg}"/>` +
    `<text x="12" y="${LAB / 2 + size * 0.36}" fill="${fg}" ` +
    `font-family="Microsoft YaHei, sans-serif" font-size="${size}">${text}</text></svg>`
  );
}

// Newest three_styles report, so the sheet can print the real build size.
let REPORT = null;
try {
  const rep = path.join(ROOT, 'delivery/performance');
  const files = fs.readdirSync(rep).filter((f) => /^three_styles_.*\.json$/.test(f)).sort();
  if (files.length) {
    const data = JSON.parse(fs.readFileSync(path.join(rep, files[files.length - 1]), 'utf8'));
    REPORT = {};
    for (const v of data.variants) REPORT[v.tag] = v;
  }
} catch (e) { REPORT = null; }

(async () => {
  const comps = [];
  let missing = [];
  for (let i = 0; i < TAGS.length; i++) {
    const [tag, label] = TAGS[i];
    const file = path.join(BASE, tag, `variant_${tag}_no_ui.png`);
    if (!fs.existsSync(file)) { missing.push(file); continue; }
    const x = PAD + i * (W + PAD);
    comps.push({ input: bar(W, label), left: x, top: PAD });
    comps.push({
      input: await sharp(file).resize(W, H, { fit: 'cover' }).png().toBuffer(),
      left: x, top: PAD + LAB,
    });
    const glb = (REPORT && REPORT[tag] && REPORT[tag].glb) || {};
    const note = `${glb.mb ? glb.mb + ' MB' : ''}${glb.triangles ? ' · ' + glb.triangles.toLocaleString() + ' tris' : ''}`;
    if (note.trim()) {
      comps.push({ input: bar(W, note, '#3a2e22', '#e8dcc6', 14), left: x, top: PAD + LAB + H });
    }
  }
  if (missing.length) console.log('missing:\n' + missing.join('\n'));

  const height = PAD + LAB + H + LAB + PAD;
  await sharp({
    create: { width: PAD + TAGS.length * (W + PAD), height, channels: 3, background: '#e9e2d4' },
  }).composite(comps).png().toFile(OUT);
  console.log('sheet ' + OUT);
})();
