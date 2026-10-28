#!/usr/bin/env python3
"""Generate the fixed-reference vs v04 camera-projection anchor overlay."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'planning/art/target_layout_v04.json'
MEASURED = ROOT / 'art/static_map/p1_autumn_courtyard/v04/bbox_v04.json'
OUT = ROOT / 'planning/art/TARGET_OVERLAY_v04.svg'
W, H = 1920, 1078

target = json.loads(TARGET.read_text(encoding='utf-8'))
measured = json.loads(MEASURED.read_text(encoding='utf-8'))
names = {
    'A01': 'A01 tree', 'A02': 'A02 stairs', 'A03': 'A03 plaza',
    'A04': 'A04 equipment', 'A05': 'A05 planters', 'A06': 'A06 watercourse',
}
lines = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1078" viewBox="0 0 1920 1078">',
    '<title>Fixed P1 reference anchors overlaid with v04 projected bounds</title>',
    '<desc>Solid red boxes are fixed reference targets; dashed cyan boxes are measured v04 bounds clipped to the canvas; yellow lines are target guides.</desc>',
    '<defs><clipPath id="canvas"><rect x="0" y="0" width="1920" height="1078"/></clipPath></defs>',
    '<g fill="none" stroke="#ffd43b" stroke-width="3" stroke-dasharray="12 8" opacity=".85">',
]
for g in target['guides']:
    y = g['y'] * H / 100
    lines.append(f'<path d="M0 {y:.1f} H1920"/>')
lines.append('</g>')
for a in target['anchors']:
    if a['id'] not in names:
        continue
    x0, y0, x1, y1 = a['bbox']
    lines.append(f'<rect x="{x0*W/100:.1f}" y="{y0*H/100:.1f}" width="{(x1-x0)*W/100:.1f}" height="{(y1-y0)*H/100:.1f}" fill="#ff3b30" fill-opacity=".035" stroke="#ff3b30" stroke-width="4"/>')
    lines.append(f'<text x="{x0*W/100+8:.1f}" y="{y0*H/100+26:.1f}" fill="#ff3b30" font-family="Arial" font-size="22" font-weight="700">{names[a["id"]]} target</text>')
    b = measured[names[a['id']].split()[0] + '_' + {'A01':'tree','A02':'stairs','A03':'plaza','A04':'equipment','A05':'planters','A06':'distant'}[a['id']]]['bbox_pct']
    ax0, ay0, ax1, ay1 = b
    lines.append(f'<g clip-path="url(#canvas)"><rect x="{ax0*W/100:.1f}" y="{ay0*H/100:.1f}" width="{(ax1-ax0)*W/100:.1f}" height="{(ay1-ay0)*H/100:.1f}" fill="none" stroke="#00cfe8" stroke-width="4" stroke-dasharray="10 7"/></g>')
    lines.append(f'<text x="{min(W-230,ax0*W/100+8):.1f}" y="{min(H-8,max(24,ay0*H/100+50)):.1f}" fill="#00b9d4" font-family="Arial" font-size="20" font-weight="700">{names[a["id"]]} actual</text>')
lines.append('</svg>')
OUT.write_text('\n'.join(lines), encoding='utf-8')
print(f'Wrote {OUT}')
