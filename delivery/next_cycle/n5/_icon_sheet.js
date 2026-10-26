/**
 * Build an icon contact sheet so "same family at 24 px" can be judged by looking,
 * not by memory. Usage: node _icon_sheet.js <outDir> [tag]
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const DIR = process.env.ICON_DIR || 'C:/软件/鼠鼠/demo_n5/assets/resources/ui/icons';
const OUT = process.argv[2] || 'C:/软件/鼠鼠/delivery/next_cycle/n5/T5/ui';
const TAG = process.argv[3] || 'before';

const files = fs.readdirSync(DIR).filter((f) => f.endsWith('.png')).sort();

async function sheet(cell, cols, bg) {
  const rows = Math.ceil(files.length / cols);
  const pad = Math.round(cell * 0.22);
  const W = cols * (cell + pad) + pad;
  const H = rows * (cell + pad) + pad;
  const parts = [];
  for (let i = 0; i < files.length; i++) {
    const x = pad + (i % cols) * (cell + pad);
    const y = pad + Math.floor(i / cols) * (cell + pad);
    const buf = await sharp(path.join(DIR, files[i]))
      .resize(cell, cell, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png().toBuffer();
    parts.push({ input: buf, left: x, top: y });
  }
  return sharp({ create: { width: W, height: H, channels: 3, background: bg } })
    .composite(parts).png().toBuffer();
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const big = await sheet(96, 7, '#efe8da');
  const small = await sheet(24, 11, '#efe8da');
  fs.writeFileSync(path.join(OUT, `icons_${TAG}_96.png`), big);
  fs.writeFileSync(path.join(OUT, `icons_${TAG}_24.png`), small);
  console.log(JSON.stringify({ count: files.length, big: `icons_${TAG}_96.png`, small: `icons_${TAG}_24.png` }));
})();
