"""在核心区范围内按高度找体量，输出最高的一批实例（用于判断哪栋是总裁塔）。

用法：python tools/df_physx_heights.py <bin> <x0> <y0> <x1> <y1>
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from df_physx_parse import parse  # noqa: E402


def main(src, box):
    x0, y0, x1, y1 = box
    d = parse(src)
    hulls, hull_of = d["hulls"], d["hull_of"]
    pos = d["pos"] / 100.0
    scl = d["scl"]

    n = len(pos)
    top_z = np.full(n, -1e9)
    fx0 = np.full(n, 1e9)
    fy0 = np.full(n, 1e9)
    fx1 = np.full(n, -1e9)
    fy1 = np.full(n, -1e9)

    for hi, (verts, idx) in enumerate(hulls):
        if idx.size == 0 or verts.size == 0:
            continue
        idxs = np.where(hull_of == hi)[0]
        if idxs.size == 0:
            continue
        v = verts / 100.0
        s = scl[idxs]
        top_z[idxs] = np.maximum(top_z[idxs], v[:, 2].max() * s[:, 2] + pos[idxs, 2])
        fx0[idxs] = np.minimum(fx0[idxs], pos[idxs, 0] + v[:, 0].min() * s[:, 0])
        fx1[idxs] = np.maximum(fx1[idxs], pos[idxs, 0] + v[:, 0].max() * s[:, 0])
        fy0[idxs] = np.minimum(fy0[idxs], pos[idxs, 1] + v[:, 1].min() * s[:, 1])
        fy1[idxs] = np.maximum(fy1[idxs], pos[idxs, 1] + v[:, 1].max() * s[:, 1])

    m = ((pos[:, 0] > x0) & (pos[:, 0] < x1) & (pos[:, 1] > y0) & (pos[:, 1] < y1)
         & (top_z > -1e8))
    idx = np.where(m)[0]
    order = idx[np.argsort(-top_z[idx])]

    print(f"核心区实例 {len(idx)} 个，按顶标高排序（前 20）：")
    print(f"{'X':>7} {'Y':>7} {'顶标高':>8} {'占地 m':>17}")
    for i in order[:20]:
        print(f"{pos[i,0]:>7.1f} {pos[i,1]:>7.1f} {top_z[i]:>8.1f} "
              f"{fx1[i]-fx0[i]:>7.1f} × {fy1[i]-fy0[i]:<7.1f}")

    grid = {}
    for i in idx:
        gx, gy = int(pos[i, 0] // 10), int(pos[i, 1] // 10)
        grid[(gx, gy)] = max(grid.get((gx, gy), -1e9), top_z[i])
    hot = sorted(grid.items(), key=lambda kv: -kv[1])[:12]
    print("\n10 m 网格最高点（热点）：")
    for (gx, gy), z in hot:
        print(f"  X {gx*10:>5}..{gx*10+10:<5} Y {gy*10:>5}..{gy*10+10:<5} 顶 {z:>7.1f}")


if __name__ == "__main__":
    src = sys.argv[1]
    box = tuple(float(a) for a in sys.argv[2:6])
    main(src, box)
