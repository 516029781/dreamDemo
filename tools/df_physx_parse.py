"""TIMEPX01 解析器 —— 还原《三角洲行动》PhysX 场景几何。

格式（小端）：
  0..7    magic "TIMEPX01"
  12      nXf   实例数（文件末尾 nXf*48 字节变换表）
  16      nHull 网格原型数
  20      nTile 地形瓦片数
  64..    hull 段：每项 [vc u32][tc u32][fl u32][verts vc*3 f32][idx tc*3 u16]
  其后    tile 段：每项 48411 字节 = 24 头 + 127*127*3（高度用前 127*127 个 u16）
  末尾    xf  段：每项 48 字节 = quat(4f) pos(3f) scl(3f) hull(u32) pad(4)
"""
import struct
import numpy as np

TILE_STRIDE = 127 * 127 * 3 + 24
XF_STRIDE = 48
N = 127


def parse(path):
    b = open(path, "rb").read()
    if b[:8] != b"TIMEPX01":
        raise ValueError("not TIMEPX01")
    n = len(b)
    nXf, nHull, nTile = struct.unpack_from("<III", b, 12)

    # ---- hull 段 ----
    hulls = []
    p = 64
    while p + 12 <= n:
        vc, tc, fl = struct.unpack_from("<III", b, p)
        if not vc or vc > 2_000_000 or tc > 4_000_000 or fl > 0xFFFF:
            break
        vs = p + 12
        ve = vs + vc * 12
        ie = ve + tc * 6
        if ie > n:
            break
        verts = np.frombuffer(b, dtype="<f4", count=vc * 3, offset=vs).reshape(-1, 3).astype(np.float64)
        verts[~np.isfinite(verts)] = 0.0
        idx = np.frombuffer(b, dtype="<u2", count=tc * 3, offset=ve).reshape(-1, 3).astype(np.int32)
        if idx.size and idx.max() >= vc:
            break
        hulls.append((verts, idx))
        p = ie

    # ---- tile 段 ----
    tiles = []
    while p + TILE_STRIDE <= n:
        nx, nz, sc = struct.unpack_from("<IIf", b, p)
        if nx != 127 or nz != 127 or not (1e-4 < sc < 1e4):
            break
        hgt = np.frombuffer(b, dtype="<u2", count=N * N, offset=p + 24).reshape(N, N)
        tiles.append({"hgt": hgt, "scale": sc})
        p += TILE_STRIDE

    # ---- xf 段 ----
    tr = n - nXf * XF_STRIDE
    raw = np.frombuffer(b, dtype="<f4", count=nXf * 12, offset=tr).reshape(nXf, 12)
    hu = np.frombuffer(b, dtype="<u4", count=nXf, offset=tr + 40 * 1) if False else None
    quat = raw[:, 0:4].astype(np.float64)
    pos = raw[:, 4:7].astype(np.float64)
    scl = raw[:, 7:10].astype(np.float64)
    hull_of = np.frombuffer(b, dtype="<u4", count=nXf, offset=0).astype(np.int64)  # placeholder
    # 逐项取 hull 索引（stride 48，u32 @40）
    idx_hull = np.empty(nXf, dtype=np.int64)
    for i in range(nXf):
        idx_hull[i] = struct.unpack_from("<I", b, tr + i * XF_STRIDE + 40)[0]

    return {
        "hulls": hulls,
        "tiles": tiles,
        "quat": quat,
        "pos": pos,
        "scl": scl,
        "hull_of": idx_hull,
        "counts": (nXf, nHull, nTile),
        "consumed": p,
    }


def quat_mat(q):
    """四元数 -> 3x3 基（与 index.html quatBasis 一致）"""
    x, y, z, w = q
    n2 = x * x + y * y + z * z + w * w
    if n2 < 1e-12:
        n2 = 1.0
    s = 2.0 / n2
    return np.array([
        [1 - s * (y * y + z * z), s * (x * y - w * z), s * (x * z + w * y)],
        [s * (x * y + w * z), 1 - s * (x * x + z * z), s * (y * z - w * x)],
        [s * (x * z - w * y), s * (y * z + w * x), 1 - s * (x * x + y * y)],
    ])


if __name__ == "__main__":
    d = parse("Physx/hangtianjidi.bin")
    tri = sum(h[1].shape[0] for h in d["hulls"])
    vtx = sum(h[0].shape[0] for h in d["hulls"])
    used = np.bincount(d["hull_of"], minlength=len(d["hulls"]))
    print(f"hulls={len(d['hulls'])} verts={vtx:,} tris={tri:,}")
    print(f"instances={len(d['hull_of'])}  hull usage: max={used.max()}  unused={np.sum(used==0)}")
    print(f"tiles={len(d['tiles'])} scale range={min(t['scale'] for t in d['tiles']):.4f}..{max(t['scale'] for t in d['tiles']):.4f}")
    print(f"hull section ends at {d['consumed']:,} bytes; remaining before xf = {(len(open('Physx/hangtianjidi.bin','rb').read()) - len(d['hull_of'])*48) - d['consumed']:,}")
    print("instance pos range:", d["pos"].min(0).round(0), d["pos"].max(0).round(0))
    print("instance hull idx range:", d["hull_of"].min(), d["hull_of"].max())
