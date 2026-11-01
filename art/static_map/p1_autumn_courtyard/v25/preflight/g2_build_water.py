# -*- coding: utf-8 -*-
"""G1b：拆掉 V20 的水卡，改真实水平水面 + 重建 M02/M03 景片。

水面：y 15.3–22.5、x ±14、z=-0.18 的水平网格，UV 可编辑水纹贴图。
近岸：沿用 T01 岸沿/暗壁（顶部 z=0.13），其投影 v≈0.221 压住水面前沿。
景片：M02 深度 55、M03 深度 60（都在水面远端 45 m 之后），Emission 1.717 抵消曝光 −0.78。
"""
import bpy
import json
import math
import os

import bmesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
SRC = os.path.join(ROOT, "background_src")
REN = os.path.join(ROOT, "renders")
scene = bpy.context.scene
cam = scene.camera

# ---------- 1. 拆旧水卡 ----------
removed = []
for ob in list(bpy.data.objects):
    if ob.name.startswith("M01 |"):
        removed.append(ob.name)
        bpy.data.objects.remove(ob, do_unlink=True)

# ---------- 2. 水面网格 ----------
for ob in list(bpy.data.objects):
    if ob.name.startswith("M01W |"):
        bpy.data.objects.remove(ob, do_unlink=True)

X0, X1 = -14.0, 14.0
Y0, Y1 = 15.30, 22.50
Z = -0.18
me = bpy.data.meshes.new("M01W water mesh")
bm = bmesh.new()
v00 = bm.verts.new((X0, Y0, Z))
v10 = bm.verts.new((X1, Y0, Z))
v11 = bm.verts.new((X1, Y1, Z))
v01 = bm.verts.new((X0, Y1, Z))
bm.faces.new((v00, v10, v11, v01))
bm.to_mesh(me)
bm.free()
uvl = me.uv_layers.new(name="UVMap")
for i, (u, v) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
    uvl.data[i].uv = (u, v)
water = bpy.data.objects.new("M01W | horizontal water plane", me)
bpy.context.collection.objects.link(water)

wmat = bpy.data.materials.get("M01W water") or bpy.data.materials.new("M01W water")
wmat.use_nodes = True
nt = wmat.node_tree
nt.nodes.clear()
tex = nt.nodes.new("ShaderNodeTexImage")
img = bpy.data.images.load(os.path.join(SRC, "M01_watertex.png"), check_existing=True)
img.filepath = "//background_src/M01_watertex.png"
img.reload()
tex.image = img
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Roughness"].default_value = 0.14
bsdf.inputs["Metallic"].default_value = 0.0
bsdf.inputs["IOR"].default_value = 1.33
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(bsdf.outputs[0], out.inputs[0])
me.materials.append(wmat)

# ---------- 3. 景片 ----------
from mathutils import Vector

fwd = (cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))).normalized()
origin = cam.matrix_world.translation
frame = [cam.matrix_world @ v for v in cam.data.view_frame(scene=scene)]
tr, br, bl, tl = frame


def corner(u, v, depth):
    top = tl.lerp(tr, u)
    bot = bl.lerp(br, u)
    p = top.lerp(bot, v)
    d = p - origin
    t = depth / d.dot(fwd)
    return origin + d * t


def make_plate(name, depth, img_file):
    for ob in list(bpy.data.objects):
        if ob.name == name:
            bpy.data.objects.remove(ob, do_unlink=True)
    TL, TR, BR, BL = corner(0, 0, depth), corner(1, 0, depth), corner(1, 1, depth), corner(0, 1, depth)
    m = bpy.data.meshes.new(name + " mesh")
    m.from_pydata([BL, BR, TR, TL], [], [(0, 1, 2, 3)])
    m.update()
    uv = m.uv_layers.new(name="UVMap")
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = c
    ob = bpy.data.objects.new(name, m)
    bpy.context.collection.objects.link(ob)
    ob.parent = cam   # 局部坐标即相机空间

    im = bpy.data.images.load(os.path.join(SRC, img_file), check_existing=True)
    im.filepath = "//background_src/" + img_file
    im.reload()
    mat = bpy.data.materials.get(name + " mat") or bpy.data.materials.new(name + " mat")
    mat.use_nodes = True
    t = mat.node_tree
    t.nodes.clear()
    ti = t.nodes.new("ShaderNodeTexImage")
    ti.image = im
    ti.interpolation = "Linear"
    ti.extension = "EXTEND"
    em = t.nodes.new("ShaderNodeEmission")
    em.inputs[1].default_value = 1.717      # 抵消 view_settings.exposure = -0.78
    trn = t.nodes.new("ShaderNodeBsdfTransparent")
    mix = t.nodes.new("ShaderNodeMixShader")
    o = t.nodes.new("ShaderNodeOutputMaterial")
    t.links.new(ti.outputs["Color"], em.inputs[0])
    t.links.new(ti.outputs["Alpha"], mix.inputs[0])
    t.links.new(trn.outputs[0], mix.inputs[1])
    t.links.new(em.outputs[0], mix.inputs[2])
    t.links.new(mix.outputs[0], o.inputs[0])
    m.materials.append(mat)
    ob.visible_shadow = False
    ob.visible_diffuse = False
    ob.visible_glossy = False
    ob.visible_transmission = False
    return ob


p2 = make_plate("M02 | far bank plate", 55.0, "M02_bank.png")
p3 = make_plate("M03 | distant air plate", 60.0, "M03_air.png")

json.dump({"removed_cards": removed,
           "water_plane": {"name": water.name, "x": [X0, X1], "y": [Y0, Y1], "z": Z,
                           "texture": "background_src/M01_watertex.png",
                           "uv": "u=(x-X0)/(X1-X0), v=(y-Y0)/(Y1-Y0)"},
           "plates": {"M02": 55.0, "M03": 60.0},
           "emission_strength": 1.717,
           "ray_visibility": "shadow/diffuse/glossy/transmission off"},
          open(os.path.join(PRE, "G2_BUILD.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
print("G2 BUILD DONE removed", len(removed))
