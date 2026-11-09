"""pilot_simple_map v01 场景构建 + 渲染（Cycles CPU）

用法：
  blender -b --python build_scene.py -- --stage blockout --out <png> [--blend <scene.blend>]
  blender -b --python build_scene.py -- --stage final    --out <png> [--blend <scene.blend>]

设计依据：knowledge/active/20261102-pilot-simple-map/SOLUTION_DESIGN.md
所有尺寸单位米，坐标与设计文档 §2 表格一一对应。
"""
import sys
import math
import bpy
from mathutils import Vector, Matrix

# ---------------------------------------------------------------- args
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default

STAGE = arg("--stage", "blockout")
OUT_PNG = arg("--out", None)
OUT_BLEND = arg("--blend", None)


# ---------------------------------------------------------------- helpers
def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h, a=1.0):
    h = h.lstrip("#")
    return (srgb_to_linear(int(h[0:2], 16)),
            srgb_to_linear(int(h[2:4], 16)),
            srgb_to_linear(int(h[4:6], 16)), a)


def make_mat(name, base_hex, rough, metallic=0.0, noise=None, wave=False):
    """noise=(scale, hex_low, hex_high, fac) 生成程序化明度扰动。"""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Base Color"].default_value = hex_rgba(base_hex)

    if noise:
        scale, low, high, fac = noise
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = scale
        tex.inputs["Detail"].default_value = 4.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = hex_rgba(low)
        ramp.color_ramp.elements[1].color = hex_rgba(high)
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MIX"
        mix.inputs["Fac"].default_value = fac
        mix.inputs["Color1"].default_value = hex_rgba(base_hex)
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], mix.inputs["Color2"])
        nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    if wave:
        tex = nt.nodes.new("ShaderNodeTexWave")
        tex.inputs["Scale"].default_value = 35.0
        tex.inputs["Distortion"].default_value = 0.6
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = hex_rgba("6E4526")
        ramp.color_ramp.elements[1].color = hex_rgba("9A663C")
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def add_box(name, size, loc, mat, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.transform(Matrix.Diagonal((size[0], size[1], size[2], 1.0)))
    ob.data.materials.append(mat)
    if bevel > 0:
        m = ob.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = 2
        m.limit_method = "ANGLE"
    return ob


def add_cyl(name, radius, depth, loc, mat, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(mat)
    m = ob.modifiers.new("Bevel", "BEVEL")
    m.width = 0.012
    m.segments = 2
    m.limit_method = "ANGLE"
    return ob


def add_hill(name, radius, scale, loc, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=radius, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.transform(Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0)))
    for poly in ob.data.polygons:
        poly.use_smooth = True
    ob.data.materials.append(mat)
    return ob


# ---------------------------------------------------------------- clean
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- materials
M_STONE = make_mat("M stone", "AFA28F", 0.82, noise=(6.0, "A89B88", "C6BBA8", 0.85))
M_STONE_LIGHT = make_mat("M stone light", "BEB2A0", 0.80, noise=(9.0, "B4A796", "D0C4B2", 0.8))
M_STONE_DARK = make_mat("M stone dark", "8E8375", 0.86, noise=(5.0, "7C7264", "9C9182", 0.85))
M_WOOD = make_mat("M wood", "8A5A34", 0.75, wave=True)
M_METAL = make_mat("M metal", "4E5257", 0.35, metallic=0.85)
M_GROUND = make_mat("M ground", "7D7264", 0.95, noise=(2.2, "6E6455", "8C8170", 0.9))
M_FAR_A = make_mat("M far A", "7E8892", 0.95)
M_FAR_B = make_mat("M far B", "9AA4AD", 0.95)

# ---------------------------------------------------------------- geometry
# 1 ground
bpy.ops.mesh.primitive_plane_add(size=120.0, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "ground"
ground.data.materials.append(M_GROUND)

# 2 platform 8 x 6 x 0.9, top at 0.9
add_box("platform", (8.0, 6.0, 0.9), (0.0, 0.0, 0.45), M_STONE, bevel=0.03)

# 3 steps: three treads 3.6 wide, 0.35 deep, tops 0.9 / 0.6 / 0.3
steps = [
    ("step_landing", 0.90, -3.175),   # y -3.00 .. -3.35 (overlaps platform by 1cm)
    ("step_mid",     0.60, -3.525),   # y -3.35 .. -3.70
    ("step_low",     0.30, -3.875),   # y -3.70 .. -4.05
]
for name, top, y in steps:
    add_box(name, (3.6, 0.36, top), (0.0, y, top / 2.0), M_STONE_LIGHT, bevel=0.015)

# 4 left parapet on platform
add_box("parapet_left", (0.30, 4.4, 1.05), (-3.85, 0.0, 1.425), M_STONE_LIGHT, bevel=0.025)

# 5-6 crates
add_box("crate_a", (0.85, 0.85, 0.85), (2.35, 1.20, 1.325), M_WOOD)
crate_b = add_box("crate_b", (0.80, 0.80, 0.80), (2.38, 1.16, 2.150), M_WOOD)
crate_b.rotation_euler[2] = math.radians(6.0)
add_box("crate_c", (0.85, 0.85, 0.85), (3.05, 0.30, 1.325), M_WOOD)

# 7 barrel
add_cyl("barrel", 0.33, 0.95, (1.55, 0.55, 1.375), M_METAL)

# 8 lamp post
add_cyl("lamp_post", 0.06, 2.60, (-2.95, 1.95, 2.20), M_METAL, verts=24)
add_box("lamp_head", (0.28, 0.28, 0.16), (-2.95, 1.95, 3.52), M_METAL, bevel=0.01)

# 9 back wall
add_box("back_wall", (8.2, 0.30, 2.00), (0.0, 3.05, 1.00), M_STONE_DARK, bevel=0.02)

# 10 far silhouettes
# 11 背景层次：不放置远景体块，改由地面按相机距离雾化（见下方 ground haze 节点）


# ---------------------------------------------------------------- ground aerial haze
# 相机距离越远，地面越接近雾色：无需体积雾即可得到背景层次，且不会出现悬浮体块
_nt = M_GROUND.node_tree
_bsdf = next(n for n in _nt.nodes if n.type == "BSDF_PRINCIPLED")
_cam = _nt.nodes.new("ShaderNodeCameraData")
_map = _nt.nodes.new("ShaderNodeMapRange")
_map.inputs["From Min"].default_value = 12.0
_map.inputs["From Max"].default_value = 78.0
_map.inputs["To Min"].default_value = 0.0
_map.inputs["To Max"].default_value = 0.92
_mix = _nt.nodes.new("ShaderNodeMixRGB")
_mix.inputs["Color2"].default_value = hex_rgba("9FA8B2")
_prev = _bsdf.inputs["Base Color"].links[0].from_socket
_nt.links.new(_prev, _mix.inputs["Color1"])
_nt.links.new(_cam.outputs["View Distance"], _map.inputs["Value"])
_nt.links.new(_map.outputs["Result"], _mix.inputs["Fac"])
_nt.links.new(_mix.outputs["Color"], _bsdf.inputs["Base Color"])

# ---------------------------------------------------------------- light
sun_data = bpy.data.lights.new("sun", "SUN")
sun_data.energy = 3.2
sun_data.angle = math.radians(2.3)  # ~0.04 rad
sun_ob = bpy.data.objects.new("sun", sun_data)
scene.collection.objects.link(sun_ob)
sun_ob.location = (-6.0, 8.0, 12.0)
# 关键：sun 为 QUATERNION 模式，赋 euler 无效
d = (Vector((0, 0, 0)) - sun_ob.location).normalized()
sun_ob.rotation_mode = "QUATERNION"
sun_ob.rotation_quaternion = d.to_track_quat("-Z", "Y")

# world ambient
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = hex_rgba("8A94A0")
bg.inputs["Strength"].default_value = 0.38

# ---------------------------------------------------------------- camera
cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 42.0
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.0, -13.4, 6.9)
target = Vector((0.0, 0.2, 1.25))
cd = (target - cam.location).normalized()
cam.rotation_mode = "QUATERNION"
cam.rotation_quaternion = cd.to_track_quat("-Z", "Y")
scene.camera = cam

# ---------------------------------------------------------------- render setup
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.seed = 0
scene.cycles.use_animated_seed = False
scene.cycles.use_denoising = True
scene.cycles.samples = 16 if STAGE == "blockout" else 64
scene.render.resolution_x = 480 if STAGE == "blockout" else 960
scene.render.resolution_y = 270 if STAGE == "blockout" else 540
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.10

# 相对输出路径写进 blend，便于隔离目录重开复现
scene.render.filepath = "//renders/final.png"
if OUT_BLEND:
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)

# ---------------------------------------------------------------- report + render
meshes = [o for o in scene.collection.all_objects if o.type == "MESH"]
print("PILOT_OBJECTS", len(meshes), sorted(o.name for o in meshes))
for o in meshes:
    zmin = min((o.matrix_world @ Vector(c)).z for c in o.bound_box)
    print("PILOT_ZMIN", o.name, round(zmin, 4))

if OUT_PNG:
    scene.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)
    print("PILOT_RENDER_DONE", OUT_PNG, scene.cycles.samples, scene.render.resolution_x, scene.render.resolution_y)
