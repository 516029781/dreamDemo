#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate the P0 calibration instrument from one source of truth.

The anchors, the evidence matrix and the blank scoring sheet all come from
ANCHORS below, so a change to a threshold can never leave two documents
disagreeing. Run from the repository root:

    python planning/execution/P0_CALIBRATION/build_p0.py
"""
import csv
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "planning", "execution", "P0_CALIBRATION")

FRAMES = {
    "F1": ("delivery/next_cycle/n5/T5/q01_formal_no_ui.png", "俯视全景 · 无 UI · 1280×720"),
    "F2": ("delivery/next_cycle/n5/T5/q01_formal_ui.png", "同机位 · 有 UI · 1280×720"),
    "F3": ("delivery/next_cycle/n5/T5/q01_dialogue.png", "对白中景 · 1280×720"),
    "F4": ("delivery/next_cycle/n5/T5/q03_behind.png", "树后低角 · 1280×720"),
    "F5": ("delivery/next_cycle/n5/T5/q05_board_full.png", "告示板近景 · 满 · 1280×720"),
    "F7": ("delivery/next_cycle/n5/T5/q05_board_empty.png", "告示板近景 · 空 · 1280×720"),
    "F6": ("delivery/next_cycle/n5/T5/q09_portrait_720x1280.png", "竖屏安全区 · 720×1280"),
    # v4: the three independent poses required by contract v2.1 section 3.1.
    "M1": ("delivery/next_cycle/n5/T3/poses/pose_m1_front_no_ui.png", "独立机位1 正面全景 · 无 UI"),
    "M2": ("delivery/next_cycle/n5/T3/poses/pose_m2_side_no_ui.png", "独立机位2 侧向45° · 无 UI"),
    "M3": ("delivery/next_cycle/n5/T3/poses/pose_m3_southeast_no_ui.png", "独立机位3 东南中位 · 无 UI"),
    "M2U": ("delivery/next_cycle/n5/T3/poses/pose_m2_side_ui.png", "同 M2 机位 · 有 UI"),
}

# Measured once on F1, recorded so an anchor can cite a number instead of an opinion.
MEASURED = {
    "character_body_px": 123,
    "character_body_pct": 17.1,
    "character_full_px": 151,
    "character_full_pct": 21.0,
    "q01_reported_px": 90.9,
    "paving_share_lower": 49.9,
    "gray_levels": 11,
    "mean_luma": 126.2,
    "brightest10_y": 34.9,
}

A = []


def add(card, dim, weight, core, frames, l3, l4, metric=""):
    A.append({"card": card, "id": dim, "weight": weight, "core": core,
              "frames": frames, "l3": l3, "l4": l4, "metric": metric})


# ---------------------------------------------------------------- ENV
add("ENV", "composition_scale", 20, True, [("F1", "全图"), ("F3", "全图"), ("F4", "全图")],
    "三个机位都能读出前中后，角色躯干占屏高 17.1%（123 px）比例本身不小，但俯视机位铺地占下半屏 49.9% 且同明度，视线被拉平、没有明确落点；任一机位主体不被裁切。",
    "至少两个机位能把视线收束到角色或主树，铺地退为背景；或在铺地上用明度梯度、铺法分区建立落点；换机位后收束关系仍成立。",
    "角色躯干 123 px / 17.1%（v4 修正，旧值 90.9 px 作废）；下半屏铺地色 49.9%")

add("ENV", "geometry_craft", 20, True, [("F1", "中景 y=200–450"), ("F5", "全图")],
    "可读物件只有树、环坛、长椅、路灯四类，彼此独立摆放；环坛是正圆、长椅是直板，没有连接件与倒角。",
    "物件成组构成角落（花坛＋长椅＋灯），近景物件有厚度、倒角、连接件；缩到 1280×720 仍能看出构造而非剪影。",
    "F1 中景可读物件 4 类")

add("ENV", "material_separation", 20, True, [("F1", "铺地 y=380–720"), ("F5", "砖面近景")],
    "石与木能区分，但砖缝等宽、磨损是均匀噪点，铺地只有一种铺法；换机位后材质差异减弱。",
    "主路、广场、边缘三种铺法可辨；砖缝不等宽，有苔、磨边与局部破损；石、木、金属三种粗糙度在同屏可区分，且不依赖换色。",
    "砖网格 17×9，缝宽恒定")

add("ENV", "lighting_contact", 20, True, [("F1", "树冠下 y=300–380；长椅脚 y=560–590"), ("F4", "树干与地面")],
    "有明确主光方向，但叶片基本不投影，树冠只靠一张贴花；长椅与花坛脚下是柔光斑，没有接触阴影。",
    "树冠在铺地投出边界可辨的长投影，长椅、花坛、路灯各有接触阴影；转灰度后仍保留不少于 9 档有效明度，暗部不死黑。",
    "灰度有效档 11 档；平均明度 126.2")

add("ENV", "vegetation_depth", 10, False, [("F1", "树冠 y=40–300"), ("F4", "绿篱带")],
    "树冠下部光秃成枝裙，绿篱读作单层团块，冠内没有空隙。",
    "冠内有空隙与明暗交替，绿篱分出前中后三层，且换机位后层次不塌。",
    "")

add("ENV", "play_readability", 10, False, [("F1", "角色周围 x=300–700"), ("F2", "角色与 UI 关系")],
    "角色可辨，但周围铺地明度接近，NPC 与主角明度差小；UI 出现后角色注意力被分走。",
    "角色是画面第一落点，角色所在区域对比度最高；路径净宽可读；UI 出现时仍不压角色主体。",
    "最亮 10% 像素重心在屏高 34.9%，即背景带而非角色")

# ---------------------------------------------------------------- CHAR
add("CHAR", "silhouette_proportion", 20, True, [("M1", "角色全身"), ("M2", "角色全身"), ("M3", "角色全身")],
    "角色外轮廓在 M1 可读，但 M3（188 px）下武器与裙摆粘连，脚部没有独立剪影，底缘是贯穿全身的平直硬切。",
    "三个独立机位下外轮廓都干净，武器、发饰、裙摆、靴子各自分离；底缘有脚形而不是硬切，缩到 90 px 仍能分辨附件。",
    "")

add("CHAR", "line_quality", 15, True, [("M1", "角色外轮廓"), ("M2", "角色外轮廓"), ("M3", "角色全身")],
    "外轮廓清楚，内线密度不均；M3 放大后局部断线，衣褶有几处重复同一笔。",
    "三个机位下外轮廓与内线同一笔触，不断线，放大不露重复；缩到 90 px 仍闭合。",
    "")

add("CHAR", "cel_color_light", 15, True, [("M1", "角色色块"), ("M2", "角色色块"), ("M3", "角色色块")],
    "色块正确，暗部是单纯压暗，没有环境色；三个机位明暗关系一致但没有随光向变化。",
    "黑、白、灰三段清楚，暗部带冷环境色并与场景主光同向；M3 侧向机位下仍能读出体积。",
    "")

add("CHAR", "identity_consistency", 25, True, [("M1", "角色全身"), ("M2", "角色全身"), ("M3", "角色全身")],
    "可辨认，但三个独立机位里至少一个不完整或细节含糊，需要靠单帧印象补齐。",
    "与锁定源同配件、同配色、同比例；M1/M2/M3 三个独立机位都完整可辨，不因场景重绘。按 R3，不要求看到侧面或背面。",
    "")

add("CHAR", "motion_contact", 15, True, [("F1", "角色脚下"), ("M3", "角色脚下")],
    "脚底与地面之间没有接触阴影，移动帧存在轻微滑动；M3 侧向机位下角色像是浮在铺地上。",
    "多帧下脚底贴合地面，接地阴影随动作移动，停下时不留残影；三个机位都能读出脚与地面的接触。",
    "M3 角色脚下无可见接触阴影")

add("CHAR", "small_scale_clarity", 10, True, [("F1", "角色 x=380–500, y=470–630")],
    "看 `evidence/CHAR_screen_1to1.png`：90 px 时能读出人形、配色与武器大致位置，但眼睛与靴子轮廓分不开。",
    "看 `evidence/CHAR_screen_1to1.png`：能指出眼睛位置，武器与靴子轮廓各自分离，轮廓内至少 3 个独立色块。",
    "角色高 123 px（v4 修正），1:1 裁图按 90 px 重采样")

# ---------------------------------------------------------------- UI
add("UI", "paper_shape", 20, True, [("F3", "对白面板 y=530–720"), ("F2", "任务卡左上")],
    "纸面板有质感，但边缘规则、厚度均匀，接近圆角矩形。",
    "轻薄半透，边缘不规则且有纤维感，不压住背后的场景，换状态后纸形一致。",
    "")

add("UI", "doodle_icon_family", 20, True, [("F2", "任务卡图标"), ("F3", "翻页与头像图标")],
    "图标来源不统一，线宽与圆角各不相同，部分是实心块。",
    "同一笔触、同一线宽、同一圆角半径，保留轻微不规则；缩到 24 px 仍同族。",
    "")

add("UI", "typography", 20, True, [("F3", "对白文字 y=560–700"), ("F2", "任务卡文字")],
    "只有字号层级，名字与正文同字重，辅助文字偏浅。",
    "名字、正文、辅助三档在字重与明度上都可分，行距稳定，720 下最小字仍可读。",
    "")

add("UI", "layout_air", 15, True, [("F3", "角色与面板之间"), ("F2", "角色周围")],
    "信息挤占角色周围，对白面板压到角色下半身。",
    "角色周围留空，信息轻量分布在四角，中央留给玩法。",
    "")

add("UI", "state_feedback", 15, True, [("F2", "六态对照"), ("F6", "竖屏安全区")],
    "有状态区分，但按下与悬停差异弱，竖屏只弹提示。",
    "默认、悬停、按下、暂停、对白、竖屏六态一致，状态切换有明确视觉回应。",
    "")

add("UI", "palette_restraint", 10, False, [("F2", "全图 UI"), ("F3", "对白面板")],
    "主色克制，但装饰色超过两种，局部出现与场景冲突的色相。",
    "乳白与炭灰为主，只保留一种交互强调色，换状态不新增色相。",
    "")

# ---------------------------------------------------------------- MIX
add("MIX", "visual_language", 25, True, [("F3", "角色与场景同屏"), ("F4", "角色与树同屏")],
    "立绘的线条与细节密度明显高于场景，读起来像高精度贴片放在低模上。",
    "角色与场景共用同一套描边、明度分档与纹理密度，同屏看不出两种画法。",
    "")

add("MIX", "color_light_coherence", 25, True, [("F3", "角色受光面与铺地受光面"), ("F1", "角色与地面")],
    "角色高光方向与场景主光不一致，角色暗部没有环境色，两者像被分别打光。",
    "角色与场景受同一主光支配，受光面朝向一致，角色暗部带场景环境色。",
    "")

add("MIX", "grounding_occlusion", 20, True, [("F1", "角色脚下 y=626–642"), ("F4", "角色与树的前后关系")],
    "角色底缘下 12px 带比同 x 更下方 30px 暗 81/255（85.4 对 166.4），说明阴影存在且是平滑渐变；但阴影是一团模糊椭圆，不随脚形，且角色底缘是贯穿全身的平直硬切，看不到脚。",
    "阴影贴合脚形并随动作移动，底缘由脚或裙摆的自然轮廓取代硬切；树前树后遮挡正确。",
    "脚下带 85.4 / 远处 166.4 / 差 81.0；底缘 y=627 为突变的水平线")

add("MIX", "focus_readability", 15, True, [("F1", "全图明度分布"), ("F2", "有 UI 时")],
    "画面最亮的部分不在角色附近（实测最亮 10% 像素重心在屏高 34.9%，落在背景带），角色不是第一落点。",
    "角色所在区域是画面最亮或对比最高处，UI 出现后仍成立。",
    "最亮 10% 重心 34.9% 屏高")

add("MIX", "world_style_coherence", 15, False, [("F2", "UI 与场景"), ("F5", "道具与场景")],
    "道具、场景、UI 三套视觉语法并存，比例与笔触互不呼应。",
    "道具、场景、UI 共用同一套比例、笔触与明度规则，换场景仍成立。",
    "")

def sync_weights():
    """Weights and core flags come from the contract, never from this file.

    The first draft hard-coded CHAR weights from memory and produced 92.00 where
    the contract says 93.75. Reading rubric.json removes that whole class of bug.
    """
    path = os.path.join(ROOT, "art_review", "rubric.json")
    with io.open(path, encoding="utf-8") as fh:
        rubric = json.load(fh)
    contract = {}
    for card, dims in rubric["cards"].items():
        for d in dims:
            contract[d["id"]] = (card, d["weight"], bool(d.get("core")))
    seen = set()
    for a in A:
        card, weight, core = contract[a["id"]]
        if card != a["card"]:
            raise SystemExit("card mismatch for %s" % a["id"])
        a["weight"], a["core"] = weight, core
        seen.add(a["id"])
    absent = set(contract) - seen
    if absent:
        raise SystemExit("anchors missing dimensions: %s" % ", ".join(sorted(absent)))
    return rubric


MATRIX_COLS = ["F1", "F2", "F3", "F4", "F5", "F6", "M1", "M2", "M3"]
# ● 适用且已有证据   ○ 适用但缺证据   ◐ 有帧但目标被遮挡/不可用   △ 不构成独立视角   — 不适用
APPLY = {
    "ENV": {"F1": "●", "F2": "●", "F3": "●", "F4": "●", "F5": "●", "F6": "△", "M1": "●", "M2": "●", "M3": "●"},
    "CHAR": {"F1": "●", "F2": "●", "F3": "●", "F4": "◐", "F5": "—", "F6": "△", "M1": "●", "M2": "●", "M3": "●"},
    "UI": {"F1": "—", "F2": "●", "F3": "●", "F4": "—", "F5": "—", "F6": "●", "M1": "—", "M2": "●", "M3": "—"},
    "MIX": {"F1": "●", "F2": "●", "F3": "●", "F4": "●", "F5": "●", "F6": "△", "M1": "●", "M2": "●", "M3": "●"},
}


def anchors_md():
    lines = ["# P0 锚点：23 个维度的 3 分与 4 分分界", "",
             "本文件由 `build_p0.py` 生成，是 P0 的唯一评分依据。",
             "打分时只看锚点里指定的帧与区域，不引用其他截图，不参考历史自评分。",
             "",
             "档位定义（验收文件 §3）：3 = 正式机位达到该特征且无关键问题；4 = 在规定多机位与多状态下均精致稳定。",
             "因此 4 分的判据一律包含“换机位仍成立”，单帧做到不算。", "",
             "## 两条通用规则", "",
             "**R1 机位不可用则不得给 4。** 若锚点指定的机位里目标被遮挡超过一半或出画，该机位不计入；"
             "剩余可用机位不足两个时，该维最高 3 分。",
             "**R2 尺寸类判断以 1:1 裁图为据。** 判断“缩到 xx px 是否可辨”，看 `evidence/` 下的 1:1 裁图，"
             "不要在原图上凭印象判断；放大图只用于确认形状，不用于判断可辨性。",
             "**R3 角色是面向相机的 2D 合成体。** 角色由 `PlayerWorldQuad` 承载，每帧执行 `setRotation(mainCamera.rotation)`，"
             "M1/M2/M3 三个机位看到的是同一张贴图，差异只在屏幕尺寸、遮挡和背景对比。"
             "因此 CHAR 的 4 分档检验的是“三个机位都完整、清晰、不被遮”，**不是 3D 多面一致**；不得以“看不到侧面或背面”为由扣分。", "",
             "## 三个独立机位（契约 v2.1 §3.1）", "",
             "| 代号 | 相机位置 | 视线落点 | 角色屏幕高 | 用途 |", "|---|---|---|---:|---|",
             "| M1 | (-2.5, 11.5, -14.6) | (-2.5, 3.5, -3.7) | 125 px | 与正式机位 F1 同机位，作为基准 |",
             "| M2 | (4.88, 6.5, -13.61) | (0, 1.0, -5.2) | 161 px | 侧向 45°，验证换角度后是否仍完整 |",
             "| M3 | (6.2, 4.6, -11.6) | (0, 1.2, -5.2) | 188 px | 东南中位，第三个互不相同的视角 |",
             "", "三个机位的角色屏幕高都远大于 90 px，因此 M 系列只用于判 CHAR 的完整性与一致性，"
             "**不得用于判 `small_scale_clarity`**（该维一律看 1:1 裁图）。`composition_scale` 也只在 Q01 机位（F1）判，"
             "M 系列的角色占比更大，不构成反例。", "",
             "## 已测量基准（F1 俯视全景，1280×720）", "",
             "| 指标 | 值 | 说明 |", "|---|---:|---|",
             "| 角色躯干高（发顶至脚底，不含武器） | 123 px / 17.1% | 逐行扫描角色专属色域 |",
             "| 角色含发饰与武器高 | 151 px / 21.0% | 视觉完整外接高度 |",
             "| Q01 记录值 | 90.9 px / 12.6% | 旧记录，与实测不一致；契约 v2.1 §3.2 已定死口径，本行仅留痕 |",
             "| 下半屏铺地色占比 | 49.9% | |",
             "| 灰度有效档 | 11 | 每档占画面 ≥1% |",
             "| 平均明度 | 126.2 / 255 | |",
             "| 最亮 10% 像素重心 | 屏高 34.9% | 落在背景带，不在角色 |", "",
             "“角色可见高度”的口径已由契约 v2.1 §3.2 定死：**屏幕空间、躯干外接框（发顶至脚底，不含武器与飘带）**。"
             "按此口径 F1 上为 123 px / 17.1%，旧记录的 90.9 px / 12.6% 作废，`composition_scale` 一律按 123 px 判。", ""]
    for card in ["ENV", "CHAR", "UI", "MIX"]:
        lines += ["## %s" % card, ""]
        for a in [x for x in A if x["card"] == card]:
            fr = "；".join("%s（%s）%s" % (f, FRAMES[f][1], r) for f, r in a["frames"])
            lines += ["### %s　权重 %d%s" % (a["id"], a["weight"], "　核心维" if a["core"] else ""), "",
                      "- 看哪里：%s" % fr,
                      "- 3 分：%s" % a["l3"],
                      "- 4 分：%s" % a["l4"]]
            if a["metric"]:
                lines.append("- 实测：%s" % a["metric"])
            lines.append("")
    return "\n".join(lines)


def matrix_md():
    head = "| 维度 | 权重 | " + " | ".join("%s<br>%s" % (c, FRAMES[c][1].split(" · ")[0]) for c in MATRIX_COLS) + " |"
    sep = "|---|---|" + "---|" * len(MATRIX_COLS)
    lines = ["# P0 证据矩阵", "",
             "● 适用且已有证据　○ 适用但缺证据　◐ 有帧但目标被遮挡、不可用于判档　△ 该帧不构成独立视角　— 不适用", "",
             head, sep]
    counts = {"●": 0, "○": 0, "◐": 0, "△": 0}
    for a in A:
        row = [a["id"], str(a["weight"])]
        for c in MATRIX_COLS:
            m = APPLY[a["card"]][c]
            if m in counts:
                counts[m] += 1
            row.append(m)
        lines.append("| " + " | ".join(row) + " |")
    lines += ["", "统计：可用证据 %d 格，缺证据 %d 格，目标被遮挡 %d 格，不构成独立视角 %d 格。" % (
        counts["●"], counts["○"], counts["◐"], counts["△"]), ""]
    lines += ["## 机位清单", "",
              "| 代号 | 文件 | 说明 |", "|---|---|---|",
              "| M1 | pose_m1_front_no_ui.png | 独立机位1，与正式机位同机位，基准 |",
              "| M2 | pose_m2_side_no_ui.png | 独立机位2，侧向 45°，角色 161 px |",
              "| M3 | pose_m3_southeast_no_ui.png | 独立机位3，东南中位，角色 188 px |",
              "| F1 | q01_formal_no_ui.png | 俯视全景，Q01 构图机位（唯一判 composition_scale 的帧） |",
              "| F3 | q01_dialogue.png | 对白中景，角色下半身被面板压住 |",
              "| F4 | q03_behind.png | 树后低角，角色被树冠遮约八成，不可用于判档 |",
              "| F5 | q05_board_full.png | 告示板近景，验证材质与构造 |",
              "", "F2 与 F1 同机位仅差 UI 叠加（缩略图差异 6.14/255）；F6 是同一画面的竖屏裁切加提示层，"
              "两者都不构成独立视角。M1/M2/M3 是契约 v2.1 §3.1 要求的三个独立机位，"
              "由 `delivery/next_cycle/n5/_p0b_poses.js` 在同一构建上拍摄，未改资产、未重建。", ""]
    return "\n".join(lines)


def sheet_csv():
    path = os.path.join(OUT, "scoring_sheet.csv")
    with io.open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["card", "dimension", "weight", "core", "evidence", "score_0_4",
                    "reason_region", "not_4_because"])
        for a in A:
            ev = ";".join(f for f, _ in a["frames"])
            w.writerow([a["card"], a["id"], a["weight"], "Y" if a["core"] else "N", ev,
                        "", "", ""])
    return path


if __name__ == "__main__":
    sync_weights()
    # The instrument must reproduce the published card totals before it is used
    # to judge anyone. If this fails, the anchors or the weights are wrong.
    ref = os.path.join(ROOT, "delivery", "next_cycle", "n5", "T4", "producer_self_review_n5.json")
    with io.open(ref, encoding="utf-8") as fh:
        prod = json.load(fh)
    expect = {"ENV": 77.5, "CHAR": 93.75, "UI": 87.5, "MIX": 80.0}
    for card, want in expect.items():
        dims = {d["id"]: d["score"] for d in prod["cards"][card]["dimensions"]}
        got = sum(a["weight"] * dims[a["id"]] for a in A if a["card"] == card) / 4.0
        if abs(got - want) > 0.01:
            raise SystemExit("weight check failed for %s: %.2f != %.2f" % (card, got, want))
    with io.open(os.path.join(OUT, "ANCHORS.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"frames": FRAMES, "measured": MEASURED, "anchors": A},
                  fh, ensure_ascii=False, indent=1)
    with io.open(os.path.join(OUT, "ANCHORS.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(anchors_md())
    with io.open(os.path.join(OUT, "EVIDENCE_MATRIX.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(matrix_md())
    p = sheet_csv()
    print("anchors", len(A), "| cards", {c: sum(1 for a in A if a["card"] == c) for c in ("ENV", "CHAR", "UI", "MIX")})
    print("wrote", p)
