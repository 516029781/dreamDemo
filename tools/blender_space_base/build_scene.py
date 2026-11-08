"""Procedural builder for space_base_minigame v01.

Run (Blender 4.5):
  blender -b --factory-startup --python tools/blender_space_base/build_scene.py -- \
    --stage graybox --out art/static_map/space_base_minigame/v01/scene_graybox.blend \
    --render art/static_map/space_base_minigame/v01/renders/graybox.png \
    --res 1920x2560 --samples 16

Open --stage final to add the 7 recognition landmarks and final palette.
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec_dims as S  # noqa: E402


# ---------------------------------------------------------------- utilities
def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["graybox", "final"], default="graybox")
    ap.add_argument("--out", required=True)
    ap.add_argument("--render", default="")
    ap.add_argument("--res", default="1920x2560")
    ap.add_argument("--samples", type=int, default=16)
    return ap.parse_args(argv)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def coll(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(value: str, alpha: float = 1.0):
    value = value.lstrip("#")
    return tuple(srgb_to_linear(int(value[i:i + 2], 16) / 255.0) for i in (0, 2, 4)) + (alpha,)


def make_mat(name, hex_color, rough=0.6, metal=0.0, alpha=1.0, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    r, g, b, a = hex_rgba(hex_color, alpha)
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
    if emission is not None:
        er, eg, eb, _ = hex_rgba(emission)
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (er, eg, eb, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = (er, eg, eb, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return m


def brick_pattern(material, base_hex, dark_hex):
    """Procedural 1.2 x 2.4 wall panel seams (no external texture)."""
    nt = material.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value[0] = math.radians(90)
    mp.inputs["Scale"].default_value = (1.0 / 1.2, 1.0 / 2.4, 1.0)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.squash = 1.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.03
    br.inputs["Mortar Smooth"].default_value = 0.1
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    mix.inputs["Color1"].default_value = hex_rgba(base_hex)
    mix.inputs["Color2"].default_value = hex_rgba(dark_hex)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], br.inputs["Vector"])
    nt.links.new(br.outputs["Fac"], mix.inputs["Fac"])
    nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])


def add_grid(name, x0, x1, y0, y1, step, z, width, material, collection):
    """One-mesh 3 m floor joint grid; L3-level lines, not props."""
    verts, faces = [], []
    def quad(ax, ay, bx, by):
        i = len(verts)
        verts.extend([(ax, ay, z), (bx, ay, z), (bx, by, z), (ax, by, z)])
        faces.append((i, i + 1, i + 2, i + 3))
    x = x0 + step
    while x < x1 - 0.001:
        quad(x - width / 2, y0, x + width / 2, y1)
        x += step
    y = y0 + step
    while y < y1 - 0.001:
        quad(x0, y - width / 2, x1, y + width / 2)
        y += step
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.validate(); mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def add_box(name, x0, x1, y0, y1, z0, z1, material, collection):
    mesh = bpy.data.meshes.new(name)
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def add_box_local(name, cx, cy, cz, dx, dy, dz, material, collection, rot_z=0.0, rot_y=0.0):
    """Box centered at (cx,cy,cz) with local dimensions; rotates around its own center."""
    mesh = bpy.data.meshes.new(name)
    hx, hy, hz = dx / 2.0, dy / 2.0, dz / 2.0
    verts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
             (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = (cx, cy, cz)
    obj.rotation_euler = (0.0, rot_y, rot_z)
    obj.data.materials.append(material)
    return obj


def add_cyl(name, x, y, z0, z1, radius, material, collection, axis="Z", vertices=24):
    depth = z1 - z0
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=(x, y, (z0 + z1) / 2.0))
    obj = bpy.context.object
    obj.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    if axis == "X":
        obj.rotation_euler[1] = math.radians(90)
    elif axis == "Y":
        obj.rotation_euler[0] = math.radians(90)
    return obj


def add_torus(name, x, y, z, major, minor, material, collection, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     location=(x, y, z), rotation=rot)
    obj = bpy.context.object
    obj.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def add_tube(name, x, y, r_out, r_in, z0, z1, material, collection, segments=48,
             a0=0.0, a1=2.0 * math.pi):
    """Vertical tube/arc shell, open top/bottom."""
    mesh = bpy.data.meshes.new(name)
    verts = []
    for z in (z0, z1):
        for r in (r_out, r_in):
            for i in range(segments + 1):
                a = a0 + (a1 - a0) * i / segments
                verts.append((x + r * math.cos(a), y + r * math.sin(a), z))
    faces = []
    stride = (segments + 1)
    # outer wall
    for i in range(segments):
        faces.append((i, i + 1, stride + i + 1, stride + i))
    # inner wall
    base = 2 * stride
    for i in range(segments):
        faces.append((base + i, base + i + 1, base + stride + i + 1, base + stride + i))
    # top/bottom
    for i in range(segments):
        faces.append((i, base + i, base + i + 1, i + 1))
        faces.append((stride + i, stride + i + 1, base + stride + i + 1, base + stride + i))
    mesh.from_pydata(verts, [], faces)
    mesh.validate()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def wall_h(name, y, x0, x1, h, openings, material, collection, thickness=S.WALL_T, z0=0.0):
    cuts = sorted(openings)
    pos = x0
    idx = 0
    for a, b in cuts:
        if a > pos:
            add_box(f"{name}_{idx}", pos, a, y - thickness / 2, y + thickness / 2, z0, h, material, collection)
            idx += 1
        pos = max(pos, b)
    if pos < x1:
        add_box(f"{name}_{idx}", pos, x1, y - thickness / 2, y + thickness / 2, z0, h, material, collection)


def wall_v(name, x, y0, y1, h, openings, material, collection, thickness=S.WALL_T, z0=0.0):
    cuts = sorted(openings)
    pos = y0
    idx = 0
    for a, b in cuts:
        if a > pos:
            add_box(f"{name}_{idx}", x - thickness / 2, x + thickness / 2, pos, a, z0, h, material, collection)
            idx += 1
        pos = max(pos, b)
    if pos < y1:
        add_box(f"{name}_{idx}", x - thickness / 2, x + thickness / 2, pos, y1, z0, h, material, collection)


def floor_rect(name, x0, x1, y0, y1, z, material, collection):
    return add_box(name, x0, x1, y0, y1, z, z + 0.02, material, collection)


# ---------------------------------------------------------------- materials
def build_materials(stage):
    if stage == "graybox":
        return {
            "field": make_mat("gb.field", "#11171a", 0.9),
            "core": make_mat("gb.core", "#243036", 0.85),
            "h1": make_mat("gb.h1", "#2b3d42", 0.85),
            "h2": make_mat("gb.h2", "#2a3a35", 0.85),
            "h3": make_mat("gb.h3", "#303b46", 0.85),
            "h4": make_mat("gb.h4", "#2f3d35", 0.85),
            "wall": make_mat("gb.wall", "#66757c", 0.7),
            "wall_h4": make_mat("gb.wall_h4", "#3d6b55", 0.7),
            "pool": make_mat("gb.pool", "#153743", 0.6),
            "pit": make_mat("gb.pit", "#0d1f2a", 0.8),
            "garden": make_mat("gb.garden", "#1d3328", 0.9),
            "road": make_mat("gb.road", "#2a3034", 0.85),
            "workshop": make_mat("gb.workshop", "#252b2e", 0.9),
            "metal": make_mat("gb.metal", "#59676d", 0.6, 0.4),
            "glass": make_mat("gb.glass", "#b8c9cf", 0.1, 0.0, 0.22),
            "yellow": make_mat("gb.yellow", "#c9a34a", 0.6),
            "green": make_mat("gb.green", "#3e9b63", 0.6),
            "dark": make_mat("gb.dark", "#1e2427", 0.8),
            "white": make_mat("gb.white", "#cfd5d6", 0.6),
            "container": make_mat("gb.container", "#4b5a60", 0.6, 0.2),
            "evac": make_mat("gb.evac", "#e6c34a", 0.5, 0.0, 1.0, "#e6c34a", 0.4),
            "teal": make_mat("gb.teal", "#2f6d78", 0.55),
            "blue": make_mat("gb.blue", "#2f5c9c", 0.4, 0.3, 1.0, "#2f5c9c", 1.2),
            "orange": make_mat("gb.orange", "#c87a30", 0.55),
            "brass": make_mat("gb.brass", "#aa8355", 0.35, 0.8),
            "stone": make_mat("gb.stone", "#3a322a", 0.7),
            "red": make_mat("gb.red", "#b23a2e", 0.55),
            "foliage": make_mat("gb.foliage", "#2f5a45", 0.85),
        }
    p = S.PALETTE
    return {
        "field": make_mat("f.field", "#151b1e", 0.95),
        "core": make_mat("f.core", p["concrete"], 0.9),
        "h1": make_mat("f.h1", "#222B2D", 0.9),
        "h2": make_mat("f.h2", "#9A9F9F", 0.9),
        "h3": make_mat("f.h3", "#8F9595", 0.9),
        "h4": make_mat("f.h4", "#9A9F9F", 0.9),
        "wall": make_mat("f.wall", p["structure_white"], 0.65),
        "wall_h4": make_mat("f.wall_h4", p["haavk_green"], 0.65),
        "pool": make_mat("f.pool", "#0E3A4A", 0.75),
        "pit": make_mat("f.pit", "#10212b", 0.8),
        "garden": make_mat("f.garden", p["garden_green"], 0.95),
        "road": make_mat("f.road", p["concrete"], 0.9),
        "workshop": make_mat("f.workshop", p["concrete"], 0.9),
        "metal": make_mat("f.metal", p["steel"], 0.45, 0.5),
        "glass": make_mat("f.glass", "#7F9AA3", 0.18, 0.0, 0.03),
        "glass_h1": make_mat("f.glass_h1", "#A9C4CC", 0.08, 0.0, 0.26),
        "body": make_mat("f.body", "#2F3A3E", 0.65, 0.3),
        "seam": make_mat("f.seam", "#7E8484", 0.9),
        "yellow": make_mat("f.yellow", p["warning_yellow"], 0.55),
        "green": make_mat("f.green", p["haavk_green"], 0.6),
        "dark": make_mat("f.dark", p["near_black"], 0.8),
        "white": make_mat("f.white", p["structure_white"], 0.6),
        "container": make_mat("f.container", "#4b6a74", 0.55, 0.3),
        "evac": make_mat("f.evac", "#e6c34a", 0.5, 0.0, 1.0, "#e6c34a", 1.5),
        "teal": make_mat("f.teal", p["teal"], 0.55),
        "blue": make_mat("f.blue", p["blue_light"], 0.4, 0.3, 1.0, p["blue_light"], 2.5),
        "orange": make_mat("f.orange", p["orange"], 0.55),
        "brass": make_mat("f.brass", p["brass"], 0.35, 0.8),
        "stone": make_mat("f.stone", p["dark_stone"], 0.7),
        "red": make_mat("f.red", "#B23A2E", 0.55),
        "foliage": make_mat("f.foliage", "#3E6B4A", 0.85),
        "water_light": make_mat("f.water_light", "#7FC2CC", 0.2, 0.0, 0.55, "#7FC2CC", 0.4),
        "wood": make_mat("f.wood", "#6B4A33", 0.7),
        "caramel": make_mat("f.caramel", "#8A5B3A", 0.6),
        "container_blue": make_mat("f.container_blue", "#2F5C9C", 0.55, 0.3),
        "container_olive": make_mat("f.container_olive", "#5A6247", 0.6, 0.2),
        "container_gray": make_mat("f.container_gray", "#676D6E", 0.6, 0.2),
        "frost": make_mat("f.frost", "#D8E2E4", 0.5, 0.0, 0.65),
    }


# ---------------------------------------------------------------- base scene
def build_base(m, stage):
    if stage == "final":
        brick_pattern(m["wall"], "#CFD5D6", "#B4BABB")
        brick_pattern(m["wall_h4"], "#3E9B63", "#357F52")
    g = coll("GROUND")
    core = coll("CORE")
    garden = coll("GARDEN")
    road = coll("ROAD")
    workshop = coll("WORKSHOP")

    # field / zone floors
    add_box("field", -8, 248, -212, 198, -0.25, 0.0, m["field"], g)
    floor_rect("core_floor", 0, 240, 0, 190, 0.0, m["core"], g)
    for key, room in S.ROOMS.items():
        floor_rect(f"floor_{key}", room["x0"] + 0.3, room["x1"] - 0.3,
                   room["y0"] + 0.3, room["y1"] - 0.3, 0.02, m[key.lower()], g)
    floor_rect("garden_floor", 0, 240, -30, 0, 0.02, m["garden"], g)
    floor_rect("road_floor", 108, 132, -60, -30, 0.02, m["road"], g)
    floor_rect("workshop_floor", 35, 205, -190, -60, 0.02, m["workshop"], g)

    # walls with door gaps
    for name, d in S.DOORS.items():
        mat = m["wall_h4"] if name.startswith("H4") else m["wall"]
        if d["axis"] == "h":
            wall_h(name, d["fixed"], d["a"], d["b"], d["h"], d["open"], mat, core)
        else:
            wall_v(name, d["fixed"], d["a"], d["b"], d["h"], d["open"], mat, core)

    # central solid body + CEO glass box
    add_box("central_body", 70, 170, 70, 120, 0, 9.0, m.get("body", m["metal"]), core)
    add_box("ceo_floor", 100, 140, 90, 120, 8.95, 9.05, m["dark"], core)
    # glass walls: west/east with 6 m stair openings; north/south solid
    wall_v("ceo_west", 100, 90, 120, 13.5, [(107, 113)], m["glass"], core, 0.12, 9.0)
    wall_v("ceo_east", 140, 90, 120, 13.5, [(97, 103)], m["glass"], core, 0.12, 9.0)
    wall_h("ceo_north", 120, 100, 140, 13.5, [], m["glass"], core, 0.12, 9.0)
    wall_h("ceo_south", 90, 100, 140, 13.5, [], m["glass"], core, 0.12, 9.0)
    # roof maintenance rail (3 m buffer south of box)
    add_box("roof_rail", 100, 140, 87.9, 88.5, 9.0, 10.1, m["yellow"], core)

    # H2/H4 stairs and bridges
    for key, st in S.STAIRS.items():
        add_box(f"stair_{key}", st["x"] - 1.5, st["x"] + 1.5, st["y"] - 1.5, st["y"] + 1.5,
                0, 9.0, m["dark"], core)
        add_box(f"stair_{key}_top", st["x"] - 1.5, st["x"] + 1.5, st["y"] - 1.5, st["y"] + 1.5,
                8.9, 9.02, m["metal"], core)
    for i, br in enumerate(S.BRIDGES):
        add_box_local(f"bridge_{i}", br["x"], br["y"], br["z"] + 0.06, br["w"], br["l"], 0.12,
                      m["metal"], core, rot_z=math.radians(br["rot_z"]))

    # H1 circular low wall (4 gaps) + 12 columns + observation band
    gaps = [(math.radians(-12), math.radians(12)), (math.radians(78), math.radians(102)),
            (math.radians(168), math.radians(192)), (math.radians(258), math.radians(282))]
    # build four arcs between gap ends
    starts = [math.radians(12), math.radians(102), math.radians(192), math.radians(282)]
    ends = [math.radians(78), math.radians(168), math.radians(258), math.radians(12 + 360)]
    for i, (a, b) in enumerate(zip(starts, ends)):
        add_tube(f"h1_lowwall_{i}", 35, 35, 19.0, 18.7, 0.0, 1.4, m["teal"], core, 18, a, b)
    for i in range(12):
        ang = math.radians(15 + i * 30)
        x, y = 35 + 19 * math.cos(ang), 35 + 19 * math.sin(ang)
        add_cyl(f"h1_col_{i}", x, y, 1.4, 4.5, 0.2, m["metal"], core, vertices=8)
    add_tube("h1_glass_band", 35, 35, 19.0, 18.85, 4.5, 5.5, m.get("glass_h1", m["glass"]), core, 48)
    add_cyl("h1_center_col", 35, 35, 0, 9.0, 1.0, m["metal"], core, vertices=16)
    # pod: cylinder along X, rotated -20 deg in plan
    pod = add_cyl("h1_pod", 42, 32, 3.25 - 7, 3.25 + 7, 1.75, m["dark"], core, axis="X", vertices=20)
    pod.rotation_euler[2] = math.radians(-20)
    add_box("h1_spawn", 60.5, 63.5, 6.5, 9.5, 0.03, 0.06, m["yellow"], core)

    # H1 four corner equipment rooms (SE 6x6 to clear spawn)
    for i, (x, y, size) in enumerate([(4, 66, 8), (66, 66, 8), (67, 4, 6), (4, 4, 8)]):
        add_box(f"h1_eq_{i}", x - size / 2, x + size / 2, y - size / 2, y + size / 2,
                0, 3.5, m["glass"], core)
    # H1 control room / beds / lockers as simple blocks
    add_box("h1_control", 43, 57, 61.5, 66.5, 0, 3.0, m["glass"], core)
    for i, x in enumerate((10, 16)):
        add_box(f"h1_bed_{i}", x - 1, x + 1, 64.5, 65.5, 0, 0.7, m["white"], core)
    for i, y in enumerate((20, 32, 44, 56)):
        add_box(f"h1_locker_{i}", 1.7, 3.3, y - 0.4, y + 0.4, 0, 2.0, m["metal"], core)

    # H2 pool + rim (spatial void; no cabins in graybox)
    add_box("h2_pool", 12, 57, 138, 166, 0.02, 0.05, m["pool"], core)
    for i, (x0, x1, y0, y1) in enumerate([(11.6, 57.4, 137.6, 138.0), (11.6, 57.4, 166.0, 166.4),
                                          (11.6, 12.0, 138.0, 166.0), (57.0, 57.4, 138.0, 166.0)]):
        add_box(f"h2_pool_rim_{i}", x0, x1, y0, y1, 0.02, 0.42, m["teal"], core)
    # H3 pit + rim
    add_box("h3_pit", 193, 217, 144, 166, 0.02, 0.05, m["pit"], core)
    for i, (x0, x1, y0, y1) in enumerate([(192.6, 217.4, 143.6, 144.0), (192.6, 217.4, 166.0, 166.4),
                                          (192.6, 193.0, 144.0, 166.0), (217.0, 217.4, 144.0, 166.0)]):
        add_box(f"h3_pit_rim_{i}", x0, x1, y0, y1, 0.02, 0.42, m["yellow"], core)

    # garden south wall + side walls
    wall_h("garden_south", -30, 0, 240, 6.0, [(112.5, 127.5)], m["wall"], garden)
    wall_v("garden_west", 0, -30, 0, 6.0, [], m["wall"], garden)
    wall_v("garden_east", 240, -30, 0, 6.0, [], m["wall"], garden)
    # garden pool / fountains / tree pits / benches / lamps
    add_box("garden_pool", 100, 140, -16, -8, 0.02, 0.05, m["pool"], garden)
    for i, (x0, x1, y0, y1) in enumerate([(99.6, 140.4, -16.4, -16.0), (99.6, 140.4, -8.0, -7.6),
                                          (99.6, 100.0, -16.0, -8.0), (140.0, 140.4, -16.0, -8.0)]):
        add_box(f"garden_pool_rim_{i}", x0, x1, y0, y1, 0.02, 0.42, m["white"], garden)
    for i, f in enumerate(S.FOUNTAINS):
        add_cyl(f"fountain_{i}", f["x"], f["y"], 0.0, 0.6, f["r"], m["white"], garden, vertices=20)
    for i, (x, y) in enumerate(S.TREE_PITS):
        add_box(f"tree_pit_{i}", x - 1.2, x + 1.2, y - 1.2, y + 1.2, 0, 0.6, m["white"], garden)
        add_cyl(f"tree_trunk_{i}", x, y, 0.6, 3.2, 0.18, m["dark"], garden, vertices=8)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.6, location=(x, y, 3.6))
        crown = bpy.context.object
        crown.name = f"tree_crown_{i}"
        for c in list(crown.users_collection):
            c.objects.unlink(crown)
        garden.objects.link(crown)
        crown.scale.z = 0.55
        crown.data.materials.append(m["foliage"])
    for i, (x, y) in enumerate(S.BENCHES):
        add_box(f"bench_{i}", x - 0.9, x + 0.9, y - 0.3, y + 0.3, 0, 0.45, m["dark"], garden)
    for i, (x, y) in enumerate(S.GARDEN_LAMPS):
        add_cyl(f"garden_lamp_{i}", x, y, 0, 4.5, 0.15, m["metal"], garden, vertices=8)
        add_cyl(f"garden_lamp_head_{i}", x, y, 4.35, 4.7, 0.35, m["yellow"], garden, vertices=12)

    # road: fences, gate, booth, barrier, pipe, bollards, pallets, sign, T-16/T-18
    add_box("road_fence_w", 107.7, 108.0, -60, -30, 0, 2.2, m["metal"], road)
    add_box("road_fence_e", 132.0, 132.3, -60, -30, 0, 2.2, m["metal"], road)
    g0, g1, gy = S.ROAD_GATE["x0"], S.ROAD_GATE["x1"], S.ROAD_GATE["y"]
    for i, x in enumerate((g0, g1)):
        add_box(f"gate_post_{i}", x - 0.15, x + 0.15, gy - 0.15, gy + 0.15, 0, 5.5, m["metal"], road)
    add_box("gate_beam", g0, g1, gy - 0.25, gy + 0.25, 5.0, 5.5, m["metal"], road)
    add_box("gate_sign", g0 + 1, g1 - 1, gy - 0.05, gy + 0.05, 3.6, 4.6, m["green"], road)
    b = S.ROAD_BOOTH
    add_box("booth", b["x"] - b["w"] / 2, b["x"] + b["w"] / 2, b["y"] - b["d"] / 2, b["y"] + b["d"] / 2, 0, b["h"], m["white"], road)
    add_box("booth_window", b["x"] - 0.5, b["x"] + 0.5, b["y"] + 1.45, b["y"] + 1.52, 1.1, 2.1, m["dark"], road)
    add_box("barrier_post", 115.8, 116.2, -43.2, -42.8, 0, 1.2, m["yellow"], road)
    add_box_local("barrier_arm", 120.0, -43.0, 4.5, 8.0, 0.2, 0.15, m["yellow"], road, rot_y=math.radians(-70))
    p = S.ROAD_PIPE
    for i, off in enumerate((-0.5, 0.0, 0.5)):
        add_cyl(f"road_pipe_{i}", (p["x0"] + p["x1"]) / 2, p["y"] + off,
                p["z"] - 12.0, p["z"] + 12.0, p["dia"] / 2, m["metal"], road, axis="X", vertices=16)
    for i, x in enumerate((110, 130)):
        add_box(f"pipe_pier_{i}", x - 0.3, x + 0.3, p["y"] - 0.3, p["y"] + 0.3, 0, 5.2, m["metal"], road)
    for i, (x, y) in enumerate(S.ROAD_BOLLARDS):
        add_box(f"bollard_{i}", x - 1.0, x + 1.0, y - 0.3, y + 0.3, 0, 0.9, m["yellow"], road)
    for i, (x, y) in enumerate(S.ROAD_PALLETS):
        add_box(f"pallet_{i}", x - 0.8, x + 0.8, y - 0.6, y + 0.6, 0, 1.4, m["container"], road)
    sx, sy = S.ROAD_SIGN
    add_box("road_sign", sx - 0.4, sx + 0.4, sy - 0.05, sy + 0.05, 0.8, 2.0, m["yellow"], road)
    t = S.ROAD_T16
    add_box("t16_bar", t["x0"], t["x1"], t["y"] - 0.3, t["y"] + 0.3, 0.9, 1.1, m["yellow"], workshop)
    for i, x in enumerate((t["x0"], (t["x0"] + t["x1"]) / 2, t["x1"])):
        add_cyl(f"t16_post_{i}", x, t["y"], 0, 1.1, 0.12, m["yellow"], workshop, vertices=8)
    tx, ty = S.ROAD_T18
    add_cyl("t18_pole", tx, ty, 0, 8.0, 0.15, m["metal"], workshop, vertices=8)
    add_box("t18_head", tx - 0.35, tx + 0.35, ty - 0.35, ty + 0.35, 7.7, 8.0, m["yellow"], workshop)

    # workshop walls (north door) + key blocks
    for name, axis, fixed, a, b, openings in [
        ("ws_north", "h", -60, 35, 205, [(114, 126)]),
        ("ws_south", "h", -190, 35, 205, []),
        ("ws_west", "v", 35, -190, -60, []),
        ("ws_east", "v", 205, -190, -60, []),
    ]:
        if axis == "h":
            wall_h(name, fixed, a, b, 9.0, openings, m["wall"], workshop, 1.2)
        else:
            wall_v(name, fixed, a, b, 9.0, openings, m["wall"], workshop, 1.2)
    add_box("ws_green_frame_w", 113.4, 114.0, -60.8, -59.2, 0, 8.0, m["green"], workshop)
    add_box("ws_green_frame_e", 126.0, 126.6, -60.8, -59.2, 0, 8.0, m["green"], workshop)
    add_box("ws_green_sign", 114.0, 126.0, -60.8, -60.2, 8.0, 9.0, m["green"], workshop)
    # T-06 pit
    pit = S.WS_PIT
    add_box("ws_pit", pit["x"] - pit["w"] / 2, pit["x"] + pit["w"] / 2,
            pit["y"] - pit["d"] / 2, pit["y"] + pit["d"] / 2, 0.02, 0.05, m["pit"], workshop)
    for i, (x0, x1, y0, y1) in enumerate([
        (pit["x"] - pit["w"] / 2 - 0.4, pit["x"] + pit["w"] / 2 + 0.4, pit["y"] - pit["d"] / 2 - 0.4, pit["y"] - pit["d"] / 2),
        (pit["x"] - pit["w"] / 2 - 0.4, pit["x"] + pit["w"] / 2 + 0.4, pit["y"] + pit["d"] / 2, pit["y"] + pit["d"] / 2 + 0.4),
        (pit["x"] - pit["w"] / 2 - 0.4, pit["x"] - pit["w"] / 2, pit["y"] - pit["d"] / 2, pit["y"] + pit["d"] / 2),
        (pit["x"] + pit["w"] / 2, pit["x"] + pit["w"] / 2 + 0.4, pit["y"] - pit["d"] / 2, pit["y"] + pit["d"] / 2),
    ]):
        add_box(f"ws_pit_rail_{i}", x0, x1, y0, y1, 0.02, 1.1, m["yellow"], workshop)
    # containers / cover / pipe / evac
    for i, (x, y) in enumerate(S.WS_CONTAINERS):
        add_box(f"ws_container_{i}", x - 3, x + 3, y - 1.2, y + 1.2, 0, 2.6, m["container"], workshop)
    for i, (x, y) in enumerate(S.WS_COVER):
        add_box(f"ws_cover_{i}", x - 3, x + 3, y - 1.2, y + 1.2, 0, 2.6, m["container"], workshop)
    wp = S.WS_PIPE
    for i in range(wp["n"]):
        add_cyl(f"ws_pipe_{i}", (wp["x0"] + wp["x1"]) / 2, wp["y"] + (i - 1.5) * 0.8,
                0.6 - 30.0, 0.6 + 30.0, wp["dia"] / 2, m["metal"], workshop, axis="X", vertices=16)
    ex, ey = S.WS_EVAC
    add_box("evac_frame_n", ex - 2, ex + 2, ey + 1.9, ey + 2.0, 0.03, 0.06, m["evac"], workshop)
    add_box("evac_frame_s", ex - 2, ex + 2, ey - 2.0, ey - 1.9, 0.03, 0.06, m["evac"], workshop)
    add_box("evac_frame_w", ex - 2.0, ex - 1.9, ey - 2, ey + 2, 0.03, 0.06, m["evac"], workshop)
    add_box("evac_frame_e", ex + 1.9, ex + 2.0, ey - 2, ey + 2, 0.03, 0.06, m["evac"], workshop)
    term = S.WS_TERMINAL
    add_box("evac_terminal", term[0] - 0.3, term[0] + 0.3, term[1] - 0.1, term[1] + 0.1, 1.0, 1.8, m["green"], workshop)
    add_box("evac_gate", 204.2, 205.0, -182, -178, 0, 2.2, m["metal"], workshop)


    # L3 floor joints (3 m); H1 gets concentric rings instead of a square grid
    if stage == "final":
        for name, box in (
            ("grid_h2", (0.3, 69.7, 120.3, 189.7)),
            ("grid_h3", (170.3, 239.7, 120.3, 189.7)),
            ("grid_h4", (170.3, 239.7, 0.3, 69.7)),
            ("grid_n", (70, 170, 120, 190)),
            ("grid_s", (70, 170, 0, 70)),
            ("grid_w", (0, 70, 70, 120)),
            ("grid_e", (170, 240, 70, 120)),
        ):
            add_grid(name, box[0], box[1], box[2], box[3], 3.0, 0.047, 0.05, m["seam"], g)
        add_grid("grid_workshop", 35, 205, -190, -60, 3.0, 0.047, 0.05, m["seam"], g)
        add_grid("grid_road", 108, 132, -60, -30, 3.0, 0.047, 0.05, m["seam"], g)
        for r in (6.0, 11.0, 16.0):
            add_tube(f"h1_ring_{int(r)}", 35, 35, r + 0.05, r, 0.048, 0.052, m["white"], g, 64)
        for i in range(8):
            a = math.radians(i * 45)
            add_box_local(f"h1_tick_{i}", 35 + 17 * math.cos(a), 35 + 17 * math.sin(a), 0.05,
                          2.0, 0.08, 0.004, m["orange"], g, rot_z=a)


def build_detail(m, stage):
    """L2-L4 landmarks for the final palette. Graybox intentionally skips this."""
    if stage != "final":
        return
    core = bpy.data.collections["CORE"]
    garden = bpy.data.collections["GARDEN"]
    road = bpy.data.collections["ROAD"]
    workshop = bpy.data.collections["WORKSHOP"]

    def hc(name, x, y, z, length, radius, material, collection=core, rot_z=0.0):
        obj = add_cyl(name, x, y, z - length / 2, z + length / 2, radius, material,
                      collection, axis="X", vertices=20)
        obj.rotation_euler[2] = math.radians(rot_z)

    def rs(prefix, cx, cy, z0):
        for i, dx in enumerate((-5.0, 5.0)):
            add_cyl(f"{prefix}_base_{i}", cx + dx, cy, z0, z0 + 1, 0.8, m["white"], core, vertices=16)
            add_box(f"{prefix}_arm_{i}", cx + dx - 0.3, cx + dx + 0.3, cy - 1.4, cy + 1.4,
                    z0 + 1, z0 + 2.8, m["white"], core)
            add_box(f"{prefix}_joint_{i}", cx + dx - 0.5, cx + dx + 0.5, cy - 0.5, cy + 0.5,
                    z0 + 2.6, z0 + 2.9, m["orange"], core)
        add_box(f"{prefix}_sat", cx - 1.5, cx + 1.5, cy - 1.5, cy + 1.5, z0 + 1.8, z0 + 3.4,
                m["dark"], core)
        for i, rot in enumerate((0, 90, 180, 270)):
            add_box_local(f"{prefix}_wing_{i}", cx, cy, z0 + 2.9, 4.0, 1.5, 0.12,
                          m["yellow"], core, rot_z=math.radians(rot))

    # H1 consoles
    for i in range(6):
        a = math.radians(i * 60)
        x, y = 35 + 16 * math.cos(a), 35 + 16 * math.sin(a)
        add_box(f"h1_console_{i}", x - 3, x + 3, y - 0.6, y + 0.6, 0, 1.1, m["white"], core)
        add_box(f"h1_console_top_{i}", x - 2.8, x + 2.8, y - 0.5, y + 0.5, 1.1, 1.18, m["orange"], core)

    # H2
    add_box("h2_water", 12.2, 56.8, 138.2, 165.8, 0.05, 0.07, m["pool"], core)
    hc("h2_cab_a", 25, 150, 1.6, 12, 1.75, m["white"], rot_z=25)
    hc("h2_cab_b", 50, 178, 1.75, 12, 1.75, m["white"], rot_z=0)
    hc("h2_cab_c", 46, 141, 1.0, 12, 1.75, m["white"], rot_z=-12)
    for i, x in enumerate((10, 60)):
        add_box(f"h2_gantry_leg_{i}", x - 0.6, x + 0.6, 169.4, 170.6, 0, 9, m["metal"], core)
    add_box("h2_gantry_beam", 10, 60, 169.4, 170.6, 8.5, 9.5, m["metal"], core)
    add_box("h2_gantry_trolley", 30, 40, 168.8, 171.2, 7.6, 8.5, m["orange"], core)
    add_cyl("h2_basket", 35, 158, 6, 7, 1.5, m["white"], core, vertices=16)
    add_box("h2_office", 2, 14, 179, 185, 2.2, 5.4, m["white"], core)
    for i in range(4):
        add_box(f"h2_office_win_{i}", 3.5 + i * 2.5, 5.0 + i * 2.5, 178.9, 179.0, 3, 4.4, m["dark"], core)
    add_box("h2_office_stair", 14, 16, 178, 186, 0, 5.4, m["metal"], core)
    add_box("h2_safe", 51.4, 52.6, 175.5, 176.5, 0, 1.5, m["dark"], core)
    add_cyl("h2_safe_dial", 52, 176.5, 0.8, 1.1, 0.2, m["brass"], core, axis="Y", vertices=12)
    # H2 teal band + yellow pool rail
    add_box("h2_band_s", 0.3, 69.7, 120.3, 120.5, 4.0, 5.0, m["teal"], core)
    add_box("h2_band_n", 0.3, 69.7, 189.5, 189.7, 4.0, 5.0, m["teal"], core)
    add_box("h2_band_w", 0.3, 0.5, 120.3, 189.7, 4.0, 5.0, m["teal"], core)
    add_box("h2_band_e", 69.5, 69.7, 120.3, 189.7, 4.0, 5.0, m["teal"], core)
    add_box("h2_rail_s", 12, 57, 166.2, 166.5, 1.0, 1.1, m["yellow"], core)
    add_box("h2_rail_n", 12, 57, 137.5, 137.8, 1.0, 1.1, m["yellow"], core)
    add_box("h2_rail_w", 11.8, 12.1, 138, 166, 1.0, 1.1, m["yellow"], core)
    add_box("h2_rail_e", 56.9, 57.2, 138, 166, 1.0, 1.1, m["yellow"], core)
    for i, (x, y) in enumerate(((80, 80), (160, 80), (80, 105), (160, 105))):
        add_box(f"roof_vent_{i}", x - 3, x + 3, y - 2, y + 2, 9.0, 10.5, m["metal"], core)
        add_cyl(f"roof_pipe_{i}", x, y, 9.0, 11.0, 0.3, m["metal"], core, vertices=10)

    # H3
    add_box("h3_pit_floor", 193.2, 216.8, 144.2, 165.8, 0.05, 0.08, m["pit"], core)
    add_box("h3_blue_n", 192.8, 217.2, 143.8, 144.2, 0.45, 0.55, m["blue"], core)
    add_box("h3_blue_inlay_n", 193.2, 216.8, 144.2, 145.0, 0.08, 0.10, m["blue"], core)
    add_box("h3_blue_inlay_s", 193.2, 216.8, 165.0, 165.8, 0.08, 0.10, m["blue"], core)
    add_box("h3_blue_inlay_w", 193.2, 194.0, 145.0, 165.0, 0.08, 0.10, m["blue"], core)
    add_box("h3_blue_inlay_e", 216.0, 216.8, 145.0, 165.0, 0.08, 0.10, m["blue"], core)
    add_box("h3_blue_s", 192.8, 217.2, 165.8, 166.2, 0.45, 0.55, m["blue"], core)
    add_box("h3_blue_w", 192.8, 193.2, 144.2, 165.8, 0.45, 0.55, m["blue"], core)
    add_box("h3_blue_e", 216.8, 217.2, 144.2, 165.8, 0.45, 0.55, m["blue"], core)
    for i in range(9):
        z = 2 + i
        add_box(f"h3_band_n_{i}", 170.3, 239.7, 189.55, 189.7, z, z + 0.08, m["blue"], core)
        add_box(f"h3_band_e_{i}", 239.55, 239.7, 120.3, 189.7, z, z + 0.08, m["blue"], core)
        add_box(f"h3_band_w_{i}", 170.3, 170.45, 120.3, 189.7, z, z + 0.08, m["blue"], core)
    for name, box in (("n", (193, 217, 166, 167.5)), ("s", (193, 217, 142.5, 144)),
                      ("w", (191.5, 193, 144, 166)), ("e", (217, 218.5, 144, 166))):
        add_box(f"h3_ring_{name}", box[0], box[1], box[2], box[3], 4.5, 4.62, m["metal"], core)
    add_box("h3_ring_rail_n", 193, 217, 167.3, 167.5, 4.62, 5.72, m["yellow"], core)
    add_box("h3_ring_rail_s", 193, 217, 142.5, 142.7, 4.62, 5.72, m["yellow"], core)
    add_box("h3_ring_rail_w", 191.5, 191.7, 144, 166, 4.62, 5.72, m["yellow"], core)
    add_box("h3_ring_rail_e", 218.3, 218.5, 144, 166, 4.62, 5.72, m["yellow"], core)
    rs("h3_robot", 205, 155, 0)
    for i, y in enumerate((150, 155, 160)):
        add_box(f"h3_safe_{i}", 227.4, 228.6, y - 0.5, y + 0.5, 0, 1.5, m["dark"], core)
    for i, y in enumerate((140, 146, 164, 170)):
        add_box(f"h3_shelf_{i}", 221, 223, y - 0.4, y + 0.4, 0, 2.0, m["metal"], core)
    add_box("h3_monitor", 217, 219, 177.5, 178.5, 1.0, 2.2, m["dark"], core)
    add_box("h3_monitor_screen", 217.1, 218.9, 177.4, 177.5, 1.3, 2.0, m["blue"], core)

    # H4
    add_box("h4_arch_w", 173, 173.5, 16, 28, 0, 8, m["white"], core)
    add_box("h4_arch_e", 182.5, 183, 16, 28, 0, 8, m["white"], core)
    add_box("h4_arch_top", 173, 183, 16, 28, 7.5, 8, m["white"], core)
    add_box("h4_arch_floor", 173.5, 182.5, 16, 28, 0.04, 0.07, m["dark"], core)
    hc("h4_hatch", 239.2, 38, 6, 0.8, 6, m["dark"])
    add_torus("h4_hatch_ring", 239.0, 38, 6, 4.6, 0.2, m["white"], core, rot=(0, math.radians(90), 0))
    add_torus("h4_hatch_ring2", 238.9, 38, 6, 2.2, 0.16, m["white"], core, rot=(0, math.radians(90), 0))
    rs("h4_robot", 205, 45, 0)
    add_box("h4_crane_beam", 170, 230, 55.4, 56.6, 10, 11.5, m["metal"], core)
    for i, x in enumerate((170, 230)):
        add_box(f"h4_crane_leg_{i}", x - 0.6, x + 0.6, 55.4, 56.6, 0, 10, m["metal"], core)
    add_cyl("h4_crane_load", 205, 56, 6, 10, 1.5, m["dark"], core, vertices=16)
    add_box("h4_low1", 178, 190, 11.85, 12.15, 0, 3, m["white"], core)
    add_box("h4_low2", 196, 212, 25.85, 26.15, 0, 3, m["white"], core)
    add_box("h4_low3", 186, 198, 39.85, 40.15, 0, 3, m["white"], core)
    for i, (x, y) in enumerate(((178, 63), (184, 63), (190, 63), (178, 67), (184, 67), (190, 67))):
        add_box(f"h4_box_{i}", x - 0.8, x + 0.8, y - 0.4, y + 0.4, 0, 1, m["container_olive"], core)
    for i, x in enumerate((186, 194, 212, 218)):
        add_box(f"h4_south_box_{i}", x - 0.6, x + 0.6, 1.5, 2.3, 0, 1, m["dark"], core)
    add_box("h4_lift", 231, 235, 6, 10, 0.02, 0.06, m["dark"], core)
    add_box("h4_lift_rail", 231, 235, 9.8, 10.0, 0.02, 1.1, m["yellow"], core)

    # stair/bridge/CEO access markers (G3 readability)
    for key, st in S.STAIRS.items():
        for name, box in (("n", (st["x"]-1.5, st["x"]+1.5, st["y"]+1.3, st["y"]+1.5)),
                          ("s", (st["x"]-1.5, st["x"]+1.5, st["y"]-1.5, st["y"]-1.3)),
                          ("w", (st["x"]-1.5, st["x"]-1.3, st["y"]-1.5, st["y"]+1.5)),
                          ("e", (st["x"]+1.3, st["x"]+1.5, st["y"]-1.5, st["y"]+1.5))):
            add_box(f"stair_rail_{key}_{name}", box[0], box[1], box[2], box[3], 9.0, 10.1, m["yellow"], core)
    for i, br in enumerate(S.BRIDGES):
        add_box_local(f"bridge_mark_{i}", br["x"], br["y"], 9.18, 0.12, 3.6, 0.04,
                      m["yellow"], core, rot_z=math.radians(br["rot_z"]))
    add_box("ceo_threshold_w", 99.85, 100.15, 107, 113, 9.05, 9.12, m["yellow"], core)
    add_box("ceo_threshold_e", 139.85, 140.15, 97, 103, 9.05, 9.12, m["yellow"], core)

    # CEO interior
    add_box("ceo_floor_detail", 100.1, 139.9, 90.1, 119.9, 9.05, 9.10, m["stone"], core)
    add_box("ceo_screen", 119.9, 120.1, 106, 114, 9.10, 12.5, m["frost"], core)
    add_box("ceo_safe", 118.75, 121.25, 118.3, 119.5, 9.10, 11.3, m["dark"], core)
    add_cyl("ceo_safe_dial", 120, 118.25, 10.1, 10.5, 0.22, m["brass"], core, axis="Y", vertices=12)
    add_box("ceo_desk", 105, 109, 115.4, 116.6, 9.10, 10.1, m["wood"], core)
    add_box("ceo_desk_screen", 106, 108, 115.2, 115.3, 10.1, 10.9, m["dark"], core)
    add_box("ceo_table", 116, 124, 101, 103, 9.10, 9.78, m["stone"], core)
    add_box("ceo_sofa_w", 104.25, 107.75, 95.4, 96.6, 9.10, 9.85, m["caramel"], core)
    add_box("ceo_sofa_e", 132.25, 135.75, 95.4, 96.6, 9.10, 9.85, m["caramel"], core)
    add_torus("ceo_arm_a", 128, 110, 10.5, 1.5, 0.08, m["brass"], core, rot=(math.radians(90), 0, 0))
    add_torus("ceo_arm_b", 128, 110, 10.5, 1.5, 0.08, m["brass"], core, rot=(0, math.radians(90), 0))
    add_torus("ceo_arm_c", 128, 110, 10.5, 1.5, 0.08, m["brass"], core, rot=(0, 0, math.radians(45)))
    add_cyl("ceo_arm_ball", 128, 110, 10, 11, 0.35, m["brass"], core, vertices=16)
    for i, x in enumerate((104, 112, 120, 128, 136)):
        add_box(f"ceo_bamboo_pot_{i}", x - 0.6, x + 0.6, 92.4, 93.6, 9.10, 9.9, m["white"], core)
        add_cyl(f"ceo_bamboo_{i}", x, 93, 9.9, 12, 0.18, m["foliage"], core, vertices=8)
    for i in range(5):
        add_box(f"ceo_grille_{i}", 128 + i * 1.6, 128.2 + i * 1.6, 119.85, 120.0, 9.10, 12.2, m["wood"], core)
    for i, (x, y) in enumerate(((110, 105), (130, 105))):
        ld = bpy.data.lights.new(f"CEO_Warm_{i}", "AREA")
        ld.shape = "SQUARE"; ld.size = 8; ld.energy = 8
        ld.color = hex_rgba("#FFD9A8")[:3]
        lo = bpy.data.objects.new(f"CEO_Warm_{i}", ld)
        bpy.context.scene.collection.objects.link(lo)
        lo.location = (x, y, 12.8)

    # rings
    for i, x in enumerate((80, 100, 120, 140, 160)):
        for j, y in enumerate((130, 180)):
            add_box(f"n_col_{i}_{j}", x - 0.6, x + 0.6, y - 0.6, y + 0.6, 0, 6, m["white"], core)
    add_box("n_beam_s", 70, 170, 129.4, 130.6, 5.7, 6.3, m["white"], core)
    add_box("n_beam_n", 70, 170, 179.4, 180.6, 5.7, 6.3, m["white"], core)
    add_box("n_band_a", 107, 113, 148, 158, 0, 2.5, m["metal"], core)
    add_box("n_band_b", 147, 153, 152, 162, 0, 2.5, m["metal"], core)
    for i, y in enumerate((135, 150, 165, 180)):
        add_cyl(f"n_lamp_{i}", 120, y, 0, 4.5, 0.15, m["metal"], core, vertices=8)
        add_cyl(f"n_lamp_head_{i}", 120, y, 4.3, 4.7, 0.3, m["yellow"], core, vertices=12)
    for i, (x, y) in enumerate(((8, 78), (60, 78), (8, 112), (60, 112))):
        add_box(f"w_pit_{i}", x - 1.2, x + 1.2, y - 1.2, y + 1.2, 0, 0.6, m["white"], core)
        add_cyl(f"w_trunk_{i}", x, y, 0.6, 3.2, 0.18, m["dark"], core, vertices=8)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.6, location=(x, y, 3.6))
        crown = bpy.context.object
        crown.name = f"w_crown_{i}"
        for c in list(crown.users_collection):
            c.objects.unlink(crown)
        core.objects.link(crown)
        crown.scale.z = 0.55
        crown.data.materials.append(m["foliage"])
    for i in range(4):
        add_cyl(f"w_pipe_{i}", 35, 94.5 + i * 0.5, 5.2 - 35, 5.2 + 35, 0.25, m["metal"], core, axis="X", vertices=12)
    for i, x in enumerate((10, 35, 60)):
        add_box(f"w_support_{i}", x - 0.3, x + 0.3, 94, 95.5, 0, 5, m["metal"], core)
    for i, y in enumerate((88, 102)):
        add_box(f"w_transformer_{i}", 2, 4, y - 1, y + 1, 0, 2.5, m["metal"], core)
    for i, (x, y) in enumerate(((185, 103), (193, 109))):
        add_box(f"e_container_{i}", x - 3, x + 3, y - 1.2, y + 1.2, 0, 2.6,
                m["container_blue"] if i == 0 else m["container_olive"], core)
    add_box("e_platform", 216, 228, 86, 94, 0, 1.2, m["white"], core)
    add_box("e_step", 214.5, 217.5, 89.5, 90.5, 0, 1.2, m["metal"], core)
    add_box("e_forklift", 205, 207.5, 103.4, 104.6, 0, 2, m["orange"], core)
    for i, (x, y) in enumerate(((176, 110), (180, 110), (184, 110), (176, 106))):
        add_box(f"e_cargo_{i}", x - 0.75, x + 0.75, y - 0.75, y + 0.75, 0, 1.2, m["dark"], core)
    for i, (x, y) in enumerate(((172, 72), (238, 72))):
        add_cyl(f"e_lamp_{i}", x, y, 0, 4.5, 0.15, m["metal"], core, vertices=8)
        add_cyl(f"e_lamp_head_{i}", x, y, 4.3, 4.7, 0.3, m["yellow"], core, vertices=12)
    for i, (x, y) in enumerate(((78, 12), (162, 12))):
        add_box(f"s_pit_{i}", x - 1.2, x + 1.2, y - 1.2, y + 1.2, 0, 0.6, m["white"], core)
        add_cyl(f"s_trunk_{i}", x, y, 0.6, 3.2, 0.18, m["dark"], core, vertices=8)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.6, location=(x, y, 3.6))
        crown = bpy.context.object
        crown.name = f"s_crown_{i}"
        for c in list(crown.users_collection):
            c.objects.unlink(crown)
        core.objects.link(crown)
        crown.scale.z = 0.55
        crown.data.materials.append(m["foliage"])

    # garden / road / workshop detail
    add_box("garden_water", 100.2, 139.8, -15.8, -8.2, 0.05, 0.07, m["pool"], garden)
    for i, f in enumerate(S.FOUNTAINS):
        add_cyl(f"fountain_water_{i}", f["x"], f["y"], 0.6, 2.0, 0.35, m["water_light"], garden, vertices=12)
    for i in range(3):
        add_cyl(f"bg_silo_{i}", 145 + i * 8, -45, 0, 7, 2.0, m["metal"], road, vertices=16)
    add_box("bg_bridge", 150, 190, -48, -42, 5.0, 5.6, m["metal"], road)
    add_box("gate_sign_plate", 115, 125, -36.05, -35.95, 3.8, 4.6, m["green"], road)
    add_box("sign_warn", 110.6, 111.4, -37.05, -36.95, 0.8, 2.0, m["yellow"], road)
    add_box("ws_control", 56, 64, -181, -175, 0, 3.5, m["glass"], workshop)
    for i, y in enumerate((-90, -102)):
        add_cyl(f"ws_tank_{i}", 57, y, 0, 5, 2.0, m["white"], workshop, vertices=20)
    for i in range(6):
        add_box(f"ws_tool_{i}", 95 + i * 7, 96.5 + i * 7, -189.4, -188.6, 0, 2, m["metal"], workshop)
    for i, (x, y) in enumerate(((60, -64), (196, -66))):
        add_box(f"ws_scrap_{i}", x - 1.5, x + 1.5, y - 1, y + 1, 0, 0.8, m["metal"], workshop)
    add_box("ws_front_court", 112, 128, -70, -62, 0.02, 0.04, m["road"], workshop)
    for i, (x, y) in enumerate(S.WS_CONTAINERS):
        mat = m["container_blue"] if i % 3 == 0 else (m["container_olive"] if i % 3 == 1 else m["container_gray"])
        add_box(f"ws_container_roof_{i}", x - 2.9, x + 2.9, y - 1.1, y + 1.1, 2.6, 2.7, mat, workshop)
    for i, (x, y) in enumerate(S.WS_COVER):
        add_box(f"ws_cover_roof_{i}", x - 2.9, x + 2.9, y - 1.1, y + 1.1, 2.6, 2.7, m["container_gray"], workshop)
    # CEO frame: corner/mid posts + top perimeter (glass stays clear)
    for i, x in enumerate((100, 120, 140)):
        for j, y in enumerate((90, 120)):
            add_box(f"ceo_post_{i}_{j}", x - 0.08, x + 0.08, y - 0.08, y + 0.08, 9, 13.5, m["brass"], core)
    for j, y in enumerate((90, 120)):
        add_box(f"ceo_top_beam_{j}", 100, 140, y - 0.08, y + 0.08, 13.35, 13.5, m["brass"], core)
    for i, x in enumerate((100, 140)):
        add_box(f"ceo_side_beam_{i}", x - 0.08, x + 0.08, 90, 120, 13.35, 13.5, m["brass"], core)



# ---------------------------------------------------------------- camera/light/render
def build_camera_and_light(m, stage):
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = Vector(S.CAMERA["location"])
    cam.rotation_euler = tuple(math.radians(a) for a in S.CAMERA["rotation_deg"])
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = S.CAMERA["ortho_scale"]
    cam_data.sensor_fit = S.CAMERA["sensor_fit"]
    cam_data.clip_start = S.CAMERA["clip_start"]
    cam_data.clip_end = S.CAMERA["clip_end"]
    bpy.context.scene.camera = cam

    sun_data = bpy.data.lights.new("Sun", "SUN")
    sun = bpy.data.objects.new("Sun", sun_data)
    bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(35), 0, 0)
    sun_data.energy = 3.5 if stage == "final" else 1.5
    sun_data.angle = math.radians(0.6)
    sun_data.color = hex_rgba("#FFF4E6")[:3]

    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = hex_rgba("#D8DEE0")
    bg.inputs["Strength"].default_value = 0.45 if stage == "final" else 0.25

    # broad interior fill, low intensity; final only
    if True:
        for i, (x, y) in enumerate([(35, 35), (35, 155), (205, 155), (205, 35), (120, -125), (120, 35)]):
            ld = bpy.data.lights.new(f"Fill_{i}", "AREA")
            ld.shape = "SQUARE"
            ld.size = 50
            ld.energy = 0.0
            ld.color = hex_rgba("#EAF2F4")[:3]
            lo = bpy.data.objects.new(f"Fill_{i}", ld)
            bpy.context.scene.collection.objects.link(lo)
            lo.location = (x, y, 18)
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.device = "CPU"
    bpy.context.scene.cycles.samples = 16
    bpy.context.scene.cycles.use_denoising = True
    if hasattr(bpy.context.scene.cycles, "denoiser"):
        bpy.context.scene.cycles.denoiser = "OPENIMAGEDENOISE"
    bpy.context.scene.cycles.max_bounces = 4
    bpy.context.scene.cycles.transmission_bounces = 4
    bpy.context.scene.render.film_transparent = False
    bpy.context.scene.view_settings.view_transform = "Standard"
    bpy.context.scene.view_settings.exposure = 0.0 if stage == "final" else -0.2
    try:
        bpy.context.scene.view_settings.look = "None"
    except Exception:
        pass
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGB"
    bpy.context.scene.render.image_settings.compression = 15


def configure_render(res: str, samples: int):
    w, h = [int(v) for v in res.lower().split("x")]
    sc = bpy.context.scene
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.cycles.samples = samples


def render_to(path: str):
    sc = bpy.context.scene
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    a = parse_args()
    clear_scene()
    m = build_materials(a.stage)
    build_base(m, a.stage)
    build_detail(m, a.stage)
    build_camera_and_light(m, a.stage)
    configure_render(a.res, a.samples)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out))
    if a.render:
        os.makedirs(os.path.dirname(os.path.abspath(a.render)), exist_ok=True)
        render_to(os.path.abspath(a.render))
    print("BUILD_OK", a.stage, a.out, a.render)


if __name__ == "__main__":
    main()
