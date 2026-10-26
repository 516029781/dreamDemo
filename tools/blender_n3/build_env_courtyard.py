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

def _grow_branch(bm, start, direction, length, r0, r1, depth, rng, tips):
    direction = Vector(direction).normalized()
    bend = Vector((rng.uniform(-0.24, 0.24), rng.uniform(-0.24, 0.24),
                   rng.uniform(0.02, 0.12)))
    mid = start + direction * (length * 0.52)
    end = mid + (direction + bend).normalized() * (length * 0.48)
    cl.add_cylinder(bm, start, mid, r0, (r0 + r1) / 2.0, 8, 0)
    cl.add_cylinder(bm, mid, end, (r0 + r1) / 2.0, r1, 7, 0)
    if depth <= 0:
        tips.append((end, (direction + bend).normalized(), r1))
        return
    child_count = 2
    base_axis = direction.cross(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                                        rng.uniform(0.2, 1.0)))).normalized()
    for i in range(child_count):
        angle = math.radians(rng.uniform(26.0, 44.0))
        axis = (base_axis if i == 0 else
                (base_axis if i % 2 else -base_axis)).normalized()
        child_dir = (direction * math.cos(angle)
                     + axis.cross(direction) * math.sin(angle)
                     + Vector((0, 0, 0.10)))
        child_dir = (child_dir + Vector((rng.uniform(-0.12, 0.12),
                                         rng.uniform(-0.12, 0.12),
                                         rng.uniform(0.02, 0.14)))).normalized()
        _grow_branch(bm, end, child_dir, length * rng.uniform(0.58, 0.70),
                     r1, r1 * 0.55, depth - 1, rng, tips)


def create_tree(collection, origin=(0, 0, 0), rot=0.0, prefix="ENV006",
                seed=20261025):
    rng = random.Random(seed)
    bark_mats = [cl.mat_wood_dark(), cl.mat_wood()]
    leaf_mats = [cl.mat_leaf_ochre(), cl.mat_leaf_amber(),
                 cl.mat_leaf_olive(), cl.mat_leaf_deep()]

    bm = bmesh.new()
    trunk_pts = [(0, 0, 0), (0.05, 0.02, 0.72), (0.11, 0.04, 1.45),
                 (0.10, 0.02, 2.02)]
    radii = [0.34, 0.295, 0.230, 0.175]
    for i in range(3):
        cl.add_cylinder(bm, trunk_pts[i], trunk_pts[i + 1], radii[i],
                        radii[i + 1], 10, 0)
    # Root flare (buttresses).
    for i in range(6):
        a = math.tau * i / 6.0 + 0.2
        p0 = (0.06 * math.cos(a), 0.06 * math.sin(a), 0.50)
        p1 = (0.50 * math.cos(a), 0.50 * math.sin(a), 0.005)
        cl.add_cylinder(bm, p0, p1, 0.11, 0.035, 6, 1)

    tips = []
    fork = Vector((0.10, 0.02, 2.02))
    main_dirs = [(0.62, 0.10, 0.85), (-0.58, 0.36, 0.80),
                 (0.16, -0.62, 0.82), (-0.24, -0.44, 0.90)]
    for i, d in enumerate(main_dirs):
        _grow_branch(bm, fork, d, 1.86, 0.155, 0.055, 3, rng, tips)
    for i, (x, y) in enumerate(((-0.78, 0.30), (0.76, -0.28))):
        start = Vector((0.08 + x * 0.10, 0.03 + y * 0.10, 1.42))
        _grow_branch(bm, start, (x, y, 0.62), 1.22, 0.120, 0.045, 1, rng, tips)

    bark = cl.finish_mesh(prefix + "_bark", bm, bark_mats, collection)
    bpy.ops.object.select_all(action="DESELECT")
    bark.select_set(True)
    bpy.context.view_layer.objects.active = bark
    bpy.ops.object.shade_auto_smooth(angle=math.radians(45.0))
    bark.select_set(False)

    leaf_bm = bmesh.new()
    leaf_count = 0
    cluster_count = 0
    # Weighted warm palette: massed ochre/amber with sparse olive reads as one
    # autumn canopy; the old four-way mix read as confetti.
    warm = [0, 0, 0, 0, 1, 1, 1, 2, 3]
    # Five main lobes + three break-up lobes define the crown volume.  Each
    # lobe carries five smaller leaf clumps (solid micro-mass + cards) so the
    # silhouette has large/medium/small rhythm instead of one smooth boulder.
    lobes = ((-0.75, 0.35, 3.95, 1.30),
             (0.85, -0.45, 3.75, 1.25),
             (0.10, 0.65, 4.62, 1.35),
             (-0.55, -0.75, 4.32, 1.20),
             (0.55, 0.15, 5.18, 1.10))
    break_lobes = ((1.55, 0.55, 4.35, 0.85),
                   (-1.35, -0.25, 4.55, 0.82),
                   (0.25, -1.25, 4.75, 0.78))

    mass_bm = bmesh.new()
    mass_mats = [cl.mat_leaf_mass(), cl.mat_leaf_deep()]
    for i, (x, y, z, r) in enumerate(lobes + break_lobes):
        cl.add_mass_lobe(mass_bm, (x, y, z + 0.08), r * 0.60, rng,
                         flatten=0.72, subdiv=3, displace=0.10,
                         mat_index=0 if i % 3 else 1)
    clump_pattern = ((0.75, 0.12, 0.18), (-0.68, 0.35, 0.22),
                     (0.08, -0.74, 0.28), (-0.22, 0.62, 0.34),
                     (0.58, -0.48, 0.04), (0.25, 0.55, -0.12))
    for i, (x, y, z, r) in enumerate(lobes + break_lobes):
        for (dx, dy, dz) in clump_pattern:
            d = Vector((dx, dy, dz)).normalized()
            jitter = Vector((rng.uniform(-0.10, 0.10),
                             rng.uniform(-0.10, 0.10),
                             rng.uniform(-0.08, 0.08)))
            center = Vector((x, y, z)) + Vector((d.x * r * 0.60,
                                                 d.y * r * 0.60,
                                                 d.z * r * 0.46)) + jitter * r * 0.25
            cr = max(0.30, r * rng.uniform(0.28, 0.36))
            cl.add_mass_lobe(mass_bm, center, cr * 0.86, rng, flatten=0.82,
                             subdiv=3, displace=0.15,
                             mat_index=1 if i % 3 == 0 else 0)
            palette = warm if i % 3 else [1, 1, 2, 3, 0]
            cards = int(rng.uniform(82, 100))
            cl.add_leaf_cluster(leaf_bm, center, cr * 1.07, cards, rng, palette,
                                leaf_size=rng.uniform(0.18, 0.28),
                                shell_inner=0.72, z_min=-0.36)
            cl.add_leaf_cluster(leaf_bm, center, cr * 1.04, 16, rng, [0, 1, 2],
                                leaf_size=0.26, shell_inner=0.92, z_min=0.0)
            leaf_count += cards + 16
            cluster_count += 1
    # A few small outer clusters break the repeated lobe silhouette.
    for (x, y, z, r) in ((1.65, 0.10, 4.15, 0.45), (-1.55, 0.25, 4.25, 0.42),
                         (0.15, -1.55, 4.55, 0.40), (0.30, 1.45, 4.85, 0.38)):
        cl.add_mass_lobe(mass_bm, (x, y, z), r * 0.86, rng, flatten=0.82,
                         subdiv=3, displace=0.15, mat_index=2)
        cl.add_leaf_cluster(leaf_bm, (x, y, z), r * 1.12, 72, rng, warm,
                            leaf_size=0.20, shell_inner=0.58, z_min=-0.30)
        leaf_count += 72
        cluster_count += 1
    # Small clumps at exposed branch tips hide bare stick ends.
    for (end, direction, r1) in tips:
        center = end + direction * 0.08 + Vector((0, 0, 0.04))
        cl.add_mass_lobe(mass_bm, center, 0.26, rng, flatten=0.82, subdiv=2,
                         displace=0.12, mat_index=2)
        cl.add_leaf_cluster(leaf_bm, center, 0.34, 22, rng, warm,
                            leaf_size=0.17, shell_inner=0.55, z_min=-0.40)
        leaf_count += 22
        cluster_count += 1
    # Olive under-layer along the lower crown edge.
    for (x, y, z, r, n) in ((-0.75, 0.35, 3.45, 0.78, 34),
                            (0.85, -0.45, 3.30, 0.70, 32),
                            (0.10, 0.65, 4.05, 0.72, 30),
                            (-0.55, -0.75, 3.85, 0.66, 28)):
        cl.add_leaf_cluster(leaf_bm, (x, y, z), r, n, rng, [2, 3, 1],
                            leaf_size=0.38, shell_inner=0.55, z_min=-0.12)
        leaf_count += n
        cluster_count += 1

    mass = cl.finish_mesh(prefix + "_crown_mass", mass_bm, mass_mats, collection)
    bpy.ops.object.select_all(action="DESELECT")
    mass.select_set(True)
    bpy.context.view_layer.objects.active = mass
    bpy.ops.object.shade_smooth()
    mass.select_set(False)
    canopy = cl.finish_mesh(prefix + "_canopy", leaf_bm, leaf_mats, collection)
    for obj in (canopy, mass):
        obj["occlusion_group"] = "OCC_tree_main"
        obj["asset_id"] = "ENV006"
        cl.set_instance(obj, origin, rot)
    canopy["canopy_clusters"] = cluster_count
    canopy["leaf_count"] = leaf_count
    mass["crown_mass_lobes"] = len(lobes) + 2
    bark["collision"] = "circle radius 0.36 at trunk base"
    bark["canopy_occlusion"] = "OCC_tree_main (hide canopy + crown_mass only)"
    print("ENV006 cluster_count=%d leaf_count=%d mass_faces=%d" % (
        cluster_count, leaf_count, len(mass.data.polygons)))
    return [bark, canopy, mass]


# ---------------------------------------------------------------------------
# ENV007 central ring planter
# ---------------------------------------------------------------------------

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


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    stage = args[0] if args else "curb"
    if stage not in ENV_STAGES:
        raise SystemExit("unknown stage %r (choose from %s)" % (
            stage, ", ".join(ENV_STAGES)))
    deliver(stage, ENV_STAGES[stage])


if __name__ == "__main__":
    main()
