/**
 * Leaf-cluster atlas for the realistic pass.
 *
 * The card geometry is a 4-triangle diamond; without an alpha cutout its
 * silhouette is a diamond, which is exactly the "solid blob" complaint. This
 * atlas gives every card a lobed-leaf cluster so the *edge* reads as foliage.
 *
 * Layout must match courtyard_lib.add_leaf(): 4 columns x 2 rows, u in
 * (col*0.5 .. +1)/4, v in (row*0.5 .. +1)/2, content filling the cell.
 *
 * Usage: node tools/art/make_leaf_atlas.js [outPath]
 */
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const W = 1024, H = 512, COLS = 4, ROWS = 2;
const CW = W / COLS, CH = H / ROWS;

// Restrained golden autumn palette sampled from the locked P1 whole-scene frame.
// Keep leaves matte and low contrast so the canopy reads as foliage at game scale.
const PALETTES = [
  ['#C9A96D', '#E0C486', '#A98752'],
  ['#B99A66', '#D5B679', '#9B7B4C'],
  ['#D1B477', '#E8D091', '#AD8D59'],
  ['#B78D5B', '#D0AD74', '#957344'],
  ['#C5A36A', '#DEC184', '#A1814E'],
  ['#D0B583', '#E8D49C', '#AA8B60'],
  ['#BE9E6C', '#D8B87D', '#9A7B4D'],
  ['#B99765', '#D3B274', '#927143'],
];

function mulberry(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** One lobed leaf as an SVG path, drawn around (0,0), radius ~1. */
function leafPath(_lobes, seedRnd) {
  const pts = [];
  const N = 72;
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    const a = -Math.PI / 2 + t * Math.PI * 2;
    // Pointed, softly uneven almond leaf; no maple-star lobes or cartoon outline.
    const side = Math.pow(Math.abs(Math.sin(a)), 0.72);
    let r = 0.12 + 0.88 * side;
    r *= 1 + 0.035 * Math.sin(a * 3 + seedRnd * 6.28);
    pts.push([Math.cos(a) * r * 0.50, Math.sin(a) * r]);
  }
  return pts;
}

function cellSvg(idx, rnd) {
  const pal = PALETTES[idx % PALETTES.length];
  const parts = [];
  const n = 8 + Math.floor(rnd() * 4);
  for (let k = 0; k < n; k++) {
    const cx = CW * 0.5 + (rnd() - 0.5) * CW * 0.52;
    const cy = CH * 0.5 + (rnd() - 0.5) * CH * 0.52;
    const rad = CH * (0.22 + rnd() * 0.12);
    const rot = rnd() * 360;
    const pts = leafPath(5, rnd());
    const d = 'M' + pts.map(p => `${(p[0] * rad).toFixed(2)},${(p[1] * rad).toFixed(2)}`).join('L') + 'Z';
    const c1 = pal[k % pal.length];
    const c2 = pal[(k + 1) % pal.length];
    const gid = `g${idx}_${k}`;
    parts.push(
      `<defs><linearGradient id="${gid}" x1="0" y1="0" x2="0.3" y2="1">` +
      `<stop offset="0" stop-color="${c1}"/><stop offset="1" stop-color="${c2}"/></linearGradient></defs>` +
      `<g transform="translate(${cx.toFixed(1)},${cy.toFixed(1)}) rotate(${rot.toFixed(1)})">` +
      `<path d="${d}" fill="url(#${gid})" stroke="${c2}" stroke-width="${(rad * 0.012).toFixed(2)}" stroke-opacity="0.20"/>` +
      `<path d="M0,${(-rad * 0.9).toFixed(2)} L0,${(rad * 1.05).toFixed(2)}" stroke="#E4D2A7" stroke-width="${(rad * 0.014).toFixed(2)}" opacity="0.26"/>` +
      `</g>`
    );
  }
  return parts.join('');
}

(async () => {
  const out = process.argv[2] || 'C:/软件/鼠鼠/demo_n5/assets/resources/textures/tex_leaf_atlas/texture.png';
  const comps = [];
  for (let idx = 0; idx < COLS * ROWS; idx++) {
    const col = idx % COLS, row = Math.floor(idx / COLS);
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${CW}" height="${CH}">${cellSvg(idx, mulberry(1701 + idx * 37))}</svg>`;
    const buf = await sharp(Buffer.from(svg)).png().toBuffer();
    // 8px bleed guard: a card samples the middle of the cell, so keep content
    // off the seams or neighbouring cells leak in.
    comps.push({ input: buf, left: col * CW, top: row * CH });
  }
  await sharp({ create: { width: W, height: H, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } })
    .composite(comps)
    .png({ compressionLevel: 9 })
    .toFile(out);
  const st = require('fs').statSync(out);
  console.log('atlas written ' + out + ' ' + W + 'x' + H + ' ' + (st.size / 1024).toFixed(0) + ' KB');
})();
