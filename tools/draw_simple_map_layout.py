"""生成简化版地图的区域布局示意图（俯视、非等比）。"""
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 1900
BG = (13, 17, 23)
PANEL = (20, 26, 36)
LINE = (70, 84, 100)
TXT = (226, 236, 242)
DIM = (128, 148, 162)

FONT_DIR = "C:/Windows/Fonts/"


def F(sz, bold=False):
    for name in (("msyhbd.ttc" if bold else "msyh.ttc"), "simhei.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(FONT_DIR + name, sz)
        except Exception:
            continue
    return ImageFont.load_default()


REGIONS = [
    # id, 名称, 副标题, 中心x, 中心y, w, h, 颜色
    ("A", "南门集散区", "出生 / 撤离  ·  90 × 80 m", 800, 1560, 300, 190, (200, 169, 107)),
    ("B", "总装厂房", "主枢纽 / 分叉  ·  120 × 100 m", 800, 1200, 400, 280, (126, 147, 168)),
    ("C", "指挥控制楼", "支线 / 资源  ·  70 × 70 m", 300, 1200, 250, 220, (92, 138, 138)),
    ("D", "航天桥", "连接 / 瓶颈  ·  180 × 25 m", 800, 800, 130, 380, (168, 101, 74)),
    ("E", "发射工位", "高潮区  ·  110 × 110 m", 800, 370, 400, 240, (217, 144, 74)),
    ("F", "试车台", "终点  ·  100 × 90 m", 1330, 420, 320, 260, (138, 106, 74)),
]

LINKS = [
    # x1,y1,x2,y2, 标签, 主线?, 标签左上角坐标
    (800, 1465, 800, 1340, "L1  厂区道路 · 60 m", True, (826, 1390)),
    (610, 1200, 425, 1200, "L2  连廊 · 40 m", False, (446, 1216)),
    (800, 1060, 800, 990, "L3  北门引道 · 50 m", True, (826, 1012)),
    (800, 610, 800, 490, "L4  桥尾入口 · 45 m", True, (826, 538)),
    (1000, 370, 1170, 420, "L5  管线廊道 · 70 m", True, (1010, 440)),
]


def main(out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")

    # 标题
    d.text((80, 60), "航天基地 · 简化地图布局", fill=TXT, font=F(46, True))
    d.text((80, 118), "6 个关键区域 / 5 条连接路线 / 主线约 500 m · 90 秒 ｜ 俯视示意，非等比",
           fill=DIM, font=F(20))

    # 连接线（先画线，区域盖在上面）
    for x1, y1, x2, y2, label, mainline, tag_xy in LINKS:
        if mainline:
            d.line([(x1, y1), (x2, y2)], fill=(150, 176, 196, 235), width=10)
        else:
            # 虚线
            import math
            L = math.hypot(x2 - x1, y2 - y1)
            n = int(L // 18)
            for i in range(n):
                t0, t1 = i / n, (i + 0.55) / n
                a = (x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0)
                b = (x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1)
                d.line([a, b], fill=(120, 140, 158, 200), width=6)
        # 标签（固定坐标，避免压住区域框）
        lx, ly = tag_xy
        tw = d.textlength(label, font=F(16))
        d.rectangle([lx - 8, ly - 5, lx + tw + 8, ly + 23], fill=(13, 17, 23, 230))
        d.text((lx, ly), label, fill=(178, 198, 212), font=F(16))

    # 区域
    for rid, name, sub, cx, cy, w, h, col in REGIONS:
        x0, y0 = cx - w / 2, cy - h / 2
        x1, y1 = cx + w / 2, cy + h / 2
        d.rounded_rectangle([x0, y0, x1, y1], radius=14,
                            fill=(col[0], col[1], col[2], 40),
                            outline=(col[0], col[1], col[2], 255), width=4)
        # ID 角标
        d.rounded_rectangle([x0 + 10, y0 + 10, x0 + 56, y0 + 56], radius=8,
                            fill=(col[0], col[1], col[2], 235))
        bb = d.textbbox((0, 0), rid, font=F(28, True))
        d.text((x0 + 33 - (bb[2] - bb[0]) / 2, y0 + 22), rid, fill=(18, 22, 30), font=F(28, True))
        if rid == "D":
            # 窄条：竖排名称 + 下方小字
            chars = list(name)
            fs = 34
            total = len(chars) * (fs + 6)
            ty = cy - total / 2 - 34
            for ch in chars:
                bb = d.textbbox((0, 0), ch, font=F(fs, True))
                d.text((cx - (bb[2] - bb[0]) / 2, ty), ch, fill=TXT, font=F(fs, True))
                ty += fs + 6
            sub2 = "180 × 25 m"
            bb = d.textbbox((0, 0), sub2, font=F(15))
            d.text((cx - (bb[2] - bb[0]) / 2, cy + total / 2 - 20), sub2,
                   fill=(196, 212, 222), font=F(15))
        else:
            fs_name = 30 if w >= 240 else 24
            bb = d.textbbox((0, 0), name, font=F(fs_name, True))
            d.text((cx - (bb[2] - bb[0]) / 2, cy - 30), name, fill=TXT, font=F(fs_name, True))
            fs_sub = 17 if w >= 240 else 14
            bb = d.textbbox((0, 0), sub, font=F(fs_sub))
            d.text((cx - (bb[2] - bb[0]) / 2, cy + 10), sub, fill=(196, 212, 222), font=F(fs_sub))

    # 图例
    lx, ly = 80, 1720
    d.text((lx, ly - 40), "图例", fill=DIM, font=F(19, True))
    d.line([(lx, ly + 8), (lx + 60, ly + 8)], fill=(150, 176, 196), width=9)
    d.text((lx + 78, ly - 8), "主线（必经）", fill=TXT, font=F(18))
    for i in range(4):
        d.line([(lx + 300 + i * 17, ly + 8), (lx + 310 + i * 17, ly + 8)],
               fill=(120, 140, 158), width=6)
    d.text((lx + 380, ly - 8), "支线（死路，含奖励）", fill=TXT, font=F(18))

    # 锚点提示
    d.text((W - 80 - 620, 1720 - 8),
           "识别锚点：立式箭体（B）· 发射塔架（E）· 斜拉桥（D）",
           fill=(150, 170, 184), font=F(18))

    img.save(out)
    print("saved", out, img.size)


if __name__ == "__main__":
    out = ("C:/软件/鼠鼠/art/static_map/space_base_minigame/concept/"
           "simple_map_layout_v01.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    main(out)
