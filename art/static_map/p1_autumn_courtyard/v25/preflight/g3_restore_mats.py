# -*- coding: utf-8 -*-
"""修复：把误留成 __blockout_clay 的对象按 V20 映射恢复材质（同名对象）。"""
import bpy, json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mapping=json.load(open(os.path.join(ROOT,"preflight","V20_MATERIAL_MAP.json"),encoding="utf-8"))
fixed=[]; missing=[]
for ob in bpy.context.scene.objects:
    if ob.type not in {"MESH","CURVE"} or not hasattr(ob.data,"materials"): continue
    names=[m.name if m else "" for m in ob.data.materials]
    if names!=["__blockout_clay"]: continue
    src=mapping.get(ob.name)
    if not src: missing.append(ob.name); continue
    ob.data.materials.clear()
    for mn in src:
        mt=bpy.data.materials.get(mn)
        if mt: ob.data.materials.append(mt)
    fixed.append(ob.name)
json.dump({"fixed":len(fixed),"missing":len(missing),"missing_sample":missing[:10]},
          open(os.path.join(ROOT,"preflight","G3_MAT_RESTORE.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,"scene.blend"))
print("MAT RESTORE", len(fixed), "missing", len(missing))
