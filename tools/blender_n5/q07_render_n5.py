"""Render the restored n4 bench source and the Q07 edited copy on one studio camera."""
import os, sys
import bpy

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import blender_common as bc

ROOT = os.path.dirname(os.path.dirname(TOOLS))


def render(blend, out):
    bpy.ops.wm.open_mainfile(filepath=blend)
    bc.setup_preview_render(target=(0.0, 0.0, 0.46), distance=3.6, elevation=1.35,
                            resolution=(1000, 760), samples=64, ground_color="#C9C2B4")
    bc.render_to(out)


render(os.path.join(ROOT, "art/candidates/candidate_n5/source/props/PROP001_bench.blend"),
       os.path.join(ROOT, "delivery/next_cycle/n5/T5/q07_restored_bench.png"))
render(os.path.join(ROOT, "art/iterations/cycle_04/PROP001/versions/q07_edited_bench_n5.blend"),
       os.path.join(ROOT, "delivery/next_cycle/n5/T5/q07_edited_bench.png"))
