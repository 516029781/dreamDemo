# -*- coding: utf-8 -*-
"""G3 交付渲染：final / no_dof / blockout / color_key / details。

要点：blockout 与 color_key 会临时替换材质，渲染后**必须恢复并校验**，
否则 clay 会被 save_as_mainfile 写回场景（v21 曾因此把树草变灰模）。
"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REN = os.path.join(ROOT, "renders")
PRE = os.path.join(ROOT, "preflight")
os.makedirs(REN, exist_ok=True)
sc = bpy.context.scene
cam = sc.camera
log = {"shots": [], "materials_restored": 0, "warnings": []}


def setup(samples, pct, dof=True):
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.seed = 0
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1078
    sc.render.resolution_percentage = pct
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    cam.data.dof.use_dof = dof
    bpy.context.preferences.filepaths.save_version = 0


def shoot(name, samples, pct, dof=True):
    path = os.path.join(REN, name)
    blend_mtime = os.path.getmtime(os.path.join(ROOT, "scene.blend"))
    if os.path.exists(path) and os.path.getsize(path) > 0 and os.path.getmtime(path) >= blend_mtime:
        log["shots"].append({"name": name, "reused": True})
        print("REUSE", name)
        return
    setup(samples, pct, dof)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    log["shots"].append({"name": name, "samples": samples, "pct": pct, "dof": dof})
    print("SHOT", name)


# ---------- 1. 正式图 ----------
shoot("final.png", 48, 100, True)

# ---------- 2. 无 DOF 诊断 ----------
shoot("no_dof_diagnostic.png", 24, 50, False)

# ---------- 3. 灰模 ----------
saved = {}
clay = bpy.data.materials.get("__blockout_clay")
if not clay:
    clay = bpy.data.materials.new("__blockout_clay")
    clay.use_nodes = True
    b = clay.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.55, 0.53, 0.50, 1)
    b.inputs["Roughness"].default_value = 0.92

for ob in sc.objects:
    if ob.type in {"MESH", "CURVE"} and hasattr(ob.data, "materials"):
        saved[ob.name] = [m.name if m else None for m in ob.data.materials]
        if ob.name.startswith("M0"):
            continue
        ob.data.materials.clear()
        ob.data.materials.append(clay)
shoot("blockout.png", 24, 50, True)

# ---------- 4. 色块 ----------
key = bpy.data.materials.get("__color_key")
if not key:
    key = bpy.data.materials.new("__color_key")
    key.use_nodes = True
    kb = key.node_tree.nodes.get("Principled BSDF")
    kb.inputs["Base Color"].default_value = (0.62, 0.55, 0.45, 1)
    kb.inputs["Roughness"].default_value = 0.95
for ob in sc.objects:
    if ob.type in {"MESH", "CURVE"} and hasattr(ob.data, "materials") and not ob.name.startswith("M0"):
        ob.data.materials.clear()
        ob.data.materials.append(key)
shoot("color_key.png", 24, 50, True)

# ---------- 5. 恢复材质（关键） ----------
for ob in sc.objects:
    if ob.name not in saved:
        continue
    mats = [bpy.data.materials.get(n) for n in saved[ob.name] if n]
    if not hasattr(ob.data, "materials"):
        continue
    ob.data.materials.clear()
    for m in mats:
        ob.data.materials.append(m)
    log["materials_restored"] += 1

# 校验：不应再有对象使用 clay/key
leak = []
for ob in sc.objects:
    if ob.type not in {"MESH", "CURVE"} or not hasattr(ob.data, "materials"):
        continue
    for m in ob.data.materials:
        if m and m.name in {"__blockout_clay", "__color_key"}:
            leak.append(ob.name)
if leak:
    log["warnings"].append(f"material leak: {leak[:10]}")

# ---------- 6. 细节板由 g3b_details.py（系统 Python + PIL）生成 ----------
log["shots"].append({"name": "details.png", "note": "delegated to g3b_details.py"})

# ---------- 7. 保存（材质已恢复） ----------
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
with open(os.path.join(PRE, "G3_DELIVER.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("RESTORED", log["materials_restored"])
print("WARN", log["warnings"])
print("SHOTS", [s["name"] for s in log["shots"]])
