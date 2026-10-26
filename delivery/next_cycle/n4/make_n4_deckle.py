"""Regenerate the torn-washi deckle edge for the n4 paper nine-slice source.

The n4a outline used long smooth cubic segments, which rendered as rounded cloud
lobes. A real hand-tear is short, irregular and slightly deeper in places, so
this emits a dense jittered polyline instead. Amplitude is kept small because
nine-slice stretches the middle of each edge horizontally.
"""
import random
import re

SVG = r"C:\软件\鼠鼠\art\candidates\candidate_n4\ui\components\paper_panel_wash.svg"
W, H = 512, 256
MARGIN = 44
STEP = 7.0
AMP = 3.4


def build_path(rng):
    x0, x1 = MARGIN * 0.42, W - MARGIN * 0.42
    y0, y1 = MARGIN * 0.28, H - MARGIN * 0.28
    top_y, bot_y = 11.0, 245.0
    left_x, right_x = 13.0, 499.0

    segs = []
    # top: left to right
    segs.append([(x0, top_y + rng.uniform(-2, 2))])
    for i in range(1, int((x1 - x0) / STEP)):
        x = x0 + i * STEP
        off = rng.uniform(-AMP, AMP)
        if rng.random() < 0.13:
            off *= 1.8
        segs.append([(x, top_y + off)])
    # right: top to bottom
    segs.append([(right_x + rng.uniform(-2, 2), y0)])
    for i in range(1, int((y1 - y0) / STEP)):
        y = y0 + i * STEP
        off = rng.uniform(-AMP, AMP)
        if rng.random() < 0.13:
            off *= 1.8
        segs.append([(right_x + off, y)])
    # bottom: right to left
    segs.append([(x1, bot_y + rng.uniform(-2, 2))])
    for i in range(1, int((x1 - x0) / STEP)):
        x = x1 - i * STEP
        off = rng.uniform(-AMP, AMP)
        if rng.random() < 0.13:
            off *= 1.8
        segs.append([(x, bot_y + off)])
    # left: bottom to top
    segs.append([(left_x + rng.uniform(-2, 2), y1)])
    for i in range(1, int((y1 - y0) / STEP)):
        y = y1 - i * STEP
        off = rng.uniform(-AMP, AMP)
        if rng.random() < 0.13:
            off *= 1.8
        segs.append([(left_x + off, y)])

    pts = [p for group in segs for p in group]
    parts = ["M%.1f %.1f" % pts[0]]
    for (px, py) in pts[1:]:
        parts.append("L%.1f %.1f" % (px, py))
    parts.append("Z")
    return "\n         ".join(_wrap(parts))


def _wrap(parts, width=6):
    for i in range(0, len(parts), width):
        yield " ".join(parts[i:i + width])


with open(SVG, "r", encoding="utf-8") as handle:
    text = handle.read()

rng = random.Random(20261025)
new_d = build_path(rng)

# Rebuild the whole paper-shape element. Matching on `d="` alone is unsafe
# because `id="paper-shape"` also contains that substring.
pattern = re.compile(
    r'<path id="paper-shape".*?fill="url\(#wash\)" fill-opacity="[\d.]+"\s*/>',
    re.DOTALL)
element = ('<path id="paper-shape"\n      d="%s"\n      fill="url(#wash)" '
           'fill-opacity="0.97"/>' % new_d)
text, hits = pattern.subn(lambda m: element, text)
if hits != 1:
    raise SystemExit("expected exactly one paper-shape element, found %d" % hits)

with open(SVG, "w", encoding="utf-8") as handle:
    handle.write(text)

print("paper-shape rewritten with %d deckle vertices" % (len(new_d.split("L")) - 1))
