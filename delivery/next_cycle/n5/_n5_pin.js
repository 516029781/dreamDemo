/**
 * n5 build-pin guard for capture scripts.
 *
 * n4 captured screenshots from one build while its behaviour results came from
 * another (P0-2). Every n5 capture must prove it is reading the pinned build
 * before it writes evidence.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = 'C:/软件/鼠鼠';
const PIN = path.join(ROOT, 'delivery/next_cycle/n5/performance/formal_build.json');

function sha256(p) {
  const h = crypto.createHash('sha256');
  h.update(fs.readFileSync(p));
  return h.digest('hex');
}

function loadPin() {
  if (!fs.existsSync(PIN)) throw new Error('no formal build pin; run tools/n5_build.py first');
  return JSON.parse(fs.readFileSync(PIN, 'utf8'));
}

/** Throws unless the served build output still matches the pinned hash. */
function assertPinnedBuild() {
  const pin = loadPin();
  const index = path.join(ROOT, 'demo_n5/build/web-desktop/index.html');
  if (!fs.existsSync(index)) throw new Error('demo_n5 web-desktop build missing');
  const actual = sha256(index);
  if (pin.output_index_sha256 && actual !== pin.output_index_sha256) {
    throw new Error('build drift: served index.html ' + actual +
      ' != pinned ' + pin.output_index_sha256 + '; rebuild or re-pin deliberately');
  }
  return pin;
}

module.exports = { loadPin, assertPinnedBuild, sha256 };
