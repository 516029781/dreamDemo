"""P1-5：水面放大 + 低地块留洞重排 + 池沿压低。

目标：冷色 0.25–0.40%，B−R +20~+28。
现状 0.087%——水面大半被池沿挡住。
"""
import bpy
from mathutils import Matrix, Vector

X0, X1 = -22.0, 22.0
CUT_Y, BANK_Y0, LOW_Z = 8.0, 19.5, -0.30
SX = 1.9          # 水面横向放大倍数
PIVOT_X = -1.1
GX0, GX1 = -6.2, 3.9
GY0, GY1 = 13.8, 16.5

sc = bpy.context.scene

low_m = bpy.data.materials.get("P1 tier | low ground")


def box(name, x0, x1, y0, y1, z0, z1, mat):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    return ob


# 1. 重排低地块（洞跟着水面一起放大）
for o in list(bpy.data.objects):
    if o.name.startswith("P1 tier | low ground"):
        bpy.data.objects.remove(o, do_unlink=True)

box("P1 tier | low ground S", X0, X1, CUT_Y, GY0, -0.60, LOW_Z, low_m)
box("P1 tier | low ground N", X0, X1, GY1, BANK_Y0 + 0.4, -0.60, LOW_Z, low_m)
box("P1 tier | low ground W", X0, GX0, GY0, GY1, -0.60, LOW_Z, low_m)
box("P1 tier | low ground E", GX1, X1, GY0, GY1, -0.60, LOW_Z, low_m)
print("LOWGROUND hole x%.1f..%.1f y%.1f..%.1f" % (GX0, GX1, GY0, GY1))

# 2. 水面横向放大 + 抬高一点，让更多水面露出来
M = (Matrix.Translation(Vector((PIVOT_X, 0, 0)))
     @ Matrix.Diagonal(Vector((SX, 1.0, 1.0, 1.0)))
     @ Matrix.Translation(Vector((-PIVOT_X, 0, 0))))
n = 0
for o in bpy.data.objects:
    if o.name.startswith("P1 pool |"):
        o.matrix_world = M @ o.matrix_world
        n += 1
        if "water surface" in o.name:
            o.location.z += 0.08          # -0.52 -> -0.44
        if "stone rim" in o.name:
            o.location.z -= 0.16          # 顶 -0.20 -> -0.36，只留薄唇
print("POOL scaled", n)

# 3. 诊断：水面材质
for o in bpy.data.objects:
    if o.name.startswith("P1 pool | water"):
        mats = [m.name for m in o.data.materials if m]
        print("WATER_MAT", mats)
        for mn in mats:
            m = bpy.data.materials.get(mn)
            if not m or not m.use_nodes:
                continue
            for nd in m.node_tree.nodes:
                if nd.type == 'BSDF_PRINCIPLED':
                    bc = nd.inputs['Base Color']
                    print("  base", [round(c, 3) for c in bc.default_value], "linked", bc.is_linked)
                    print("  emis", [round(c, 3) for c in nd.inputs['Emission Color'].default_value],
                          "strength", round(nd.inputs['Emission Strength'].default_value, 3))
bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
print("S5_WATER_DONE")
