"""v11 isolated reopen reproduction: render the ortho master at 420x735."""
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out_png = argv[0]
sc = bpy.context.scene
sc.camera = bpy.data.objects["Camera"]
sc.render.resolution_x = 420
sc.render.resolution_y = 735
sc.cycles.samples = 24
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print("REPRO_RENDER_OK", out_png)
