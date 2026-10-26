// Prepare a runtime-only working copy of a downloaded Ark-Models candidate.
// The locked source files in reference/character_sources/ are never modified.
// The atlas page name is rewritten only because '#' in a file name becomes a URL
// fragment and cannot be fetched by pixi-spine's atlas loader.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = path.resolve(__dirname, '..', '..');
const ID = process.argv[2] || '291_aglina_boc1';
const SRC = path.join(ROOT, 'reference', 'character_sources', 'ark_models', ID);
const WORK = path.join(__dirname, 'work', ID);

const base = fs.readdirSync(SRC).find(f => f.endsWith('.skel'));
if (!base) throw new Error('no .skel in ' + SRC);
const stem = base.replace(/\.skel$/, '');

fs.mkdirSync(WORK, { recursive: true });

function sha256(buf) {
  return crypto.createHash('sha256').update(buf).digest('hex').toUpperCase();
}
function gitBlobSha1(buf) {
  const h = crypto.createHash('sha1');
  h.update('blob ' + buf.length + '\0');
  h.update(buf);
  return h.digest('hex');
}

const files = {};
for (const ext of ['.skel', '.png', '.atlas']) {
  const src = path.join(SRC, stem + ext);
  const buf = fs.readFileSync(src);
  files[ext] = { source: path.relative(ROOT, src).replace(/\\/g, '/'), bytes: buf.length, sha256: sha256(buf), git_blob_sha1: gitBlobSha1(buf) };
}

// Runtime copies with URL-safe names.
fs.writeFileSync(path.join(WORK, ID + '.skel'), fs.readFileSync(path.join(SRC, stem + '.skel')));
fs.copyFileSync(path.join(SRC, stem + '.png'), path.join(WORK, ID + '.png'));
let atlas = fs.readFileSync(path.join(SRC, stem + '.atlas'), 'utf8');
const lines = atlas.split('\n');
const pageLine = lines.findIndex(l => /\.png\s*$/.test(l));
if (pageLine < 0) throw new Error('no atlas page line');
const originalPage = lines[pageLine].trim();
lines[pageLine] = ID + '.png';
atlas = lines.join('\n');
fs.writeFileSync(path.join(WORK, ID + '.atlas'), atlas);

const skel = fs.readFileSync(path.join(WORK, ID + '.skel'));
const header = skel.subarray(0, 64).toString('latin1').replace(/\0/g, '|');

const manifest = {
  candidate_id: ID,
  repository: 'https://github.com/isHarryh/Ark-Models',
  commit: 'e65fb9147846b64bcf2df956b8cd8da77a51b9b8',
  source_directory: 'models/' + (ID === '291_aglina_boc1' ? '291_aglina_boc%231' : ID),
  original_atlas_page_name: originalPage,
  runtime_working_copy_reason: "atlas page name contains '#', which URL parsers treat as a fragment; runtime copy renames skeleton/atlas/texture to URL-safe names without changing bytes of .skel/.png",
  runtime_working_copy: path.relative(ROOT, WORK).replace(/\\/g, '/'),
  files,
  skel_header_strings: header,
  skeleton_version: (() => {
    // Spine 3.8 binary starts with a length-prefixed hash string followed by the
    // version string. Byte layout is confirmed by the runtime parse (pixi-spine).
    const head = skel.subarray(0, 64).toString('latin1');
    const m = head.match(/(\d+\.\d+\.\d+)/);
    return m ? m[1] : null;
  })(),
  skeleton_hash_string: skel.subarray(1, 29).toString('latin1')
};
fs.writeFileSync(path.join(WORK, 'runtime_copy_manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
console.log(JSON.stringify(manifest, null, 2));
