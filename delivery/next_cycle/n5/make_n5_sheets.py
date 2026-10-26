"""n5 comparison sheets: P1 style anchor + n4/n5 same-camera deltas.

The n4 provisional report criticised n4 for scoring single-region improvements
without a full-frame counter-check. So each sheet carries three columns:
  - P1  : style/density anchor from the shipped reference (NOT this camera)
  - n4  : previous candidate, same camera as n5 when preset A is kept
  - n5  : current candidate
Crop rows compare n4 vs n5 only, because those two are genuinely same-camera.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path("C:/软件/鼠鼠")
N5 = ROOT / "delivery/next_cycle/n5"
N4 = ROOT / "delivery/next_cycle/n4"
T3, T4, T6 = N5 / "T3", N5 / "T4", N5 / "T6"
P1 = ROOT / "reference/_raw_screenshots/P1"
FONT = "C:/Windows/Fonts/NotoSansSC-VF.ttf"
BG = (246, 242, 233)
INK = (38, 41, 42)


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except Exception:
        return ImageFont.load_default()


def label(draw, xy, text, size=20, fill=INK):
    draw.text(xy, text, font=font(size), fill=fill)


def fit(im, w, h):
    im = im.convert("RGB")
    sc = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)


def tile(sheet, draw, im, x, y, w, h, caption):
    pic = fit(im, w, h)
    sheet.paste(pic, (x + (w - pic.width) // 2, y + (h - pic.height) // 2))
    draw.rectangle([x, y, x + w, y + h], outline=(170, 164, 150), width=2)
    label(draw, (x, y + h + 6), caption, 15)


def three_column(out, title, p1_img, n4_img, n5_img, p1_caption):
    w, h = 400, 240
    sheet = Image.new("RGB", (3 * w + 80, h + 130), BG)
    d = ImageDraw.Draw(sheet)
    label(d, (20, 16), title, 24)
    for i, (im, cap) in enumerate((
            (p1_img, p1_caption),
            (n4_img, "candidate_n4 · same camera"),
            (n5_img, "candidate_n5 · same camera"))):
        tile(sheet, d, im, 20 + i * (w + 20), 52, w, h, cap)
    sheet.save(out)
    print(out)


def crop_rows(out, title, n4_img, n5_img, crops):
    """crops: list of (caption, normalised box) applied to both candidates."""
    cw, ch = 440, 262
    sheet = Image.new("RGB", (2 * cw + 70, len(crops) * (ch + 58) + 54), BG)
    d = ImageDraw.Draw(sheet)
    label(d, (20, 16), title, 24)
    for i, (caption, box) in enumerate(crops):
        y = 64 + i * (ch + 58)
        for j, (img, name) in enumerate(((n4_img, "n4"), (n5_img, "n5"))):
            W, H = img.size
            im = img.crop((int(box[0] * W), int(box[1] * H),
                           int(box[2] * W), int(box[3] * H)))
            tile(sheet, d, im, 20 + j * (cw + 30), y, cw, ch, f"{caption} · {name}")
    sheet.save(out)
    print(out)


def main():
    forms = {}
    for tag, base in (("n4", N4 / "T3"), ("n5", T3)):
        for key in ("formal_no_ui", "formal_ui", "dialogue"):
            p = base / f"game_final{'N4' if tag == 'n4' else 'N5'}_{key}.png"
            if p.is_file():
                forms[(tag, key)] = Image.open(p)

    if ("n5", "formal_no_ui") not in forms:
        raise SystemExit("n5 formal_no_ui missing; capture before building sheets")

    env_crops = [
        ("tree + planter", (0.14, 0.01, 0.59, 0.64)),
        ("bench / lamp", (0.62, 0.48, 1.0, 0.90)),
        ("foreground path edge", (0.0, 0.58, 0.48, 1.0)),
    ]

    if ("n4", "formal_no_ui") in forms:
        crop_rows(T4 / "N01_geometry_before_after.png",
                  "N01 geometry: n4 vs n5 (same camera)",
                  forms[("n4", "formal_no_ui")], forms[("n5", "formal_no_ui")],
                  env_crops)
        crop_rows(T4 / "N02_shadow_before_after.png",
                  "N02 shadow / contact: n4 vs n5 (same camera)",
                  forms[("n4", "formal_no_ui")], forms[("n5", "formal_no_ui")],
                  [("tree shade + planter contact", (0.08, 0.30, 0.55, 0.80)),
                   ("bench / lamp contact", (0.60, 0.46, 1.0, 0.92)),
                   ("character contact", (0.22, 0.62, 0.60, 1.0))])
        three_column(T4 / "N01_style_anchor.png",
                     "P1 style anchor vs n4 / n5 gameplay frames",
                     Image.open(P1 / "t015s.jpg"),
                     forms[("n4", "formal_no_ui")], forms[("n5", "formal_no_ui")],
                     "P1 t015 · style/density anchor, NOT this camera")

    if ("n4", "dialogue") in forms and ("n5", "dialogue") in forms:
        three_column(T4 / "N03_ui_before_after.png",
                     "N03 UI: P1 anchor vs n4 / n5 dialogue",
                     Image.open(P1 / "t044s.jpg"),
                     forms[("n4", "dialogue")], forms[("n5", "dialogue")],
                     "P1 t044 · UI style anchor, NOT this camera")

    mat = [Image.open(T3 / f"mat_finalN5_{k}.png")
           for k in ("ENV001", "ENV006", "PROP001", "PROP004")
           if (T3 / f"mat_finalN5_{k}.png").is_file()]
    if mat:
        grid = Image.new("RGB", (2 * 620 + 60, 2 * 440 + 110), BG)
        gd = ImageDraw.Draw(grid)
        label(gd, (20, 16), "N02 material closeups · candidate_n5", 24)
        names = ["ENV001 stone paving", "ENV006 autumn tree", "PROP001 bench", "PROP004 lamp"]
        for i, im in enumerate(mat[:4]):
            c, r = i % 2, i // 2
            tile(grid, gd, im, 20 + c * 640, 56 + r * 455, 620, 400, names[i])
        grid.save(T4 / "N02_material_closeups.png")
        print(T4 / "N02_material_closeups.png")

    vis, hid = T4 / "N04_actor_visible.png", T4 / "N04_actor_hidden.png"
    if vis.is_file() and hid.is_file():
        sheet = Image.new("RGB", (2 * 620 + 60, 430), BG)
        d = ImageDraw.Draw(sheet)
        label(d, (20, 16), "N04 real bbox: visible vs hidden PlayerWorldQuad", 24)
        tile(sheet, d, Image.open(vis), 20, 56, 620, 350, "visible")
        tile(sheet, d, Image.open(hid), 660, 56, 620, 350, "hidden")
        sheet.save(T4 / "N04_actor_bbox.png")
        print(T4 / "N04_actor_bbox.png")

    n05 = [T4 / f"N05_{k}.png" for k in ("fresh_portrait", "resize_portrait", "restored_landscape")]
    if all(p.is_file() for p in n05):
        sheet = Image.new("RGB", (3 * 400 + 80, 400), BG)
        d = ImageDraw.Draw(sheet)
        label(d, (20, 16), "N05 orientation: fresh portrait / resize / restore", 22)
        for i, (p, cap) in enumerate(zip(n05, ("fresh portrait", "resize portrait",
                                               "restored landscape"))):
            tile(sheet, d, Image.open(p), 20 + i * 420, 52, 400, 320, cap)
        sheet.save(T4 / "N05_orientation.png")
        print(T4 / "N05_orientation.png")

    idles = [T6 / "character_n" / f"idle_{i:02d}.png" for i in range(6)]
    moves = [T6 / "character_n" / f"move_{i:02d}.png" for i in range(6)]
    if all(p.is_file() for p in idles + moves):
        sheet = Image.new("RGB", (6 * 300 + 60, 2 * 250 + 110), BG)
        d = ImageDraw.Draw(sheet)
        label(d, (20, 16), "N07 idle (top) / move (bottom): 6 unique frames each", 24)
        for i in range(6):
            tile(sheet, d, Image.open(idles[i]), 20 + i * 300, 52, 290, 220, f"idle {i}")
            tile(sheet, d, Image.open(moves[i]), 20 + i * 300, 322, 290, 220, f"move {i}")
        sheet.save(T6 / "character_n/N07_animation_sheet.png")
        print(T6 / "character_n/N07_animation_sheet.png")


main()
