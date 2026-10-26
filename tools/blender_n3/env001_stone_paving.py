"""
ENV001 stone paving module (native Blender geometry, A0 slice).

4.0 x 4.0 world-unit module, top surface z=0.14, origin at module base centre.
Rows alternate long (0.98) and short (0.48) slabs on a 1.0 m joint grid; edge
joints are half-width (0.01) so two modules butt into a full 0.02 joint.
Slabs are real 0.10-thick boxes with a live->applied bevel; the mortar bed is
a separate 0.04-thick object. Preview renders are Cycles CPU renders.

Run from project root:
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/env001_stone_paving.py -- build
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/env001_stone_paving.py -- render
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import blender_common as bc  # noqa: E402

PROJECT = os.path.dirname(os.path.dirname(TOOLS_DIR))
SRC_DIR = os.path.join(PROJECT, "art", "full", "source", "environment")
PREVIEW_DIR = os.path.join(PROJECT, "art", "full", "previews", "environment")
BLEND = os.path.join(SRC_DIR, "ENV001_stone_paving.blend")
GLB = os.path.join(SRC_DIR, "ENV001_stone_paving.glb")
PNG_SINGLE = os.path.join(PREVIEW_DIR, "ENV001_stone_paving.png")
PNG_TILED = os.path.join(PREVIEW_DIR, "ENV001_stone_paving_tiled2x2.png")

SLAB_TOP = 0.14
SLAB_BOTTOM = 0.04
MORTAR_TOP = 0.04
MODULE_HALF = 2.0
JOINT = 0.02
EDGE_HALF_JOINT = 0.01

EVEN_X = [(-1.99, -1.01), (-0.99, -0.01), (0.01, 0.99), (1.01, 1.99)]
ODD_X = [(-1.99, -1.51), (-1.49, -1.01), (-0.99, -0.51), (-0.49, -0.01),
         (0.01, 0.49), (0.51, 0.99), (1.01, 1.49), (1.51, 1.99)]


def add_box(bm, x0, x1, y0, y1, z0, z1):
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    sx, sy, sz = (x1 - x0), (y1 - y0), (z1 - z0)
    mat = Matrix.Translation((cx, cy, cz)) @ Matrix.Diagonal((sx, sy, sz, 1.0))
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat)


def build():
    bc.reset_scene()
    rng = random.Random(20261024)  # fixed seed: same layout every run

    slab_bm = bmesh.new()
    slab_count = 0
    for row in range(8):
        z0 = -1.99 + row * 0.5
        z1 = z0 + 0.48
        pieces = EVEN_X if row % 2 == 0 else ODD_X
        for (x0, x1) in pieces:
            lift = rng.uniform(0.0, 0.0035)
            add_box(slab_bm, x0, x1, z0, z1, SLAB_BOTTOM, SLAB_TOP + lift)
            slab_count += 1

    slab_mesh = bpy.data.meshes.new("ENV001_stone_paving_mesh")
    slab_bm.to_mesh(slab_mesh)
    slab_bm.free()
    slabs = bpy.data.objects.new("ENV001_stone_paving", slab_mesh)
    bpy.context.collection.objects.link(slabs)
    bpy.context.view_layer.objects.active = slabs
    slabs.select_set(True)

    bevel = slabs.modifiers.new("BEV_slab_edges", "BEVEL")
    bevel.width = 0.006
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(40.0)
    bevel.harden_normals = True
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    bpy.ops.object.shade_auto_smooth(angle=math.radians(32.0))

    stone = bc.make_stone_material("MAT_stone_paving", base_hex="#B9B1A2",
                                   roughness=0.68, noise_scale=2.8,
                                   roughness_variation=0.14, color_variation=0.09)
    slab_mesh.materials.append(stone)

    # Mortar bed: real geometry, sits under the slabs and shows in the joints.
    mortar_bm = bmesh.new()
    add_box(mortar_bm, -MODULE_HALF, MODULE_HALF, -MODULE_HALF, MODULE_HALF,
            0.0, MORTAR_TOP)
    mortar_mesh = bpy.data.meshes.new("ENV001_mortar_bed_mesh")
    mortar_bm.to_mesh(mortar_mesh)
    mortar_bm.free()
    mortar = bpy.data.objects.new("ENV001_mortar_bed", mortar_mesh)
    bpy.context.collection.objects.link(mortar)
    mortar_mesh.materials.append(
        bc.make_stone_material("MAT_mortar", base_hex="#8C8578", roughness=0.93,
                               noise_scale=9.0, roughness_variation=0.06,
                               color_variation=0.07)
    )

    # Tileability facts.
    xs = [v.co.x for v in slab_mesh.vertices]
    ys = [v.co.y for v in slab_mesh.vertices]
    zs = [v.co.z for v in slab_mesh.vertices]
    print("ENV001 slab_count=%d bounds_x=(%.4f, %.4f) bounds_y=(%.4f, %.4f) z=(%.4f, %.4f)" % (
        slab_count, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    print("ENV001 joint=%.3f edge_half_joint=%.3f module=%.1fx%.1f top=%.3f" % (
        JOINT, EDGE_HALF_JOINT, 2 * MODULE_HALF, 2 * MODULE_HALF, SLAB_TOP))
    print("ENV001 origin_world=%s dims=%s" % (
        tuple(round(v, 4) for v in slabs.matrix_world.translation),
        tuple(round(v, 4) for v in slabs.dimensions)))
    print("ENV001 mortar origin_world=%s dims=%s" % (
        tuple(round(v, 4) for v in mortar.matrix_world.translation),
        tuple(round(v, 4) for v in mortar.dimensions)))
    print("ENV001 materials=%s %s" % (
        [m.name for m in slab_mesh.materials], [m.name for m in mortar_mesh.materials]))

    os.makedirs(SRC_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=False)
    print("ENV001_SAVED=%s bytes=%d" % (BLEND, os.path.getsize(BLEND)))

    bpy.ops.object.select_all(action="DESELECT")
    slabs.select_set(True)
    mortar.select_set(True)
    bpy.context.view_layer.objects.active = slabs
    bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)
    print("ENV001_GLB=%s bytes=%d" % (GLB, os.path.getsize(GLB)))

    bc.print_scene_facts([slabs, mortar])


def _duplicate_tiles(objects, offsets):
    copies = []
    for (ox, oy) in offsets:
        for src in objects:
            dup = src.copy()
            dup.data = src.data.copy()
            dup.name = "%s_tile_%d_%d" % (src.name, ox, oy)
            dup.location = (src.location.x + ox, src.location.y + oy, src.location.z)
            bpy.context.collection.objects.link(dup)
            copies.append(dup)
    return copies


def render():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    slabs = bpy.data.objects.get("ENV001_stone_paving")
    mortar = bpy.data.objects.get("ENV001_mortar_bed")
    if slabs is None or mortar is None:
        raise RuntimeError("ENV001 objects missing after reopen")
    print("ENV001_REOPEN dims=%s mats=%s" % (
        tuple(round(v, 4) for v in slabs.dimensions),
        [m.name for m in slabs.data.materials]))

    bc.setup_preview_render(target=(0.0, 0.0, 0.10), distance=5.0, elevation=2.3,
                            resolution=(1000, 760), samples=64,
                            ground_color="#C9C2B4")
    bc.render_to(PNG_SINGLE)

    # 2x2 tiling preview: extra copies exist only in this in-memory preview scene.
    _duplicate_tiles([slabs, mortar], [(4.0, 0.0), (0.0, 4.0), (4.0, 4.0)])

    cam = bpy.context.scene.camera
    cam.data.lens = 50.0
    cam.location = (2.0 + 9.6 * math.sin(math.radians(38.0)),
                    2.0 - 9.6 * math.cos(math.radians(38.0)),
                    6.4)
    direction = Vector((2.0, 2.0, 0.05)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 900
    bpy.context.scene.cycles.samples = 72
    bc.render_to(PNG_TILED)


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    stage = args[0] if args else "build"
    if stage == "build":
        build()
    elif stage == "render":
        render()
    else:
        raise SystemExit("unknown stage: %s" % stage)


if __name__ == "__main__":
    main()
