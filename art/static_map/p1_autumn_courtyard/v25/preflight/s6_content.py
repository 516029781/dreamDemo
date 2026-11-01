"""P2-1 + P5-1 + P5-2：边线断线物、岸顶树冠、低地块植被。

方案：§七（断线物）、§十一（树与植被）
"""
import math
import os
import random

import bpy

random.seed(20261101)
sc = bpy.context.scene
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")


def s2l(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def mat(name, rgb, rough=0.9, spec=0.3):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (s2l(rgb[0]), s2l(rgb[1]), s2l(rgb[2]), 1.0)
    b.inputs["Roughness"].default_value = rough
    try:
        b.inputs["Specular IOR Level"].default_value = spec
    except Exception:
        pass
    return m


def link(ob):
    sc.collection.objects.link(ob)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, m):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    ob = link(bpy.data.objects.new(name, me))
    ob.data.materials.append(m)
    return ob


def cyl(name, cx, cy, z0, h, r, m, seg=20):
    verts, faces = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z0))
        verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z0 + h))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    faces.append(tuple(range(0, 2 * seg, 2)))
    faces.append(tuple(range(2 * seg - 1, 0, -2)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = link(bpy.data.objects.new(name, me))
    ob.data.materials.append(m)
    return ob


def quad(name, w, h, m, uv=True):
    v = [(-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, 0, h), (-w / 2, 0, h)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], [(0, 1, 2, 3)])
    me.update()
    if uv:
        layer = me.uv_layers.new(name="UV")
        coords = [(0, 0), (1, 0), (1, 1), (0, 1)]
        for i, loop in enumerate(me.loops):
            layer.data[i].uv = coords[loop.vertex_index]
    ob = link(bpy.data.objects.new(name, me))
    ob.data.materials.append(m)
    return ob


def grass_card_mat():
    m = bpy.data.materials.get("P1 veg | grass card")
    if m:
        return m
    m = bpy.data.materials.new("P1 veg | grass card")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.95
    b.inputs["Emission Strength"].default_value = 0.35
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(ASSETS, "grass_tall.png"), check_existing=True)
    tex.extension = "CLIP"
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
    nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    m.blend_method = 'CLIP'
    return m


# ---------------- 1. 边线断线物 ----------------
wood = mat("P1 edge | barrel wood", (128, 96, 66), 0.92)
iron = mat("P1 edge | rail iron", (86, 84, 80), 0.55, 0.5)
bag = mat("P1 edge | sandbag", (168, 152, 126), 0.95)
stone = mat("P1 edge | step stone", (176, 168, 154), 0.86)

made = []
for cx in (-4.2, 2.8):
    for k, rr in ((0, 1.00), (1, 0.92)):
        made.append(cyl("P1 edge | barrel %s.%d" % (str(cx), k), cx, 8.62, -0.30 + k * 0.02,
                        2.20, rr, wood, 24))
    made.append(cyl("P1 edge | barrel rim %s" % str(cx), cx, 8.62, 1.88, 0.10, 1.04,
                    mat("P1 edge | barrel rim", (150, 120, 84), 0.8), 24))

for i, (xa, xb) in enumerate(((-7.0, -4.8), (-2.6, 0.2), (3.4, 5.2))):
    y = 8.06
    made.append(box("P1 edge | rail top %d" % i, xa, xb, y - 0.04, y + 0.04, 0.92, 1.00, iron))
    made.append(box("P1 edge | rail mid %d" % i, xa, xb, y - 0.04, y + 0.04, 0.50, 0.57, iron))
    for xx in (xa, xb):
        made.append(box("P1 edge | rail post %d %.1f" % (i, xx), xx - 0.05, xx + 0.05,
                        y - 0.05, y + 0.05, 0.06, 1.00, iron))

for i in range(4):
    x = random.uniform(-6.5, 5.0)
    z = 0.10
    for k in range(random.randint(2, 3)):
        made.append(box("P1 edge | sandbag %d.%d" % (i, k), x - 0.30, x + 0.30,
                        7.86 + k * 0.06, 8.12 + k * 0.06, z, z + 0.20, bag))
        z += 0.17

# 下行石阶（3 级，总降 0.36）
for k in range(3):
    zt = 0.06 - 0.12 * (k + 1)
    made.append(box("P1 edge | downstep %d" % k, 3.6, 4.8, 8.18 + k * 0.30,
                    8.18 + (k + 1) * 0.30, -0.30, zt, stone))

# ---------------- 2. 低地块草丛 ----------------
gmat = grass_card_mat()
n_card = 0
for i in range(64):
    y = random.uniform(8.9, 19.0)
    if 13.4 < y < 16.9:          # 水面区留空
        y += 3.6
    x = random.uniform(-9.0, 9.0)
    z = -0.30
    s = random.uniform(0.5, 1.15)
    ob = quad("P1 veg | low grass %d" % i, 1.5 * s, 0.9 * s, gmat)
    ob.location = (x, y, z)
    ob.rotation_euler = (0, 0, random.uniform(0, math.pi))
    n_card += 1
print("GRASS_CARDS", n_card)

# ---------------- 3. 岸顶树冠 ----------------
crown = mat("P1 crown | dark", (58, 48, 38), 0.95, 0.1)
crown2 = mat("P1 crown | dark warm", (76, 60, 42), 0.95, 0.1)
n_crown = 0
for i in range(14):
    x = random.uniform(-16.0, 16.0)
    y = random.uniform(20.5, 27.0)
    z = random.uniform(1.2, 3.6)
    rx = random.uniform(2.4, 5.2)
    rz = random.uniform(1.6, 3.2)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0,
                                          location=(x, y, z))
    ob = bpy.context.object
    ob.name = "P1 crown | %02d" % i
    ob.scale = (rx, rx * 0.75, rz)
    ob.data.materials.append(crown if i % 2 else crown2)
    n_crown += 1
print("CROWNS", n_crown)

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
print("S6_CONTENT_DONE", len(made))
