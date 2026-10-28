#!/usr/bin/env node
/**
 * 一致性验收：一次输出 4 类指标，与 style.json 的 global_targets 逐项比对。
 *
 * 用法：
 *   node tools/art/consistency_check.js <待检图> [--baseline <基线图>] [--json <输出路径>]
 *
 * 设计意图（见 planning/art/ART_CONSISTENCY_MECHANISM.md）：
 *   L1 全局色调曲线  -> L 分位 + >180 占比
 *   L2 单一色相轴    -> 冷色像素占比 + 色相直方图
 *   L3 色阶分档      -> 六档直方图 + 最大单簇占比
 *   L4 细节频率      -> 边缘密度的四象限离散度（越低越"统一"，过高说明频率不一致）
 *
 * 退出码：0 全通过；1 有超差项（便于接入 CI / 构建脚本）。
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

function req(pkg) {
    const base = path.resolve(__dirname, '../../.tooling/package.json');
    return createRequire(base)(pkg);
}

const sharp = req('sharp');
const STYLE = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../planning/art/style.json'), 'utf8'));

const W = 480;

function hsv(R, G, B) {
    const r = R / 255, g = G / 255, b = B / 255;
    const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
    let h = 0;
    if (d > 1e-6) {
        if (mx === r) h = ((g - b) / d + 6) % 6;
        else if (mx === g) h = (b - r) / d + 2;
        else h = (r - g) / d + 4;
        h *= 60;
    }
    return { h, s: mx < 1e-6 ? 0 : (d / mx) * 100 };
}

async function analyse(file) {
    const { data, info } = await sharp(file).resize({ width: W }).removeAlpha()
        .raw().toBuffer({ resolveWithObject: true });
    const N = info.width * info.height;
    const L = new Float32Array(N), S = new Float32Array(N), H = new Float32Array(N);

    for (let p = 0; p < N; p++) {
        const i = p * info.channels;
        const R = data[i], G = data[i + 1], B = data[i + 2];
        L[p] = 0.2126 * R + 0.7152 * G + 0.0722 * B;
        const q = hsv(R, G, B);
        S[p] = q.s;
        H[p] = q.h;
    }

    const pct = (arr, p) => {
        const a = Array.from(arr).sort((x, y) => x - y);
        return a[Math.floor(a.length * p)];
    };

    // L1 全局色调曲线
    const curve = {
        p25: Math.round(pct(L, 0.25)), p50: Math.round(pct(L, 0.50)),
        p75: Math.round(pct(L, 0.75)), p90: Math.round(pct(L, 0.90)),
        p99: Math.round(pct(L, 0.99)), max: Math.round(pct(L, 0.999)),
    };
    let above180 = 0;
    for (let p = 0; p < N; p++) if (L[p] > 180) above180++;
    curve.share_above_180_pct = +(above180 / N * 100).toFixed(1);

    // L2 单一色相轴
    let cool = 0;
    const hueHist = new Array(12).fill(0);
    for (let p = 0; p < N; p++) {
        if (L[p] < 20) continue;
        hueHist[Math.floor(H[p] / 30) % 12]++;
        if (H[p] > 60 && H[p] < 300 && S[p] > 12) cool++;
    }
    const hue = {
        cool_pixel_share_pct: +(cool / N * 100).toFixed(1),
        warm_axis_share_pct: +((hueHist[0] + hueHist[1]) / N * 100).toFixed(1), // 0-60°
    };

    // L3 色阶分档 + 最大单簇
    const bands = [0, 0, 0, 0, 0, 0];
    const clusters = {};
    for (let p = 0; p < N; p++) {
        const l = L[p];
        const b = l < 40 ? 0 : l < 75 ? 1 : l < 110 ? 2 : l < 145 ? 3 : l < 180 ? 4 : 5;
        bands[b]++;
        if (l >= 12) {
            const k = Math.floor(H[p] / 30) + '|' + Math.min(4, Math.floor(S[p] / 20)) + '|' + Math.min(4, Math.floor(l / 50));
            clusters[k] = (clusters[k] || 0) + 1;
        }
    }
    const ladder = {
        lt40: +(bands[0] / N * 100).toFixed(1), '40_75': +(bands[1] / N * 100).toFixed(1),
        '75_110': +(bands[2] / N * 100).toFixed(1), '110_145': +(bands[3] / N * 100).toFixed(1),
        '145_180': +(bands[4] / N * 100).toFixed(1), gt180: +(bands[5] / N * 100).toFixed(1),
    };
    const maxCluster = +(Math.max(...Object.values(clusters)) / N * 100).toFixed(1);

    // L4 细节频率：四象限边缘密度离散度
    const edge = await edgeQuadrants(file);

    return { file, N, curve, hue, ladder, max_single_cluster_share_pct: maxCluster, sat_p50: +pct(S, 0.5).toFixed(0), edge };
}

async function edgeQuadrants(file) {
    const { data, info } = await sharp(file).resize({ width: W }).greyscale().raw()
        .toBuffer({ resolveWithObject: true });
    const w = info.width, h = info.height;
    const q = [0, 0, 0, 0], n = [0, 0, 0, 0];
    for (let y = 1; y < h - 1; y++) {
        for (let x = 1; x < w - 1; x++) {
            const i = y * w + x;
            const gx = Math.abs(data[i + 1] - data[i - 1]);
            const gy = Math.abs(data[i + w] - data[i - w]);
            const mag = Math.hypot(gx, gy);
            const qi = (y < h / 2 ? 0 : 2) + (x < w / 2 ? 0 : 1);
            q[qi] += mag > 12 ? 1 : 0;
            n[qi]++;
        }
    }
    const v = q.map((c, i) => +(c / n[i] * 100).toFixed(2));
    const mean = v.reduce((a, b) => a + b, 0) / 4;
    const spread = Math.sqrt(v.reduce((s, x) => s + (x - mean) ** 2, 0) / 4) / mean * 100;
    return { quad_pct: v, spread_pct: +spread.toFixed(1) };
}

function check(cur, tgt) {
    const rows = [];
    const add = (name, got, lo, hi, unit, hard) => {
        const pass = hard ? (got >= lo && got <= hi) : true;
        rows.push({ name, got, target: `${lo}–${hi}${unit || ''}`, pass, hard });
    };
    add('L p50', cur.curve.p50, tgt.L_p50 - 10, tgt.L_p50 + 10, '', true);
    add('L p90', cur.curve.p90, tgt.L_p90 - 12, tgt.L_p90 + 12, '', true);
    add('L p99', cur.curve.p99, tgt.L_p99 - 15, tgt.L_p99 + 15, '', true);
    add('>180 占比', cur.curve.share_above_180_pct, tgt.share_above_180_pct[0], tgt.share_above_180_pct[1], '%', true);
    add('sat p50', cur.sat_p50, tgt.sat_p50 - 5, tgt.sat_p50 + 5, '', true);
    add('冷色像素', cur.hue.cool_pixel_share_pct, 0, tgt.cool_pixel_share_pct_max, '%', true);
    for (const [k, [lo, hi]] of Object.entries(tgt.value_ladder_pct)) {
        if (k.startsWith('_')) continue; // 跳过说明字段
        add('色阶 ' + k, cur.ladder[k], lo, hi, '%', true);
    }
    add('最大单色簇', cur.max_single_cluster_share_pct, 0, tgt.max_single_cluster_share_pct, '%', true);
    add('细节频率离散度', cur.edge.spread_pct, 0, 60, '%', false); // 软指标
    return rows;
}

(async () => {
    const args = process.argv.slice(2);
    if (!args.length) {
        console.error('用法: node tools/art/consistency_check.js <图> [--json out.json]');
        process.exit(2);
    }
    const target = args[0];
    const jsonFlag = args.indexOf('--json');

    const cur = await analyse(target);
    const rows = check(cur, STYLE.global_targets);

    const w = (s, n) => String(s).padEnd(n);
    console.log('\n一致性验收 · ' + path.basename(target));
    console.log('─'.repeat(64));
    console.log(w('指标', 16) + w('实测', 10) + w('目标', 18) + '结果');
    console.log('─'.repeat(64));
    for (const r of rows) {
        const mark = r.hard ? (r.pass ? 'PASS' : 'FAIL') : (r.pass ? 'ok' : 'warn');
        console.log(w(r.name, 16) + w(r.got, 10) + w(r.target, 18) + mark);
    }
    const fails = rows.filter(r => r.hard && !r.pass);
    console.log('─'.repeat(64));
    console.log(fails.length ? `未通过 ${fails.length} 项：` + fails.map(f => f.name).join('、')
        : '全部通过');

    if (jsonFlag >= 0) {
        fs.writeFileSync(args[jsonFlag + 1], JSON.stringify({ measured: cur, rows }, null, 2));
        console.log('已写入 ' + args[jsonFlag + 1]);
    }
    process.exit(fails.length ? 1 : 0);
})();
