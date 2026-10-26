/*
 * Render every DEMO UI state at 1:1 design pixels with headless Chrome, run layout/font
 * assertions, and build the state index + contact sheet.
 *
 * Usage:
 *   node tools/ui/build_ui.js
 *   node tools/ui/render_ui_previews.js
 *
 * Outputs (all preview/export only):
 *   art/full/previews/ui/<state_id>.png     (1280x720, or 720x1280 for rotate_notice)
 *   art/full/previews/ui/state_index.json
 *   art/full/previews/ui/contact_sheet.png
 *   art/full/previews/ui/render_log.txt
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { pathToFileURL } = require('url');

const ROOT = path.resolve(__dirname, '..', '..');
const UI = path.join(ROOT, 'art', 'candidates', 'candidate_n5', 'ui');
const OUT = path.join(ROOT, 'art', 'candidates', 'candidate_n5', 'previews', 'ui');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const puppeteer = require(path.join(ROOT, '.tooling', 'node_modules', 'puppeteer-core'));
const sharp = require(path.join(ROOT, '.tooling', 'node_modules', 'sharp'));

const pkg = name => JSON.parse(fs.readFileSync(path.join(ROOT, '.tooling', 'node_modules', name, 'package.json'), 'utf8')).version;
const sha = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const bytes = p => fs.statSync(p).size;
const rel = p => path.relative(ROOT, p).split(path.sep).join('/');

const COVERAGE = {
  'tokens: colors/fonts/type/line/spacing/safe/component states': ['spec_type', 'spec_icons', 'safe_area_landscape'],
  'title: initial / pressed / loading': ['title_initial', 'title_pressed', 'title_loading'],
  'loading: progress / failure / retry': ['loading_progress', 'loading_failure', 'loading_retry_pressed'],
  'quest HUD: talk / 0-3 / 1-3 / 2-3 / 3-3 / submit / done': ['hud_talk', 'hud_0_3', 'hud_1_3', 'hud_2_3', 'hud_3_3', 'hud_submit', 'hud_done'],
  'interaction: talk / pick / place / view / pressed / disabled / hidden': ['interact_talk', 'interact_pick', 'interact_place', 'interact_view', 'interact_pressed', 'interact_disabled', 'interact_hidden'],
  'joystick: idle / drag / hidden': ['joystick_idle', 'joystick_drag', 'joystick_hidden'],
  'dialogue: two speakers, pages, accept': ['dialogue_gardener_p1', 'dialogue_player_p2', 'dialogue_accept_pressed'],
  'pause: resume / mute on / mute off / restart': ['pause_default', 'pause_sound_on', 'pause_restart_pressed'],
  'complete: three cards / continue / restart': ['complete_default', 'complete_continue_pressed'],
  'toasts: pickup / task update / error-retry': ['toast_pickup', 'toast_task_update', 'toast_error'],
  'first-use: move / interact': ['tip_first_move', 'tip_first_interact'],
  'rotation / safe area': ['safe_area_landscape', 'rotate_notice'],
  'paper nine-slice + separate decorations': ['spec_nine_slice'],
  'editable icons 24/32/48': ['spec_icons']
};

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const pageErrors = [];
  const consoleErrors = [];
  const failedRequests = [];

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars', '--allow-file-access-from-files', '--force-color-profile=srgb',
      '--font-render-hinting=none', '--disable-lcd-text']
  });
  const chromeVersion = await browser.version();
  const page = await browser.newPage();
  page.on('pageerror', e => pageErrors.push(String(e)));
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  page.on('requestfailed', req => failedRequests.push(req.url() + ' :: ' + (req.failure() && req.failure().errorText)));

  await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1 });
  const startUrl = pathToFileURL(path.join(UI, 'states.html')).href + '?state=title_initial&preview=1';
  await page.goto(startUrl, { waitUntil: 'load', timeout: 30000 });
  await page.evaluate(() => document.fonts.ready);

  const meta = await page.evaluate(() => {
    const out = [];
    UI_STATE_ORDER.forEach(id => {
      const s = UI_STATES[id];
      out.push({
        id: s.id, group: s.group, label: s.label, size: s.size,
        desc: s.desc, copy: s.copy || [], components: s.components || []});
    });
    return out;
  });

  const fontInfo = await page.evaluate(async () => {
    await document.fonts.ready;
    const body = document.querySelector('body');
    return {
      status: document.fonts.status,
      faces: Array.from(document.fonts).map(f => ({ family: f.family, weight: f.weight, status: f.status })),
      bodyFamily: getComputedStyle(body).fontFamily
    };
  });

  const results = [];
  const logLines = [];
  logLines.push('秋庭来信 UI kit — headless Chrome preview render log');
  logLines.push('generated_at: ' + new Date().toISOString());
  logLines.push('producer: Qoder execution agent (self-check only; not independent review)');
  logLines.push('');
  logLines.push('COMMANDS');
  logLines.push('  node tools/ui/build_ui.js');
  logLines.push('  node tools/ui/render_ui_previews.js');
  logLines.push('');
  logLines.push('TOOLCHAIN');
  logLines.push('  node ' + process.version);
  logLines.push('  puppeteer-core ' + pkg('puppeteer-core'));
  logLines.push('  sharp ' + pkg('sharp'));
  logLines.push('  Chrome ' + chromeVersion);
  logLines.push('  fonts: local Noto Sans SC / Noto Serif SC via css/preview_fonts.css');
  logLines.push('  font status: ' + fontInfo.status + '; body stack: ' + fontInfo.bodyFamily);
  logLines.push('  font faces: ' + fontInfo.faces.map(f => `${f.family} ${f.weight} ${f.status}`).join(' | '));
  logLines.push('');
  logLines.push('PER-STATE RESULTS');

  for (const s of meta) {
    pageErrors.length = 0; consoleErrors.length = 0; failedRequests.length = 0;
    const [w, h] = s.size;
    await page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });
    await page.evaluate(id => window.renderState(id), s.id);
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all(Array.from(document.images).map(img => (img.complete && img.naturalWidth > 0)
        ? Promise.resolve()
        : new Promise(resolve => { img.onload = resolve; img.onerror = resolve; })));
      await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    });
    await wait(30);

    const checks = await page.evaluate(({ w, h }) => {
      const errors = [];
      const warnings = [];
      const stage = document.getElementById('stage');
      const body = document.body;
      const sr = stage.getBoundingClientRect();
      if (Math.round(sr.width) !== w || Math.round(sr.height) !== h) {
        errors.push(`stage is ${Math.round(sr.width)}x${Math.round(sr.height)}, expected ${w}x${h}`);
      }
      if (body.scrollWidth > w + 1 || body.scrollHeight > h + 1) {
        errors.push(`body scroll ${body.scrollWidth}x${body.scrollHeight} exceeds ${w}x${h}`);
      }
      if (stage.scrollWidth > w + 1 || stage.scrollHeight > h + 1) {
        errors.push(`stage content ${stage.scrollWidth}x${stage.scrollHeight} exceeds ${w}x${h}`);
      }

      const imgs = Array.from(document.images);
      imgs.forEach(img => {
        if (!img.complete || img.naturalWidth === 0) errors.push(`image not loaded: ${img.getAttribute('src')}`);
      });

      const buttons = Array.from(document.querySelectorAll('button')).filter(b => {
        const r = b.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
      });
      buttons.forEach(b => {
        const r = b.getBoundingClientRect();
        if (Math.min(r.width, r.height) < 47.5) {
          errors.push(`touch target ${Math.round(r.width)}x${Math.round(r.height)} < 48: ${b.getAttribute('aria-label') || b.textContent.trim().slice(0, 24)}`);
        }
        const name = b.getAttribute('aria-label') || b.textContent.trim();
        if (!name) errors.push('button without accessible name');
      });

      const textSelectors = ['.dialogue__text', '.title-card__subtitle', '.hud__title', '.hud__sub', '.tip__body',
        '.toast__title', '.toast__sub', '.error-box', '.failure-card__body', '.complete__quote', '.pause__sub',
        '.type-row__sample', '.rotate-card__body'];
      textSelectors.forEach(sel => {
        document.querySelectorAll(sel).forEach(el => {
          if (el.scrollWidth > el.clientWidth + 1) warnings.push(`text may be clipped horizontally: ${sel}`);
          if (el.scrollHeight > el.clientHeight + 1 && getComputedStyle(el).overflowY === 'hidden') {
            warnings.push(`text may be clipped vertically: ${sel}`);
          }
        });
      });

      document.querySelectorAll('.paper__deco, .tip__arrow, .anno, .backdrop__label').forEach(el => el.dataset.allowOverflow = '1');
      const clipped = [];
      document.querySelectorAll('#app *').forEach(el => {
        if (el.dataset.allowOverflow) return;
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') return;
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return;
        if (r.left < -1 || r.top < -1 || r.right > w + 1 || r.bottom > h + 1) {
          clipped.push(el.className || el.tagName);
        }
      });
      if (clipped.length) warnings.push('elements outside stage: ' + Array.from(new Set(clipped)).slice(0, 6).join(', '));

      const bodyFont = getComputedStyle(document.querySelector('.t-body') || body).fontFamily;
      const nameEl = document.querySelector('.dialogue__speaker');
      const nameFont = nameEl ? getComputedStyle(nameEl).fontFamily : null;
      if (!bodyFont.includes('Noto Sans SC')) errors.push('body sample is not using Noto Sans SC: ' + bodyFont);
      if (nameFont && !nameFont.includes('Noto Serif SC')) errors.push('speaker name is not using Noto Serif SC: ' + nameFont);

      return {
        errors, warnings,
        counts: {
          buttons: buttons.length,
          images: imgs.length,
          images_ok: imgs.filter(i => i.complete && i.naturalWidth > 0).length,
          papers: document.querySelectorAll('.paper').length,
          svg_icons: document.querySelectorAll('.icon svg').length
        },
        fonts: { body: bodyFont, name: nameFont },
        stage: { width: Math.round(sr.width), height: Math.round(sr.height) },
        body_scroll: { width: body.scrollWidth, height: body.scrollHeight }
      };
    }, { w, h });

    const file = path.join(OUT, s.id + '.png');
    await page.screenshot({ path: file, type: 'png', fullPage: false, clip: { x: 0, y: 0, width: w, height: h } });
    const sm = await sharp(file).metadata();
    if (sm.width !== w || sm.height !== h) checks.errors.push(`PNG ${sm.width}x${sm.height} != ${w}x${h}`);

    const runtimeErrors = [...pageErrors, ...consoleErrors, ...failedRequests];
    if (runtimeErrors.length) checks.errors.push(...runtimeErrors);

    const ok = checks.errors.length === 0;
    results.push({
      id: s.id, group: s.group, label: s.label, desc: s.desc, copy: s.copy, components: s.components,
      canvas: { width: w, height: h },
      preview: 'art/full/previews/ui/' + s.id + '.png',
      preview_sha256: sha(file),
      preview_bytes: bytes(file),
      checks: { ok, errors: checks.errors, warnings: checks.warnings, counts: checks.counts, fonts: checks.fonts }
    });
    logLines.push(`${ok ? 'PASS' : 'FAIL'}  ${s.id.padEnd(28)} ${w}x${h}  buttons=${checks.counts.buttons} images=${checks.counts.images_ok}/${checks.counts.images} papers=${checks.counts.papers}`);
    checks.errors.forEach(e => logLines.push('    ERROR ' + e));
    checks.warnings.forEach(e => logLines.push('    warn  ' + e));
  }

  // Contact sheet is rendered as HTML so labels use the real Noto faces too.
  const cols = 6;
  const tileW = 384;
  const gap = 16;
  const sheetWidth = 56 + cols * tileW + (cols - 1) * gap;
  const cards = results.map(r => {
    const portrait = r.canvas.height > r.canvas.width;
    return `<figure class="tile">
      <div class="tile__img ${portrait ? 'portrait' : ''}"><img src="./${r.id}.png" alt="${r.label}"></div>
      <figcaption><b>${r.label}</b><span>${r.id}</span><em>${r.canvas.width}×${r.canvas.height}${portrait ? ' · portrait' : ''}</em></figcaption>
    </figure>`;
  }).join('\n');
  const passed = results.filter(r => r.checks.ok).length;
  const warnings = results.reduce((n, r) => n + r.checks.warnings.length, 0);
  const sheetHtml = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>
    @font-face{font-family:"Noto Sans SC";src:url("file:///C:/Windows/Fonts/NotoSansSC-VF.ttf") format("truetype");font-weight:100 900;font-display:block}
    @font-face{font-family:"Noto Serif SC";src:url("file:///C:/Windows/Fonts/NotoSerifSC-VF.ttf") format("truetype");font-weight:100 900;font-display:block}
    *{box-sizing:border-box} body{margin:0;background:#211f1b;color:#F3F0E6;font-family:"Noto Sans SC",sans-serif;padding:28px}
    .head{display:flex;align-items:flex-end;gap:24px;border-bottom:1px solid rgba(250,248,241,.18);padding-bottom:16px;margin-bottom:18px}
    .eyebrow{font-size:11px;letter-spacing:3px;color:#D8AA58;font-weight:600;margin-bottom:6px}
    h1{font-family:"Noto Serif SC",serif;font-size:34px;line-height:42px;font-weight:600;letter-spacing:2px;margin:0 0 4px}
    .sub{font-size:12px;line-height:19px;color:rgba(243,240,230,.62)}
    .stats{margin-left:auto;text-align:right;font-size:11px;line-height:19px;color:rgba(243,240,230,.58)}
    .stats b{color:#9FD8C8;font-size:18px;font-weight:600}
    .badge{display:inline-block;border:1px solid rgba(216,170,88,.5);color:#E8C88C;font-size:10px;letter-spacing:1.2px;padding:2px 7px;margin-left:5px}
    .grid{display:grid;grid-template-columns:repeat(${cols},${tileW}px);gap:${gap}px}
    .tile{margin:0;background:rgba(250,248,241,.045);border:1px solid rgba(250,248,241,.11);padding:8px}
    .tile__img{height:216px;display:flex;align-items:center;justify-content:center;background:#14130f;overflow:hidden}
    .tile__img img{width:100%;height:100%;object-fit:contain;display:block}
    .tile__img.portrait img{width:auto;height:216px}
    figcaption{display:grid;grid-template-columns:1fr auto;gap:1px 8px;padding:7px 2px 1px}
    figcaption b{font-size:12px;font-weight:600;color:#F3F0E6;letter-spacing:.2px}
    figcaption span{font-size:9px;color:rgba(243,240,230,.38);grid-column:1;letter-spacing:.2px}
    figcaption em{font-style:normal;font-size:9px;color:rgba(159,216,200,.62);grid-column:2;grid-row:1 / span 2;align-self:center}
    .foot{margin-top:20px;padding-top:12px;border-top:1px solid rgba(250,248,241,.12);font-size:10px;line-height:17px;color:rgba(243,240,230,.42)}
  </style></head><body>
    <div class="head">
      <div><div class="eyebrow">秋庭来信 · COURTYARD CHAPTER</div><h1>UI 状态联系表 / STATE CONTACT SHEET</h1>
      <div class="sub">1280×720 设计与预览 · HTML/CSS/SVG 源 · PNG 仅作预览 · Noto Sans SC / Noto Serif SC 实际中文渲染</div></div>
      <div class="stats"><b>${results.length}</b> states · ${passed} checks pass · ${warnings} warnings<br>
        <span class="badge">NO COCOS VERIFICATION</span><span class="badge">NOT APPROVED</span><span class="badge">PORTRAITS PENDING</span></div>
    </div>
    <div class="grid">${cards}</div>
    <div class="foot">Preview-only. Scene backdrop is a labelled stand-in, not final environment art. Portrait slots are empty; no AI faces and no crop of the old A-stage character. Fonts are local preview installs and must be embedded/licensed before release. Generated by tools/ui/render_ui_previews.js — self-check, not independent review.</div>
  </body></html>`;
  const sheetPath = path.join(OUT, '_contact_sheet.html');
  fs.writeFileSync(sheetPath, sheetHtml, 'utf8');
  const sheetPage = await browser.newPage();
  await sheetPage.setViewport({ width: sheetWidth, height: 900, deviceScaleFactor: 1 });
  await sheetPage.goto(pathToFileURL(sheetPath).href, { waitUntil: 'load', timeout: 30000 });
  await sheetPage.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(Array.from(document.images).map(img => img.complete ? Promise.resolve() : new Promise(r => { img.onload = r; img.onerror = r; })));
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  });
  await sheetPage.screenshot({ path: path.join(OUT, 'contact_sheet.png'), fullPage: true });
  const sheetMeta = await sharp(path.join(OUT, 'contact_sheet.png')).metadata();
  await sheetPage.close();
  await browser.close();

  const index = {
    name: '秋庭来信 UI kit state index',
    version: '0.1.0',
    generated_at: new Date().toISOString(),
    status: 'preview_only_unapproved',
    design_canvas: '1280x720 landscape',
    coverage: COVERAGE,
    summary: {
      total: results.length,
      checks_pass: passed,
      checks_fail: results.length - passed,
      warnings,
      preview_dpr: 1,
      contact_sheet: { path: 'art/full/previews/ui/contact_sheet.png', width: sheetMeta.width, height: sheetMeta.height }
    },
    toolchain: {
      chrome: chromeVersion,
      node: process.version,
      puppeteer_core: pkg('puppeteer-core'),
      sharp: pkg('sharp'),
      renderer: 'tools/ui/render_ui_previews.js',
      builder: 'tools/ui/build_ui.js'
    },
    fonts: {
      body: 'Noto Sans SC (variable, local preview install; embed + subset before release)',
      display: 'Noto Serif SC (variable, local preview install; embed + subset before release)',
      observed_status: fontInfo.status,
      observed_faces: fontInfo.faces
    },
    limitations: [
      'No Cocos Creator scene, no WeChat DevTools and no device verification. These are browser-rendered PNG previews of HTML/CSS/SVG sources.',
      'The scene backdrop is an explicitly labelled stand-in, not final environment art.',
      'Player portrait uses the approved 1015_aglna2 runtime head crop; gardener portrait uses a real P1 t054 reference crop. The full-body gardener static slice is still candidate (mask edge review pending). No AI faces; no old A-stage character crop.',
      'Fonts are installed locally for preview only. Release requires OFL-licensed embedded subsets under the WeChat package budget.',
      'The UI source is a draft and has not been approved by the controller or an independent reviewer.',
      'Safe areas and the WeChat capsule exclusion are design values; they require real device/build verification.'
    ],
    states: results
  };
  fs.writeFileSync(path.join(OUT, 'state_index.json'), JSON.stringify(index, null, 2) + '\n', 'utf8');

  logLines.push('');
  logLines.push(`SUMMARY ${passed}/${results.length} pass, ${results.length - passed} fail, ${warnings} warnings`);
  logLines.push('CONTACT SHEET art/full/previews/ui/contact_sheet.png ' + sheetMeta.width + 'x' + sheetMeta.height);
  logLines.push('LIMITATIONS: no Cocos/WeChat/device verification; scene stand-in; portraits integrated from approved/candidate real sources; fonts preview-only; UI not approved.');
  fs.writeFileSync(path.join(OUT, 'render_log.txt'), logLines.join('\n') + '\n', 'utf8');

  console.log(logLines.join('\n'));
  if (passed !== results.length) process.exitCode = 1;
})();
