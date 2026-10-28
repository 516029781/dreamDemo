#!/usr/bin/env node
/**
 * 后处理栈原型：Bloom + Grain + Vignette + CA。
 *
 * 为什么需要：参考图带有明显的相机特征（高光泛光、胶片颗粒、暗角、边缘色差），
 * v02 的成图完全没有。这一段在 Blender 里是 compositor 节点，成本极低，
 * 但它决定了画面"像不像一张照片"。
 *
 * 本脚本只用于**验证收益**，不是最终方案——最终在 Blender compositor 里做，
 * 因为那里能做真 DOF（需要深度通道），而这里只能做伪造的。
 *
 * 用法：node tools/art/apply_post.js <输入> <输出> [--bloom 0.18] [--grain 3] [--vig 0.22] [--ca 1.0]
 */
const path = require('path');
const { createRequire } = require('module');
const sharp = createRequire(path.resolve(__dirname, '../../.tooling/package.json'))('sharp');

const args = process.argv.slice(2);
const num = (flag, def) => { const i = args.indexOf(flag); return i >= 0 ? parseFloat(args[i + 1]) : def; };

const BLOOM = num('--bloom', 0.18);
const GRAIN = num('--grain', 3.0);
const VIG = num('--vig', 0.22);
const CA = num('--ca', 1.0);

function prng(seed) {
    let s = seed >>> 0;
    return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}

(async () => {
    const [src, out] = args;
    if (!src || !out) { console.error('用法: node tools/art/apply_post.js <输入> <输出>'); process.exit(2); }

    const { data, info } = await sharp(src).removeAlpha().raw().toBuffer({ resolveWithObject: true });
    const W = info.width, H = info.height, C = info.channels;
    const N = W * H;
    const px = (x, y, c) => data[(y * W + x) * C + c];
    const cl = v => v < 0 ? 0 : v > 255 ? 255 : v;

    // ---- 1. Bloom：抽高光 → 模糊 → 屏幕叠加 ----
    // 只取 L>215 的部分，避免整体发灰
    const hi = Buffer.alloc(N * 3);
    for (let p = 0; p < N; p++) {
        const i = p * C;
        const L = 0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2];
        const k = Math.max(0, Math.min(1, (L - 215) / 40));
        hi[p * 3] = data[i] * k; hi[p * 3 + 1] = data[i + 1] * k; hi[p * 3 + 2] = data[i + 2] * k;
    }
    const blur = await sharp(hi, { raw: { width: W, height: H, channels: 3 } })
        .blur(16).raw().toBuffer();

    const outp = Buffer.alloc(N * 3);
    for (let p = 0; p < N; p++) {
        const i = p * C, o = p * 3;
        for (let c = 0; c < 3; c++) {
            const base = data[i + c] / 255;
            const b = blur[p * 3 + c] / 255 * BLOOM;
            // screen
            outp[o + c] = cl(Math.round((1 - (1 - base) * (1 - b)) * 255));
        }
    }

    // ---- 2. 色差：以画面中心为原点做径向偏移 ----
    const cx = W / 2, cy = H / 2;
    const rmax = Math.hypot(cx, cy);
    if (CA > 0) {
        const src3 = Buffer.from(outp);
        for (let y = 0; y < H; y++) {
            for (let x = 0; x < W; x++) {
                const dx = x - cx, dy = y - cy;
                const d = Math.hypot(dx, dy) / rmax;
                const k = CA * d * d * 2.2;
                const sx = Math.round(x + dx / Math.max(1e-6, Math.hypot(dx, dy)) * k);
                const bx = Math.round(x - dx / Math.max(1e-6, Math.hypot(dx, dy)) * k);
                const sy = Math.round(y + dy / Math.max(1e-6, Math.hypot(dx, dy)) * k);
                const by = Math.round(y - dy / Math.max(1e-6, Math.hypot(dx, dy)) * k);
                const o = (y * W + x) * 3;
                if (sx >= 0 && sx < W && sy >= 0 && sy < H) outp[o] = src3[(sy * W + sx) * 3];
                if (bx >= 0 && bx < W && by >= 0 && by < H) outp[o + 2] = src3[(by * W + bx) * 3 + 2];
            }
        }
    }

    // ---- 3. 暗角 + 颗粒 ----
    const rnd = prng(20261028);
    for (let y = 0; y < H; y++) {
        for (let x = 0; x < W; x++) {
            const o = (y * W + x) * 3;
            const d = Math.hypot(x - cx, y - cy) / rmax;
            const v = 1 - VIG * d * d;
            const n = (rnd() + rnd() + rnd() - 1.5) * GRAIN;  // 近似高斯
            for (let c = 0; c < 3; c++) outp[o + c] = cl(Math.round(outp[o + c] * v + n));
        }
    }

    await sharp(outp, { raw: { width: W, height: H, channels: 3 } }).png().toFile(out);
    console.log('post: bloom=' + BLOOM + ' grain=' + GRAIN + ' vig=' + VIG + ' ca=' + CA + '  -> ' + out);
})();
