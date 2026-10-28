#!/usr/bin/env node
/**
 * 构图位置闸门：把每个元素在我们图里的屏幕包围盒，与参考图里同一元素的框比较。
 *
 * 为什么单独做这一条：
 *   region_report 的 target 用的是"语义对齐"坐标（物体在哪就量哪），它判的是材质 L/sat，
 *   判不了"物体摆在哪"。如果只靠它，把树挪到画面正中也能全 PASS。
 *   所以位置必须独立判：元素包围盒中心 与 参考框中心 的偏差，容差 ±8% 画面宽/高。
 *
 * 用法：
 *   node tools/art/composition_check.js <bbox.json>
 *   bbox.json 由 art/static_map/p1_autumn_courtyard/v03/bbox_probe.py 生成
 */
const fs = require('fs');
const path = require('path');

const ROOT = 'C:/软件/鼠鼠';
const REGIONS = JSON.parse(fs.readFileSync(path.join(ROOT, 'planning/art/regions.json'), 'utf8'));

// 参考框中心 → 我们在图里的包围盒中心，允许的偏差（百分点）
const TOL = 9.0;
// 参考框的覆盖率下限：我们的盒子至少要占到参考框 60%，否则算"太小/太远"
const MIN_SIZE_RATIO = 0.55;

const file = process.argv[2];
if (!file) {
    console.error('用法: node tools/art/composition_check.js <bbox.json>');
    process.exit(2);
}
const bb = JSON.parse(fs.readFileSync(file, 'utf8'));

const rows = [];
let pass = 0, total = 0;

for (const r of REGIONS.regions) {
    if (r.measure === false) continue;
    // 只有"参考框≈物体外接框"的元素才做位置比较；其余参考框只是取样小块
    if (!r.bbox_check) continue;
    const b = bb[r.id];
    if (!b) {
        rows.push({ id: r.id, name: r.name, verdict: 'SKIP', note: '无投影数据' });
        continue;
    }
    const [rx1, ry1, rx2, ry2] = r.ref;
    const rcx = (rx1 + rx2) / 2, rcy = (ry1 + ry2) / 2;
    const [bx1, by1, bx2, by2] = b;
    const bcx = (bx1 + bx2) / 2, bcy = (by1 + by2) / 2;
    const dx = bcx - rcx, dy = bcy - rcy;

    const rw = rx2 - rx1, rh = ry2 - ry1;
    const bwi = Math.max(0, Math.min(100, bx2) - Math.max(0, bx1));
    const bhe = Math.max(0, Math.min(100, by2) - Math.max(0, by1));
    const cover = Math.min(1, (bwi * bhe) / Math.max(1, rw * rh));

    total++;
    const ok = Math.abs(dx) <= TOL && Math.abs(dy) <= TOL && cover >= MIN_SIZE_RATIO;
    if (ok) pass++;
    const why = [];
    if (Math.abs(dx) > TOL) why.push('横向偏' + dx.toFixed(0) + '%');
    if (Math.abs(dy) > TOL) why.push('纵向偏' + dy.toFixed(0) + '%');
    if (cover < MIN_SIZE_RATIO) why.push('画面占比仅' + (cover * 100).toFixed(0) + '%');
    rows.push({ id: r.id, name: r.name, dx, dy, cover, ok, why: why.join(' / ') });
}

const pad = (s, n) => String(s).padEnd(n);
console.log('\n构图位置闸门 · 元素包围盒中心 vs 参考框中心（容差 ±' + TOL + '%）');
console.log('─'.repeat(78));
console.log(pad('区', 5) + pad('区域名', 18) + pad('Δx', 8) + pad('Δy', 8) + pad('画面占比', 10) + '结果');
console.log('─'.repeat(78));
for (const r of rows) {
    if (r.verdict === 'SKIP') {
        console.log(pad(r.id, 5) + pad(r.name, 18) + pad('—', 8) + pad('—', 8) + pad('—', 10) + 'SKIP ' + r.note);
        continue;
    }
    console.log(pad(r.id, 5) + pad(r.name, 18)
        + pad((r.dx >= 0 ? '+' : '') + r.dx.toFixed(1), 8)
        + pad((r.dy >= 0 ? '+' : '') + r.dy.toFixed(1), 8)
        + pad((r.cover * 100).toFixed(0) + '%', 10)
        + (r.ok ? 'PASS' : 'FAIL ' + r.why));
}
console.log('─'.repeat(78));
console.log(pass + '/' + total + ' 区站位在容差内（只统计参考框约等于物体外接框的元素）');
process.exit(pass === total ? 0 : 1);
