"""Create candidate_n5 vs n2/P1 comparison sheets."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
N4 = ROOT / "delivery/next_cycle/n5"
N2 = ROOT / "delivery/next_cycle"
P1 = ROOT / "reference/_raw_screenshots/P1"
BG = (246, 242, 233)
INK = (38, 41, 42)
MUTED = (92, 95, 90)
LINE = (180, 174, 160)
FONT = "C:/Windows/Fonts/NotoSansSC-VF.ttf"


def font(size, bold=False):
    try:
        return ImageFont.truetype(FONT, size)
    except Exception:
        return ImageFont.load_default()


def text(d, xy, s, size=18, color=INK, bold=False):
    d.text(xy, s, font=font(size, bold), fill=color)


def panel(sheet, d, im, xy, size, label):
    x, y = xy
    w, h = size
    im = im.convert("RGB")
    scale = min(w / im.width, h / im.height)
    im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    sheet.paste(im, (x + (w - im.width) // 2, y + (h - im.height) // 2))
    d.rectangle([x, y, x + w, y + h], outline=LINE, width=2)
    text(d, (x, y - 28), label, 18, INK, True)


def reference():
    items = [
        ("P1 t084 · fixed full-scene anchor", P1 / "t084s.jpg"),
        ("candidate_n5 · formal no UI", N4 / "T3/game_finalN5h_formal_no_ui.png"),
        ("P1 t084 · fixed full-scene anchor", P1 / "t084s.jpg"),
        ("candidate_n5 · HUD", N4 / "T3/game_finalN5h_formal_ui.png"),
        ("P1 t090 · dialogue UI supplement", P1 / "t090s.jpg"),
        ("candidate_n5 · dialogue", N4 / "T3/game_finalN5h_dialogue.png"),
    ]
    W, H = 560, 315
    sheet = Image.new("RGB", (2 * W + 90, 3 * (H + 62) + 54), BG)
    d = ImageDraw.Draw(sheet)
    text(d, (30, 16), "candidate_n5 vs P1: t084 is the fixed full-scene anchor", 26, INK, True)
    for i, (label, path) in enumerate(items):
        col, row = i % 2, i // 2
        x = 30 + col * (W + 30)
        y = 74 + row * (H + 62)
        panel(sheet, d, Image.open(path), (x, y), (W, H), label)
    out = N4 / "T2/reference_comparison_t084.png"
    sheet.save(out)
    print(out)


def before_after():
    n2 = Image.open(N2 / "T3/game_finalN2_formal_no_ui.png")
    n4 = Image.open(N4 / "T3/game_finalN5h_formal_no_ui.png")
    W, H = 600, 338
    sheet = Image.new("RGB", (2 * W + 90, 3 * (H + 60) + 56), BG)
    d = ImageDraw.Draw(sheet)
    text(d, (30, 16), "N01/N02: candidate_n2 vs candidate_n5", 26, INK, True)
    text(d, (30, 46), "同一机位，非位图生成；树/花坛/长椅/前景与材质纹理由原生 Blender 源更新", 16, MUTED)
    panel(sheet, d, n2, (30, 80), (W, H), "candidate_n2")
    panel(sheet, d, n4, (30 + W + 30, 80), (W, H), "candidate_n5")
    crops = [
        ("树冠/花坛 close", n2, n4, (180, 10, 760, 470)),
        ("长椅 close", n2, n4, (980, 380, 1280, 600)),
        ("前景 close", n2, n4, (0, 500, 520, 720)),
    ]
    # crops are taken from a 1280x720 pair and shown side by side
    cw, ch = 400, 250
    for i, (label, a, b, box) in enumerate(crops):
        y = 80 + (i + 1) * (H + 60)
        panel(sheet, d, a.crop(box), (30, y), (2 * W + 30, ch), label + " · n2")
        panel(sheet, d, b.crop(box), (30 + 2 * W + 30, y), (0, 0), "") if False else None
    # Instead, a dedicated 3-row close sheet.
    sheet2 = Image.new("RGB", (2 * cw + 90, 3 * (ch + 62) + 54), BG)
    d2 = ImageDraw.Draw(sheet2)
    text(d2, (30, 16), "N01/N02 close-ups: n2 vs n4", 26, INK, True)
    for i, (label, a, b, box) in enumerate(crops):
        col = 0
        y = 74 + i * (ch + 62)
        panel(sheet2, d2, a.crop(box), (30, y), (cw, ch), label + " · n2")
        panel(sheet2, d2, b.crop(box), (30 + cw + 30, y), (cw, ch), label + " · n4")
    sheet2.save(N4 / "T4/N01_geometry_closeups.png")
    sheet.save(N4 / "T4/N01_geometry_before_after.png")
    print(N4 / "T4/N01_geometry_before_after.png")
    print(N4 / "T4/N01_geometry_closeups.png")


def ui_compare():
    n2 = Image.open(N2 / "T3/game_finalN2_dialogue.png")
    n4 = Image.open(N4 / "T3/game_finalN5h_dialogue.png")
    W, H = 600, 338
    sheet = Image.new("RGB", (2 * W + 90, H + 120), BG)
    d = ImageDraw.Draw(sheet)
    text(d, (30, 16), "N03 UI: n2 vs n4 (dialogue)", 26, INK, True)
    text(d, (30, 46), "n4: 对白高度 176 (24.4%), 半透明外缘+内层纸, 增大字色对比, 手绘边角", 16, MUTED)
    panel(sheet, d, n2, (30, 90), (W, H), "candidate_n2")
    panel(sheet, d, n4, (30 + W + 30, 90), (W, H), "candidate_n5")
    sheet.save(N4 / "T4/N03_ui_before_after.png")
    print(N4 / "T4/N03_ui_before_after.png")


if __name__ == "__main__":
    reference()
    before_after()
    ui_compare()
