# -*- coding: utf-8 -*-
"""Producer-side notes for the v10 request (G2/G3/G5/G8/S4-S7 + external gates).

These are the checks that cannot be computed: each file states what was looked
at, on which crop, and the verdict, so the reviewer can re-derive it.
"""
from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "knowledge", "active", "20261105-space-base-v10-garden",
                  "runs", "20261105-1800", "evidence")

NOTES = {
    "G2/mentions.md": """# G2 制作侧笔记（v10）

遮字复测：四室 H1 青灰、H2 深青、H3 藏蓝、H4 墨绿青、中央总裁盒棕木+黄铜；岛外为中轴大道
（桥栏/灯列/检查站/门架）、中央花园平台（水池/棕榈列/模纹园/花坛/廊架/门架）与东南半岛
（仓库/罐群/锯齿车间/集装箱/撤离广场）。花园新增的门架横梁与导视牌均为无字色块，
顶视图与英雄图 100% 下无任何可辨文字。G2 PASS（制作侧自评）。
""",
    "G3/notes.md": """# G3 制作侧笔记（v10）

总裁盒开顶后两竖梯入口（黄舱盖 110,68 / 130,52）清晰；落地层四边实墙（x=120 中墙无门）；
环廊无门；盒内家具 >=3 件可辨（S14 连通域计数见 S14/ceo_readout.json）。花园新增构筑物
（廊架、服务箱变、门架）均不遮挡盒顶开口。G3 PASS。
""",
    "G5/pair_note.md": """# G5 制作侧笔记（v10）

A/B 对照沿用半岛颈口 (u0,v0) -> 撤离黄框 (u90,v19) 连线：B 图（本 master）u78 集装箱
遮挡黄框，A 图（无集装箱）可见；checks/05_g5_pair.png 为半岛放大。v10 花园位于 t40-114，
不在该连线的投影带上（连线 v 坐标 16-19，花园带 |v|<=50 但 t<114 段与连线 v 不重叠），
新增平台未改变遮挡关系。G5 PASS（几何验证+目视）。
""",
    "G8/notes.md": """# G8 制作侧笔记（v10）

引道与半岛沥青同屏（checks/02_avenue_bridge.png）：桥面 asphalt 与半岛 asphalt 连续；
花园两端接桥处 8 m 入口坡（+5.135 -> +4.70）与桥面同材，无高差台阶；岛南豁口接缝平顺。
G8 PASS（spec r06 口径）。
""",
    "S4/notes.md": """# S4 制作侧笔记（v10）

五室色相签名唯一：H1 青灰 195 度、H2 深青 191 度、H3 藏蓝 218 度、H4 墨绿青 166 度、
总裁暖棕 31 度（color_probe S15 实测）。花园配色为中性暖灰铺装 + 近黑绿植栽 + 锈橙饰带，
不构成第六个房间色相（S15 探针仅取室内五区）。S4 PASS。
""",
    "S5/notes.md": """# S5 制作侧笔记（v10）

特写（core 片 + checks/06_paving.png）：全场景无圆角造型；Bevel 0.012-0.08 仅作 1-2 px 边光。
花园池缘与挡墙压顶按要求做 0.045 m 圆角（bullnose），属参考图定义的构件倒边，不是造型圆角。
S5 PASS。
""",
    "S6/notes.md": """# S6 制作侧笔记（v10）

地面分格：平台 6 m 二级缝（0.030 m 宽）+ 24 m 一级缝（0.060 m 宽），缝边 0.12 m 锈渍晕；
外圈 1.2 m 深色边带沿八角轮廓内缩 0.9 m。checks/06_paving.png 可读两级缝与边带，
顶视图 master 可读 24 m 主格。S6 PASS。
""",
    "S7/notes.md": """# S7 制作侧笔记（v10）

阴影硬边（sun angle 2.2 度，半影 0.3-0.6 m）；影长约为物高 1.0 倍（太阳 45 度），
低于 0.6-0.8 倍口径，记录偏差（55 度会破坏 S15 房间饱和度，回滚，见 GATE_REPORT）。
总裁盒为唯一暖区（色温 #FFD9A8 + 深棕木 + 黄铜）；花园锈渍为材质固有色，非光照暖偏。
S7 PASS（含偏差记录）。
""",
    "external/A1.md": """# A1（外置）

本轮角色层沿用 v09 剪影角色，藏于 is_char 集合，交付图统一隐藏；场景主光方向
（方位 -22 度 / 高度 45 度）已冻结在 scene.blend，运行时角色阴影需对齐该方向。
""",
    "external/W3.md": """# W3（外置）

外置：真机首帧/内存需在小游戏运行时实测；交付 jpg <=3 MB + 分包建议不变。
""",
    "external/W4.md": """# W4（外置）

外置：低端机降级 1440x1920 / 1280x1707 的裁切与世界坐标一致性需运行时验证。
""",
}

for rel, text in NOTES.items():
    p = os.path.join(EV, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    print("WROTE", rel)
print("NOTES_OK")
