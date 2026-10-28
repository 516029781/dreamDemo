/**
 * Build the look-dev contact sheet: reference frame on top, the three variant
 * renders underneath at identical size, so the choice is made on one image.
 *
 * Usage: node _variant_sheet.js
 */
const fs = require('fs');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const DIR = 'C:/软件/鼠鼠/delivery/next_cycle/n5/T5/variants';
const REF = 'C:/软件/鼠鼠/reference/_raw_screenshots/P1/t015s.jpg';
const BENCH = JSON.parse(fs.readFileSync('C:/软件/鼠鼠/planning/art/ART_VARIANTS.json', 'utf8')).variants;

const TAG_H = 34;
const CAP_H = 26;

function bar(w, h, text, bg, fg, size) {
  const svg = `<svg width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="${bg}"/>
    <text x="12" y="${h / 2 + size * 0.36}" fill="${fg}" font-family="Microsoft YaHei, sans-serif" font-size="${size}">${text}</text>
  </svg>`;
  return Buffer.from(svg);
}

(async () => {
  const tags = ['A', 'B', 'C'].filter((t) => fs.existsSync(`${DIR}/variant_${t}_no_ui.png`));
  if (!tags.length) throw new Error('no variant shots yet');

  const REF_W = 1180, REF_H = Math.round(REF_W * 9 / 16);
  const V_W = 620, V_H = Math.round(V_W * 9 / 16);
  const pad = 14;

  const refBuf = await sharp(REF).resize(REF_W, REF_H, { fit: 'cover' }).png().toBuffer();
  const comps = [];
  let y = pad;

  comps.push({ input: bar(REF_W, TAG_H, '参考 t015 · 目标观感（同区域实测：树冠 L40 S16 / 铺地 H27 / 草 H20 S25）',
                          '#231b13', '#f6f1e6', 60 * 0.35), left: pad, top: y });
  y += TAG_H;
  comps.push({ input: refBuf, left: pad, top: y });
  y += REF_H + pad + 6;

  const rowW = tags.length * V_W + (tags.length - 1) * pad;
  tags.forEach((tag, i) => {
    const x = pad + i * (V_W + pad);
    const cfg = BENCH[tag] || {};
    comps.push({ input: bar(V_W, TAG_H, `${tag} · ${cfg.label || ''}`, '#231b13', '#f6f1e6', 15),
                 left: x, top: y });
  });
  const capY = y + TAG_H;
  tags.forEach((tag, i) => {
    const x = pad + i * (V_W + pad);
    comps.push({ input: bar(V_W, CAP_H,
      `叶 ×${(BENCH[tag] || {}).leaf_scale ?? '?'} · 数量 ×${(BENCH[tag] || {}).leaf_count_scale ?? '?'} · 草宽 ×${(BENCH[tag] || {}).grass_width ?? '?'} · 铺地 ${(BENCH[tag] || {}).paving_unify ? '统一大板' : '分级'}`,
      '#3a2f24', '#d9cdb8', 13), left: x, top: capY });
  });
  const imgY = capY + CAP_H;
  for (let i = 0; i < tags.length; i++) {
    const tag = tags[i];
    const buf = await sharp(`${DIR}/variant_${tag}_no_ui.png`)
      .resize(V_W, V_H, { fit: 'cover' }).png().toBuffer();
    comps.push({ input: buf, left: pad + i * (V_W + pad), top: imgY });
  }

  const totalH = imgY + V_H + pad;
  const totalW = Math.max(REF_W, rowW) + pad * 2;
  await sharp({ create: { width: totalW, height: totalH, channels: 3, background: '#e9e2d4' } })
    .composite(comps).png().toFile(`${DIR}/variants_sheet.png`);
  console.log('sheet ok ' + totalW + 'x' + totalH + ' tags=' + tags.join(','));
})();
