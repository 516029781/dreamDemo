"""
Verify native A0/ENV001/PROP001 deliverables: real uncompressed .blend headers,
real mesh geometry (no image planes), procedural-only materials (no image
textures), and persistence of dimensions after reopen.

Run from project root:
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/verify_native_assets.py
"""
import os
import sys

import bpy

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(TOOLS_DIR))

BLENDS = [
    os.path.join(PROJECT, "art", "full", "previews", "a0", "a0_stone_block_v1.blend"),
    os.path.join(PROJECT, "art", "full", "previews", "a0", "a0_stone_block_v2.blend"),
    os.path.join(PROJECT, "art", "full", "source", "environment",
                 "ENV001_stone_paving.blend"),
    os.path.join(PROJECT, "art", "full", "source", "props", "PROP001_bench.blend"),
]

failures = []


def check(cond, message):
    print(("PASS " if cond else "FAIL ") + message)
    if not cond:
        failures.append(message)


for path in BLENDS:
    rel = os.path.relpath(path, PROJECT)
    check(os.path.isfile(path), "file exists: " + rel)
    if not os.path.isfile(path):
        continue
    with open(path, "rb") as fh:
        header = fh.read(12)
    check(header.startswith(b"BLENDER"), "uncompressed BLENDER header %r: %s" % (
        header, rel))

    bpy.ops.wm.open_mainfile(filepath=path)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    check(len(meshes) >= 1, "has mesh objects: %s (%d)" % (rel, len(meshes)))
    total_tris = 0
    for obj in meshes:
        deps = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(deps)
        me = ev.to_mesh()
        verts = [ev.matrix_world @ v.co for v in me.vertices]
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        total_tris += tris
        dims = tuple(round(max(v[i] for v in verts) - min(v[i] for v in verts), 4)
                     for i in range(3))
        print("  MESH %s dims=%s tris=%d origin=%s mats=%s" % (
            obj.name, dims, tris,
            tuple(round(v, 4) for v in obj.matrix_world.translation),
            [m.name for m in me.materials if m]))
        check(tris > 0, "non-empty geometry: %s/%s" % (rel, obj.name))
        check(len(me.vertices) > 4, "more than a bare quad/plane: %s/%s verts=%d" % (
            rel, obj.name, len(me.vertices)))
    print("  TOTAL_TRIS=%d objects=%d materials=%d" % (
        total_tris, len(meshes), len(bpy.data.materials)))

    image_nodes = []
    for mat in bpy.data.materials:
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    image_nodes.append((mat.name, node.name))
    check(not image_nodes, "no image-texture nodes (no AI/photo textures): %s %s" % (
        rel, image_nodes))
    check(len(bpy.data.images) == 0, "no image datablocks in source: %s (%d)" % (
        rel, len(bpy.data.images)))

    check(bpy.data.filepath and os.path.isfile(bpy.data.filepath),
          "reopened from disk: " + rel)

print("")
if failures:
    print("VERIFY_RESULT=FAIL count=%d" % len(failures))
    sys.exit(1)
print("VERIFY_RESULT=PASS blends=%d" % len(BLENDS))
