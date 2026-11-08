"""Render the v09 near views (P1-P8): beauty pass + an exact 1-sample depth pass.

The depth pass uses a material override whose emission is driven by
LightPath.RayLength, so it costs ~1 sample per frame and needs no compositor
(the Blender 5 compositor API dropped the PNG output slot we used before).

Usage:
  blender -b scene.blend --python tools/blender_space_base/render_v9_near.py -- \
      <out_dir> [samples] [width] [height] [CameraP1 ...]
"""
import os
import sys
import time

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_dir = argv[0] if argv else "art/static_map/space_base_minigame/v09/renders/near"
samples = int(argv[1]) if len(argv) > 1 else 48
width = int(argv[2]) if len(argv) > 2 else 2560
height = int(argv[3]) if len(argv) > 3 else 1440
only = argv[4:] if len(argv) > 4 else None

DEPTH_RANGE = 220.0
os.makedirs(out_dir, exist_ok=True)
sc = bpy.context.scene
vl = bpy.context.view_layer

for o in bpy.data.objects:
    if o.get("is_char"):
        o.hide_render = False

names = only or [f"CameraP{i}" for i in range(1, 9)]


def setup_render(w, h, spp, path):
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.cycles.samples = spp
    sc.cycles.use_denoising = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.filepath = path


# ---------------------------------------------------------------- beauty pass
for name in names:
    cam = bpy.data.objects.get(name)
    if cam is None:
        print("MISSING", name)
        continue
    sc.camera = cam
    setup_render(width, height, samples, os.path.join(out_dir, f"{name}.png"))
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print("NEAR_DONE %s %.1fs" % (name, time.time() - t0))

# ---------------------------------------------------------------- depth pass
dmat = bpy.data.materials.new("V9Depth")
dmat.use_nodes = True
nt = dmat.node_tree
nt.nodes.clear()
lp = nt.nodes.new("ShaderNodeLightPath")
div = nt.nodes.new("ShaderNodeMath")
div.operation = "DIVIDE"
div.inputs[1].default_value = DEPTH_RANGE
div.use_clamp = True
inv = nt.nodes.new("ShaderNodeMath")
inv.operation = "SUBTRACT"
inv.inputs[0].default_value = 1.0
inv.use_clamp = True
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Strength"].default_value = 1.0
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(lp.outputs["Ray Length"], div.inputs[0])
nt.links.new(div.outputs[0], inv.inputs[1])
nt.links.new(inv.outputs[0], em.inputs["Color"])
nt.links.new(em.outputs["Emission"], out.inputs["Surface"])

world = sc.world
old_strength = 1.0
if world and world.use_nodes:
    for n in world.node_tree.nodes:
        if n.type == "BACKGROUND":
            old_strength = n.inputs["Strength"].default_value
            n.inputs["Strength"].default_value = 0.0

vl.material_override = dmat
sc.render.image_settings.color_mode = "BW"
for name in names:
    cam = bpy.data.objects.get(name)
    if cam is None:
        continue
    sc.camera = cam
    setup_render(width, height, 1, os.path.join(out_dir, f"{name}_z.png"))
    bpy.ops.render.render(write_still=True)
    print("DEPTH_DONE", name)

vl.material_override = None
if world and world.use_nodes:
    for n in world.node_tree.nodes:
        if n.type == "BACKGROUND":
            n.inputs["Strength"].default_value = old_strength
print("NEAR_ALL_OK")
