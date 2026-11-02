"""测量 TIMEPX01 场景的实际尺寸：整体包围盒、主体区域、分区尺寸、高程分布。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from df_physx_parse import parse, quat_mat  # noqa: E402


def all_triangles(src):
    d = parse(src)
    hulls, hull_of = d["hulls"], d["hull_of"]
    quat, pos, scl = d["quat"], d["pos"], d["scl"]
    pos_m = pos / 100.0
    by_hull = {}
    for i, h in enumerate(hull_of):
        by_hull.setdefault(int(h), []).append(i)

    chunks = []
    inst_ids = []
    for hi, inst_list in by_hull.items():
        verts, idx = hulls[hi]
        if idx.size == 0:
            continue
        inst = np.asarray(inst_list)
        tri0 = (verts[idx] / 100.0).astype(np.float32)
        B = max(1, int(2_000_000 // max(1, tri0.shape[0])))
        for s in range(0, len(inst), B):
            blk = inst[s:s + B]
            R = np.stack([quat_mat(q) for q in quat[blk]])
            v = tri0[None] * scl[blk][:, None, None, :]
            w = np.matmul(v, np.transpose(R, (0, 2, 1))[:, None, :, :])
            w += pos_m[blk][:, None, None, :]
            chunks.append(w.reshape(-1, 3, 3).astype(np.float32))
            inst_ids.append(np.repeat(blk, tri0.shape[0]))
    return np.concatenate(chunks, 0), np.concatenate(inst_ids, 0), d


def main(src):
    tri, inst_id, d = all_triangles(src)
    P = tri.reshape(-1, 3)
    print(f"三角面 {len(tri):,}   实例 {len(d['hull_of']):,}")

    lo, hi = P.min(0), P.max(0)
    print(f"\n[整体包围盒]  X {lo[0]:.1f} .. {hi[0]:.1f}  = {hi[0]-lo[0]:.1f} m")
    print(f"              Y {lo[1]:.1f} .. {hi[1]:.1f}  = {hi[1]-lo[1]:.1f} m")
    print(f"              Z {lo[2]:.1f} .. {hi[2]:.1f}  = {hi[2]-lo[2]:.1f} m")

    # ---- 主体区域：40 m 网格，剔除只含零星碰撞体的边缘格 ----
    cell = 40.0
    gx = ((P[:, 0] - lo[0]) / cell).astype(int)
    gy = ((P[:, 1] - lo[1]) / cell).astype(int)
    nx, ny = gx.max() + 1, gy.max() + 1
    grid = np.zeros((nx, ny), np.int32)
    np.add.at(grid, (gx, gy), 1)

    occ = grid > 0
    thr = np.percentile(grid[occ], 35)          # 低于 35 分位的格子视为零散碰撞体
    core = grid > max(20, thr)
    ci, cj = np.where(core)
    print(f"\n[主体区域] 40 m 网格阈值 {max(20, int(thr))} 面/格，占用格 {len(ci)}/{occ.sum()}")
    print(f"  X {lo[0]+ci.min()*cell:.1f} .. {lo[0]+(ci.max()+1)*cell:.1f}  = {(ci.max()-ci.min()+1)*cell:.1f} m")
    print(f"  Y {lo[1]+cj.min()*cell:.1f} .. {lo[1]+(cj.max()+1)*cell:.1f}  = {(cj.max()-cj.min()+1)*cell:.1f} m")

    # ---- 高程分层占比（按实例原点） ----
    pz = d["pos"][:, 2] / 100.0
    print("\n[高程分布 · 实例原点]")
    for a, b in [(-200, -60), (-60, -40), (-40, -20), (-20, 0), (0, 20), (20, 60), (60, 200)]:
        m = (pz >= a) & (pz < b)
        if m.sum():
            print(f"  {a:>5} .. {b:<5} m : {m.sum():>6} 个 ({m.mean()*100:5.1f}%)")

    # ---- 高层结构（可能的地标） ----
    topz = tri[:, :, 2].max(1)
    hi_mask = topz > np.percentile(topz, 99.7)
    th = tri[hi_mask]
    print(f"\n[最高 0.3% 三角面] z > {np.percentile(topz, 99.7):.1f} m，{hi_mask.sum():,} 个面")
    tp = th.reshape(-1, 3)
    # 聚类到 60 m 格，列出最高的几处
    key = ((tp[:, 0] // 60).astype(int), (tp[:, 1] // 60).astype(int))
    import collections
    best = collections.defaultdict(float)
    cnts = collections.defaultdict(int)
    for k, z in zip(zip(*key), tp[:, 2]):
        best[k] = max(best[k], z)
        cnts[k] += 1
    tops = sorted(best.items(), key=lambda kv: -kv[1])[:8]
    for (cx, cy), z in tops:
        print(f"   ({cx*60+30:>7.0f}, {cy*60+30:>7.0f}) m  顶点最高 {z:.1f} m  面数 {cnts[(cx,cy)]}")

    # ---- 最长连续结构的长度估计（桥/引道） ----
    # 用主方向投影 + 覆盖率判断：沿 45° 家族方向找最长的连续占用带
    print("\n[细长结构检测]")
    for ang in range(0, 180, 15):
        a = np.deg2rad(ang)
        u = np.stack([np.cos(a), np.sin(a)])
        t = inst_id.shape[0]
        cen = d["pos"][inst_id][:, :2] / 100.0
        proj = cen @ u
        perp = cen @ np.array([-u[1], u[0]])
        # 沿 proj 每 10 m 一格，看 perp 宽度 < 30 m 的连续格能延伸多远
        bins = np.floor(proj / 10).astype(int)
        order = np.argsort(bins)
        bs, pp = bins[order], perp[order]
        runs, cur, start = [], 0, None
        prev = None
        widths = {}
        for b, p in zip(bs, pp):
            if b not in widths:
                widths[b] = [p, p]
            else:
                widths[b][0] = min(widths[b][0], p)
                widths[b][1] = max(widths[b][1], p)
        keys = sorted(widths)
        best_len, cur_len = 0, 0
        for i, b in enumerate(keys):
            w = widths[b][1] - widths[b][0]
            narrow = w < 40 and (widths[b][1] - widths[b][0]) > 0
            if narrow:
                cur_len += 10
                best_len = max(best_len, cur_len)
            else:
                cur_len = 0
        if best_len >= 200:
            print(f"  方向 {ang:>3}° : 窄带连续长度 ≈ {best_len} m")

    return tri


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Physx/hangtianjidi.bin")
