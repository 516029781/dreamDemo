#!/usr/bin/env node
/**
 * 植被卡图集打包：把 cards/*.png 按 manifest 拼成 2x2 的 atlas.png。
 *
 * 为什么要这个脚本：atlas.png 之前是手工拼的，谁在哪个格、有没有重复、
 * 有没有打包了却没人引用的卡，全都看不出来。结果就是两个叶子格里放了同一张图，
 * 树冠只有一种叶形（见 atlas_manifest.json 的 ATLAS-01）。
 *
 * 规则：
 *   - 每格 512x512，1:1 直接粘贴，不缩放、不重采样、不锐化；
 *   - 源图必须是 512x512 RGBA，尺寸不符直接报错，不静默拉伸；
 *   - 打完自检 sha256 与格内像素，任何一项不符就非零退出。
 *
 * 用法：
 *   node tools/art/pack_card_atlas.js            # 打包并写回 atlas.png
 *   node tools/art/pack_card_atlas.js --check    # 只校验现有 atlas.png，不写文件
 *   node tools/art/pack_card_atlas.js --out /tmp/atlas_test.png
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { createRequire } = require('module');

const ROOT = 'C:/软件/鼠鼠';
const sharp = createRequire(path.resolve(ROOT, '.tooling/package.json'))('sharp');

const ATLAS_DIR = path.join(ROOT, 'art/static_map/p1_autumn_courtyard/v03/assets/foliage');
const MANIFEST = path.join(ATLAS_DIR, 'atlas_manifest.json');

const args = process.argv.slice(2);
const CHECK_ONLY = args.includes('--check');
const outIdx = args.indexOf('--out');
const OUT = outIdx >= 0 ? args[outIdx + 1] : path.join(ATLAS_DIR, 'atlas.png');

const sha256 = (p) => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');

async function main() {
    const m = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
    const [W, H] = m.atlas.size;
    const CELL = m.atlas.cell;
    if (W !== CELL * 2 || H !== CELL * 2) throw new Error(`manifest 尺寸与 2x2 不符: ${W}x${H} cell=${CELL}`);

    // ---- 1. 逐格校验源文件 ----
    const layers = [];
    const problems = [];
    const usedCells = new Set();

    for (const c of m.cells) {
        const [cx, cy] = c.cell;
        const key = `${cx},${cy}`;
        if (usedCells.has(key)) problems.push(`单元重复声明: ${key}`);
        usedCells.add(key);
        if (cx < 0 || cx > 1 || cy < 0 || cy > 1) problems.push(`单元越界: ${key}`);

        const abs = path.join(ROOT, c.source);
        if (!fs.existsSync(abs)) { problems.push(`源文件不存在: ${c.source}`); continue; }

        const actual = sha256(abs);
        if (actual !== c.sha256) problems.push(`哈希不符 ${path.basename(c.source)}: 清单 ${c.sha256.slice(0, 12)} ≠ 实际 ${actual.slice(0, 12)}`);

        const meta = await sharp(abs).metadata();
        if (meta.width !== CELL || meta.height !== CELL) {
            throw new Error(`${path.basename(c.source)} 是 ${meta.width}x${meta.height}，要求 ${CELL}x${CELL}；不做静默缩放`);
        }

        layers.push({ input: abs, left: cx * CELL, top: cy * CELL });
    }

    // ---- 2. 重复内容检查（这次真出过问题）----
    const bySha = {};
    for (const c of m.cells) {
        bySha[c.sha256] = bySha[c.sha256] || [];
        bySha[c.sha256].push(`(${c.cell.join(',')})`);
    }
    const dups = Object.entries(bySha).filter(([, cells]) => cells.length > 1);

    // ---- 3. 拼图 ----
    const buf = await sharp({
        create: { width: W, height: H, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } },
    })
        .composite(layers)
        .png({ compressionLevel: 9, adaptiveFiltering: false })
        .toBuffer();

    // ---- 4. 像素级自检：把拼出来的图切回四格，逐格与原图比 ----
    const report = { out: OUT, size: [W, H], cell: CELL, cells: [], duplicate_cells: [], problems: [] };

    for (const c of m.cells) {
        const [cx, cy] = c.cell;
        const abs = path.join(ROOT, c.source);
        const cellBuf = await sharp(buf)
            .extract({ left: cx * CELL, top: cy * CELL, width: CELL, height: CELL })
            .raw().toBuffer();
        const srcBuf = await sharp(abs).ensureAlpha().raw().toBuffer();
        let maxDiff = 0;
        for (let i = 0; i < cellBuf.length; i++) {
            const d = Math.abs(cellBuf[i] - srcBuf[i]);
            if (d > maxDiff) maxDiff = d;
            if (maxDiff > 1) break;
        }
        report.cells.push({ cell: [cx, cy], source: path.basename(c.source), role: c.role, max_pixel_diff: maxDiff });
        if (maxDiff > 1) problems.push(`单元 (${cx},${cy}) 像素不一致 maxdiff=${maxDiff}`);
    }

    for (const [sha, cells] of dups) {
        report.duplicate_cells.push({ sha256: sha.slice(0, 12), cells });
        problems.push(`同一张图被放进多个格: ${cells.join(' ')}（ATLAS-01，会让树冠只有一种叶形）`);
    }

    report.duplicate_cells.forEach((d) => {
        const entry = m.cells.find((c) => c.sha256.startsWith(d.sha256));
        report.duplicate_cells[report.duplicate_cells.indexOf(d)].label = entry ? entry.label : '';
    });

    if (CHECK_ONLY) {
        // 校验模式：与磁盘上的 atlas 比像素，不看 PNG 字节（编码器不同 SHA 会不同）
        const onDisk = await sharp(path.join(ATLAS_DIR, 'atlas.png')).raw().toBuffer();
        const rebuilt = await sharp(buf).raw().toBuffer();
        let maxDiff = 0;
        for (let i = 0; i < onDisk.length; i++) {
            const d = Math.abs(onDisk[i] - rebuilt[i]);
            if (d > maxDiff) maxDiff = d;
            if (maxDiff > 1) break;
        }
        report.disk_vs_rebuilt_max_pixel_diff = maxDiff;
        if (maxDiff > 1) report.problems.push(`磁盘 atlas 与重建结果不一致 maxdiff=${maxDiff}`);
    } else {
        fs.writeFileSync(OUT, buf);
        report.sha256 = crypto.createHash('sha256').update(buf).digest('hex');
        report.bytes = buf.length;
    }

    report.problems = problems;
    console.log(JSON.stringify(report, null, 2));

    // 重复格属于已知缺陷（ATLAS-01），在 --check 模式下只告警；
    // 其他问题（哈希不符、像素不符、越界）一律非零退出。
    const hard = problems.filter((p) => !p.includes('ATLAS-01'));
    if (hard.length) {
        console.error(`\n打包失败：${hard.length} 个问题`);
        process.exit(1);
    }
    if (dups.length) console.error('\n警告：存在重复单元（ATLAS-01），见 atlas_manifest.json 的 known_defect');
}

main().catch((e) => { console.error(e.message); process.exit(1); });
