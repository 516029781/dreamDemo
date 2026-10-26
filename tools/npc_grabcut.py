import cv2
import numpy as np
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "art", "full", "source", "characters", "CHAR003_NPC_GARDENER")

def imread_u(path, flags):
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, flags)

def imwrite_u(path, img):
    ext = os.path.splitext(path)[1]
    ok, buf = cv2.imencode(ext, img)
    if not ok:
        raise RuntimeError('encode failed: ' + path)
    buf.tofile(path)

src = imread_u(os.path.join(D, "npc_source_crop_490x670.png"), cv2.IMREAD_COLOR)
rough = imread_u(os.path.join(D, "npc_rough_mask.png"), cv2.IMREAD_GRAYSCALE)
if src is None or rough is None:
    raise SystemExit("missing source or rough mask")
h, w = rough.shape[:2]
mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
mask[rough > 128] = cv2.GC_PR_FGD
# Definite background border and known corners.
mask[:14, :] = cv2.GC_BGD
mask[-14:, :] = cv2.GC_BGD
mask[:, :14] = cv2.GC_BGD
mask[:, -14:] = cv2.GC_BGD
# Definite foreground core: erode the hand mask so the edge halos are not forced.
core = cv2.erode((rough > 128).astype(np.uint8), np.ones((9, 9), np.uint8), iterations=1)
mask[core > 0] = cv2.GC_FGD
bgd = np.zeros((1, 65), np.float64)
fgd = np.zeros((1, 65), np.float64)
rect = (8, 8, w - 16, h - 16)
cv2.grabCut(src, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
# Clean specks and fill tiny holes; keep separate components such as paper/hands.
kernel = np.ones((3, 3), np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, kernel, iterations=1)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel, iterations=1)
n, labels, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
clean = np.zeros_like(fg)
for i in range(1, n):
    if stats[i, cv2.CC_STAT_AREA] >= 120:
        clean[labels == i] = 255
# Feathered alpha mask for compositing.
alpha = cv2.GaussianBlur(clean, (0, 0), 0.8)
imwrite_u(os.path.join(D, "npc_grabcut_mask.png"), alpha)
b, g, r = cv2.split(src)
rgba = cv2.merge([b, g, r, alpha])
imwrite_u(os.path.join(D, "npc_grabcut_rgba.png"), rgba)
bg = np.full_like(src, (211, 225, 232))
a = (alpha.astype(np.float32) / 255.0)[..., None]
preview = (src.astype(np.float32) * a + bg.astype(np.float32) * (1 - a)).astype(np.uint8)
imwrite_u(os.path.join(D, "npc_grabcut_preview.png"), preview)
print("grabcut done", fg.shape, "fg_pixels", int((alpha > 8).sum()))
