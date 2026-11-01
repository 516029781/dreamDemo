import bpy, os, sys, json
from pathlib import Path
ROOT=Path(r'C:\软件\鼠鼠')
CAND=ROOT/'delivery/next_cycle/n5/T6/candidate_n5s1r'
BLEND=CAND/'source/MAP001_courtyard.blend'
GLB=CAND/'source/MAP001_courtyard.glb'
ATLAS=Path(r'C:\Users\tt\AppData\Local\Temp\n5_leaf_atlas_candidate.png')
sys.path.insert(0,str(ROOT/'tools/blender_n5'))
import courtyard_lib as cl
if not BLEND.is_file() or not ATLAS.is_file(): raise SystemExit('missing saved .blend or ASCII atlas input')
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene=bpy.context.scene
materials=[]
for mat in bpy.data.materials:
    tex=mat.get('engine_texture_path')
    if tex:
        mat['engine_texture_path']=str(ATLAS)
meshes=[o for o in scene.objects if o.type=='MESH' and not o.name.startswith('COL_')]
fonts=[o for o in scene.objects if o.type=='FONT']
total_tris=sum(cl.object_triangles(o) for o in meshes)
vertices=sum(len(o.data.vertices) for o in meshes)
for o in meshes: cl.clean_mesh_object(o)
depsgraph=bpy.context.evaluated_depsgraph_get()
for f in fonts:
    me=bpy.data.meshes.new_from_object(f.evaluated_get(depsgraph))
    conv=bpy.data.objects.new(f.name,me); conv.matrix_world=f.matrix_world.copy(); scene.collection.objects.link(conv)
    cl.clean_mesh_object(conv); meshes.append(conv)
ao=cl.apply_vertex_ao(meshes)
cl.export_glb(meshes,str(GLB))
# Reuse the candidate's unchanged route/interaction manifest, update only the
# known stair coordinate and measured source geometry statistics.
layout=json.loads((ROOT/'delivery/next_cycle/n5/T6/candidate_n5s1q/source/layout.json').read_text(encoding='utf-8'))
for inst in layout.get('instances',[]):
    if inst.get('instance_id')=='edge_steps':
        inst['position']=[-2.0,0.0,-6.8]
        inst['collider']['center']=[-2.0,-6.8]
        inst['note']='landscape foreground left of traversal lane and inside formal camera; no climbing'
        inst['source']='candidate_n5s1r reopened native Blender source; ENV005 stair repositioned from camera-projection test'
layout['generated_by']='tools/blender_n5/build_map001.py + reopened-native-export (S1R)'
layout['stats']['mesh_objects']=len(meshes)-len(fonts)
layout['stats']['text_objects']=len(fonts)
layout['stats']['triangles']=total_tris
layout['stats']['vertices']=vertices
layout['stats']['materials']=sorted({m.name for o in meshes for m in o.data.materials if m and not m.name.startswith('ENG_')})
(ROOT/'delivery/next_cycle/n5/T6/candidate_n5s1r/source/layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'blend_reopened':str(BLEND),'glb_written':str(GLB),'glb_bytes':GLB.stat().st_size,'mesh_objects':len(meshes)-len(fonts),'text_objects':len(fonts),'source_triangles':total_tris,'vertices':vertices,'ao':ao},ensure_ascii=False))
