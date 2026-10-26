import bpy,json,os,hashlib
from pathlib import Path
root=Path(r'C:/软件/鼠鼠');out=root/'art_review/reports/independent_20261025_candidate'
paths=['art/full/source/layout/MAP001_courtyard.blend','art/full/source/environment/ENV006_autumn_tree.blend','art/full/source/props/PROP001_bench.blend','art/iterations/cycle_02/PROP001/versions/q07_edited_bench.blend']
results=[]
for rel in paths:
 p=root/rel
 if not p.is_file():results.append({'path':rel,'missing':True});continue
 bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False)
 meshes=[o for o in bpy.data.objects if o.type=='MESH']
 images=[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file),'exists':bool(im.packed_file) or Path(bpy.path.abspath(im.filepath)).is_file()} for im in bpy.data.images if im.filepath]
 bench=bpy.data.objects.get('PROP001_bench_wood')
 results.append({'path':rel,'opened':True,'objects':len(bpy.data.objects),'meshes':len(meshes),'uv_meshes':sum(bool(o.data.uv_layers) for o in meshes),'materials':len(bpy.data.materials),'images':images,'bench_wood_dimensions':list(bench.dimensions) if bench else None,'base_mesh_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),'geometry_editable':bool(meshes)})
(out/'native_reopen.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print('AUDIT_NATIVE_REOPEN_DONE',len(results))