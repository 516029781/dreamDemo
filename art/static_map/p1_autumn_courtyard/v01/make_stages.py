import bpy, os
ROOT=os.path.dirname(os.path.abspath(__file__))
BLEND=os.path.join(ROOT,'scene.blend')
OUT=os.path.join(ROOT,'renders')
os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
scene=bpy.context.scene
scene.render.resolution_x=1920; scene.render.resolution_y=1078; scene.render.resolution_percentage=25
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
scene.cycles.samples=12
neutral=bpy.data.materials.new('Evidence grey blockout'); neutral.diffuse_color=(.34,.34,.34,1); neutral.use_nodes=True
neutral.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.34,.34,.34,1)
hidden_tokens=['leaf','grass','pennant','distant foliage','nosing','vent','grate','wheel','cart','step shadow']
all_objects=list(scene.objects)
original_hidden={o.name:o.hide_render for o in all_objects}
original_mats={o.name:list(o.data.materials) if hasattr(o.data,'materials') else None for o in all_objects}
def render(name):
    scene.render.filepath=os.path.join(OUT,name)
    bpy.ops.render.render(write_still=True)
# S1 neutral blockout: remove secondary details and temporarily apply one flat neutral material.
for ob in all_objects:
    if any(t in ob.name.lower() for t in hidden_tokens): ob.hide_render=True
    if hasattr(ob.data,'materials'):
        ob.data.materials.clear(); ob.data.materials.append(neutral)
render('01_blockout.png')
# Color key uses the complete palette and planting silhouette so it can judge the whole composition.
for ob in all_objects:
    ob.hide_render=original_hidden[ob.name]
    if hasattr(ob.data,'materials') and original_mats[ob.name] is not None:
        ob.data.materials.clear()
        for m in original_mats[ob.name]: ob.data.materials.append(m)
render('01b_color_key.png')
# The first full combination proof is the current complete preview render.
scene.render.resolution_percentage=50; scene.cycles.samples=24
scene.render.filepath=os.path.join(OUT,'02_material.png')
bpy.ops.render.render(write_still=True)
