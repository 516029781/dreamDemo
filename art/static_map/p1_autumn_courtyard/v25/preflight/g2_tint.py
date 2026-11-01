# -*- coding: utf-8 -*-
"""单假设：整图偏灰米，是叶/草材质缺暖色。只调材质色，不动几何与灯光。"""
import bpy, json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log={}
def tweak(match, fn, tag):
    n=0
    for m in bpy.data.materials:
        if not m.use_nodes or match not in m.name: continue
        b=next((x for x in m.node_tree.nodes if x.bl_idname=="ShaderNodeBsdfPrincipled"),None)
        if not b: continue
        c=b.inputs["Base Color"].default_value
        before=[round(v,3) for v in c[:3]]
        r,g,bb=fn(c[0],c[1],c[2])
        b.inputs["Base Color"].default_value=(min(1,r),min(1,g),min(1,bb),1)
        log.setdefault(tag,[]).append({"mat":m.name,"before":before,"after":[round(r,3),round(g,3),round(bb,3)]})
        n+=1
    return n
# 叶：向琥珀偏（提 R、压 B）
n1=tweak("leaf", lambda r,g,b:(r*1.18+0.02, g*1.02, b*0.80), "leaf")
n2=tweak("Leaf", lambda r,g,b:(r*1.18+0.02, g*1.02, b*0.80), "Leaf")
# 干草：向金黄偏
n3=tweak("Dry grass", lambda r,g,b:(r*1.06+0.03, g*1.00+0.01, b*0.72), "dry_grass")
n4=tweak("Grass", lambda r,g,b:(r*1.05+0.02, g*1.00, b*0.76), "grass")
json.dump({"counts":{"leaf":n1+n2,"dry_grass":n3,"grass":n4},"changes":log},
          open(os.path.join(ROOT,"preflight","G2_TINT.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,"scene.blend"))
print("TINT DONE", n1+n2+n3+n4)
