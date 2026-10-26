import bpy,json,os
from pathlib import Path
r=Path('C:/软件/鼠鼠');out=r/'art_review/reports/independent_20261024'
paths=[r/'art/full/source/layout/MAP001_courtyard.blend',r/'art/full/source/environment/ENV006_autumn_tree.blend',r/'art/full/source/props/PROP001_bench.blend']
# Resolve catalogue paths rather than guessing a file name.
cat=json.loads((r/'art/full/art_complete_catalog.json').read_text(encoding='utf-8'))
paths=[]
for a in cat['items']:
 if a['id'] in ['MAP001','ENV006','PROP001']:
  paths.extend(r/p for p in a['source_paths'] if p.endswith('.blend'))
records=[]
for p in paths:
 bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False,use_scripts=False)
 meshes=[o for o in bpy.data.objects if o.type=='MESH']
 for o in meshes:o.data.calc_loop_triangles()
 images=[{'name':im.name,'filepath':im.filepath,'packed':bool(im.packed_file),'exists':bool(im.packed_file) or os.path.exists(bpy.path.abspath(im.filepath))} for im in bpy.data.images if im.source=='FILE']
 records.append({'path':str(p.relative_to(r)),'opened':True,'mesh_objects':len(meshes),'mesh_triangles':sum(len(o.data.loop_triangles) for o in meshes),'uv_meshes':sum(bool(o.data.uv_layers) for o in meshes),'materials':len(bpy.data.materials),'images':images})
(out/'native_reopen.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('NATIVE_REOPEN',json.dumps(records,ensure_ascii=True))
