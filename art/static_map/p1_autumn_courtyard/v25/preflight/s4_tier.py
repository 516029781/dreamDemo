"""S1 两层地块骨架：截台地到 y8 + 1.5m 挡墙 + 低地块。

方案：planning/art/P1_TWO_TIER_TERRAIN_PLAN_20261101.md §五
"""
import bpy
import bmesh
from mathutils import Vector

CUT_Y = 8.0
LOW_Z = -1.44
WALL_TOP = 0.06

sc = bpy.context.scene


def mk_mat(name, rgb, rough, spec=0.4):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1.0)
    b.inputs["Roughness"].default_value = rough
    try:
        b.inputs["Specular IOR Level"].default_value = spec
    except Exception:
        pass
    return m


def box(name, x0, x1, y0, y1, z0, z1, mat):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


# ---------- 1. 台地：原网格太粗（114 顶点，110 个在 y>8），改用重建 ----------
terrace = bpy.data.objects.get("Rear service terrace ground")
old_mat = None
if terrace:
    if terrace.data.materials:
        old_mat = terrace.data.materials[0]
    terrace.hide_render = True
    print("ORIG_TERRACE hidden")

# ---------- 2. 隐藏 y>8.5 的旧物（保留景片） ----------
hidden = 0
for o in bpy.data.objects:
    if o.type != 'MESH' or o.hide_render:
        continue
    if o.name.startswith(("P1 tier", "M0")):
        continue
    ys = [(o.matrix_world @ Vector(c)).y for c in o.bound_box]
    if min(ys) > 8.5:
        o.hide_render = True
        hidden += 1
print("HIDDEN_FAR", hidden)

# ---------- 3. 挡墙 / 压顶 / 低地块 ----------
stone = mk_mat("P1 tier | wall limestone", (166, 158, 144), 0.86)
cap = mk_mat("P1 tier | wall coping", (188, 180, 166), 0.78)
sand = mk_mat("P1 tier | low sand", (150, 136, 112), 0.96)

# 新台地：y2.6-8.0，顶面 z0.06（材质沿用原台地的石板）
tmat = old_mat if old_mat else stone
box("P1 tier | upper terrace", -20.0, 20.0, 2.60, 8.00, LOW_Z - 0.30, WALL_TOP, tmat)
print("NEW_TERRACE", "-20..20 y2.6..8.0")

box("P1 tier | retaining wall", -22, 22, 7.80, 8.40, LOW_Z, WALL_TOP, stone)
box("P1 tier | wall coping", -22, 22, 7.74, 8.46, WALL_TOP, WALL_TOP + 0.12, cap)
box("P1 tier | low ground", -22, 22, 8.0, 30.0, LOW_Z - 0.30, LOW_Z, sand)

# 墙面分段明度：上段略暗、中段最暗、下段反弹（顶点色）
wall = bpy.data.objects["P1 tier | retaining wall"]
if not wall.data.color_attributes:
    wall.data.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
col = wall.data.color_attributes["Col"]
for i, v in enumerate(wall.data.vertices):
    z = v.co.z
    t = (z - LOW_Z) / (WALL_TOP - LOW_Z)
    if t > 0.72:
        k = 0.82
    elif t > 0.22:
        k = 0.66
    else:
        k = 0.74
    col.data[i].color = (k, k * 0.98, k * 0.94, 1.0)
mat = wall.data.materials[0]
nt = mat.node_tree
bsdf = nt.nodes.get("Principled BSDF")
attr = nt.nodes.new('ShaderNodeVertexColor')
attr.layer_name = "Col"
mix = nt.nodes.new('ShaderNodeMix')
mix.data_type = 'RGBA'
mix.blend_type = 'MULTIPLY'
mix.inputs[0].default_value = 1.0
mix.inputs[6].default_value = (166 / 255, 158 / 255, 144 / 255, 1.0)
nt.links.new(attr.outputs['Color'], mix.inputs[7])
nt.links.new(mix.outputs[2], bsdf.inputs['Base Color'])

# ---------- 4. 中景前移，让开挡墙视线 ----------
# 实测：y1-2.5 的箱子高 1.5m，在画面上占 v29-45，正好盖住 y8 挡墙（v29-41）。
# 参考图里平台上的构筑物在 v40-60，必须更靠相机。整组前移 4 m。
moved = 0
for o in bpy.data.objects:
    if o.hide_render:
        continue
    if o.name.startswith(("P1 yard |", "P1 center planter")):
        m = o.matrix_world.copy()
        m.translation.y -= 4.0
        o.matrix_world = m
        moved += 1
print("YARD_MOVED", moved)

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
print("S4_TIER_DONE")
