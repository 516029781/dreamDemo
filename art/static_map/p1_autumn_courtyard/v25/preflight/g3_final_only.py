import bpy, json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sc=bpy.context.scene; cam=sc.camera
sc.render.engine="CYCLES"; sc.cycles.samples=48; sc.cycles.seed=0; sc.cycles.use_denoising=True
cam.data.dof.use_dof=True
sc.render.resolution_x=1920; sc.render.resolution_y=1078; sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
sc.render.filepath=os.path.join(ROOT,"renders","final.png")
bpy.context.preferences.filepaths.save_version=0
bpy.ops.render.render(write_still=True)
print("FINAL ONLY DONE")
