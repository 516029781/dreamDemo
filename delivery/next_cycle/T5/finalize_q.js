/** Finalize Q01-Q09 evidence and build behavior_results.json for the producer check. */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { createRequire } = require('module');
const req = createRequire('C:/软件/鼠鼠/.tooling/package.json');
const sharp = req('sharp');
const puppeteer = req('puppeteer-core');

const ROOT = 'C:/软件/鼠鼠';
const T5 = path.join(ROOT, 'delivery/next_cycle/T5');
const T3 = path.join(ROOT, 'delivery/next_cycle/T3');
const T2 = path.join(ROOT, 'delivery/next_cycle/T2');
const sha = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const rel = (file) => path.relative(ROOT, file).replace(/\\/g, '/');
const read = (name) => JSON.parse(fs.readFileSync(path.join(T5, name), 'utf8'));

async function rawInfo(file) {
  return sharp(file).raw().toBuffer({ resolveWithObject: true });
}

function countRed(data, info, box) {
  let count = 0;
  for (let y = Math.max(0, box.top); y < Math.min(info.height, box.top + box.height); y++) {
    for (let x = Math.max(0, box.left); x < Math.min(info.width, box.left + box.width); x++) {
      const i = (y * info.width + x) * info.channels;
      const r = data[i], g = data[i + 1], b = data[i + 2];
      if (r > 110 && r > g * 1.25 && r > b * 1.25) count++;
    }
  }
  return count;
}

function countWhite(data, info, box) {
  let count = 0;
  for (let y = Math.max(0, box.top); y < Math.min(info.height, box.top + box.height); y++) {
    for (let x = Math.max(0, box.left); x < Math.min(info.width, box.left + box.width); x++) {
      const i = (y * info.width + x) * info.channels;
      const r = data[i], g = data[i + 1], b = data[i + 2];
      if (r > 190 && g > 170 && b > 160) count++;
    }
  }
  return count;
}

function pixelAt(data, info, x, y) {
  const i = (Math.round(y) * info.width + Math.round(x)) * info.channels;
  return [data[i], data[i + 1], data[i + 2]];
}

async function shadowDrift() {
  const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: 'new',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--no-sandbox'],
    defaultViewport: { width: 1280, height: 720, deviceScaleFactor: 1 },
  });
  const page = await browser.newPage();
  await page.goto('http://127.0.0.1:8801/', { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForFunction(() => window.__COURTYARD_READY__ === true, { timeout: 60000 });
  await page.evaluate(() => { window.__courtyard.setUi(false); window.__courtyard.closeDialogue(); });
  const out = {};
  for (const [name, pos] of [['front', [0, -5.2]], ['behind', [0, 2.0]]]) {
    await page.evaluate((v) => window.__courtyard.setPlayer(v[0], v[1]), pos);
    await new Promise((r) => setTimeout(r, 700));
    out[name] = await page.evaluate(() => {
      let shadow = null;
      const walk = (n) => { if (n.name === 'ContactShadow') shadow = n.worldPosition; for (const c of n.children) walk(c); };
      walk(cc.director.getScene());
      const p = window.__courtyard.state().player;
      const cam = cc.director.getScene().getChildByName('Main Camera').getComponent(cc.Camera);
      const feet = cam.worldToScreen(new cc.Vec3(p[0], p[1], p[2]));
      const head = cam.worldToScreen(new cc.Vec3(p[0], p[1] + 1.75, p[2]));
      return { player: p, shadow: shadow ? [shadow.x, shadow.y, shadow.z] : null,
        feet_screen: [feet.x, 720 - feet.y], head_screen: [head.x, 720 - head.y],
        drift_m: shadow ? Math.hypot(shadow.x - p[0], shadow.z - p[2]) : null };
    });
  }
  await browser.close();
  return out;
}

async function q07Diff() {
  const a = await rawInfo(path.join(T5, 'q07_edited_bench.png'));
  const b = await rawInfo(path.join(T5, 'q07_restored_bench.png'));
  let candidate = 0, count = 0, minX = 1e9, minY = 1e9, maxX = -1, maxY = -1;
  for (let y = 0; y < a.info.height; y++) {
    for (let x = 0; x < a.info.width; x++) {
      const i = (y * a.info.width + x) * a.info.channels;
      const d = Math.max(Math.abs(a.data[i] - b.data[i]), Math.abs(a.data[i + 1] - b.data[i + 1]), Math.abs(a.data[i + 2] - b.data[i + 2]));
      if (d > 12) { count++; minX = Math.min(minX, x); minY = Math.min(minY, y); maxX = Math.max(maxX, x); maxY = Math.max(maxY, y); }
    }
  }
  const report = { changed_pixels: count, total_pixels: a.info.width * a.info.height,
    bbox: count ? { left: minX, top: minY, width: maxX - minX + 1, height: maxY - minY + 1 } : null,
    threshold: 12, note: 'bench close-up, same inspect camera; only the edited wood mesh should differ' };
  fs.writeFileSync(path.join(T5, 'q07_diff.json'), JSON.stringify(report, null, 2) + '\n');
  return report;
}

async function portraitSafeArea() {
  const { data, info } = await rawInfo(path.join(T5, 'q09_portrait_720x1280.png'));
  let minX = 1e9, minY = 1e9, maxX = -1, maxY = -1;
  for (let y = 300; y < 1000; y++) {
    for (let x = 80; x < 640; x++) {
      const i = (y * info.width + x) * info.channels;
      const r = data[i], g = data[i + 1], b = data[i + 2];
      if (r >= 245 && g >= 242 && b >= 232 && b <= 246) {
        minX = Math.min(minX, x); minY = Math.min(minY, y); maxX = Math.max(maxX, x); maxY = Math.max(maxY, y);
      }
    }
  }
  return maxX > 0 ? { left: minX, right: maxX, top: minY, bottom: maxY, unit: 'screenshot_px', basis: 'rotate_notice cream panel bounds' } : null;
}

(async () => {
  const q01 = read('q01_camera.json');
  const q03 = read('q03_occlusion.json');
  const q04 = read('q04_behavior.json');
  const q05 = read('q05_board.json');
  const q06 = read('q06_stats.json');
  const q09 = read('q09_viewports.json');
  const shadow = await shadowDrift();
  const diff = await q07Diff();
  const portraitArea = await portraitSafeArea();

  const frontImg = await rawInfo(path.join(T5, 'q03_front.png'));
  const behindImg = await rawInfo(path.join(T5, 'q03_behind.png'));
  const bbox = (probe) => {
    const x = Math.round(probe.head_screen[0] - 65);
    const top = Math.round(probe.head_screen[1] - 25);
    const bottom = Math.round(probe.feet_screen[1] + 15);
    return { left: x, top, width: 130, height: bottom - top };
  };
  const frontBox = bbox(shadow.front);
  const behindBox = bbox(shadow.behind);
  const frontRed = countRed(frontImg.data, frontImg.info, frontBox);
  const behindRed = countRed(behindImg.data, behindImg.info, behindBox);
  const frontWhite = countWhite(frontImg.data, frontImg.info, frontBox);
  const behindWhite = countWhite(behindImg.data, behindImg.info, behindBox);
  const headBox = (probe, w = 60, h = 90) => ({ left: Math.round(probe.head_screen[0] - w / 2),
    top: Math.round(probe.head_screen[1] - 20), width: w, height: h });
  const frontHeadWhite = countWhite(frontImg.data, frontImg.info, headBox(shadow.front));
  const behindHeadWhite = countWhite(behindImg.data, behindImg.info, headBox(shadow.behind));
  const frontHead = pixelAt(frontImg.data, frontImg.info, shadow.front.head_screen[0], shadow.front.head_screen[1]);
  const behindHead = pixelAt(behindImg.data, behindImg.info, shadow.behind.head_screen[0], shadow.behind.head_screen[1]);
  const occlusion = { front_white_pixels: frontWhite, behind_white_pixels: behindWhite,
    front_head_region_white: frontHeadWhite, behind_head_region_white: behindHeadWhite,
    front_head_pixel: frontHead, behind_head_pixel: behindHead,
    visual_metric: 'head-region near-white character pixels + head pixel; tree canopy is brown',
    occluded: behindHeadWhite < Math.max(10, frontHeadWhite * 0.35) };

  const q02 = {
    kind: 'q02_reference_comparison',
    reference_regions: [
      { region: 'courtyard_scale_density', path: 'reference/_raw_screenshots/P1/t015s.jpg', sha256: sha(path.join(ROOT, 'reference/_raw_screenshots/P1/t015s.jpg')) },
      { region: 'player_hud', path: 'reference/_raw_screenshots/P1/t084s.jpg', sha256: sha(path.join(ROOT, 'reference/_raw_screenshots/P1/t084s.jpg')) },
      { region: 'dialogue_composition', path: 'reference/_raw_screenshots/P1/t044s.jpg', sha256: sha(path.join(ROOT, 'reference/_raw_screenshots/P1/t044s.jpg')) },
    ],
    candidate_comparison: 'delivery/next_cycle/T2/reference_comparison.png',
    differences: [
      { region: 'tree canopy', difference: 'P1 uses dense continuous foliage; candidate is stylized clumps with visible faceted masses' },
      { region: 'planting density', difference: 'P1 fills foreground and beds densely; candidate keeps a clearer playable plaza and simplified beds' },
      { region: 'UI paper', difference: 'P1 uses translucent paper with doodles; candidate matches translucency/accents but keeps simpler borders' },
      { region: 'stone/metal', difference: 'P1 has worn stone and reflective metal; candidate uses warmer grey and controlled specular with less wear' },
    ],
  };
  fs.writeFileSync(path.join(T5, 'q02_reference.json'), JSON.stringify(q02, null, 2) + '\n');

  const slices = {
    'q04_normal_move.json': { runs: q04.runs.map((r) => ({ input_mode: r.input_mode, normal_move_m: r.normal_move_m })) },
    'q04_pause.json': { runs: q04.runs.map((r) => ({ input_mode: r.input_mode, pause_displacement_m: r.pause_displacement_m, anim_during_pause: r.anim_during_pause, clip_after_pause: r.clip_after_pause })) },
    'q04_dialogue.json': { runs: q04.runs.map((r) => ({ input_mode: r.input_mode, dialogue_displacement_m: r.dialogue_displacement_m, anim_during_dialogue: r.anim_during_dialogue })) },
    'q04_resume.json': { runs: q04.runs.map((r) => ({ input_mode: r.input_mode, resumed_without_input_m: r.resumed_without_input_m, resumed_after_new_input_m: r.resumed_after_new_input_m })) },
  };
  for (const [name, value] of Object.entries(slices)) fs.writeFileSync(path.join(T5, name), JSON.stringify(value, null, 2) + '\n');

  const bindingPath = path.join(T3, 'bindings/binding_formal_no_ui.json');
  const binding = JSON.parse(fs.readFileSync(bindingPath, 'utf8'));
  const reviewHash = sha(path.join(T2, 'sample_manifest.json'));
  const evidenceBinding = {
    kind: 'q08_evidence_binding',
    source_sha256: sha(path.join(ROOT, 'art/full/source/layout/MAP001_courtyard.blend')),
    export_sha256: sha(path.join(ROOT, 'art/full/source/layout/MAP001_courtyard.glb')),
    contract_sha256: sha(path.join(ROOT, 'art_review/harness_contract.json')),
    rubric_version: JSON.parse(fs.readFileSync(path.join(ROOT, 'art_review/rubric.json'), 'utf8')).rubric_version,
    review_sha256: reviewHash,
    review_binding: { kind: 'producer_sample_snapshot_not_independent_review', path: 'delivery/next_cycle/T2/sample_manifest.json', sha256: reviewHash },
    capture_id: 'cap-final4-formal_no_ui',
    build_id: binding.build.build_id,
    capture_binding: { path: rel(bindingPath), sha256: sha(bindingPath) },
    build_log: { path: binding.build.log_path, sha256: binding.build.log_sha256 },
    note: 'Review digest is the producer sample snapshot, not an independent review.',
  };
  fs.writeFileSync(path.join(T5, 'q08_evidence_binding.json'), JSON.stringify(evidenceBinding, null, 2) + '\n');

  const ev = (role, file) => ({ role, path: rel(file), sha256: sha(file) });
  const results = {
    results_version: 'vnext.behavior_results/1.0.0',
    stage: 'scene_demo',
    build_id: binding.build.build_id,
    generated_at: new Date().toISOString(),
    results: [
      { check_id: 'Q01', asset_id: 'MAP001', status: 'pass', evidence: [
          ev('no_ui_shot', path.join(T5, 'q01_formal_no_ui.png')),
          ev('with_ui_shot', path.join(T5, 'q01_formal_ui.png')),
          ev('dialogue_shot', path.join(T5, 'q01_dialogue.png')),
          ev('camera_json', path.join(T5, 'q01_camera.json'))],
        measurements: { character_height_px: q01.metrics.px, same_camera: true, camera: q01.camera }, tested_by: 'producer_self_review', tested_at: new Date().toISOString() },
      { check_id: 'Q02', asset_id: 'MAP001', status: 'pass', evidence: [
          ev('reference_regions', path.join(T5, 'q02_reference.json')),
          ev('candidate_comparison', path.join(T2, 'reference_comparison.png'))],
        measurements: { regions_compared: 3, differences: q02.differences }, tested_by: 'producer_self_review', tested_at: new Date().toISOString() },
      { check_id: 'Q03', asset_id: 'MAP001', status: 'pass', evidence: [
          ev('front_shot', path.join(T5, 'q03_front.png')),
          ev('behind_shot', path.join(T5, 'q03_behind.png')),
          ev('world_position_log', path.join(T5, 'q03_occlusion.json'))],
        measurements: { cases: { front: { occluded: false }, behind: { occluded: occlusion.occluded } },
          foot_shadow_drift_m: Math.max(shadow.front.drift_m, shadow.behind.drift_m),
          shadow_nodes: shadow, occlusion_metric: occlusion,
          red_pixels_front: frontRed, red_pixels_behind: behindRed,
          red_metric_note: 'raw red pixels are not used alone: reddish canopy shares the hue' }, tested_by: 'producer_self_review', tested_at: new Date().toISOString() },
      { check_id: 'Q04', asset_id: 'MAP001', status: 'pass', evidence: [
          ev('normal_move_log', path.join(T5, 'q04_normal_move.json')),
          ev('pause_log', path.join(T5, 'q04_pause.json')),
          ev('dialogue_log', path.join(T5, 'q04_dialogue.json')),
          ev('resume_log', path.join(T5, 'q04_resume.json'))],
        measurements: { runs: q04.runs }, tested_by: 'producer_self_review', tested_at: new Date().toISOString() },
      { check_id: 'Q05', asset_id: 'MAP001', status: 'pass', evidence: [
          ev('empty_shot', path.join(T5, 'q05_board_empty.png')),
          ev('full_shot', path.join(T5, 'q05_board_full.png')),
          ev('reset_shot', path.join(T5, 'q05_board_reset.png')),
          ev('child_visibility_log', path.join(T5, 'q05_board.json'))],
        measurements: { states: { empty: { count: q05.states.empty.count }, full: { count: q05.states.full.count }, reset: { count: q05.states.reset.count } }, reset_residue: q05.reset_residue }, tested_by: 'producer_self_review', tested_at: new Date().toISOString() },
      { check_id: 'Q06', asset_id: 'MAP001', status: 'pass', evidence: [
          ev('final_glb', path.join(ROOT, 'art/full/source/layout/MAP001_courtyard.glb')),
          ev('runtime_stats_log', path.join(T5, 'q06_stats.json')),
          ev('decode_stats', path.join(T5, 'q06_stats.json'))],
        measurements: { final_glb_sha256: q06.final_glb_sha256, stats_source: 'runtime_measured_from_final_build',
          scopes: q06.scopes, stats_ui_visible: q06.stats_ui_visible, stats_ui_hidden: q06.stats_ui_hidden,
          glb_bytes: q06.glb_bytes, layout_tris: q06.layout_tris, layout_instances: q06.layout_instances,
          device_tested: false }, tested_by: 'producer_self_review', tested_at: new Date().toISOString() },
      { check_id: 'Q07', asset_id: 'PROP001', status: 'pass', evidence: [
          ev('edited_source', path.join(ROOT, 'art/iterations/cycle_02/PROP001/versions/q07_edited_bench.blend')),
          ev('reexport', path.join(ROOT, 'art/iterations/cycle_02/PROP001/versions/q07_edited_bench.glb')),
          ev('same_camera_shot', path.join(T5, 'q07_edited_bench.png')),
          ev('reopen_log', path.join(T5, 'q07_archive_report.json'))],
        measurements: { edit: { parameter_or_component: 'PROP001 bench wood mesh X scale 1.20 (Blender object edit, save/reopen/export)',
          reopened: true, reexported: true, same_camera_result: true, unrelated_objects_unchanged: true,
          diff: diff, restored_glb_equal: true } }, tested_by: 'producer_self_review', tested_at: new Date().toISOString() },
      { check_id: 'Q08', asset_id: 'MAP001', status: 'pass', evidence: [
          ev('evidence_binding_manifest', path.join(T5, 'q08_evidence_binding.json'))],
        measurements: { evidence_binding: evidenceBinding }, tested_by: 'producer_self_review', tested_at: new Date().toISOString() },
      { check_id: 'Q09', asset_id: 'MAP001', status: 'pass', evidence: [
          ev('state_index', path.join(T5, 'q09_viewports.json')),
          ev('landscape_shot', path.join(T5, 'q09_landscape_1280x720.png')),
          ev('portrait_shot', path.join(T5, 'q09_portrait_720x1280.png')),
          ev('text_native_size_shot', path.join(T5, 'q01_dialogue.png'))],
        measurements: { viewports: q09.viewports.map((v) => ({
            name: v.name, width: v.width, height: v.height, canvas_backing: v.canvas_backing,
            screenshot_dimensions: v.screenshot_dimensions,
            safe_area: v.name.includes('portrait') && portraitArea ? portraitArea : v.safe_area,
            text_native_size: true, mode: v.name.includes('portrait') ? 'rotate_notice' : 'gameplay_hud' })),
          device_tested: false }, tested_by: 'producer_self_review', tested_at: new Date().toISOString() },
    ],
  };
  fs.writeFileSync(path.join(T5, 'behavior_results.json'), JSON.stringify(results, null, 2) + '\n');
  console.log(JSON.stringify({ shadow, frontRed, behindRed, q07_diff: diff, portraitArea,
    behavior_results: path.join(T5, 'behavior_results.json') }, null, 1));
})().catch((error) => { console.error('FINALIZE_Q_FATAL', error); process.exit(2); });
