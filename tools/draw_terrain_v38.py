"""v3.8 地形骨架示意图（北朝上）。

输出：planning/art/_terrain_v38.png
坐标：世界 x 0..240，y -254..166；1 m = 5 px。
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W_M, H_M = 240.0, 420.0
S = 5.0
PAD_L, PAD_T, PAD_R, PAD_B = 90, 250, 90, 120
W = int(W_M * S) + PAD_L + PAD_R
H = int(H_M * S) + PAD_T + PAD_B
Y_TOP = 166.0

WATER = (26, 45, 50)
WATER_LINE = (34, 56, 60)
LAND = (150, 148, 137)
LAND_EDGE = (96, 96, 88)
ROAD = (54, 60, 61)
PLAZA = (178, 174, 160)
GARDEN = (154, 158, 136)
DOCK = (128, 132, 128)
LAUNCH = (86, 84, 78)
ROOM = {
    "H1 离心": (176, 154, 128),
    "H2 浮力": (128, 158, 166),
    "H3 蓝室": (120, 132, 170),
    "H4 黑室": (126, 160, 134),
}
INK = (238, 236, 226)
MUTED = (176, 186, 184)
ACCENT = (232, 146, 74)
ACCENT2 = (120, 216, 190)

FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_B = "C:/Windows/Fonts/msyhbd.ttc"


def f(sz, bold=False):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT, sz)
    except Exception:
        return ImageFont.load_default()


def X(x):
    return PAD_L + x * S


def Y(y):
    return PAD_T + (Y_TOP - y) * S


def poly(dr, pts, fill=None, outline=None, width=2):
    p = [(X(x), Y(y)) for x, y in pts]
    dr.polygon(p, fill=fill, outline=outline)
    if outline and width > 1:
        dr.line(p + [p[0]], fill=outline, width=width)


def rot(o, u, v, du, dv):
    """局部坐标 -> 世界坐标。u/v 为单位向量。"""
    return (o[0] + u[0] * du + v[0] * dv, o[1] + u[1] * du + v[1] * dv)


def text(dr, xy, s, sz=20, fill=INK, bold=False, anchor="la"):
    dr.text((X(xy[0]), Y(xy[1])), s, font=f(sz, bold), fill=fill, anchor=anchor)


def main():
    img = Image.new("RGB", (W, H), WATER)
    dr = ImageDraw.Draw(img)

    # 水面细纹
    for i in range(0, W, 72):
        dr.line([(i, PAD_T), (i + 260, H - PAD_B)], fill=WATER_LINE, width=1)

    # ---------- 陆地 ----------
    # 核心岛：切角八边形
    core = [(72, -14), (168, -14), (194, 8), (194, 112),
            (168, 134), (72, 134), (46, 112), (46, 8)]
    poly(dr, core, LAND, LAND_EDGE, 4)

    # 南花园半岛
    poly(dr, [(70, -64), (170, -64), (170, -14), (70, -14)], GARDEN, LAND_EDGE, 4)

    # 堤道
    d = (12.0, -78.0)
    L = math.hypot(*d)
    u = (d[0] / L, d[1] / L)
    n = (-u[1], u[0])
    a = (160, -58)
    b = (172, -136)
    poly(dr, [(a[0] + n[0] * 9, a[1] + n[1] * 9), (b[0] + n[0] * 9, b[1] + n[1] * 9),
              (b[0] - n[0] * 9, b[1] - n[1] * 9), (a[0] - n[0] * 9, a[1] - n[1] * 9)],
         LAND, LAND_EDGE, 4)

    # 水平试车间（干船坞）：20° 斜置
    O = (172, -136)
    ang = math.radians(20)
    uu = (math.sin(ang), -math.cos(ang))
    vv = (math.cos(ang), math.sin(ang))
    dock = [rot(O, uu, vv, 0, -25), rot(O, uu, vv, 96, -25),
            rot(O, uu, vv, 96, 25), rot(O, uu, vv, 0, 25)]
    poly(dr, dock, DOCK, (232, 228, 214), 7)
    # 坞底（内缩 2.5 m）
    floor = [rot(O, uu, vv, 2.5, -22.5), rot(O, uu, vv, 93.5, -22.5),
             rot(O, uu, vv, 93.5, 22.5), rot(O, uu, vv, 2.5, 22.5)]
    poly(dr, floor, (104, 108, 104), (60, 64, 60), 2)
    # 西墙检修坡道（从 +6 下到 ±0）
    ramp = [rot(O, uu, vv, 6, -22), rot(O, uu, vv, 66, -22),
            rot(O, uu, vv, 66, -17), rot(O, uu, vv, 6, -17)]
    poly(dr, ramp, (188, 184, 170), (120, 116, 104), 2)
    for i in range(9):
        u0 = 8 + i * 6
        c = rot(O, uu, vv, u0, -22)
        d2 = rot(O, uu, vv, u0, -17)
        dr.line([(X(c[0]), Y(c[1])), (X(d2[0]), Y(d2[1]))], fill=(150, 146, 134), width=2)


    # 西区大门（桥 + 岛 + 断头院）
    poly(dr, [(32, 50), (46, 50), (46, 70), (32, 70)], LAND, LAND_EDGE, 3)
    poly(dr, [(16, 42), (32, 42), (32, 78), (16, 78)], LAND, LAND_EDGE, 4)
    poly(dr, [(4, 36), (16, 36), (16, 84), (4, 84)], LAND, LAND_EDGE, 4)

    # 西侧远景：太空电梯塔所在的小岛
    poly(dr, [(2, 100), (20, 100), (20, 128), (2, 128)], LAND, LAND_EDGE, 3)

    # ---------- 环路（八边形环带） ----------
    poly(dr, core, ROAD)
    poly(dr, [(60, 0), (180, 0), (180, 120), (60, 120)], LAND, LAND_EDGE, 3)

    # ---------- 四室 ----------
    rooms = [
        ("H1 离心", 60, 0, 120, 60),
        ("H4 黑室", 120, 0, 180, 60),
        ("H2 浮力", 60, 60, 120, 120),
        ("H3 蓝室", 120, 60, 180, 120),
    ]
    for name, x0, y0, x1, y1 in rooms:
        poly(dr, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], ROOM[name], (70, 70, 64), 4)
        text(dr, ((x0 + x1) / 2, (y0 + y1) / 2 + 4), name, 26, (36, 38, 34), True, "mm")

    # 中脊 / 导轨
    dr.line([(X(120), Y(120)), (X(120), Y(0))], fill=(70, 74, 68), width=7)
    dr.line([(X(120), Y(120)), (X(120), Y(0))], fill=(206, 210, 202), width=2)
    for ty in range(4, 134, 12):
        dr.line([(X(118.4), Y(ty)), (X(121.6), Y(ty))], fill=(206, 210, 202), width=1)
    text(dr, (128, 129), "屋顶导轨（不可通行）", 11, (212, 214, 204), True, "la")

    # 总裁盒
    box = [(100, 45), (140, 45), (140, 75), (100, 75)]
    poly(dr, box, (214, 200, 160), ACCENT, 4)
    text(dr, (120, 64), "总裁", 22, (70, 54, 30), True, "mm")
    text(dr, (120, 52), "悬空 12 m", 14, (92, 72, 44), False, "mm")

    # 花园喷泉 / 折纸
    dr.ellipse([X(109), Y(-28), X(131), Y(-50)], outline=(92, 150, 150), width=5)
    dr.ellipse([X(115), Y(-34), X(125), Y(-44)], outline=(92, 150, 150), width=3)
    text(dr, (120, -38), "◎ 喷泉", 14, (56, 84, 84), False, "mm")
    for px in (98, 142):
        dr.polygon([(X(px), Y(-26)), (X(px + 5), Y(-31)), (X(px - 2), Y(-34))],
                   fill=ACCENT, outline=(120, 70, 30))
    text(dr, (86, -60), "南侧花园半岛 100×50", 15, (58, 64, 52), True, "la")

    # 堤道标注
    text(dr, (180, -96), "跨水堤道 18 m", 15, (70, 74, 66), True, "la")

    # 试车间标注（沿长轴）
    text(dr, (190, -184), "水平试车间", 19, (48, 50, 46), True, "ma")
    text(dr, (190, -191), "坞底 ±0 · 墙顶 +9", 11, (66, 68, 64), False, "ma")
    # 内部集装箱列
    for _u in (40, 50, 60, 70, 78):
        c = rot(O, uu, vv, _u, 16)
        dr.rectangle([X(c[0] - 3), Y(c[1] + 1), X(c[0] + 3), Y(c[1] - 1)],
                     fill=(78, 96, 92), outline=(40, 50, 48))
    # 撤离点
    ex = rot(O, uu, vv, 90, 19)
    dr.rectangle([X(ex[0] - 3), Y(ex[1] + 3), X(ex[0] + 3), Y(ex[1] - 3)],
                 fill=(240, 206, 90), outline=(120, 90, 20), width=3)
    text(dr, (ex[0] - 9, ex[1] + 2), "撤离点", 13, (120, 88, 20), True, "rm")

    # 西区大门
    text(dr, (24, 86), "西区大门（封死）", 13, (232, 226, 210), True, "la")
    # 西侧远景太空电梯
    dr.line([(X(11), Y(114)), (X(11), Y(114) - 96)], fill=(214, 218, 214), width=5)
    dr.line([(X(4), Y(114) - 90), (X(18), Y(114) - 90)], fill=(214, 218, 214), width=7)
    dr.rectangle([X(7), Y(114) + 2, X(15), Y(108)], fill=(206, 210, 206), outline=(80, 84, 80), width=2)
    text(dr, (24, 108), "电梯塔（远景）", 11, (200, 206, 200), True, "la")

    # ---------- 撤离路线 ----------
    dock_uv = [(0, 0), (6, -18), (66, -18), (74, -16), (74, 19), (90, 19)]
    dock_xy = [rot(O, uu, vv, u, v) for u, v in dock_uv]
    route = [(90, 30), (90, 0), (120, 0), (120, -14), (120, -27), (131, -31),
             (133, -39), (131, -47), (145, -54), (160, -58), (172, -136)] + dock_xy[1:]
    pts = [(X(x), Y(y)) for x, y in route]
    dr.line(pts, fill=ACCENT, width=5, joint="curve")
    for p in pts:
        dr.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=ACCENT)

    # 距离分段
    text(dr, (93, 22), "30 m", 12, (120, 60, 20), True, "rm")
    text(dr, (104, -3), "44 m", 12, (120, 60, 20), True, "lm")
    text(dr, (152, -40), "花园 70 m", 12, (120, 60, 20), True, "lm")
    text(dr, (182, -104), "堤道 79 m", 12, (120, 60, 20), True, "lm")
    text(dr, (175, -150), "坞内 138 m", 12, (120, 60, 20), True, "lm")

    # ---------- 标注 ----------
    text(dr, (53, 64), "西环路", 12, (224, 226, 216), True, "mm")
    text(dr, (187, 64), "东环路", 12, (224, 226, 216), True, "mm")
    text(dr, (60, 127), "北环路 14 m", 13, (220, 220, 210), True, "la")
    text(dr, (120, -9), "南 环 路", 14, (52, 58, 54), True, "ma")
    text(dr, (90, -110), "南 湾（水）", 16, (120, 170, 172), True, "mm")

    # 比例尺
    bx, by = PAD_L + 14, H - 58
    dr.line([(bx, by), (bx + 100 * S, by)], fill=INK, width=4)
    for xx in (bx, bx + 50 * S, bx + 100 * S):
        dr.line([(xx, by - 7), (xx, by + 7)], fill=INK, width=4)
    dr.text((bx, by + 12), "0", font=f(14), fill=INK)
    dr.text((bx + 50 * S - 12, by + 12), "50", font=f(14), fill=INK)
    dr.text((bx + 100 * S - 18, by + 12), "100 m", font=f(14), fill=INK)

    # 指北针
    nx, ny = W - 62, PAD_T - 34
    dr.ellipse([nx - 26, ny - 18, nx + 26, ny + 34], fill=(18, 30, 34), outline=(70, 96, 98))
    dr.polygon([(nx, ny - 12), (nx - 9, ny + 18), (nx, ny + 11), (nx + 9, ny + 18)], fill=INK)
    dr.text((nx - 5, ny + 20), "N", font=f(13, True), fill=INK)

    # 标题
    dr.text((PAD_L, 28), "航天基地 · v3.10 地形骨架", font=f(38, True), fill=INK)
    dr.text((PAD_L, 74), "北朝上 ｜ 水域为底 ｜ 核心区切角岛 ｜ 南侧花园半岛 ｜ 跨水堤道 ｜ 东南干船坞 ｜ 撤离 361 m",
            font=f(17), fill=MUTED)

    # 图例
    lx, ly = PAD_L, 108
    items = [("陆地 / 平台", LAND), ("环路", ROAD), ("水", (52, 88, 92)), ("撤离路线", ACCENT)]
    for i, (label, col) in enumerate(items):
        xx = lx + i * 168
        dr.rectangle([xx, ly, xx + 18, ly + 18], fill=col, outline=MUTED)
        dr.text((xx + 24, ly + 1), label, font=f(14), fill=MUTED)

    os.makedirs("planning/art", exist_ok=True)
    out = "planning/art/_terrain_v39.png"
    img.save(out)
    print("saved", out, img.size)


if __name__ == "__main__":
    main()
