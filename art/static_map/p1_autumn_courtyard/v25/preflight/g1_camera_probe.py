# -*- coding: utf-8 -*-
"""G1a：C0/C1/C2 纯色机位取景图（960×539，无 DOF，同曝光、同物件、同 53mm）。

判定：上方灰幕是否缩小；左树、右草池、中央设备、台阶/栏杆、中央水口是否仍完整可读。
只要出现"水口消失 / 草冠被切 / 台阶占满下半幅"，该候选作废。
"""
import bpy
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REN = os.path.join(ROOT, "renders")
PRE = os.path.join(ROOT, "preflight")
sc = bpy.context.scene
cam = sc.camera

BASE_ROT_X = cam.rotation_euler.x
# 注意：相机 rot_x 越大越接近水平（90°=水平）。要"朝下"必须减小 rot_x。
VARIANTS = {
    "C0": 0.0,
    "C1": -math.radians(1.5),
    "C2": -math.radians(3.0),
}

# ---- 纯色：统一黏土 + 洋红诊断 world ----
clay = bpy.data.materials.get("__probe_clay") or bpy.data.materials.new("__probe_clay")
clay.use_nodes = True
pb = clay.node_tree.nodes.get("Principled BSDF")
pb.inputs["Base Color"].default_value = (0.55, 0.55, 0.55, 1)
pb.inputs["Roughness"].default_value = 0.95
saved = {}
for ob in sc.objects:
    if ob.type in {"MESH", "CURVE"} and hasattr(ob.data, "materials"):
        saved[ob.name] = [m.name for m in ob.data.materials]
        ob.data.materials.clear()
        ob.data.materials.append(clay)

w = sc.world
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1.0, 0.0, 1.0, 1.0)
bg.inputs[1].default_value = 1.0

sc.render.engine = "CYCLES"
sc.cycles.samples = 8
sc.cycles.seed = 0
sc.cycles.use_denoising = False
cam.data.dof.use_dof = False
sc.render.resolution_x = 1920
sc.render.resolution_y = 1078
sc.render.resolution_percentage = 50
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
bpy.context.preferences.filepaths.save_version = 0

log = {"base_rotation_x": BASE_ROT_X, "lens": cam.data.lens,
       "location": list(cam.location), "exposure": sc.view_settings.exposure,
       "variants": {}}
for tag, delta in VARIANTS.items():
    cam.rotation_euler.x = BASE_ROT_X + delta
    sc.render.filepath = os.path.join(REN, "G1_probe_%s.png" % tag)
    bpy.ops.render.render(write_still=True)
    log["variants"][tag] = {"rot_x": round(cam.rotation_euler.x, 6),
                            "pitch_deg": round(90 - math.degrees(cam.rotation_euler.x), 3),
                            "delta_deg": round(math.degrees(delta), 3)}
    print("PROBE", tag, log["variants"][tag])

cam.rotation_euler.x = BASE_ROT_X

# 还原材质与世界
for name, mats in saved.items():
    ob = bpy.data.objects.get(name)
    if ob and hasattr(ob.data, "materials"):
        ob.data.materials.clear()
        for m in mats:
            mt = bpy.data.materials.get(m)
            if mt:
                ob.data.materials.append(mt)
bg.inputs[0].default_value = (0.54, 0.52, 0.49, 1.0)
bg.inputs[1].default_value = 0.2

json.dump(log, open(os.path.join(PRE, "G1_CAMERA_PROBE.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("PROBE DONE")
