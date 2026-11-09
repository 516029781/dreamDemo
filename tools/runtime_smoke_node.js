// Node stub smoke for runtime_space_base/game.js.
// This is NOT a WeChat/device test; it only checks loader/pan/clamp logic.
// Run: node tools/runtime_smoke_node.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.resolve(__dirname, '..');
const project = path.join(root, 'runtime_space_base');
const jpeg = path.join(project, 'assets', 'space_base_v02.jpg');

function jpegSize(file) {
  const b = fs.readFileSync(file);
  let i = 2;
  while (i < b.length) {
    if (b[i] !== 0xff) { i++; continue; }
    const m = b[i + 1];
    if (m === 0xc0 || m === 0xc2) {
      return { width: b.readUInt16BE(i + 7), height: b.readUInt16BE(i + 5) };
    }
    if (m === 0xd8 || m === 0xd9) { i += 2; continue; }
    i += 2 + b.readUInt16BE(i + 2);
  }
  throw new Error('no SOF marker');
}

const size = jpegSize(jpeg);
const logs = [];
const draws = [];
let imageObj = null;
let rafQueue = [];
const handlers = {};

const ctx = new Proxy({
  scale() {}, fillRect() {}, beginPath() {}, arc() {}, fill() {}, stroke() {},
  fillText() {}, set fillStyle(v) {}, set font(v) {}, set lineWidth(v) {}, set strokeStyle(v) {},
}, {
  get(t, k) {
    if (k === 'drawImage') return (...args) => draws.push(args.slice(0, 5));
    return t[k];
  },
});

const canvas = { width: 0, height: 0, getContext: () => ctx };
const wx = {
  getSystemInfoSync: () => ({ pixelRatio: 2, windowWidth: 540, windowHeight: 960, memorySize: 4096, benchmarkLevel: 30 }),
  createCanvas: () => canvas,
  createImage: () => {
    imageObj = { width: 0, height: 0, onload: null, onerror: null, set src(v) { this._src = v; } };
    return imageObj;
  },
  onTouchStart: (f) => { handlers.start = f; },
  onTouchMove: (f) => { handlers.move = f; },
  onTouchEnd: (f) => { handlers.end = f; },
  onTouchCancel: (f) => { handlers.cancel = f; },
  onMemoryWarning: (f) => { handlers.memory = f; },
};

const sandbox = {
  wx,
  console: {
    log: (...a) => logs.push({ level: 'log', args: a }),
    warn: (...a) => logs.push({ level: 'warn', args: a }),
    error: (...a) => logs.push({ level: 'error', args: a }),
  },
  requestAnimationFrame: (f) => { rafQueue.push(f); },
  Date,
  Math,
};
vm.createContext(sandbox);
const code = fs.readFileSync(path.join(project, 'game.js'), 'utf8');
vm.runInContext(code, sandbox, { filename: 'game.js' });

function flush(frames) {
  for (let i = 0; i < frames; i++) {
    const q = rafQueue; rafQueue = [];
    for (const f of q) f();
  }
}

if (!imageObj) throw new Error('createImage not called');
imageObj.width = size.width;
imageObj.height = size.height;
if (!imageObj.onload) throw new Error('onload not set');
imageObj.onload();
flush(2);

function lastCam() {
  const d = draws[draws.length - 1];
  if (!d) throw new Error('no drawImage');
  return { camX: d[1], camY: d[2], viewW: d[3], viewH: d[4] };
}

const initial = lastCam();
handlers.start({ touches: [{ clientX: 500, clientY: 500 }] });
handlers.move({ touches: [{ clientX: 10000, clientY: 10000 }] });
handlers.end();
flush(1);
const clampedLow = lastCam();
handlers.start({ touches: [{ clientX: 500, clientY: 500 }] });
handlers.move({ touches: [{ clientX: -10000, clientY: -10000 }] });
handlers.end();
flush(1);
const clampedHigh = lastCam();

const loaded = logs.find(l => String(l.args[0]).includes('SPACE_BASE_MAP_LOADED'));
const first = logs.find(l => String(l.args[0]).includes('SPACE_BASE_FIRST_FRAME'));
const result = {
  status: 'diagnostic_only',
  note: 'Node stub; not a WeChat/device test. W3/W4 remain external.',
  image: { path: jpeg, width: size.width, height: size.height },
  initial, clampedLow, clampedHigh,
  checks: {
    map_loaded_log: !!loaded,
    first_frame_log: !!first,
    low_clamped: clampedLow.camX === 0 && clampedLow.camY === 0,
    high_clamped: clampedHigh.camX === 840 && clampedHigh.camY === 940,
    no_errors: !logs.some(l => l.level === 'error'),
  },
  logs: logs.map(l => ({ level: l.level, args: l.args.map(a => (typeof a === 'object' ? JSON.parse(JSON.stringify(a)) : a)) })),
};
const out = path.join(root, 'knowledge', 'active', '20261102-space-base-detail', 'runs', '20261102-1907', 'evidence', 'external', 'W3_node_smoke.json');
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, JSON.stringify(result, null, 1));
console.log('NODE_SMOKE', JSON.stringify(result.checks), 'out', out);
process.exit(Object.values(result.checks).every(Boolean) ? 0 : 1);
