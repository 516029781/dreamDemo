"""
Reusable native postcard geometry (PROP006 pickup cards and PROP003 board cards).

A card is one mesh with four/five material slots: paper, ink, accent, accent2
and brass (pins).  Card origin is bottom centre, front faces -Y, so after the
Y-up glTF export the printed face points +Z; layout rotations turn it toward the
player.  Art is real thin geometry (no textures, no generated images).
"""
import math
import sys
import os

import bmesh
import bpy
from mathutils import Vector

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import courtyard_lib as cl  # noqa: E402


def _front_box(bm, x, z, w, h, t, scale, mat_index):
    # Thin relief box sitting on the card front (-Y).
    cl.add_box(bm, (x * scale, -0.0015 * scale - t * scale / 2.0, z * scale),
               (w * scale, t * scale, h * scale), mat_index=mat_index)


def _dotted_ring(bm, cx, cz, radius, dots, scale, mat_index, dot=0.0035):
    for i in range(dots):
        a = math.tau * i / dots
        _front_box(bm, cx + radius * math.cos(a), cz + radius * math.sin(a),
                   dot, dot, 0.0006, scale, mat_index)


def create_postcard(collection, design, name, scale=1.75, pins=False,
                    materials=None):
    """design: 'A' bench+leaf, 'B' tree+ring, 'C' pergola+postmark."""
    paper = cl.mat_paper_cream()
    ink = cl.mat_ink()
    accent_map = {
        "A": (cl.mat_leaf_ochre(), cl.mat_metal_rust()),
        "B": (cl.mat_leaf_olive(), cl.mat_leaf_amber()),
        "C": (cl.mat_leaf_amber(), cl.mat_leaf_olive()),
    }
    accent, accent2 = accent_map[design]
    brass = cl.mat_metal_brass()
    mats = [paper, ink, accent, accent2, brass]

    w, h, t = 0.16, 0.11, 0.003
    bm = bmesh.new()
    cl.add_box(bm, (0, 0, h / 2.0), (w, t, h), mat_index=0)

    # Frame line inset 0.006, 0.0012 wide.
    margin = 0.006
    for (x, z, bw, bh) in ((0, margin, w - 2 * margin, 0.0012),
                           (0, h - margin, w - 2 * margin, 0.0012),
                           (-w / 2 + margin, h / 2, 0.0012, h - 2 * margin),
                           (w / 2 - margin, h / 2, 0.0012, h - 2 * margin)):
        _front_box(bm, x, z, bw, bh, 0.0006, scale, 1)

    # Stamp (top right) with a tiny inner motif.
    sx, sz = 0.052, 0.085
    _front_box(bm, sx, sz, 0.030, 0.030, 0.0008, scale, 3)
    _front_box(bm, sx, sz, 0.022, 0.022, 0.0010, scale, 0)
    if design == "B":
        _dotted_ring(bm, sx, sz, 0.0075, 8, scale, 1, dot=0.0022)
    else:
        _front_box(bm, sx, sz, 0.012, 0.0014, 0.0012, scale, 1)
        _front_box(bm, sx, sz, 0.0014, 0.012, 0.0012, scale, 1)

    # Address / message lines (lower right).
    for i in range(3):
        _front_box(bm, 0.033, 0.030 + i * 0.010, 0.054, 0.0011, 0.0007,
                   scale, 1)
    _front_box(bm, 0.033, 0.061, 0.036, 0.0013, 0.0007, scale, 1)

    # Design motif (left half of the card).
    mx, mz = -0.034, 0.052
    if design == "A":
        # Bench: seat, back, legs; plus one leaf.
        for (dx, dz, bw, bh) in ((0.0, -0.004, 0.060, 0.006),
                                 (0.0, 0.010, 0.060, 0.005),
                                 (-0.020, 0.003, 0.005, 0.016)):
            _front_box(bm, mx + dx, mz + dz, bw, bh, 0.0010, scale, 3)
        for dx in (-0.026, 0.026):
            _front_box(bm, mx + dx, mz - 0.011, 0.004, 0.010, 0.0010, scale, 3)
        cl.add_leaf(bm, (0.008 * scale, -0.0035 * scale, 0.082 * scale),
                    Vector((0, -1, 0.2)), 0.034 * scale,
                    math.radians(20), 2)
    elif design == "B":
        # Tree: trunk, three canopy leaves, dotted ring under it.
        _front_box(bm, mx, mz - 0.006, 0.006, 0.030, 0.0012, scale, 1)
        for (dx, dz, rr) in ((0.0, 0.020, 0.020), (-0.013, 0.012, 0.014),
                             (0.013, 0.012, 0.014)):
            cl.add_leaf(bm, ((mx + dx) * scale, -0.0040 * scale,
                             (mz + dz) * scale), Vector((0, -1, 0.1)),
                        rr * scale, math.radians(90), 2)
        _dotted_ring(bm, mx, mz - 0.021, 0.024, 14, scale, 3, dot=0.0030)
    else:
        # Pergola: two posts, beam, five rafters.
        for dx in (-0.026, 0.026):
            _front_box(bm, mx + dx, mz - 0.006, 0.005, 0.034, 0.0010, scale, 1)
        _front_box(bm, mx, mz + 0.011, 0.064, 0.005, 0.0010, scale, 3)
        for i in range(5):
            _front_box(bm, mx - 0.024 + i * 0.012, mz + 0.018, 0.003, 0.012,
                       0.0008, scale, 1)
        _dotted_ring(bm, 0.028, 0.078, 0.014, 10, scale, 3, dot=0.0024)

    if pins:
        for dx in (-w / 2 + 0.018, w / 2 - 0.018):
            cl.add_cylinder(bm, (dx * scale, -t / 2 * scale, (h - 0.018) * scale),
                            (dx * scale, -(t / 2 + 0.006) * scale,
                             (h - 0.018) * scale), 0.0026 * scale,
                            0.0020 * scale, 6, 4)

    obj = cl.finish_mesh(name, bm, mats, collection)
    obj["asset_id"] = "PROP006" if not pins else "PROP003"
    obj["postcard_design"] = design
    obj["front_face"] = "-Y in Blender / +Z in engine"
    obj["pickup_offset_y"] = 0.15
    return obj
