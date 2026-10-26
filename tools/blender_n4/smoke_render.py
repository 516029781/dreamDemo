"""A0 render smoke test: minimal Cycles CPU render in background."""
import bpy
import time

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=1.0)
cube = bpy.context.object
mat = bpy.data.materials.new("MAT_smoke")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.5, 0.45, 0.38, 1.0)
cube.data.materials.append(mat)

bpy.ops.object.camera_add(location=(3.0, -3.0, 2.0))
cam = bpy.context.object
cam.rotation_euler = (1.1, 0.0, 0.785)
bpy.context.scene.camera = cam

bpy.ops.object.light_add(type="AREA", location=(2.0, -1.0, 4.0))
bpy.context.object.data.energy = 400.0

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 16
scene.render.resolution_x = 320
scene.render.resolution_y = 240
scene.render.filepath = "C:/软件/鼠鼠/tools/blender/logs/smoke.png"
t0 = time.time()
bpy.ops.render.render(write_still=True)
print("RENDER_SECONDS=%.2f" % (time.time() - t0))
