"""隔离复现脚本：只重开给定 blend 并渲染，不改任何场景参数。

用法：
  blender -b <scene.blend> --python render_only.py -- <output_png>

设计意图：复现必须用**存进 blend 里的**设置，不允许脚本另外调参，
否则"复现"只是在重复脚本，而不是验证打包后的场景自身。
"""
import sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[0] if argv else "//renders/reopen.png"

sc = bpy.context.scene
print("REOPEN_ENGINE", sc.render.engine)
print("REOPEN_SAMPLES", sc.cycles.samples)
print("REOPEN_RES", sc.render.resolution_x, sc.render.resolution_y)
print("REOPEN_SEED", sc.cycles.seed, "animated", sc.cycles.use_animated_seed)
print("REOPEN_VIEW", sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure)
print("REOPEN_CAMERA", sc.camera.name, [round(v, 3) for v in sc.camera.location])
print("REOPEN_FILE_LIBRARIES", [lib.filepath for lib in bpy.data.libraries])
print("REOPEN_IMAGES", [(im.name, im.filepath) for im in bpy.data.images if im.source == "FILE"])

sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("REOPEN_DONE", out)
