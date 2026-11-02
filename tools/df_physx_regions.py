"""按几何占用自动分割场景区块，输出各区块的尺寸与面积（用于确认“有多大”）。"""
import os
import sys
from collections import deque

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from df_physx_parse import parse, quat_mat  # noqa: E402


def instances_world(src):
    d = parse(src)
    hulls, hull_of = d["hulls"], d["hull_of"]
    quat, pos, scl = d["quat"], d["pos"], d["scl"]
    pos_m = pos / 100.0

    # 每个实例的世界空间 XY 半径（用 hull 顶点 bbox 估）
    rad = np.zeros(len(pos_m))
    for hi, (verts, idx) in enumerate(hulls):
        if verts.size == 0:
            continue
        ext = np.abs(verts / 100.0).max(0) * np.abs(scl[hull_of == hi]).max(0)
        rad[hull_of == hi] = np.hypot(ext[0], ext[1])
    return pos_m, rad, d


def main(src, cell=25.0):
    pos, rad, d = instances_world(src)
    lo = (pos[:, :2] - rad[:, None]).min(0) - 10
    hi = (pos[:, :2] + rad[:, None]).max(0) + 10
    nx = int(np.ceil((hi[0] - lo[0]) / cell))
    ny = int(np.ceil((hi[1] - lo[1]) / cell))

    grid = np.zeros((nx, ny), np.int32)
    gx = ((pos[:, 0] - lo[0]) / cell).astype(int)
    gy = ((pos[:, 1] - lo[1]) / cell).astype(int)
    ok = (gx >= 0) & (gx < nx) & (gy >= 0) & (gy < ny)
    np.add.at(grid, (gx[ok], gy[ok]), 1)

    occ = grid > 0
    thr = max(3, int(np.percentile(grid[occ], 30)))
    solid = grid > thr
    print(f"网格 {nx}x{ny} @ {cell:.0f} m，占用 {occ.sum()} 格，阈值 {thr} 面/格 -> 实心 {solid.sum()} 格")

    # 4-连通分量
    lab = -np.ones((nx, ny), np.int32)
    comps = []
    cur = 0
    for i in range(nx):
        for j in range(ny):
            if not solid[i, j] or lab[i, j] >= 0:
                continue
            q = deque([(i, j)])
            lab[i, j] = cur
            cells = []
            while q:
                x, y = q.popleft()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = x + dx, y + dy
                    if 0 <= a < nx and 0 <= b < ny and solid[a, b] and lab[a, b] < 0:
                        lab[a, b] = cur
                        q.append((a, b))
            comps.append(cells)
            cur += 1

    comps.sort(key=len, reverse=True)
    print(f"\n连通区块 {len(comps)} 个，列出前 6 个：\n")
    print(f"{'#':>2} {'X 范围(m)':>22} {'Y 范围(m)':>22} {'尺寸 W×D (m)':>18} {'格数':>6} {'约面积':>10}")
    for k, cells in enumerate(comps[:6], 1):
        ci = [c[0] for c in cells]
        cj = [c[1] for c in cells]
        x0, x1 = lo[0] + min(ci) * cell, lo[0] + (max(ci) + 1) * cell
        y0, y1 = lo[1] + min(cj) * cell, lo[1] + (max(cj) + 1) * cell
        area = len(cells) * cell * cell
        print(f"{k:>2} {x0:>8.0f}..{x1:<10.0f} {y0:>8.0f}..{y1:<10.0f} "
              f"{(x1-x0):>7.0f} × {(y1-y0):<7.0f} {len(cells):>6} {area/1e4:>7.1f} 公顷")

    # 最长轴尺寸
    print("\n[轴向尺寸]")
    P = pos[:, :2]
    print(f"  X 跨度 {P[:,0].max()-P[:,0].min():.0f} m, Y 跨度 {P[:,1].max()-P[:,1].min():.0f} m")
    # 主方向（PCA）
    c = P - P.mean(0)
    cov = c.T @ c / len(c)
    w, v = np.linalg.eigh(cov)
    u = v[:, np.argmax(w)]
    proj = c @ u
    perp = c @ np.array([-u[1], u[0]])
    ang = np.rad2deg(np.arctan2(u[1], u[0]))
    print(f"  主方向 {ang:.1f}°，沿主方向跨度 {proj.max()-proj.min():.0f} m，"
          f"垂直方向 {perp.max()-perp.min():.0f} m")
    return comps, lo, cell


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Physx/hangtianjidi.bin")
