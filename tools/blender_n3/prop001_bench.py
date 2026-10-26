"""
PROP001 park bench (native Blender geometry, A0 slice).

Wood slats + dark metal side frames, real geometry with bevels.
Overall: 1.70 x 0.70 x 0.88 world units, origin at base centre (0,0,0),
seat top 0.44, front faces -Y. Two materials only (wood, metal).
Preview renders are Cycles CPU renders.

Run from project root:
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/prop001_bench.py -- build
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/prop001_bench.py -- render
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import blender_common as bc  # noqa: E402

PROJECT = os.path.dirname(os.path.dirname(TOOLS_DIR))
SRC_DIR = os.path.join(PROJECT, "art", "candidates", "candidate_n3", "source", "props")
PREVIEW_DIR = os.path.join(PROJECT, "art", "candidates", "candidate_n3", "previews", "props")
BLEND = os.path.join(SRC_DIR, "PROP001_bench.blend")
GLB = os.path.join(SRC_DIR, "PROP001_bench.glb")
PNG = os.path.join(PREVIEW_DIR, "PROP001_bench.png")

WIDTH = 1.70          # X
DEPTH = 0.70          # Y (front -Y)
HEIGHT = 0.88         # Z
SEAT_TOP = 0.44
BACK_TILT_DEG = 9.0


def box(bm, center, size, rot_x=0.0):
    mat = (Matrix.Translation(center)
           @ Matrix.Rotation(math.radians(rot_x), 4, "X")
           @ Matrix.Diagonal((size[0], size[1], size[2], 1.0)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=mat)


def build_wood_mesh():
    bm = bmesh.new()
    slat_t = 0.030
    # Seat: 4 narrower slats with visible gaps and slightly rounded edges.
    seat_depths = [(-0.225, -0.115), (-0.090, 0.020), (0.045, 0.155), (0.180, 0.250)]
    for (y0, y1) in seat_depths:
        box(bm, (0.0, (y0 + y1) / 2, SEAT_TOP - slat_t / 2), (1.58, y1 - y0, slat_t))

    # Back: 4 horizontal slats on a 9-degree recline.
    for z in (0.555, 0.665, 0.775, 0.885):
        y = 0.245 + math.tan(math.radians(BACK_TILT_DEG)) * (z - SEAT_TOP)
        box(bm, (0.0, y, z), (1.58, 0.030, 0.072), rot_x=-BACK_TILT_DEG)

    mesh = bpy.data.meshes.new("PROP001_bench_wood_mesh")
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def build_metal_mesh():
    bm = bmesh.new()
    leg = 0.050
    for x in (-0.76, 0.76):
        # front/rear legs with a slight outward splay.
        box(bm, (x, -0.250, 0.195), (leg, leg, 0.39), rot_x=2.0)
        box(bm, (x, 0.240, 0.195), (leg, leg, 0.39), rot_x=-2.0)
        # seat rails and lower stretcher.
        box(bm, (x, -0.005, 0.395), (leg, 0.54, leg))
        box(bm, (x, -0.005, 0.140), (0.036, 0.46, 0.036))
        # foot pads.
        box(bm, (x, -0.250, 0.014), (0.10, 0.10, 0.028))
        box(bm, (x, 0.240, 0.014), (0.10, 0.10, 0.028))
        # back upright, tilted with the slats.
        mid_z = (SEAT_TOP + 0.885) / 2
        y = 0.235 + math.tan(math.radians(BACK_TILT_DEG)) * (mid_z - SEAT_TOP)
        box(bm, (x, y, mid_z), (leg, leg, 0.50), rot_x=-BACK_TILT_DEG)
        # armrest with two supports.
        box(bm, (x, -0.020, 0.630), (0.052, 0.58, 0.040))
        box(bm, (x, -0.250, 0.515), (0.040, 0.040, 0.245))
        box(bm, (x, 0.205, 0.540), (0.040, 0.040, 0.210))
        # bolt caps at the frame/arm joints.
        for (bx, bz) in ((-0.250, 0.515), (0.205, 0.540), (-0.005, 0.395)):
            box(bm, (x, bx, bz), (0.064, 0.064, 0.020))

    mesh = bpy.data.meshes.new("PROP001_bench_metal_mesh")
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def build():
    bc.reset_scene()
    wood = bpy.data.objects.new("PROP001_bench_wood", build_wood_mesh())
    metal = bpy.data.objects.new("PROP001_bench_metal", build_metal_mesh())
    for obj in (wood, metal):
        bpy.context.collection.objects.link(obj)

    for obj, width, seg in ((wood, 0.0060, 3), (metal, 0.0040, 3)):
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bev = obj.modifiers.new("BEV_edges", "BEVEL")
        bev.width = width
        bev.segments = seg
        bev.limit_method = "ANGLE"
        bev.angle_limit = math.radians(40.0)
        bev.harden_normals = True
        bpy.ops.object.modifier_apply(modifier=bev.name)
        bpy.ops.object.shade_auto_smooth(angle=math.radians(32.0))
        obj.select_set(False)

    wood.data.materials.append(bc.make_wood_material("MAT_bench_wood", "#887158"))
    metal.data.materials.append(
        bc.make_metal_material("MAT_bench_metal", "#494744", roughness=0.36)
    )

    parent = bpy.data.objects.new("PROP001_bench", None)
    parent.empty_display_type = "PLAIN_AXES"
    parent.empty_display_size = 0.2
    bpy.context.collection.objects.link(parent)
    for obj in (wood, metal):
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()

    # Join-free hierarchy keeps wood/metal separable in engine; origin is base centre.
    verts = [v.co for v in wood.data.vertices] + [v.co for v in metal.data.vertices]
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    zs = [v.z for v in verts]
    print("PROP001 bounds_x=(%.4f, %.4f) bounds_y=(%.4f, %.4f) z=(%.4f, %.4f)" % (
        min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    print("PROP001 overall_dims=(%.3f, %.3f, %.3f) seat_top=%.3f back_tilt=%.1fdeg" % (
        max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), SEAT_TOP,
        BACK_TILT_DEG))
    print("PROP001 origins wood=%s metal=%s parent=%s" % (
        tuple(round(v, 4) for v in wood.matrix_world.translation),
        tuple(round(v, 4) for v in metal.matrix_world.translation),
        tuple(round(v, 4) for v in parent.matrix_world.translation)))
    print("PROP001 materials wood=%s metal=%s" % (
        [m.name for m in wood.data.materials], [m.name for m in metal.data.materials]))

    os.makedirs(SRC_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=False)
    print("PROP001_SAVED=%s bytes=%d" % (BLEND, os.path.getsize(BLEND)))

    bpy.ops.object.select_all(action="DESELECT")
    for obj in (wood, metal):
        obj.select_set(True)
    bpy.context.view_layer.objects.active = wood
    bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_tangents=True)
    print("PROP001_GLB=%s bytes=%d" % (GLB, os.path.getsize(GLB)))

    bc.print_scene_facts([wood, metal])


def render():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    wood = bpy.data.objects.get("PROP001_bench_wood")
    metal = bpy.data.objects.get("PROP001_bench_metal")
    if wood is None or metal is None:
        raise RuntimeError("PROP001 objects missing after reopen")
    print("PROP001_REOPEN wood_dims=%s metal_dims=%s" % (
        tuple(round(v, 4) for v in wood.dimensions),
        tuple(round(v, 4) for v in metal.dimensions)))

    bc.setup_preview_render(target=(0.0, 0.0, 0.46), distance=3.6, elevation=1.35,
                            resolution=(1000, 760), samples=72,
                            ground_color="#C9C2B4")
    bc.render_to(PNG)

    # Contact-shadow check is part of the preview: ground plane is real geometry.


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
