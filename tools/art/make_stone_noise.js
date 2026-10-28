/**
 * Generate a seamless stone detail map with NO grout grid.
 *
 * Why this exists: tex_stone_tiles.png is a 4x4 atlas of stone cells separated
 * by light grout lines. Tiled onto slab top faces it painted a second, much
 * finer grid on top of the geometry joints - which is what read as "white
 * lines on the flagstones" and "the paving tiles are all different sizes".
 * Slabs only need mottling and grain; the joints are already geometry.
 *
 * Usage: node tools/art/make_stone_noise.js [outPath]
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const ROOT = 'C:/软件/鼠鼠';
const OUT = process.argv[2] ||
  path.join(ROOT, 'demo_n5/assets/resources/textures/tex_stone_noise.png');
const SIZE = 512;

function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const smooth = (t) => t * t * (3 - 2 * t);

/** Periodic value noise: lattices wrap at `freq`, so the tile is seamless. */
function periodic(freq, seed, size) {
  const rnd = mulberry32(seed);
  const g = new Float32Array(freq * freq);
  for (let i = 0; i < g.length; i++) g[i] = rnd();
  const out = new Float32Array(size * size);
  for (let y = 0; y < size; y++) {
    const fy = (y / size) * freq;
    const y0 = Math.floor(fy) % freq;
    const y1 = (y0 + 1) % freq;
    const ty = smooth(fy - Math.floor(fy));
    for (let x = 0; x < size; x++) {
      const fx = (x / size) * freq;
      const x0 = Math.floor(fx) % freq;
      const x1 = (x0 + 1) % freq;
      const tx = smooth(fx - Math.floor(fx));
      const a = g[y0 * freq + x0], b = g[y0 * freq + x1];
      const c = g[y1 * freq + x0], d = g[y1 * freq + x1];
      const top = a + (b - a) * tx;
      const bot = c + (d - c) * tx;
      out[y * size + x] = top + (bot - top) * ty;
    }
  }
  return out;
}

// Octaves: coarse mottling, medium cloudiness, fine grain. Amplitudes are in
// 0-255 units of the final pixel; total stays under ~14 so the slab reads as
// one flat stone rather than a noisy aggregate.
const OCTAVES = [
  [2, 7.0, 1091],
  [4, 5.0, 2601],
  [8, 3.4, 7717],
  [16, 2.2, 13171],
  [64, 1.6, 20261],
];

// Warm neutral stone. Slightly red-biased so it sits under a warm key light
// without turning pink. Mean of the finished map is normalised to TARGET_MEAN
// so the material colour stays the source of truth.
const BASE = [232, 226, 214];
const TARGET_MEAN = 232;

function main() {
  const size = SIZE;
  const acc = new Float32Array(size * size);
  for (const [freq, amp, seed] of OCTAVES) {
    const layer = periodic(freq, seed, size);
    for (let i = 0; i < acc.length; i++) acc[i] += (layer[i] - 0.5) * 2 * amp;
  }
  // Directional grain: five nearly-horizontal sine bands, wrapped so the tile
  // still repeats. Reads as stone bedding, not as noise.
  for (let y = 0; y < size; y++) {
    const band = Math.sin((y / size) * Math.PI * 2 * 5) * 1.6
               + Math.sin((y / size) * Math.PI * 2 * 11 + 1.7) * 0.9;
    for (let x = 0; x < size; x++) acc[y * size + x] += band;
  }

  const buf = Buffer.alloc(size * size * 3);
  let sum = 0;
  for (let i = 0; i < size * size; i++) sum += acc[i];
  const mean = sum / (size * size);
  for (let i = 0; i < size * size; i++) {
    const n = acc[i] - mean;
    for (let c = 0; c < 3; c++) {
      const v = BASE[c] + n * (c === 0 ? 1.0 : c === 1 ? 0.96 : 0.90);
      buf[i * 3 + c] = Math.max(0, Math.min(255, Math.round(v)));
    }
  }
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  sharp(buf, { raw: { width: size, height: size, channels: 3 } })
    .png({ compressionLevel: 9, palette: false })
    .toFile(OUT)
    .then((info) => {
      console.log('stone noise ' + OUT + ' ' + info.width + 'x' + info.height +
                  ' ' + Math.round(info.size / 1024) + 'KB');
    })
    .catch((e) => { console.error(e); process.exit(1); });
}

main();
