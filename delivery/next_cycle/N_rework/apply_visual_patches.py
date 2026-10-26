"""Apply N01/N03 source patches (tree, hedge, groundcover, paper texture, UI already in TS)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# --- tree ---
p = ROOT / "tools/blender/build_env_courtyard.py"
s = p.read_text(encoding="utf-8")
s = s.replace("bend = Vector((rng.uniform(-0.17, 0.17), rng.uniform(-0.17, 0.17),\n                   rng.uniform(0.02, 0.10)))",
              "bend = Vector((rng.uniform(-0.24, 0.24), rng.uniform(-0.24, 0.24),\n                   rng.uniform(0.02, 0.12)))")
s = s.replace("    child_count = 2 if depth == 1 else 3", "    child_count = 2")
s = s.replace("        _grow_branch(bm, fork, d, 1.78, 0.150, 0.060, 2, rng, tips)",
              "        _grow_branch(bm, fork, d, 1.86, 0.155, 0.055, 3, rng, tips)")
s = s.replace("        _grow_branch(bm, start, (x, y, 0.62), 1.18, 0.115, 0.050, 1, rng, tips)",
              "        _grow_branch(bm, start, (x, y, 0.62), 1.22, 0.120, 0.045, 1, rng, tips)")
old = """    clump_pattern = ((0.72, 0.18, 0.16), (-0.62, 0.40, 0.22),
                     (0.05, -0.70, 0.26), (-0.25, 0.60, 0.34),
                     (0.55, -0.45, 0.02))
    for i, (x, y, z, r) in enumerate(lobes + break_lobes):
        for (dx, dy, dz) in clump_pattern:
            d = Vector((dx, dy, dz)).normalized()
            center = Vector((x, y, z)) + Vector((d.x * r * 0.62,
                                                 d.y * r * 0.62,
                                                 d.z * r * 0.46))
            cr = max(0.40, r * 0.38)
            cl.add_mass_lobe(mass_bm, center, cr, rng, flatten=0.80,
                             subdiv=2, displace=0.14,
                             mat_index=1 if i % 3 == 0 else 0)
            cl.add_leaf_cluster(leaf_bm, center, cr * 1.06, 40, rng, warm,
                                leaf_size=0.40, shell_inner=0.70,
                                z_min=-0.30)
            cl.add_leaf_cluster(leaf_bm, center, cr * 1.04, 6, rng, [0, 1],
                                leaf_size=0.56, shell_inner=0.95, z_min=0.0)
            leaf_count += 46
            cluster_count += 1"""
new = """    clump_pattern = ((0.75, 0.12, 0.18), (-0.68, 0.35, 0.22),
                     (0.08, -0.74, 0.28), (-0.22, 0.62, 0.34),
                     (0.58, -0.48, 0.04), (0.25, 0.55, -0.12))
    for i, (x, y, z, r) in enumerate(lobes + break_lobes):
        for (dx, dy, dz) in clump_pattern:
            d = Vector((dx, dy, dz)).normalized()
            jitter = Vector((rng.uniform(-0.10, 0.10),
                             rng.uniform(-0.10, 0.10),
                             rng.uniform(-0.08, 0.08)))
            center = Vector((x, y, z)) + Vector((d.x * r * 0.60,
                                                 d.y * r * 0.60,
                                                 d.z * r * 0.46)) + jitter * r * 0.25
            cr = max(0.30, r * rng.uniform(0.28, 0.36))
            cl.add_mass_lobe(mass_bm, center, cr, rng, flatten=0.82,
                             subdiv=2, displace=0.15,
                             mat_index=1 if i % 3 == 0 else 0)
            palette = warm if i % 3 else [1, 1, 2, 3, 0]
            cards = int(rng.uniform(58, 76))
            cl.add_leaf_cluster(leaf_bm, center, cr * 1.07, cards, rng, palette,
                                leaf_size=rng.uniform(0.34, 0.48),
                                shell_inner=0.58, z_min=-0.36)
            cl.add_leaf_cluster(leaf_bm, center, cr * 1.04, 9, rng, [0, 1, 2],
                                leaf_size=0.52, shell_inner=0.92, z_min=0.0)
            leaf_count += cards + 9
            cluster_count += 1
    # A few small outer clusters break the repeated lobe silhouette.
    for (x, y, z, r) in ((1.65, 0.10, 4.15, 0.45), (-1.55, 0.25, 4.25, 0.42),
                         (0.15, -1.55, 4.55, 0.40), (0.30, 1.45, 4.85, 0.38)):
        cl.add_mass_lobe(mass_bm, (x, y, z), r * 0.86, rng, flatten=0.82,
                         subdiv=2, displace=0.15, mat_index=2)
        cl.add_leaf_cluster(leaf_bm, (x, y, z), r * 1.12, 48, rng, warm,
                            leaf_size=0.40, shell_inner=0.58, z_min=-0.30)
        leaf_count += 48
        cluster_count += 1"""
assert old in s
s = s.replace(old, new)
s = s.replace("        cl.add_leaf_cluster(leaf_bm, center, 0.34, 14, rng, warm,\n                            leaf_size=0.32, shell_inner=0.55, z_min=-0.40)",
              "        cl.add_leaf_cluster(leaf_bm, center, 0.34, 12, rng, warm,\n                            leaf_size=0.34, shell_inner=0.55, z_min=-0.40)")
s = s.replace("        leaf_count += 14\n        cluster_count += 1\n    # Olive under-layer",
              "        leaf_count += 12\n        cluster_count += 1\n    # Olive under-layer")
s = s.replace("        cl.add_leaf_cluster(leaf_bm, (x, y, z), r, n, rng, [2, 3],\n                            leaf_size=0.36, shell_inner=0.55, z_min=-0.12)",
              "        cl.add_leaf_cluster(leaf_bm, (x, y, z), r, n, rng, [2, 3, 1],\n                            leaf_size=0.38, shell_inner=0.55, z_min=-0.12)")
p.write_text(s, encoding="utf-8")

# --- hedge / groundcover ---
p = ROOT / "tools/blender/build_map001.py"
s = p.read_text(encoding="utf-8")
old = """    for row, (yy, base_z, rr) in enumerate(((-12.0, 0.55, 1.05), (-13.0, 0.35, 0.90))):
        for i in range(20 if row == 0 else 14):
            x = -14.0 + i * (1.5 if row == 0 else 2.1)
            r = rr + 0.12 * ((i * 7) % 4) / 3.0
            cl.add_mass_lobe(hedge_bm, (x, yy, base_z), r, rng,
                             flatten=0.55, subdiv=2, displace=0.18,
                             mat_index=(i + row) % 2)
            cl.add_leaf_cluster(hedge_leaf_bm, (x, yy, base_z + r * 0.32),
                                r * 0.95, 18, rng, [0, 1, 1, 2],
                                leaf_size=0.30, shell_inner=0.55, z_min=-0.25)"""
new = """    for row, (yy, base_z, rr, spacing, count) in enumerate((
            (-11.9, 0.55, 0.64, 1.05, 27),
            (-12.5, 0.42, 0.56, 1.20, 24),
            (-13.0, 0.30, 0.50, 1.35, 20))):
        for i in range(count):
            x = -14.0 + i * spacing + (row * 0.22)
            r = rr + rng.uniform(-0.04, 0.10)
            cl.add_mass_lobe(hedge_bm, (x, yy, base_z), r * 0.72, rng,
                             flatten=0.55, subdiv=2, displace=0.16,
                             mat_index=(i + row) % 2)
            cl.add_leaf_cluster(hedge_leaf_bm, (x, yy, base_z + r * 0.30),
                                r * 1.10, 34, rng, [1, 2, 3, 0],
                                leaf_size=rng.uniform(0.22, 0.32),
                                shell_inner=0.55, z_min=-0.30)"""
assert old in s
s = s.replace(old, new)
old2 = """    for side, sx in (("east", 16.0), ("west", -16.0)):
        side_bm = bmesh.new()
        for i in range(6):
            y = -8.0 + i * 3.2
            cl.add_mass_lobe(side_bm, (sx, y, 0.50), 0.80, rng,
                             flatten=0.55, subdiv=2, displace=0.16,
                             mat_index=i % 2)
        side_hedge = cl.finish_mesh("MAP001_bg_hedge_" + side, side_bm,
                                    [cl.mat_leaf_deep(), cl.mat_leaf_olive()],
                                    collection)
        side_hedge["asset_id"] = "SCENERY\""""
new2 = """    for side, sx in (("east", 16.0), ("west", -16.0)):
        side_bm = bmesh.new()
        side_leaf_bm = bmesh.new()
        for i in range(8):
            y = -8.0 + i * 2.6
            r = 0.58 + rng.uniform(-0.04, 0.08)
            cl.add_mass_lobe(side_bm, (sx, y, 0.50), r * 0.72, rng,
                             flatten=0.55, subdiv=2, displace=0.16,
                             mat_index=i % 2)
            cl.add_leaf_cluster(side_leaf_bm, (sx, y, 0.68), r * 1.1, 30, rng,
                                [1, 2, 3, 0], leaf_size=0.28,
                                shell_inner=0.55, z_min=-0.30)
        side_hedge = cl.finish_mesh("MAP001_bg_hedge_" + side, side_bm,
                                    [cl.mat_leaf_deep(), cl.mat_leaf_olive()],
                                    collection)
        side_cards = cl.finish_mesh("MAP001_bg_hedge_" + side + "_cards",
                                    side_leaf_bm,
                                    [cl.mat_leaf_deep(), cl.mat_leaf_olive(),
                                     cl.mat_leaf_amber()], collection)
        for obj in (side_hedge, side_cards):
            obj["asset_id"] = "SCENERY\""""
assert old2 in s
s = s.replace(old2, new2)
old3 = """                   ("ENV011", -9.5, -1.5, 160.0, 1.20),
                   ("ENV012", 9.5, -2.5, 30.0, 1.15)]"""
new3 = """                   ("ENV011", -9.5, -1.5, 160.0, 1.20),
                   ("ENV012", 9.5, -2.5, 30.0, 1.15),
                   ("ENV011", -11.0, -8.8, 20.0, 1.35),
                   ("ENV011", -4.0, -8.8, 90.0, 1.25),
                   ("ENV011", 4.0, -8.8, 150.0, 1.30),
                   ("ENV011", 11.0, -8.8, 210.0, 1.30),
                   ("ENV012", -7.0, -8.8, 40.0, 1.15),
                   ("ENV012", 7.0, -8.8, 120.0, 1.20),
                   ("ENV011", -12.8, 3.8, 75.0, 1.20),
                   ("ENV011", 12.8, -1.2, 175.0, 1.20),
                   ("ENV012", -6.0, 9.3, 10.0, 1.10),
                   ("ENV012", 6.0, 9.3, 80.0, 1.10)]"""
assert old3 in s
s = s.replace(old3, new3)
p.write_text(s, encoding="utf-8")
print("tree/hedge/groundcover patches applied")
