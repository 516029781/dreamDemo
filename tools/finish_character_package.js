const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'art', 'phase1', 'reference_character');
const invPath = path.join(OUT, 'clip_inventory.json');
const inventory = JSON.parse(fs.readFileSync(invPath, 'utf8'));

function sha(p) {
  return crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
}
function size(p) { return fs.statSync(p).size; }
function chromeVersion() {
  try {
    const dir = 'C:/Program Files/Google/Chrome/Application';
    return fs.readdirSync(dir).filter(x => /^\d+\.\d+\.\d+\.\d+$/.test(x)).sort().pop() || 'unknown';
  } catch { return 'unknown'; }
}
const pkgVersion = name => JSON.parse(fs.readFileSync(path.join(ROOT, '.tooling', 'node_modules', name, 'package.json'), 'utf8')).version;
const pixiVersion = pkgVersion('pixi.js');
const spineVersion = pkgVersion('pixi-spine');
const sharpVersion = pkgVersion('sharp');
const puppeteerVersion = pkgVersion('puppeteer-core');
const gifencVersion = pkgVersion('gifenc');

const files = {
  idle_preview: path.join(OUT, 'idle_preview.png'),
  idle_on_paper: path.join(OUT, 'idle_on_paper.png'),
  move_preview: path.join(OUT, 'move_preview.gif'),
  reference_comparison: path.join(OUT, 'reference_comparison.png'),
  clip_inventory: invPath,
  move_contact: path.join(OUT, 'move_contact.png')
};
const hashes = {};
for (const [key, p] of Object.entries(files)) hashes[key] = { path: path.relative(ROOT, p).split(path.sep).join('/'), sha256: sha(p), bytes: size(p) };

const log = [
  '291_aglina character_playback runtime/capture log',
  'generated_at: ' + new Date().toISOString(),
  'producer: Qoder agent (self; not an independent reviewer)',
  '',
  'COMMANDS ACTUALLY RUN',
  '  powershell.exe -NoProfile -File C:/软件/鼠鼠/run-art-harness.ps1 audit  -> blocked (exit 3)',
  '  node tools/spine_puppeteer_probe.js  -> runtime parse + WebGL render probe',
  '  node tools/spine_animation_contact.js -> 26 sample frames, contact sheet, action inspection',
  '  node tools/spine_final_capture.js -> idle + 30 Move frames + GIF + clip inventory (wrapper stopped after inventory write; this log assembled from the frozen files)',
  '  node tools/render_comparison.js -> reference_comparison.png',
  '',
  'TOOLCHAIN',
  '  node ' + process.version,
  '  chrome ' + chromeVersion(),
  '  pixi.js ' + pixiVersion,
  '  pixi-spine ' + spineVersion + ' (Spine 3.8 runtime)',
  '  sharp ' + sharpVersion,
  '  puppeteer-core ' + puppeteerVersion,
  '  gifenc ' + gifencVersion,
  '  renderer: WebGL2 / ANGLE SwiftShader in headless Chromium',
  '  Spine editor/Blender/Cocos/Krita: not installed on this machine',
  '',
  'SOURCE (LOCKED)',
  '  reference/character_sources/ark_models/291_aglina/build_char_291_aglina.skel',
  '  reference/character_sources/ark_models/291_aglina/build_char_291_aglina.atlas',
  '  reference/character_sources/ark_models/291_aglina/build_char_291_aglina.png',
  '  skeleton_sha256: ' + inventory.source_skeleton_sha256,
  '  parsed_version: ' + inventory.skeleton_version,
  '  skins: ' + JSON.stringify(inventory.skins),
  '  animations: ' + JSON.stringify(inventory.animations),
  '  setup_clip: Default duration 0 (not used as idle)',
  '',
  'MAPPING / CAPTURE',
  '  idle = Relax (2.0s), capture time 0.5s; Move = Move (1.0s); Interact = Interact (1.0s)',
  '  capture canvas: ' + JSON.stringify(inventory.render_contract.capture_size) + '; fixed camera: ' + JSON.stringify(inventory.render_contract.fixed_camera),
  '  Move frames: ' + inventory.render_contract.move_frames + ' @ ' + inventory.render_contract.move_fps + 'fps, 1.0s loop',
  '  background: ' + inventory.render_contract.background,
  '  transparent idle/frames are post-keyed from the real runtime capture; the matte is not part of the asset',
  '',
  'OUTPUT HASHES',
  ...Object.entries(hashes).map(([k, v]) => '  ' + k + ': ' + v.sha256 + ' (' + v.bytes + ' bytes) ' + v.path),
  '',
  'IDENTITY',
  '  reference: P1 t044/t084 (red/black outfit, red-pink hair, large red/black weapon)',
  '  observed: 291 default (white coat, ash-brown hair, black bag, black/white gun; gun hidden in Relax/Move)',
  '  same character ID candidate: true; same skin as P1: false',
  '  H09: not met (candidate fail). H05: same skin/source identity not met.',
  '  No AI image or replacement character was generated; controller must provide/approve a matching skin or update the source contract.',
  '',
  'STATUS',
  '  Mechanical artifacts are complete for character_playback.',
  '  Independent review, controller attestation, Cocos engine import, full art catalog and scene_demo are NOT done.',
  '  The stage is NOT accepted. Do not report this as a full art or gameplay completion.'
].join('\n') + '\n';
fs.writeFileSync(path.join(OUT, 'runtime_log.txt'), log);

const submission = {
  character_mode: 'reference_spine',
  artifacts: [
    { role: 'clip_inventory', path: 'art/phase1/reference_character/clip_inventory.json' },
    { role: 'idle_preview', path: 'art/phase1/reference_character/idle_preview.png' },
    { role: 'move_preview', path: 'art/phase1/reference_character/move_preview.gif' },
    { role: 'reference_comparison', path: 'art/phase1/reference_character/reference_comparison.png' },
    { role: 'runtime_log', path: 'art/phase1/reference_character/runtime_log.txt' }
  ],
  production_methods: ['reference_spine']
};
fs.writeFileSync(path.join(OUT, 'submission_character_playback.json'), JSON.stringify(submission, null, 2) + '\n');
console.log(JSON.stringify({ hashes, submission: path.join(OUT, 'submission_character_playback.json'), log: path.join(OUT, 'runtime_log.txt') }, null, 2));
