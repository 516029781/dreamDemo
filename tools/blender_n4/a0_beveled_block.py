"""
A0 native Blender test: beveled stone block, dimension change, save/reopen,
preview render, GLB export.

Run (from project root, Blender 4.5.15 portable):
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/a0_beveled_block.py -- build
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/a0_beveled_block.py -- modify
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/a0_beveled_block.py -- render

Outputs (uncompressed .blend + preview PNG + GLB):
  art/full/previews/a0/a0_stone_block_v1.blend
  art/full/previews/a0/a0_stone_block_v2.blend
  art/full/previews/a0/a0_stone_block_v2.png
  tools/blender/out/a0_stone_block.glb
"""
import math
import os
import sys

import bpy
from mathutils import Matrix

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import blender_common as bc  # noqa: E402

PROJECT = os.path.dirname(os.path.dirname(TOOLS_DIR))
OUT_DIR = os.path.join(PROJECT, "art", "full", "previews", "a0")
V1 = os.path.join(OUT_DIR, "a0_stone_block_v1.blend")
V2 = os.path.join(OUT_DIR, "a0_stone_block_v2.blend")
PNG = os.path.join(OUT_DIR, "a0_stone_block_v2.png")
GLB = os.path.join(PROJECT, "tools", "blender", "out", "a0_stone_block.glb")
OBJ_NAME = "A0_stone_block"


def evaluated_size(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(deps)
    mesh = ev.to_mesh()
    verts = [ev.matrix_world @ v.co for v in mesh.vertices]
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    zs = [v.z for v in verts]
    size = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    ev.to_mesh_clear()
    return size


def build():
    bc.reset_scene()
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.0))
    obj = bpy.context.object
    obj.name = OBJ_NAME
    obj.data.name = OBJ_NAME + "_mesh"
    obj.dimensions = (1.2, 0.8, 0.6)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # Origin at base centre: shift mesh up by half height, keep object at (0,0,0).
    obj.data.transform(Matrix.Translation((0.0, 0.0, 0.3)))

    bevel = obj.modifiers.new("BEV_bevel", "BEVEL")
    bevel.width = 0.03
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(40.0)
    bevel.harden_normals = True

    bpy.ops.object.shade_auto_smooth(angle=math.radians(35.0))

    mat = bc.make_stone_material("MAT_stone_block", base_hex="#B9B1A2")
    obj.data.materials.append(mat)

    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=V1, compress=False)
    print("SAVED_V1=%s exists=%s bytes=%d" % (V1, os.path.isfile(V1), os.path.getsize(V1)))
    print("BUILD_BASE_DIMS=%s" % (tuple(round(d, 4) for d in obj.dimensions),))
    print("BUILD_EVAL_DIMS=%s" % (tuple(round(d, 4) for d in evaluated_size(obj)),))
    print("BEVEL width=%.4f segments=%d show_viewport=%s" % (
        bevel.width, bevel.segments, bevel.show_viewport))


def modify():
    bpy.ops.wm.open_mainfile(filepath=V1)  # proves the saved file reopens
    obj = bpy.data.objects.get(OBJ_NAME)
    if obj is None:
        raise RuntimeError("object %s missing after reopen" % OBJ_NAME)
    bevel = obj.modifiers.get("BEV_bevel")
    if bevel is None:
        raise RuntimeError("bevel modifier missing after reopen")
    print("REOPENED_V1 dims=%s bevel_width=%.4f" % (
        tuple(round(d, 4) for d in obj.dimensions), bevel.width))

    obj.dimensions = (1.6, 0.9, 0.75)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel.width = 0.04
    bevel.segments = 4
    bpy.context.view_layer.update()

    bpy.ops.wm.save_as_mainfile(filepath=V2, compress=False)
    print("SAVED_V2=%s exists=%s bytes=%d" % (V2, os.path.isfile(V2), os.path.getsize(V2)))
    print("MODIFIED_BASE_DIMS=%s" % (tuple(round(d, 4) for d in obj.dimensions),))
    print("MODIFIED_EVAL_DIMS=%s" % (tuple(round(d, 4) for d in evaluated_size(obj)),))


def render():
    bpy.ops.wm.open_mainfile(filepath=V2)
    obj = bpy.data.objects.get(OBJ_NAME)
    if obj is None:
        raise RuntimeError("object missing on render reopen")
    dims = tuple(round(d, 4) for d in evaluated_size(obj))
    print("RENDER_REOPEN dims=%s materials=%s" % (
        dims, [m.name for m in obj.data.materials]))
    if abs(dims[0] - 1.6) > 1e-3 or abs(dims[2] - 0.75) > 1e-3:
        raise RuntimeError("dimensions from modify run did not persist: %s" % (dims,))

    bc.setup_preview_render(target=(0.0, 0.0, 0.35), distance=3.4, elevation=1.0,
                            resolution=(960, 720), samples=64)
    bc.render_to(PNG)

    os.makedirs(os.path.dirname(GLB), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=GLB, export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True,
    )
    print("GLB_WRITTEN=%s bytes=%d" % (GLB, os.path.getsize(GLB)))
    bc.print_scene_facts([obj])


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    stage = args[0] if args else "build"
    if stage == "build":
        build()
    elif stage == "modify":
        modify()
    elif stage == "render":
        render()
    else:
        raise SystemExit("unknown stage: %s" % stage)


if __name__ == "__main__":
    main()
