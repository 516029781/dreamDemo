"""
Build the remaining courtyard environment modules as native Blender geometry.

ENV002 curb, ENV003 low wall, ENV004 railing, ENV005 decorative steps,
ENV006 autumn tree, ENV007 central ring planter, ENV008 side planter,
ENV009/010 shrubs, ENV011 dry grass, ENV012 fallen leaves.

Each stage builds one module, saves an uncompressed .blend + GLB (constant PBR
fallbacks), then renders a Cycles CPU studio preview.  All geometry is real and
all materials are procedural; nothing is a generated image or a PNG-as-source.

Run (one stage per process), from the project root:
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/build_env_courtyard.py -- curb

Stages: curb, low_wall, railing, steps, tree, ring_planter, side_planter,
        shrub_a, shrub_b, dry_grass, fallen_leaves
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import courtyard_lib as cl  # noqa: E402


# ---------------------------------------------------------------------------
# ENV002 curb (2.0 m module)
# ---------------------------------------------------------------------------

def create_curb(collection, origin=(0, 0, 0), rot=0.0, prefix="ENV002",
                lod=False):
    light, dark = cl.mat_stone_base(), cl.mat_stone_dark()
    bm = bmesh.new()
    cl.add_box(bm, (0, 0, 0.035), (2.0, 0.36, 0.07), mat_index=1)
    cl.add_box(bm, (-0.505, 0, 0.125), (0.99, 0.28, 0.11), mat_index=0)
    cl.add_box(bm, (0.505, 0, 0.125), (0.99, 0.28, 0.11), mat_index=0)
    obj = cl.finish_mesh(prefix + "_stone", bm, [light, dark], collection)
    if lod:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_auto_smooth(angle=math.radians(30.0))
        obj.select_set(False)
    else:
        cl.add_bevel(obj, width=0.009, segments=2)
    cl.set_instance(obj, origin, rot)
    obj["asset_id"] = "ENV002"
    obj["module_length"] = 2.0
    obj["collision"] = "box 2.0 x 0.36, height 0.18"
    return [obj]


# ---------------------------------------------------------------------------
# ENV003 low wall (4.0 m module, edge closure)
# ---------------------------------------------------------------------------

def create_low_wall(collection, origin=(0, 0, 0), rot=0.0, prefix="ENV003",
                    lod=False):
    base, mortar, light, dark = (cl.mat_stone_base(), cl.mat_mortar(),
                                 cl.mat_stone_light(), cl.mat_stone_dark())
    bm = bmesh.new()
    # Plinth + mortar core.
    cl.add_box(bm, (0, 0, 0.06), (4.0, 0.46, 0.12), mat_index=0)
    cl.add_box(bm, (0, 0, 0.42), (3.98, 0.34, 0.60), mat_index=1)
    # Three block courses, alternating full blocks and half-end courses.
    course_z = (0.21, 0.405, 0.60)
    positions = [
        [(-1.49, 0.96, 0), (-0.49, 0.96, 0), (0.51, 0.96, 0), (1.51, 0.96, 0)],
        [(-1.74, 0.47, 0), (-0.99, 0.96, 0), (0.01, 0.96, 0), (1.01, 0.96, 0),
         (1.74, 0.47, 0)],
        [(-1.49, 0.96, 0), (-0.49, 0.96, 0), (0.51, 0.96, 0), (1.51, 0.96, 0)],
    ]
    for course, z in enumerate(course_z):
        for (x, width, _) in positions[course]:
            shade = 0 if (course + int(round(x * 2)) % 2 == 0) else 2
            cl.add_box(bm, (x, 0, z), (width, 0.36, 0.18), mat_index=shade)
    # Coping.
    cl.add_box(bm, (0, 0, 0.74), (4.04, 0.50, 0.10), mat_index=2)
    obj = cl.finish_mesh(prefix + "_stone", bm, [base, mortar, light, dark],
                         collection)
    cl.add_bevel(obj, width=0.010, segments=1 if lod else 2)
    cl.set_instance(obj, origin, rot)
    obj["asset_id"] = "ENV003"
    obj["module_length"] = 4.0
    obj["collision"] = "box 4.0 x 0.50, height 0.79"
    return [obj]


# ---------------------------------------------------------------------------
# ENV004 railing (2.0 m module)
# ---------------------------------------------------------------------------

def create_railing(collection, origin=(0, 0, 0), rot=0.0, prefix="ENV004",
                   lod=False):
    iron, brass = cl.mat_metal(), cl.mat_metal_brass()
    bm = bmesh.new()
    for x in (-0.965, 0.965):
        cl.add_box(bm, (x, 0, 0.035), (0.16, 0.16, 0.07), mat_index=0)
        cl.add_box(bm, (x, 0, 0.52), (0.07, 0.07, 0.90), mat_index=0)
        cl.add_box(bm, (x, 0, 0.985), (0.10, 0.10, 0.05), mat_index=1)
        # small pyramid cap
        cl.add_cylinder(bm, (x, 0, 1.01), (x, 0, 1.075), 0.055, 0.004, 4, 0)
    cl.add_box(bm, (0, 0, 0.935), (1.94, 0.055, 0.055), mat_index=0)
    cl.add_box(bm, (0, 0, 0.13), (1.90, 0.045, 0.045), mat_index=0)
    balusters = 5 if lod else 9
    for i in range(balusters):
        x = -0.80 + i * (1.60 / (balusters - 1))
        cl.add_box(bm, (x, 0, 0.53), (0.022, 0.022, 0.76), mat_index=0)
    obj = cl.finish_mesh(prefix + "_metal", bm, [iron, brass], collection)
    cl.add_bevel(obj, width=0.0045, segments=1 if lod else 2)
    cl.set_instance(obj, origin, rot)
    obj["asset_id"] = "ENV004"
    obj["module_length"] = 2.0
    obj["collision"] = "box 2.0 x 0.10, height 1.12"
    return [obj]


# ---------------------------------------------------------------------------
# ENV005 decorative steps (landscape only, no floor gameplay)
# ---------------------------------------------------------------------------

def create_steps(collection, origin=(0, 0, 0), rot=0.0, prefix="ENV005",
                 lod=False):
    stone, dark = cl.mat_stone_light(), cl.mat_stone_dark()
    bm = bmesh.new()
    # Three treads; front at y=-0.55, rising toward +Y.  Each tread is a real
    # 0.15 m slab resting on the one below (no hidden stacked solids).
    for i in range(3):
        z0, z1 = 0.15 * i, 0.15 * (i + 1)
        y0, y1 = -0.55 + 0.34 * i, 0.55
        cl.add_box(bm, (0, (y0 + y1) / 2.0, (z0 + z1) / 2.0),
                   (2.40, y1 - y0, 0.15), mat_index=0)
    for x in (-1.26, 1.26):
        cl.add_box(bm, (x, 0.02, 0.22), (0.12, 1.30, 0.44), mat_index=1)
        cl.add_box(bm, (x, 0.02, 0.4575), (0.16, 1.34, 0.035), mat_index=0)
    obj = cl.finish_mesh(prefix + "_stone", bm, [stone, dark], collection)
    cl.add_bevel(obj, width=0.012, segments=1 if lod else 2)
    cl.set_instance(obj, origin, rot)
    obj["asset_id"] = "ENV005"
    obj["landscape_only"] = True
    obj["collision"] = "box 2.64 x 1.34, height 0.49"
    return [obj]


# ---------------------------------------------------------------------------
# ENV006 autumn tree (trunk + branches + layered leaf clusters)
# ---------------------------------------------------------------------------

def _grow_branch(bm, start, direction, length, r0, r1, depth, rng, tips, anchors):
    direction = Vector(direction).normalized()
    p0 = Vector(start)
    side = direction.cross(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                                   rng.uniform(0.2, 1.0)))).normalized()
    bend = side * rng.uniform(0.10, 0.22) + Vector((0, 0, rng.uniform(0.01, 0.06)))
    d1 = (direction + bend * 0.34 + Vector((rng.uniform(-0.04, 0.04),
                                            rng.uniform(-0.04, 0.04), 0.02))).normalized()
    p1 = p0 + (direction * 0.72 + d1 * 0.28).normalized() * (length * 0.34)
    d2 = (d1 + bend * 0.24 + Vector((0, 0, 0.025))).normalized()
    p2 = p1 + d2 * (length * 0.34)
    d3 = (d2 + bend * 0.16 + Vector((rng.uniform(-0.03, 0.03),
                                     rng.uniform(-0.03, 0.03), 0.02))).normalized()
    p3 = p2 + d3 * (length * 0.32)
    radii = [r0, r0 * 0.72 + r1 * 0.28, r0 * 0.38 + r1 * 0.62, r1]
    cl.add_smooth_tube(bm, [p0, p1, p2, p3], radii, segments=8,
                       mat_index=0, ring_noise=0.018, rng=rng)
    if depth <= 0:
        tips.append((p3, d3, r1))
        return
    anchors.append((p3, d3, r1))
    if depth >= 2:
        anchors.append((p2, d2, radii[2]))
    base_axis = direction.cross(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                                        rng.uniform(0.2, 1.0)))).normalized()
    for i in range(2):
        angle = math.radians(rng.uniform(24.0, 44.0))
        axis = (base_axis if i % 2 == 0 else -base_axis).normalized()
        child_dir = (direction * math.cos(angle)
                     + axis.cross(direction) * math.sin(angle)
                     + Vector((0, 0, 0.09)))
        child_dir = (child_dir + Vector((rng.uniform(-0.10, 0.10),
                                         rng.uniform(-0.10, 0.10),
                                         rng.uniform(0.01, 0.12)))).normalized()
        _grow_branch(bm, p3, child_dir, length * rng.uniform(0.58, 0.72),
                     r1, r1 * rng.uniform(0.44, 0.55), depth - 1, rng,
                     tips, anchors)


def _leaf_palette_for(z, radial, rng, leaf_mats):
    """Top/outer sprigs read golden, inner and lower sprigs stay olive."""
    if z > 4.15 or radial > 1.35:
        pool = [0, 0, 4, 1, 2, 0, 4, 3]
    elif z < 3.55:
        pool = [2, 2, 3, 1, 2, 0]
    else:
        pool = [0, 1, 2, 3, 0, 4, 2, 1]
    return [rng.choice(pool) for _ in range(12)]


def _add_leaf_sprig(bark_bm, leaf_bm, anchor, direction, scale, rng,
                    leaf_mats, palette, bare=False, origin="", records=None):
    """A short twig carrying two attached leaf shells with a darker inner shell.

    ``records`` (optional) receives one entry per leaf shell so the A/B/C
    ablation can measure how far each leaf mass sits from a recorded branch
    anchor/tip.  Recording consumes no random numbers.
    """
    anchor = Vector(anchor)
    direction = Vector(direction).normalized()
    side = direction.cross(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0.6))).normalized()
    d0 = (direction + side * rng.uniform(-0.18, 0.18) + Vector((0, 0, 0.035))).normalized()
    bend = side * rng.uniform(0.03, 0.08)
    end = anchor + d0 * (0.40 * scale) + bend * (0.18 * scale)
    cl.add_smooth_tube(bark_bm, [anchor, anchor + d0 * (0.18 * scale),
                                 anchor + d0 * (0.30 * scale) + bend * (0.10 * scale),
                                 end],
                       [0.020 * scale, 0.013 * scale, 0.008 * scale,
                        0.003 * scale],
                       segments=5, mat_index=1, ring_noise=0.04, rng=rng)
    if bare:
        return
    dark = [2, 3, 2, 1]
    for t, cr, bright_count, dark_count, leaf_lo, leaf_hi in (
            (0.17, 0.30, 46, 30, 0.240, 0.310),
            (0.30, 0.190, 23, 15, 0.210, 0.270)):
        center = anchor + d0 * (t * scale) + Vector(
            (rng.uniform(-0.045, 0.045), rng.uniform(-0.045, 0.045),
             rng.uniform(-0.035, 0.035))) * scale
        cl.add_leaf_cluster(leaf_bm, center, cr * 0.92 * scale, dark_count, rng,
                            dark, leaf_size=rng.uniform(0.105, 0.140) * scale,
                            flatten=0.80, shell_inner=0.25, z_min=-0.75)
        if records is not None:
            records.append({"origin": origin, "kind": "sprig_inner",
                            "center": tuple(center),
                            "base": tuple(anchor),
                            "radius": cr * 0.92 * scale,
                            "leaves": dark_count})
        cl.add_leaf_cluster(leaf_bm, center, cr * 1.20 * scale, bright_count, rng,
                            palette, leaf_size=rng.uniform(leaf_lo, leaf_hi) * scale,
                            flatten=0.76, shell_inner=0.40, z_min=-0.65)
        if records is not None:
            records.append({"origin": origin, "kind": "sprig_outer",
                            "center": tuple(center),
                            "base": tuple(anchor),
                            "radius": cr * 1.20 * scale,
                            "leaves": bright_count})


def _add_anchored_cluster(bark_bm, leaf_bm, anchor, direction, scale, rng,
                          leaf_mats, palette, records=None, origin="c_anchor"):
    """Variant C replacement mass: one short twig grown from a real branch
    anchor/tip, carrying a single two-shell leaf cluster aligned with the
    branch direction.  Deliberately lighter than a baseline sprig (38 leaves
    vs 120) so C stays below A in total leaf count."""
    anchor = Vector(anchor)
    direction = Vector(direction).normalized()
    side = direction.cross(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                                   0.6))).normalized()
    d0 = (direction + side * rng.uniform(-0.14, 0.14)
          + Vector((0, 0, 0.05))).normalized()
    end = anchor + d0 * (0.26 * scale)
    cl.add_smooth_tube(bark_bm, [anchor, anchor + d0 * (0.12 * scale), end],
                       [0.016 * scale, 0.008 * scale, 0.003 * scale],
                       segments=5, mat_index=1, ring_noise=0.04, rng=rng)
    center = anchor + d0 * (0.15 * scale)
    cl.add_leaf_cluster(leaf_bm, center, 0.24 * scale, 12, rng,
                        [2, 3, 2, 1], leaf_size=0.115 * scale,
                        flatten=0.80, shell_inner=0.30, z_min=-0.75)
    if records is not None:
        records.append({"origin": origin, "kind": "anchor_inner",
                        "center": tuple(center), "base": tuple(anchor),
                        "radius": 0.24 * scale, "leaves": 12})
    cl.add_leaf_cluster(leaf_bm, center, 0.32 * scale, 26, rng, palette,
                        leaf_size=0.145 * scale, flatten=0.76,
                        shell_inner=0.40, z_min=-0.65)
    if records is not None:
        records.append({"origin": origin, "kind": "anchor_outer",
                        "center": tuple(center), "base": tuple(anchor),
                        "radius": 0.32 * scale, "leaves": 26})


def create_tree(collection, origin=(0, 0, 0), rot=0.0, prefix="ENV006", seed=20261025,
                variant="C", stats_out=None):
    rng = random.Random(seed)
    variant = (variant or "A").upper()
    if variant not in ("A", "B", "C"):
        raise ValueError("unknown tree variant %r (A/B/C)" % variant)
    cluster_records = []
    sprig_counts = {"volume": 0, "tip": 0, "tip_secondary": 0,
                    "anchor": 0, "outer_silhouette": 0, "c_anchor": 0}
    bark_mats = [cl.mat_wood_dark(), cl.mat_wood()]
    leaf_mats = [cl.mat_leaf_atlas()]
    # The inner core must read as shadow inside the canopy. leaf_deep (#746337)
    # is warm enough that smooth-shaded lobes read as bald tan patches, so the
    # core uses the desaturated far tone and is kept small enough for the
    # coating cards to cover it.

    bark_bm = bmesh.new()
    leaf_bm = bmesh.new()
    trunk_pts = [(0.0, 0.0, 0.0), (0.025, 0.012, 0.55),
                 (0.065, 0.030, 1.15), (0.100, 0.022, 1.72),
                 (0.110, 0.015, 2.06)]
    trunk_radii = [0.345, 0.300, 0.235, 0.185, 0.158]
    cl.add_smooth_tube(bark_bm, trunk_pts, trunk_radii, segments=14,
                       mat_index=0, ring_noise=0.022, rng=rng)
    # Root flare: a low collar plus eight real roots that enter the soil.
    cl.add_smooth_tube(bark_bm, [(0, 0, 0.30), (0, 0, 0.13), (0, 0, 0.015)],
                       [0.360, 0.420, 0.480], segments=16, mat_index=0,
                       ring_noise=0.018, rng=rng, cap_start=False)
    for i in range(8):
        a = math.tau * i / 8.0 + rng.uniform(-0.10, 0.10)
        reach = rng.uniform(0.50, 0.72)
        lift = rng.uniform(0.90, 0.98)
        p0 = (0.06 * math.cos(a), 0.06 * math.sin(a), 0.16)
        p1 = (0.20 * math.cos(a), 0.20 * math.sin(a), 0.10)
        p2 = (reach * 0.72 * math.cos(a), reach * 0.72 * math.sin(a), 0.035)
        p3 = (reach * math.cos(a), reach * math.sin(a), -0.015)
        cl.add_smooth_tube(bark_bm, [p0, p1, p2, p3],
                           [0.085 * lift, 0.065, 0.038, 0.012],
                           segments=7, mat_index=1, ring_noise=0.03, rng=rng)
    # Raised bark ridges make the trunk readable instead of a smooth cone.
    for i in range(7):
        a = math.tau * i / 7.0 + 0.12
        pts = []
        radii = []
        for k, (cx, cy, cz) in enumerate(trunk_pts[1:4]):
            idx = k + 1
            rr = trunk_radii[idx] * 1.015
            aa = a + 0.16 * cz
            pts.append((cx + rr * math.cos(aa), cy + rr * math.sin(aa), cz))
            radii.append(0.013)
        cl.add_smooth_tube(bark_bm, pts, radii, segments=5, mat_index=1,
                           ring_noise=0.10, rng=rng)
    # One scarred knot.
    cl.add_mass_lobe(bark_bm, (0.30, -0.16, 1.02), 0.075, rng,
                     flatten=0.55, subdiv=2, displace=0.16, mat_index=1)

    tips = []
    anchors = []
    fork = Vector((0.11, 0.015, 2.06))
    main_dirs = [(0.62, 0.08, 0.80), (-0.55, 0.30, 0.72),
                 (0.10, -0.62, 0.82), (-0.20, -0.40, 0.90),
                 (0.30, 0.55, 0.72), (-0.30, -0.05, 0.94)]
    for d in main_dirs:
        _grow_branch(bark_bm, fork, d, 1.72, 0.140, 0.030, 4, rng, tips, anchors)
    # Mid-canopy branches leave the trunk at different heights so the crown
    # is not a single umbrella fork.
    for (x, y, z, ln) in ((0.86, 0.16, 1.66, 1.38), (-0.78, -0.24, 1.82, 1.30),
                          (0.18, -0.84, 1.52, 1.34), (-0.24, 0.80, 1.74, 1.26)):
        start = Vector((0.06 + x * 0.07, 0.02 + y * 0.07, z))
        _grow_branch(bark_bm, start, (x, y, 0.52), ln, 0.092, 0.026, 3, rng,
                     tips, anchors)
    for (x, y) in ((-0.86, 0.32), (0.84, -0.30)):
        start = Vector((0.06 + x * 0.09, 0.02 + y * 0.09, 1.36))
        _grow_branch(bark_bm, start, (x, y, 0.48), 1.10, 0.070, 0.022, 2, rng,
                     tips, anchors)

    # Inner filler sprigs, distributed through the crown volume.  These are the
    # suspected "leaves with no branch" source: their twig bases are random
    # points inside the crown, not recorded branch anchors/tips.  B/C consume
    # exactly the same random draws into throwaway bmeshes, so every later
    # sprig stays identical to A and only this layer is removed.
    filler_bark = bmesh.new() if variant != "A" else bark_bm
    filler_leaf = bmesh.new() if variant != "A" else leaf_bm
    for i in range(112):
        a = math.tau * i / 112.0 + rng.uniform(-0.26, 0.26)
        r = rng.uniform(0.50, 1.62)
        z = rng.uniform(2.85, 4.70)
        anchor = (r * math.cos(a), r * math.sin(a), z)
        _add_leaf_sprig(filler_bark, filler_leaf, anchor,
                        (math.cos(a), math.sin(a), rng.uniform(0.02, 0.45)),
                        rng.uniform(0.92, 1.28), rng, leaf_mats,
                        _leaf_palette_for(z, r, rng, leaf_mats),
                        bare=(rng.random() < 0.05), origin="volume",
                        records=(cluster_records if variant == "A" else None))
        if variant == "A":
            sprig_counts["volume"] += 1
    if variant != "A":
        filler_bark.free()
        filler_leaf.free()

    # Terminal tips carry the silhouette; a few stay as bare twigs.
    for (pos, d, r1) in tips:
        a = rng.uniform(0.0, math.tau)
        out = Vector((d.x + 0.22 * math.cos(a), d.y + 0.22 * math.sin(a),
                      d.z + rng.uniform(-0.04, 0.22))).normalized()
        z = pos.z
        radial = math.hypot(pos.x, pos.y)
        _add_leaf_sprig(bark_bm, leaf_bm, pos, out,
                        rng.uniform(0.76, 1.05), rng, leaf_mats,
                        _leaf_palette_for(z, radial, rng, leaf_mats),
                        bare=(rng.random() < 0.10), origin="tip",
                        records=cluster_records)
        sprig_counts["tip"] += 1
        if rng.random() < 0.30:
            out2 = Vector((d.x + rng.uniform(-0.5, 0.5),
                           d.y + rng.uniform(-0.5, 0.5),
                           d.z + rng.uniform(0.0, 0.22))).normalized()
            _add_leaf_sprig(bark_bm, leaf_bm, pos, out2,
                            rng.uniform(0.58, 0.80), rng, leaf_mats,
                            _leaf_palette_for(z - 0.2, radial, rng, leaf_mats),
                            origin="tip_secondary", records=cluster_records)
            sprig_counts["tip_secondary"] += 1
    anchor_sprig_indices = set()
    for anchor_idx, (pos, d, r1) in enumerate(anchors):
        if rng.random() > 0.68:
            continue
        anchor_sprig_indices.add(anchor_idx)
        out = Vector((d.x + rng.uniform(-0.3, 0.3),
                      d.y + rng.uniform(-0.3, 0.3),
                      rng.uniform(0.05, 0.45))).normalized()
        _add_leaf_sprig(bark_bm, leaf_bm, pos, out,
                        rng.uniform(0.64, 0.90), rng, leaf_mats,
                        _leaf_palette_for(pos.z, math.hypot(pos.x, pos.y),
                                          rng, leaf_mats),
                        origin="anchor", records=cluster_records)
        sprig_counts["anchor"] += 1

    # n5c: there is no solid interior core any more. The smooth mass lobes were
    # exactly the "green blob" the user saw whenever leaf coverage dropped, so
    # the see-through gaps are now closed with leaf clusters instead: anything
    # the player can see is made of leaves, not a hidden sphere.
    for _ in range(52):
        u = rng.uniform(-1.0, 1.0)
        theta = rng.uniform(0.0, math.tau)
        rr = 0.55 * math.sqrt(max(0.0, 1.0 - u * u))
        pos = (rr * 1.30 * math.cos(theta), rr * 1.30 * math.sin(theta),
               3.86 + u * 0.58)
        cl.add_leaf_cluster(leaf_bm, pos, rng.uniform(0.32, 0.48), 14, rng,
                            [3, 1, 3, 2], leaf_size=rng.uniform(0.18, 0.25),
                            flatten=0.70, shell_inner=0.22, z_min=-0.72)
        cluster_records.append({"origin": "inner", "kind": "inner_shell",
                                "center": pos, "base": pos,
                                "radius": 0.40, "leaves": 10})

    # South-side skirt: the Q03 behind-tree test exposes the crown's lower rim
    # where the character peeks between leaf clusters. Close that band with a
    # dedicated ring biased toward the camera side (+Y in Blender).
    for i in range(20):
        a = math.radians(-115.0 + i * 11.5)
        rr = rng.uniform(0.95, 1.35)
        pos = (rr * math.cos(a), rr * math.sin(a) + 0.25, rng.uniform(2.35, 3.25))
        cl.add_leaf_cluster(leaf_bm, pos, rng.uniform(0.30, 0.44), 12, rng,
                            [3, 1, 2, 3], leaf_size=rng.uniform(0.17, 0.24),
                            flatten=0.62, shell_inner=0.18, z_min=-0.80)
        cluster_records.append({"origin": "south_skirt", "kind": "south_skirt",
                                "center": pos, "base": pos,
                                "radius": 0.38, "leaves": 12})

    # Low bough: the Q03 behind-tree view sees past the bare trunk below the
    # crown, and a real tree of this size carries foliage down to chest height
    # on its shaded side. This also fixes the top-heavy "mushroom" read.
    for i in range(16):
        a = math.radians(150.0 + i * 9.0)
        rr = rng.uniform(0.85, 1.30)
        z = rng.uniform(1.75, 2.55)
        pos = (rr * math.cos(a), rr * math.sin(a) + 0.15, z)
        cl.add_leaf_cluster(leaf_bm, pos, rng.uniform(0.28, 0.42), 12, rng,
                            [1, 3, 2, 1], leaf_size=rng.uniform(0.19, 0.26),
                            flatten=0.58, shell_inner=0.16, z_min=-0.85)
        cluster_records.append({"origin": "low_bough", "kind": "low_bough",
                                "center": pos, "base": pos,
                                "radius": 0.36, "leaves": 12})

    # Inner curtain: the behind-tree view needs the trunk-side band closed
    # without a solid core (the core was the complaint we just removed). Dense
    # overlapping cards read as foliage at every angle the camera can reach.
    for i in range(40):
        a = math.radians(i * 9.0 + rng.uniform(-4.0, 4.0))
        rr = rng.uniform(0.35, 0.85)
        z = rng.uniform(1.95, 3.35)
        pos = (rr * math.cos(a), rr * math.sin(a), z)
        cl.add_leaf_cluster(leaf_bm, pos, rng.uniform(0.30, 0.46), 20, rng,
                            [3, 1, 3, 2, 1], leaf_size=rng.uniform(0.24, 0.32),
                            flatten=0.55, shell_inner=0.10, z_min=-0.90)
        cluster_records.append({"origin": "inner_curtain", "kind": "inner_curtain",
                                "center": pos, "base": pos,
                                "radius": 0.40, "leaves": 20})

    # A few outer silhouette sprigs, still attached by short twigs.
    for (x, y, z, sc) in ((1.85, 0.25, 4.30, 1.22), (-1.75, -0.15, 4.45, 1.18),
                          (0.20, -1.85, 4.55, 1.14), (0.40, 1.75, 4.65, 1.10),
                          (1.35, -1.15, 3.95, 1.06), (-1.25, 1.10, 4.05, 1.04),
                          (0.95, 1.35, 4.35, 1.0), (-0.90, -1.35, 4.35, 1.0),
                          (1.65, 1.00, 3.85, 0.98), (-1.55, -0.95, 3.90, 0.98),
                          (1.95, -0.65, 3.95, 1.06), (-1.90, 0.70, 4.05, 1.04),
                          (0.65, -1.95, 4.20, 1.02), (-0.70, 1.90, 4.25, 1.0)):
        anchor = (x * 0.78, y * 0.78, z - 0.18)
        _add_leaf_sprig(bark_bm, leaf_bm, anchor, (x, y, 0.25),
                        sc, rng, leaf_mats,
                        _leaf_palette_for(z, 1.8, rng, leaf_mats),
                        origin="outer_silhouette", records=cluster_records)
        sprig_counts["outer_silhouette"] += 1

    # Wispy outer layer: bare twigs that poke past the crown edge carrying a
    # few sparse leaves. Without this the silhouette closes into one solid
    # blob; P1's trees stay broken up at the rim.
    for i in range(26):
        a = rng.uniform(0, math.tau)
        zt = rng.uniform(0.15, 0.95)
        rr = math.sqrt(max(0.0, 1.0 - zt * zt))
        outward = Vector((math.cos(a) * rr, math.sin(a) * rr, zt * 0.72)).normalized()
        anchor = Vector((outward.x * 1.28, outward.y * 1.28, 4.05 + outward.z * 1.05))
        reach = rng.uniform(0.34, 0.72)
        tip = anchor + outward * reach + Vector((0, 0, rng.uniform(-0.06, 0.14)))
        cl.add_smooth_tube(bark_bm, [anchor, anchor.lerp(tip, 0.55), tip],
                           [0.016, 0.009, 0.0025], segments=4,
                           mat_index=0, ring_noise=0.03, rng=rng)
        for t in (0.55, 0.82, 1.0):
            p = anchor.lerp(tip, t)
            cr = rng.uniform(0.13, 0.20)
            cnt = rng.randint(5, 9)
            cl.add_leaf_cluster(leaf_bm, p, cr,
                                cnt, rng,
                                _leaf_palette_for(p.z, 1.4, rng, leaf_mats),
                                leaf_size=rng.uniform(0.170, 0.240),
                                flatten=0.62, shell_inner=0.30, z_min=-0.70)
            cluster_records.append({"origin": "wispy", "kind": "wispy_leaf",
                                    "center": tuple(p), "base": tuple(anchor),
                                    "radius": cr, "leaves": cnt})

    # Variant C: after removing the random volume fill, put a modest number of
    # lighter clusters back on real recorded branch anchors (not on tips that
    # already carry a sprig).  Each cluster gets its own short twig along the
    # branch direction, so its leaves inherit a visible support path.
    if variant == "C":
        crng = random.Random(seed + 7)
        candidates = [a for i, a in enumerate(anchors)
                      if i not in anchor_sprig_indices]
        # Prefer lower anchors: with an even shuffle the foliage collects at the
        # top and the crown reads mushroom-shaped over a bare branch skirt.
        low = [a for a in candidates if a[0].z <= 3.55]
        high = [a for a in candidates if a[0].z > 3.55]
        crng.shuffle(low)
        crng.shuffle(high)
        candidates = low + high
        selected = []
        for (pos, d, r1) in candidates:
            if len(selected) >= 84:
                break
            if any((Vector(pos) - Vector(s[0])).length < 0.42 for s in selected):
                continue
            selected.append((pos, d, r1))
        for (pos, d, r1) in selected:
            z = pos.z
            radial = math.hypot(pos.x, pos.y)
            scale = crng.uniform(0.68, 0.95)
            _add_anchored_cluster(
                bark_bm, leaf_bm, pos, d, scale, crng, leaf_mats,
                _leaf_palette_for(z, radial, crng, leaf_mats),
                records=cluster_records)
            sprig_counts["c_anchor"] += 1

    if stats_out is not None:
        stats_out.update({
            "variant": variant,
            "seed": seed,
            "tips": [tuple(p) for (p, _d, _r) in tips],
            "anchors": [tuple(p) for (p, _d, _r) in anchors],
            "sprig_counts": dict(sprig_counts),
            "volume_sprigs_skipped": 112 if variant != "A" else 0,
            "leaf_clusters": len(cluster_records),
            "leaf_cards": sum(r["leaves"] for r in cluster_records),
            "cluster_records": cluster_records,
        })

    if cl.STYLE == "c":
        # Cartoon crown: a dome of overlapping lobes instead of 84 small tip
        # clusters. Blobbing every cluster leaves the branch skeleton visible
        # (the first pass looked like a dead tree), so the crown has to be built
        # as volume.
        # 2026-10-27: the first dome was seven lobes of r=1.0-1.55 at fixed
        # offsets. Seven spheres of that size cannot overlap enough to read as
        # one canopy, so each one kept a hard silhouette and the crown looked
        # like a pile of orange boulders. Eleven smaller, deliberately
        # interpenetrating lobes (squashed to 0.72) close the volume and the
        # outline becomes a wide lozenge, which is what the reference shows.
        crown_center = (0.0, 0.0, 4.62)
        crown_lobes = [(0.0, 0.0, 0.16, 1.24)]
        for i in range(6):
            a = math.tau * i / 6.0 + 0.25
            crown_lobes.append((math.cos(a) * 1.16, math.sin(a) * 1.16,
                                -0.28, 1.02))
        for i in range(4):
            a = math.tau * i / 4.0 + 0.9
            crown_lobes.append((math.cos(a) * 0.64, math.sin(a) * 0.64,
                                0.52, 0.96))
        for (dx, dy, dz, lr) in crown_lobes:
            cl.add_mass_lobe(
                leaf_bm,
                (crown_center[0] + dx, crown_center[1] + dy,
                 crown_center[2] + dz),
                lr, crng, flatten=0.72, subdiv=1, displace=0.13, mat_index=0)

    bark = cl.finish_mesh(prefix + "_bark", bark_bm, bark_mats, collection)
    bpy.ops.object.select_all(action="DESELECT")
    bark.select_set(True)
    bpy.context.view_layer.objects.active = bark
    bpy.ops.object.shade_smooth()
    bark.select_set(False)

    canopy = cl.finish_mesh(prefix + "_canopy", leaf_bm, leaf_mats, collection)
    for obj in (canopy,):
        obj["occlusion_group"] = "OCC_tree_main"
        obj["asset_id"] = "ENV006"
        cl.set_instance(obj, origin, rot)
    for obj in (bark, canopy):
        obj.scale = (0.94, 0.94, 0.94)
    bark["collision"] = "circle radius 0.36 at trunk base"
    bark["canopy_occlusion"] = "OCC_tree_main (hide canopy only; no solid core)"
    print("ENV006 sprig_tree tips=%d anchors=%d" % (len(tips), len(anchors)))
    return [bark, canopy]


def create_ring_planter(collection, origin=(0, 0, 0), rot=0.0, prefix="ENV007"):
    stone, light, dark, soil = (cl.mat_stone_base(), cl.mat_stone_light(),
                               cl.mat_stone_dark(), cl.mat_soil())
    bm = bmesh.new()
    # 18 curved stone blocks with 1-degree joints.
    # Smooth stone drum with shallow vertical joints and two course lines.
    cl.add_solid_ring(bm, 1.55, 2.02, 0.07, 0.55, segments=96, mat_index=0)
    for i in range(12):
        a = math.radians(360.0 * i / 12.0)
        sx, sy = 2.015 * math.cos(a), 2.015 * math.sin(a)
        cl.add_box(bm, (sx, sy, 0.31), (0.020, 0.030, 0.46),
                   rot_deg=(0, 0, math.degrees(a) + 90.0), mat_index=2)
    for z in (0.235, 0.385):
        cl.add_solid_ring(bm, 2.018, 2.028, z - 0.006, z + 0.006,
                          segments=96, mat_index=2)
    blocks = cl.finish_mesh(prefix + "_blocks", bm, [stone, light, dark], collection)
    cl.add_bevel(blocks, width=0.004, segments=2)
    plinth_bm = bmesh.new()
    cl.add_solid_ring(plinth_bm, 1.50, 2.07, 0.0, 0.08, segments=96, mat_index=0)
    plinth = cl.finish_mesh(prefix + "_plinth", plinth_bm, [dark], collection)
    cl.add_bevel(plinth, width=0.006, segments=2)

    cap_bm = bmesh.new()
    cl.add_solid_ring(cap_bm, 1.58, 2.08, 0.55, 0.63, segments=96, mat_index=0)
    cap = cl.finish_mesh(prefix + "_cap", cap_bm, [light], collection)
    cl.add_bevel(cap, width=0.008, segments=2)

    soil_bm = bmesh.new()
    cl.add_cylinder(soil_bm, (0, 0, 0.10), (0, 0, 0.615), 1.60, 1.60, 36, 0)
    soil_obj = cl.finish_mesh(prefix + "_soil", soil_bm, [soil], collection)
    bpy.ops.object.select_all(action="DESELECT")
    soil_obj.select_set(True)
    bpy.context.view_layer.objects.active = soil_obj
    bpy.ops.object.shade_auto_smooth(angle=math.radians(40.0))
    soil_obj.select_set(False)

    objs = [blocks, plinth, cap, soil_obj]
    for obj in objs:
        cl.set_instance(obj, origin, rot)
        obj["asset_id"] = "ENV007"
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth()
        obj.select_set(False)
    blocks["collision"] = "circle radius 2.08 centred at origin"
    blocks["path_note"] = "ring walkway outside radius 2.08"
    return objs


# ---------------------------------------------------------------------------
# ENV008 side planter
# ---------------------------------------------------------------------------

def create_side_planter(collection, origin=(0, 0, 0), rot=0.0, prefix="ENV008"):
    stone, light, dark, soil = (cl.mat_stone_base(), cl.mat_stone_light(),
                               cl.mat_stone_dark(), cl.mat_soil())
    bm = bmesh.new()
    cl.add_box(bm, (0, 0, 0.035), (3.24, 1.44, 0.07), mat_index=2)
    cl.add_box(bm, (0, 0, 0.23), (3.12, 1.32, 0.32), mat_index=0)
    for course, z in enumerate((0.07 + 0.08, 0.07 + 0.24)):
        for y in (-0.60, 0.60):
            for i in range(4):
                x = -1.17 + i * 0.78
                cl.add_box(bm, (x, y, z), (0.76, 0.20, 0.155),
                           mat_index=1 if (i + course) % 2 == 0 else 0)
        for x in (-1.50, 1.50):
            cl.add_box(bm, (x, 0, z), (0.20, 0.98, 0.155),
                       mat_index=1 if course % 2 == 0 else 0)
    # Cap stones.
    for y in (-0.60, 0.60):
        cl.add_box(bm, (0, y, 0.435), (3.28, 0.28, 0.09), mat_index=1)
    for x in (-1.50, 1.50):
        cl.add_box(bm, (x, 0, 0.435), (0.28, 1.02, 0.09), mat_index=1)
    obj = cl.finish_mesh(prefix + "_stone", bm, [stone, light, dark], collection)
    cl.add_bevel(obj, width=0.008, segments=2)

    soil_bm = bmesh.new()
    cl.add_box(soil_bm, (0, 0, 0.22), (2.98, 1.18, 0.38), mat_index=0)
    soil_obj = cl.finish_mesh(prefix + "_soil", soil_bm, [soil], collection)

    objs = [obj, soil_obj]
    for o in objs:
        cl.set_instance(o, origin, rot)
        o["asset_id"] = "ENV008"
    obj["collision"] = "box 3.28 x 1.48, height 0.48"
    return objs


# ---------------------------------------------------------------------------
# ENV009 / ENV010 shrubs
# ---------------------------------------------------------------------------

def _create_shrub(collection, prefix, origin, rot, seed, clusters, stems,
                  base_radius, height, leaf_size, leaf_mats, palette):
    rng = random.Random(seed)
    bark_bm = bmesh.new()
    for i in range(stems):
        a = math.tau * i / stems + rng.uniform(-0.3, 0.3)
        r = base_radius * rng.uniform(0.25, 0.55)
        p0 = (r * 0.4 * math.cos(a), r * 0.4 * math.sin(a), -0.02)
        p1 = (r * math.cos(a), r * math.sin(a),
              height * rng.uniform(0.55, 0.80))
        cl.add_cylinder(bark_bm, p0, p1, 0.018, 0.008, 6, 0)
    bark = cl.finish_mesh(prefix + "_stems", bark_bm, [cl.mat_wood_dark()],
                          collection)
    bpy.ops.object.select_all(action="DESELECT")
    bark.select_set(True)
    bpy.context.view_layer.objects.active = bark
    bpy.ops.object.shade_auto_smooth(angle=math.radians(45.0))
    bark.select_set(False)

    # Weighted warm palette: massed autumn reads as one bush, uniform random
    # four-way mix reads as scattered seedlings.
    leaf_bm = bmesh.new()
    for (dx, dy, dz, r, count) in clusters:
        center = (dx * base_radius, dy * base_radius, height * 0.55 + dz)
        cl.add_leaf_cluster(
            leaf_bm, center, r, count, rng, palette, leaf_size=leaf_size,
            flatten=rng.uniform(0.7, 0.95), shell_inner=0.32)
        cl.add_leaf_cluster(
            leaf_bm, center, r * 0.92, max(14, int(count * 0.55)), rng, palette,
            leaf_size=leaf_size * 1.5, flatten=rng.uniform(0.75, 1.0),
            shell_inner=0.55)
    leaves = cl.finish_mesh(prefix + "_leaves", leaf_bm, leaf_mats, collection)
    leaves["occlusion_group"] = "OCC_" + prefix.lower()

    for obj in (bark, leaves):
        cl.set_instance(obj, origin, rot)
        obj["asset_id"] = prefix.upper()
    bark["collision"] = "circle radius %.2f" % base_radius
    return [bark, leaves]


def create_shrub_a(collection, origin=(0, 0, 0), rot=0.0, prefix="ENV009"):
    leaf_mats = [cl.mat_leaf_ochre(), cl.mat_leaf_amber(), cl.mat_leaf_olive(),
                 cl.mat_leaf_deep()]
    return _create_shrub(
        collection, prefix, origin, rot, 9001,
        clusters=[(0.30, 0.10, 0.08, 0.40, 78), (-0.28, 0.16, 0.00, 0.38, 74),
                  (0.02, -0.32, 0.04, 0.40, 76), (0.0, 0.0, 0.24, 0.44, 70),
                  (0.12, 0.18, -0.10, 0.34, 52)],
        stems=5, base_radius=0.50, height=0.92, leaf_size=0.26,
        leaf_mats=leaf_mats, palette=[0, 0, 0, 1, 1, 2, 3])


def create_shrub_b(collection, origin=(0, 0, 0), rot=0.0, prefix="ENV010"):
    leaf_mats = [cl.mat_leaf_amber(), cl.mat_leaf_ochre(), cl.mat_leaf_olive(),
                 cl.mat_leaf_deep()]
    return _create_shrub(
        collection, prefix, origin, rot, 9002,
        clusters=[(0.42, 0.05, 0.00, 0.48, 84), (-0.40, 0.18, 0.06, 0.46, 80),
                  (0.05, -0.44, 0.02, 0.46, 78), (0.0, 0.05, 0.38, 0.50, 72),
                  (-0.10, -0.05, 0.08, 0.42, 62), (0.18, 0.30, -0.16, 0.36, 50)],
        stems=6, base_radius=0.62, height=1.12, leaf_size=0.28,
        leaf_mats=leaf_mats, palette=[1, 1, 1, 0, 0, 2, 3])


# ---------------------------------------------------------------------------
# ENV011 dry grass clump
# ---------------------------------------------------------------------------

def create_dry_grass(collection, origin=(0, 0, 0), rot=0.0, prefix="ENV011"):
    rng = random.Random(11011)
    mats = [cl.mat_grass_dry(), cl.mat_grass_pale(), cl.mat_leaf_ochre()]
    bm = bmesh.new()

    def ribbon(base, lean, height, width, mat_index, segments=4):
        pts = []
        for s in range(segments + 1):
            t = s / segments
            pts.append(Vector((base.x + lean.x * t * t,
                               base.y + lean.y * t * t,
                               base.z + height * t)))
        left, right = [], []
        for s in range(segments):
            p = pts[s]
            w = width * (1.0 - s / segments) * 0.5
            left.append(bm.verts.new((p.x - w, p.y, p.z)))
            right.append(bm.verts.new((p.x + w, p.y, p.z)))
        for s in range(segments - 1):
            f = bm.faces.new((left[s], right[s], right[s + 1], left[s + 1]))
            f.material_index = mat_index
        tip = bm.verts.new(tuple(pts[segments]))
        f = bm.faces.new((left[-1], right[-1], tip))
        f.material_index = mat_index

    for i in range(120):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.0, 0.30)
        base = Vector((r * math.cos(a), r * math.sin(a), 0.0))
        lean = Vector((rng.uniform(-0.16, 0.16), rng.uniform(-0.16, 0.16),
                       rng.uniform(0.03, 0.12)))
        ribbon(base, lean, rng.uniform(0.30, 0.68), rng.uniform(0.010, 0.020),
               rng.choice([0, 1, 2]))
    # Seed heads.
    for i in range(18):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.05, 0.26)
        base = Vector((r * math.cos(a), r * math.sin(a), 0.0))
        top = base + Vector((rng.uniform(-0.10, 0.10), rng.uniform(-0.10, 0.10),
                             rng.uniform(0.40, 0.62)))
        cl.add_cylinder(bm, base, top, 0.004, 0.002, 4, 1)
        tip_dir = Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 1.0))
        cl.add_leaf(bm, top, tip_dir, 0.055, rng.uniform(0, math.tau), 0)

    obj = cl.finish_mesh(prefix + "_clump", bm, mats, collection)
    cl.set_instance(obj, origin, rot)
    obj["asset_id"] = "ENV011"
    obj["collision"] = "none (ground cover)"
    return [obj]


# ---------------------------------------------------------------------------
# ENV012 fallen leaves cluster
# ---------------------------------------------------------------------------

def create_fallen_leaves(collection, origin=(0, 0, 0), rot=0.0,
                         prefix="ENV012", seed=12012):
    rng = random.Random(seed)
    mats = [cl.mat_leaf_ochre(), cl.mat_leaf_amber(), cl.mat_leaf_deep(),
            cl.mat_leaf_olive()]
    bm = bmesh.new()
    for i in range(94):
        a = rng.uniform(0, math.tau)
        r = 0.55 * math.sqrt(rng.uniform(0.0, 1.0))
        center = Vector((r * math.cos(a), r * math.sin(a),
                         0.004 + rng.uniform(0.0, 0.012)))
        normal = Vector((rng.uniform(-0.22, 0.22), rng.uniform(-0.22, 0.22), 1.0))
        cl.add_leaf(bm, center, normal, rng.uniform(0.070, 0.118),
                    rng.uniform(0, math.tau), rng.choice([0, 1, 2, 3]),
                    tilt=rng.uniform(-0.25, 0.25))
    # Two fallen twigs.
    for i in range(2):
        p0 = Vector((rng.uniform(-0.35, 0.35), rng.uniform(-0.35, 0.35), 0.012))
        p1 = p0 + Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.25, 0.25), 0.0))
        cl.add_cylinder(bm, p0, p1, 0.010, 0.006, 5, 0)
    obj = cl.finish_mesh(prefix + "_leaves", bm, mats, collection)
    cl.set_instance(obj, origin, rot)
    obj["asset_id"] = "ENV012"
    obj["collision"] = "none (ground detail)"
    return [obj]


# ---------------------------------------------------------------------------
# Delivery wrapper
# ---------------------------------------------------------------------------

ENV_STAGES = {
    "curb": {
        "id": "ENV002", "name": "ENV002_curb", "folder": "environment",
        "builder": create_curb, "target": (0, 0, 0.09), "distance": 3.3,
        "elevation": 30.0, "resolution": (1000, 700), "samples": 48,
        "objects_note": "2.0 x 0.30 x 0.18 m curb module",
    },
    "low_wall": {
        "id": "ENV003", "name": "ENV003_low_wall", "folder": "environment",
        "builder": create_low_wall, "target": (0, 0, 0.42), "distance": 8.2,
        "elevation": 20.0, "resolution": (1100, 700), "samples": 48,
        "objects_note": "4.0 x 0.50 x 0.79 m low wall module",
    },
    "railing": {
        "id": "ENV004", "name": "ENV004_railing", "folder": "environment",
        "builder": create_railing, "target": (0, 0, 0.58), "distance": 5.4,
        "elevation": 16.0, "resolution": (1000, 760), "samples": 48,
        "objects_note": "2.0 x 0.16 x 1.10 m railing module",
    },
    "steps": {
        "id": "ENV005", "name": "ENV005_steps", "folder": "environment",
        "builder": create_steps, "target": (0, 0, 0.24), "distance": 5.6,
        "elevation": 22.0, "resolution": (1000, 760), "samples": 48,
        "objects_note": "2.64 x 1.34 x 0.49 m decorative steps",
    },
    "tree": {
        "id": "ENV006", "name": "ENV006_autumn_tree", "folder": "environment",
        "builder": create_tree, "target": (0, 0, 2.55), "distance": 13.5,
        "elevation": 10.0, "resolution": (1000, 900), "samples": 64,
        "objects_note": "5.4 m autumn tree; canopy in OCC_tree_main",
        "ground_color": "#B9B1A2",
    },
    "ring_planter": {
        "id": "ENV007", "name": "ENV007_ring_planter", "folder": "environment",
        "builder": create_ring_planter, "target": (0, 0, 0.28), "distance": 6.8,
        "elevation": 26.0, "resolution": (1000, 800), "samples": 52,
        "objects_note": "4.16 m diameter ring planter, height 0.63 m",
    },
    "side_planter": {
        "id": "ENV008", "name": "ENV008_side_planter", "folder": "environment",
        "builder": create_side_planter, "target": (0, 0, 0.24), "distance": 6.2,
        "elevation": 27.0, "resolution": (1000, 780), "samples": 52,
        "objects_note": "3.28 x 1.48 x 0.48 m side planter",
    },
    "shrub_a": {
        "id": "ENV009", "name": "ENV009_shrub_a", "folder": "plants",
        "builder": create_shrub_a, "target": (0, 0, 0.46), "distance": 3.4,
        "elevation": 20.0, "resolution": (900, 760), "samples": 44,
        "objects_note": "~1.0 m shrub A",
    },
    "shrub_b": {
        "id": "ENV010", "name": "ENV010_shrub_b", "folder": "plants",
        "builder": create_shrub_b, "target": (0, 0, 0.55), "distance": 4.0,
        "elevation": 20.0, "resolution": (900, 760), "samples": 44,
        "objects_note": "~1.3 m shrub B",
    },
    "dry_grass": {
        "id": "ENV011", "name": "ENV011_dry_grass", "folder": "plants",
        "builder": create_dry_grass, "target": (0, 0, 0.24), "distance": 1.9,
        "elevation": 24.0, "resolution": (900, 760), "samples": 44,
        "objects_note": "~0.55 m dry grass clump",
    },
    "fallen_leaves": {
        "id": "ENV012", "name": "ENV012_fallen_leaves", "folder": "plants",
        "builder": create_fallen_leaves, "target": (0, 0, 0.03), "distance": 2.4,
        "elevation": 38.0, "resolution": (900, 760), "samples": 44,
        "objects_note": "~1.0 m fallen leaf cluster (real geometry)",
    },
}


def deliver(stage_key, cfg):
    cl.reset_scene()
    collection = bpy.context.scene.collection
    objects = cfg["builder"](collection, (0, 0, 0), 0.0, cfg["name"])
    facts = cl.print_module_facts(cfg["name"], objects)
    print("STAGE %s asset_id=%s note=%s" % (stage_key, cfg["id"],
                                            cfg["objects_note"]))

    src_dir = cl.SRC_PLANT if cfg["folder"] == "plants" else cl.SRC_ENV
    prev_dir = cl.PREVIEW_PLANT if cfg["folder"] == "plants" else cl.PREVIEW_ENV
    blend = os.path.join(src_dir, cfg["name"] + ".blend")
    glb = os.path.join(src_dir, cfg["name"] + ".glb")
    png = os.path.join(prev_dir, cfg["name"] + ".png")

    cl.save_blend(blend)
    cl.export_glb(objects, glb)
    cl.setup_studio(target=cfg["target"], distance=cfg["distance"],
                    elevation_deg=cfg["elevation"], fov_deg=35.0,
                    resolution=cfg["resolution"], samples=cfg["samples"],
                    ground_color=cfg.get("ground_color", "#C9C2B4"))
    cl.render_to(png)
    print("DELIVERED %s blend=%s glb=%s png=%s tris=%d" % (
        cfg["id"], blend, glb, png, facts["triangles"]))


# ---------------------------------------------------------------------------
# A/B/C tree ablation previews (candidate_n5, agent E)
# ---------------------------------------------------------------------------

AGENT_DIR = os.path.join(cl.PROJECT, "delivery", "next_cycle", "n5", "agent_e")
TREE_ABLATION_PREVIEWS = os.path.join(cl.PREVIEW_ENV, "tree_ablation")
FLOATING_GAP_M = 0.30
BASE_GAP_M = 0.15


def _place_camera(cam, target, distance, elevation_deg, azimuth_deg):
    az = math.radians(azimuth_deg)
    elev = math.radians(elevation_deg)
    cam.location = Vector((
        target[0] + distance * math.cos(elev) * math.sin(az),
        target[1] - distance * math.cos(elev) * math.cos(az),
        target[2] + distance * math.sin(elev) + 0.02,
    ))
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _set_world(scene, color, strength):
    world = scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*color, 1.0)
    bg.inputs["Strength"].default_value = strength


def _flat_black_material():
    mat = bpy.data.materials.new("MAT_ablation_silhouette")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    em.inputs["Strength"].default_value = 0.0
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def _render_variant_views(variant, objects, out_dir):
    scene = bpy.context.scene
    cfg = ENV_STAGES["tree"]
    cl.ensure_dir(out_dir)
    cl.setup_studio(target=cfg["target"], distance=cfg["distance"],
                    elevation_deg=cfg["elevation"], fov_deg=35.0,
                    resolution=cfg["resolution"], samples=cfg["samples"],
                    ground_color=cfg.get("ground_color", "#C9C2B4"))
    cam = scene.camera
    paths = {}

    # 1. Normal shaded studio view (same camera as the integrator's build).
    paths["normal_studio"] = os.path.join(
        out_dir, "%s_normal_studio.png" % variant)
    cl.render_to(paths["normal_studio"])

    # 2. Gameplay distance: same FOV as the map camera, tree small in frame.
    _place_camera(cam, (0, 0, 0.80), 33.0, 45.0, 0.0)
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.cycles.samples = 48
    paths["gameplay"] = os.path.join(out_dir, "%s_gameplay.png" % variant)
    cl.render_to(paths["gameplay"])

    # 3. Branch-line closeup: hide leaf canopy and crown mass; lighter world so
    #    the trunk -> branch taper is readable.
    bark, canopy, mass = objects
    canopy.hide_render = True
    mass.hide_render = True
    ground = bpy.data.objects.get("PREVIEW_ground")
    if ground is not None:
        ground.hide_render = True
    _set_world(scene, (0.62, 0.60, 0.56), 0.90)
    _place_camera(cam, (0, 0, 2.35), 8.2, 6.0, 32.0)
    scene.render.resolution_x, scene.render.resolution_y = 1000, 900
    paths["branch_only"] = os.path.join(
        out_dir, "%s_branch_only.png" % variant)
    cl.render_to(paths["branch_only"])

    # 4. Flat black silhouette against pure white: the studio camera, all leaf
    #    and bark geometry included, no ground plane.
    canopy.hide_render = False
    mass.hide_render = False
    black = _flat_black_material()
    for obj in (bark, canopy, mass):
        for slot in obj.material_slots:
            slot.material = black
    _set_world(scene, (1.0, 1.0, 1.0), 1.0)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.cycles.samples = 8
    _place_camera(cam, cfg["target"], cfg["distance"], cfg["elevation"], 32.0)
    scene.render.resolution_x, scene.render.resolution_y = 1000, 900
    paths["silhouette"] = os.path.join(out_dir, "%s_silhouette.png" % variant)
    cl.render_to(paths["silhouette"])
    return paths


def _median(values):
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def _p90(values):
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[int(round(0.9 * (len(ordered) - 1)))]


def _score_clusters(stats):
    support = [Vector(p) for p in stats["tips"]] + [Vector(p) for p in stats["anchors"]]
    by_origin = {}
    for rec in stats["cluster_records"]:
        center = Vector(rec["center"])
        nearest = min((center - p).length for p in support)
        gap = nearest - float(rec["radius"])
        rec["nearest_support_m"] = round(nearest, 4)
        rec["support_gap_m"] = round(gap, 4)
        rec["floating"] = gap > FLOATING_GAP_M
        base = Vector(rec.get("base", rec["center"]))
        base_gap = min((base - p).length for p in support)
        rec["base_support_gap_m"] = round(base_gap, 4)
        rec["unsupported_origin"] = base_gap > BASE_GAP_M
        bucket = by_origin.setdefault(rec["origin"], {
            "clusters": 0, "leaves": 0, "floating": 0,
            "unsupported_origin": 0, "gaps": [], "base_gaps": []})
        bucket["clusters"] += 1
        bucket["leaves"] += int(rec["leaves"])
        bucket["floating"] += 1 if rec["floating"] else 0
        bucket["unsupported_origin"] += 1 if rec["unsupported_origin"] else 0
        bucket["gaps"].append(gap)
        bucket["base_gaps"].append(base_gap)
    for bucket in by_origin.values():
        gaps = bucket.pop("gaps")
        base_gaps = bucket.pop("base_gaps")
        bucket["median_gap_m"] = round(_median(gaps), 4)
        bucket["p90_gap_m"] = round(_p90(gaps), 4)
        bucket["median_base_gap_m"] = round(_median(base_gaps), 4)
        bucket["p90_base_gap_m"] = round(_p90(base_gaps), 4)
    floating = [r for r in stats["cluster_records"] if r["floating"]]
    unsupported = [r for r in stats["cluster_records"] if r["unsupported_origin"]]
    stats["floating_proxy"] = {
        "definition": ("floating when nearest recorded anchor/tip minus cluster "
                       "radius exceeds %.2f m (cluster sphere does not reach the "
                       "support ball)" % FLOATING_GAP_M),
        "threshold_m": FLOATING_GAP_M,
        "clusters_total": len(stats["cluster_records"]),
        "clusters_floating": len(floating),
        "clusters_floating_pct": round(
            100.0 * len(floating) / max(1, len(stats["cluster_records"])), 2),
        "floating_by_origin": {
            origin: sum(1 for r in floating if r["origin"] == origin)
            for origin in sorted({r["origin"] for r in floating})},
        "origin_base_threshold_m": BASE_GAP_M,
        "clusters_with_unsupported_origin": len(unsupported),
        "unsupported_origin_by_origin": {
            origin: sum(1 for r in unsupported if r["origin"] == origin)
            for origin in sorted({r["origin"] for r in unsupported})},
        "by_origin": by_origin,
    }


def run_tree_ablation(variant, stats_only=False):
    cfg = ENV_STAGES["tree"]
    cl.ensure_dir(AGENT_DIR)
    cl.ensure_dir(TREE_ABLATION_PREVIEWS)
    cl.reset_scene()
    stats = {}
    prefix = "ENV006_%s" % variant
    objects = create_tree(bpy.context.scene.collection, (0, 0, 0), 0.0,
                          prefix, seed=20261025, variant=variant,
                          stats_out=stats)
    facts = cl.print_module_facts(prefix, objects)
    stats["facts"] = facts
    stats["triangles_by_object"] = {o.name: cl.object_triangles(o) for o in objects}
    stats["triangles"] = facts["triangles"]
    stats["canopy_triangles"] = stats["triangles_by_object"].get(
        prefix + "_canopy", 0)
    _score_clusters(stats)

    blend = os.path.join(AGENT_DIR, "source", prefix + "_variant_%s.blend" % variant)
    glb = os.path.join(AGENT_DIR, "source", prefix + "_variant_%s.glb" % variant)
    cl.save_blend(blend)
    cl.export_glb(objects, glb)
    stats["source_blend"] = blend.replace("\\", "/")
    stats["source_glb"] = glb.replace("\\", "/")

    stats["camera"] = {
        "studio": {"target": list(cfg["target"]), "distance": cfg["distance"],
                   "elevation_deg": cfg["elevation"], "azimuth_deg": 32.0,
                   "fov_deg": 35.0, "resolution": list(cfg["resolution"]),
                   "samples": cfg["samples"]},
        "gameplay": {"target": [0, 0, 0.80], "distance": 33.0,
                     "elevation_deg": 45.0, "azimuth_deg": 0.0,
                     "fov_deg": 35.0, "resolution": [1280, 720]},
        "branch_only": {"target": [0, 0, 2.35], "distance": 8.2,
                        "elevation_deg": 6.0, "azimuth_deg": 32.0,
                        "fov_deg": 35.0, "resolution": [1000, 900]},
        "silhouette": {"target": list(cfg["target"]), "distance": cfg["distance"],
                       "elevation_deg": cfg["elevation"], "azimuth_deg": 32.0,
                       "fov_deg": 35.0, "resolution": [1000, 900]},
    }

    if stats_only:
        stats["renders"] = {}
    else:
        stats["renders"] = _render_variant_views(
            variant, objects, TREE_ABLATION_PREVIEWS)

    stats_path = os.path.join(AGENT_DIR, "stats_%s.json" % variant)
    cl.write_json(stats_path, stats)
    print("ABLATION variant=%s leaf_cards=%d leaf_clusters=%d tris=%d "
          "floating=%d/%d" % (
              variant, stats["leaf_cards"], stats["leaf_clusters"],
              stats["triangles"],
              stats["floating_proxy"]["clusters_floating"],
              stats["floating_proxy"]["clusters_total"]))


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    stage = args[0] if args else "curb"
    if stage not in ENV_STAGES:
        raise SystemExit("unknown stage %r (choose from %s)" % (
            stage, ", ".join(ENV_STAGES)))
    variant = None
    if "--variant" in args:
        variant = args[args.index("--variant") + 1].upper()
    stats_only = "--stats-only" in args
    if variant:
        if stage != "tree":
            raise SystemExit("--variant is only supported for the tree stage")
        run_tree_ablation(variant, stats_only=stats_only)
    else:
        deliver(stage, ENV_STAGES[stage])


if __name__ == "__main__":
    main()
