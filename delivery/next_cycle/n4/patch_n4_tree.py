"""Candidate_n4 style-level tree: branch-attached leaf sprigs, not spherical clumps."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
ENV = ROOT / "tools/blender_n4/build_env_courtyard.py"


NEW = '''def _grow_branch(bm, start, direction, length, r0, r1, depth, rng, tips, anchors):
    direction = Vector(direction).normalized()
    p0 = Vector(start)
    side = direction.cross(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                                   rng.uniform(0.2, 1.0)))).normalized()
    bend = side * rng.uniform(0.08, 0.20) + Vector((0, 0, rng.uniform(0.02, 0.08)))
    d1 = (direction + bend * 0.30 + Vector((rng.uniform(-0.05, 0.05),
                                            rng.uniform(-0.05, 0.05), 0.02))).normalized()
    p1 = p0 + (direction * 0.70 + d1 * 0.30).normalized() * (length * 0.38)
    d2 = (d1 + bend * 0.22 + Vector((0, 0, 0.035))).normalized()
    p2 = p1 + d2 * (length * 0.34)
    d3 = (d2 + bend * 0.16 + Vector((rng.uniform(-0.03, 0.03),
                                     rng.uniform(-0.03, 0.03), 0.025))).normalized()
    p3 = p2 + d3 * (length * 0.28)
    rmid0 = r0 * 0.72 + r1 * 0.28
    rmid1 = r0 * 0.35 + r1 * 0.65
    cl.add_cylinder(bm, p0, p1, r0, rmid0, 10, 0)
    cl.add_cylinder(bm, p1, p2, rmid0, rmid1, 9, 0)
    cl.add_cylinder(bm, p2, p3, rmid1, r1, 8, 0)
    if depth <= 0:
        tips.append((p3, d3, r1))
        return
    if depth >= 2:
        anchors.append((p3, d3, r1))
    child_count = 2
    base_axis = direction.cross(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                                        rng.uniform(0.2, 1.0)))).normalized()
    for i in range(child_count):
        angle = math.radians(rng.uniform(25.0, 47.0))
        axis = (base_axis if i % 2 == 0 else -base_axis).normalized()
        child_dir = (direction * math.cos(angle)
                     + axis.cross(direction) * math.sin(angle)
                     + Vector((0, 0, 0.10)))
        child_dir = (child_dir + Vector((rng.uniform(-0.12, 0.12),
                                         rng.uniform(-0.12, 0.12),
                                         rng.uniform(0.02, 0.14)))).normalized()
        _grow_branch(bm, p3, child_dir, length * rng.uniform(0.58, 0.72),
                     r1, r1 * rng.uniform(0.45, 0.56), depth - 1, rng, tips, anchors)


def _add_leaf_sprig(bark_bm, leaf_bm, mass_bm, anchor, direction, scale, rng,
                    warm, leaf_mats, mass_mats):
    """A short twig carrying 3 small leaf clusters; leaves are attached, not floating balls."""
    anchor = Vector(anchor)
    direction = Vector(direction).normalized()
    side = direction.cross(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0.6))).normalized()
    d0 = (direction + side * rng.uniform(-0.12, 0.12) + Vector((0, 0, 0.04))).normalized()
    end = anchor + d0 * (0.34 * scale)
    cl.add_cylinder(bark_bm, anchor, end, 0.020 * scale, 0.006 * scale, 6, 0)
    local = [0.10, 0.20, 0.30]
    for k, t in enumerate(local):
        center = anchor + d0 * (t * scale) + Vector((rng.uniform(-0.05, 0.05),
                                                     rng.uniform(-0.05, 0.05),
                                                     rng.uniform(-0.04, 0.04))) * scale
        cr = (0.11 + 0.025 * k) * scale
        cl.add_mass_lobe(mass_bm, center, cr * 0.55, rng, flatten=0.82,
                         subdiv=2, displace=0.14, mat_index=2)
        cl.add_leaf_cluster(leaf_bm, center, cr * 1.75, 16, rng, warm,
                            leaf_size=rng.uniform(0.07, 0.11) * scale,
                            flatten=0.72, shell_inner=0.30, z_min=-0.85)
        cl.add_leaf_cluster(leaf_bm, center, cr * 1.55, 7, rng, [2, 3, 1],
                            leaf_size=rng.uniform(0.06, 0.09) * scale,
                            flatten=0.82, shell_inner=0.55, z_min=-0.40)


def create_tree(collection, origin=(0, 0, 0), rot=0.0, prefix="ENV006", seed=20261025):
    rng = random.Random(seed)
    bark_mats = [cl.mat_wood_dark(), cl.mat_wood()]
    leaf_mats = [cl.mat_leaf_ochre(), cl.mat_leaf_amber(),
                 cl.mat_leaf_olive(), cl.mat_leaf_deep()]
    mass_mats = [cl.mat_leaf_mass(), cl.mat_leaf_deep()]
    warm = [0, 0, 0, 0, 1, 1, 1, 2, 3]

    bark_bm = bmesh.new()
    leaf_bm = bmesh.new()
    mass_bm = bmesh.new()
    trunk_pts = [(0, 0, 0), (0.05, 0.02, 0.72), (0.11, 0.04, 1.45),
                 (0.10, 0.02, 2.04)]
    radii = [0.34, 0.295, 0.225, 0.170]
    for i in range(3):
        cl.add_cylinder(bark_bm, trunk_pts[i], trunk_pts[i + 1], radii[i],
                        radii[i + 1], 12, 0)
    for i in range(7):
        a = math.tau * i / 7.0 + 0.18
        p0 = (0.06 * math.cos(a), 0.06 * math.sin(a), 0.52)
        p1 = (0.54 * math.cos(a), 0.54 * math.sin(a), 0.004)
        cl.add_cylinder(bark_bm, p0, p1, 0.105, 0.030, 6, 1)

    tips = []
    anchors = []
    fork = Vector((0.10, 0.02, 2.04))
    main_dirs = [(0.62, 0.10, 0.85), (-0.58, 0.36, 0.80),
                 (0.16, -0.62, 0.82), (-0.24, -0.44, 0.90),
                 (0.36, 0.56, 0.76), (-0.36, -0.10, 0.94)]
    for d in main_dirs:
        _grow_branch(bark_bm, fork, d, 2.02, 0.145, 0.032, 4, rng, tips, anchors)
    for (x, y) in ((-0.82, 0.30), (0.80, -0.28), (0.12, 0.84), (-0.20, -0.78)):
        start = Vector((0.08 + x * 0.10, 0.03 + y * 0.10, 1.40))
        _grow_branch(bark_bm, start, (x, y, 0.62), 1.40, 0.105, 0.028, 3, rng, tips, anchors)

    # Core masses: small, dark, hidden behind the attached sprigs.
    core = ((0.0, 0.0, 4.12, 1.10), (-0.55, 0.20, 3.75, 0.86),
            (0.58, -0.30, 3.82, 0.84), (0.10, 0.58, 4.48, 0.80),
            (-0.35, -0.52, 4.35, 0.78), (0.46, 0.32, 4.62, 0.74),
            (-0.62, -0.18, 4.72, 0.68), (0.15, -0.62, 4.15, 0.70))
    for (cx, cy, cz, cr) in core:
        cl.add_mass_lobe(mass_bm, (cx, cy, cz), cr, rng, flatten=0.72,
                         subdiv=2, displace=0.16, mat_index=0)
    # Inner filler sprigs on the core surface.
    for i in range(14):
        a = math.tau * i / 14.0 + rng.uniform(-0.18, 0.18)
        r = rng.uniform(1.0, 1.55)
        z = rng.uniform(3.55, 4.75)
        anchor = (r * math.cos(a), r * math.sin(a), z)
        _add_leaf_sprig(bark_bm, leaf_bm, mass_bm, anchor,
                        (math.cos(a), math.sin(a), rng.uniform(0.1, 0.5)),
                        rng.uniform(0.85, 1.15), rng, warm, leaf_mats, mass_mats)

    # Terminal tips: two attached sprigs per tip plus one on branch junctions.
    for (pos, d, r1) in tips:
        a = rng.uniform(0.0, math.tau)
        out = Vector((d.x + 0.22 * math.cos(a), d.y + 0.22 * math.sin(a),
                      d.z + rng.uniform(-0.05, 0.22))).normalized()
        _add_leaf_sprig(bark_bm, leaf_bm, mass_bm, pos, out,
                        rng.uniform(0.78, 1.10), rng, warm, leaf_mats, mass_mats)
        if rng.random() < 0.65:
            out2 = Vector((d.x + rng.uniform(-0.5, 0.5), d.y + rng.uniform(-0.5, 0.5),
                           d.z + rng.uniform(0.0, 0.25))).normalized()
            _add_leaf_sprig(bark_bm, leaf_bm, mass_bm, pos, out2,
                            rng.uniform(0.62, 0.88), rng, warm, leaf_mats, mass_mats)
    for (pos, d, r1) in anchors[::2]:
        out = Vector((d.x + rng.uniform(-0.25, 0.25), d.y + rng.uniform(-0.25, 0.25),
                      rng.uniform(0.1, 0.5))).normalized()
        _add_leaf_sprig(bark_bm, leaf_bm, mass_bm, pos, out,
                        rng.uniform(0.55, 0.80), rng, warm, leaf_mats, mass_mats)

    # A few outer silhouette sprigs, still attached by short twigs.
    for (x, y, z, sc) in ((1.85, 0.25, 4.30, 0.85), (-1.75, -0.15, 4.45, 0.82),
                          (0.20, -1.85, 4.55, 0.78), (0.40, 1.75, 4.65, 0.76),
                          (1.35, -1.15, 3.95, 0.72), (-1.25, 1.10, 4.05, 0.70)):
        anchor = (x * 0.78, y * 0.78, z - 0.18)
        _add_leaf_sprig(bark_bm, leaf_bm, mass_bm, anchor, (x, y, 0.25),
                        sc, rng, warm, leaf_mats, mass_mats)

    bark = cl.finish_mesh(prefix + "_bark", bark_bm, bark_mats, collection)
    bpy.ops.object.select_all(action="DESELECT")
    bark.select_set(True)
    bpy.context.view_layer.objects.active = bark
    bpy.ops.object.shade_smooth()
    bark.select_set(False)

    mass = cl.finish_mesh(prefix + "_crown_mass", mass_bm, mass_mats, collection)
    bpy.ops.object.select_all(action="DESELECT")
    mass.select_set(True)
    bpy.context.view_layer.objects.active = mass
    bpy.ops.object.shade_smooth()
    mass.select_set(False)
    canopy = cl.finish_mesh(prefix + "_canopy", leaf_bm, leaf_mats, collection)
    for obj in (canopy, mass):
        obj["occlusion_group"] = "OCC_tree_main"
        obj["asset_id"] = "ENV006"
        cl.set_instance(obj, origin, rot)
    bark["collision"] = "circle radius 0.36 at trunk base"
    bark["canopy_occlusion"] = "OCC_tree_main (hide canopy + crown_mass only)"
    print("ENV006 sprig_tree tips=%d anchors=%d" % (len(tips), len(anchors)))
    return [bark, canopy, mass]


'''

s = ENV.read_text(encoding="utf-8")
start = s.index("def _grow_branch(")
end = s.index("def create_ring_planter(", start)
s = s[:start] + NEW + s[end:]
ENV.write_text(s, encoding="utf-8")
print("n4 tree replaced")
