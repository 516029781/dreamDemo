"""Candidate_n4: finer hedge/background foliage, inlay ring, denser foreground."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
MAP = ROOT / "tools/blender_n4/build_map001.py"
s = MAP.read_text(encoding="utf-8")

OLD_HEDGE = '''    for row, (yy, base_z, rr, spacing, count) in enumerate((
            (-11.9, 0.55, 0.66, 1.02, 29),
            (-12.5, 0.42, 0.58, 1.16, 26),
            (-13.1, 0.30, 0.52, 1.30, 23),
            (-13.7, 0.22, 0.47, 1.48, 20))):
        for i in range(count):
            x = -14.0 + i * spacing + (row * 0.18)
            r = rr + rng.uniform(-0.04, 0.10)
            cl.add_mass_lobe(hedge_bm, (x, yy, base_z), r * 0.46, rng,
                             flatten=0.55, subdiv=2, displace=0.16,
                             mat_index=(i + row) % 2)
            cl.add_leaf_cluster(hedge_leaf_bm, (x, yy, base_z + r * 0.30),
                                r * 1.38, 88, rng, [1, 2, 3, 0],
                                leaf_size=rng.uniform(0.10, 0.16),
                                shell_inner=0.70, z_min=-0.30)'''
NEW_HEDGE = '''    for row, (yy, base_z, rr, spacing, count) in enumerate((
            (-11.9, 0.52, 0.66, 1.02, 29),
            (-12.5, 0.40, 0.58, 1.16, 26),
            (-13.1, 0.28, 0.52, 1.30, 23),
            (-13.7, 0.20, 0.47, 1.48, 20))):
        for i in range(count):
            x = -14.0 + i * spacing + (row * 0.18)
            r = rr + rng.uniform(-0.04, 0.10)
            cl.add_mass_lobe(hedge_bm, (x, yy, base_z + 0.08), r * 0.20, rng,
                             flatten=0.60, subdiv=2, displace=0.14,
                             mat_index=(i + row) % 2)
            for k, (dz, cr, ls) in enumerate(((-0.08, 0.52, 1.0),
                                              (0.16, 0.60, 1.08),
                                              (0.38, 0.46, 0.88))):
                cl.add_leaf_cluster(hedge_leaf_bm, (x + rng.uniform(-0.10, 0.10), yy,
                                                    base_z + dz),
                                    r * cr, 30, rng, [1, 2, 3, 0],
                                    leaf_size=rng.uniform(0.085, 0.135) * ls,
                                    flatten=0.76, shell_inner=0.48, z_min=-0.55)'''
assert OLD_HEDGE in s
s = s.replace(OLD_HEDGE, NEW_HEDGE)

OLD_SIDE = '''        for i in range(8):
            y = -8.0 + i * 2.6
            r = 0.58 + rng.uniform(-0.04, 0.08)
            cl.add_mass_lobe(side_bm, (sx, y, 0.50), r * 0.48, rng,
                             flatten=0.55, subdiv=2, displace=0.16,
                             mat_index=i % 2)
            cl.add_leaf_cluster(side_leaf_bm, (sx, y, 0.68), r * 1.35, 40, rng,
                                [1, 2, 3, 0], leaf_size=0.32,
                                shell_inner=0.55, z_min=-0.30)'''
NEW_SIDE = '''        for i in range(9):
            y = -8.4 + i * 2.35
            r = 0.58 + rng.uniform(-0.04, 0.08)
            cl.add_mass_lobe(side_bm, (sx, y, 0.58), r * 0.20, rng,
                             flatten=0.58, subdiv=2, displace=0.14,
                             mat_index=i % 2)
            for (dz, cr) in ((-0.08, 0.54), (0.18, 0.62), (0.40, 0.44)):
                cl.add_leaf_cluster(side_leaf_bm, (sx + rng.uniform(-0.10, 0.10), y,
                                                  0.58 + dz), r * cr, 28, rng,
                                    [1, 2, 3, 0], leaf_size=rng.uniform(0.08, 0.12),
                                    flatten=0.76, shell_inner=0.46, z_min=-0.55)'''
assert OLD_SIDE in s
s = s.replace(OLD_SIDE, NEW_SIDE)

OLD_BAND = '''    for i, (x, y, r, z) in enumerate(distant):
        cl.add_mass_lobe(band_bm, (x, y, z), r * 0.55, rng, flatten=0.62,
                         subdiv=2, displace=0.15, mat_index=i % 2)
        cl.add_leaf_cluster(band_cards, (x, y, z), r * 1.28, 92, rng,
                            [2, 2, 3, 1], leaf_size=0.17,
                            shell_inner=0.70, z_min=-0.30)'''
NEW_BAND = '''    for i, (x, y, r, z) in enumerate(distant):
        cl.add_mass_lobe(band_bm, (x, y, z), r * 0.25, rng, flatten=0.62,
                         subdiv=2, displace=0.15, mat_index=i % 2)
        for (dx, dz, cr) in ((-0.52, -0.10, 0.62), (0.45, 0.06, 0.58),
                             (0.0, 0.30, 0.52)):
            cl.add_leaf_cluster(band_cards, (x + r * dx, y, z + r * dz),
                                r * cr, 42, rng, [2, 2, 3, 1],
                                leaf_size=rng.uniform(0.09, 0.14),
                                flatten=0.76, shell_inner=0.46, z_min=-0.55)'''
assert OLD_BAND in s
s = s.replace(OLD_BAND, NEW_BAND)

OLD_TREE = '''            cl.add_mass_lobe(tree_leaf_bm, center, tr * rr, rng, flatten=0.72,
                             subdiv=2, displace=0.18, mat_index=li % 2)
            cl.add_leaf_cluster(tree_leaf_bm, center, tr * rr * 1.45, 64, rng,
                                [2, 2, 3, 1], leaf_size=0.16,
                                shell_inner=0.70, z_min=-0.34)'''
NEW_TREE = '''            cl.add_mass_lobe(tree_leaf_bm, center, tr * rr * 0.38, rng, flatten=0.72,
                             subdiv=2, displace=0.18, mat_index=li % 2)
            for (dx, dy, dz, cr) in ((0.0, 0.0, 0.0, 0.52), (-0.28, 0.10, 0.12, 0.40),
                                     (0.26, -0.08, 0.08, 0.38)):
                cl.add_leaf_cluster(tree_leaf_bm,
                                    (center[0] + tr * rr * dx,
                                     center[1] + tr * rr * dy,
                                     center[2] + tr * rr * dz),
                                    tr * rr * cr, 30, rng, [2, 2, 3, 1],
                                    leaf_size=rng.uniform(0.075, 0.12),
                                    flatten=0.76, shell_inner=0.46, z_min=-0.55)'''
assert OLD_TREE in s
s = s.replace(OLD_TREE, NEW_TREE)

# Add an inlay ring and moss/leaf patches in the foreground detail function.
OLD_FG = '''    rng = random.Random(20261025 + 3)
    stone, light, dark = cl.mat_stone_base(), cl.mat_stone_light(), cl.mat_stone_dark()
    soil_mat = cl.mat_soil()'''
NEW_FG = '''    rng = random.Random(20261025 + 3)
    stone, light, dark = cl.mat_stone_base(), cl.mat_stone_light(), cl.mat_stone_dark()
    soil_mat = cl.mat_soil()
    # Thin dark stone inlay ring frames the hero planter without adding a collider.
    inlay_bm = bmesh.new()
    cl.add_solid_ring(inlay_bm, 3.06, 3.13, 0.002, 0.010, segments=96, mat_index=2)
    inlay = cl.finish_mesh("MAP001_fg_inlay_ring", inlay_bm, [stone, light, dark], collection)
    inlay["asset_id"] = "SCENERY"
    inlay["role"] = "stone inlay ring around hero planter; visual only"'''
assert OLD_FG in s
s = s.replace(OLD_FG, NEW_FG)

OLD_BED = '''        leaves = bmesh.new()
        for cx, cz, cr in ((-0.55, 0.0, 0.42), (0.50, 0.05, 0.38),
                           (0.0, -0.25, 0.34)):
            cl.add_leaf_cluster(leaves, (cx, cz, 0.34), cr, 54, rng,
                                [1, 1, 2, 3, 0], leaf_size=0.28,
                                shell_inner=0.55, z_min=-0.30)'''
NEW_BED = '''        leaves = bmesh.new()
        for cx, cz, cr in ((-0.55, 0.0, 0.42), (0.50, 0.05, 0.38),
                           (0.0, -0.25, 0.34)):
            for (dx, dz, dz2, lf) in ((0.0, 0.0, 0.0, 0.16),
                                      (-0.18, 0.12, 0.14, 0.13),
                                      (0.20, -0.10, 0.10, 0.12)):
                cl.add_leaf_cluster(leaves, (cx + dx, cz + dz, 0.26 + dz2),
                                    cr * 0.75, 38, rng, [1, 1, 2, 3, 0],
                                    leaf_size=lf, flatten=0.72,
                                    shell_inner=0.45, z_min=-0.55)'''
assert OLD_BED in s
s = s.replace(OLD_BED, NEW_BED)

MAP.write_text(s, encoding="utf-8")
print("n4 map foliage/foreground patched")
