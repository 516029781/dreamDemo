# N3 verification: color render at half res, low samples, fixed camera, no DOF.
import bpy, os, time

t0 = time.time()
sc = bpy.context.scene
HERE = os.path.dirname(__file__)
RD = os.path.join(os.path.dirname(HERE), "renders")
cam = sc.camera
dof0 = cam.data.dof.use_dof
cam.data.dof.use_dof = False
res0 = (sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage)
s0 = sc.cycles.samples
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 539, 100
sc.cycles.samples = 48
sc.render.filepath = os.path.join(RD, "n5q_color.png")
bpy.ops.render.render(write_still=True)
cam.data.dof.use_dof = dof0
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = res0
sc.cycles.samples = s0
print("N3_RENDER_DONE elapsed=%.1fs" % (time.time() - t0))
