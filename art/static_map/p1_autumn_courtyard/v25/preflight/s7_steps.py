"""P4-1：前景 0.7 m 立面 → 9 级台阶 + 水面降饱和。

实测落差：广场 z+0.04 → 下层 z−1.27，共 1.31 m。
9 × 0.145 = 1.305，踏面 0.256，进深 2.30 m（y −4.3 … −6.6）。
"""
import bpy

sc = bpy.context.scene

X0, X1 = -10.4, 3.5
Z_TOP = 0.04
Z_BOT = -1.27
N = 9
RISE = (Z_TOP - Z_BOT) / N      # 0.1456
TREAD = 0.256
Y0 = -4.30

stone = bpy.data.materials.get("P1 edge | step stone")


def box(name, x0, x1, y0, y1, z0, z1, m):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    ob.data.materials.append(m)
    return ob


# 1. 台阶
for i in range(N):
    zt = Z_TOP - RISE * (i + 1)
    ya = Y0 - TREAD * i
    yb = Y0 - TREAD * (i + 1)
    box("P1 steps | %02d" % i, X0, X1, yb, ya, Z_BOT - 0.10, zt, stone)
print("STEPS", N, "rise %.3f tread %.3f" % (RISE, TREAD))

# 2. 隐藏旧立面（含悬空段）
hid = 0
for o in bpy.data.objects:
    if o.name.startswith("Landing front fascia"):
        o.hide_render = True
        hid += 1
print("FASCIA_HIDDEN", hid)

# 3. 水面降饱和（B−R 34.9 → 目标 24 左右）
m = bpy.data.materials.get("P1 pool water")
if m and m.use_nodes:
    for nd in m.node_tree.nodes:
        if nd.type == 'BSDF_PRINCIPLED':
            base = (0.050, 0.072, 0.098, 1.0)
            nd.inputs["Base Color"].default_value = base
            nd.inputs["Emission Color"].default_value = base
            nd.inputs["Emission Strength"].default_value = 0.10
            print("WATER", [round(c, 3) for c in base], "emis 0.10")

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
print("S7_STEPS_DONE")
