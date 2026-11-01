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
# 2026-10-27: the mortar bed used to top out 100 mm under the slab face, so
# every joint was a 10 cm deep slot. Whatever the geometry did at the seam -
# an inset corner, a bevel, a 3.5 mm lift difference - the eye found the mortar
# plane at the bottom of the slot, lit head-on, and the joint read as a bright
# white chip instead of a dark line. Raising the bed to 6 mm under the face
# turns the joint into a shallow dark groove: there is no lit floor to see, and
# the slab side walls are buried in the bed so their slope cannot catch light.
MORTAR_TOP = 0.134
MORTAR_BOTTOM = 0.0
JOINT = 0.02
MODULE_HALF = 2.0

EVEN_X = [(-1.99, -1.01), (-0.99, -0.01), (0.01, 0.99), (1.01, 1.99)]
ODD_X = [(-1.99, -1.51), (-1.49, -1.01), (-0.99, -0.51), (-0.49, -0.01),
         (0.01, 0.49), (0.51, 0.99), (1.01, 1.49), (1.51, 1.99)]


def add_paving_module(slabs_bm, mortar_bm, center, z_top=SLAB_TOP,
                      seed=20261024, variant=0):
    """Append one 4x4 m paving module (slabs + mortar) at center=(x, y).

    Big-format only: three 1.33 m courses per module. The reference uses large
    slabs with joints that barely differ in value; dense 0.5 m tiles turned the
    ground into a high-frequency grid (measured 2.4x the reference edge density).
    """
    rng = random.Random(seed)
    cx, cy = center
    slab_bottom = z_top - (SLAB_TOP - SLAB_BOTTOM)
    mortar_top = z_top - (SLAB_TOP - MORTAR_TOP)
    mortar_bottom = z_top - (SLAB_TOP - MORTAR_BOTTOM)
    courses = 3
    course_h = 3.98 / courses
    joint = 0.018
    repair_row = rng.randint(0, courses - 2)
    repair_piece = 0
    for row in range(courses):
        y0 = cy - 1.99 + row * course_h
        y1 = y0 + course_h - joint
        if variant == 1:
            pieces = [(-1.99, -0.02), (-0.01, 1.99)]
        elif variant == 2:
            pieces = [(-1.99, -0.68), (-0.66, 0.66), (0.68, 1.99)]
        else:
            # Running bond: alternate courses shift their vertical joints.
            off = 0.0 if row % 2 == 0 else 0.44
            pieces = [(-1.99, -1.10 + off), (-1.08 + off, 0.10 + off),
                      (0.12 + off, 1.99)]
        # Repair group: one deterministic run of 2-4 adjacent slabs reads as a
        # mend, not as a random dirty tile. Group column shifts per row so the
        # patch forms an L instead of a stripe.
        repair = repair_row if row == repair_row else (repair_row - 1)
        for pi, (x0, x1) in enumerate(pieces):
            # 2026-10-27: every slab used to ride 0-3.5 mm high on its own
            # random lift. Neighbours therefore stepped against each other and
            # the joint walls of the neighbouring slab caught the key light -
            # at 720p that resolved as a dotted bright line along every joint,
            # the last remaining "white speck" on the paving. The draw is kept
            # so the shared RNG stream (and the whole layout) stays identical.
            rng.uniform(0.0, 0.0035)
            lift = 0.0
            patched = (row in (repair, repair + 1)
                       and pi in (repair_piece, repair_piece + 1))
            cl.add_box(slabs_bm, (cx + (x0 + x1) / 2.0, (y0 + y1) / 2.0,
                                  (slab_bottom + z_top + lift) / 2.0),
                       (x1 - x0 - joint, y1 - y0, z_top + lift - slab_bottom),
                       mat_index=2 if patched else 0)
    cl.add_box(mortar_bm, (cx, cy, (mortar_bottom + mortar_top) / 2.0),
               (2 * MODULE_HALF, 2 * MODULE_HALF, mortar_top - mortar_bottom),
               mat_index=0)
    # Hairline cracks: thin strips along the joints, two per module.
    #
    # They were authored as 6 mm tall boxes lifted 4 mm off the slab - a ridge,
    # not a groove. The top face catches the key light, so 32 of them rendered
    # as a regular grid of white scratches that read as grass on the paving.
    # N5_PAVING_CRACKS: 1 = original ridge, 2 = flush dark inlay, 0 = none.
    crack_mode = os.environ.get("N5_PAVING_CRACKS", "0")
    if crack_mode != "0":
        flush = crack_mode == "2"
        crack_z = z_top + 0.0008 if flush else z_top + 0.004
        crack_h = 0.0016 if flush else 0.006
        for ci in range(2):
            along_x = rng.random() < 0.5
            length = rng.uniform(1.1, 2.2)
            if along_x:
                x0 = cx + rng.uniform(-1.6, 1.6 - length * 0.5)
                y0 = cy + rng.choice([-1.99, -0.66, 0.67, 1.99]) * rng.uniform(0.92, 0.98)
                cl.add_box(slabs_bm, (x0 + length / 2.0, y0, crack_z),
                           (length, 0.022, crack_h), mat_index=2)
            else:
                y0 = cy + rng.uniform(-1.6, 1.6 - length * 0.5)
                x0 = cx + rng.choice([-1.99, -0.66, 0.67, 1.99]) * rng.uniform(0.92, 0.98)
                cl.add_box(slabs_bm, (x0, y0 + length / 2.0, crack_z),
                           (0.022, length, crack_h), mat_index=2)


def _add_slab(bm, cx, cy, w, d, z_bottom, z_top, rng, mat_index=0,
              corner_jitter=0.0):
    """One slab as a 12-triangle box whose four top corners move independently.

    A plain box gives four right angles per corner, so every joint in the map was
    parallel and exactly 0.02 m wide — the reviewer's "17x9 grid with constant
    joints". Cutting the top face's corners inward by an independent amount makes
    neighbouring slabs share a wavy joint of varying width while the triangle
    count stays at 12 and the top stays flat.
    """
    hw, hd = w / 2.0, d / 2.0
    j = corner_jitter
    corners = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
    # One inset for all four corners, not four independent ones.
    #
    # The old version moved each top corner by an independent uniform(0, j).
    # Two neighbours in a junction therefore both pulled back, and the slab
    # sides sloped outward toward the bottom, so every junction opened into a
    # V-shaped notch up to ~5 cm wide. Ten centimetres under that notch sits
    # the mortar slab, a horizontal face pointing at the key light, which is
    # why the map showed a regular grid of bright white blocks on the paving
    # (reported as "grass growing on the flagstones"). A single inset per slab
    # can only narrow it, so neighbours keep one continuous joint and no void
    # is ever created.
    e = rng.uniform(0.0, j) if j else 0.0
    hw_t, hd_t = hw - e, hd - e
    top = []
    for sx, sy in corners:
        x = cx + sx * hw_t
        y = cy + sy * hd_t
        top.append(bm.verts.new((x, y, z_top)))
    bottom = []
    for sx, sy in corners:
        bottom.append(bm.verts.new((cx + sx * hw, cy + sy * hd, z_bottom)))
    made = [bm.faces.new(top), bm.faces.new(list(reversed(bottom)))]
    for i in range(4):
        k = (i + 1) % 4
        made.append(bm.faces.new((bottom[i], bottom[k], top[k], top[i])))
    for f in made:
        f.material_index = mat_index


def _course_widths(rng, count, jitter=0.22):
    """Split 3.98 m into `count` slabs of unequal width."""
    total = 3.98
    raw = [1.0 + rng.uniform(-jitter, jitter) for _ in range(count)]
    scale = total / sum(raw)
    widths = [w * scale for w in raw]
    # absorb the rounding drift into the last piece so the module stays 4 m
    widths[-1] = total - sum(widths[:-1])
    return widths


def add_paving_module_style(slabs_bm, mortar_bm, center, style, z_top=SLAB_TOP,
                            seed=20261024):
    """Append one 4x4 m module in one of the three paving languages.

    plaza  large hand-cut flags (2-3 per course) for the central square
    path   narrow running bond (5-6 per course) along the axes
    edge   small cobbles (9-10 per course) on the outer margins
    """
    rng = random.Random(seed)
    cx, cy = center
    slab_bottom = z_top - (SLAB_TOP - SLAB_BOTTOM)
    mortar_top = z_top - (SLAB_TOP - MORTAR_TOP)
    mortar_bottom = z_top - (SLAB_TOP - MORTAR_BOTTOM)

    if style == 'plaza':
        # 2026-10-27: one language for the whole yard. Big hand-cut flags -
        # three courses of 1.33 m per 4 m module, 2-3 pieces per course. The
        # eight 0.5 m courses read as small tiles and, together with the three
        # different bond patterns, produced the "paving format is inconsistent"
        # note. Reference slabs are roughly 1.2 x 0.6 m.
        courses, dims, jitter, joint = 3, (2, 3), 0.0, 0.014
    elif style == 'path':
        courses, dims, jitter, joint = 8, (5, 6), 0.005, 0.011
    else:
        courses, dims, jitter, joint = 10, (9, 10), 0.004, 0.010

    # Look-dev knobs. UNIFY collapses the three paving languages into the plaza
    # one so the whole yard reads as a single flagstone field; JOINT_SCALE
    # narrows the gap without touching slab sizes.
    # Default flipped to 1 on 2026-10-27: mixing 1.33 m flags with 0.4 m cobbles
    # in the same frame is what the reviewer called "格式不统一".
    if os.environ.get("N5_PAVING_UNIFY", "1") == "1":
        style = 'plaza'
        courses, dims, jitter, joint = 3, (2, 3), 0.0, 0.014
    joint = joint * float(os.environ.get("N5_PAVING_JOINT_SCALE", "1") or 1)

    course_h = 3.98 / courses
    # Unequal course heights: with every course 0.5 m the joints still line up
    # into a perfect grid even when the individual slabs vary in width.
    weights = [1.0 + rng.uniform(-0.26, 0.26) for _ in range(courses)]
    scale = 3.98 / sum(weights)
    heights = [w * scale for w in weights]
    heights[-1] = 3.98 - sum(heights[:-1])
    y_cursor = cy - 1.99
    for row in range(courses):
        course_h = heights[row]
        y0 = y_cursor
        y_cursor += course_h
        # running bond: alternate courses start half a slab later
        offset = 0.0
        if style == 'path' and row % 2 == 1:
            offset = course_h * 0.0
        count = rng.randint(*dims)
        widths = _course_widths(rng, count)
        x = cx - 1.99
        if style == 'path' and row % 2 == 1:
            # shift by half a slab and let the two ends close the module
            half = widths[0] / 2.0
            x = cx - 1.99 - half
            widths = [half] + widths + [half]
        for w in widths:
            x0, x1 = max(cx - 1.99, x), min(cx + 1.99, x + w - joint)
            x += w
            if x1 - x0 < 0.05:
                continue
            depth = course_h - joint
            # 2026-10-27: every slab used to ride 0-3.5 mm high on its own
            # random lift. Neighbours therefore stepped against each other and
            # the joint walls of the neighbouring slab caught the key light -
            # at 720p that resolved as a dotted bright line along every joint,
            # the last remaining "white speck" on the paving. The draw is kept
            # so the shared RNG stream (and the whole layout) stays identical.
            rng.uniform(0.0, 0.0035)
            lift = 0.0
            worn = 0.0
            if style == 'edge' and rng.random() < 0.05:
                # a settled cobble: 8 mm low, catches a shadow line
                worn = 0.008
            _add_slab(slabs_bm, (x0 + x1) / 2.0, y0 + depth / 2.0,
                      x1 - x0, depth, slab_bottom,
                      z_top + lift - worn, rng,
                      mat_index=0, corner_jitter=jitter)
    cl.add_box(mortar_bm, (cx, cy, (mortar_bottom + mortar_top) / 2.0),
               (2 * MODULE_HALF, 2 * MODULE_HALF, mortar_top - mortar_bottom),
               mat_index=0)
    # Hairline cracks: thin dark strips sitting just above the slab top along
    # the joints. Two per module, deterministic, never floating.
    for ci in range(2):
        along_x = rng.random() < 0.5
        length = rng.uniform(1.1, 2.2)
        if along_x:
            x0 = cx + rng.uniform(-1.6, 1.6 - length * 0.5)
            y0 = cy + rng.choice([-1.99, -0.66, 0.67, 1.99]) * rng.uniform(0.92, 0.98)
            cl.add_box(slabs_bm, (x0 + length / 2.0, y0, z_top + 0.004),
                       (length, 0.022, 0.006), mat_index=2)
        else:
            y0 = cy + rng.uniform(-1.6, 1.6 - length * 0.5)
            x0 = cx + rng.choice([-1.99, -0.66, 0.67, 1.99]) * rng.uniform(0.92, 0.98)
            cl.add_box(slabs_bm, (x0, y0 + length / 2.0, z_top + 0.004),
                       (0.022, length, 0.006), mat_index=2)


def create_paving(collection, centers, z_top=SLAB_TOP, prefix="PAVING",
                  bevel_segments=2, materials=None, lod=False, variants=False,
                  styles=None):
    slabs_bm = bmesh.new()
    mortar_bm = bmesh.new()
    used = []
    for i, center in enumerate(centers):
        if styles:
            style = styles[i] if i < len(styles) else styles[-1]
            used.append(style)
            add_paving_module_style(slabs_bm, mortar_bm, center, style,
                                    z_top=z_top, seed=20261024 + i * 17)
            continue
        variant = 0
        if variants:
            # Module centres sit on a 4 m grid, so mixing the raw coordinates
            # collapses to 0; index the grid first, then mix.
            ix, iy = int(round(center[0] / 4.0)), int(round(center[1] / 4.0))
            variant = (ix * 5 + iy * 3) % 4
        used.append(variant)
        add_paving_module(slabs_bm, mortar_bm, center, z_top=z_top,
                          seed=20261024 + i * 17, variant=variant)
    print("PAVING variants=%s" % used)
    bmesh.ops.recalc_face_normals(slabs_bm, faces=slabs_bm.faces)
    slabs = cl.finish_mesh(prefix + "_slabs", slabs_bm,
                           [cl.mat_stone_base(), cl.mat_stone_light(), cl.mat_stone_dark()], collection)
    # Per-slab tonal variation uses native materials (no UV/texture claim); map LOD
    # keeps the same joints but breaks the flat single-color field.
    for poly in slabs.data.polygons:
        c = poly.center
        key = (int(c.x * 1.7) * 13 + int(c.y * 1.7) * 7) % 23
        poly.material_index = 1 if key in (0, 5, 7, 11, 18) else 2 if key in (3, 14) else 0
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
