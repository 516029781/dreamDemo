# -*- coding: utf-8 -*-
"""实机色板 vs v05 现值对照表（供方案引用）。数据源：reference/_df_screenshots/PALETTE.json + 5.11.2 换算。"""
from PIL import Image, ImageDraw, ImageFont

ROWS = [
    ("H1 离心", "圆形腔体 · 中央柱 · 横置吊舱", "#1E2A2F", "#0B6D83", "#547684", "#77837E", "灰绿 → 青灰"),
    ("H2 浮力", "矩形深池 · 冷灰钢 · 少量锈", "#16262B", "#1D6C79", "#477A8A", "#8A8F86", "灰绿 → 深青"),
    ("H3 蓝室", "深藏蓝肋板墙 · 肋间蓝灯带", "#05142F", "#40659D", "#3A6DBF", "#A2A396", "浅灰 → 藏蓝"),
    ("H4 黑室", "墨绿灰墙 · 绿涂装板仅少量", "#21312F", "#4D864E", "#58837D", "#6E7568", "灰绿 → 墨绿青"),
    ("C5 总裁", "深棕木 · 棕皮革 · 黄铜 · 绿植", "#4B3B2E", "#976D49", "#95755B", "#D8C9AE", "奶油 → 深棕木"),
    ("水平试车间", "灰绿混凝土 · 深青设备 · 黄黑警示", "#47514C", "#204144", "#788980", "#878D8C", "略偏绿"),
    ("撤离点", "蓝光淹没 · 黄色只做地面标记", "#275292", "#3E66A3", "#467CCD", "#F2C230", "黄 → 蓝光"),
]
HEAD = ["实机主色", "实机强调", "换算后（用）", "v05 现值"]

PAD, ROW_H, TOP = 34, 108, 160
W = 1320
H = TOP + ROW_H * len(ROWS) + 70
c = Image.new("RGB", (W, H), (17, 21, 25))
d = ImageDraw.Draw(c)
fT = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 30)
fR = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 21)
fS = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 14)
fM = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 15)

d.text((PAD, 26), "航天基地 · 实机色板 vs v05 现值（来源：reference/_df_screenshots/PALETTE.json）", font=fT, fill=(238, 242, 236))
d.text((PAD, 68), "四间房在实机里是「青 / 深蓝 / 墨绿」，v05 全是「灰绿」（S 0.03–0.07）——这是\"看起来不对\"的第一原因，比明度更根本", font=fS, fill=(154, 172, 174))

x0 = PAD + 250
col_w = (W - x0 - PAD) // 4
for i, h in enumerate(HEAD):
    d.text((x0 + i * col_w, 118), h, font=fS, fill=(140, 158, 160))

for r, (name, note, real, accent, mapped, cur, delta) in enumerate(ROWS):
    y = TOP + r * ROW_H
    if r % 2 == 0:
        d.rectangle([PAD - 8, y - 6, W - PAD + 8, y + ROW_H - 14], fill=(22, 27, 31))
    d.text((PAD, y + 6), name, font=fR, fill=(232, 236, 228))
    d.text((PAD, y + 36), note, font=fS, fill=(132, 150, 152))
    d.text((PAD, y + 58), "→ " + delta, font=fS, fill=(186, 176, 140))
    for i, hexv in enumerate((real, accent, mapped, cur)):
        sx = x0 + i * col_w
        sw, sh = 150, 62
        rgb = tuple(int(hexv.lstrip("#")[k:k + 2], 16) for k in (0, 2, 4))
        d.rectangle([sx, y, sx + sw, y + sh], fill=rgb, outline=(70, 78, 80))
        tc = (20, 20, 20) if sum(rgb) > 380 else (235, 235, 230)
        d.text((sx + 8, y + sh - 24), hexv, font=fM, fill=tc)
d.text((PAD, H - 52), "换算规则：L' = 0.34 + 0.55·L，S 保持（≤0.85）；墙顶 L'+0.12，地面 L'−0.06。必须「保形换色」——整间平涂会让 S1 从 54.1% 掉到 40.3%，保形换色 48.7%。", font=fS, fill=(206, 214, 206))
c.save("planning/art/SPACE_BASE_PALETTE_VS_REAL_20261103.png")
print("PALETTE_SHEET_OK", c.size)
