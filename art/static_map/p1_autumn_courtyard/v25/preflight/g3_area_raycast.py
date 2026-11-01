# -*- coding: utf-8 -*-
"""候选背景面积：射线首命中分类（M01W=W、M02=K、M03=A、未命中=world→A、其余=F）。
说明：景片按不透明处理（其透明区实际背后是 M03/world，同属 A/K，误差已记入 caveat）。"""
import bpy, json, os
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE=os.path.join(ROOT,"preflight")
sc=bpy.context.scene; cam=sc.camera
o=cam.matrix_world.translation
tr,br,bl,tl=[cam.matrix_world@v for v in cam.data.view_frame(scene=sc)]
dg=bpy.context.evaluated_depsgraph_get()
NX,NY=384,216
cnt={"F":0,"W":0,"K":0,"A":0}; tot=0
for yi in range(NY):
    v=(yi+0.5)/NY
    for xi in range(NX):
        u=(xi+0.5)/NX
        p=tl.lerp(tr,u).lerp(bl.lerp(br,u),v); d=(p-o).normalized()
        hit,loc,n,i,ob,mw=sc.ray_cast(dg,o,d)
        tot+=1
        if not hit: cnt["A"]+=1; continue
        nm=ob.name
        if nm.startswith("M01W"): cnt["W"]+=1
        elif nm.startswith("M02"): cnt["K"]+=1
        elif nm.startswith("M03"): cnt["A"]+=1
        else: cnt["F"]+=1
areas={k:round(v/tot,5) for k,v in cnt.items()}
U=areas["F"]+areas["W"]+areas["K"]+areas["A"]
bg=areas["W"]+areas["K"]+areas["A"]
ref=json.load(open(os.path.join(ROOT,"reference_analysis","background_masks","P1_FWKA_MASK.json"),encoding="utf-8"))["areas_fraction_of_frame"]
out={"grid":[NX,NY],"counts":cnt,"areas":areas,"U":round(U,5),"background":round(bg,5),
     "background_over_U":round(bg/U,5),"reference_background_over_U":ref["background_over_U"],
     "delta_pp":round((bg/U-ref["background_over_U"])*100,2),
     "method":"ray-cast first-hit classification; cards treated as opaque",
     "caveat":"M02/M03 的 alpha 透明区在射线法里仍计为其类别；实际背后为更远层（同属背景），对背景总量影响很小，但会略微改变 W/K/A 的内部分布。"}
json.dump(out, open(os.path.join(PRE,"G3_BG_AREA.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
