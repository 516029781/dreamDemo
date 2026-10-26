"""
ENV001-compatible paving layout shared by the look scene and MAP001.

The module footprint, slab pattern, joint widths and thickness match
art/full/source/environment/ENV001_stone_paving.blend (4.0 x 4.0 m module,
slab tops at +0.14 in module space, mortar bed 0.04 thick).  MAP001 uses the
same pattern at a lower bevel LOD so the full map stays near the triangle
budget; the delivered ENV001 source itself is untouched.
"""
import random
import sys
import os
import math

import bmesh
import bpy

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import courtyard_lib as cl  # noqa: E402

SLAB_TOP = 0.14
SLAB_BOTTOM = 0.04
MORTAR_TOP = 0.04
MORTAR_BOTTOM = 0.0
JOINT = 0.02
MODULE_HALF = 2.0

EVEN_X = [(-1.99, -1.01), (-0.99, -0.01), (0.01, 0.99), (1.01, 1.99)]
ODD_X = [(-1.99, -1.51), (-1.49, -1.01), (-0.99, -0.51), (-0.49, -0.01),
         (0.01, 0.49), (0.51, 0.99), (1.01, 1.49), (1.51, 1.99)]


def add_paving_module(slabs_bm, mortar_bm, center, z_top=SLAB_TOP,
                      seed=20261024):
    """Append one 4x4 m paving module (slabs + mortar) at center=(x, y)."""
    rng = random.Random(seed)
    cx, cy = center
    slab_bottom = z_top - (SLAB_TOP - SLAB_BOTTOM)
    mortar_top = z_top - (SLAB_TOP - MORTAR_TOP)
    mortar_bottom = z_top - (SLAB_TOP - MORTAR_BOTTOM)
    for row in range(8):
        y0 = cy - 1.99 + row * 0.5
        y1 = y0 + 0.48
        pieces = EVEN_X if row % 2 == 0 else ODD_X
        for (x0, x1) in pieces:
            lift = rng.uniform(0.0, 0.0035)
            w = x1 - x0
            cl.add_box(slabs_bm, (cx + (x0 + x1) / 2.0, (y0 + y1) / 2.0,
                                  (slab_bottom + z_top + lift) / 2.0),
                       (w, y1 - y0, z_top + lift - slab_bottom), mat_index=0)
    cl.add_box(mortar_bm, (cx, cy, (mortar_bottom + mortar_top) / 2.0),
               (2 * MODULE_HALF, 2 * MODULE_HALF, mortar_top - mortar_bottom),
               mat_index=0)


def create_paving(collection, centers, z_top=SLAB_TOP, prefix="PAVING",
                  bevel_segments=2, materials=None, lod=False):
    slabs_bm = bmesh.new()
    mortar_bm = bmesh.new()
    for i, center in enumerate(centers):
        add_paving_module(slabs_bm, mortar_bm, center, z_top=z_top,
                          seed=20261024 + i * 17)
    slabs = cl.finish_mesh(prefix + "_slabs", slabs_bm,
                           [cl.mat_stone_base(), cl.mat_stone_light(), cl.mat_stone_dark()], collection)
    # Per-slab tonal variation uses native materials (no UV/texture claim); map LOD
    # keeps the same joints but breaks the flat single-color field.
    for poly in slabs.data.polygons:
        c = poly.center
        key = (int(c.x * 1.7) * 13 + int(c.y * 1.7) * 7) % 23
        poly.material_index = 1 if key in (0, 7) else 2 if key == 3 else 0
    if bevel_segments > 0:
        cl.add_bevel(slabs, width=0.006, segments=1 if lod else bevel_segments)
    else:
        # Map LOD: sharp slab edges are invisible at the full-map camera
        # distance; joints and 3.5 mm top variation remain real geometry.
        bpy.ops.object.select_all(action="DESELECT")
        slabs.select_set(True)
        bpy.context.view_layer.objects.active = slabs
        bpy.ops.object.shade_auto_smooth(angle=math.radians(30.0))
        slabs.select_set(False)
    mortar = cl.finish_mesh(prefix + "_mortar", mortar_bm, [cl.mat_mortar()],
                            collection)
    return [slabs, mortar]
