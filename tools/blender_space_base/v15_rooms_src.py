# =====================================================================
# v15 · four core rooms
# Spec: planning/art/SPACE_BASE_CORE_ROOMS_ART_PLAN_20261108.md (v1.3)
# Local hall frame: u = t - t0, v = off - v0, both 0..34, inner clear 0.45..33.55
# All lateral positions go through av()/avr() so AV_ROT is applied once.
# =====================================================================

_V15_FONT = {
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00110", "01010", "10010", "11111", "00010", "00010", "00010"),
}


def _v15_cyl(name, t, off, z0, z1, r, mat, c, verts=48):
    x, y = av(t, off)
    return add_cyl(name, x, y, z0, z1, r, mat, c, vertices=verts)


def _v15_ring(name, t, off, r, w, z0, z1, mat, c, seg=64, a0=0.0, a1=2 * math.pi):
    x, y = av(t, off)
    return add_tube(name, x, y, r + w * 0.5, max(0.02, r - w * 0.5), z0, z1, mat, c, seg, a0, a1)


def _v15_hcyl(name, t, off, zc, length, r, mat, c, deg=0.0, verts=24):
    x, y = av(t, off)
    return add_cyl_h(name, x, y, zc, length, r, mat, c, vertices=verts,
                     rot_z=AV_ROT + math.radians(deg))


def _v15_rot(name, t, off, du, dv, z0, z1, mat, c, deg=0.0):
    x, y = av(t, off)
    return add_box_local(name, x, y, (z0 + z1) * 0.5, du, dv, z1 - z0, mat, c,
                         rot_z=AV_ROT + math.radians(deg))


def _v15_text(name, t0, v0, cu, cv, z0, z1, txt, m, c, cell=0.5, gap=0.6, mat=None):
    """Ground stencil. Horizontal runs are merged into single tiles (object budget)."""
    mat = mat or m["white"]
    n = len(txt)
    width = n * 5 * cell + (n - 1) * gap * cell
    uu = cu - width * 0.5
    for ci, ch in enumerate(txt):
        rows = _V15_FONT.get(ch)
        if not rows:
            continue
        for ry, row in enumerate(rows):
            cx = 0
            while cx < len(row):
                if row[cx] != "1":
                    cx += 1
                    continue
                run = 1
                while cx + run < len(row) and row[cx + run] == "1":
                    run += 1
                a = uu + cx * cell
                b = cv + (3.5 - ry - 1) * cell
                avr("%s_%d_%d_%d" % (name, ci, ry, cx), t0 + a, t0 + a + run * cell,
                    v0 + b, v0 + b + cell, z0, z1, mat, c)
                cx += run
        uu += 5 * cell + gap * cell


def fit_out(name, t0, t1, v0, v1, z, m, c):
    """v15: per-hall rebuild. Four halls only -- no CEO room by user ruling (22:19)."""
    tag = name.lower()
    if name == "H1":
        _v15_h1(tag, t0, v0, z, m, c)
    elif name == "H2":
        _v15_h2(tag, t0, v0, z, m, c)
    elif name == "H3":
        _v15_h3(tag, t0, v0, z, m, c)
    elif name == "H4":
        _v15_h4(tag, t0, v0, z, m, c)


# ---------------------------------------------------------------- H1 centrifuge
def _v15_h1(tag, t0, v0, z, m, c):
    def R(nm, u0, u1, w0, w1, z0, z1, mat):
        avr("%s_v15_%s" % (tag, nm), t0 + u0, t0 + u1, v0 + w0, v0 + w1, z0, z1, mat, c)

    IN0, IN1 = 0.45, 33.55
    ZF = z + 0.06
    Z1 = ZF + 0.14          # whole-hall dark deck (0.14 m solid, not a decal)
    R("deck", IN0, IN1, IN0, IN1, ZF, Z1, m["h1_floor"])
    # wall skirt 1.2 m painted on the north + west walls only (D4: no four-side frame)
    R("skirt_n", IN0, IN1, IN0, IN0 + 1.2, Z1, Z1 + 0.10, m["cap_h1"])
    R("skirt_w", IN0, IN0 + 1.2, IN0 + 1.2, IN1, Z1, Z1 + 0.10, m["cap_h1"])
    # bright perimeter walk 1.35 m -- the "dark floor + light ring" figure/ground (D5)
    R("walk_n", IN0, IN1, IN0 + 1.2, IN0 + 2.55, Z1, Z1 + 0.10, m["platform"])
    R("walk_w", IN0 + 1.2, IN0 + 2.55, IN0 + 2.55, IN1, Z1, Z1 + 0.10, m["platform"])
    R("walk_s", IN0, IN1, IN1 - 1.5, IN1, Z1, Z1 + 0.10, m["platform"])
    R("walk_e", IN1 - 1.5, IN1, IN0, IN1 - 1.5, Z1, Z1 + 0.10, m["platform"])
    Z2 = Z1 + 0.10
    # main circular floor
    _v15_cyl("%s_v15_disc" % tag, t0 + 17.0, v0 + 17.0, Z2 - 0.02, Z2 + 0.12,
             14.0, m["h1_disc"], c, 72)
    Z3 = Z2 + 0.12
    for i, rr in enumerate((3.0, 5.5, 8.0, 11.0)):
        _v15_ring("%s_v15_ring%d" % (tag, i), t0 + 17.0, v0 + 17.0, rr, 0.30,
                  Z3, Z3 + 0.10, m["white"], c, 72)
    for i in range(12):
        a = i * 30.0 + 6.0
        cu = 17.0 + 9.4 * math.cos(math.radians(a))
        cv = 17.0 + 9.4 * math.sin(math.radians(a))
        _v15_rot("%s_v15_tick%d" % (tag, i), t0 + cu, v0 + cv, 1.6, 0.30,
                 Z3, Z3 + 0.08, m["orange"], c, deg=a)
    # centre column: silver segmented shaft, black flanges, rust foot ring
    _v15_ring("%s_v15_colfoot" % tag, t0 + 17.0, v0 + 17.0, 1.05, 0.55, Z3, Z3 + 0.26,
              m["ws_refractory"], c, 32)
    _v15_cyl("%s_v15_col" % tag, t0 + 17.0, v0 + 17.0, Z3, Z3 + 8.6, 0.70, m["metal"], c, 24)
    for i in range(8):
        hh = Z3 + 1.4 + i * 0.95
        _v15_rot("%s_v15_flange%d" % (tag, i), t0 + 17.0, v0 + 17.0, 1.55, 1.55,
                 hh, hh + 0.20, m["dark"], c)
    # the pod: the only diagonal in the hall
    zc = Z3 + 2.30
    _v15_hcyl("%s_v15_pod" % tag, t0 + 20.0, v0 + 15.0, zc, 8.4, 1.25, m["char_dark"], c, -18, 28)
    aa = math.radians(-18)
    for i, s in enumerate((-1.9, 1.9)):
        cu = 20.0 + s * math.cos(aa)
        cv = 15.0 + s * math.sin(aa)
        _v15_hcyl("%s_v15_podband%d" % (tag, i), t0 + cu, v0 + cv, zc, 0.55, 1.31,
                  m["steel"], c, -18, 28)
    for i, s in enumerate((-4.0, 4.0)):
        cu = 20.0 + s * math.cos(aa)
        cv = 15.0 + s * math.sin(aa)
        _v15_hcyl("%s_v15_podcap%d" % (tag, i), t0 + cu, v0 + cv, zc, 0.34, 1.27,
                  m["dark"], c, -18, 28)
    for i, s in enumerate((-3.0, 3.0)):
        cu = 20.0 + s * math.cos(aa)
        cv = 15.0 + s * math.sin(aa)
        _v15_rot("%s_v15_podskid%d" % (tag, i), t0 + cu, v0 + cv, 1.4, 2.2,
                 Z3, zc - 1.10, m["dark"], c, -18)
    # observation window band -> cabinet row on the north wall, second run on east
    R("cab_n", 2.0, 16.0, IN0, IN0 + 2.2, Z2, Z2 + 2.2, m["white"])
    for i in range(6):
        uu = 2.0 + 2.33 * (i + 1)
        R("cabn_seam%d" % i, uu - 0.06, uu + 0.06, IN0, IN0 + 2.2, Z2 + 0.10,
          Z2 + 2.26, m["dark"])
    R("cab_e", 30.4, 32.6, 2.0, 8.0, Z2, Z2 + 2.2, m["white"])
    for i in range(3):
        ww = 2.0 + 2.0 * (i + 1)
        R("cabe_seam%d" % i, 30.4, 32.6, ww - 0.06, ww + 0.06, Z2 + 0.10, Z2 + 2.26,
          m["dark"])
    # six ring consoles (seeded jitter, not a perfect 6-way split)
    jit = (3.0, -4.5, 6.0, -2.0, 4.0, -5.5)
    for i in range(6):
        a = math.radians(i * 60 + jit[i])
        cu = 17.0 + 15.2 * math.cos(a)
        cv = 17.0 + 15.2 * math.sin(a)
        _v15_rot("%s_v15_console%d" % (tag, i), t0 + cu, v0 + cv, 3.0, 1.1,
                 Z2, Z2 + 1.10, m["steel"], c, deg=math.degrees(a) + 90)
        _v15_rot("%s_v15_consoletop%d" % (tag, i), t0 + cu, v0 + cv, 2.6, 0.9,
                 Z2 + 1.10, Z2 + 1.18, m["orange"], c, deg=math.degrees(a) + 90)
    # two corner equipment rooms (not four -- break the mirror)
    for i, (u0, w0) in enumerate(((IN1 - 4.7, IN0 + 1.2), (IN1 - 4.7, IN1 - 4.7))):
        R("eq%d_glass" % i, u0, u0 + 4.2, w0, w0 + 4.2, Z2, Z2 + 2.6, m["glass"])
        for j, (a0, a1, b0, b1) in enumerate(((u0, u0 + 4.2, w0, w0 + 0.18),
                                              (u0, u0 + 4.2, w0 + 4.02, w0 + 4.2),
                                              (u0, u0 + 0.18, w0, w0 + 4.2),
                                              (u0 + 4.02, u0 + 4.2, w0, w0 + 4.2))):
            R("eq%d_fr%d" % (i, j), a0, a1, b0, b1, Z2 + 2.6, Z2 + 2.75, m["steel"])
    # mid-scale groups (structured runs, driver of perceived density)
    for i in range(5):
        R("pallet%d" % i, 23.0 + i * 1.9, 23.9 + i * 1.9, 28.0, 31.0, Z2, Z2 + 1.3,
          m["container_gray"])
    R("tray_a", 4.5, 4.5 + 9.0, 6.2, 7.0, Z2, Z2 + 0.32, m["metal"])
    R("tray_b", 4.5, 4.5 + 9.0, 7.6, 8.4, Z2, Z2 + 0.32, m["metal"])
    for i in range(4):
        R("cabinet%d" % i, 30.4, 31.6, 22.0 + i * 2.1, 23.6 + i * 2.1, Z2, Z2 + 2.1,
          m["steel"])
    for i in range(6):
        R("plate%d" % i, 26.5 + (i % 3) * 2.2, 27.6 + (i % 3) * 2.2,
          21.0 + (i // 3) * 2.2, 22.1 + (i // 3) * 2.2, Z3, Z3 + 0.10, m["floorshadow"])
    # one structure-shadow pair across the disc (skylight / truss projection)
    _v15_rot("%s_v15_shade%d" % (tag, 0), t0 + 13.0, v0 + 12.0, 22.0, 1.4,
             Z3, Z3 + 0.18, m["floorshadow"], c, deg=28)
    _v15_rot("%s_v15_shade%d" % (tag, 1), t0 + 12.0, v0 + 11.4, 16.0, 0.8,
             Z3, Z3 + 0.19, m["garden_coping"], c, deg=28)
    for i in range(6):
        R("scrate%d" % i, 2.4 + i * 1.5, 3.6 + i * 1.5, 30.4, 31.6, Z3, Z3 + 1.1,
          m["container_gray"])
    for i in range(6):
        R("splate%d" % i, 26.6 + (i % 3) * 2.2, 27.7 + (i % 3) * 2.2,
          16.0 + (i // 3) * 2.2, 17.1 + (i // 3) * 2.2, Z3, Z3 + 0.2, m["metal"])
    _v15_text("%s_v15_id" % tag, t0, v0, 22.5, 24.6, Z3, Z3 + 0.06, "H1", m, c)


# ----------------------------------------------------------------- H2 buoyancy
def _v15_h2(tag, t0, v0, z, m, c):
    def R(nm, u0, u1, w0, w1, z0, z1, mat):
        avr("%s_v15_%s" % (tag, nm), t0 + u0, t0 + u1, v0 + w0, v0 + w1, z0, z1, mat, c)

    IN0, IN1 = 0.45, 33.55
    ZF = z + 0.06
    ZD = ZF + 0.36          # deck top
    PX0, PX1, PY0, PY1 = 6.0, 28.0, 10.0, 24.0
    RC = 1.2                # coping width
    # deck built as four strips so the pool is a real void, not paint
    R("deck_n", IN0, IN1, IN0, PY0 - RC, ZF, ZD, m["dock"])
    R("deck_s", IN0, IN1, PY1 + RC, IN1, ZF, ZD, m["dock"])
    R("deck_w", IN0, PX0 - RC, PY0 - RC, PY1 + RC, ZF, ZD, m["dock"])
    R("deck_e", PX1 + RC, IN1, PY0 - RC, PY1 + RC, ZF, ZD, m["dock"])
    # pool bed + inner shadow ledge
    R("bed", PX0, PX1, PY0, PY1, ZF, ZF + 0.14, m["h2_poolbed"])
    for nm, (a0, a1, b0, b1) in {
            "sh_n": (PX0, PX1, PY0, PY0 + 1.6),
            "sh_s": (PX0, PX1, PY1 - 1.6, PY1),
            "sh_w": (PX0, PX0 + 1.6, PY0 + 1.6, PY1 - 1.6),
            "sh_e": (PX1 - 1.6, PX1, PY0 + 1.6, PY1 - 1.6)}.items():
        R(nm, a0, a1, b0, b1, ZF + 0.14, ZF + 0.24, m["cope"])
    # coping: concrete upstand + teal cap (the single strongest colour cue of H2)
    for nm, (a0, a1, b0, b1) in {
            "rim_n": (PX0 - RC, PX1 + RC, PY0 - RC, PY0),
            "rim_s": (PX0 - RC, PX1 + RC, PY1, PY1 + RC),
            "rim_w": (PX0 - RC, PX0, PY0, PY1),
            "rim_e": (PX1, PX1 + RC, PY0, PY1)}.items():
        R(nm, a0, a1, b0, b1, ZF, ZF + 1.50, m["dock"])
        R(nm + "_cap", a0, a1, b0, b1, ZF + 1.50, ZF + 1.66, m["cap_h2"])
    # thin yellow paint line inside the pool (real: 0.1 m; readable: 0.3 m)
    for nm, (a0, a1, b0, b1) in {
            "yl_n": (PX0 + 0.1, PX1 - 0.1, PY0 + 1.15, PY0 + 1.45),
            "yl_w": (PX0 + 1.15, PX0 + 1.45, PY0 + 1.45, PY1 - 1.15)}.items():
        R(nm, a0, a1, b0, b1, ZF + 0.14, ZF + 0.22, m["ws_yellow"])
    # three pressure chambers, three different headings, two in the pool
    for i, (cu, cv, ang, inpool) in enumerate(((11.5, 15.0, 25, True),
                                               (20.5, 20.5, 0, True),
                                               (25.2, 6.6, -12, False))):
        zc = (ZF + 0.24 + 1.1) if inpool else (ZD + 1.1)
        _v15_hcyl("%s_v15_chamber%d" % (tag, i), t0 + cu, v0 + cv, zc, 7.0, 1.10,
                  m["steel"], c, ang, 24)
        aa = math.radians(ang)
        for j, s in enumerate((-2.0, 0.0, 2.0)):
            uu = cu + s * math.cos(aa)
            vv = cv + s * math.sin(aa)
            _v15_hcyl("%s_v15_chband%d_%d" % (tag, i, j), t0 + uu, v0 + vv, zc, 0.42,
                      1.15, m["dark"], c, ang, 24)
        uu = cu + 3.6 * math.cos(aa)
        vv = cv + 3.6 * math.sin(aa)
        _v15_hcyl("%s_v15_chend%d" % (tag, i), t0 + uu, v0 + vv, zc, 0.30, 1.12,
                  m["ws_yellow"], c, ang, 24)
    # gantry: one beam, no deck plate
    for i, uu in enumerate((3.6, 30.4)):
        _v15_cyl("%s_v15_gleg%d" % (tag, i), t0 + uu, v0 + 17.0, ZD, z + 8.4, 0.55,
                 m["steel"], c, 12)
    R("gbeam", 3.6, 30.4, 16.4, 17.6, z + 7.6, z + 8.4, m["metal"])
    R("gtrolley", 9.2, 11.4, 16.1, 17.9, z + 8.4, z + 8.9, m["steel"])
    R("bbasket", 13.0, 15.6, 16.0, 18.2, z + 2.6, z + 4.9, m["metal"])
    for i, (cu, cv) in enumerate(((13.6, 16.4), (15.0, 17.8))):
        _v15_cyl("%s_v15_bcab%d" % (tag, i), t0 + cu, v0 + cv, z + 4.9, z + 8.4, 0.06,
                 m["dark"], c, 4)
    # office cabin on the deck, window band as top seam
    R("office", 1.4, 9.4, 26.2, 30.2, ZD, ZD + 3.1, m["white"])
    R("office_seam", 1.4, 9.4, 26.2, 26.45, ZD + 1.5, ZD + 2.9, m["dark"])
    for i in range(4):
        R("office_mul%d" % i, 2.6 + i * 1.7, 2.72 + i * 1.7, 26.2, 26.45,
          ZD + 1.5, ZD + 2.9, m["steel"])
    R("office_rim", 1.4, 9.4, 26.2, 26.45, ZD + 3.1, ZD + 3.3, m["steel"])
    for i in range(3):
        R("office_ahu%d" % i, 2.2 + i * 2.3, 3.6 + i * 2.3, 27.4, 29.2, ZD + 3.1, ZD + 3.9,
          m["metal"])
    # black steel guard runs on the coping (not a full yellow ring -- D3)
    for i, (a0, a1) in enumerate(((7.0, 12.0), (15.0, 20.0), (22.0, 27.0))):
        R("guard%d" % i, a0, a1, PY0 - RC - 0.05, PY0 - RC + 0.35, ZF + 1.66,
          ZF + 2.75, m["dark"])
    for i, (b0, b1) in enumerate(((11.0, 16.0), (18.0, 23.0))):
        R("guarde%d" % i, PX1 + RC - 0.35, PX1 + RC + 0.05, b0, b1, ZF + 1.66,
          ZF + 2.75, m["dark"])
    # hazard steps down to the pool (two, offset)
    for i, (a0, b0) in enumerate(((5.2, 25.4), (28.6, 14.0))):
        R("step%d" % i, a0, a0 + 2.2, b0, b0 + 1.4, ZD, ZD + 1.2, m["ws_yellow"])
    # mid-scale runs
    for i in range(6):
        R("crate%d" % i, 2.0 + i * 1.7, 3.0 + i * 1.7, 31.2, 32.4, ZD, ZD + 1.0,
          m["container_gray"])
    for i in range(4):
        R("pipe%d" % i, 31.4, 31.9, 9.5 + i * 0.9, 20.0 + i * 0.9, ZD, ZD + 0.42,
          m["metal"])
    for i in range(5):
        R("lplate%d" % i, 12.0 + i * 2.6, 13.2 + i * 2.6, 26.4, 27.6, ZD, ZD + 0.05,
          m["floorshadow"])
    # skylight: three bright bands and one dark beam shadow on the pool bed
    for i in range(2):
        R("sky%d" % i, PX0 + 3.4 + i * 9.0, PX0 + 5.2 + i * 9.0, PY0 + 2.4, PY1 - 2.4,
          ZF + 0.24, ZF + 0.275, m["platform"])
    R("sky_beam", PX0, PX1, 16.4, 17.6, ZF + 0.24, ZF + 0.30, m["floorshadow"])
    # mid-scale density run B (west/east decks, south wall)
    for i in range(4):
        for j in range(2):
            R("deckplate%d_%d" % (i, j), 1.2 + j * 2.1, 2.5 + j * 2.1,
              11.0 + i * 2.8, 12.4 + i * 2.8, ZD, ZD + 0.22, m["metal"])
    for i in range(6):
        R("scab%d" % i, 12.0 + i * 1.8, 13.3 + i * 1.8, 31.9, 33.3, ZD, ZD + 1.6,
          m["steel"])
    for i in range(6):
        R("ncrate%d" % i, 12.4 + i * 1.5, 13.5 + i * 1.5, 1.1, 2.3, ZD, ZD + 0.9,
          m["container_gray"])
    for i in range(6):
        R("psupp%d" % i, 30.3, 31.1, 10.0 + i * 1.9, 10.8 + i * 1.9, ZD, ZD + 0.7,
          m["dark"])
    _v15_text("%s_v15_id" % tag, t0, v0, 19.0, 3.0, ZD, ZD + 0.06, "H2", m, c)


# -------------------------------------------------------------------- H3 blue
def _v15_h3(tag, t0, v0, z, m, c):
    def R(nm, u0, u1, w0, w1, z0, z1, mat):
        avr("%s_v15_%s" % (tag, nm), t0 + u0, t0 + u1, v0 + w0, v0 + w1, z0, z1, mat, c)

    IN0, IN1 = 0.45, 33.55
    ZF = z + 0.06
    ZD = ZF + 1.20          # deck top, 1.2 m above the pit bed (reads as depth)
    PX0, PX1, PY0, PY1 = 11.0, 23.0, 11.0, 22.0
    R("deck_n", IN0, IN1, IN0, PY0, ZF, ZD, m["floor_ind"])
    R("deck_s", IN0, IN1, PY1, IN1, ZF, ZD, m["floor_ind"])
    R("deck_w", IN0, PX0, PY0, PY1, ZF, ZD, m["floor_ind"])
    R("deck_e", PX1, IN1, PY0, PY1, ZF, ZD, m["floor_ind"])
    R("pit", PX0, PX1, PY0, PY1, ZF, ZF + 0.14, m["h3_pitbed"])
    for nm, (a0, a1, b0, b1) in {
            "pit_sh_n": (PX0, PX1, PY0, PY0 + 1.2),
            "pit_sh_s": (PX0, PX1, PY1 - 1.2, PY1),
            "pit_sh_w": (PX0, PX0 + 1.2, PY0 + 1.2, PY1 - 1.2),
            "pit_sh_e": (PX1 - 1.2, PX1, PY0 + 1.2, PY1 - 1.2)}.items():
        R(nm, a0, a1, b0, b1, ZF + 0.14, ZF + 0.24, m["cap_h3"])
    # hazard edge on the deck, 3 gaps
    for i, (a0, a1, b0, b1) in enumerate(((PX0 - 0.7, PX1 + 0.7, PY0 - 0.7, PY0),
                                          (PX0 - 0.7, PX1 + 0.7, PY1, PY1 + 0.7))):
        R("haz%d" % i, a0, a1, b0, b1, ZD, ZD + 0.10, m["ws_yellow"])
    for i, (b0, b1) in enumerate(((PY0, PY0 + 4.0), (PY0 + 5.0, PY0 + 7.0),
                                  (PY0 + 8.0, PY1))):
        R("hazw%d" % i, PX0 - 0.7, PX0, b0, b1, ZD, ZD + 0.10, m["ws_yellow"])
        R("haze%d" % i, PX1, PX1 + 0.7, b0, b1, ZD, ZD + 0.10, m["ws_yellow"])
    # satellite: pedestal + dark bus + four copper-gold wings + dishes
    _v15_cyl("%s_v15_satped" % tag, t0 + 17.0, v0 + 16.5, ZF + 0.14, ZF + 2.30, 0.9,
             m["dark"], c, 16)
    R("satbus", 15.5, 18.5, 15.0, 18.0, ZF + 2.30, ZF + 3.70, m["metal"])
    R("satbus2", 16.2, 17.8, 15.7, 17.3, ZF + 3.70, ZF + 4.00, m["dark"])
    for i, (ang, off) in enumerate(((16, 2.3), (-16, 2.3), (16, -2.3), (-16, -2.3))):
        cu = 17.0 + off * math.cos(math.radians(ang + 90))
        cv = 16.5 + off * math.sin(math.radians(ang + 90))
        _v15_rot("%s_v15_wing%d" % (tag, i), t0 + cu, v0 + cv, 3.4, 1.35,
                 ZF + 3.72, ZF + 3.86, m["gold"], c, deg=ang)
    _v15_cyl("%s_v15_dish0" % tag, t0 + 19.6, v0 + 18.8, ZF + 3.8, ZF + 3.92, 0.65,
             m["dark"], c, 12)
    _v15_cyl("%s_v15_dish1" % tag, t0 + 15.0, v0 + 14.4, ZF + 3.8, ZF + 3.92, 0.50,
             m["dark"], c, 12)
    # two white arms, different poses, yellow joint rings
    for i, (cu, cv, deg, ln) in enumerate(((13.4, 16.2, 62, 3.6), (20.6, 17.0, -48, 3.4))):
        _v15_cyl("%s_v15_armbase%d" % (tag, i), t0 + cu, v0 + cv, ZF + 0.14, ZF + 2.0,
                 0.62, m["dark"], c, 12)
        _v15_rot("%s_v15_arm%d" % (tag, i), t0 + cu, v0 + cv, ln, 0.55, ZF + 2.0,
                 ZF + 2.45, m["white"], c, deg=deg)
        _v15_cyl("%s_v15_joint%d" % (tag, i), t0 + cu, v0 + cv, ZF + 2.0, ZF + 2.52,
                 0.45, m["ws_yellow"], c, 12)
        dd = math.radians(deg)
        uu = cu + ln * 0.5 * math.cos(dd)
        vv = cv + ln * 0.5 * math.sin(dd)
        _v15_rot("%s_v15_arm2_%d" % (tag, i), t0 + uu, v0 + vv, ln * 0.75, 0.45,
                 ZF + 2.45, ZF + 2.85, m["white"], c, deg=deg + 34)
    # gallery -> wall service band 1.5 m, blue steel
    R("band_n", IN0, IN1, IN0, IN0 + 1.5, ZD, ZD + 0.12, m["cap_h3"])
    R("band_w", IN0, IN0 + 1.5, IN0 + 1.5, IN1, ZD, ZD + 0.12, m["cap_h3"])
    R("band_e", IN1 - 1.5, IN1, IN0 + 1.5, IN1, ZD, ZD + 0.12, m["cap_h3"])
    # three continuous light strips (D6) + six short beats
    R("strip_n", 3.2, 27.8, IN0 + 0.5, IN0 + 1.0, ZD + 0.12, ZD + 0.26, m["h3_strip"])
    R("strip_w", IN0 + 0.5, IN0 + 1.0, 3.2, 27.8, ZD + 0.12, ZD + 0.26, m["h3_strip"])
    R("strip_e", IN1 - 1.0, IN1 - 0.5, 8.0, 27.8, ZD + 0.12, ZD + 0.26, m["h3_strip"])
    for i, (a0, b0) in enumerate(((6.0, 2.6), (12.0, 2.6), (18.0, 2.6),
                                  (6.0, 31.4), (12.0, 31.4), (24.0, 31.4))):
        R("sbeat%d" % i, a0, a0 + 1.8, b0, b0 + 0.5, ZD + 0.12, ZD + 0.26, m["h3_strip"])
    # racks and safes
    for i in range(4):
        R("rack%d" % i, 29.6, 31.9, 13.6 + i * 2.2, 14.8 + i * 2.2, ZD, ZD + 2.4,
          m["metal"])
    for i in range(3):
        R("safe%d" % i, 4.6, 5.8, 13.0 + i * 1.9, 14.2 + i * 1.9, ZD, ZD + 1.5,
          m["dark"])
    for i in range(4):
        R("crate%d" % i, 6.0 + i * 1.6, 7.2 + i * 1.6, 27.4, 28.6, ZD, ZD + 1.0,
          m["container_gray"])
    # one shadow band along the pit west edge (gallery projection)
    R("shade", PX0 + 1.2, PX0 + 2.2, PY0 + 1.2, PY1 - 1.2, ZF + 0.24, ZF + 0.27,
      m["floorshadow"])
    # mid-scale density run B
    for i in range(4):
        for j in range(2):
            R("crateb%d_%d" % (i, j), 12.6 + i * 2.6, 13.8 + i * 2.6,
              24.6 + j * 2.2, 25.8 + j * 2.2, ZD, ZD + 1.0, m["container_gray"])
    for i in range(4):
        for j in range(2):
            R("plateb%d_%d" % (i, j), 25.4 + i * 1.9, 26.6 + i * 1.9,
              26.0 + j * 2.4, 27.2 + j * 2.4, ZD, ZD + 0.22, m["metal"])
    for i in range(6):
        R("wcab%d" % i, 2.2, 3.6, 12.4 + i * 1.9, 13.8 + i * 1.9, ZD, ZD + 1.9,
          m["steel"])
    for i in range(6):
        R("ndrum%d" % i, 12.4 + i * 1.3, 13.3 + i * 1.3, 3.0, 4.2, ZD, ZD + 0.9,
          m["container_olive"] if i % 2 else m["metal"])
    for i in range(4):
        R("etray%d" % i, 24.4, 31.2, 15.2 + i * 2.0, 15.9 + i * 2.0, ZD, ZD + 0.3,
          m["dark"])
    for i in range(6):
        R("scrate%d" % i, 4.0 + i * 1.6, 5.2 + i * 1.6, 25.4, 26.6, ZD, ZD + 1.0,
          m["container_gray"])
    _v15_text("%s_v15_id" % tag, t0, v0, 6.5, 30.0, ZD, ZD + 0.06, "H3", m, c)


# ------------------------------------------------------------------- H4 black
def _v15_h4(tag, t0, v0, z, m, c):
    def R(nm, u0, u1, w0, w1, z0, z1, mat):
        avr("%s_v15_%s" % (tag, nm), t0 + u0, t0 + u1, v0 + w0, v0 + w1, z0, z1, mat, c)

    IN0, IN1 = 0.45, 33.55
    ZF = z + 0.06
    ZD = ZF + 0.24
    R("deck", IN0, IN1, IN0, IN1, ZF, ZD, m["terrace"])
    # green band on the two walls that are green in the real room
    R("green_n", IN0, IN1, IN0, IN0 + 1.2, ZD, ZD + 0.10, m["cap_h4"])
    R("green_e", IN1 - 1.2, IN1, IN0 + 1.2, IN1, ZD, ZD + 0.10, m["cap_h4"])
    # circular hatch: Ø6 ring + 12 radial ribs + hub + inner ring, east side
    _v15_cyl("%s_v15_hatch" % tag, t0 + 28.0, v0 + 17.0, ZD, ZD + 0.14, 3.75,
             m["char_dark"], c, 40)
    _v15_ring("%s_v15_hatch_ring" % tag, t0 + 28.0, v0 + 17.0, 3.62, 0.45, ZD + 0.14,
              ZD + 0.30, m["cope"], c, 40)
    _v15_ring("%s_v15_hatch_ring2" % tag, t0 + 28.0, v0 + 17.0, 2.30, 0.38, ZD + 0.14,
              ZD + 0.28, m["cope"], c, 32)
    for i in range(12):
        a = i * 30.0 + 15.0
        cu = 28.0 + 2.95 * math.cos(math.radians(a))
        cv = 17.0 + 2.95 * math.sin(math.radians(a))
        _v15_rot("%s_v15_rib%d" % (tag, i), t0 + cu, v0 + cv, 1.70, 0.34,
                 ZD + 0.14, ZD + 0.30, m["steel"], c, deg=a)
    _v15_cyl("%s_v15_hub" % tag, t0 + 28.0, v0 + 17.0, ZD + 0.14, ZD + 0.38, 0.85,
             m["ws_yellow"], c, 16)
    # barrel-vault mouth: dark recess pad + two concentric rib arcs + jamb columns
    R("vault", 1.2, 7.2, 2.4, 9.6, ZD, ZD + 0.14, m["char_dark"])
    for i, rr in enumerate((2.0, 3.3, 4.6)):
        _v15_ring("%s_v15_arc%d" % (tag, i), t0 + 6.5, v0 + 6.0, rr, 0.60, ZD + 0.14,
                  ZD + 0.34, m["rib_blue"], c, 40,
                  AV_ROT + math.radians(-90), AV_ROT + math.radians(90))
    for i, ww in enumerate((3.4, 8.6)):
        _v15_cyl("%s_v15_jamb%d" % (tag, i), t0 + 6.5, v0 + ww, ZD, z + 2.8, 0.32,
                 m["white"], c, 12)
    # "日" partition: 2 verticals + 3 horizontals, 1.5 m high with dark cap
    for i, uu in enumerate((12.0, 18.0)):
        R("pv%d" % i, uu, uu + 0.4, 6.0, 14.0, ZD, ZD + 1.2, m["white"])
        R("pvc%d" % i, uu - 0.1, uu + 0.5, 6.0, 14.0, ZD + 1.2, ZD + 1.42, m["cope"])
    # yellow channel arrows so the partitions read as walls, not shelving
    for i, (au, av_, deg) in enumerate(((13.0, 8.6, 0), (16.6, 11.4, 90), (13.0, 12.6, 180))):
        _v15_rot("%s_v15_arrow%d" % (tag, i), t0 + au, v0 + av_, 1.6, 0.45,
                 ZD + 0.14, ZD + 0.24, m["ws_yellow"], c, deg=deg)
        _v15_rot("%s_v15_arrowtip%d" % (tag, i), t0 + au + 0.9, v0 + av_, 0.9, 0.45,
                 ZD + 0.14, ZD + 0.24, m["ws_yellow"], c, deg=deg + 30)
    for i, vv in enumerate((6.0, 10.0, 14.0)):
        R("ph%d" % i, 12.0, 18.0, vv, vv + 0.4, ZD, ZD + 1.2, m["white"])
        R("phc%d" % i, 12.0, 18.0, vv - 0.1, vv + 0.5, ZD + 1.2, ZD + 1.42, m["cope"])
    # overhead crane, single beam
    R("cbeam", 3.0, 31.0, 26.4, 27.6, z + 7.6, z + 8.4, m["steel"])
    _v15_cyl("%s_v15_ctrolley" % tag, t0 + 20.0, v0 + 27.0, z + 8.4, z + 8.9, 0.9,
             m["metal"], c, 12)
    _v15_hcyl("%s_v15_cpod" % tag, t0 + 20.0, v0 + 27.0, z + 6.0, 3.0, 0.75, m["dark"],
              c, 90, 16)
    for i, cu in enumerate((19.6, 20.4)):
        _v15_cyl("%s_v15_ccab%d" % (tag, i), t0 + cu, v0 + 27.0, z + 6.6, z + 8.4, 0.05,
                 m["dark"], c, 4)
    # 4x4 black lift shaft with a 3 m gap in the railing
    R("shaft", 29.0, 33.0, 3.0, 7.0, ZD, ZD + 0.5, m["pit"])
    for i, (a0, a1, b0, b1) in enumerate(((29.0, 33.0, 3.0, 3.25),
                                          (29.0, 29.25, 3.25, 5.0),
                                          (32.75, 33.0, 3.25, 7.0))):
        R("srail%d" % i, a0, a1, b0, b1, ZD + 0.5, ZD + 1.1, m["ws_yellow"])
    # military crates, 4x2 grid
    for i in range(4):
        for j in range(2):
            R("mil%d_%d" % (i, j), 4.0 + i * 2.0, 5.4 + i * 2.0, 28.6 + j * 1.1,
              29.4 + j * 1.1, ZD, ZD + 0.9, m["container_olive"] if (i + j) % 2
              else m["sand"])
    for i in range(4):
        R("blackbox%d" % i, 8.0 + i * 1.4, 9.1 + i * 1.4, 31.6, 32.6, ZD, ZD + 0.8,
          m["dark"])
    # arms + satellite, one arm raised (same kit as H3, different pose)
    _v15_cyl("%s_v15_armbase" % tag, t0 + 21.2, v0 + 22.4, ZD, ZD + 1.0, 0.6,
             m["dark"], c, 12)
    _v15_rot("%s_v15_arm" % tag, t0 + 21.2, v0 + 22.4, 3.4, 0.5, ZD + 1.0, ZD + 1.4,
             m["white"], c, deg=112)
    _v15_cyl("%s_v15_joint" % tag, t0 + 21.2, v0 + 22.4, ZD + 1.0, ZD + 1.45, 0.42,
             m["ws_yellow"], c, 12)
    R("sat", 19.4, 21.2, 20.2, 22.0, ZD + 1.4, ZD + 2.4, m["metal"])
    for i, ang in enumerate((30, -30, 150, -150)):
        _v15_rot("%s_v15_wing%d" % (tag, i), t0 + 20.3, v0 + 21.1, 1.9, 0.8,
                 ZD + 1.8, ZD + 1.92, m["steel"], c, deg=ang)
    for i in range(4):
        R("ecab%d" % i, 24.2, 25.6, 6.0 + i * 2.4, 7.6 + i * 2.4, ZD, ZD + 2.0, m["steel"])
    for i in range(6):
        R("eplate%d" % i, 20.6 + (i % 3) * 2.4, 21.8 + (i % 3) * 2.4,
          24.6 + (i // 3) * 2.4, 25.8 + (i // 3) * 2.4, ZD, ZD + 0.05, m["floorshadow"])
    R("ehose", 22.0, 26.0, 21.0, 21.6, ZD, ZD + 0.8, m["orange"])
    # red/blue pipe runs on the floor to the north then east
    R("pipe_r", IN0, 26.0, 1.75, 2.1, ZD + 0.10, ZD + 0.34, m["orange"])
    R("pipe_b", 25.6, 26.0, 1.75, 20.0, ZD + 0.10, ZD + 0.34, m["evac_blue"])
    # mid-scale density run B
    for i in range(4):
        for j in range(2):
            R("palletb%d_%d" % (i, j), 8.0 + i * 1.9, 9.2 + i * 1.9,
              21.6 + j * 1.6, 22.6 + j * 1.6, ZD, ZD + 0.8, m["container_olive"])
    for i in range(6):
        R("wdrum%d" % i, 4.0 + i * 1.3, 4.9 + i * 1.3, 19.2, 20.4, ZD, ZD + 0.9,
          m["metal"] if i % 2 else m["sand"])
    for i in range(6):
        R("ntray%d" % i, 20.0 + i * 2.0, 21.4 + i * 2.0, 2.4, 3.2, ZD, ZD + 0.3,
          m["dark"])
    for i in range(4):
        R("seplate%d" % i, 26.4 + (i % 2) * 2.4, 27.6 + (i % 2) * 2.4,
          10.0 + (i // 2) * 2.4, 11.2 + (i // 2) * 2.4, ZD, ZD + 0.2, m["metal"])
    # one shadow pair: crane-beam band + arch-mouth light
    R("shade_beam", 3.0, 31.0, 26.9, 28.1, ZD + 0.24, ZD + 0.42, m["floorshadow"])
    R("shade_arch", 6.6, 9.4, 4.6, 7.4, ZD + 0.06, ZD + 0.10, m["garden_coping"])
    for i in range(5):
        R("spallet%d" % i, 24.0, 25.2, 14.0 + i * 1.6, 15.0 + i * 1.6, ZD, ZD + 0.9,
          m["container_olive"] if i % 2 else m["sand"])
    _v15_text("%s_v15_id" % tag, t0, v0, 17.0, 31.0, ZD, ZD + 0.06, "H4", m, c)
