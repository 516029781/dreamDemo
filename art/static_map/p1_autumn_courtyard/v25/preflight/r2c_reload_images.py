# -*- coding: utf-8 -*-
"""强制解包并重载背景贴图，修掉 blend 内 packed 旧缓存；同时把光照压回不过曝。

已知：v21 重绘过 M03_air.png，但成图顶部仍是旧蓝灰 (101,107,120)，
说明 bpy.data.images 里是 packed 副本，磁盘改动不生效。
"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
SRC = os.path.join(ROOT, "background_src")
sc = bpy.context.scene
log = {"images": [], "lights": [], "exposure": None, "warnings": []}

# ---------- 1. 解包 + reload 全部背景图 ----------
targets = []
for img in bpy.data.images:
    fp = bpy.path.abspath(img.filepath) if img.filepath else ""
    if not fp:
        continue
    if os.path.basename(fp).startswith(("M01", "M02", "M03")):
        targets.append((img, fp))

for img, fp in targets:
    before = {"packed": bool(img.packed_file), "size": tuple(img.size),
              "filepath": img.filepath}
    if img.packed_file:
        try:
            img.unpack(method="USE_ORIGINAL")
        except Exception as e:  # noqa: BLE001
            log["warnings"].append(f"unpack failed {img.name}: {e}")
    # 路径归一到 v22/background_src
    want = os.path.join(SRC, os.path.basename(fp))
    if os.path.exists(want):
        img.filepath = want
    img.reload()
    px = list(img.pixels[0:4]) if len(img.pixels) >= 4 else []
    log["images"].append({
        "name": img.name,
        "before": before,
        "after": {"packed": bool(img.packed_file), "size": tuple(img.size),
                  "filepath": img.filepath},
        "first_px": [round(v, 3) for v in px],
    })

# ---------- 2. 光照：压回不过曝 ----------
ADJ = {
    "Warm late afternoon key": 340.0,
    "v15 broad warm camera-side bounce": 52.0,
    "Cool sky fill": 15.0,
    "Warm directional afternoon sun": 11.0,
}
for ob in sc.objects:
    if ob.type != "LIGHT":
        continue
    if ob.name in ADJ:
        L = ob.data
        before = L.energy
        L.energy = ADJ[ob.name]
        log["lights"].append({"name": ob.name, "before": before, "after": L.energy})

before_exp = sc.view_settings.exposure
sc.view_settings.exposure = -1.02
log["exposure"] = {"before": round(before_exp, 3), "after": -1.02}

# ---------- 3. 背景景片改纯自发光，避免被光强影响 ----------
for ob in sc.objects:
    if ob.type != "MESH" or not ob.name.startswith("M0"):
        continue
    for slot in ob.material_slots:
        m = slot.material
        if not m or not m.node_tree:
            continue
        for n in m.node_tree.nodes:
            if n.type == "EMISSION":
                before = n.inputs["Strength"].default_value
                n.inputs["Strength"].default_value = 1.72
                log["warnings"].append(f"{ob.name} emission {before:.2f} -> 1.72")

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
with open(os.path.join(PRE, "R2C_RELOAD.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print("=== IMAGES ===")
for d in log["images"]:
    print(f'  {d["name"][:28]:30s} packed {d["before"]["packed"]} -> {d["after"]["packed"]}  '
          f'size {d["before"]["size"]} -> {d["after"]["size"]}')
print("=== LIGHTS ===", log["lights"])
print("=== EXPOSURE ===", log["exposure"])
for w in log["warnings"]:
    print("  !", w)
