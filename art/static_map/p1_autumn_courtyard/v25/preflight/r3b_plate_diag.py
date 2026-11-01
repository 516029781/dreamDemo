# -*- coding: utf-8 -*-
"""诊断并修复景片贴图全黑：检查 image 像素，必要时按绝对路径强制重载。"""
import bpy
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "preflight")
SRC = os.path.join(ROOT, "background_src")
sc = bpy.context.scene
log = {"plates": [], "fixed": []}

TARGETS = {
    "M03 | distant air plate mat": "M03_air.png",
    "M02 | far bank plate mat": "M02_bank.png",
}

for mat_name, png in TARGETS.items():
    mat = bpy.data.materials.get(mat_name)
    if not mat or not mat.node_tree:
        log["plates"].append({"mat": mat_name, "error": "missing material"})
        continue
    tex = next((n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE"), None)
    if not tex or not tex.image:
        log["plates"].append({"mat": mat_name, "error": "no image node"})
        continue
    img = tex.image
    rec = {
        "mat": mat_name,
        "image": img.name,
        "filepath": img.filepath,
        "abs": bpy.path.abspath(img.filepath),
        "size": tuple(img.size),
        "packed": bool(img.packed_file),
        "source": img.source,
        "colorspace": img.colorspace_settings.name,
    }
    # 采样中心与顶部像素
    if img.size[0] > 0:
        w, h = img.size
        px = list(img.pixels)
        def at(u, v):
            x = int(u * (w - 1)); y = int(v * (h - 1))
            i = (y * w + x) * 4
            return [round(px[i + k], 3) for k in range(4)]
        rec["px_top_mid"] = at(0.5, 0.995)   # 图像顶部（v 接近 1）
        rec["px_center"] = at(0.5, 0.5)
        rec["px_bottom_mid"] = at(0.5, 0.01)
    log["plates"].append(rec)

    # 若贴图异常（尺寸 0 或顶部全黑且 alpha 0），强制重载
    need = (img.size[0] == 0) or (rec.get("px_top_mid", [0, 0, 0, 0])[3] < 0.02
                                  and png == "M03_air.png")
    if need:
        want = os.path.join(SRC, png)
        if os.path.exists(want):
            old = img
            new_img = bpy.data.images.load(want, check_existing=False)
            new_img.reload()
            new_img.colorspace_settings.name = "sRGB"
            tex.image = new_img
            if old.users == 0:
                bpy.data.images.remove(old)
            log["fixed"].append({"mat": mat_name, "new": new_img.name,
                                 "abs": want, "size": tuple(new_img.size)})

# 同时检查景片是否被相机父级变换二次作用
for ob in sc.objects:
    if ob.name.startswith(("M02 |", "M03 |")):
        world = ob.matrix_world.translation
        log.setdefault("objects", []).append({
            "name": ob.name,
            "parent": ob.parent.name if ob.parent else None,
            "world_loc": [round(v, 2) for v in world],
            "matrix_scale": [round(v, 3) for v in ob.matrix_world.to_scale()],
            "visible": ob.visible_get(),
            "hide_render": ob.hide_render,
        })

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "scene.blend"))
with open(os.path.join(PRE, "R3B_PLATE_DIAG.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=1)

print(json.dumps(log, ensure_ascii=False, indent=1))
