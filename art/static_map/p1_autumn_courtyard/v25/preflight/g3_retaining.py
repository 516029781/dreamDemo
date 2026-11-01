# -*- coding: utf-8 -*-
"""单假设：左上亮米断面色块是台地远端切面。加一段挡土墙将其收成可读的岸壁。"""
import bpy, bmesh, json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sc=bpy.context.scene
m=bpy.data.materials.get("T01 | retaining stone")
if m is None:
    m=bpy.data.materials.new("T01 | retaining stone"); m.use_nodes=True
    b=m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value=(0.235,0.212,0.176,1)
    b.inputs["Roughness"].default_value=0.93
for ob in list(bpy.data.objects):
    if ob.name.startswith("T01 | far retaining"):
        bpy.data.objects.remove(ob, do_unlink=True)
def box(name,x0,x1,y0,y1,z0,z1,mat):
    me=bpy.data.meshes.new(name); bm=bmesh.new()
    bmesh.ops.create_cube(bm,size=1.0); bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(ob)
    ob.scale=(x1-x0,y1-y0,z1-z0); ob.location=((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)
    me.materials.append(mat); return ob
w=box("T01 | far retaining wall",-22,22,15.02,15.34,-1.35,0.055,m)
c=box("T01 | far retaining coping",-22,22,14.94,15.42,0.055,0.115,m)
json.dump({"wall":{"x":[-22,22],"y":[15.02,15.34],"z":[-1.35,0.055]},
           "coping":{"y":[14.94,15.42],"z":[0.055,0.115]},
           "material":{"base":[0.235,0.212,0.176],"rough":0.93},
           "reason":"遮住 Rear service terrace ground 在 y=15.2 的裸露切面"},
          open(os.path.join(ROOT,"preflight","G3_RETAINING.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,"scene.blend"))
print("RETAINING DONE")
