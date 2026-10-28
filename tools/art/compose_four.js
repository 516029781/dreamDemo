/**
 * Contact sheet: the three look directions next to the reference frame.
 *
 * Usage: node tools/art/compose_four.js [outPath] [stampJson]
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const ROOT = 'C:/软件/鼠鼠';
const BASE = path.join(ROOT, 'delivery/next_cycle/n5/T5/styles');
const REF = path.join(ROOT, 'reference/_raw_screenshots/P1/t015s.jpg');
const OUT = process.argv[2] || path.join(ROOT, 'delivery/next_cycle/n5/T5/ui/styles_three.png');

const W = 620, H = 349, PAD = 12, LAB = 30;

const panels = [
  ['O', 'O 自有程序化 · 大板铺地 + 浅色叶'],
  ['C', 'C 卡通低模 · 圆冠团块 + 平涂'],
  ['R', 'R 写实贴图 · 叶图集 alpha 裁剪'],
  [null, '参考图 · 目标'],
];

function labeler(text, size = 15) {
  return Buffer.from(
    '<svg width="' + W + '" height="' + LAB + '" xmlns="http://www.w3.org/2000/svg">' +
    '<rect width="100%" height="100%" fill="#1d1812"/>' +
    '<text x="10" y="' + (LAB / 2 + size * 0.36) + '" fill="#f4eee2" ' +
    'font-family="Microsoft YaHei, sans-serif" font-size="' + size + '">' + text + '</text>' +
    '</svg>');
}

(async () => {
  const report = {};
  try {
    const dir = path.join(ROOT, 'delivery/performance');
    const files = fs.readdirSync(dir).filter((f) => /^three_styles_.*\.json$/.test(f)).sort();
    if (files.length) {
      const data = JSON.parse(fs.readFileSync(path.join(dir, files[files.length - 1]), 'utf8'));
      for (const v of data.variants) {
        if (v.glb) report[v.tag] = Math.round(v.glb.triangles / 1000) + 'k tri · ' +
          v.glb.mb.toFixed(1) + ' MB';
      }
    }
  } catch (e) { /* sheet still renders without sizes */ }

  const tiles = [];
  for (const [tag, text] of panels) {
    const src = tag ? path.join(BASE, tag, 'variant_' + tag + '_no_ui.png') : REF;
    if (!fs.existsSync(src)) continue;
    const img = await sharp(src).resize(W, H, { fit: 'cover' }).png().toBuffer();
    const cap = labeler(tag && report[tag] ? text + '   ' + report[tag] : text);
    tiles.push({ img, cap });
  }

  const cols = 2;
  const rows = Math.ceil(tiles.length / cols);
  const sheetW = cols * W + (cols + 1) * PAD;
  const sheetH = rows * (H + LAB) + (rows + 1) * PAD;
  const comps = [];
  tiles.forEach((t, i) => {
    const cx = PAD + (i % cols) * (W + PAD);
    const cy = PAD + Math.floor(i / cols) * (H + LAB + PAD);
    comps.push({ input: t.cap, left: cx, top: cy });
    comps.push({ input: t.img, left: cx, top: cy + LAB });
  });
  await sharp({ create: { width: sheetW, height: sheetH, channels: 3, background: '#14100c' } })
    .composite(comps).png().toFile(OUT);
  console.log('sheet ' + OUT + '  ' + sheetW + 'x' + sheetH);
})();
