# -*- coding: utf-8 -*-
"""S3c · 远岸灌木带（把"一条硬线"打掉）

问题诊断（射线实测）：台地地面在 y=15.2 处**平切结束**，上面的 `T01 | far retaining coping`
只是一条 z=0.02 的薄片；再往后什么都没有，直接跳到 55 m 的景片贴图。
所以画面上 v14 处是一条笔直的接缝：亮的台地 → 平的贴图。

做法：沿 y 14.6–15.5 摆一排**有体积的干灌木**（0.8–1.5 m），
顶部落在 v6 左右、根部压住 v14 的接缝，用真实轮廓 + 投影 + 明暗把线吃掉；
再在后面补一层更矮更灰的灌木，形成"近灌 → 远灌 → 景片"三层递进。

用法: blender -b scene.blend -P preflight/s3c_bank.py
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Vector, noise

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
K = json.load(open(os.path.join(PRE, "KNOBS.json"), encoding="utf-8"))
random.seed(4242)

for ob in list(bpy.data.objects):
    if ob.name.startswith("P1 bank"):
        bpy.data.objects.remove(ob, do_unlink=True)
for m in list(bpy.data.materials):
    if m.name.startswith("P1 bank |"):
        bpy.data.materials.remove(m)


def s2l(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mk_mat(name, srgb, rough=0.92):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = tuple(s2l(c) for c in srgb) + (1.0,)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = 0.15
    return m


MATS = [
    mk_mat("P1 bank | shrub olive", (104, 100, 66)),
    mk_mat("P1 bank | shrub amber", (128, 96, 60)),
    mk_mat("P1 bank | shrub dry", (120, 108, 84)),
    mk_mat("P1 bank | shrub haze", (138, 128, 110)),
]

made = []


def shrub(name, cx, cy, r, h, mat, seed):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    rnd = random.Random(seed)
    sx, sy, sz = r * rnd.uniform(0.85, 1.25), r * rnd.uniform(0.75, 1.1), h
    for v in bm.verts:
        p = v.co
        n = noise.noise(Vector((p.x * 2.2 + seed, p.y * 2.2, p.z * 2.2)))
        k = 1.0 + 0.24 * n
        v.co = Vector((p.x * k * sx, p.y * k * sy, max(-0.15, p.z * k) * sz))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    ob.location = (cx, cy, 0.03)
    ob.data.materials.append(mat)
    # 轻微的朝向差，避免一排"圆球"
    ob.rotation_euler = (0, 0, rnd.uniform(0, 6.283))
    made.append(ob.name)
    return ob


# 近层：y 14.55–15.35，高 0.75–1.45，密
x = -15.0
i = 0
while x < 15.0:
    w = random.uniform(0.55, 1.15)
    h = random.uniform(0.78, 1.32) * K.get("bank_h", 1.0)
    y = random.uniform(14.55, 15.20)
    shrub("P1 bank | shrub A%02d" % i, x + w * 0.5, y, w,
          h, random.choice(MATS[:3]), 100 + i)
    x += w * random.uniform(1.05, 1.5)
    i += 1

# 远层：y 15.25–15.55，更矮更灰（大气透视）
x = -14.0
j = 0
while x < 14.0:
    w = random.uniform(0.7, 1.5)
    h = random.uniform(0.55, 0.95) * K.get("bank_h", 1.0)
    y = random.uniform(15.25, 15.55)
    shrub("P1 bank | shrub B%02d" % j, x + w * 0.5, y, w,
          h, MATS[3], 300 + j)
    x += w * random.uniform(1.0, 1.45)
    j += 1

# 三五处更高的丛，打断"齐平"的顶线
for k, (cx, cy, hh, ww) in enumerate([(-9.4, 14.9, 1.55, 1.5), (-2.2, 15.0, 1.62, 1.35),
                                     (3.6, 14.8, 1.48, 1.6), (9.8, 15.05, 1.58, 1.45)]):
    shrub("P1 bank | shrub C%d" % k, cx, cy, ww, hh * K.get("bank_h", 1.0), MATS[1], 500 + k)

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
json.dump({"count": len(made), "names": made[:60]},
          open(os.path.join(PRE, "S3C_BANK.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("S3C_DONE shrubs=%d" % len(made))
