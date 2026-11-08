"""v02 L2/L3 detail pass on top of the v01 scene.

Run:
  blender -b art/static_map/space_base_minigame/v02/scene.blend \
    --python tools/blender_space_base/build_detail_v2.py -- --save

Only adds detail; no layout/camera changes. Uses procedural materials from v01.
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import bpy
from mathutils import Vector


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", action="store_true")
    return ap.parse_args(argv)


def C(name):
    return bpy.data.collections[name]


def M(name):
    m = bpy.data.materials.get(name)
    if m is None:
        raise RuntimeError(f"missing material {name}")
    return m


def box(name, x0, x1, y0, y1, z0, z1, material, collection):
    mesh = bpy.data.meshes.new(name)
    verts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh.from_pydata(verts, [], faces)
    mesh.validate(); mesh.update()
    o = bpy.data.objects.new(name, mesh)
    collection.objects.link(o)
    o.data.materials.append(material)
    return o


def box_local(name, cx, cy, cz, dx, dy, dz, material, collection, rot_z=0.0, rot_y=0.0):
    mesh = bpy.data.meshes.new(name)
    hx, hy, hz = dx / 2, dy / 2, dz / 2
    verts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
             (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    mesh.from_pydata(verts, [], faces)
    mesh.validate(); mesh.update()
    o = bpy.data.objects.new(name, mesh)
    collection.objects.link(o)
    o.location = (cx, cy, cz)
    o.rotation_euler = (0, rot_y, rot_z)
    o.data.materials.append(material)
    return o


def cyl(name, x, y, z0, z1, radius, material, collection, axis="Z", vertices=16, rot_z=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=z1 - z0,
                                        location=(x, y, (z0 + z1) / 2))
    o = bpy.context.object
    o.name = name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    collection.objects.link(o)
    o.data.materials.append(material)
    if axis == "X":
        o.rotation_euler[1] = math.radians(90)
    elif axis == "Y":
        o.rotation_euler[0] = math.radians(90)
    o.rotation_euler[2] += rot_z
    return o


def sphere(name, x, y, z, radius, material, collection, scale_z=0.55):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius, location=(x, y, z))
    o = bpy.context.object
    o.name = name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    collection.objects.link(o)
    o.scale.z = scale_z
    o.data.materials.append(material)
    return o


def main():
    a = args()
    core, garden, road, workshop = C("CORE"), C("GARDEN"), C("ROAD"), C("WORKSHOP")
    wall, wall_h4 = M("f.wall"), M("f.wall_h4")
    metal, dark, white = M("f.metal"), M("f.dark"), M("f.white")
    teal, blue, orange = M("f.teal"), M("f.blue"), M("f.orange")
    yellow, brass, wood = M("f.yellow"), M("f.brass"), M("f.wood")
    caramel, foliage = M("f.caramel"), M("f.foliage")
    cblue, colive, cgray = M("f.container_blue"), M("f.container_olive"), M("f.container_gray")
    pool, pit, stone = M("f.pool"), M("f.pit"), M("f.stone")
    green, frost, evac = M("f.green"), M("f.frost"), M("f.evac")
    seam, roadmat = M("f.seam"), M("f.road")

    # ---------------- H1 consoles / window mullions / equipment
    for i in range(6):
        ang = math.radians(i * 60)
        x, y = 35 + 16 * math.cos(ang), 35 + 16 * math.sin(ang)
        box_local(f"v2_h1_desk_{i}", x, y, 0.59, 6.0, 1.2, 1.18, dark, core, rot_z=ang + math.pi / 2)
        xi, yi = 35 + 15.55 * math.cos(ang), 35 + 15.55 * math.sin(ang)
        box_local(f"v2_h1_scr_{i}", xi, yi, 1.35, 1.6, 0.12, 0.34, blue, core, rot_z=ang + math.pi / 2)
        box_local(f"v2_h1_led_{i}", xi - 0.12 * math.cos(ang), yi - 0.12 * math.sin(ang), 1.215,
                  0.18, 0.12, 0.07, orange, core, rot_z=ang + math.pi / 2)
    for i in range(12):
        ang = math.radians(i * 30)
        x, y = 35 + 19 * math.cos(ang), 35 + 19 * math.sin(ang)
        box(f"v2_h1_mull_{i}", x - 0.07, x + 0.07, y - 0.07, y + 0.07, 4.5, 5.5, white, core)
    for i, (x, y) in enumerate(((4, 66), (66, 66), (67, 4), (4, 4))):
        box(f"v2_h1_eq_{i}", x - 1.5, x + 1.5, y - 1.0, y + 1.0, 0, 1.8, metal, core)
        box(f"v2_h1_eqscreen_{i}", x - 0.8, x + 0.8, y + 1.0, y + 1.1, 0.8, 1.6, blue, core)
    for i, y in enumerate((20, 32, 44, 56)):
        box(f"v2_h1_handle_{i}", 3.3, 3.45, y - 0.15, y + 0.15, 0.8, 1.3, brass, core)

    # ---------------- H2 cabins / gantry / office / pool rail
    for i, (x, y, zc) in enumerate(((25, 150, 3.3), (50, 178, 3.5), (46, 141, 2.9))):
        box(f"v2_h2_hatch_{i}", x - 1.0, x + 1.0, y - 1.0, y + 1.0, zc, zc + 0.18, dark, core)
        box(f"v2_h2_band_{i}", x - 3.0, x + 3.0, y - 0.25, y + 0.25, zc + 0.02, zc + 0.12, orange, core)
    for i, x in enumerate((33, 37)):
        cyl(f"v2_h2_cable_{i}", x, 164, 7.0, 9.4, 0.05, dark, core, vertices=6)
    box("v2_h2_hook", 33.8, 36.2, 163.8, 164.2, 6.6, 6.9, metal, core)
    for i in range(5):
        box(f"v2_h2_office_mull_{i}", 3.5 + i * 2.5, 3.6 + i * 2.5, 178.85, 178.95, 3.0, 4.5, metal, core)
    box("v2_h2_office_door", 12.5, 13.5, 178.85, 178.95, 2.2, 4.4, dark, core)
    for i, (x, y) in enumerate(((12.2, 138.2), (12.2, 152), (12.2, 166), (57, 138.2), (57, 152), (57, 166))):
        box(f"v2_h2_railpost_{i}", x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0.42, 1.2, yellow, core)
    for i, x in enumerate((20, 30, 40, 50)):
        box(f"v2_h2_valve_{i}", x - 0.2, x + 0.2, 137.4, 137.8, 0.6, 1.0, orange, core)

    # ---------------- H3 safes / shelves / monitor / dish
    for i, y in enumerate((150, 155, 160)):
        box(f"v2_h3_safe_handle_{i}", 228.6, 228.9, y - 0.15, y + 0.15, 0.8, 1.2, brass, core)
    for i, y in enumerate((140, 146, 164, 170)):
        for j, z in enumerate((0.3, 1.1)):
            box(f"v2_h3_shelfbox_{i}_{j}", 221.1, 222.5, y - 0.35, y + 0.35, z, z + 0.55, dark, core)
    box("v2_h3_monitor_stand", 217.5, 218.5, 177.7, 178.3, 0.0, 1.0, metal, core)
    cyl("v2_h3_dish", 205, 155, 3.4, 3.8, 0.8, white, core, vertices=16)
    for i, dx in enumerate((-1.0, 1.0)):
        box(f"v2_h3_dish_rod_{i}", 205 + dx - 0.05, 205 + dx + 0.05, 153.8, 156.2, 3.6, 3.9, white, core)
    for i, (x, y) in enumerate(((194, 145), (216, 145), (194, 165), (216, 165))):
        box(f"v2_h3_crate_strap_{i}", x - 0.65, x + 0.65, y - 0.1, y + 0.1, 0.75, 1.02, orange, core)

    # ---------------- H4 hatch ribs / arch / crane / elevator
    for i in range(8):
        ang = math.radians(i * 45)
        y, z = 38 + 4.2 * math.cos(ang), 6 + 4.2 * math.sin(ang)
        box(f"v2_h4_hatch_rib_{i}", 239.0, 239.12, y - 0.12, y + 0.12, z - 0.4, z + 0.4, white, core)
    box("v2_h4_hatch_hub", 238.9, 239.1, 37.6, 38.4, 5.6, 6.4, brass, core)
    for i, y in enumerate((18, 22, 26)):
        box(f"v2_h4_arch_rib_{i}", 173, 183, y - 0.15, y + 0.15, 7.7, 8.0, white, core)
    for i, x in enumerate((203.3, 206.7)):
        cyl(f"v2_h4_cable_{i}", x, 56, 6.2, 10.0, 0.05, dark, core, vertices=6)
    box("v2_h4_hook", 203.1, 206.9, 55.8, 56.2, 5.8, 6.1, metal, core)
    for i, (x, y) in enumerate(((231.2, 6.2), (234.8, 6.2), (231.2, 9.8), (234.8, 9.8))):
        box(f"v2_h4_lift_post_{i}", x - 0.08, x + 0.08, y - 0.08, y + 0.08, 0.0, 1.2, yellow, core)
    for i, y in enumerate((16, 24, 32, 40, 48, 56, 64)):
        box(f"v2_h4_pipe_r_{i}", 239.30, 239.50, y - 2.0, y + 2.0, 12.2, 12.4, orange, core)
    box("v2_h4_pipe_b", 239.50, 239.70, 12, 66, 12.0, 12.2, blue, core)

    # ---------------- CEO mullions / chairs / details
    for i in range(8):
        x = 103.5 + i * 5.0
        box(f"v2_ceo_mull_n_{i}", x - 0.06, x + 0.06, 89.9, 90.05, 9.0, 13.5, brass, core)
        box(f"v2_ceo_mull_s_{i}", x - 0.06, x + 0.06, 119.95, 120.1, 9.0, 13.5, brass, core)
    for i, (x, y) in enumerate(((117.5, 100.5), (118.5, 100.5), (121.5, 100.5), (122.5, 100.5),
                                (117.5, 103.5), (122.5, 103.5))):
        box(f"v2_ceo_chair_{i}", x - 0.3, x + 0.3, y - 0.3, y + 0.3, 9.1, 9.7, dark, core)
    for i, (x, y) in enumerate(((119.0, 101.5), (121.0, 101.5), (120.0, 102.2))):
        box(f"v2_ceo_table_item_{i}", x - 0.15, x + 0.15, y - 0.12, y + 0.12, 9.78, 9.9, brass, core)
    for i, (x, y) in enumerate(((106.0, 96.0), (107.0, 96.0), (133.0, 96.0), (134.0, 96.0))):
        box(f"v2_ceo_cushion_{i}", x - 0.4, x + 0.4, y - 0.45, y + 0.45, 9.85, 10.05, white, core)
    for i, x in enumerate((104, 112, 120, 128, 136)):
        cyl(f"v2_ceo_stem_{i}", x, 93.0, 9.85, 11.2, 0.04, foliage, core, vertices=8)
        sphere(f"v2_ceo_leaf_{i}", x, 93.0, 11.2, 0.45, foliage, core, 0.7)
    for i, (x, y) in enumerate(((110, 105), (120, 105), (130, 105), (120, 115))):
        box(f"v2_ceo_downlight_{i}", x - 0.35, x + 0.35, y - 0.35, y + 0.35, 13.32, 13.4, yellow, core)

    # ---------------- garden tree clusters / fountains / benches
    for i, (x, y) in enumerate(((40, -10), (200, -10), (80, -22), (160, -22))):
        sphere(f"v2_tree_cluster_a_{i}", x + 0.8, y + 0.4, 3.8, 1.0, foliage, garden, 0.65)
        sphere(f"v2_tree_cluster_b_{i}", x - 0.8, y - 0.4, 3.5, 0.9, foliage, garden, 0.6)
    for i, (x, y) in enumerate(((110, -12), (130, -12))):
        cyl(f"v2_fountain_spray_{i}", x, y, 0.6, 2.2, 0.08, M("f.water_light"), garden, vertices=8)
    for i, (x, y) in enumerate(((95, -27), (145, -27), (120, -5))):
        for j in range(3):
            box(f"v2_bench_slat_{i}_{j}", x - 0.9, x + 0.9, y - 0.3 + j * 0.2, y - 0.18 + j * 0.2, 0.45, 0.5, wood, garden)
        box(f"v2_bench_arm_{i}_a", x - 0.9, x - 0.75, y - 0.3, y + 0.3, 0.45, 0.7, metal, garden)
        box(f"v2_bench_arm_{i}_b", x + 0.75, x + 0.9, y - 0.3, y + 0.3, 0.45, 0.7, metal, garden)
    for i, (x0, x1, y0, y1) in enumerate(((99.8, 140.2, -16.2, -16.0), (99.8, 140.2, -8.0, -7.8),
                                          (99.8, 100.0, -16.0, -8.0), (140.0, 140.2, -16.0, -8.0))):
        box(f"v2_garden_pool_tile_{i}", x0, x1, y0, y1, 0.42, 0.46, white, garden)

    # ---------------- rings
    for i, x in enumerate((80, 100, 120, 140, 160)):
        for j, y in enumerate((130, 180)):
            box(f"v2_col_base_{i}_{j}", x - 0.7, x + 0.7, y - 0.7, y + 0.7, 0, 0.35, metal, core)
            box(f"v2_col_cap_{i}_{j}", x - 0.7, x + 0.7, y - 0.7, y + 0.7, 5.65, 6.0, white, core)
    for i, x in enumerate((107.6, 112.4)):
        cyl(f"v2_n_band_pipe_{i}", x, 153, 2.55, 2.75, 0.18, teal, core, axis="Y", vertices=10)
    for i, y in enumerate((94.5, 95.0, 95.5, 96.0)):
        cyl(f"v2_w_flange_{i}", 20 + i * 8, y, 5.15, 5.45, 0.34, dark, core, axis="Y", vertices=10)
    for i, y in enumerate((88, 102)):
        for j in range(4):
            box(f"v2_transformer_fin_{i}_{j}", 1.7, 2.0, y - 0.8 + j * 0.4, y - 0.7 + j * 0.4, 0.4, 2.2, metal, core)
    for i, (x0, x1, y0, y1) in enumerate(((216, 228, 86, 86.2), (216, 228, 93.8, 94.0),
                                          (216, 216.2, 86, 94), (227.8, 228, 86, 94))):
        box(f"v2_e_platform_rail_{i}", x0, x1, y0, y1, 1.2, 2.2, yellow, core)
    for i, (x, y) in enumerate(((176, 110), (180, 110), (184, 110), (176, 106))):
        box(f"v2_e_cargo_strap_{i}", x - 0.8, x + 0.8, y - 0.1, y + 0.1, 1.2, 1.25, dark, core)
    for i, x in enumerate((205.8, 206.8)):
        box(f"v2_e_fork_{i}", x - 0.08, x + 0.08, 104.6, 106.2, 0.0, 0.12, metal, core)
    for i, (x, y) in enumerate(((78, 12), (162, 12))):
        sphere(f"v2_s_tree_cluster_{i}", x + 0.7, y, 3.8, 0.9, foliage, core, 0.6)

    # ---------------- corridor detail
    for i, x in enumerate((117, 120, 123)):
        box(f"v2_gate_arrow_{i}", x - 0.25, x + 0.25, -36.05, -35.95, 4.0, 4.4, white, road)
    box("v2_booth_desk", 110.8, 113.2, -42.8, -41.8, 0.8, 1.0, wood, road)
    box("v2_booth_door", 111.3, 112.7, -43.5, -43.4, 0.0, 2.2, dark, road)
    for i in range(4):
        box(f"v2_barrier_stripe_{i}", 117 + i * 1.8, 117.35 + i * 1.8, -43.12, -42.88, 1.02, 1.13, dark, road)
    for i, x in enumerate((110, 118, 126, 130)):
        cyl(f"v2_pipe_flange_{i}", x, -49, 5.15, 5.45, 0.34, dark, road, axis="Y", vertices=10)
    for i in range(10):
        y = -59 + i * 3.2
        box(f"v2_fence_post_{i}", 107.7, 108.1, y - 0.08, y + 0.08, 0, 2.2, metal, road)
    for i, (x, y) in enumerate(((109, -34), (109, -44), (109, -54), (131, -39), (131, -49), (131, -57))):
        box(f"v2_bollard_stripe_{i}", x - 1.0, x + 1.0, y - 0.3, y + 0.3, 0.75, 0.9, white, road)
    for i, (x, y) in enumerate(((127, -35), (129, -39))):
        box(f"v2_pallet_strap_{i}", x - 0.8, x + 0.8, y - 0.05, y + 0.05, 1.4, 1.45, dark, road)
    for i in range(3):
        cyl(f"v2_silo_ring_{i}", 145 + i * 8, -45, 4.0, 4.2, 2.05, dark, road, vertices=16)
    for i, x in enumerate((155, 185)):
        box(f"v2_bridge_cable_{i}", x - 0.05, x + 0.05, -48, -42, 5.6, 7.0, dark, road)

    # ---------------- workshop detail
    for i, (x, y) in enumerate(((43, -170), (43, -160), (43, -150), (43, -140), (65, -70), (75, -70))):
        box(f"v2_container_door_{i}", x + 3.0, x + 3.12, y - 1.0, y + 1.0, 0.2, 2.4, dark, workshop)
        for j in range(5):
            rx = x - 2.4 + j * 1.2
            box(f"v2_container_rib_{i}_{j}", rx - 0.08, rx + 0.08, y - 1.28, y - 1.20, 0.2, 2.4, dark, workshop)
    for i, y in enumerate((-90, -102)):
        for j, x in enumerate((54.8, 59.2)):
            box(f"v2_tank_ladder_{i}_{j}", x - 0.06, x + 0.06, y, y + 0.1, 0.0, 5.0, metal, workshop)
        cyl(f"v2_tank_pipe_{i}", 57, y, 5.0, 6.0, 0.18, metal, workshop, vertices=10)
    box("v2_control_desk", 58, 62, -179, -177.5, 0.9, 1.0, wood, workshop)
    box("v2_control_screen", 59, 61, -179.1, -179.0, 1.0, 1.6, blue, workshop)
    for i in range(6):
        box(f"v2_tool_handle_{i}", 95 + i * 7.2, 95.5 + i * 7.2, -189.4, -189.3, 1.0, 1.3, brass, workshop)
    for i, x in enumerate((120, 130, 140, 150)):
        cyl(f"v2_ws_pipe_flange_{i}", x, -165, 0.3, 0.9, 0.35, dark, workshop, axis="Y", vertices=10)
    box("v2_evac_screen", 202.9, 203.1, -180.2, -179.8, 1.25, 1.55, blue, workshop)
    for i, y in enumerate((-182, -180, -178)):
        box(f"v2_evac_gate_bar_{i}", 204.2, 204.3, y - 0.03, y + 0.03, 0.0, 2.2, metal, workshop)
    for i, x in enumerate((116, 118, 120, 122)):
        box(f"v2_t16_stripe_{i}", x - 0.25, x + 0.25, -62.2, -61.8, 0.95, 1.1, dark, workshop)
    box("v2_t18_glow", 127.7, 128.3, -64.3, -63.7, 7.4, 8.0, yellow, workshop)

    # ---------------- L3 signs / guide line / arrows
    box("v2_h1_sign", 0.30, 0.36, 13.8, 16.2, 5.6, 8.6, blue, core)
    box("v2_h1_sign_txt", 0.36, 0.37, 14.2, 15.8, 6.4, 8.2, white, core)
    box("v2_h2_sign", 0.30, 0.36, 148.8, 151.2, 6.6, 9.6, blue, core)
    box("v2_h2_sign_txt", 0.36, 0.37, 149.2, 150.8, 7.4, 9.2, white, core)
    box("v2_h3_sign", 239.64, 239.70, 148.8, 151.2, 7.6, 10.6, blue, core)
    box("v2_h3_sign_txt", 239.63, 239.64, 149.2, 150.8, 8.4, 10.2, white, core)
    box("v2_h4_sign", 239.64, 239.70, 28.8, 31.2, 9.6, 12.6, blue, core)
    box("v2_h4_sign_txt", 239.63, 239.64, 29.2, 30.8, 10.4, 12.2, white, core)
    box("v2_ceo_sign", 116, 124, 69.9, 70.0, 1.4, 3.4, blue, core)
    for i, (y, x0, x1) in enumerate(((70.3, 32, 38), (120.3, 32, 38), (120.3, 202, 208))):
        box(f"v2_door_sign_{i}", x0, x1, y, y + 0.1, 3.2, 3.8, white, core)
    # green guide line on road + bend
    box("v2_green_line_a", 119.92, 120.08, -60, -30, 0.08, 0.10, green, road)
    box("v2_green_line_b", 120.0, 124.0, -61.0, -60.8, 0.08, 0.10, green, road)
    for i, (x, y) in enumerate(((126, -70), (150, -100), (180, -150))):
        box(f"v2_evac_arrow_{i}", x - 0.6, x + 0.6, y - 0.15, y + 0.15, 0.08, 0.10, yellow, workshop)
    # S-04 corridor guide line and H4/T-14 floor markings
    box("v2_s04_line", 70, 170, 35.0, 35.15, 0.08, 0.10, white, core)
    for i, (x0, x1) in enumerate(((175, 195), (205, 235))):
        box(f"v2_h4_floor_line_{i}", x0, x1, 3.0, 3.15, 0.08, 0.10, yellow, core)
    box("v2_ws_line_s", 36.0, 204.0, -187.4, -187.25, 0.08, 0.10, yellow, workshop)
    box("v2_ws_line_n_w", 36.0, 114.0, -62.75, -62.60, 0.08, 0.10, yellow, workshop)
    box("v2_ws_line_n_e", 126.0, 204.0, -62.75, -62.60, 0.08, 0.10, yellow, workshop)
    box("v2_ws_line_w", 36.75, 36.90, -187.4, -62.6, 0.08, 0.10, yellow, workshop)
    box("v2_ws_line_e", 203.1, 203.25, -187.4, -62.6, 0.08, 0.10, yellow, workshop)

    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(bpy.data.filepath))
    print("DETAIL_V2_OK", len([o for o in bpy.data.objects if o.type == "MESH"]))


if __name__ == "__main__":
    main()
