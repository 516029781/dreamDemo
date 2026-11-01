# -*- coding: utf-8 -*-
"""按相机视锥重建 M02/M03 全画幅景片。

v21 缺陷：景片包围盒 z 26–40（相机上方），完全在视野外，从未被渲染到；
顶部露出的是 world 底色。本脚本按 cam.data.view_frame 在指定距离投影
全画幅矩形，UV 对齐 1920×1078，透明处走 Transparent BSDF。

深度：M03 60m（空气/远山），M02 55m（对岸），M03 在远、M02 在近。
"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
SRC = os.path.join(ROOT, "background_src")
sc = bpy.context.scene
cam = sc.camera
log = {"removed": [], "created": [], "warnings": []}


def plane_at(distance, name):
    """在相机前方 distance 米处，按视锥构建全画幅矩形。

    顶点用**相机局部坐标**（不加 matrix_world），因为对象 parent 到相机后
    会再乘一次相机矩阵；用世界坐标会导致二次变换、景片飞出视野。
    """
    fr = cam.data.view_frame(scene=sc)  # 右上, 右下, 左下, 左上 (相机空间)
    verts = []
    for p in fr:
        k = distance / (-p.z)
        verts.append(p * k)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for i, co in enumerate([(1, 1), (1, 0), (0, 0), (0, 1)]):
        uv.data[i].uv = co
    ob = bpy.data.objects.new(name, mesh)
    sc.collection.objects.link(ob)
    ob.parent = cam
    ob.matrix_parent_inverse.identity()
    return ob


def emis_mat(name, png, strength=1.72, tint=(1, 1, 1)):
    mat = bpy.data.materials.get(name)
    if mat:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.location = (380, 0)
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    trans.location = (140, -160)
    emis = nt.nodes.new("ShaderNodeEmission")
    emis.location = (140, 60)
    emis.inputs["Strength"].default_value = strength
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.location = (-220, 0)
    img = bpy.data.images.load(os.path.join(SRC, png), check_existing=True)
    img.reload()
    img.colorspace_settings.name = "sRGB"
    tex.image = img
    tex.interpolation = "Linear"
    tex.extension = "CLIP"

    nt.links.new(tex.outputs["Color"], emis.inputs["Color"])
    nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(emis.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    mat.blend_method = "BLEND" if hasattr(mat, "blend_method") else None
    return mat


# 1) 删掉旧景片
for ob in list(sc.objects):
    if ob.name.startswith(("M02 | far bank", "M03 | distant air", "M02 | M02", "M03 | M03")):
        log["removed"].append({"name": ob.name, "loc": [round(v, 2) for v in ob.matrix_world.translation]})
        bpy.data.objects.remove(ob, do_unlink=True)

# 2) 建 M03（远，60m）与 M02（近，55m）
specs = [
    ("M03 | distant air plate", 60.0, "M03_air.png", "M03 | distant air plate mat", 1.72),
    ("M02 | far bank plate", 55.0, "M02_bank.png", "M02 | far bank plate mat", 1.72),
]
for obj_name, dist, png, mat_name, strength in specs:
    ob = plane_at(dist, obj_name)
    mat = emis_mat(mat_name, png, strength)
    ob.data.materials.append(mat)
    ob.visible_shadow = False
    log["created"].append({
        "name": obj_name, "dist": dist, "png": png,
        "bbox": [[round(min(v[i] for v in ob.bound_box), 2),
                  round(max(v[i] for v in ob.bound_box), 2)] for i in range(3)],
    })

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
with open(os.path.join(PRE, "R3_PLATES.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("REMOVED:", [d["name"] for d in log["removed"]])
print("CREATED:")
for d in log["created"]:
    print(" ", d["name"], d["dist"], "m", d["bbox"])
