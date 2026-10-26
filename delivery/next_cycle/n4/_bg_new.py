def _hedge_volume(bm, axis, fixed, start, end, z0, z1, thick, rng,
                  mat_index=0):
    """Continuous displaced hedge volume with a wavy top; no topiary balls."""
    cols = max(10, int((end - start) / 0.42))
    rows = 6
    front, back = [], []
    for i in range(cols + 1):
        u = start + (end - start) * i / cols
        top = z1 + 0.16 * math.sin(i * 0.55 + fixed * 0.7) + rng.uniform(-0.09, 0.09)
        fcol, bcol = [], []
        for j in range(rows + 1):
            t = j / rows
            z = z0 + (top - z0) * t
            jitter = rng.uniform(-0.035, 0.035)
            if axis == "x":
                f = (u, fixed - thick / 2 + jitter, z)
                b = (u, fixed + thick / 2 + jitter, z)
            else:
                f = (fixed - thick / 2 + jitter, u, z)
                b = (fixed + thick / 2 + jitter, u, z)
            fcol.append(bm.verts.new(f))
            bcol.append(bm.verts.new(b))
        front.append(fcol)
        back.append(bcol)
    for i in range(cols):
        for j in range(rows):
            bm.faces.new((front[i][j], front[i][j + 1],
                          front[i + 1][j + 1], front[i + 1][j])).material_index = mat_index
            bm.faces.new((back[i][j], back[i + 1][j],
                          back[i + 1][j + 1], back[i][j + 1])).material_index = mat_index
        bm.faces.new((front[i][rows], back[i][rows], back[i + 1][rows],
                      front[i + 1][rows])).material_index = mat_index
    for j in range(rows):
        bm.faces.new((front[0][j], front[0][j + 1], back[0][j + 1],
                      back[0][j])).material_index = mat_index
        bm.faces.new((front[-1][j], back[-1][j], back[-1][j + 1],
                      front[-1][j + 1])).material_index = mat_index
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))


def _hedge_leaf_skin(bm, axis, fixed, start, end, z0, z1, thick, rng,
                     mats, tall_shoots=True):
    cols = max(8, int((end - start) / 0.52))
    for i in range(cols + 1):
        u = start + (end - start) * i / cols + rng.uniform(-0.12, 0.12)
        top = z1 + 0.16 * math.sin(i * 0.62 + fixed * 0.7)
        for side in (-1, 1):
            for t in (0.16, 0.40, 0.66, 0.90):
                z = z0 + (top - z0) * t
                off = thick / 2 + rng.uniform(0.02, 0.16)
                if axis == "x":
                    center = (u, fixed + side * off, z + rng.uniform(-0.05, 0.05))
                else:
                    center = (fixed + side * off, u, z + rng.uniform(-0.05, 0.05))
                cl.add_leaf_cluster(bm, center, rng.uniform(0.42, 0.62), 26, rng,
                                    [0, 1, 2, 3, 0, 2], leaf_size=rng.uniform(0.135, 0.195),
                                    flatten=0.82, shell_inner=0.30, z_min=-0.80)
        # A leaf cap along the wavy top closes the silhouette.
        for dx in (-0.18, 0.18):
            if axis == "x":
                center = (u + dx, fixed + rng.uniform(-0.22, 0.22), top + 0.06)
            else:
                center = (fixed + rng.uniform(-0.22, 0.22), u + dx, top + 0.06)
            cl.add_leaf_cluster(bm, center, rng.uniform(0.38, 0.54), 24, rng,
                                [0, 2, 3, 1, 0], leaf_size=rng.uniform(0.145, 0.205),
                                flatten=0.72, shell_inner=0.22, z_min=-0.45)
        if tall_shoots and i % 5 == 2:
            if axis == "x":
                anchor = Vector((u, fixed, top - 0.12))
            else:
                anchor = Vector((fixed, u, top - 0.12))
            endp = anchor + Vector((rng.uniform(-0.12, 0.12),
                                    rng.uniform(-0.12, 0.12),
                                    rng.uniform(0.42, 0.72)))
            cl.add_smooth_tube(bm, [anchor, endp], [0.014, 0.003], segments=4,
                               mat_index=0, ring_noise=0.04, rng=rng)
            cl.add_leaf_cluster(bm, endp, 0.22, 10, rng, [0, 1, 3],
                                leaf_size=0.15, flatten=0.8, shell_inner=0.25,
                                z_min=-0.5)


def add_background_scenery(collection):
    """Continuous hedge walls, background autumn trees and a distant treeline.

    Native meshes only, no colliders and no catalog instances. The hedge is a
    displaced volume with leaf skin, not a row of spheres.
    """
    rng = random.Random(20261025)
    mass_bm = bmesh.new()
    leaf_bm = bmesh.new()
    mass_mats = [cl.mat_leaf_mass(), cl.mat_leaf_deep(), cl.mat_leaf_olive()]
    leaf_mats = [cl.mat_leaf_olive(), cl.mat_leaf_deep(),
                 cl.mat_leaf_amber(), cl.mat_leaf_gold()]

    # North hedge: continuous wall behind the 0.79 m low wall.
    _hedge_volume(mass_bm, "x", -10.85, -14.2, 14.2, 0.0, 2.38, 1.55, rng, 0)
    _hedge_leaf_skin(leaf_bm, "x", -10.85, -14.2, 14.2, 0.0, 2.38, 1.55, rng,
                     leaf_mats)
    # A second, higher leaf row behind gives layered depth without a second
    # solid wall.
    _hedge_volume(mass_bm, "x", -12.05, -14.2, 14.2, 0.0, 2.85, 1.1, rng, 1)
    _hedge_leaf_skin(leaf_bm, "x", -12.05, -14.2, 14.2, 0.0, 2.85, 1.1, rng,
                     [cl.mat_leaf_olive(), cl.mat_leaf_deep(),
                      cl.mat_leaf_amber()], tall_shoots=False)

    # Side hedges along the east/west railings.
    for sx in (-14.75, 14.75):
        _hedge_volume(mass_bm, "y", sx, -9.4, 9.4, 0.0, 2.10, 1.25, rng, 2)
        _hedge_leaf_skin(leaf_bm, "y", sx, -9.4, 9.4, 0.0, 2.10, 1.25, rng,
                         leaf_mats)

    # Low front hedge strips at the wall base, leaving the north path open.
    for (x0, x1) in ((-14.0, -4.4), (4.4, 14.0)):
        _hedge_volume(mass_bm, "x", -9.28, x0, x1, 0.0, 1.04, 0.72, rng, 0)
        _hedge_leaf_skin(leaf_bm, "x", -9.28, x0, x1, 0.0, 1.04, 0.72, rng,
                         [cl.mat_leaf_olive(), cl.mat_leaf_deep(),
                          cl.mat_leaf_amber()], tall_shoots=False)

    # Ivy pads on the wall face.
    for i in range(60):
        x = rng.uniform(-13.4, 13.4)
        if abs(x) < 2.6:
            continue
        cl.add_leaf_cluster(leaf_bm, (x, -9.42, rng.uniform(0.38, 0.82)),
                            rng.uniform(0.24, 0.42), 14, rng,
                            [2, 1, 0, 3], leaf_size=0.115, flatten=0.44,
                            shell_inner=0.18, z_min=-0.45)

    hedge = cl.finish_mesh("MAP001_bg_hedge", mass_bm, mass_mats, collection)
    bpy.ops.object.select_all(action="DESELECT")
    hedge.select_set(True)
    bpy.context.view_layer.objects.active = hedge
    bpy.ops.object.shade_smooth()
    hedge.select_set(False)
    hedge_cards = cl.finish_mesh("MAP001_bg_hedge_cards", leaf_bm,
                                 leaf_mats, collection)
    for obj in (hedge, hedge_cards):
        obj["asset_id"] = "SCENERY"
        obj["role"] = "continuous background hedge outside the playable area"

    # Background autumn trees: crown centres low enough to clear the hedge and
    # sit inside the top of the formal camera.
    tree_trunk_bm = bmesh.new()
    tree_leaf_bm = bmesh.new()
    tree_mats = [cl.mat_leaf_olive(), cl.mat_leaf_deep(), cl.mat_leaf_amber(),
                 cl.mat_leaf_gold()]
    for ti, (tx, ty, th, tr) in enumerate(((-12.2, -13.9, 6.2, 1.15),
                                           (-6.0, -14.6, 6.8, 1.25),
                                           (0.8, -14.2, 6.0, 1.10),
                                           (6.8, -14.9, 7.0, 1.30),
                                           (12.0, -14.0, 6.2, 1.12))):
        cl.add_smooth_tube(tree_trunk_bm,
                           [(tx, ty, 0.0), (tx + 0.08, ty + 0.04, th * 0.42),
                            (tx - 0.05, ty + 0.08, th * 0.70)],
                           [tr * 0.15, tr * 0.10, tr * 0.065], segments=8,
                           mat_index=0, ring_noise=0.04, rng=rng)
        for (dx, dz, rr) in ((0.0, 0.62, 1.00), (-0.44, 0.56, 0.80),
                             (0.42, 0.58, 0.84), (0.06, 0.76, 0.72),
                             (-0.12, 0.46, 0.66)):
            center = (tx + dx * tr * 1.8, ty + rng.uniform(-0.3, 0.3), th * dz)
            for (ox, oy, oz, cr) in ((0.0, 0.0, 0.0, 0.66),
                                     (-0.30, 0.12, 0.10, 0.50),
                                     (0.28, -0.10, 0.08, 0.48)):
                cl.add_leaf_cluster(
                    tree_leaf_bm,
                    (center[0] + tr * rr * ox,
                     center[1] + tr * rr * 0.55 * oy,
                     center[2] + tr * rr * oz),
                    tr * rr * cr, 48, rng, [2, 2, 1, 3, 0, 4],
                    leaf_size=rng.uniform(0.16, 0.235),
                    flatten=0.78, shell_inner=0.34, z_min=-0.58)
    tree_trunks = cl.finish_mesh("MAP001_bg_tree_trunks", tree_trunk_bm,
                                 [cl.mat_wood_dark()], collection)
    tree_crowns = cl.finish_mesh("MAP001_bg_tree_crowns", tree_leaf_bm,
                                 tree_mats, collection)
    for obj in (tree_trunks, tree_crowns):
        obj["asset_id"] = "SCENERY"
        obj["role"] = "background autumn trees behind hedge"

    # Distant treeline replaces the flat grey roof boxes: overlapping crowns
    # and a low dark ribbon close the top of frame naturally.
    band_bm = bmesh.new()
    band_leaf_bm = bmesh.new()
    _hedge_volume(band_bm, "x", -16.2, -16.0, 16.0, 1.5, 3.4, 1.4, rng, 0)
    for i in range(34):
        x = -15.6 + i * 0.95 + rng.uniform(-0.25, 0.25)
        z = 3.4 + 1.15 * math.sin(i * 0.55) + rng.uniform(-0.2, 0.35)
        cl.add_leaf_cluster(band_leaf_bm, (x, -16.1, z), rng.uniform(1.35, 1.85),
                            46, rng, [2, 2, 3, 1, 0],
                            leaf_size=rng.uniform(0.20, 0.28),
                            flatten=0.80, shell_inner=0.22, z_min=-0.65)
    band = cl.finish_mesh("MAP001_bg_treeline_mass", band_bm,
                          [cl.mat_leaf_deep(), cl.mat_leaf_mass()], collection)
    band_cards = cl.finish_mesh("MAP001_bg_treeline_cards", band_leaf_bm,
                                tree_mats, collection)
    for obj in (band, band_cards):
        obj["asset_id"] = "SCENERY"
        obj["role"] = "distant treeline behind the hedge"

    STATE.setdefault("scenery", []).append({
        "kind": "background_depth_layer",
        "hedge": ["MAP001_bg_hedge", "MAP001_bg_hedge_cards"],
        "trees": ["MAP001_bg_tree_trunks", "MAP001_bg_tree_crowns"],
        "distant": ["MAP001_bg_treeline_mass", "MAP001_bg_treeline_cards"],
        "note": "continuous hedge volume + leaf skin; no colliders; depth only",
    })
