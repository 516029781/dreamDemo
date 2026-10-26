/*
 * Build the editable UI kit support files from the authored JSON/SVG sources.
 * - css/tokens.css is generated from tokens.json (never hand-edited)
 * - css/preview_fonts.css points headless Chrome at locally installed Noto fonts
 * - components/icons/*.svg and components/icons.svg are generated from icons.json
 * - exports/paper_panel_128.9slice.png is a 3x export of the editable panel SVG
 *
 * Usage: node tools/ui/build_ui.js
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const UI = path.join(ROOT, 'art', 'candidates', 'candidate_n5', 'ui');
const sharp = require(path.join(ROOT, '.tooling', 'node_modules', 'sharp'));

const tokens = JSON.parse(fs.readFileSync(path.join(UI, 'tokens.json'), 'utf8'));
const iconSource = JSON.parse(fs.readFileSync(path.join(UI, 'components', 'icons.json'), 'utf8'));

function kebab(key) {
  return String(key)
    .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
    .replace(/_/g, '-')
    .toLowerCase();
}

function flatten(obj, prefix, out, skipTop = []) {
  for (const [key, value] of Object.entries(obj)) {
    const name = prefix ? `${prefix}-${kebab(key)}` : kebab(key);
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      flatten(value, name, out, skipTop);
    } else if (Array.isArray(value)) {
      out.push([name, value.join(', ')]);
    } else {
      out.push([name, String(value)]);
    }
  }
  return out;
}

const cssTokens = [];
for (const group of ['canvas', 'font', 'type', 'color', 'line', 'radius', 'space', 'shadow', 'opacity', 'motion', 'safe', 'layout', 'nineSlice']) {
  if (tokens[group]) flatten(tokens[group], kebab(group), cssTokens, ['meta']);
}
const tokenLines = [
  '/* GENERATED FILE — edit art/full/ui/tokens.json and run `node tools/ui/build_ui.js`. */',
  ':root {'
];
for (const [name, value] of cssTokens) {
  tokenLines.push(`  --${name}: ${value};`);
}
tokenLines.push('  --font-body: var(--font-body-stack);');
tokenLines.push('  --font-display: var(--font-display-stack);');
tokenLines.push('}');
tokenLines.push('');
fs.writeFileSync(path.join(UI, 'css', 'tokens.css'), tokenLines.join('\n'), 'utf8');

fs.writeFileSync(path.join(UI, 'css', 'preview_fonts.css'), `/* PREVIEW ONLY. Not part of the game build.
   Headless Chrome loads the locally installed Noto CJK variable fonts so the previews
   exercise real Chinese glyphs. Release builds must embed licensed/subset font files. */
@font-face {
  font-family: "Noto Sans SC";
  src: url("file:///C:/Windows/Fonts/NotoSansSC-VF.ttf") format("truetype");
  font-weight: 100 900;
  font-display: block;
}
@font-face {
  font-family: "Noto Serif SC";
  src: url("file:///C:/Windows/Fonts/NotoSerifSC-VF.ttf") format("truetype");
  font-weight: 100 900;
  font-display: block;
}
`, 'utf8');

function iconBody(icon, indent = '  ') {
  const parts = [];
  for (const d of icon.fills || []) {
    parts.push(`${indent}<path d="${d}" fill="currentColor" stroke="none"/>`);
  }
  for (const d of icon.strokes || []) {
    parts.push(`${indent}<path d="${d}"/>`);
  }
  for (const [cx, cy] of icon.dots || []) {
    parts.push(`${indent}<circle cx="${cx}" cy="${cy}" r="1.1" fill="currentColor" stroke="none"/>`);
  }
  return parts.join('\n');
}

const iconDir = path.join(UI, 'components', 'icons');
fs.mkdirSync(iconDir, { recursive: true });
const iconFiles = [];
for (const [name, icon] of Object.entries(iconSource.icons)) {
  const body = iconBody(icon);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="${iconSource.viewBox}" fill="none" stroke="currentColor" stroke-width="${iconSource.strokeWidth}" stroke-linecap="round" stroke-linejoin="round" role="img" aria-label="${icon.label}">
${body}
</svg>
`;
  fs.writeFileSync(path.join(iconDir, `icon_${name}.svg`), svg, 'utf8');
  iconFiles.push(`components/icons/icon_${name}.svg`);
}

const symbols = Object.entries(iconSource.icons).map(([name, icon]) => {
  return `  <symbol id="icon-${name}" viewBox="${iconSource.viewBox}">
${iconBody(icon, '    ')}
  </symbol>`;
}).join('\n');
fs.writeFileSync(path.join(UI, 'components', 'icons.svg'), `<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" style="position:absolute" aria-hidden="true">
  <!-- GENERATED from components/icons.json. Path-only icons; no text. -->
${symbols}
</svg>
`, 'utf8');

const iconJs = `/* GENERATED from components/icons.json by tools/ui/build_ui.js. Path-only, no baked text. */
(function (root) {
  var DATA = ${JSON.stringify(iconSource, null, 2)};
  function svg(name, size, className) {
    var icon = DATA.icons[name];
    if (!icon) throw new Error('Unknown icon: ' + name);
    var s = size || 24;
    var cls = className ? ' class="' + className + '"' : '';
    var parts = [];
    (icon.fills || []).forEach(function (d) { parts.push('<path d="' + d + '" fill="currentColor" stroke="none"/>'); });
    (icon.strokes || []).forEach(function (d) { parts.push('<path d="' + d + '"/>'); });
    (icon.dots || []).forEach(function (p) { parts.push('<circle cx="' + p[0] + '" cy="' + p[1] + '" r="1.1" fill="currentColor" stroke="none"/>'); });
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + s + '" height="' + s + '" viewBox="' + DATA.viewBox + '"' +
      cls + ' fill="none" stroke="currentColor" stroke-width="' + DATA.strokeWidth + '" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' +
      parts.join('') + '</svg>';
  }
  root.UI_ICONS = { data: DATA, svg: svg, names: Object.keys(DATA.icons) };
})(window);
`;
fs.writeFileSync(path.join(UI, 'js', 'icons.js'), iconJs, 'utf8');

async function exportNineSlice() {
  const src = path.join(UI, 'components', 'paper_panel.svg');
  const buf = fs.readFileSync(src);
  const png = await sharp(buf, { density: 216 }).png({ compressionLevel: 9 }).toBuffer();
  const meta = await sharp(png).metadata();
  const out = path.join(UI, 'exports', 'paper_panel_128.9slice.png');
  fs.writeFileSync(out, png);
  const spec = {
    source: 'art/full/ui/components/paper_panel.svg',
    role: '9-slice paper panel texture, 3x export of the editable SVG',
    source_size_px: 128,
    slice_px_at_1x: 32,
    export_size_px: [meta.width, meta.height],
    export_slice_px: 96,
    css_border_width_px: 32,
    css_border_image_slice: 96,
    center_is_plain_paper: true,
    decorations_are_separate: ['deco_tape.svg', 'deco_stamp.svg', 'deco_leaf.svg', 'deco_pin.svg', 'deco_string.svg', 'deco_seal.svg'],
    note: 'PNG is a derived export. Edit the SVG or the CSS nine-slice component, never this PNG.'
  };
  fs.writeFileSync(path.join(UI, 'exports', 'paper_panel_128.9slice.json'), JSON.stringify(spec, null, 2) + '\n', 'utf8');
  return spec;
}

function walk(dir, acc = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p, acc);
    else acc.push(p);
  }
  return acc;
}

function validate() {
  const errors = [];
  const warnings = [];
  const requiredTokens = [
    'color.paper.base', 'color.ink.strong', 'font.body.stack', 'font.display.stack',
    'type.body.size', 'type.title.size', 'line.line', 'space.6', 'safe.insetTop',
    'nineSlice.slice', 'layout.dialogueW'
  ];
  for (const pathStr of requiredTokens) {
    let cur = tokens;
    for (const k of pathStr.split('.')) cur = cur && cur[k];
    if (!cur) errors.push(`tokens.json missing ${pathStr}`);
  }
  const svgs = walk(path.join(UI, 'components')).filter(p => p.endsWith('.svg'));
  for (const p of svgs) {
    const text = fs.readFileSync(p, 'utf8');
    if (/<text[\s>]/i.test(text)) errors.push(`${path.relative(ROOT, p)} contains <text>; text must stay in code`);
    if (/<image[\s>]/i.test(text)) errors.push(`${path.relative(ROOT, p)} contains <image>; no raster baking`);
    if (/href=["']https?:/i.test(text)) errors.push(`${path.relative(ROOT, p)} references a remote asset`);
  }
  if (Object.keys(iconSource.icons).length < 15) errors.push('icon family unexpectedly small');
  const forbiddenCopy = ['信使', '未寄出的信', '把信送到', 'messenger'];
  const sources = walk(UI).filter(p => /\.(html|js|css|json|svg|md)$/.test(p) && !p.includes('exports') && !p.endsWith('build_report.json'));
  for (const p of sources) {
    const text = fs.readFileSync(p, 'utf8');
    for (const phrase of forbiddenCopy) {
      if (text.includes(phrase) && !p.endsWith('build_ui.js')) warnings.push(`${path.relative(ROOT, p)} mentions old story phrase "${phrase}" — confirm it is only a negative rule`);
    }
  }
  return { errors, warnings, svg_count: svgs.length, icon_count: Object.keys(iconSource.icons).length };
}

(async () => {
  const nine = await exportNineSlice();
  const checks = validate();
  const report = {
    generated_at: new Date().toISOString(),
    generator: 'tools/ui/build_ui.js',
    node: process.version,
    sharp: require(path.join(ROOT, '.tooling', 'node_modules', 'sharp', 'package.json')).version,
    tokens: 'art/full/ui/tokens.json',
    css_variables_written: cssTokens.length,
    icons_written: iconFiles.length,
    nine_slice: nine,
    checks
  };
  fs.writeFileSync(path.join(UI, 'build_report.json'), JSON.stringify(report, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify({
    css_variables: cssTokens.length,
    icons: iconFiles.length,
    nine_slice: `${nine.export_size_px[0]}x${nine.export_size_px[1]} slice ${nine.export_slice_px}`,
    errors: checks.errors,
    warnings: checks.warnings
  }, null, 2));
  if (checks.errors.length) process.exitCode = 1;
})();
