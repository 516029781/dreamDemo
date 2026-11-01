"""相机投影换算：世界 (y, z) → 画面 v，用于把参考图的 v 带翻译成场景参数。

只用相机矩阵与视场角，不依赖 Blender（避免每次加载 200MB 场景）。
参数取自 scene.blend：loc (0.25, -20.5, 8.2)，rot_x 1.20999500，53mm / 36mm，1920x1078。
"""
import math
import sys

CAM = (0.25, -20.5, 8.2)
ROT_X = 1.20999500
LENS = 53.0
SENSOR_W = 36.0
RES_X, RES_Y = 1920, 1078

SENSOR_H = SENSOR_W * RES_Y / RES_X
TAN_HALF_V = (SENSOR_H / 2.0) / LENS

S, C = math.sin(ROT_X), math.cos(ROT_X)
# 相机局部轴在世界系里的表示
FWD = (0.0, S, -C)          # 视线方向（朝 +y 略向下）
UP = (0.0, C, S)            # 画面向上
RIGHT = (1.0, 0.0, 0.0)


def v_of(y, z, x=0.0):
    dx, dy, dz = x - CAM[0], y - CAM[1], z - CAM[2]
    depth = dx * FWD[0] + dy * FWD[1] + dz * FWD[2]
    up = dx * UP[0] + dy * UP[1] + dz * UP[2]
    ndc = (up / depth) / TAN_HALF_V
    return 0.5 * (1.0 - ndc)


def y_of(v, z, x=0.0):
    """给定 z 与 v，反解 y（在 z 平面上的交点）。"""
    lo, hi = -40.0, 200.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if v_of(mid, z, x) > v:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def table(z, label):
    print("\n== %s (z=%.2f) ==" % (label, z))
    print("   y      v")
    for y in (4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 26, 30):
        print("  %4.1f  %6.1f" % (y, 100 * v_of(y, z)))


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        print("v = %.1f%%" % (100 * v_of(float(sys.argv[1]), float(sys.argv[2]))))
        raise SystemExit
    table(0.06, "高平台顶面")
    table(-0.30, "低地块")
    table(-0.40, "水面")
    print("\n== 反解：目标 v → 该 z 平面上的 y ==")
    for z, name in ((0.06, "平台"), (-0.30, "低地"), (-0.40, "水面")):
        print("  %s: " % name, end="")
        for v in (0.30, 0.26, 0.22, 0.20, 0.18, 0.14, 0.10, 0.06):
            print("v%.0f→y%.1f  " % (100 * v, y_of(v, z)), end="")
        print()
