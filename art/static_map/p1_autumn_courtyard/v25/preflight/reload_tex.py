# -*- coding: utf-8 -*-
"""重载背景贴图（避免 Blender 缓存旧图）。"""
import bpy

n = 0
for img in bpy.data.images:
    if img.name.startswith(("M0", "P1_", "__")) or "air" in img.name.lower() or "bank" in img.name.lower():
        try:
            img.reload()
            n += 1
            print("RELOAD", img.name, img.size[:])
        except Exception as e:
            print("SKIP", img.name, e)
print("RELOADED", n)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
