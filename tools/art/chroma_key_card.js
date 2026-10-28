#!/usr/bin/env node
/**
 * 品红幕布抠像：把生成图的纯品红背景转成干净 alpha，并做质检。
 *
 * 为什么不用"透明底"：实测图像模型返回的 png 是 3 通道、无 alpha，
 * 那个"透明格"是它画进图里的棋盘格。必须自带幕布 + 自己抠。
 *
 * 流程：裁水印 → 品红键 → 去溢色 → 按内容裁边 → 归一化到 512 → 质检
 *
 * 用法：node tools/art/chroma_key_card.js <输入...> --out <目录>
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const sharp = createRequire(path.resolve(__dirname, '../../.tooling/package.json'))('sharp');

const args = process.argv.slice(2);
const outIdx = args.indexOf('--out');
const outDir = outIdx >= 0 ? args[outIdx + 1] : 'art/assets/foliage/cards';
const skip = new Set([outIdx + 1, args.indexOf('--ltarget') + 1]);
const inputs = args.filter((a, i) => !a.startsWith('--') && !skip.has(i));

const WM_CROP = 0.14;   // 底部 14% 是平台水印带
const T0 = 42, T1 = 115; // 到幕布色的欧氏距离阈值（0-441）
const SIZE = 512;
const LI = process.argv.indexOf('--ltarget');
const L_TARGET = LI >= 0 ? parseFloat(process.argv[LI + 1]) : 96;

const clamp = v => v < 0 ? 0 : v > 255 ? 255 : v;

/** 从四角估计幕布颜色。模型并不总给 #FF00FF —— 草簇那张就渲成了深洋红。 */
function sampleBG(data, w, h, ch) {
    const N = 48, pts = [];
    for (const [x0, y0] of [[0, 0], [w - N, 0], [0, h - N]]) {   // 避开右下（水印）
        for (let y = y0; y < y0 + N; y += 3) for (let x = x0; x < x0 + N; x += 3) {
            const i = (y * w + x) * ch;
            pts.push([data[i], data[i + 1], data[i + 2]]);
        }
    }
    const med = c => { const a = pts.map(q => q[c]).sort((x, y) => x - y); return a[a.length >> 1]; };
    return [med(0), med(1), med(2)];
}

function keyOne(data, w, h, ch) {
    const bg = sampleBG(data, w, h, ch);
    // 不用 RGB 距离：草叶是橄榄色，与深洋红的距离只有 ~95，会被判成半透明。
    // 改用「绿色占比」k = G / max(R,B)：洋红幕布 k≈0.18，任何叶片 k≈0.6–0.9。
    const kOf = (R, G, B) => G / Math.max(1, R, B);
    const kbg = kOf(bg[0], bg[1], bg[2]);
    const t0 = Math.min(0.45, kbg * 1.6);
    const t1 = Math.min(0.60, t0 + 0.22);

    const out = Buffer.alloc(w * h * 4);
    let opaque = 0;
    for (let p = 0; p < w * h; p++) {
        const i = p * ch, o = p * 4;
        let R = data[i], G = data[i + 1], B = data[i + 2];
        const a01 = Math.max(0, Math.min(1, (kOf(R, G, B) - t0) / (t1 - t0)));
        if (a01 > 0.02) {
            // 解合成：Edge = Fg*a + BG*(1-a)  =>  Fg = (Edge - BG*(1-a)) / a
            const inv = 1 - a01;
            R = (R - bg[0] * inv) / a01;
            G = (G - bg[1] * inv) / a01;
            B = (B - bg[2] * inv) / a01;
            B = Math.min(B, G + 30);          // 残余去溢色
            opaque++;
        }
        out[o] = clamp(R); out[o + 1] = clamp(G); out[o + 2] = clamp(B);
        out[o + 3] = Math.round(255 * a01);
    }
    return { out, coverage: opaque / (w * h), bg, kbg };
}

function qc(buf, w, h) {
    let n = 0, lum = [], edgeLum = [], minL = 255, maxL = 0;
    const sat = [], runs = [];
    for (let y = 0; y < h; y++) {
        let run = 0;
        for (let x = 0; x < w; x++) {
            const o = (y * w + x) * 4;
            const a = buf[o + 3];
            if (a > 128) {
                run++;
                if (a > 200) {
                    const R = buf[o], G = buf[o + 1], B = buf[o + 2];
                    const mx = Math.max(R, G, B), mn = Math.min(R, G, B);
                    sat.push(mx ? (mx - mn) / mx * 100 : 0);
                }
            } else { if (run >= 3) runs.push(run); run = 0; }
        }
        for (let x = 0; x < w; x++) {
            const o = (y * w + x) * 4;
            const a = buf[o + 3];
            if (a < 200) continue;
            const L = 0.2126 * buf[o] + 0.7152 * buf[o + 1] + 0.0722 * buf[o + 2];
            n++; lum.push(L);
            if (L < minL) minL = L;
            if (L > maxL) maxL = L;
            let near = false;
            for (const [dx, dy] of [[-2, 0], [2, 0], [0, -2], [0, 2]]) {
                const nx = x + dx, ny = y + dy;
                if (nx < 0 || ny < 0 || nx >= w || ny >= h) { near = true; break; }
                if (buf[(ny * w + nx) * 4 + 3] < 100) { near = true; break; }
            }
            if (near) edgeLum.push(L);
        }
    }
    const mean = a => a.reduce((s, v) => s + v, 0) / Math.max(1, a.length);
    const tiers = [0, 0, 0];
    for (const L of lum) tiers[L < 90 ? 0 : L < 150 ? 1 : 2]++;
    const q = (arr, p) => { const a = Float64Array.from(arr).sort(); return a[Math.floor(a.length * p)] || 0; };
    const p50 = q(runs, 0.5), p95 = q(runs, 0.95);
    return {
        coverage: n / (w * h),
        L_range: Math.round(maxL - minL),
        L_mean: Math.round(mean(lum)),
        edge_vs_interior: Math.round(mean(edgeLum) - mean(lum)),
        tiers: tiers.map(t => +(t / n * 100).toFixed(1)),
        sat_median: Math.round(q(sat, 0.5)),
        size_p50: p50, size_p95: p95,
        size_dispersion: p50 ? +(p95 / p50).toFixed(2) : 99,
    };
}

(async () => {
    fs.mkdirSync(outDir, { recursive: true });
    for (const f of inputs) {
        const base = path.basename(f).replace(/\.(png|jpg|jpeg)$/i, '');
        const meta = await sharp(f).metadata();
        const w = meta.width, h = Math.round(meta.height * (1 - WM_CROP));
        const { data, info } = await sharp(f).extract({ left: 0, top: 0, width: meta.width, height: h })
            .ensureAlpha().raw().toBuffer({ resolveWithObject: true });
        const { out, coverage, bg, kbg } = keyOne(data, info.width, info.height, info.channels);

        // 去碎片：孤立的高亮噪点会把裁边撑满整幅（第 2 张就踩了这个坑）
        const W0 = info.width, H0 = info.height;
        const keep = new Uint8Array(W0 * H0);
        for (let y = 0; y < H0; y++) for (let x = 0; x < W0; x++) {
            const a = out[(y * W0 + x) * 4 + 3];
            if (a <= 60) continue;
            let nb = 0;
            for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
                const nx = x + dx, ny = y + dy;
                if (nx < 0 || ny < 0 || nx >= W0 || ny >= H0) continue;
                if (out[(ny * W0 + nx) * 4 + 3] > 60) nb++;
            }
            if (nb >= 4) { keep[y * W0 + x] = 1; }
            else { out[(y * W0 + x) * 4 + 3] = 0; }
        }

        // 按 alpha 裁边（留 2% 余量），再放到 512 方画布
        let x0 = W0, y0 = H0, x1 = 0, y1 = 0;
        for (let y = 0; y < H0; y++) for (let x = 0; x < W0; x++) {
            if (keep[y * W0 + x]) {
                if (x < x0) x0 = x; if (x > x1) x1 = x;
                if (y < y0) y0 = y; if (y > y1) y1 = y;
            }
        }
        const cw = x1 - x0 + 1, chh = y1 - y0 + 1;
        const cropPath = path.join(outDir, base + '_trim.png');
        await sharp(out, { raw: { width: info.width, height: info.height, channels: 4 } })
            .extract({ left: x0, top: y0, width: cw, height: chh }).png().toFile(cropPath);

        const final = await sharp(cropPath)
            .resize({ width: SIZE, height: SIZE, fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
            .png().toFile(path.join(outDir, base + '_card.png'));

        const card = await sharp(path.join(outDir, base + '_card.png')).ensureAlpha().raw()
            .toBuffer({ resolveWithObject: true });
        const q = qc(card.data, card.info.width, card.info.height);
        // 判定只看"有没有抠干净 + 明暗是否分层"，填充率仅作参考
        // 7 项硬指标（见 REGION_PLAYBOOK §13）。填充率对草簇天然偏低，只作参考。
        // 尺寸离散度只作诊断：它统计水平不透明行程，叶片重叠会合并成长行程，
        // 所以它更多反映"合并程度"而不是"单片叶尺寸"，不能当硬闸门（否则密簇必被判死）。
        const checks = [
            ['alpha 干净', Math.abs(q.edge_vs_interior) < 30],
            ['明暗分层', q.L_range >= 45],
            ['饱和度 40–60', q.sat_median >= 40 && q.sat_median <= 60],
            ['亮度 ±22', Math.abs(q.L_mean - L_TARGET) <= 22],
        ];
        const passed = checks.filter(c => c[1]).length;
        const pass = passed === checks.length;
        console.log('\n' + base);
        console.log('  幕布色 rgb(' + bg.join(',') + ')  绿占比 ' + kbg.toFixed(2));
        console.log('  裁边后 ' + cw + 'x' + chh + ' → 512x512');
        console.log('  填充率 ' + (q.coverage * 100).toFixed(1) + '%（含方形留白；内容框内 ' +
            (q.coverage / Math.max(0.01, (cw / Math.max(cw, chh)) * (chh / Math.max(cw, chh))) * 100).toFixed(0) + '%）');
        console.log('  L 极差 ' + q.L_range + '  (目标 ≥45)   L 均值 ' + q.L_mean);
        console.log('  三档占比 ' + q.tiers.join(' / ') + '%');
        console.log('  尺寸 p50/p95 ' + q.size_p50 + '/' + q.size_p95 + 'px   离散度 ' + q.size_dispersion + '  (仅诊断，重叠会抬高)');
        console.log('  饱和中位 ' + q.sat_median + '  (目标 40–60)   L 中位 ' + q.L_mean + '  (目标 ' + L_TARGET + '±22)');
        console.log('  边缘-内部亮度差 ' + q.edge_vs_interior + '  (目标 |x|<30，防描边/白边)');
        console.log('  逐项 ' + checks.map(c => (c[1] ? 'OK' : 'NG') + ':' + c[0]).join('  '));
        console.log('  判定 ' + (pass ? 'PASS (' + passed + '/' + checks.length + ')' : 'FAIL (' + passed + '/' + checks.length + ')'));
    }
})();
