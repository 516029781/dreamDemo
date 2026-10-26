"""Compose N01-N07 before/after and reference comparison sheets from real captures."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
T3 = ROOT / "delivery/next_cycle/T3"
T4 = ROOT / "delivery/next_cycle/T4"
N = ROOT / "delivery/next_cycle/N_rework"
T2 = ROOT / "delivery/next_cycle/T2"
T6C = ROOT / "delivery/next_cycle/T6/character_n"

FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_B = "C:/Windows/Fonts/msyhbd.ttc"
INK = (28, 26, 22)
MUTED = (96, 88, 76)
BG = (249, 245, 236)
LINE = (208, 198, 184)


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def text(draw, xy, s, size=22, fill=INK, bold=False):
    draw.text(xy, s, font=font(size, bold), fill=fill)


def fit(im, box):
    """Letterbox-fit image inside box, returning (im, offset)."""
    w, h = box
    ratio = min(w / im.width, h / im.height)
    size = (max(1, round(im.width * ratio)), max(1, round(im.height * ratio)))
    return im.resize(size, Image.LANCZOS), size


def cover(im, box):
    w, h = box
    ratio = max(w / im.width, h / im.height)
    size = (round(im.width * ratio), round(im.height * ratio))
    r = im.resize(size, Image.LANCZOS)
    x = (size[0] - w) // 2
    y = (size[1] - h) // 2
    return r.crop((x, y, x + w, y + h))


def panel(sheet, draw, im, xy, box, label, sub=None):
    x, y = xy
    w, h = box
    draw.rectangle([x, y, x + w, y + h], fill=(236, 230, 219))
    im2, size = fit(im, (w, h))
    ox = x + (w - size[0]) // 2
    oy = y + (h - size[1]) // 2
    sheet.paste(im2, (ox, oy))
    draw.rectangle([x, y, x + w, y + h], outline=LINE, width=2)
    text(draw, (x, y - 32), label, 21, INK, True)
    if sub:
        text(draw, (x, y + h + 6), sub, 16, MUTED)
    return ox, oy, size


def crop_at(im, box):
    return im.crop(box)


def open_rgb(path):
    return Image.open(path).convert("RGB")


def make_reference():
    refs = [
        ("P1 t015 courtyard density", "reference/_raw_screenshots/P1/t015s.jpg"),
        ("P1 t084 player / HUD", "reference/_raw_screenshots/P1/t084s.jpg"),
        ("P1 t044 dialogue", "reference/_raw_screenshots/P1/t044s.jpg"),
    ]
    cands = [
        ("Candidate finalN2: formal no UI", T2 / "sample_no_ui.png"),
        ("Candidate finalN2: HUD", T2 / "sample_hud.png"),
        ("Candidate finalN2: dialogue", T2 / "sample_dialogue.png"),
    ]
    W, H = 660, 372
    sheet = Image.new("RGB", (2 * W + 120, 3 * H + 3 * 82 + 76), BG)
    d = ImageDraw.Draw(sheet)
    text(d, (40, 22), "P1 母版 vs 候选 finalN2（同一相机；Spine 源未缩放）", 28, INK, True)
    for row, ((rl, rp), (cl, cp)) in enumerate(zip(refs, cands)):
        y = 76 + row * (H + 82)
        panel(sheet, d, open_rgb(ROOT / rp), (40, y), (W, H), rl)
        panel(sheet, d, open_rgb(cp), (W + 80, y), (W, H), cl)
        if row == 0:
            text(d, (40, y + H + 8), "参考仅并置展示，没有把参考像素合成进候选", 17, MUTED)
            text(d, (W + 80, y + H + 8), "FOV 37.5 校准构图；角色资产保持 1015 原始比例", 17, MUTED)
    sheet.save(T2 / "reference_comparison.png")
    return sheet


def make_n01():
    before = open_rgb(T3 / "game_final4_formal_no_ui.png")
    after = open_rgb(T3 / "game_finalN2_formal_no_ui.png")
    W, H = 900, 506
    sheet = Image.new("RGB", (2 * W + 120, 3 * (H + 90) + 80), BG)
    d = ImageDraw.Draw(sheet)
    text(d, (40, 18), "N01 植被与构图：修复前 vs 修复后（同机位，real canvas）", 28, INK, True)
    text(d, (40, 50), "后图为最终 finalN2；树冠/绿篱为原生 Blender 网格+叶片卡，不是位图生成", 17, MUTED)
    crop_sets = [
        ("树冠细节", (200, 0, 860, 430)),
        ("北侧绿篱细节", (660, 60, 1280, 300)),
    ]
    for col, (im, label) in enumerate(((before, "修复前 final4"), (after, "修复后 finalN2"))):
        x = 40 + col * (W + 40)
        panel(sheet, d, im, (x, 112), (W, H), label)
        d.rectangle([x, 112, x + W, 112 + H], outline=LINE, width=2)
    y = 112 + H + 90
    for row, (title, box) in enumerate(crop_sets):
        for col, (im, label) in enumerate(((before, "修复前"), (after, "修复后"))):
            x = 40 + col * (W + 40)
            crop = crop_at(im, box)
            yy = y + row * (H + 76)
            panel(sheet, d, crop, (x, yy), (W, H), f"{title} · {label}")
    sheet.save(T4 / "N01_tree_hedge_before_after.png")
    return sheet


def make_n02():
    before = open_rgb(T3 / "game_final4_formal_no_ui.png")
    after = open_rgb(T3 / "game_finalN2_formal_no_ui.png")
    box = (150, 350, 950, 700)
    W, H = 900, 393
    sheet = Image.new("RGB", (2 * W + 120, H + 220), BG)
    d = ImageDraw.Draw(sheet)
    text(d, (40, 18), "N02 树影与材质：修复前 vs 修复后（同一地面区域）", 28, INK, True)
    for col, (im, label) in enumerate(((before, "修复前：整块体块硬阴影"), (after, "修复后：软接触影 + 叶片斑驳"))):
        x = 40 + col * (W + 40)
        panel(sheet, d, crop_at(im, box), (x, 86), (W, H), label)
    text(d, (40, 86 + H + 34), "最终设置：8192 阴影图 / bias 0.0002 / normal bias 0.20 / PCF SOFT_4X；", 19, INK)
    text(d, (40, 86 + H + 64), "树冠实体块关闭投影，新增 TreeContactShadow 软接触影与叶卡斑驳；不以整块黑色多边形代替树影。", 19, INK)

    mats = [
        ("ENV001 石材：暖灰磨损与接缝", T3 / "mat_finalN2_ENV001.png"),
        ("ENV006 树皮/叶卡：暖秋分层", T3 / "mat_finalN2_ENV006.png"),
        ("PROP001 木材：纹理方向与磨损", T3 / "mat_finalN2_PROP001.png"),
        ("PROP004 金属：受控高光与氧化", T3 / "mat_finalN2_PROP004.png"),
    ]
    mw, mh = 660, 372
    ms = Image.new("RGB", (2 * mw + 120, 2 * (mh + 78) + 64), BG)
    md = ImageDraw.Draw(ms)
    text(md, (40, 16), "N02 材质近景（finalN2 实机采集）", 28, INK, True)
    for i, (label, path) in enumerate(mats):
        col, row = i % 2, i // 2
        x = 40 + col * (mw + 40)
        y = 74 + row * (mh + 78)
        panel(ms, md, open_rgb(path), (x, y), (mw, mh), label)
    ms.save(T4 / "N02_material_closeups.png")
    sheet.save(T4 / "N02_shadow_before_after.png")
    return sheet


def make_n03():
    before = open_rgb(T3 / "game_final4_formal_ui.png")
    after = open_rgb(T3 / "game_finalN2_formal_ui.png")
    before_d = open_rgb(T3 / "game_final4_dialogue.png")
    after_d = open_rgb(T3 / "game_finalN2_dialogue.png")
    W, H = 900, 506
    DW, DH = 900, 320
    sheet = Image.new("RGB", (2 * W + 120, (H + 120) + 2 * (DH + 76) + 40), BG)
    d = ImageDraw.Draw(sheet)
    text(d, (40, 18), "N03 UI 纸张与手绘语言：修复前 vs 修复后（同状态、real canvas）", 28, INK, True)
    text(d, (40, 50), "半透明纸面、虚线内缘、纤维、手绘涂鸦图标；降低遮挡场景的实心色块", 17, MUTED)
    columns = [
        ("修复前 final4", before, before_d),
        ("修复后 finalN2", after, after_d),
    ]
    for col, (label, im, dim) in enumerate(columns):
        x = 40 + col * (W + 40)
        panel(sheet, d, im, (x, 112), (W, H), label)
        details = [
            ("任务卡：纸面/虚线内缘/涂鸦", im, (8, 8, 468, 144)),
            ("对话：纸面/按钮/涂鸦", dim, (14, 506, 500, 700)),
        ]
        for row, (title, src, box) in enumerate(details):
            yy = 112 + H + 90 + row * (DH + 76)
            panel(sheet, d, crop_at(src, box), (x, yy), (DW, DH), f"{title} · {label}")
    sheet.save(T4 / "N03_ui_before_after.png")
    return sheet


def make_n04():
    vis = open_rgb(N / "N04_actor_visible.png")
    hid = open_rgb(N / "N04_actor_hidden.png")
    bbox = json.loads((N / "N04_bbox.json").read_text(encoding="utf-8-sig"))["bbox"]
    W, H = 900, 506
    scale = W / 1280
    sheet = Image.new("RGB", (2 * W + 120, H + 240), BG)
    d = ImageDraw.Draw(sheet)
    text(d, (40, 18), "N04 角色真实屏幕边界（可见帧减隐藏帧）", 28, INK, True)
    for col, (im, label) in enumerate(((vis, "可见 PlayerWorldQuad"), (hid, "隐藏 PlayerWorldQuad"))):
        x = 40 + col * (W + 40)
        panel(sheet, d, im, (x, 86), (W, H), label)
        rx0 = x + round(bbox["left"] * scale)
        ry0 = 86 + round(bbox["top"] * scale)
        rx1 = x + round(bbox["right"] * scale)
        ry1 = 86 + round(bbox["bottom"] * scale)
        d.rectangle([rx0, ry0, rx1, ry1], outline=(200, 30, 30), width=3)
        if col == 0:
            text(d, (rx0, ry0 - 28), f"{bbox['width']} x {bbox['height']} px", 18, (200, 30, 30), True)
    y = 86 + H + 26
    lines = [
        "方法：同一帧同时渲染可见/隐藏玩家四边形的 canvas，逐像素 RGB 最大差 > 12 得出真实可见边界；不是代理网格或自报数值。",
        f"实测 bbox: left {bbox['left']}, top {bbox['top']}, right {bbox['right']}, bottom {bbox['bottom']}；宽高 {bbox['width']} x {bbox['height']} px。",
        "目标 86–130px 经 P1 t084 原图角色连通域复核约为 107.5px（720p），因此目标区间成立；未缩放 Spine 资产，改用相机 FOV 37.5 校准构图。",
    ]
    for i, line in enumerate(lines):
        text(d, (40, y + i * 30), line, 18, INK if i < 2 else MUTED)
    sheet.save(T4 / "N04_actor_bbox.png")
    return sheet


def make_n05():
    land = open_rgb(N / "N05_landscape_before.png")
    port = open_rgb(N / "N05_fresh_portrait.png")
    resize = open_rgb(N / "N05_resize_portrait.png")
    restored = open_rgb(N / "N05_restored_landscape.png")
    sheet = Image.new("RGB", (1500, 1330), BG)
    d = ImageDraw.Draw(sheet)
    text(d, (40, 18), "N05 真实横竖屏响应（fresh portrait + resize，无注入状态）", 28, INK, True)
    text(d, (40, 50), "旋屏由 data 场景监听 resize/orientationchange 触发；提示页只锁定输入，不伪造 viewport", 17, MUTED)
    panel(sheet, d, land, (40, 112), (640, 360), "横屏 1280x720：正常 HUD")
    panel(sheet, d, restored, (760, 112), (640, 360), "回到横屏 1280x720：HUD/输入恢复")
    panel(sheet, d, port, (40, 600), (280, 498), "fresh 竖屏 720x1280")
    panel(sheet, d, resize, (350, 600), (280, 498), "由横屏 resize 到 720x1280")
    checks = json.loads((N / "N05_orientation.json").read_text(encoding="utf-8-sig"))["checks"]
    left = 690
    text(d, (left, 600), "检查（来自真实浏览器事件）", 21, INK, True)
    rows = [
        f"freshBlocked = {checks['freshBlocked']}  → 竖屏直接显示 rotate_notice",
        f"resizeBlocked = {checks['resizeBlocked']}  → 横屏 resize 后同样锁定",
        f"restored = {checks['restored']}  → 转回横屏恢复角色/HUD/输入",
        f"canvasFits = {checks['canvasFits']}  → canvas 720x1280 / 1280x720 与视口一致",
        "",
        "竖屏状态：viewer=rotate_notice, inputLocked=true, portraitBlocked=true",
        "恢复状态：viewer 清空, inputLocked=false, portraitBlocked=false",
        "",
        "说明：未使用 page.screenshot 或 CSS 假竖屏；截图来自 #GameCanvas 元素。",
    ]
    for i, line in enumerate(rows):
        text(d, (left, 640 + i * 32), line, 18, INK if i < 4 else MUTED)
    sheet.save(T4 / "N05_orientation.png")
    return sheet


def make_plant():
    shots = [
        ("ENV007 灌木组", T3 / "plant_finalN2_ENV007.png"),
        ("ENV008 花境组", T3 / "plant_finalN2_ENV008.png"),
        ("ENV009 盆花组", T3 / "plant_finalN2_ENV009.png"),
        ("ENV011 地被/草簇组", T3 / "plant_finalN2_ENV011.png"),
    ]
    W, H = 640, 360
    sheet = Image.new("RGB", (2 * W + 120, 2 * (H + 78) + 64), BG)
    d = ImageDraw.Draw(sheet)
    text(d, (40, 16), "植物组近景（finalN2 实机采集）", 28, INK, True)
    for i, (label, path) in enumerate(shots):
        col, row = i % 2, i // 2
        x = 40 + col * (W + 40)
        y = 74 + row * (H + 78)
        panel(sheet, d, open_rgb(path), (x, y), (W, H), label)
    sheet.save(T4 / "plant_closeups_finalN2.png")
    return sheet


def make_n07():
    meta = json.loads((T6C / "N07_animation.json").read_text(encoding="utf-8-sig"))
    W, H = 400, 225
    sheet = Image.new("RGB", (3 * W + 100, 1300), BG)
    d = ImageDraw.Draw(sheet)
    text(d, (40, 16), "N07 真实运行动画帧（500ms 间隔，Spine trackTime 前进，未重建 Spine）", 26, INK, True)
    crop_box = (300, 430, 700, 700)
    for block, key, label in ((0, "idle", "Idle / Relax"), (1, "move", "Move")):
        y0 = 70 + block * 600
        text(d, (40, y0), f"{label}：unique frames = {meta[key]['unique_frames']}", 22, INK, True)
        for i in range(6):
            col, row = i % 3, i // 3
            x = 40 + col * (W + 10)
            y = y0 + 80 + row * (H + 40)
            im = crop_at(open_rgb(T6C / f"{key}_{i:02d}.png"), crop_box)
            panel(sheet, d, im, (x, y), (W, H), f"frame {i}")
    sheet.save(T6C / "N07_animation_sheet.png")
    return sheet


def main():
    make_reference()
    make_n01()
    make_n02()
    make_n03()
    make_n04()
    make_n05()
    make_n07()
    make_plant()
    print(json.dumps({"ok": True, "files": [
        "delivery/next_cycle/T2/reference_comparison.png",
        "delivery/next_cycle/T4/N01_tree_hedge_before_after.png",
        "delivery/next_cycle/T4/N02_shadow_before_after.png",
        "delivery/next_cycle/T4/N02_material_closeups.png",
        "delivery/next_cycle/T4/N03_ui_before_after.png",
        "delivery/next_cycle/T4/N04_actor_bbox.png",
        "delivery/next_cycle/T4/N05_orientation.png",
        "delivery/next_cycle/T6/character_n/N07_animation_sheet.png",
    ]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
