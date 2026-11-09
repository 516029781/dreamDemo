"""简化版航天基地：三区总览图 + 核心区平面图（1 层平铺）。

核心区按真实布局做四角 + 中央：
  H1 离心（西南） H2 浮力（西北） H3 蓝市（东北） H4 黑市（东南） 总裁（中央）
总裁只从浮力 / 黑市两个口进，保持原有的"易守难攻"关系。
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = "C:/Windows/Fonts/"
BG = (11, 14, 20)
TXT = (228, 238, 244)
DIM = (132, 152, 166)


def F(sz, bold=False):
    for name in (("msyhbd.ttc" if bold else "msyh.ttc"), "simhei.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(FONT_DIR + name, sz)
        except Exception:
            continue
    return ImageFont.load_default()


def dashed_line(d, p1, p2, fill, width=4, dash=14, gap=9):
    x1, y1 = p1
    x2, y2 = p2
    L = math.hypot(x2 - x1, y2 - y1)
    if L < 1:
        return
    n = max(1, int(L // (dash + gap)))
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    for i in range(n + 1):
        s = i * (dash + gap)
        e = min(s + dash, L)
        if s >= L:
            break
        d.line([(x1 + ux * s, y1 + uy * s), (x1 + ux * e, y1 + uy * e)],
               fill=fill, width=width)


def arrow(d, p1, p2, fill, width=5, head=18):
    x1, y1 = p1
    x2, y2 = p2
    d.line([p1, p2], fill=fill, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    for s in (-0.45, 0.45):
        d.line([p2, (x2 - head * math.cos(ang + s), y2 - head * math.sin(ang + s))],
               fill=fill, width=width)


# ══════════════════════════════════════════════════════════
# 图 1：三区总览 + 完整撤离路线（统一局部坐标系，单位 m）
#   核心区 (0,0)..(240,240) ｜ 桥 (110,-200)..(130,0) ｜ 试车间 (35,-330)..(205,-200)
# ══════════════════════════════════════════════════════════
def draw_overview(out):
    W, H = 1400, 1800
    PX = 2.4
    OX = (W - 240 * PX) / 2
    OY = 1010

    def X(v):
        return OX + v * PX

    def Y(v):
        return OY + v * PX

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((64, 40), "航天基地 · 三区路线总览", fill=TXT, font=F(42, True))
    d.text((64, 96), "核心区 → 航天桥 → 试车间（丢包撤离点）｜ 主线约 570 m ｜ 单层平铺，无垂直交通",
           fill=DIM, font=F(18))

    route_col = (74, 222, 168)

    # ---------- 试车间 ----------
    d.rounded_rectangle([X(35), Y(-330), X(205), Y(-200)], radius=8,
                        fill=(120, 88, 60, 50), outline=(190, 146, 96), width=4)
    d.text((X(43), Y(-324)), "试 车 间", fill=TXT, font=F(26, True))
    d.text((X(43), Y(-310)), "170 × 130 m ｜ 单层大跨度厂房", fill=(200, 170, 140), font=F(14))
    # 卧式试车架
    d.rectangle([X(46), Y(-300), X(120), Y(-262)], outline=(160, 124, 86), width=2)
    d.text((X(48), Y(-308)), "卧式试车架", fill=(176, 146, 116), font=F(12))
    # 导流坑
    d.polygon([(X(136), Y(-300)), (X(170), Y(-300)), (X(158), Y(-262)), (X(146), Y(-262))],
              outline=(160, 124, 86), width=2)
    d.text((X(140), Y(-308)), "导流坑", fill=(176, 146, 116), font=F(12))

    # 丢包撤离点（东南角）
    dx, dy = 180, -285
    d.ellipse([X(dx) - 26, Y(dy) - 26, X(dx) + 26, Y(dy) + 26],
              fill=(60, 190, 140, 90), outline=(70, 220, 160), width=4)
    bb = d.textbbox((0, 0), "撤", font=F(20, True))
    d.text((X(dx) - bb[2] / 2, Y(dy) - 12), "撤", fill=(130, 245, 195), font=F(20, True))
    d.text((X(dx) - 46, Y(dy) + 36), "丢包撤离点", fill=(110, 235, 175), font=F(15, True))

    # ---------- 航天桥 ----------
    d.rectangle([X(110), Y(-200), X(130), Y(0)],
                fill=(168, 104, 74, 190), outline=(206, 136, 98), width=4)
    # 双塔
    for ty in (-150, -50):
        d.line([(X(104), Y(ty)), (X(104), Y(ty + 22))], fill=(206, 138, 100), width=4)
        d.line([(X(136), Y(ty)), (X(136), Y(ty + 22))], fill=(206, 138, 100), width=4)
    d.text((X(138), Y(-160)), "航 天 桥", fill=TXT, font=F(24, True))
    d.text((X(138), Y(-144)), "200 × 20 m ｜ 双塔斜拉", fill=DIM, font=F(14))
    d.text((X(138), Y(-130)), "全场唯一瓶颈，无岔路", fill=(186, 150, 128), font=F(14))

    # ---------- 核心区 ----------
    d.rounded_rectangle([X(0), Y(0), X(240), Y(240)], radius=8,
                        fill=(30, 38, 52, 130), outline=(120, 148, 176), width=4)
    d.text((X(8), Y(6)), "核 心 区", fill=TXT, font=F(24, True))
    d.text((X(8), Y(20)), "240 × 240 m ｜ 四角四室 + 中央总裁", fill=(160, 178, 194), font=F(13))

    mods = [
        ("浮力", 10, 10, 70, 75, (92, 138, 168)),
        ("蓝市", 160, 10, 70, 75, (96, 150, 140)),
        ("离心", 10, 155, 70, 75, (176, 120, 84)),
        ("黑市", 160, 155, 70, 75, (140, 110, 160)),
        ("总裁", 100, 100, 40, 40, (196, 168, 96)),
    ]
    for name, mx, my, mw, mh, col in mods:
        d.rounded_rectangle([X(mx), Y(my), X(mx + mw), Y(my + mh)], radius=4,
                            fill=(col[0], col[1], col[2], 70), outline=col, width=3)
        bb = d.textbbox((0, 0), name, font=F(18, True))
        d.text((X(mx + mw / 2) - bb[2] / 2, Y(my + mh / 2) - 12), name,
               fill=TXT, font=F(18, True))

    # 走廊示意
    d.rectangle([X(10), Y(85), X(230), Y(105)], fill=(80, 98, 124, 210))
    d.rectangle([X(10), Y(135), X(230), Y(155)], fill=(80, 98, 124, 210))
    d.rectangle([X(10), Y(105), X(30), Y(135)], fill=(80, 98, 124, 210))
    d.rectangle([X(210), Y(105), X(230), Y(135)], fill=(80, 98, 124, 210))

    # 北门
    d.rectangle([X(110), Y(-4), X(130), Y(4)], fill=BG)
    d.text((X(133), Y(-8)), "北门", fill=(170, 192, 208), font=F(13))

    # ---------- 撤离路线 ----------
    pts = [
        (48, 216),      # 离心室内起点
        (48, 155),      # 离心北门
        (48, 145),      # 南走廊
        (20, 145),
        (20, 95),       # 西走廊 → 北走廊
        (120, 95),
        (120, 0),       # 北门
        (120, -200),    # 过桥
        (120, -250),    # 试车间内
        (172, -278),    # 转向丢包点
    ]
    for i in range(len(pts) - 1):
        arrow(d, (X(pts[i][0]), Y(pts[i][1])),
              (X(pts[i + 1][0]), Y(pts[i + 1][1])), route_col, width=5, head=15)

    nx, ny = X(248), Y(96)
    d.text((nx, ny), "撤离路线", fill=route_col, font=F(17, True))
    for i, line in enumerate(["离心（起点）", "→ 西走廊 → 北走廊", "→ 北门 → 航天桥",
                              "→ 试车间 → 丢包点"]):
        d.text((nx, ny + 28 + i * 22), line, fill=(120, 210, 178), font=F(13))

    # ---------- 图例 ----------
    ly = H - 120
    d.line([(64, ly), (64 + 52, ly)], fill=route_col, width=5)
    d.text((64 + 66, ly - 11), "撤离路线（必经）", fill=TXT, font=F(16))
    d.rounded_rectangle([64 + 280, ly - 12, 64 + 308, ly + 12], radius=4,
                        fill=(196, 168, 96, 80), outline=(196, 168, 96), width=2)
    d.text((64 + 322, ly - 11), "总裁室（中央，双入口）", fill=TXT, font=F(16))
    d.text((64, ly + 40), "单层平铺：所有模块同标高，靠走廊和门连接，无楼梯",
           fill=(140, 158, 172), font=F(15))

    img.save(out)
    print("saved", out, img.size)


# ══════════════════════════════════════════════════════════
# 图 2：核心区平面（5 模块 + 环形走廊 + 门）
#   方位：上=北。离心在西南(左下)、浮力在西北(左上)
#        蓝市在东北(右上)、黑市在东南(右下)、总裁在正中
# ══════════════════════════════════════════════════════════
def draw_core(out):
    W, H = 1700, 1420
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((64, 44), "核心区 · 单层平面", fill=TXT, font=F(42, True))
    d.text((64, 100), "240 × 240 m ｜ 四角四室 + 中央总裁室 ｜ 环形走廊宽 20 m ｜ 全部同标高",
           fill=DIM, font=F(18))

    PX = 4.2
    ox, oy = 90, 230

    def X(v):
        return ox + v * PX

    def Y(v):
        return oy + v * PX

    # 外框
    d.rounded_rectangle([X(0), Y(0), X(240), Y(240)], radius=8,
                        fill=(30, 38, 52, 120), outline=(112, 138, 168), width=4)

    # 环形走廊
    COR = (80, 98, 124, 225)
    d.rectangle([X(10), Y(85), X(230), Y(105)], fill=COR)     # 北
    d.rectangle([X(10), Y(135), X(230), Y(155)], fill=COR)    # 南
    d.rectangle([X(10), Y(105), X(30), Y(135)], fill=COR)     # 西
    d.rectangle([X(210), Y(105), X(230), Y(135)], fill=COR)   # 东
    d.text((X(112), Y(89)), "北走廊", fill=(158, 178, 196), font=F(13))
    d.text((X(112), Y(140)), "南走廊", fill=(158, 178, 196), font=F(13))

    rooms = [
        # name, x, y, w, h, color, note, 方位
        ("H2 浮力", 10, 10, 70, 75, (92, 138, 168), "22 点 · 深潜池", "西北"),
        ("H3 蓝市", 160, 10, 70, 75, (96, 150, 140), "18 点 · 直升机电闸", "东北"),
        ("H1 离心", 10, 155, 70, 75, (176, 120, 84), "31 点 · 全图最肥", "西南"),
        ("H4 黑市", 160, 155, 70, 75, (140, 110, 160), "10 点 · 支线小室", "东南"),
    ]
    for name, rx, ry, rw, rh, col, note, comp in rooms:
        d.rounded_rectangle([X(rx), Y(ry), X(rx + rw), Y(ry + rh)], radius=5,
                            fill=(col[0], col[1], col[2], 66), outline=col, width=3)
        bb = d.textbbox((0, 0), name, font=F(22, True))
        d.text((X(rx + rw / 2) - bb[2] / 2, Y(ry + rh / 2) - 30), name, fill=TXT, font=F(22, True))
        bb = d.textbbox((0, 0), note, font=F(13))
        d.text((X(rx + rw / 2) - bb[2] / 2, Y(ry + rh / 2) + 2), note,
               fill=(208, 220, 228), font=F(13))
        bb = d.textbbox((0, 0), comp, font=F(12))
        d.text((X(rx + rw / 2) - bb[2] / 2, Y(ry + rh / 2) + 24), comp,
               fill=(140, 158, 172), font=F(12))

    # 中央总裁室
    d.rounded_rectangle([X(100), Y(100), X(140), Y(140)], radius=5,
                        fill=(196, 168, 96, 84), outline=(216, 188, 114), width=4)
    bb = d.textbbox((0, 0), "总裁室", font=F(19, True))
    d.text((X(120) - bb[2] / 2, Y(112)), "总裁室", fill=(255, 248, 220), font=F(19, True))
    bb = d.textbbox((0, 0), "11 点", font=F(13))
    d.text((X(120) - bb[2] / 2, Y(132)), "11 点", fill=(242, 228, 192), font=F(13))

    # 总裁两条通道（只接浮力 / 黑市）
    d.line([(X(100), Y(100)), (X(70), Y(85))], fill=(216, 188, 114), width=9)
    d.line([(X(140), Y(140)), (X(170), Y(155))], fill=(216, 188, 114), width=9)
    d.text((X(74), Y(90)), "通道 A", fill=(232, 206, 140), font=F(14))
    d.text((X(146), Y(150)), "通道 B", fill=(232, 206, 140), font=F(14))

    # 房间门（在房间边线上开缺口）
    doors = [
        (44, 82, 8, 7),    # 浮力 -> 北走廊
        (188, 82, 8, 7),   # 蓝市 -> 北走廊
        (44, 151, 8, 7),   # 离心 -> 南走廊
        (188, 151, 8, 7),  # 黑市 -> 南走廊
    ]
    for gx, gy, gw, gh in doors:
        d.rectangle([X(gx), Y(gy), X(gx + gw), Y(gy + gh)], fill=(20, 26, 36))

    # 中庭北区 + 北门
    d.text((X(104), Y(40)), "中庭北区", fill=(150, 168, 184), font=F(16))
    d.rectangle([X(110), Y(-5), X(130), Y(5)], fill=(20, 26, 36))
    d.polygon([(X(120), Y(-13)), (X(113), Y(0)), (X(127), Y(0))], fill=(74, 222, 168))
    d.text((X(134), Y(-11)), "北门 → 航天桥", fill=(110, 235, 175), font=F(16, True))

    # 中央中庭
    d.text((X(148), Y(112)), "中央", fill=(128, 148, 164), font=F(13))
    d.text((X(148), Y(124)), "中庭", fill=(128, 148, 164), font=F(13))

    # 撤离路线：离心 → 西走廊 → 北走廊 → 中庭北区 → 北门
    route = [(48, 216), (48, 145), (20, 145), (20, 95), (120, 95), (120, 10), (120, -6)]
    rc = (74, 222, 168)
    for i in range(len(route) - 1):
        dashed_line(d, (X(route[i][0]), Y(route[i][1])),
                    (X(route[i + 1][0]), Y(route[i + 1][1])), rc, width=5, dash=16, gap=10)
    d.ellipse([X(48) - 9, Y(216) - 9, X(48) + 9, Y(216) + 9],
              outline=rc, width=4)

    # 尺寸标注
    d.line([(X(0), Y(252)), (X(240), Y(252))], fill=(120, 140, 156), width=2)
    for xx in (0, 240):
        d.line([(X(xx), Y(248)), (X(xx), Y(256))], fill=(120, 140, 156), width=2)
    bb = d.textbbox((0, 0), "240 m", font=F(15))
    d.text((X(120) - bb[2] / 2, Y(256)), "240 m", fill=(160, 180, 194), font=F(15))

    # 右侧说明
    tx = X(250)
    ty = oy + 4
    d.text((tx, ty), "连通关系", fill=(200, 218, 230), font=F(21, True))
    ty += 40
    rows = [
        ("离心 — 浮力", "西走廊直连", TXT),
        ("浮力 — 蓝市", "北走廊直连", TXT),
        ("蓝市 — 黑市", "东走廊直连", TXT),
        ("黑市 — 离心", "南走廊直连", TXT),
        ("总裁 — 浮力", "通道 A（入口一）", (232, 206, 140)),
        ("总裁 — 黑市", "通道 B（入口二）", (232, 206, 140)),
    ]
    for a, b, col in rows:
        d.text((tx, ty), a, fill=col, font=F(15, True))
        d.text((tx + 150, ty), b, fill=(168, 186, 200), font=F(15))
        ty += 30

    ty += 16
    for line in ["外圈四条走廊形成闭环，", "任意两室之间最多走一条边。",
                 "总裁室只有两个入口，", "没有第三个口——这是它", "易守难攻的原因。"]:
        d.text((tx, ty), line, fill=DIM, font=F(14))
        ty += 24

    ty += 20
    d.text((tx, ty), "1 层化处理", fill=(200, 218, 230), font=F(21, True))
    ty += 36
    for line in ["原设定总裁室在四层悬空，", "需爬竖梯。本方案压到同一层，",
                 "但保留「只能从浮力/黑市进」", "的双入口关系，玩法张力不变。"]:
        d.text((tx, ty), line, fill=DIM, font=F(14))
        ty += 24

    img.save(out)
    print("saved", out, img.size)


if __name__ == "__main__":
    base = "C:/软件/鼠鼠/art/static_map/space_base_minigame/concept"
    os.makedirs(base, exist_ok=True)
    draw_overview(os.path.join(base, "simple_v02_route_overview.png"))
    draw_core(os.path.join(base, "simple_v02_core_plan.png"))
