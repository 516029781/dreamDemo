"""Build the human review sheet for v04 (one image: master + checklist + evidence strip)."""
from __future__ import annotations

import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "art", "static_map", "space_base_minigame", "v04")
CHK = os.path.join(V, "checks")
REN = os.path.join(V, "renders")

FB = "C:/Windows/Fonts/msyhbd.ttc"
FR = "C:/Windows/Fonts/msyh.ttc"
BG = (18, 22, 26)
INK = (236, 240, 234)
MUT = (150, 168, 170)
ACC = (232, 194, 90)
OK = (120, 200, 140)
WARN = (232, 150, 80)

ITEMS = [
    ("G2", "区域辨识", "master 全图",
     "遮住所有文字，仍能说出：离心 / 浮力 / 蓝室 / 黑室 / 总裁 / 花园 / 船坞",
     "自检：靠圆墙、深池、坑、绿墙、奶油盒可区分", "pass?"),
    ("G3", "总裁可达", "check_core",
     "两部竖梯入口读得出；x=120 落地层是实墙；环廊与屋顶导轨摸不到门",
     "自检：两梯在 H2 (112,68) / H4 (130,52)，实墙无洞", "pass?"),
    ("G5", "撤离遮挡", "check_g5_pair",
     "A 图（有箱列）看不见黄框；B 图（去箱）黄框出现——只差 5 个集装箱",
     "自检：A 无黄、B 远端露黄，机位与光照完全一致", "pass?"),
    ("G8", "花园-堤道接缝", "check_garden_causeway",
     "地面材质、分缝在花园与堤道之间连续；无断缝、无突然色差",
     "自检：暖灰→中性灰有一次渐变，接缝在检查站下方", "pass?"),
    ("S4", "五室色相签名", "check_core",
     "离心青 / 浮力蓝 / 蓝室浅灰 / 黑室绿 / 总裁暖奶油，每室只有一种",
     "自检：压顶色带 + 地面 + 主锚三处一致", "pass?"),
    ("S5", "无倒角", "check_dock",
     "混凝土与金属为直角硬边，没有圆角；管线本身是圆管不算",
     "自检：全部 add_box 直角，墙口无倒角", "pass?"),
    ("S6", "分缝尺度", "check_core",
     "目标：墙 1.2×2.4、地 3×3。**当前只做了地面分区，墙面分缝未做**",
     "裁决：7 px/m 下竖缝 <1 px，建议降级为“地面分区 + 墙脚带”", "decide"),
    ("S7", "阴影与暖区", "master 全图",
     "阴影方向一致、长度 0.6–0.8 倍；总裁盒是全图唯一暖色区",
     "自检：太阳 62°，CEO 暖自发光 0.35，其余冷灰", "pass?"),
    ("S1", "浅色占比口径", "GATE_REPORT",
     "全帧 {full}%（水面 {water}%）；陆地相对 {land}% ≥45%——请确认改口径",
     "裁决：四面环水后全帧 45% 不可能达成，建议按陆地口径", "decide"),
    ("A1/W3/W4", "外部项", "—",
     "角色阴影 / 真机首帧 / 低端机选图：本轮无角色层、未上真机",
     "结论：不适用，不计入本轮", "n/a"),
]


def fit(im, w, h):
    im = im.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    return im


def main():
    master = Image.open(os.path.join(REN, "space_base_v04_master.png")).convert("RGB")
    gate = json.load(open(os.path.join(V, "GATE_REPORT.json"), encoding="utf-8"))
    stats = gate["S1_S2_S3"]
    land = stats["S1_light_ratio"] / (1 - stats["water_ratio"])

    W = 1960
    left_w = 860
    pad = 28
    head = 150
    body_h = 1330
    strip_h = 330
    H = head + body_h + strip_h + pad * 3

    canvas = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(canvas)
    f_title = ImageFont.truetype(FB, 34)
    f_sub = ImageFont.truetype(FR, 16)
    f_item = ImageFont.truetype(FB, 17)
    f_std = ImageFont.truetype(FR, 14)
    f_small = ImageFont.truetype(FR, 13)
    f_num = ImageFont.truetype(FB, 15)

    dr.text((pad, 22), "space_base_minigame v04 · 人工审核单", font=f_title, fill=INK)
    dr.text((pad, 66),
            "机械项已过：G1 尺寸 / G4 探针 / W1 文件 / S2 绿 2.6%% / S3 橙 0.05%%　｜　"
            f"S1 全帧 {stats['S1_light_ratio'] * 100:.1f}%、陆地相对 {land * 100:.1f}%",
            font=f_sub, fill=MUT)
    dr.text((pad, 92), "下面 10 项脚本判断不了，需要人眼看图；每项都写了看哪张、什么算过。",
            font=f_sub, fill=MUT)

    # master on the left
    mh = body_h
    mw = left_w
    mi = fit(master, mw, mh)
    mx = pad + (mw - mi.width) // 2
    my = head + (mh - mi.height) // 2
    canvas.paste(mi, (mx, my))
    dr.rectangle([mx - 1, my - 1, mx + mi.width, my + mi.height], outline=(60, 70, 74))
    dr.text((mx, my + mi.height + 6), "master 1680×2478（7 px/m，北朝上）", font=f_small, fill=MUT)

    # checklist on the right
    x0 = pad + left_w + pad
    col_w = W - x0 - pad
    y = head
    items = []
    for cid, name, where, std, note, verdict in ITEMS:
        items.append((cid, name, where,
                      std.format(full=f"{stats['S1_light_ratio'] * 100:.1f}",
                                 water=f"{stats['water_ratio'] * 100:.1f}",
                                 land=f"{land * 100:.1f}"),
                      note, verdict))
    for i, (cid, name, where, std, note, verdict) in enumerate(items, 1):
        ih = 128
        dr.rounded_rectangle([x0, y, x0 + col_w, y + ih - 10], 8, fill=(26, 31, 36),
                             outline=(44, 52, 58))
        dr.text((x0 + 12, y + 10), "%02d" % i, font=f_num, fill=ACC)
        dr.text((x0 + 44, y + 8), "%s · %s" % (cid, name), font=f_item, fill=INK)
        tag = {"pass?": "待判", "decide": "待裁决", "n/a": "不适用"}[verdict]
        col = {"pass?": OK, "decide": WARN, "n/a": MUT}[verdict]
        tw = dr.textlength(tag, font=f_small)
        dr.rounded_rectangle([x0 + col_w - tw - 20, y + 10, x0 + col_w - 8, y + 30], 6,
                             outline=col)
        dr.text((x0 + col_w - tw - 14, y + 12), tag, font=f_small, fill=col)
        dr.text((x0 + 44, y + 34), "看：" + where, font=f_small, fill=MUT)
        # wrap std text
        words = std
        line = ""
        ly = y + 55
        for ch in words:
            if dr.textlength(line + ch, font=f_std) > col_w - 60:
                dr.text((x0 + 44, ly), line, font=f_std, fill=(214, 220, 214))
                line = ""
                ly += 20
            line += ch
        if line:
            dr.text((x0 + 44, ly), line, font=f_std, fill=(214, 220, 214))
        ly += 20
        if ly < y + ih - 18:
            dr.text((x0 + 44, ly), note, font=f_small, fill=(120, 140, 140))
        y += ih

    # evidence strip
    thumbs = [("check_core", "核心区 / 四室 + 总裁", 1),
              ("check_garden_causeway", "花园 → 堤道接缝", 1),
              ("check_dock", "干船坞 / 坞底 + 撤离", 1),
              ("check_g5_pair", "G5：有箱列 vs 去箱列", 2),
              ("check_north", "北环路 / 临水矮墙", 1)]
    sy = head + body_h + pad
    units = sum(t[2] for t in thumbs)
    unit_w = (W - pad * (units + 1)) / units
    cx = pad
    for name, label, weight in thumbs:
        p = os.path.join(CHK, name + ".png")
        if not os.path.exists(p):
            continue
        slot_w = int(unit_w * weight + pad * (weight - 1))
        im = fit(Image.open(p).convert("RGB"), slot_w, strip_h - 46)
        canvas.paste(im, (cx, sy))
        dr.rectangle([cx - 1, sy - 1, cx + im.width, sy + im.height], outline=(60, 70, 74))
        dr.text((cx, sy + im.height + 6), label, font=f_small, fill=MUT)
        cx += slot_w + pad

    out = os.path.join(V, "REVIEW_SHEET.png")
    canvas.save(out)
    print("REVIEW_SHEET", canvas.size, out)


if __name__ == "__main__":
    main()
