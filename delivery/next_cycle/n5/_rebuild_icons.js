/**
 * Redraw the 21 UI icons as one family.
 *
 * Contract U02 asks for "thin lines, hand-drawn feel, light irregularity, open
 * thin frames". The old set mixed solid glyphs (play triangle, four-point star)
 * with thin strokes and used different corner radii, which is why the reviewers
 * read it as "icons from different sources".
 *
 * One spec for all: 96x96 viewBox, stroke only, width 7, round caps and joins,
 * content inside 18..78, and a fixed +/-0.6 px jitter so the lines are not
 * mechanically straight. Pure black + alpha, matching the existing assets.
 *
 * Usage:
 *   node _rebuild_icons.js --out <dir>      write to a folder for preview
 *   node _rebuild_icons.js --apply          overwrite demo_n5/assets/resources/ui/icons
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');

const DIR = 'C:/软件/鼠鼠/demo_n5/assets/resources/ui/icons';
const OUT = process.argv.includes('--out')
  ? process.argv[process.argv.indexOf('--out') + 1]
  : 'C:/软件/鼠鼠/delivery/next_cycle/n5/T5/ui/icons_after';
const APPLY = process.argv.includes('--apply');

const SW = 7;          // stroke width, matches the old icons' optical weight
const JIT = 0.6;       // hand-drawn jitter in viewBox units

// deterministic jitter so a rebuild is byte-stable
let seed = 20261026;
function rnd() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff;
  return seed / 0x7fffffff;
}
function j(v) { return +(v + (rnd() * 2 - 1) * JIT).toFixed(2); }
function pt(x, y) { return `${j(x)} ${j(y)}`; }
function line(x1, y1, x2, y2) { return `M${pt(x1, y1)} L${pt(x2, y2)}`; }
function poly(points, close) {
  return 'M' + points.map(([x, y]) => pt(x, y)).join(' L') + (close ? ' Z' : '');
}
function arc(cx, cy, r, a0, a1, sweep) {
  const rad = (d) => (d * Math.PI) / 180;
  const x0 = cx + r * Math.cos(rad(a0)), y0 = cy + r * Math.sin(rad(a0));
  const x1 = cx + r * Math.cos(rad(a1)), y1 = cy + r * Math.sin(rad(a1));
  const large = Math.abs(a1 - a0) > 180 ? 1 : 0;
  return `M${pt(x0, y0)} A${r} ${r} 0 ${large} ${sweep} ${pt(x1, y1)}`;
}
function circle(cx, cy, r) {
  // a single 360 deg A-command collapses when start == end; emit a <circle> instead
  return `<circle cx="${j(cx)}" cy="${j(cy)}" r="${j(r)}"/>`;
}

const ICONS = {
  // straight arrow, shaft slightly bowed so it does not read as a UI glyph
  arrow: [line(20, 48, 68, 47), poly([[56, 33], [73, 48], [56, 62]])],
  check: [poly([[22, 50], [39, 67], [73, 29]])],
  close: [line(26, 27, 69, 70), line(69, 27, 27, 69)],
  // was a solid triangle; now an open thin frame like everything else
  continue: [poly([[35, 25], [71, 48], [35, 72]], true)],
  // two offset frames, both open on the shared corner
  copy: ['M40 19 H74 V53', 'M22 33 H58 V73 H22 Z'],
  info: [circle(48, 48, 28), line(48, 44, 48, 66), line(48, 32, 48, 33.5)],
  leaf: ['M26 71 C27 41 44 24 72 24 C72 53 56 70 26 71 Z', 'M33 64 C40 53 51 41 65 31'],
  lock: ['M31 44 H65 V74 H31 Z', 'M38 44 V34 C38 27 43 22 48 22 C53 22 58 27 58 34 V44', line(48, 53, 48, 61)],
  menu: [line(20, 33, 76, 32), line(20, 48, 66, 47), line(20, 63, 72, 64)],
  // ticket: open frame, punched notch on the left, small open star top-right
  pickup: ['M28 36 H70 V66 H28 Z', 'M28 43 C23 46 23 56 28 59', 'M62 18 L64.5 25 L72 27 L64.5 29 L62 36 L59.5 29 L52 27 L59.5 25 Z'],
  pin: ['M48 78 C48 78 68 57 68 40 C68 29 59 20 48 20 C37 20 28 29 28 40 C28 57 48 78 48 78 Z', circle(48, 39, 9)],
  // screen / frame with stand
  place: ['M22 26 H74 V60 H22 Z', line(48, 60, 48, 70), line(36, 71, 60, 70)],
  postcard: ['M20 34 H76 V64 H20 Z', 'M56 42 H68 V54 H56 Z', line(28, 44, 47, 43)],
  // clock face with a return arrow above it
  restart: [circle(48, 54, 21), line(48, 42, 48, 54), line(48, 54, 56, 58), poly([[40, 11], [48, 19], [40, 27]])],
  retry: ['M66 31 C58 19 40 17 30 28 C18 41 21 61 35 71 C50 81 70 72 74 56', poly([[58, 17], [67, 30], [53, 33]])],
  // phone in portrait
  rotate: ['M34 22 H62 V74 H34 Z', line(44, 67, 52, 67)],
  sound_off: ['M22 40 H34 L48 28 V68 L34 56 H22 Z', line(58, 40, 72, 56), line(72, 40, 58, 56)],
  sound_on: ['M22 40 H34 L48 28 V68 L34 56 H22 Z', 'M58 38 C63 44 63 52 58 58', 'M66 31 C75 42 75 54 66 65'],
  sparkle: ['M48 20 C50 38 58 46 76 48 C58 50 50 58 48 76 C46 58 38 50 20 48 C38 46 46 38 48 20 Z'],
  talk: ['M22 28 H74 V58 H44 L32 70 V58 H22 Z', line(36, 43, 37, 43.6), line(48, 43, 49, 43.6), line(60, 43, 61, 43.6)],
  // eye: pointed at both corners so it does not read as a capsule
  view: ['M18 48 C34 24 62 24 78 48 C62 72 34 72 18 48 Z', circle(48, 48, 10)],
};

function svgFor(paths) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">
    <g fill="none" stroke="#000000" stroke-width="${SW}" stroke-linecap="round" stroke-linejoin="round">
      ${paths.map((d) => (d.startsWith('<') ? d : `<path d="${d}"/>`)).join('\n      ')}
    </g>
  </svg>`;
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const files = fs.readdirSync(DIR).filter((f) => f.endsWith('.png')).sort();
  const missing = files
    .map((f) => path.basename(f, '.png'))
    .filter((n) => !ICONS[n.replace(/^icon_/, '')]);
  if (missing.length) {
    console.error('NO_SPEC_FOR', missing.join(', '));
    process.exit(2);
  }
  const written = [];
  for (const [name, paths] of Object.entries(ICONS)) {
    seed = 20261026;
    const buf = await sharp(Buffer.from(svgFor(paths))).png().toBuffer();
    const target = path.join(APPLY ? DIR : OUT, `icon_${name}.png`);
    fs.writeFileSync(target, buf);
    written.push(name);
  }
  console.log(JSON.stringify({ written: written.length, to: APPLY ? DIR : OUT, missing }));
})();
