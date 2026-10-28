#!/usr/bin/env node
/**
 * 冻结式调色：拟合一次 → 存盘 → 之后只套用，不再重算。
 *
 * 为什么必须冻结：Grade 是整条管线的最后一步，每改一次内容就重新拟合，
 * 等于把"目标"也跟着改，区域闸门会永远在漂。方案里写死：**只做一次，之后冻结**。
 *
 * 用法：
 *   node tools/art/grade_lut.js --fit <参考图> <渲染图> --save planning/art/grade_lut.json
 *   node tools/art/grade_lut.js --apply <渲染图> <输出> --load planning/art/grade_lut.json
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const sharp = createRequire(path.resolve(__dirname, '../../.tooling/package.json'))('sharp');

const args = process.argv.slice(2);
const argOf = (flag) => { const i = args.indexOf(flag); return i >= 0 ? args[i + 1] : null; };

function cdfOf(hist, N) {
    const c = new Float64Array(256);
    let acc = 0;
    for (let v = 0; v < 256; v++) { acc += hist[v]; c[v] = acc / N; }
    return c;
}
function invCdf(c, u) {
    if (u <= c[0]) return 0;
    for (let v = 1; v < 256; v++) {
        if (c[v] >= u) {
            const t = (u - c[v - 1]) / Math.max(1e-9, c[v] - c[v - 1]);
            return (v - 1) + t;
        }
    }
    return 255;
}
async function histOf(file) {
    const { data, info } = await sharp(file).resize({ width: 480 }).removeAlpha()
        .raw().toBuffer({ resolveWithObject: true });
    const N = info.width * info.height;
    const h = [new Float64Array(256), new Float64Array(256), new Float64Array(256)];
    for (let p = 0; p < N; p++) {
        const i = p * info.channels;
        h[0][data[i]]++; h[1][data[i + 1]]++; h[2][data[i + 2]]++;
    }
    return { h, N };
}

(async () => {
    const saveTo = argOf('--save');
    const loadFrom = argOf('--load');
    const fitIdx = args.indexOf('--fit');
    const applyIdx = args.indexOf('--apply');

    if (fitIdx >= 0) {
        const ref = args[fitIdx + 1], src = args[fitIdx + 2];
        const A = await histOf(ref), B = await histOf(src);
        const cA = A.h.map(h => cdfOf(h, A.N));
        const cB = B.h.map(h => cdfOf(h, B.N));
        const lut = [0, 1, 2].map(ch => {
            const row = new Array(256);
            for (let v = 0; v < 256; v++) {
                const u = Math.min(0.999, Math.max(0.001, cB[ch][v]));
                row[v] = Math.max(0, Math.min(255, Math.round(invCdf(cA[ch], u))));
            }
            return row;
        });
        const rec = {
            _meta: {
                version: '1.0.0', created: new Date().toISOString().slice(0, 19),
                reference: ref, fitted_against: src,
                rule: '拟合一次后冻结；此后所有版本只套用，不再重算。改动内容后若整体偏色，先查内容再决定是否重拟合。'
            },
            lut,
        };
        fs.writeFileSync(saveTo, JSON.stringify(rec));
        console.log('LUT 已冻结 → ' + saveTo);
        for (let ch = 0; ch < 3; ch++) {
            const pts = [0, 64, 128, 192, 255].map(v => v + '→' + lut[ch][v]).join('  ');
            console.log('  ' + 'RGB'[ch] + ': ' + pts);
        }
        return;
    }

    if (applyIdx >= 0) {
        const src = args[applyIdx + 1], out = args[applyIdx + 2];
        const rec = JSON.parse(fs.readFileSync(loadFrom, 'utf8'));
        const lut = rec.lut;
        const { data, info } = await sharp(src).removeAlpha().raw().toBuffer({ resolveWithObject: true });
        const o3 = Buffer.alloc(info.width * info.height * 3);
        for (let p = 0; p < info.width * info.height; p++) {
            const i = p * info.channels, o = p * 3;
            o3[o] = lut[0][data[i]];
            o3[o + 1] = lut[1][data[i + 1]];
            o3[o + 2] = lut[2][data[i + 2]];
        }
        await sharp(o3, { raw: { width: info.width, height: info.height, channels: 3 } }).png().toFile(out);
        console.log('已套用冻结 LUT (' + rec._meta.created + ') → ' + out);
        return;
    }
    console.error('用法: --fit <参考> <渲染> --save <json> | --apply <渲染> <输出> --load <json>');
    process.exit(2);
})();
