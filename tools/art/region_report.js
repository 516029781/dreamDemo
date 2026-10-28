#!/usr/bin/env node
/**
 * 区域级美术验收：按 planning/art/regions.json 的语义区域逐块比对参考图与待检图。
 *
 * 为什么需要它：
 *   全局直方图闸门（consistency_check.js）只看分布，把参考图的 LUT 贴到一张画得很差的
 *   图上也能 13/13 全过。区域闸门补上两件全局指标做不到的事：
 *     1. 整块物件缺失（target 为 null）——分布可以被别处补齐，缺失的物件不能；
 *     2. 单区偏色/偏灰/细节密度不同档——会在大面积平均里被稀释掉。
 *
 * 用法：
 *   node tools/art/region_report.js <参考图> <待检图> [--json out.json]
 *
 * 退出码：0 全部通过；1 有超差或缺失项。
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const sharp = createRequire(path.resolve(__dirname, '../../.tooling/package.json'))('sharp');
const CFG = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../planning/art/regions.json'), 'utf8'));
const TOL = CFG._meta.tolerance;

const pct = (arr, p) => {
    const a = Float32Array.from(arr).sort();
    return a[Math.floor(a.length * p)];
};

async function cropRaw(file, rect) {
    const m = await sharp(file).metadata();
    const x1 = Math.max(0, Math.min(m.width - 8, Math.round(m.width * rect[0] / 100)));
    const y1 = Math.max(0, Math.min(m.height - 8, Math.round(m.height * rect[1] / 100)));
    const x2 = Math.max(x1 + 8, Math.min(m.width, Math.round(m.width * rect[2] / 100)));
    const y2 = Math.max(y1 + 8, Math.min(m.height, Math.round(m.height * rect[3] / 100)));
    const { data, info } = await sharp(file)
        .extract({ left: x1, top: y1, width: x2 - x1, height: y2 - y1 })
        .removeAlpha().raw().toBuffer({ resolveWithObject: true });
    return { data, info, w: x2 - x1, h: y2 - y1 };
}

async function stats(file, rect) {
    const { data, info, w, h } = await cropRaw(file, rect);
    const N = w * h;
    const L = new Float32Array(N), S = new Float32Array(N);
    let RmB = 0, hi = 0, lo = 0;
    for (let p = 0; p < N; p++) {
        const i = p * info.channels;
        const R = data[i], G = data[i + 1], B = data[i + 2];
        L[p] = 0.2126 * R + 0.7152 * G + 0.0722 * B;
        const mx = Math.max(R, G, B), mn = Math.min(R, G, B);
        S[p] = mx ? (mx - mn) / mx * 100 : 0;
        RmB += R - B;
        if (L[p] > 180) hi++;
        if (L[p] < 40) lo++;
    }
    // 边缘密度：灰度梯度 > 12 的像素占比
    const gs = await sharp(file)
        .metadata().then(meta => sharp(file)
            .extract({
                left: Math.round(meta.width * rect[0] / 100),
                top: Math.round(meta.height * rect[1] / 100),
                width: Math.max(8, Math.round(meta.width * (rect[2] - rect[0]) / 100)),
                height: Math.max(8, Math.round(meta.height * (rect[3] - rect[1]) / 100)),
            }).greyscale().raw().toBuffer({ resolveWithObject: true }));

    const gw = gs.info.width, gh = gs.info.height, gd = gs.data;
    let e = 0, en = 0;
    for (let y = 1; y < gh - 1; y++) {
        for (let x = 1; x < gw - 1; x++) {
            const i = y * gw + x;
            const mag = Math.hypot(Math.abs(gd[i + 1] - gd[i - 1]), Math.abs(gd[i + gw] - gd[i - gw]));
            if (mag > 12) e++;
            en++;
        }
    }
    return {
        L: Math.round(pct(L, 0.5)), Lmean: Math.round(L.reduce((a, b) => a + b, 0) / N),
        sat: Math.round(pct(S, 0.5)), RmB: Math.round(RmB / N),
        edge: +(e / Math.max(1, en) * 100).toFixed(2),
        hi180: +(hi / N * 100).toFixed(1), lo40: +(lo / N * 100).toFixed(1),
    };
}

/** 四边遮挡带：对比度归一化边缘密度（阈值 = 2 × 全图中位梯度）
 *
 * 注意（实测结论，见 planning/art/REGION_PLAYBOOK_20261028.md）：
 *   该指标对"空边"很敏感且调色救不回来（v02 上边 0.09、加曲线后 0.01），
 *   但对"有物体但对比度不同"的边会漂移（左边 0.36 → 0.87）。
 *   因此只用于判定"这条边有没有东西"，不用于判定"像不像"。
 */
async function borderEdges(file) {
    const { data, info } = await sharp(file).resize({ width: 960 }).greyscale()
        .raw().toBuffer({ resolveWithObject: true });
    const w = info.width, h = info.height;
    const g = new Float32Array(w * h);
    for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) {
        const i = y * w + x;
        g[i] = Math.hypot(data[i + 1] - data[i - 1], data[i + w] - data[i - w]);
    }
    const nz = Float32Array.from(g).filter(v => v > 0).sort();
    const thr = 2 * nz[Math.floor(nz.length * 0.5)];
    const strips = { 上: [0, 0, 100, 8], 下: [0, 92, 100, 100], 左: [0, 0, 8, 100], 右: [92, 0, 100, 100] };
    const out = {};
    for (const [k, r] of Object.entries(strips)) {
        const x1 = Math.round(w * r[0] / 100), y1 = Math.round(h * r[1] / 100);
        const x2 = Math.round(w * r[2] / 100), y2 = Math.round(h * r[3] / 100);
        let e = 0, n = 0;
        for (let y = Math.max(1, y1); y < Math.min(h - 1, y2); y++)
            for (let x = Math.max(1, x1); x < Math.min(w - 1, x2); x++) {
                if (g[y * w + x] > thr) e++;
                n++;
            }
        out[k] = +(e / Math.max(1, n) * 100).toFixed(1);
    }
    return out;
}


/** 细节预算：按景深分带的边缘密度，用于判断"细节有没有放对地方"
 *
 * 参考图的规律是"远密近疏"——但这不是景深造成的，而是材质造成的：
 * 远景是草墙/树线（高频小叶片），近景是石板（低频大面）。所以这条只看
 * "每类材质该有的细节量"，不能反推距离。
 * 仅供参考，不计失败（跨调色会漂移）。
 */
async function depthBands(file) {
    const { data, info } = await sharp(file).resize({ width: 960 }).greyscale()
        .raw().toBuffer({ resolveWithObject: true });
    const w = info.width, h = info.height;
    const g = new Float32Array(w * h);
    for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) {
        const i = y * w + x;
        g[i] = Math.hypot(data[i + 1] - data[i - 1], data[i + w] - data[i - w]);
    }
    const nz = Float32Array.from(g).filter(v => v > 0).sort();
    const thr = 2 * nz[Math.floor(nz.length * 0.5)];
    const bands = {
        '远景 y4-18': [25, 4, 75, 18],
        '中景 y22-40': [28, 22, 75, 40],
        '近景 y55-75': [18, 55, 60, 75],
        '底边 y85-98': [10, 85, 90, 98],
        '右上 y0-12': [60, 0, 88, 12],
    };
    const out = {};
    for (const [k, r] of Object.entries(bands)) {
        const x1 = Math.round(w * r[0] / 100), y1 = Math.round(h * r[1] / 100);
        const x2 = Math.round(w * r[2] / 100), y2 = Math.round(h * r[3] / 100);
        let c = 0, n = 0;
        for (let y = Math.max(1, y1); y < Math.min(h - 1, y2); y++)
            for (let x = Math.max(1, x1); x < Math.min(w - 1, x2); x++) {
                if (g[y * w + x] > thr) c++;
                n++;
            }
        out[k] = +(c / Math.max(1, n) * 100).toFixed(1);
    }
    return out;
}

(async () => {
    const args = process.argv.slice(2);
    if (args.length < 2) {
        console.error('用法: node tools/art/region_report.js <参考图> <待检图> [--self] [--json out.json] [--crops dir]');
        process.exit(2);
    }
    const [refFile, tgtFile] = args;
    const jsonFlag = args.indexOf('--json');
    // --self：两侧都用参考框。用来验证度量管线本身（所有 Δ 必须为 0），
    // 而不是验证区域框选得对不对（那要靠 --crops 目视核对）。
    const selfMode = args.includes('--self');
    const cropsFlag = args.indexOf('--crops');

    const rows = [];
    for (const r of CFG.regions) {
        if (r.measure === false) {
            rows.push({ ...r, ref: await stats(refFile, r.ref), tgt: null, skip: true, pass: true, reason: '参考图不可稳定取样' });
            continue;
        }
        const a = await stats(refFile, r.ref);
        const tgtRect = selfMode ? r.ref : r.target;
        if (!tgtRect) {
            rows.push({ ...r, ref: a, tgt: null, dL: null, dSat: null, edgeRatio: null, pass: false, reason: '整块缺失' });
            continue;
        }
        const b = await stats(selfMode ? refFile : tgtFile, tgtRect);
        const dL = b.L - a.L, dSat = b.sat - a.sat;
        const edgeRatio = Math.abs(b.edge - a.edge) / Math.max(a.edge, 1);
        const fails = [];
        if (Math.abs(dL) > TOL.L_abs_max) fails.push('L差' + dL);
        if (Math.abs(dSat) > TOL.sat_abs_max) fails.push('sat差' + dSat);
        // 软指标：跨调色不可比（见 borderEdges 注释），只提示不计失败
        const edgeWarn = edgeRatio > TOL.edge_ratio_max;
        rows.push({ ...r, ref: a, tgt: b, dL, dSat, edgeRatio: +edgeRatio.toFixed(2), edgeWarn, pass: fails.length === 0, reason: fails.join(' / ') });
    }

    if (cropsFlag >= 0) {
        const dir = args[cropsFlag + 1];
        fs.mkdirSync(dir, { recursive: true });
        for (const r of CFG.regions) {
            const m = await sharp(refFile).metadata();
            const cut = async (rect, tag) => {
                if (!rect) return;
                const l = Math.round(m.width * rect[0] / 100), t = Math.round(m.height * rect[1] / 100);
                const wd = Math.max(8, Math.round(m.width * (rect[2] - rect[0]) / 100));
                const ht = Math.max(8, Math.round(m.height * (rect[3] - rect[1]) / 100));
                await sharp(refFile).extract({ left: l, top: t, width: Math.min(wd, m.width - l), height: Math.min(ht, m.height - t) })
                    .resize({ width: 300 }).png().toFile(path.join(dir, r.id + '_' + tag + '.png'));
            };
            await cut(r.ref, 'ref');
        }
        console.log('裁剪块已写入 ' + dir);
    }

    const compRef = await borderEdges(refFile);
    const compTgt = selfMode ? compRef : await borderEdges(tgtFile);

    const w = (s, n) => String(s).padEnd(n);
    console.log('\n区域级验收 · ' + path.basename(tgtFile));
    console.log('─'.repeat(96));
    console.log(w('区', 4) + w('区域名', 18) + w('参考L/sat/edge', 18) + w('实测L/sat/edge', 18) + w('ΔL', 6) + w('Δsat', 6) + w('密度比', 8) + '结果');
    console.log('─'.repeat(96));
    for (const r of rows) {
        const a = r.ref;
        const b = r.tgt;
        console.log(
            w(r.id, 4) + w(r.name, 18) +
            w(a.L + '/' + a.sat + '/' + a.edge, 18) +
            w(b ? b.L + '/' + b.sat + '/' + b.edge : '—', 18) +
            w(b ? (r.dL > 0 ? '+' : '') + r.dL : '—', 6) +
            w(b ? (r.dSat > 0 ? '+' : '') + r.dSat : '—', 6) +
            w(b ? r.edgeRatio.toFixed(2) : '—', 8) +
            (r.skip ? 'SKIP（' + r.reason + '）' : r.pass ? (r.edgeWarn ? 'PASS(细节密度偏' + r.edgeRatio.toFixed(2) + ')' : 'PASS') : 'FAIL ' + r.reason));
    }
    const fails = rows.filter(r => !r.pass && !r.skip);
    console.log('─'.repeat(96));
    console.log(fails.length
        ? `未通过 ${fails.length}/${rows.filter(r => !r.skip).length} 区：` + fails.map(f => f.id).join('、')
        : `全部 ${rows.filter(r => !r.skip).length} 区通过（${rows.filter(r => r.skip).length} 区不可测已跳过）`);

    console.log('\n四边遮挡带 · 对比度归一化边缘密度（只判\'这条边有没有东西\'，不判\'像不像\'）');
    const MIN_RATIO = CFG.composition.border_occlusion.min_ratio_vs_ref;
    let compPass = true;
    const borderFails = [];
    for (const k of ['上', '下', '左', '右']) {
        const ratio = compTgt[k] / Math.max(compRef[k], 0.1);
        const ok = k === '下' ? ratio >= MIN_RATIO : ratio >= MIN_RATIO;
        if (!ok) { compPass = false; borderFails.push(k); }
        console.log('  ' + k + '边   参考 ' + String(compRef[k]).padStart(5) +
            '   实测 ' + String(compTgt[k]).padStart(5) +
            '   比值 ' + ratio.toFixed(2) + (ok ? '  PASS' : '  FAIL 该边过空'));
    }
    console.log('  判定   ' + (compPass ? 'PASS 四边均有物件压住' : 'FAIL 空边：' + borderFails.join('、')));

    const dbRef = await depthBands(refFile);
    const dbTgt = selfMode ? dbRef : await depthBands(tgtFile);
    console.log('\n细节预算 · 按景深分带（仅供参考：细节应由材质决定，不由距离决定）');
    for (const k of Object.keys(dbRef)) {
        const ratio = dbTgt[k] / Math.max(dbRef[k], 0.1);
        const tag = ratio < 0.6 ? '  ← 细节不足' : ratio > 1.4 ? '  ← 细节过多/假细节' : '';
        console.log('  ' + k.padEnd(14) + '参考 ' + String(dbRef[k]).padStart(5) +
            '   实测 ' + String(dbTgt[k]).padStart(5) + '   比值 ' + ratio.toFixed(2) + tag);
    }

    if (jsonFlag >= 0) {
        fs.writeFileSync(args[jsonFlag + 1], JSON.stringify({ ref: refFile, target: tgtFile, rows, composition: { ref: compRef, target: compTgt, pass: compPass } }, null, 2));
        console.log('\n已写入 ' + args[jsonFlag + 1]);
    }
    process.exit((fails.length || !compPass) ? 1 : 0);
})();
