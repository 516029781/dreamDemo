/** Compose before/after pairs or a labeled grid for review evidence. */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const HEADER = 64;
const GAP = 8;
const CREAM = '#F2EFE6';

function labelSvg(width, height, text, sub = '') {
  return Buffer.from(`<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="${CREAM}"/>
    <text x="16" y="30" font-family="Segoe UI, sans-serif" font-size="22" fill="#2E3234">${text}</text>
    <text x="16" y="50" font-family="Segoe UI, sans-serif" font-size="13" fill="#6B655C">${sub}</text>
  </svg>`);
}

async function prepare(file, crop, targetWidth) {
  let pipeline = sharp(file);
  if (crop) pipeline = pipeline.extract(crop);
  if (targetWidth) pipeline = pipeline.resize({ width: targetWidth });
  const { data, info } = await pipeline.png().toBuffer({ resolveWithObject: true });
  return { data, width: info.width, height: info.height };
}

async function pair(before, after, out, labelA, labelB, crop) {
  const target = 900;
  const a = await prepare(before, crop, target);
  const b = await prepare(after, crop, target);
  const width = a.width + GAP + b.width;
  const height = Math.max(a.height, b.height) + HEADER + GAP;
  const canvas = sharp({ create: { width, height, channels: 3, background: CREAM } });
  await canvas.composite([
    { input: labelSvg(a.width, HEADER, labelA), left: 0, top: 0 },
    { input: labelSvg(b.width, HEADER, labelB), left: a.width + GAP, top: 0 },
    { input: a.data, left: 0, top: HEADER },
    { input: b.data, left: a.width + GAP, top: HEADER },
  ]).png().toFile(out);
  console.log(JSON.stringify({ out, width, height }));
}

async function grid(out, title, items) {
  const target = 620;
  const prepared = [];
  for (const item of items) prepared.push({ ...(await prepare(item.file, item.crop, target)), label: item.label });
  const cols = 2;
  const rows = Math.ceil(prepared.length / cols);
  const cellW = Math.max(...prepared.map((p) => p.width));
  const cellH = Math.max(...prepared.map((p) => p.height)) + HEADER;
  const width = cols * cellW + (cols + 1) * GAP;
  const height = HEADER + rows * cellH + (rows + 1) * GAP;
  const composites = [{ input: labelSvg(width, HEADER, title), left: 0, top: 0 }];
  prepared.forEach((p, i) => {
    const x = GAP + (i % cols) * (cellW + GAP);
    const y = HEADER + GAP + Math.floor(i / cols) * (cellH + GAP);
    composites.push({ input: labelSvg(cellW, HEADER, p.label), left: x, top: y });
    composites.push({ input: p.data, left: x, top: y + HEADER });
  });
  await sharp({ create: { width, height, channels: 3, background: CREAM } })
    .composite(composites).png().toFile(out);
  console.log(JSON.stringify({ out, width, height }));
}

(async () => {
  const mode = process.argv[2];
  if (mode === 'pair') {
    const [, , , before, after, out, labelA, labelB, cropRaw] = process.argv;
    const crop = cropRaw ? Object.fromEntries(cropRaw.split(',').map((v, i) => [['left', 'top', 'width', 'height'][i], Number(v)])) : null;
    await pair(before, after, out, labelA, labelB, crop);
  } else if (mode === 'grid') {
    const [, , , out, title, ...rest] = process.argv;
    const items = [];
    for (let i = 0; i < rest.length; i += 2) items.push({ file: rest[i], label: rest[i + 1] });
    await grid(out, title, items);
  } else {
    console.error('usage: pair <before> <after> <out> <labelA> <labelB> [left,top,w,h] | grid <out> <title> <img1> <label1> ...');
    process.exit(2);
  }
})().catch((error) => { console.error('COMPOSE_FATAL', error); process.exit(2); });
