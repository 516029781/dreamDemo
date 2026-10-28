import bpy, os, time, json, hashlib
ROOT=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(ROOT,'renders'); os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'scene.blend'))
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True
scene.render.resolution_x=1920; scene.render.resolution_y=1078; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
scene.render.filepath=os.path.join(OUT,'03_final.png')
bpy.context.preferences.filepaths.save_version=0
start=time.perf_counter(); bpy.ops.render.render(write_still=True); seconds=time.perf_counter()-start
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'scene.blend'))
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
 return h.hexdigest()
cam=scene.camera
record={'status':'rendered','blender':'5.2.3 LTS','engine':scene.render.engine,'samples':scene.cycles.samples,'denoising':scene.cycles.use_denoising,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'camera_location':[round(x,5) for x in cam.location],'camera_rotation_euler':[round(x,6) for x in cam.rotation_euler],'lens_mm':cam.data.lens,'focus_distance_m':cam.data.dof.focus_distance,'f_stop':cam.data.dof.aperture_fstop,'elapsed_seconds':round(seconds,2),'object_count':len(scene.objects),'blend_sha256':sha(os.path.join(ROOT,'scene.blend')),'render_sha256':sha(os.path.join(OUT,'03_final.png'))}
with open(os.path.join(ROOT,'render_log.json'),'w',encoding='utf-8') as f: json.dump(record,f,indent=2)
print(json.dumps(record,indent=2))
