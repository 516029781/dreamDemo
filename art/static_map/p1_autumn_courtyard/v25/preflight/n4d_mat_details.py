# Batch A (N4d): material identity details. One hypothesis: adding structural
# seams/streaks to wood crates and tank, and darkening grate joints, raises
# material-surface score. No geometry added except hair-thin seam strips? No -
# texture-only changes to stay cheap.
import bpy, json, os, time

t0 = time.time()
sc = bpy.context.scene
LOG = {}

# 1) wood: increase wave stripes frequency + distort with noise for plank feel
m = bpy.data.materials.get("Old stained wood")
if m and m.use_nodes:
    nt = m.node_tree
    wave = next((n for n in nt.nodes if n.type == 'TEX_WAVE'), None)
    if wave:
        wave.inputs["Scale"].default_value = max(2.2, wave.inputs["Scale"].default_value * 2.6)
        wave.inputs["Distortion"].default_value = 4.5
        LOG["wood_wave"] = [wave.inputs["Scale"].default_value, 4.5]

# 2) tank / cylinder metals: darker joint ring feel via roughness variance isn't
#    possible textureless; instead deepen base slightly and add gloss break
for mn in ("Muted rust service metal",):
    mm = bpy.data.materials.get(mn)
    if mm and mm.use_nodes:
        for nd in mm.node_tree.nodes:
            if nd.type == 'BSDF_PRINCIPLED':
                c = nd.inputs["Base Color"].default_value
                nd.inputs["Base Color"].default_value = (c[0]*0.92, c[1]*0.92, c[2]*0.95, 1.0)
                LOG["rust_deepened"] = True

# 3) deck grates: darker to read as open metal
for ob in sc.objects:
    if ob.name.startswith("Open metal deck grate") and ob.data.materials:
        m2 = ob.data.materials[0]
        if m2.use_nodes:
            for nd in m2.node_tree.nodes:
                if nd.type == 'BSDF_PRINCIPLED' and not nd.inputs["Base Color"].is_linked:
                    c = nd.inputs["Base Color"].default_value
                    nd.inputs["Base Color"].default_value = (c[0]*0.72, c[1]*0.72, c[2]*0.75, 1.0)
        LOG["grate_dark"] = m2.name

# 4) crate lid + hooped barrel lid contrast
lm = bpy.data.materials.get("Old stained wood")

bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile()
LOG["elapsed_s"] = round(time.time() - t0, 1)
with open(os.path.join(os.path.dirname(__file__), "N4D_MAT_LOG.json"), "w", encoding="utf-8") as f:
    json.dump(LOG, f, ensure_ascii=False, indent=1)
print("N4D_DONE", LOG)
