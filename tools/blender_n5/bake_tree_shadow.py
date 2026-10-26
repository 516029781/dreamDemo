"""Bake the courtyard tree's ground shade by projecting its real geometry.

The n4b tree shade was a hand-placed radial ellipse, which read as a painted
blob and was scored down under lighting_contact. This renders the silhouette of
the actual bark/canopy/mass meshes sheared along the sun vector onto the ground
plane, so the decal carries genuine foliage shape and the wispy rim.

Native geometry only: no AI image, no image-to-image, no generative fill.
"""
import math
import os

import bpy
from mathutils import Matrix, Vector

ROOT = r"C:\软件\鼠鼠"
TREE = os.path.join(ROOT, "art/candidates/candidate_n5/source/environment",
                    "ENV006_autumn_tree.blend")
OUT_RAW = os.path.join(ROOT, "art/candidates/candidate_n5/source/layout",
                       "ENV006_tree_shadow_raw.png")
OUT_DIR = os.path.dirname(OUT_RAW)

# Ground shear applied per unit of height, in Blender map space
# (X = engine X, Y = -engine Z, Z = engine Y). Matches the engine key at
# elevation ~41 deg, so shadow reach is roughly 1/tan(41) = 1.19 x height.
SHEAR_X = 0.86
SHEAR_Y = 0.50
RES = 1024
BLEND_SPREAD = 0.055


def shadow_proxy():
    src = [bpy.data.objects[n] for n in
           ("ENV006_autumn_tree_bark", "ENV006_autumn_tree_canopy",
            "ENV006_autumn_tree_crown_mass")
           if n in bpy.data.objects]
    if not src:
        raise SystemExit("tree meshes not found in %s" % TREE)
    for o in src:
        o.hide_render = True
    copies = []
    for o in src:
        c = o.copy()
        c.data = o.data.copy()
        bpy.context.collection.objects.link(c)
        copies.append(c)
    bpy.ops.object.select_all(action="DESELECT")
    for c in copies:
        c.select_set(True)
    bpy.context.view_layer.objects.active = copies[-1]
    bpy.ops.object.join()
    proxy = bpy.context.view_layer.objects.active
    proxy.name = "ENV006_tree_shadow_proxy"
    # The copies were taken from render-hidden sources and inherited the flag.
    proxy.hide_render = False
    proxy.hide_viewport = False
    # Project along the sun vector onto z = 0.
    proxy.matrix_world = Matrix((
        (1.0, 0.0, SHEAR_X, 0.0),
        (0.0, 1.0, SHEAR_Y, 0.0),
        (0.0, 0.0, 0.0, 1.0),
        (0.0, 0.0, 0.0, 1.0),
    )) @ proxy.matrix_world
    return proxy


def black_emission():
    mat = bpy.data.materials.new("SHADOW_MASK")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (0, 0, 0, 1)
    emit.inputs["Strength"].default_value = 1.0
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def frame_camera(proxy):
    xs, ys = [], []
    for corner in proxy.bound_box:
        w = proxy.matrix_world @ Vector(corner)
        xs.append(w.x)
        ys.append(w.y)
    cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2.0 * 1.06
    cam_data = bpy.data.cameras.new("SHADOW_CAM")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = half * 2.0
    cam_data.clip_end = 200.0
    cam = bpy.data.objects.new("SHADOW_CAM", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (cx, cy, 40.0)
    cam.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.scene.camera = cam
    return cx, cy, half


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=TREE)
    proxy = shadow_proxy()
    mat = black_emission()
    proxy.data.materials.clear()
    proxy.data.materials.append(mat)
    cx, cy, half = frame_camera(proxy)

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_x = RES
    scene.render.resolution_y = RES
    scene.world = bpy.data.worlds.new("FLAT") if "FLAT" not in bpy.data.worlds \
        else bpy.data.worlds["FLAT"]
    scene.world.use_nodes = False
    scene.world.color = (0.0, 0.0, 0.0)
    scene.render.filepath = OUT_RAW
    bpy.ops.render.render(write_still=True)
    print(json_line(cx, cy, half))


def json_line(cx, cy, half):
    import json
    return json.dumps({
        "kind": "q_env006_projected_tree_shadow",
        "source_blend": TREE,
        "out": OUT_RAW,
        "shear": [SHEAR_X, SHEAR_Y],
        "sun_elevation_deg": round(math.degrees(math.atan2(1.0, math.hypot(SHEAR_X, SHEAR_Y))), 2),
        "centre": [round(cx, 3), round(cy, 3)],
        "ortho_half_extent": round(half, 3),
        "resolution": RES,
    })


main()
