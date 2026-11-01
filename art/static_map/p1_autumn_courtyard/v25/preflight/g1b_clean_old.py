import bpy, json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
removed=[]
for ob in list(bpy.data.objects):
    if ob.name in ("M02 | far bank card","M03 | distant trees air card") or ob.name.startswith("V18 B06 |"):
        removed.append(ob.name); bpy.data.objects.remove(ob, do_unlink=True)
hidden=[]
for ob in bpy.context.scene.objects:
    if ob.name.startswith("V18 B06 |") and not ob.hide_render:
        ob.hide_render=True; hidden.append(ob.name)
json.dump({"removed":removed,"hidden":hidden}, open(os.path.join(ROOT,"preflight","G1B_CLEAN_OLD.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,"scene.blend"))
print("CLEAN OLD", len(removed))
