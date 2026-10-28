#!/usr/bin/env node
/**
 * 实验工具：把「参考图的色调分布」拟合成一张逐通道 LUT，应用到目标图上。
 *
 * 目的不是产出成品，而是**测量 L1 全局色调曲线这一层的能力边界**：
 *   把曲线做到理论最优（逐通道百分位完全匹配）之后，一致性闸门还剩几项不过，
 *   剩下的就必须靠内容（几何/材质/布光）解决，不能靠调色。
 *
 * 用法：
 *   node tools/art/apply_tone_curve.js <参考图> <目标图> <输出图> [--strength 1.0]
 */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

const sharp = createRequire(path.resolve(__dirname, '../../.tooling/package.json'))('sharp');

async function channelHist(file, width) {
    const { data, info } = await sharp(file).resize({ width }).removeAlpha()
        .raw().toBuffer({ resolveWithObject: true });
    const N = info.width * info.height;
    const h = [new Float64Array(256), new Float64Array(256), new Float64Array(256)];
    for (let p = 0; p < N; p++) {
        const i = p * info.channels;
        h[0][data[i]]++; h[1][data[i + 1]]++; h[2][data[i + 2]]++;
    }
    return { h, N };
}

function cdf(hist, N) {
    const c = new Float64Array(256);
    let acc = 0;
    for (let v = 0; v < 256; v++) { acc += hist[v]; c[v] = acc / N; }
    return c;
}

/** 反 CDF：给定累计比例 u，返回该图在这个通道上的取值 */
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

async function main() {
    const [refFile, srcFile, outFile] = process.argv.slice(2);
    if (!outFile) {
        console.error('用法: node tools/art/apply_tone_curve.js <参考图> <目标图> <输出图> [--strength 1]');
        process.exit(2);
    }
    const si = process.argv.indexOf('--strength');
    const strength = si >= 0 ? parseFloat(process.argv[si + 1]) : 1.0;

    const W = 480;
    const A = await channelHist(refFile, W);
    const B = await channelHist(srcFile, W);
    const cA = A.h.map(h => cdf(h, A.N));
    const cB = B.h.map(h => cdf(h, B.N));

    // 逐通道 LUT：src 的第 v 级 -> ref 的同分位取值
    const LUT = [0, 1, 2].map(ch => {
        const lut = new Uint8Array(256);
        for (let v = 0; v < 256; v++) {
            const u = Math.min(0.999, Math.max(0.001, cB[ch][v]));
            const tgt = invCdf(cA[ch], u);
            lut[v] = Math.max(0, Math.min(255, Math.round(v + (tgt - v) * strength)));
        }
        return lut;
    });

    console.log('LUT 形状（输入 → 输出）：');
    for (let ch = 0; ch < 3; ch++) {
        const pts = [0, 32, 64, 96, 128, 160, 192, 224, 255]
            .map(v => v + '→' + LUT[ch][v]).join('  ');
        console.log('  ' + 'RGB'[ch] + ': ' + pts);
    }

    const meta = await sharp(srcFile).metadata();
    const { data, info } = await sharp(srcFile).removeAlpha().raw()
        .toBuffer({ resolveWithObject: true });
    const out = Buffer.alloc(info.width * info.height * 3);
    for (let p = 0; p < info.width * info.height; p++) {
        const i = p * info.channels, o = p * 3;
        out[o] = LUT[0][data[i]];
        out[o + 1] = LUT[1][data[i + 1]];
        out[o + 2] = LUT[2][data[i + 2]];
    }
    await sharp(out, { raw: { width: info.width, height: info.height, channels: 3 } })
        .png().toFile(outFile);
    console.log('\n写入 ' + outFile + '  (' + meta.width + 'x' + meta.height + ', strength=' + strength + ')');
}

main();
