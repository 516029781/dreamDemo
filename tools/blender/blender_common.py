"""
Shared helpers for native Blender asset scripts (A0 slice).

No external/generated image assets are used: all previews are Cycles renders of
real geometry and procedural materials. Units: 1 Blender unit = 1 world unit
(the project treats 1 unit as roughly 1 metre, see DEMO_EXECUTION_SPEC.md 3.1).
"""
import math
import os

import bpy
from mathutils import Vector


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear_rgba(hex_color, alpha=1.0):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), alpha)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    return scene


def make_stone_material(name="MAT_stone", base_hex="#B9B1A2", roughness=0.72,
                        noise_scale=6.0, roughness_variation=0.16,
                        color_variation=0.10):
    """Principled stone material with procedural roughness/colour break-up.

    Note: the noise nodes are Blender-side only; engine use requires a bake
    (documented limitation, FULL_ART_DELIVERY.md 11.1 item 5).
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)

    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-800, 0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.location = (-600, 0)
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.55
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-380, 120)
    base = hex_to_linear_rgba(base_hex)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = tuple(
        min(1.0, c * (1.0 - color_variation)) for c in base[:3]
    ) + (1.0,)
    ramp.color_ramp.elements[1].position = 0.68
    ramp.color_ramp.elements[1].color = tuple(
        min(1.0, c * (1.0 + color_variation)) for c in base[:3]
    ) + (1.0,)

    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.location = (-380, -160)
    rough.inputs["From Min"].default_value = 0.0
    rough.inputs["From Max"].default_value = 1.0
    rough.inputs["To Min"].default_value = max(0.0, roughness - roughness_variation)
    rough.inputs["To Max"].default_value = min(1.0, roughness + roughness_variation)

    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(noise.outputs["Fac"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_wood_material(name="MAT_wood", base_hex="#887158"):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)

    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-800, 0)
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.location = (-620, 0)
    mapping.inputs["Scale"].default_value = (1.0, 6.0, 1.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.location = (-440, 0)
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-220, 60)
    base = hex_to_linear_rgba(base_hex)
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = tuple(c * 0.72 for c in base[:3]) + (1.0,)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = tuple(min(1.0, c * 1.22) for c in base[:3]) + (1.0,)
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.55
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_metal_material(name="MAT_metal", base_hex="#494744", roughness=0.38):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_to_linear_rgba(base_hex)
    bsdf.inputs["Metallic"].default_value = 0.85
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def add_ground(size=40.0, color_hex="#CFC8BA", z=-0.003):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    plane = bpy.context.object
    plane.name = "PREVIEW_ground"
    mat = bpy.data.materials.new("MAT_preview_ground")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_to_linear_rgba(color_hex)
    bsdf.inputs["Roughness"].default_value = 0.85
    plane.data.materials.append(mat)
    return plane


def _look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_preview_render(target=(0.0, 0.0, 0.35), distance=4.2, elevation=0.85,
                         resolution=(960, 720), samples=48, ground=True,
                         ground_color="#CFC8BA"):
    """Camera/light/render setup matching the P1 warm-key / cool-fill brief."""
    scene = bpy.context.scene
    if ground:
        add_ground(color_hex=ground_color)

    az = math.radians(38.0)  # from south-east, matching fixed 45-degree demo camera
    cam_loc = (
        target[0] + distance * math.sin(az),
        target[1] - distance * math.cos(az),
        target[2] + elevation,
    )
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.name = "PREVIEW_camera"
    cam.data.lens = 50.0
    _look_at(cam, target)
    scene.camera = cam

    bpy.ops.object.light_add(type="AREA", location=(-3.2, -3.0, 4.6))
    key = bpy.context.object
    key.name = "PREVIEW_key"
    key.data.energy = 430.0
    key.data.size = 3.5
    key.data.color = (1.0, 0.95, 0.88)
    _look_at(key, target)

    bpy.ops.object.light_add(type="AREA", location=(3.8, 1.6, 2.6))
    fill = bpy.context.object
    fill.name = "PREVIEW_fill"
    fill.data.energy = 120.0
    fill.data.size = 4.0
    fill.data.color = (0.78, 0.85, 1.0)
    _look_at(fill, target)

    world = bpy.data.worlds.new("PREVIEW_world") if scene.world is None else scene.world
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.36, 0.41, 0.47, 1.0)
    bg.inputs["Strength"].default_value = 0.55

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.15
    return cam


def render_to(path, scene=None):
    scene = scene or bpy.context.scene
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if not os.path.isfile(path):
        raise RuntimeError("render did not produce %s" % path)
    print("RENDER_WRITTEN=%s bytes=%d" % (path, os.path.getsize(path)))


def print_scene_facts(objects=None):
    objects = objects or [o for o in bpy.data.objects if o.type == "MESH"]
    for obj in objects:
        dims = tuple(round(v, 4) for v in obj.dimensions)
        print("OBJECT name=%s dims=%s origin_world=%s verts=%d tris=%d" % (
            obj.name, dims,
            tuple(round(v, 4) for v in obj.matrix_world.translation),
            len(obj.data.vertices), sum(len(p.vertices) - 2 for p in obj.data.polygons),
        ))
        for m in obj.data.materials:
            if m:
                print("  MATERIAL %s" % m.name)
