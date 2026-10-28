#!/usr/bin/env node
/**
 * S6 合成：把角色与 UI 叠到渲染图上（不进 Blender，改文案/挪按钮不用重渲 50 秒）。
 *
 * 输入：clean.png（渲染 + 后处理；冻结 LUT 尚未接入，接上后才是完整的 clean）
 * 输出：final_ui.png（+ 角色层 layer_char.png，供分层交付）
 *
 * 注意：当前没有 --no-ui 开关，UI 与角色是一次性烧进 final_ui.png 的；
 * 要单独出 UI 层或纯角色图，需要新增参数（见 PRESENTATION_CHECK.md P-10）。
 *
 * 角色用切片立绘（npc_gardener_slice），因为 Spine 首帧导出需要引擎侧渲染；
 * 静态图只需一张正面待机，切片与选集里其它资产同源，混用成本最低。
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const sharp = createRequire(path.resolve(__dirname, '../../.tooling/package.json'))('sharp');

const ROOT = 'C:/软件/鼠鼠';
const IN = process.argv[2] || path.join(ROOT, 'art/static_map/p1_autumn_courtyard/v03/renders/clean.png');
const OUT = process.argv[3] || path.join(ROOT, 'art/static_map/p1_autumn_courtyard/v03/renders/final_ui.png');
const CHAR = path.join(ROOT, 'demo_n5s1/assets/resources/char/npc_gardener_slice.png');
const PANEL = path.join(ROOT, 'demo_n5s1/assets/resources/ui/paper_panel_wash.png');

const W = 1920, H = 1078;
// 角色站位对齐参考 R13 [47,38,56,52]：脚底 y≈570（原来 712，低了 13%），
// 身高 162px（原来 256，比参考的 150px 大一档，会把广场压掉）。
const FEET = { x: 988, y: 570 };
const CHAR_H = 162;

(async () => {
    // ---------- 1. 角色：缩放 + 轻微暖调，融入场景 ----------
    const ch = await sharp(CHAR)
        .resize({ height: CHAR_H, fit: 'inside', background: { r: 0, g: 0, b: 0, alpha: 0 } })
        .modulate({ saturation: 1.05, brightness: 1.26 })
        .png().toBuffer();
    const cm = await sharp(ch).metadata();

    // ---------- 2. 接触阴影 + 选中框（先铺在角色下面） ----------
    const shW = Math.round(cm.width * 1.15), shH = 34;
    const shadowSvg = `<svg width="${shW}" height="${shH}" xmlns="http://www.w3.org/2000/svg">
      <defs><radialGradient id="g"><stop offset="0" stop-color="#241a12" stop-opacity="0.62"/>
      <stop offset="1" stop-color="#241a12" stop-opacity="0"/></radialGradient></defs>
      <ellipse cx="${shW / 2}" cy="${shH / 2}" rx="${shW / 2 - 2}" ry="${shH / 2 - 2}" fill="url(#g)"/></svg>`;
    const shadow = await sharp(Buffer.from(shadowSvg)).blur(6).png().toBuffer();

    const ringW = Math.round(cm.width * 1.30), ringH = 44;
    const ringSvg = `<svg width="${ringW}" height="${ringH}" xmlns="http://www.w3.org/2000/svg">
      <ellipse cx="${ringW / 2}" cy="${ringH / 2}" rx="${ringW / 2 - 3}" ry="${ringH / 2 - 3}"
       fill="none" stroke="#4fd1c5" stroke-width="3" stroke-dasharray="26 16" opacity="0.85"/></svg>`;
    const ring = await sharp(Buffer.from(ringSvg)).png().toBuffer();

    // ---------- 3. UI：纸面板 + 文案 + 顶部条 + 右下按钮 ----------
    const panel = await sharp(PANEL).resize({ width: 430 }).png().toBuffer();
    const pm = await sharp(panel).metadata();

    const uiSvg = `<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg">
      <style>
        .t1 { font-family: "Microsoft YaHei","Noto Sans SC",sans-serif; font-weight:700; }
        .t2 { font-family: "Microsoft YaHei","Noto Sans SC",sans-serif; font-weight:400; }
      </style>
      <!-- 顶部状态条：图标 + 场景名 + 进度点 + 分隔线（参考图顶部本身就有密集 UI） -->
      <rect x="0" y="0" width="${W}" height="64" fill="#1a1510" opacity="0.58"/>
      <rect x="0" y="62" width="${W}" height="2" fill="#e8d9bd" opacity="0.22"/>
      <rect x="26" y="18" width="28" height="28" rx="6" fill="none" stroke="#e8d9bd" stroke-width="2" opacity="0.6"/>
      <line x1="32" y1="26" x2="48" y2="26" stroke="#e8d9bd" stroke-width="2" opacity="0.55"/>
      <line x1="32" y1="32" x2="44" y2="32" stroke="#e8d9bd" stroke-width="2" opacity="0.55"/>
      <line x1="32" y1="38" x2="48" y2="38" stroke="#e8d9bd" stroke-width="2" opacity="0.55"/>
      <text x="70" y="40" class="t2" font-size="22" fill="#f2e9d8" opacity="0.94">秋日庭院 · 午后</text>
      <text x="238" y="40" class="t2" font-size="19" fill="#f2e9d8" opacity="0.55">探索模式</text>
      <line x1="330" y1="18" x2="330" y2="46" stroke="#e8d9bd" stroke-width="1.5" opacity="0.3"/>
      <circle cx="358" cy="32" r="6" fill="#e8d9bd" opacity="0.9"/>
      <circle cx="380" cy="32" r="6" fill="#e8d9bd" opacity="0.45"/>
      <circle cx="402" cy="32" r="6" fill="#e8d9bd" opacity="0.45"/>
      <text x="422" y="39" class="t2" font-size="19" fill="#e8d9bd" opacity="0.6">1 / 3</text>
      <text x="${W - 30}" y="40" class="t2" font-size="20" fill="#f2e9d8" opacity="0.7" text-anchor="end">ESC 返回</text>
      <line x1="${W - 130}" y1="18" x2="${W - 130}" y2="46" stroke="#e8d9bd" stroke-width="1.5" opacity="0.3"/>
      <!-- 任务卡文案（面板图另叠） -->
      <text x="96" y="150" class="t2" font-size="21" fill="#6b533a" opacity="0.85">当前任务</text>
      <text x="96" y="196" class="t1" font-size="35" fill="#3a2a1b">找到落脚处</text>
      <line x1="96" y1="214" x2="430" y2="214" stroke="#8a6a48" stroke-width="2" opacity="0.35"/>
      <text x="96" y="252" class="t2" font-size="25" fill="#54402c">打扫庭院　(1/3)</text>
      <!-- 右下按钮 -->
      <rect x="${W - 300}" y="${H - 132}" width="212" height="66" rx="33" fill="#2c2118" opacity="0.88"/>
      <rect x="${W - 300}" y="${H - 132}" width="212" height="66" rx="33" fill="none" stroke="#e8d9bd" stroke-width="2" opacity="0.45"/>
      <text x="${W - 194}" y="${H - 89}" class="t1" font-size="27" fill="#f6eddb" text-anchor="middle">打 开</text>
      <!-- 左下图标条 -->
      <circle cx="86" cy="${H - 96}" r="30" fill="#2c2118" opacity="0.8"/>
      <circle cx="86" cy="${H - 96}" r="30" fill="none" stroke="#e8d9bd" stroke-width="2" opacity="0.35"/>
      <circle cx="164" cy="${H - 96}" r="30" fill="#2c2118" opacity="0.8"/>
      <circle cx="164" cy="${H - 96}" r="30" fill="none" stroke="#e8d9bd" stroke-width="2" opacity="0.35"/>
    </svg>`;
    const ui = await sharp(Buffer.from(uiSvg)).png().toBuffer();

    // 左下两个图标（原来只是两个空圆，看着没做完）
    const iconPaths = [
        path.join(ROOT, 'demo_n5s1/assets/resources/ui/icons/icon_check.png'),
        path.join(ROOT, 'demo_n5s1/assets/resources/ui/deco_leaf.png'),
    ];
    const icons = [];
    for (let i = 0; i < 2; i++) {
        if (!fs.existsSync(iconPaths[i])) continue;
        const buf = await sharp(iconPaths[i]).resize({ width: 34, height: 34, fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
            .png().toBuffer();
        icons.push({ input: buf, left: 86 + i * 78 - 17, top: H - 96 - 17, blend: 'over' });
    }

    // ---------- 4. 合成顺序：底图 → 阴影 → 选中框 → 角色 → 面板 → UI ----------
    const base = await sharp(IN).resize({ width: W, height: H }).png().toBuffer();
    const charLayer = await sharp({ create: { width: W, height: H, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } })
        .composite([{ input: ch, left: Math.round(FEET.x - cm.width / 2), top: FEET.y - cm.height }])
        .png().toBuffer();

    await sharp(base)
        .composite([
            { input: shadow, left: Math.round(FEET.x - shW / 2), top: FEET.y - shH / 2, blend: 'over' },
            { input: ring, left: Math.round(FEET.x - ringW / 2), top: FEET.y - ringH / 2, blend: 'over' },
            { input: charLayer, left: 0, top: 0 },
            { input: panel, left: 52, top: 92, blend: 'over' },
            { input: ui, left: 0, top: 0, blend: 'over' },
            ...icons,
        ])
        .png().toFile(OUT);

    // 角色单独存一层，供分层交付
    await sharp(charLayer).png().toFile(path.join(path.dirname(OUT), 'layer_char.png'));

    console.log('合成完成 → ' + OUT);
    console.log('  角色 ' + cm.width + 'x' + cm.height + '  脚底 (' + FEET.x + ',' + FEET.y + ')');
})();
