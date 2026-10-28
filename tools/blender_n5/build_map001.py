"""
Build MAP001, the full 28 x 20 courtyard layout, from the native module set.

Coordinate contract (also written into layout.json):
  * engine: Y up, ground XZ, map centre (0,0,0), X in [-14,14], Z in [-10,10]
  * Blender scene: X = engine X, Y = -engine Z, Z = engine Y
  * module local front is -Y in Blender, which is +Z in engine space; layout
    rotation_y is the engine yaw applied to that local front.
  * paving modules are sunk so their top surface is engine Y = 0 (ENV001's own
    source keeps its 0.14 module-space top; the layout position compensates).
  * 1 Blender unit = 1 world unit.

The map is assembled from the same builder functions that produce the
standalone module sources (plus the existing PROP001 bench appended from its
source file).  No background image is used.  Cycles renders are previews.

Run from the project root:
  .tools/blender/blender-4.5.15-windows-x64/blender.exe --background --factory-startup \
      --python tools/blender/build_map001.py
"""
import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

import courtyard_lib as cl  # noqa: E402

# Whole-scene style switch, owned by courtyard_lib so foliage and grass agree.
STYLE = cl.STYLE
import courtyard_postcard as pc  # noqa: E402
import env001_layout  # noqa: E402
import build_env_courtyard as env  # noqa: E402
import build_props_courtyard as props  # noqa: E402

BUILD_OUTPUT_ROOT = os.environ.get("N5_BUILD_OUTPUT_ROOT", "").strip()
if BUILD_OUTPUT_ROOT:
    BUILD_LAYOUT = os.path.join(BUILD_OUTPUT_ROOT, "source")
    BUILD_PREVIEW = os.path.join(BUILD_OUTPUT_ROOT, "previews")
    os.makedirs(BUILD_LAYOUT, exist_ok=True)
    os.makedirs(BUILD_PREVIEW, exist_ok=True)
else:
    BUILD_LAYOUT = cl.SRC_LAYOUT
    BUILD_PREVIEW = cl.PREVIEW_LAYOUT
BLEND = os.path.join(BUILD_LAYOUT, "MAP001_courtyard.blend")
GLB = os.path.join(BUILD_LAYOUT, "MAP001_courtyard.glb")
LAYOUT = os.path.join(BUILD_LAYOUT, "layout.json")
PNG = os.path.join(BUILD_PREVIEW, "MAP001_courtyard.png")
PNG_TOP = os.path.join(BUILD_PREVIEW, "MAP001_topdown.png")

MAP_SIZE = (28.0, 20.0)
SOIL_TOP = -0.02

# 4x4 m paving modules in map (x, z) space, shared by the paving builder and the
# ground-cover placement so grass can never be planted on top of stone.
PAVING_CENTERS = [
    (-4, -4), (0, -4), (4, -4),
    (-4, 0), (0, 0), (4, 0),
    (-4, 4), (0, 4), (4, 4),
    (-8, -4), (-8, 0), (-8, 4),
    (8, 4), (12, 6), (0, -8), (0, 8),
]
PAVING_HALF = 2.0


def on_paving(x, z, inset=0.12, margin=0.0):
    """True when a map-space point falls inside a paving module.

    `inset` shrinks the module before testing (tolerates a prop that is a little
    inside the stone). `margin` grows it - that is the one planting needs, since
    a tuft must keep its whole radius clear of the slabs. Passing a positive
    radius as `inset` would do the opposite and let more grass onto the paving.
    """
    limit = PAVING_HALF - inset + margin
    return any(abs(x - cx) <= limit and abs(z - cz) <= limit
               for (cx, cz) in PAVING_CENTERS)


# A2 instrumentation: switch distant layers individually so the "dark band"
# can be attributed to one layer instead of guessed. Variant runs render a
# preview only and never overwrite the canonical GLB.
N5_LAYERS = {
    "north_hedge": os.environ.get("N5_NO_NORTH_HEDGE") != "1",
    "back_row": os.environ.get("N5_NO_BACK_ROW") != "1",
    "side_hedges": os.environ.get("N5_NO_SIDE_HEDGES") != "1",
    "front_strips": os.environ.get("N5_NO_FRONT_STRIPS") != "1",
    "bg_trees": os.environ.get("N5_NO_BG_TREES") != "1",
    "treeline": os.environ.get("N5_NO_TREELINE") != "1",
}
N5_VARIANT = os.environ.get("N5_VARIANT", "").strip()

# 2026-10-26 D1: grass/ground-cover density scale. Grass and hedge-leaf cards
# carry ~69% of the map triangles while paving (half the frame) carries 0.5%.
# The scale only multiplies how many turf patches are planted; patch positions,
# spread and blade shape are unchanged, so lowering it thins the sward instead
# of moving it. Default 1.0 keeps every existing build byte-identical.
N5_GRASS_SCALE = float(os.environ.get("N5_GRASS_SCALE", "1.0"))
# Per-group multipliers on top of the master scale: the ring planter is the
# focal prop at the formal camera, the background strips are not. Defaults keep
# every group at master scale, so an unset environment builds as before.
N5_GRASS_AREAS = float(os.environ.get("N5_GRASS_AREAS", "2.0"))
N5_GRASS_BEDS = float(os.environ.get("N5_GRASS_BEDS", "1.0"))
N5_GRASS_RING = float(os.environ.get("N5_GRASS_RING", "1.0"))
N5_GRASS_SIDES = float(os.environ.get("N5_GRASS_SIDES", "1.0"))
# D1b: blade-level thinning that leaves tuft positions (and therefore the RNG
# stream) untouched. Prefer this over the count scales above when a change must
# not disturb anything built after the grass.
# The D1b/D2 density knobs used to default to 1.0 and were set by hand per
# run, so a plain rebuild silently produced the pre-reduction 188 MB / 1.45M
# triangle map. The values below are the ones the shipped candidate used;
# keeping them as defaults is what makes a rebuild comparable at all.
# PAVING_VARIANTS now defaults on for the same reason: forgetting it once
# dropped every slab to variant 0 and added 20% triangles.
N5_GRASS_BLADE_KEEP = float(os.environ.get("N5_GRASS_BLADE_KEEP", "0.44"))
# The ring planter is the focal prop in every formal shot; 0 means "follow the
# global keep", any other value overrides it for the ring and side planters.
# The ring bed sits at the centre of every frame, so it keeps more blades than
# the rest of the lawn: 0.55 against the global 0.44. Defaulting this to 0.0
# silently made the ring inherit the stricter global value.
N5_GRASS_RING_BLADE_KEEP = float(os.environ.get("N5_GRASS_RING_BLADE_KEEP", "0.55"))

# Look-dev knobs (bench A/B/C): every blade in the map is built by _add_blade,
# so scaling width/height there covers lawn, ring bed and side planters at once
# without touching the individual tuft call sites.
N5_GRASS_WIDTH_SCALE = float(os.environ.get("N5_GRASS_WIDTH_SCALE", "1") or 1)
N5_GRASS_HEIGHT_SCALE = float(os.environ.get("N5_GRASS_HEIGHT_SCALE", "1") or 1)
# Blades per tuft. Widening blades without thinning them keeps the same edge
# count per pixel (just chunkier), so the look-dev bench moves width and count
# together: fewer, wider blades read calmer at 720p than many thin ones.
N5_GRASS_COUNT_SCALE = float(os.environ.get("N5_GRASS_COUNT_SCALE", "1") or 1)
# Blade silhouette: segments / bend exponent / tip taper / awn forks.
N5_GRASS_SEGMENTS = int(os.environ.get("N5_GRASS_SEGMENTS", "2") or 2)
N5_GRASS_CURVE = float(os.environ.get("N5_GRASS_CURVE", "2.0") or 2.0)
N5_GRASS_TAPER = float(os.environ.get("N5_GRASS_TAPER", "0.82") or 0.82)
N5_GRASS_SPIKE = os.environ.get("N5_GRASS_SPIKE", "0") == "1"

# 2026-10-26 D2: hedge leaf-card density. Cards are 4 tris each and the two
# hedge rows carried 467,624 of the map's triangles (41%) for a band a few
# dozen pixels tall at the formal camera. `*_BACK_KEEP` addresses the flank
# that faces away from the courtyard: those cards sit behind the solid hedge
# volume from every shipped camera, so 0 removes them without touching the
# silhouette. Top caps are never thinned. Defaults 1.0 keep the old build.
N5_HEDGE_KEEP = float(os.environ.get("N5_HEDGE_KEEP", "0.78"))
# W3 vegetation_depth: the back face used to be stripped to zero, so the hedge
# read as one flat card from the front. Keeping a thin back layer lets the
# near face, the mid band and the far foliage separate by density instead of
# by a silhouette line.
N5_HEDGE_BACK_KEEP = float(os.environ.get("N5_HEDGE_BACK_KEEP", "0.42"))
N5_HEDGE_FAR_KEEP = float(os.environ.get("N5_HEDGE_FAR_KEEP", "0.74"))
N5_HEDGE_FAR_BACK_KEEP = float(os.environ.get("N5_HEDGE_FAR_BACK_KEEP", "0.45"))


def _try_render(path, label):
    """Render a diagnostic preview without aborting the build.

    The GLB and layout.json are the product; the overview/top-down PNGs are
    previews. A Cycles save failure (file lock, tangent abort on an ngon mesh)
    must not leave a rebuilt GLB without its layout, which happened on the D1
    grass run.
    """
    try:
        cl.render_to(path)
        return True
    except Exception as exc:  # noqa: BLE001 - preview is best-effort
        print("PREVIEW_RENDER_FAILED=%s %s" % (label, exc))
        return False


def _gs(count, group=1.0):
    """Scale a patch count without ever reaching zero.

    2026-10-27: this used to clamp at `count` so the knobs could only thin the
    sward. Filling the bare ground on the right of frame needs the opposite
    direction, so the scale is now symmetric. Defaults are still 1.0, which is
    exactly the old behaviour.
    """
    scale = N5_GRASS_SCALE * group
    return max(1, int(round(count * scale)))

STATE = {
    "instances": [],
    "interactions": [],
    "proxies": [],
    "occlusion": [],
}


def record(asset_id, inst_id, x, z, rot=0.0, y=0.0, scale=1.0,
           collider=None, interaction_id=None, occlusion_group=None,
           source=None, note=None, objects=None, merged_object=None,
           lod=None):
    entry = {
        "asset_id": asset_id,
        "instance_id": inst_id,
        "position": [round(x, 3), round(y, 3), round(z, 3)],
        "rotation_y": round(rot, 2),
        "scale": [scale, scale, scale],
        "collider": collider or {"type": "none"},
        "interaction_id": interaction_id,
        "occlusion_group": occlusion_group,
        "source": source,
        "note": note,
    }
    if objects:
        entry["objects"] = [o.name for o in objects]
    if merged_object:
        entry["merged_object"] = merged_object
    if lod:
        entry["lod"] = lod
    STATE["instances"].append(entry)
    return entry


def box_collider(x, z, w, d, rot=0.0, height=1.0):
    return {"type": "box", "center": [round(x, 3), round(z, 3)],
            "size": [round(w, 3), round(d, 3)],
            "rotation_y": round(rot, 2), "height": round(height, 3)}


def circle_collider(x, z, radius, height=1.0):
    return {"type": "circle", "center": [round(x, 3), round(z, 3)],
            "radius": round(radius, 3), "height": round(height, 3)}


def join_meshes(objects, name, collection):
    meshes = [o for o in objects if o.type == "MESH"]
    if len(meshes) == 1:
        meshes[0].name = name
        meshes[0]["merged_from"] = 1
        return meshes[0]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    active = meshes[0]
    bpy.context.view_layer.objects.active = active
    bpy.ops.object.join()
    active.name = name
    active["merged_from"] = len(meshes)
    return active


def add_ground(collection):
    bm = bmesh.new()
    cl.add_box(bm, (0, 0, SOIL_TOP - 0.01), (28.0, 20.0, 0.02), mat_index=0)
    ground = cl.finish_mesh("MAP001_ground", bm, [cl.mat_ground_soil()],
                            collection)

    skirt_bm = bmesh.new()
    cl.add_box(skirt_bm, (0, 0, -0.21), (40.0, 32.0, 0.16), mat_index=0)
    skirt = cl.finish_mesh("MAP001_ground_skirt", skirt_bm,
                           [cl.mat_ground_skirt()], collection)
    return [ground, skirt]


def _add_blade(bm, base, height, lean, width, mat_index, rng, segments=None):
    base = Vector(base)
    lean = Vector(lean)
    if segments is None:
        segments = N5_GRASS_SEGMENTS
    if N5_GRASS_HEIGHT_SCALE != 1.0:
        height = height * N5_GRASS_HEIGHT_SCALE
        lean = lean * N5_GRASS_HEIGHT_SCALE
    if N5_GRASS_WIDTH_SCALE != 1.0:
        width = width * N5_GRASS_WIDTH_SCALE
    wdir = Vector((-lean.y, lean.x, 0.0))
    if wdir.length < 1e-5:
        wdir = Vector((1.0, 0.0, 0.0))
    wdir.normalize()
    prev = None
    for s in range(segments + 1):
        t = s / segments
        # A straight t^2 lean gives a rigid needle. A higher exponent bends the
        # blade over near the tip, which is what the reference sward does and
        # what stops the grass reading as pins stuck in the ground.
        k = t ** N5_GRASS_CURVE
        p = base + Vector((lean.x * k, lean.y * k, height * t))
        w = width * (1.0 - N5_GRASS_TAPER * t) * 0.5
        l = bm.verts.new(p - wdir * w)
        r = bm.verts.new(p + wdir * w)
        if prev is not None:
            f = bm.faces.new((prev[0], l, r, prev[1]))
            f.material_index = mat_index
        prev = (l, r)
    top = base + Vector((lean.x, lean.y, height))
    if N5_GRASS_SPIKE:
        # Dry-grass awns: two short forks off the tip instead of a single point.
        for sign in (-1, 1):
            tp = top + Vector((0, 0, height * (0.10 if sign > 0 else 0.02))) \
                + wdir * (width * 0.30 * sign)
            v = bm.verts.new(tp)
            f = bm.faces.new((prev[0], v, prev[1]))
            f.material_index = mat_index
        return
    tip = bm.verts.new(top + Vector((0, 0, height * 0.08)))
    f = bm.faces.new((prev[0], tip, prev[1]))
    f.material_index = mat_index


def _add_flower(bm, center, rng, size, petal_index=0, core_index=1,
                stem_index=3, stem_length=0.20):
    center = Vector(center)
    spin = rng.uniform(0, math.tau)
    cl.add_cylinder(bm, center - Vector((0, 0, stem_length)), center,
                    0.0045, 0.0035, 4, stem_index)
    for i in range(5):
        a = math.tau * i / 5.0 + spin
        off = Vector((math.cos(a), math.sin(a), 0.0)) * size * 0.42
        cl.add_leaf(bm, center + off, (0, 0, 1), size,
                    a + math.pi / 2.0, petal_index, tilt=0.22)
    cl.add_leaf(bm, center + Vector((0, 0, size * 0.06)), (0, 0, 1),
                size * 0.30, spin, core_index, tilt=0.0)


def _add_grass_pad(bm, center, rng, radius, height, blade_width, mats, count):
    """Cartoon tuft: 5 wide flat blades, no subdivision, 1 triangle each.

    Low-poly grass reads as a few chunky blades with a hard edge; subdividing
    them (the o/r path) only produces thin needles that alias into noise.
    """
    n = max(3, min(7, int(round(count * 0.45))))
    for _ in range(n):
        a = rng.uniform(0, math.tau)
        rr = radius * math.sqrt(rng.uniform(0, 1)) * 0.7
        bx = center[0] + rr * math.cos(a)
        by = center[1] + rr * math.sin(a)
        bz = center[2] + 0.004
        h = height * rng.uniform(0.78, 1.25)
        lean = 0.34 * h
        w = blade_width * rng.uniform(1.5, 2.3)
        mat = rng.choice(mats)
        tip = bm.verts.new((bx + math.cos(a) * lean, by + math.sin(a) * lean, bz + h))
        left = bm.verts.new((bx - math.sin(a) * w, by + math.cos(a) * w, bz))
        right = bm.verts.new((bx + math.sin(a) * w, by - math.cos(a) * w, bz))
        face = bm.faces.new((left, right, tip))
        face.material_index = mat
        face.smooth = False


def _add_grass_tuft(bm, center, rng, radius, height, blade_width, mats, count=14,
                    keep=None):
    if STYLE == "c":
        return _add_grass_pad(bm, center, rng, radius, height, blade_width, mats, count)
    blade_keep = N5_GRASS_BLADE_KEEP if keep is None else keep
    if N5_GRASS_COUNT_SCALE != 1.0:
        count = max(1, int(round(count * N5_GRASS_COUNT_SCALE)))
    for i in range(count):
        a = rng.uniform(0, math.tau)
        rr = radius * math.sqrt(rng.uniform(0, 1))
        base = (center[0] + rr * math.cos(a), center[1] + rr * math.sin(a),
                center[2] + 0.005)
        h = height * rng.uniform(0.55, 1.15)
        lean = (rng.uniform(-0.22, 0.22) * h, rng.uniform(-0.22, 0.22) * h, 0)
        w = blade_width * rng.uniform(0.7, 1.3)
        mat = rng.choice(mats)
        # 2026-10-26 D1b: thin blades, never tufts. _add_blade draws no random
        # numbers, so skipping a blade leaves the RNG stream untouched: every
        # tuft keeps its original position and every mesh built after the grass
        # (paving, moss, flowers, cobbles) stays byte-identical. Thinning tuft
        # counts instead re-rolled the ring planter into bald patches.
        if blade_keep < 1.0 and ((i * 2654435761) % 1000) / 1000.0 >= blade_keep:
            continue
        _add_blade(bm, base, h, lean, w, mat, rng)


VEG_AUDIT = []


def _add_turf_patch(bm, center, rng, spread, mats, density, height,
                    blade_width, z=0.0, keep=None, blocked=None,
                    container="unknown"):
    """A tight sward of overlapping tufts so ground reads as planted, not sticked.

    Blades are shorter and wider than a lone tuft and each patch re-uses one of
    a few seed centres, which keeps the merged mesh cheap enough to draw.
    """
    for _ in range(density):
        a = rng.uniform(0, math.tau)
        rr = spread * math.sqrt(rng.uniform(0, 1))
        cx = center[0] + rr * math.cos(a)
        cz = center[1] + rr * math.sin(a)
        tuft_r = rng.uniform(0.10, 0.20) * spread + 0.07
        # A tuft is not a point: blades reach roughly tuft_r plus their lean
        # beyond the centre. Testing only the centre let the sward spill up to
        # ~0.15 m onto the flagstones, which is what read as "grass on the
        # paving". Test the tuft's own radius against the paving edge instead.
        hit = False
        if blocked is not None:
            try:
                hit = bool(blocked(cx, cz, margin=tuft_r + 0.16))
            except TypeError:
                hit = bool(blocked(cx, cz))
        VEG_AUDIT.append({"x": round(cx, 3), "z": round(cz, 3),
                          "h": round(center[2] + z, 3),
                          "on_paving": hit, "container": container,
                          "dropped": hit})
        if hit:
            continue
        _add_grass_tuft(bm, (cx, cz, center[2] + z), rng, tuft_r,
                        height * rng.uniform(0.72, 1.18),
                        blade_width * rng.uniform(1.15, 1.75), mats,
                        count=rng.randint(10, 14), keep=keep)


def _hedge_top(z1, u, fixed):
    """Hedge silhouette sampled in world space, shared by mass and leaf skin.

    Both builders used to compute their own sine from a column index, so the
    skin drifted off the volume. Low-frequency notches also stop the row from
    reading as one flat band across the top of the camera.
    """
    swell = (0.46 * math.sin(u * 0.86 + fixed * 0.53)
             + 0.27 * math.sin(u * 2.13 - fixed * 0.31)
             + 0.12 * math.sin(u * 4.70 + fixed * 1.10))
    notch = -1.02 if math.sin(u * 0.62 + fixed * 0.21) < -0.58 else 0.0
    return z1 + swell + notch


def _hedge_volume(bm, axis, fixed, start, end, z0, z1, thick, rng,
                  mat_index=0):
    """Continuous displaced hedge volume with a wavy top; no topiary balls."""
    cols = max(10, int((end - start) / 0.42))
    rows = 6
    front, back = [], []
    for i in range(cols + 1):
        u = start + (end - start) * i / cols
        top = _hedge_top(z1, u, fixed) + rng.uniform(-0.09, 0.09)
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
                     mats, tall_shoots=True, keep=1.0, keep_back=None):
    """`mats` is a list of mesh material-slot indices to draw cards from.

    `keep` thins the leaf cards on the courtyard-facing side, `keep_back` on
    the side facing away. Cards are thinned without changing how many random
    numbers are drawn, so neighbouring meshes stay bit-identical. The top layer
    and the top caps are exempt: they carry the silhouette, and at the grazing
    angle of the side hedges a thinned ridge lets the pale outer ground show
    through.
    """
    if STYLE == "c":
        # Low-poly hedges are the solid box already built underneath; a card
        # skin on top would only add 40x the triangles for a fuzzier edge.
        return 0
    if keep_back is None:
        keep_back = keep
    # Hedges ring the courtyard, so the visible flank is always the one facing
    # the origin and the other flank is buried in the hedge volume.
    front_sign = -1 if fixed > 0 else 1
    cols = max(8, int((end - start) / 0.52))
    for i in range(cols + 1):
        u = start + (end - start) * i / cols + rng.uniform(-0.12, 0.12)
        top = _hedge_top(z1, u, fixed)
        for side in (-1, 1):
            side_keep = keep if side == front_sign else keep_back
            for t in (0.14, 0.34, 0.54, 0.75, 0.94):
                z = z0 + (top - z0) * t
                off = thick / 2 + rng.uniform(0.02, 0.18)
                if axis == "x":
                    center = (u, fixed + side * off, z + rng.uniform(-0.05, 0.05))
                else:
                    center = (fixed + side * off, u, z + rng.uniform(-0.05, 0.05))
                layer_keep = 1.0 if t >= 0.9 else side_keep
                cl.add_leaf_cluster(bm, center, rng.uniform(0.56, 0.78), 42, rng,
                                    mats, leaf_size=_bg_leaf(rng.uniform(0.16, 0.23)),
                                    flatten=0.38, shell_inner=0.34, z_min=-0.80,
                                    keep=layer_keep)
        # A leaf cap along the wavy top closes the silhouette.
        for dx in (-0.20, 0.0, 0.20):
            if axis == "x":
                center = (u + dx, fixed + rng.uniform(-0.24, 0.24), top + 0.06)
            else:
                center = (fixed + rng.uniform(-0.24, 0.24), u + dx, top + 0.06)
            cl.add_leaf_cluster(bm, center, rng.uniform(0.48, 0.66), 34, rng,
                                mats, leaf_size=_bg_leaf(rng.uniform(0.17, 0.235)),
                                flatten=0.52, shell_inner=0.26, z_min=-0.45)
        if tall_shoots and i % 5 == 2:
            if axis == "x":
                anchor = Vector((u, fixed, top - 0.12))
            else:
                anchor = Vector((fixed, u, top - 0.12))
            endp = anchor + Vector((rng.uniform(-0.12, 0.12),
                                    rng.uniform(-0.12, 0.12),
                                    rng.uniform(0.42, 0.72)))
            cl.add_smooth_tube(bm, [anchor, endp], [0.014, 0.003], segments=4,
                               mat_index=mats[0], ring_noise=0.04, rng=rng)
            cl.add_leaf_cluster(bm, endp, 0.22, 10, rng, mats,
                                leaf_size=_bg_leaf(0.15), flatten=0.8, shell_inner=0.25,
                                z_min=-0.5)


def _bg_leaf(size):
    """Undo N5_LEAF_SCALE for background foliage.

    The hero crown needs oversized cards to read at 4 m, but the same multiplier
    on a hedge 14 m away inflates every background leaf to about a metre and the
    horizon becomes a heap of flat brown triangles. Background clusters keep the
    size they were authored at.
    """
    return size / max(1.0, cl.LEAF_SCALE ** 0.55)


def add_background_scenery(collection):
    """Continuous hedge walls, background autumn trees and a distant treeline.

    Native meshes only, no colliders and no catalog instances. The hedge is a
    displaced volume with leaf skin, not a row of spheres.
    """
    rng = random.Random(20261025)
    mass_bm = bmesh.new()
    leaf_bm = bmesh.new()
    # The far hedge row is kept as its own object pair so A2 can isolate which
    # layer makes the dark band by toggling visibility, instead of guessing or
    # paying for a full MAP001 rebuild per hypothesis.
    far_mass_bm = bmesh.new()
    far_leaf_bm = bmesh.new()
    # 2026-10-27: the volume under the leaf skin used to borrow the leaf
    # palette, and with no cards covering the crown of the hedge it showed
    # through as a band of smooth cream "dunes" across the top of frame. The
    # volume is interior shadow now; every lit surface is a leaf card.
    mass_mats = [cl.mat_leaf_mass(), cl.mat_leaf_mass(),
                 cl.mat_leaf_mass(), cl.mat_leaf_mass()]
    # One merged slot list for every card mesh; the palettes below are slot
    # indices, so a row can be graded without rebuilding the mesh.
    leaf_cards_mats = [cl.mat_leaf_olive(), cl.mat_leaf_ochre(),
                       cl.mat_leaf_gold(), cl.mat_leaf_amber(),
                       cl.mat_leaf_deep(), cl.mat_leaf_far()]
    near_leaf = [0, 1, 2, 3, 0, 4, 2]
    # The far row is graded toward a desaturated cool olive so hedge, wall and
    # paving no longer sit in one brightness band across the top of frame.
    far_leaf = [5, 4, 5, 3, 4, 5]
    front_leaf = [0, 4, 3]

    # North hedge: continuous wall behind the 0.79 m low wall.
    if N5_LAYERS["north_hedge"]:
        _hedge_volume(mass_bm, "x", -10.85, -14.2, 14.2, 0.0, 1.72, 1.45, rng, 0)
        _hedge_leaf_skin(leaf_bm, "x", -10.85, -14.2, 14.2, 0.0, 1.72, 1.45, rng,
                         near_leaf, keep=N5_HEDGE_KEEP,
                         keep_back=N5_HEDGE_BACK_KEEP)
    # A second, higher leaf row behind gives layered depth without a second
    # solid wall.
    if N5_LAYERS["back_row"]:
        _hedge_volume(far_mass_bm, "x", -11.95, -14.2, 14.2, 0.0, 1.95, 1.05, rng, 3)
        _hedge_leaf_skin(far_leaf_bm, "x", -11.95, -14.2, 14.2, 0.0, 1.95, 1.05, rng,
                         far_leaf, tall_shoots=False, keep=N5_HEDGE_FAR_KEEP,
                         keep_back=N5_HEDGE_FAR_BACK_KEEP)

    # Side hedges along the east/west railings.
    if N5_LAYERS["side_hedges"]:
        for sx in (-14.75, 14.75):
            _hedge_volume(mass_bm, "y", sx, -9.4, 9.4, 0.0, 1.62, 1.15, rng, 2)
            _hedge_leaf_skin(leaf_bm, "y", sx, -9.4, 9.4, 0.0, 1.62, 1.15, rng,
                             near_leaf, keep=N5_HEDGE_KEEP,
                             keep_back=N5_HEDGE_BACK_KEEP)

    # Low front hedge strips at the wall base, leaving the north path open.
    if N5_LAYERS["front_strips"]:
        for (x0, x1) in ((-14.0, -4.4), (4.4, 14.0)):
            _hedge_volume(mass_bm, "x", -9.28, x0, x1, 0.0, 0.96, 0.72, rng, 0)
            _hedge_leaf_skin(leaf_bm, "x", -9.28, x0, x1, 0.0, 0.96, 0.72, rng,
                             front_leaf, tall_shoots=False, keep=N5_HEDGE_KEEP,
                             keep_back=N5_HEDGE_BACK_KEEP)

    # Ivy pads on the wall face.
    for i in range(60):
        x = rng.uniform(-13.4, 13.4)
        if abs(x) < 2.6:
            continue
        cl.add_leaf_cluster(leaf_bm, (x, -9.42, rng.uniform(0.38, 0.82)),
                            rng.uniform(0.24, 0.42), 14, rng,
                            [2, 1, 0, 3], leaf_size=_bg_leaf(0.115), flatten=0.44,
                            shell_inner=0.18, z_min=-0.45)

    hedge = cl.finish_mesh("MAP001_bg_hedge", mass_bm, mass_mats, collection)
    bpy.ops.object.select_all(action="DESELECT")
    hedge.select_set(True)
    bpy.context.view_layer.objects.active = hedge
    bpy.ops.object.shade_smooth()
    hedge.select_set(False)
    hedge_cards = cl.finish_mesh("MAP001_bg_hedge_cards", leaf_bm,
                                 leaf_cards_mats, collection)
    for obj in (hedge, hedge_cards):
        if obj is None:
            continue
        obj["asset_id"] = "SCENERY"
        obj["role"] = "continuous background hedge outside the playable area"

    far_hedge = cl.finish_mesh("MAP001_bg_hedge_far", far_mass_bm, mass_mats,
                               collection)
    bpy.ops.object.select_all(action="DESELECT")
    far_hedge.select_set(True)
    bpy.context.view_layer.objects.active = far_hedge
    bpy.ops.object.shade_smooth()
    far_hedge.select_set(False)
    far_hedge_cards = cl.finish_mesh("MAP001_bg_hedge_far_cards", far_leaf_bm,
                                     leaf_cards_mats, collection)
    for obj in (far_hedge, far_hedge_cards):
        if obj is None:
            continue
        obj["asset_id"] = "SCENERY"
        obj["role"] = "second, higher hedge row behind the north hedge"

    # The strip between the hedge and the treeline used to be the flat skirt
    # plane, which read as a wall across the horizon. Low haze-toned rises give
    # the ground something to recede into.
    far_bm = bmesh.new()
    far_mats = [cl.mat_leaf_haze(), cl.mat_leaf_mid_haze()]
    for i in range(9):
        mx = -13.0 + i * 3.25 + rng.uniform(-0.8, 0.8)
        my = rng.uniform(-15.6, -12.3)
        mr = rng.uniform(1.25, 1.75)
        cl.add_mass_lobe(far_bm, (mx, my, rng.uniform(0.18, 0.36)), mr, rng,
                         flatten=0.18, subdiv=2, displace=0.025, mat_index=1)
    far_rises = cl.finish_mesh("MAP001_far_rises", far_bm, far_mats, collection)
    far_rises["asset_id"] = "SCENERY"
    far_rises["role"] = "low haze-toned ground rises between hedge and treeline"

    # Background autumn trees: crown centres low enough to clear the hedge and
    # sit inside the top of the formal camera.
    tree_trunk_bm = bmesh.new()
    tree_leaf_bm = bmesh.new()
    # Far layers step LIGHTER, not darker (aerial perspective). n4 graded
    # distance darker than the near hedge, which inverted depth and read as a
    # dark band across the top of frame.
    tree_mats = [cl.mat_leaf_atlas()]
    # Background crowns get only haze mats: with the warm key they used to
    # render as dark maroon lumps that pull the eye to the top of frame.
    # Far crowns assign card material indices 0..2. A one-slot list silently
    # exported indices 1 and 2 as the glTF default white material, which caused
    # the pale triangular foliage band in the game camera.
    bg_tree_mats = [cl.mat_leaf_atlas(), cl.mat_leaf_atlas(), cl.mat_leaf_atlas()]
    bg_tree_specs = (((-12.2, -13.9, 5.8, 0.95),
                      (-6.0, -14.6, 6.1, 1.02),
                      (0.8, -14.2, 5.7, 0.90),
                      (6.8, -14.9, 6.0, 1.00),
                      (12.0, -14.0, 5.8, 0.92)) if N5_LAYERS["bg_trees"] else ())
    for ti, (tx, ty, th, tr) in enumerate(bg_tree_specs):
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
                    tr * rr * cr, 60, rng, [1, 2, 1, 0, 2, 1],
                    leaf_size=_bg_leaf(rng.uniform(0.20, 0.29)),
                    flatten=0.78, shell_inner=0.28, z_min=-0.58)
    tree_trunks = cl.finish_mesh("MAP001_bg_tree_trunks", tree_trunk_bm,
                                 [cl.mat_wood_dark()], collection)
    tree_crowns = cl.finish_mesh("MAP001_bg_tree_crowns", tree_leaf_bm,
                                 bg_tree_mats, collection)
    for obj in (tree_trunks, tree_crowns):
        obj["asset_id"] = "SCENERY"
        obj["role"] = "background autumn trees behind hedge"

    # Distant treeline replaces the flat grey roof boxes: overlapping crowns
    # and a low dark ribbon close the top of frame naturally.
    band_bm = bmesh.new()
    band_leaf_bm = bmesh.new()
    if N5_LAYERS["treeline"]:
        # P1-foreground pass: keep the horizon as a soft, low canopy instead
        # of a tall brown wall at the top of the playable camera.
        _hedge_volume(band_bm, "x", -16.2, -16.0, 16.0, 2.0, 3.35, 1.15, rng, 0)
    for i in range(27 if N5_LAYERS["treeline"] else 0):
        x = -15.6 + i * 0.95 + rng.uniform(-0.25, 0.25)
        z = 3.9 + 0.72 * math.sin(i * 0.55) + rng.uniform(-0.15, 0.20)
        cl.add_leaf_cluster(band_leaf_bm, (x, -16.1, z), rng.uniform(0.95, 1.35),
                            32, rng, [2, 2, 1, 2, 0],
                            leaf_size=_bg_leaf(rng.uniform(0.20, 0.26)),
                            flatten=0.80, shell_inner=0.22, z_min=-0.65)
    # A light, lower crown line closes the skyline without making a jagged
    # mountain silhouette. Fewer cards also reduce far-scene overdraw.
    for i in range(17 if N5_LAYERS["treeline"] else 0):
        x = -15.2 + i * 1.9 + rng.uniform(-0.30, 0.30)
        z = 4.75 + 0.45 * math.sin(i * 0.8 + 0.7) + rng.uniform(-0.15, 0.20)
        cl.add_leaf_cluster(band_leaf_bm, (x, -16.3, z), rng.uniform(0.70, 1.05),
                            28, rng, [2, 1, 2, 2, 0, 2],
                            leaf_size=_bg_leaf(rng.uniform(0.20, 0.26)),
                            flatten=0.76, shell_inner=0.25, z_min=-0.55)
    band = cl.finish_mesh("MAP001_bg_treeline_mass", band_bm,
                          [cl.mat_leaf_haze(), cl.mat_leaf_mid_haze()], collection)
    band_cards = cl.finish_mesh("MAP001_bg_treeline_cards", band_leaf_bm,
                                bg_tree_mats, collection)
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

def add_proxy_box(collection, name, x, z, w, d, rot, height):
    bm = bmesh.new()
    cl.add_box(bm, (0, 0, height / 2.0), (w, d, height), mat_index=0)
    obj = cl.finish_mesh(name, bm, [], collection)
    obj.location = (x, -z, 0.0)
    obj.rotation_euler = (0, 0, math.radians(rot))
    obj.display_type = "WIRE"
    obj.hide_render = True
    obj["collision_proxy"] = True
    obj["shape"] = "box"
    STATE["proxies"].append({"name": name, "shape": "box",
                             "center": [x, 0, z], "size": [w, height, d],
                             "rotation_y": rot})
    return obj


def add_proxy_circle(collection, name, x, z, radius, height):
    bm = bmesh.new()
    cl.add_cylinder(bm, (0, 0, 0), (0, 0, height), radius, radius, 16, 0)
    obj = cl.finish_mesh(name, bm, [], collection)
    obj.location = (x, -z, 0.0)
    obj.display_type = "WIRE"
    obj.hide_render = True
    obj["collision_proxy"] = True
    obj["shape"] = "circle"
    STATE["proxies"].append({"name": name, "shape": "circle",
                             "center": [x, 0, z], "radius": radius,
                             "height": height})
    return obj


def add_accents(collection):
    """Colour accents the reference uses to break the warm monochrome: a few
    glazed jars and two short bunting lines (teal/orange/cream). Small saturated
    objects at human scale do the colour work that post-processing cannot."""
    rng = random.Random(20261027 + 5)
    teal = cl.make_procedural_material("MAT_ceramic_teal", "#4F7C74", roughness=0.34,
                                       noise_scale=5.0, color_variation=0.05,
                                       roughness_variation=0.08, bump_strength=0.05)
    flag_teal = cl.make_procedural_material("MAT_flag_teal", "#3E6E6A", roughness=0.78)
    flag_orange = cl.make_procedural_material("MAT_flag_orange", "#C4653A", roughness=0.78)
    flag_cream = cl.make_procedural_material("MAT_flag_cream", "#D8C7A6", roughness=0.80)

    jars_bm = bmesh.new()
    for (jx, jz) in ((2.15, -0.85), (-2.35, -0.70)):
        base = (jx, -jz, 0.0)
        cl.add_cylinder(jars_bm, (base[0], base[1], 0.02), (base[0], base[1], 0.34),
                        0.24, 0.20, segments=14, mat_index=0)
        cl.add_cylinder(jars_bm, (base[0], base[1], 0.34), (base[0], base[1], 0.40),
                        0.13, 0.16, segments=14, mat_index=0)
        cl.add_cylinder(jars_bm, (base[0], base[1], 0.40), (base[0], base[1], 0.44),
                        0.19, 0.18, segments=14, mat_index=0)
    jars = cl.finish_mesh("MAP001_accent_jars", jars_bm, [teal], collection)
    for obj in (jars,):
        obj["asset_id"] = "SCENERY"
        obj["role"] = "glazed jars: cool accent near the ring planter"

    flags_bm = bmesh.new()
    string_bm = bmesh.new()
    def bunting(x0, y0, x1, y1, z, sag, step=0.42):
        import math as _m
        n = max(2, int(_m.hypot(x1 - x0, y1 - y0) / step))
        pts = []
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            zz = z - sag * 4.0 * t * (1.0 - t)
            pts.append((x, y, zz))
        cl.add_smooth_tube(string_bm, pts, [0.008] * len(pts), segments=5, mat_index=0)
        for i in range(1, n):
            (sx, sy, sz), (ex, ey, ez) = pts[i - 1], pts[i]
            mx, my, mz = (sx + ex) / 2.0, (sy + ey) / 2.0, (sz + ez) / 2.0
            mat = (i * 7) % 3
            for side in (1.0, -1.0):
                yoff = 0.0
                v0 = flags_bm.verts.new((mx - 0.14, my + yoff, mz))
                v1 = flags_bm.verts.new((mx + 0.14, my + yoff, mz))
                v2 = flags_bm.verts.new((mx, my + yoff, mz - 0.26))
                if side < 0:
                    f = flags_bm.faces.new((v0, v2, v1))
                else:
                    f = flags_bm.faces.new((v0, v1, v2))
                f.material_index = mat
    bunting(-7.0, -8.4, 7.0, -8.4, 2.35, 0.35)
    bunting(-8.5, -3.2, -8.5, 3.8, 2.15, 0.30)
    flags = cl.finish_mesh("MAP001_accent_bunting", flags_bm,
                           [flag_teal, flag_orange, flag_cream], collection)
    strings = cl.finish_mesh("MAP001_accent_bunting_string", string_bm,
                             [cl.mat_metal_brass()], collection)
    for obj in (flags, strings):
        obj["asset_id"] = "SCENERY"
        obj["role"] = "bunting lines: teal/orange/cream accents"


def add_foreground_details(collection):
    """Low native planting beds and leaf drifts that break the empty paving
    without changing the playable route or the camera."""
    rng = random.Random(20261025 + 3)
    stone, light, dark = cl.mat_stone_base(), cl.mat_stone_light(), cl.mat_stone_dark()
    soil_mat = cl.mat_soil()
    leaf_mats = [cl.mat_leaf_ochre(), cl.mat_leaf_amber(),
                 cl.mat_leaf_olive(), cl.mat_leaf_deep()]
    beds = ((-4.6, -5.8, 3.2, 1.35), (4.6, -5.8, 3.2, 1.35))
    for bi, (bx, bz, bw, bd) in enumerate(beds):
        border = bmesh.new()
        cl.add_box(border, (0, 0, 0.05), (bw, bd, 0.10), mat_index=2)
        cl.add_box(border, (0, 0, 0.14), (bw - 0.18, bd - 0.18, 0.10), mat_index=0)
        for sx in (-1, 1):
            cl.add_box(border, (sx * (bw / 2 - 0.08), 0, 0.17),
                       (0.16, bd, 0.14), mat_index=0 if sx < 0 else 2)
        for sz in (-1, 1):
            cl.add_box(border, (0, sz * (bd / 2 - 0.08), 0.17),
                       (bw, 0.16, 0.14), mat_index=0 if sz > 0 else 2)
        border_obj = cl.finish_mesh("MAP001_fg_bed_%d_stone" % bi, border,
                                    [stone, light, dark], collection)
        cl.add_bevel(border_obj, width=0.008, segments=2)
        border_obj.location = (bx, -bz, 0)
        border_obj["asset_id"] = "SCENERY"
        soil = bmesh.new()
        cl.add_box(soil, (0, 0, 0.12), (bw - 0.30, bd - 0.30, 0.10), mat_index=0)
        soil_obj = cl.finish_mesh("MAP001_fg_bed_%d_soil" % bi, soil, [soil_mat],
                                  collection)
        soil_obj.location = (bx, -bz, 0)
        soil_obj["asset_id"] = "SCENERY"
        leaves = bmesh.new()
        for cx, cz, cr in ((-0.55, 0.0, 0.42), (0.50, 0.05, 0.38),
                           (0.0, -0.25, 0.34)):
            for (dx, dz, dz2, lf) in ((0.0, 0.0, 0.0, 0.16),
                                      (-0.18, 0.12, 0.14, 0.13),
                                      (0.20, -0.10, 0.10, 0.12)):
                cl.add_leaf_cluster(leaves, (cx + dx, cz + dz, 0.205 + dz2 * 0.4),
                                    cr * 0.75, 30, rng, [1, 1, 2, 3, 0],
                                    leaf_size=lf * 0.85, flatten=0.25,
                                    shell_inner=0.10, z_min=-0.45)
        leaf_obj = cl.finish_mesh("MAP001_fg_bed_%d_leaves" % bi, leaves,
                                  leaf_mats, collection)
        leaf_obj.location = (bx, -bz, 0)
        leaf_obj["asset_id"] = "SCENERY"
        bed_grass = bmesh.new()
        for _ in range(45):
            gx = rng.uniform(-bw / 2 + 0.24, bw / 2 - 0.24)
            gz = rng.uniform(-bd / 2 + 0.20, bd / 2 - 0.20)
            _add_turf_patch(bed_grass, (gx, gz, 0.205), rng,
                            rng.uniform(0.20, 0.34), [0, 0, 1, 2, 3],
                            rng.randint(5, 7), rng.uniform(0.42, 0.60),
                            rng.uniform(0.050, 0.064), container="fg_bed")
        bed_grass_obj = cl.finish_mesh("MAP001_fg_bed_%d_grass" % bi, bed_grass,
                                       [cl.mat_grass_dry(), cl.mat_grass_pale(),
                                        cl.mat_leaf_olive(), cl.mat_leaf_deep()],
                                       collection)
        bed_grass_obj.location = (bx, -bz, 0)
        bed_grass_obj["asset_id"] = "SCENERY"
        bed_flowers = bmesh.new()
        for _ in range(16):
            fx = rng.uniform(-bw / 2 + 0.26, bw / 2 - 0.26)
            fz = rng.uniform(-bd / 2 + 0.22, bd / 2 - 0.22)
            _add_flower(bed_flowers, (fx, fz, 0.36 + rng.uniform(0.0, 0.16)),
                        rng, rng.uniform(0.050, 0.075),
                        petal_index=0 if rng.random() < 0.65 else 1,
                        core_index=2, stem_length=0.16)
        bed_flowers_obj = cl.finish_mesh(
            "MAP001_fg_bed_%d_flowers" % bi, bed_flowers,
            [cl.mat_flower_rose(), cl.mat_flower_cream(), cl.mat_leaf_gold(),
             cl.mat_leaf_olive()], collection)
        bed_flowers_obj.location = (bx, -bz, 0)
        bed_flowers_obj["asset_id"] = "SCENERY"

    # Leaf drifts along the south path edge, one merged draw.
    drift = bmesh.new()
    for (dx, dz, count, radius) in ((-5.8, -7.4, 90, 0.7), (5.8, -7.4, 90, 0.7),
                                     (-2.8, -8.2, 58, 0.45), (2.8, -8.2, 58, 0.45),
                                     (-11.5, -6.2, 38, 0.4), (11.5, -6.2, 38, 0.4),
                                     (-1.9, 2.3, 42, 0.52), (1.7, 2.5, 42, 0.52),
                                     (0.2, -2.1, 34, 0.48), (-2.7, -1.2, 28, 0.42),
                                     (2.9, -1.0, 28, 0.42), (-6.2, 3.9, 24, 0.38),
                                     (6.2, 3.9, 24, 0.38)):
        cl.add_leaf_cluster(drift, (dx, dz, 0.045), radius, count, rng,
                            [0, 0, 1, 2, 3], leaf_size=0.15, flatten=0.09,
                            shell_inner=0.05, z_min=-0.40)
    drift_obj = cl.finish_mesh("MAP001_fg_leaf_drift", drift, leaf_mats, collection)
    drift_obj["asset_id"] = "SCENERY"
    drift_obj["role"] = "foreground leaf drift on paving edge"


def add_garden_ground(collection, plants_collection, proxy_collection):
    """Stone-edged planting beds, grass/leaf ground cover and small flowers.

    The beds replace the bare dark-soil margins that dominated the formal
    camera; all cover is native blade/petal geometry merged into a few draws.
    """
    rng = random.Random(20261025 + 11)
    stone, light, dark, soil = (cl.mat_stone_base(), cl.mat_stone_light(),
                                cl.mat_stone_dark(), cl.mat_soil())
    beds = [(-11.2, -5.2, 2.6, 4.2), (11.4, 0.7, 2.6, 3.0),
            (-10.9, -8.3, 3.6, 1.6), (10.9, -8.3, 3.6, 1.6)]
    border_bm = bmesh.new()
    soil_bm = bmesh.new()
    for (bx, bz, bw, bd) in beds:
        by = -bz
        cl.add_box(border_bm, (bx, by, 0.055), (bw, bd, 0.11), mat_index=2)
        cl.add_box(border_bm, (bx, by, 0.155), (bw - 0.22, bd - 0.22, 0.09),
                   mat_index=0)
        # Cap course: four runs with staggered short blocks.
        for sx in (-1, 1):
            for i in range(int(bd / 0.42)):
                zz = by - bd / 2 + 0.21 + i * 0.42
                cl.add_box(border_bm, (bx + sx * (bw / 2 - 0.075), zz, 0.235),
                           (0.20, 0.39, 0.075),
                           mat_index=0 if (i + sx) % 2 == 0 else 2)
        for sz in (-1, 1):
            for i in range(int(bw / 0.42)):
                xx = bx - bw / 2 + 0.21 + i * 0.42
                cl.add_box(border_bm, (xx, by + sz * (bd / 2 - 0.075), 0.235),
                           (0.39, 0.20, 0.075),
                           mat_index=0 if (i + sz) % 2 == 0 else 2)
        cl.add_box(soil_bm, (bx, by, 0.165), (bw - 0.30, bd - 0.30, 0.17),
                   mat_index=0)
        add_proxy_box(proxy_collection, "COL_bed_%d" % len(STATE["proxies"]),
                      bx, bz, bw, bd, 0, 0.30)
    border = cl.finish_mesh("MAP001_garden_beds_stone", border_bm,
                            [stone, light, dark], collection)
    cl.add_bevel(border, width=0.007, segments=2)
    border["asset_id"] = "SCENERY"
    bed_soil = cl.finish_mesh("MAP001_garden_beds_soil", soil_bm, [soil],
                              collection)
    bed_soil["asset_id"] = "SCENERY"

    # Grass cover: dense overlapping turf patches rather than lone tall tufts.
    grass_bm = bmesh.new()
    grass_mats = [cl.mat_grass_dry(), cl.mat_grass_pale()]
    turf_mats = [0, 0, 1, 1, 0, 1]
    areas = [(-12.2, 0.0, 1.8, 9.2, 150), (12.2, 0.0, 1.8, 9.2, 150),
             (-9.1, -4.6, 1.1, 3.4, 60), (9.1, -4.6, 1.1, 3.4, 60),
             (-9.1, 4.6, 1.1, 3.4, 60), (9.1, 4.6, 1.1, 3.4, 60),
             (-6.5, -8.9, 7.0, 0.8, 80), (6.5, -8.9, 7.0, 0.8, 80),
             (-6.5, 8.9, 7.0, 0.8, 80), (6.5, 8.9, 7.0, 0.8, 80),
             (-2.9, -5.8, 1.4, 1.2, 40), (2.9, -5.8, 1.4, 1.2, 40),
             (-8.6, -4.9, 1.0, 1.0, 30), (8.6, -4.9, 1.0, 1.0, 30)]
    for (ax, az, rx, rz, count) in areas:
        target = _gs(count, N5_GRASS_AREAS)
        placed = 0
        tries = 0
        while placed < target and tries < target * 4:
            tries += 1
            u = rng.uniform(-1, 1)
            v = rng.uniform(-1, 1)
            if u * u + v * v > 1.0:
                continue
            bx = ax + u * rx
            bz = az + v * rz
            # Keep the whole patch (centre + its spread) off the flagstones;
            # per-tuft testing inside the patch would otherwise cull most of it.
            if on_paving(bx, bz, margin=0.38):
                continue
            placed += 1
            _add_turf_patch(grass_bm, (bx, -bz, 0.012), rng,
                            rng.uniform(0.28, 0.50), turf_mats,
                            rng.randint(4, 6), rng.uniform(0.17, 0.29),
                            rng.uniform(0.042, 0.056),
                            blocked=on_paving, container="open_ground")
    for (bx, bz, bw, bd) in beds:
        by = -bz
        if on_paving(bx, bz):
            continue
        for _ in range(_gs(45, N5_GRASS_BEDS)):
            gx = bx + rng.uniform(-bw / 2 + 0.30, bw / 2 - 0.30)
            gz = by + rng.uniform(-bd / 2 + 0.30, bd / 2 - 0.30)
            _add_turf_patch(grass_bm, (gx, gz, 0.24), rng,
                            rng.uniform(0.22, 0.40), [0, 0, 1, 2, 3],
                            rng.randint(4, 6), rng.uniform(0.24, 0.42),
                            rng.uniform(0.042, 0.056),
                            blocked=on_paving, container="bed")
    # Ring-planter soil: P1's planters overflow, so fill the whole disc with a
    # golden sward instead of a few sparse tufts around the trunk.
    for _ in range(_gs(190, N5_GRASS_RING)):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.30, 1.62)
        _add_turf_patch(grass_bm, (r * math.cos(a), r * math.sin(a), 0.625),
                        rng, rng.uniform(0.16, 0.30), [1, 0, 1, 0, 2],
                        rng.randint(4, 6), rng.uniform(0.26, 0.46),
                        rng.uniform(0.042, 0.056),
                        keep=(N5_GRASS_RING_BLADE_KEEP or None),
                        container="ring_planter")
    # Side planters read as empty boxes at the formal camera; give them the same
    # overflowing sward as the ring planter, in each planter's local frame.
    side_planters = ((-11.8, -4.6, 0.0), (11.8, 4.8, math.radians(90)))
    for (px, py, prot) in side_planters:
        ca, sa = math.cos(prot), math.sin(prot)
        for _ in range(_gs(58, N5_GRASS_SIDES)):
            lx = rng.uniform(-1.36, 1.36)
            ly = rng.uniform(-0.52, 0.52)
            wx = px + lx * ca - ly * sa
            wy = py + lx * sa + ly * ca
            _add_turf_patch(grass_bm, (wx, wy, 0.42), rng,
                            rng.uniform(0.16, 0.28), [1, 0, 1, 2, 3],
                            rng.randint(4, 6), rng.uniform(0.24, 0.44),
                            rng.uniform(0.042, 0.056),
                            container="side_planter")
    # Moss/leaf edges along paving modules and bed feet.
    moss_bm = bmesh.new()
    moss_mats = [cl.mat_leaf_olive(), cl.mat_leaf_deep(),
                 cl.mat_leaf_amber()]
    for (mx, mz, mr) in ((-8.35, -7.9, 1.0), (8.35, -7.9, 1.0),
                         (-8.35, 7.9, 1.0), (8.35, 7.9, 1.0),
                         (-6.9, -6.9, 0.8), (6.9, -6.9, 0.8),
                         (-6.9, 6.9, 0.8), (6.9, 6.9, 0.8)):
        cl.add_leaf_cluster(moss_bm, (mx, -mz, 0.020), mr, 34, rng,
                            [0, 0, 1, 2], leaf_size=0.085, flatten=0.12,
                            shell_inner=0.05, z_min=-0.30)
    for _ in range(150):
        side = -1 if rng.random() < 0.5 else 1
        mx = side * rng.uniform(8.8, 13.2)
        mz = rng.uniform(-8.8, 8.8)
        if rng.random() < 0.3:
            mx = rng.uniform(-8.0, 8.0)
            mz = (1 if rng.random() < 0.5 else -1) * rng.uniform(8.6, 9.6)
        cl.add_leaf_cluster(moss_bm, (mx, -mz, 0.016), rng.uniform(0.34, 0.66),
                            rng.randint(14, 26), rng, [0, 0, 1, 2, 3],
                            leaf_size=rng.uniform(0.06, 0.10), flatten=0.10,
                            shell_inner=0.05, z_min=-0.25)
    # Leaf mulch inside the stone beds hides bare soil between plant clumps.
    for (bx, bz, bw, bd) in beds:
        by = -bz
        for _ in range(22):
            lx = bx + rng.uniform(-bw / 2 + 0.28, bw / 2 - 0.28)
            lz = by + rng.uniform(-bd / 2 + 0.24, bd / 2 - 0.24)
            cl.add_leaf_cluster(moss_bm, (lx, lz, 0.265), 0.26, 8, rng,
                                [0, 1, 2, 3], leaf_size=rng.uniform(0.08, 0.12),
                                flatten=0.12, shell_inner=0.05, z_min=-0.25)
    # Ivy pads on the central ring wall and spilling over the cap.
    for i in range(34):
        a = math.tau * i / 34.0 + rng.uniform(-0.08, 0.08)
        cl.add_leaf_cluster(moss_bm, (2.045 * math.cos(a), 2.045 * math.sin(a),
                                      rng.uniform(0.28, 0.62)), 0.24, 8, rng,
                            [0, 1, 2], leaf_size=0.095, flatten=0.55,
                            shell_inner=0.20, z_min=-0.40)
    for i in range(16):
        a = math.tau * i / 16.0 + rng.uniform(-0.12, 0.12)
        cl.add_leaf_cluster(moss_bm, (1.96 * math.cos(a), 1.96 * math.sin(a),
                                      0.66), 0.32, 12, rng, [0, 2, 1],
                            leaf_size=0.105, flatten=0.38, shell_inner=0.18,
                            z_min=-0.25)
    moss = cl.finish_mesh("MAP001_garden_moss", moss_bm, moss_mats, collection)
    moss["asset_id"] = "SCENERY"

    # Flowers: rose and cream petals with a brass core, concentrated in beds.
    flower_bm = bmesh.new()
    petal_mats = [cl.mat_flower_rose(), cl.mat_flower_cream(),
                  cl.mat_leaf_gold(), cl.mat_leaf_olive()]
    for (bx, bz, bw, bd) in beds:
        by = -bz
        for _ in range(28):
            fx = bx + rng.uniform(-bw / 2 + 0.32, bw / 2 - 0.32)
            fz = by + rng.uniform(-bd / 2 + 0.32, bd / 2 - 0.32)
            _add_flower(flower_bm, (fx, fz, 0.42 + rng.uniform(0.0, 0.18)),
                        rng, rng.uniform(0.055, 0.085),
                        petal_index=0 if rng.random() < 0.62 else 1,
                        core_index=2)
    for _ in range(26):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.55, 1.35)
        _add_flower(flower_bm, (r * math.cos(a), r * math.sin(a),
                                0.72 + rng.uniform(0.0, 0.12)),
                    rng, rng.uniform(0.045, 0.070),
                    petal_index=0 if rng.random() < 0.5 else 1, core_index=2)
    for (px, py, prot) in ((-11.8, -4.6, 0.0), (11.8, 4.8, math.radians(90))):
        ca, sa = math.cos(prot), math.sin(prot)
        for _ in range(10):
            lx = rng.uniform(-1.20, 1.20)
            ly = rng.uniform(-0.44, 0.44)
            _add_flower(flower_bm,
                        (px + lx * ca - ly * sa, py + lx * sa + ly * ca,
                         0.56 + rng.uniform(0.0, 0.16)),
                        rng, rng.uniform(0.050, 0.078),
                        petal_index=0 if rng.random() < 0.55 else 1,
                        core_index=2)
    flowers = cl.finish_mesh("MAP001_garden_flowers", flower_bm, petal_mats,
                             collection)
    flowers["asset_id"] = "SCENERY"

    # A few low pebbles at path edges.
    pebble_bm = bmesh.new()
    for _ in range(46):
        px = rng.uniform(-13.2, 13.2)
        pz = rng.uniform(-9.2, 9.2)
        if abs(px) < 8.6 and abs(pz) < 8.6:
            continue
        cl.add_mass_lobe(pebble_bm, (px, -pz, 0.03),
                         rng.uniform(0.045, 0.095), rng, flatten=0.45,
                         subdiv=1, displace=0.22, mat_index=rng.randint(0, 2))
    pebbles = cl.finish_mesh("MAP001_garden_pebbles", pebble_bm,
                            [stone, dark, light], collection)
    pebbles["asset_id"] = "SCENERY"

    # Decorative cobble course around the central planter.
    ring_bm = bmesh.new()
    for i in range(86):
        a = math.tau * i / 86.0 + rng.uniform(-0.012, 0.012)
        r = 2.42 + (i % 3) * 0.055 + rng.uniform(-0.018, 0.018)
        cl.add_mass_lobe(ring_bm, (r * math.cos(a), r * math.sin(a), 0.025),
                         rng.uniform(0.065, 0.105), rng, flatten=0.32,
                         subdiv=1, displace=0.18, mat_index=rng.randint(0, 2))
    ring_cobbles = cl.finish_mesh("MAP001_garden_ring_cobbles", ring_bm,
                                  [stone, dark, light], collection)
    cl.add_bevel(ring_cobbles, width=0.004, segments=1)
    ring_cobbles["asset_id"] = "SCENERY"

    grass = cl.finish_mesh("MAP001_garden_grass", grass_bm, grass_mats,
                           collection)
    grass["asset_id"] = "SCENERY"

    # Bed shrubs use the catalog assets so their silhouettes and density stay
    # consistent with the standalone module sources.
    bed_shrubs = [("ENV010", -11.9, -4.4, 15.0, 0.78),
                  ("ENV009", -10.5, -6.3, 120.0, 0.72),
                  ("ENV009", 11.7, 0.0, 200.0, 0.80),
                  ("ENV009", -11.4, -8.3, 70.0, 0.72),
                  ("ENV010", 11.4, -8.3, 160.0, 0.74),
                  ("ENV009", -10.3, -8.4, 35.0, 0.64),
                  ("ENV010", 10.3, -8.2, 145.0, 0.66),
                  ("ENV009", 11.0, 1.4, 80.0, 0.70)]
    for i, (asset, x, z, rot, scale) in enumerate(bed_shrubs):
        builder = env.create_shrub_a if asset == "ENV009" else env.create_shrub_b
        objs = builder(plants_collection, (x, -z, 0.24), rot,
                       "MAP001_bedshrub_%02d" % i)
        for o in objs:
            o.scale = (scale, scale, scale)
        record(asset, "bed_shrub_%02d" % i, x, z, rot, y=0.24, scale=scale,
               collider={"type": "none"},
               source="art/candidates/candidate_n5/source/plants/%s.blend" % (
                   "ENV009_shrub_a" if asset == "ENV009" else "ENV010_shrub_b"),
               objects=objs, note="inside a stone-edged bed; bed proxy blocks")

    STATE.setdefault("scenery", []).append({
        "kind": "garden_ground",
        "beds": [{"center": [b[0], b[1]], "size": [b[2], b[3]]}
                 for b in beds],
        "objects": ["MAP001_garden_beds_stone", "MAP001_garden_beds_soil",
                    "MAP001_garden_grass", "MAP001_garden_flowers",
                    "MAP001_garden_moss", "MAP001_garden_pebbles"],
        "note": "native blades/petals; merged into few draws; bed proxies block",
    })


def append_bench(collection, x, z, rot):
    path = os.path.join(cl.SRC_PROP, "PROP001_bench.blend")
    names = ["PROP001_bench", "PROP001_bench_wood", "PROP001_bench_metal"]
    with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
        data_to.objects = [n for n in names if n in data_from.objects]
    root = None
    meshes = []
    for obj in data_to.objects:
        if obj is None:
            continue
        collection.objects.link(obj)
        if obj.name == "PROP001_bench":
            root = obj
        elif obj.type == "MESH":
            meshes.append(obj)
    if root is None or not meshes:
        raise RuntimeError("PROP001 bench append failed")
    root.location = (x, -z, 0.0)
    root.rotation_euler = (0, 0, math.radians(rot))
    bpy.context.view_layer.update()
    for obj in meshes:
        mw = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = mw
        obj["asset_id"] = "PROP001"
        obj["appended_from"] = "art/candidates/candidate_n3/source/props/PROP001_bench.blend"
        for slot in obj.material_slots:
            if slot.material:
                base = slot.material.name.split(".")[0]
                canon = bpy.data.materials.get(base)
                if canon is not None:
                    slot.material = canon
    root["asset_id"] = "PROP001"
    bpy.data.objects.remove(root, do_unlink=True)
    for name, (hex_color, roughness, metallic) in {
            "MAT_bench_wood": ("#887158", 0.55, 0.0),
            "MAT_bench_metal": ("#494744", 0.36, 0.85)}.items():
        mat = bpy.data.materials.get(name)
        if mat is not None:
            mat["engine_base_color"] = list(cl.hex_to_linear_rgba(hex_color))
            mat["engine_roughness"] = roughness
            mat["engine_metallic"] = metallic
            mat["source_hex"] = hex_color
    return meshes


# ---------------------------------------------------------------------------
# Clearance validation
# ---------------------------------------------------------------------------

def _dist_point_box(px, pz, collider):
    cx, cz = collider["center"]
    ang = math.radians(-collider.get("rotation_y", 0.0))
    dx, dz = px - cx, pz - cz
    lx = dx * math.cos(ang) - dz * math.sin(ang)
    lz = dx * math.sin(ang) + dz * math.cos(ang)
    hw, hd = collider["size"][0] / 2.0, collider["size"][1] / 2.0
    qx = max(abs(lx) - hw, 0.0)
    qz = max(abs(lz) - hd, 0.0)
    return math.hypot(qx, qz)


def _dist_point_collider(px, pz, collider):
    if collider["type"] == "circle":
        cx, cz = collider["center"]
        return max(0.0, math.hypot(px - cx, pz - cz) - collider["radius"])
    if collider["type"] == "box":
        return _dist_point_box(px, pz, collider)
    return 1e9


def clearance_report(points):
    colliders = []
    for i in STATE["instances"]:
        c = i["collider"]
        if c["type"] in ("box", "circle"):
            colliders.append(c)
        elif c["type"] == "compound":
            colliders.extend(c.get("shapes", []))
    results = []
    for name, px, pz, required in points:
        best = min((_dist_point_collider(px, pz, c) for c in colliders),
                   default=1e9)
        inside = any(
            c["type"] == "circle"
            and math.hypot(px - c["center"][0], pz - c["center"][1])
            < c["radius"]
            for c in colliders
        ) or any(
            c["type"] == "box"
            and _dist_point_box(px, pz, c) <= 0.0
            for c in colliders
        )
        results.append({
            "point": name, "nearest_surface_m": round(best, 3),
            "required_m": required, "pass": (best >= required and not inside),
            "inside_collider": inside,
        })
        print("CLEARANCE %s nearest=%.3f required=%.2f inside=%s %s" % (
            name, best, required, inside, "PASS" if best >= required and not inside
            else "FAIL"))
    return results


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build():
    cl.reset_scene()
    scene = bpy.context.scene
    c_ground = cl.new_collection("MAP_ground")
    c_pave = cl.new_collection("MAP_paving")
    c_env = cl.new_collection("MAP_environment")
    c_props = cl.new_collection("MAP_props")
    c_plants = cl.new_collection("MAP_plants")
    c_edge = cl.new_collection("MAP_edge_closure")
    c_col = cl.new_collection("MAP_collision_proxies")
    c_light = cl.new_collection("MAP_lighting")

    # Ground / skirt.
    add_ground(c_ground)
    STATE["ground"] = {
        "courtyard": {"size": [28.0, 20.0], "top_y": SOIL_TOP,
                      "material": "MAT_ground_soil"},
        "skirt": {"size": [40.0, 32.0], "top_y": -0.13,
                  "note": "visual edge skirt outside the playable 28x20 area"},
    }
    add_background_scenery(c_env)
    add_foreground_details(c_env)
    add_accents(c_env)
    add_garden_ground(c_env, c_plants, c_col)

    # Paving modules (same 4x4 layout as ENV001, map LOD bevel).
    # n4 review: "regular paving tiles dominate the frame" — one bond pattern with
    # constant joints over the whole courtyard. Three languages instead: the 3x3
    # central square gets large hand-cut flags, the two axis modules get a narrow
    # running bond that reads as a path, and the five outer modules get cobbles.
    paving_centers = PAVING_CENTERS
    core = {(-4, -4), (0, -4), (4, -4), (-4, 0), (0, 0), (4, 0),
            (-4, 4), (0, 4), (4, 4)}
    path = {(0, -8), (0, 8)}
    paving_styles = ['plaza' if (x, z) in core else 'path' if (x, z) in path
                     else 'edge' for (x, z) in paving_centers]
    paving_objs = env001_layout.create_paving(
        c_pave, [(x, -z) for (x, z) in paving_centers], z_top=0.0,
        prefix="MAP001_paving", bevel_segments=0, lod=True,
        styles=paving_styles)
    paving_obj = paving_objs[0]
    for i, (x, z) in enumerate(paving_centers):
        record("ENV001", "paving_%02d" % i, x, z, 0.0, 0.0,
               collider={"type": "none"},
               source="art/full/source/environment/ENV001_stone_paving.blend",
               note="map LOD: %s bond, top at y=0" % paving_styles[i],
               merged_object=paving_obj.name,
               lod="bevel_segments=0")

    # Curbs (2.0 m modules; low kerbs are non-blocking).
    curb_placements = []
    for z in (-9, -7):
        curb_placements += [(-2, z, 90), (2, z, 90)]
    for z in (7, 9):
        curb_placements += [(-2, z, 90), (2, z, 90)]
    for x in (-5, -3, 3, 5):
        curb_placements += [(x, -6, 0), (x, 6, 0)]
    for z in (-5, -3, -1, 1):
        curb_placements.append((6, z, 90))
    for z in (-5, -3, -1, 1, 3, 5):
        curb_placements.append((-10, z, 90))
    for x in (-9, -7):
        curb_placements.append((x, -6, 0))
    curb_placements += [(10, 3, 90)]
    for x in (7, 9):
        curb_placements += [(x, 2, 0), (x, 6, 0)]
    curb_placements += [(10, 7, 90)]
    for x in (11, 13):
        curb_placements += [(x, 4, 0), (x, 8, 0)]

    curb_objs = []
    for i, (x, z, rot) in enumerate(curb_placements):
        objs = env.create_curb(c_edge, (x, -z, 0.0), rot, "MAP001_curb_%02d" % i,
                               lod=True)
        curb_objs += objs
        record("ENV002", "curb_%02d" % i, x, z, rot, collider={"type": "none"},
               source="art/full/source/environment/ENV002_curb.blend",
               note="map LOD; 0.18 m kerb, non-blocking", lod="1-seg bevel")
    curb_merged = join_meshes(curb_objs, "MAP001_curbs", c_edge)
    for inst in STATE["instances"]:
        if inst["asset_id"] == "ENV002":
            inst["merged_object"] = curb_merged.name

    # Edge closure: low wall north, railing east/west/south.
    wall_objs = []
    for i, x in enumerate((-12, -8, -4, 0, 4, 8, 12)):
        objs = env.create_low_wall(c_edge, (x, -9.7, 0), 0.0,
                                   "MAP001_low_wall_%02d" % i, lod=True)
        wall_objs += objs
        record("ENV003", "low_wall_%02d" % i, x, 9.7, 0.0,
               collider=box_collider(x, 9.7, 4.0, 0.5, 0.0, 0.79),
               source="art/full/source/environment/ENV003_low_wall.blend",
               note="north edge closure; map LOD", lod="1-seg bevel")
    wall_merged = join_meshes(wall_objs, "MAP001_north_wall", c_edge)
    for inst in STATE["instances"]:
        if inst["asset_id"] == "ENV003":
            inst["merged_object"] = wall_merged.name

    rail_objs = []
    rail_index = 0
    rail_specs = []
    # The near rail sits at -8.8 so it enters the bottom of the game frame and
    # gives the paving the foreground occlusion the reference has.
    for x in range(-13, 14, 2):
        # Open a 4 m gate for the foreground stair at x=8.0.
        if x in (7, 9):
            continue
        rail_specs.append((x, -8.8, 0.0))
    for z in range(-9, 10, 2):
        rail_specs.append((13.9, z, 90.0))
        rail_specs.append((-13.9, z, 90.0))
    for (x, z, rot) in rail_specs:
        objs = env.create_railing(c_edge, (x, -z, 0), rot,
                                  "MAP001_railing_%02d" % rail_index, lod=True)
        rail_objs += objs
        record("ENV004", "railing_%02d" % rail_index, x, z, rot,
               collider=box_collider(x, z, 2.0, 0.10, rot, 1.12),
               source="art/full/source/environment/ENV004_railing.blend",
               note="map LOD: 5 balusters, 1-seg bevel", lod="5 balusters")
        rail_index += 1
    rail_merged = join_meshes(rail_objs, "MAP001_railings", c_edge)
    for inst in STATE["instances"]:
        if inst["asset_id"] == "ENV004":
            inst["merged_object"] = rail_merged.name

    # Decorative foreground steps (landscape only, blocked). Keep them left of
    # the traversal lane and inside the formal camera's lower frame.
    step_objs = env.create_steps(c_edge, (-2.0, 6.8, 0), 180.0,
                                 "MAP001_steps", lod=True)
    record("ENV005", "edge_steps", -2.0, -6.8, 180.0,
           collider=box_collider(-2.0, -6.8, 2.7, 1.4, 180.0, 0.49),
           source="art/full/source/environment/ENV005_steps.blend",
           note="landscape foreground left of traversal lane; no climbing",
           objects=step_objs)

    # Central ring planter + hero tree.
    planter_objs = env.create_ring_planter(c_env, (0, 0, 0), 0.0,
                                           "MAP001_ring_planter")
    record("ENV007", "ring_planter", 0, 0, 0.0,
           collider=circle_collider(0, 0, 2.08, 0.63),
           source="art/full/source/environment/ENV007_ring_planter.blend",
           objects=planter_objs, note="walkway outside r=2.08")
    add_proxy_circle(c_col, "COL_ring_planter", 0, 0, 2.08, 0.63)

    tree_objs = env.create_tree(c_env, (0, 0, 0.55), 0.0, "MAP001_tree")
    canopy = [o for o in tree_objs if o.name.endswith("_canopy")][0]
    occ_objs = [o.name for o in tree_objs
                if o.name.endswith("_canopy") or o.name.endswith("_crown_mass")]
    record("ENV006", "hero_tree", 0, 0, 0.0, y=0.55,
           collider=circle_collider(0, 0, 0.36, 1.4),
           occlusion_group="OCC_tree_main",
           source="art/full/source/environment/ENV006_autumn_tree.blend",
           objects=tree_objs,
           note="tree base sits just below planter soil top y=0.615; y=0.55; "
                "canopy object " + canopy.name + " + solid crown mass")
    STATE["occlusion"].append({
        "id": "OCC_tree_main",
        "objects": occ_objs,
        "rule": "hide canopy + crown mass when the player silhouette is behind it "
                "relative to the fixed camera; restore on exit",
        "note": "runtime occlusion is not implemented or engine-tested yet",
    })

    # Side planters + shrubs inside them.
    sp_objs = env.create_side_planter(c_env, (-11.8, -4.6, 0), 0.0,
                                      "MAP001_west_planter")
    record("ENV008", "west_planter", -11.8, 4.6, 0.0,
           collider=box_collider(-11.8, 4.6, 3.28, 1.48, 0.0, 0.48),
           source="art/full/source/environment/ENV008_side_planter.blend",
           objects=sp_objs)
    add_proxy_box(c_col, "COL_west_planter", -11.8, 4.6, 3.28, 1.48, 0.0, 0.48)

    sp2_objs = env.create_side_planter(c_env, (11.8, 4.8, 0), 90.0,
                                       "MAP001_east_planter")
    record("ENV008", "east_planter", 11.8, -4.8, 90.0,
           collider=box_collider(11.8, -4.8, 3.28, 1.48, 90.0, 0.48),
           source="art/full/source/environment/ENV008_side_planter.blend",
           objects=sp2_objs)
    add_proxy_box(c_col, "COL_east_planter", 11.8, -4.8, 3.28, 1.48, 90.0, 0.48)

    # Existing bench source, appended and placed.
    bench_objs = append_bench(c_props, -9.3, -4.4, 90.0)
    record("PROP001", "bench_A", -9.3, -4.4, 90.0,
           collider=box_collider(-9.3, -4.4, 1.7, 0.70, 90.0, 0.88),
           source="art/full/source/props/PROP001_bench.blend",
           objects=bench_objs, note="appended from existing PROP001 source")
    add_proxy_box(c_col, "COL_bench_A", -9.3, -4.4, 1.7, 0.70, 90.0, 0.88)
    bench_b = append_bench(c_props, -6.4, -5.0, 0.0)
    record("PROP001", "bench_B", -6.4, -5.0, 0.0,
           collider=box_collider(-6.4, -5.0, 1.7, 0.70, 0.0, 0.88),
           source="art/candidates/candidate_n3/source/props/PROP001_bench.blend",
           objects=bench_b, note="foreground bench, N01 depth")
    add_proxy_box(c_col, "COL_bench_B", -6.4, -5.0, 1.7, 0.70, 0.0, 0.88)
    bench_c = append_bench(c_props, 6.4, -5.0, 180.0)
    record("PROP001", "bench_C", 6.4, -5.0, 180.0,
           collider=box_collider(6.4, -5.0, 1.7, 0.70, 180.0, 0.88),
           source="art/candidates/candidate_n3/source/props/PROP001_bench.blend",
           objects=bench_c, note="foreground bench, N01 depth")
    add_proxy_box(c_col, "COL_bench_C", 6.4, -5.0, 1.7, 0.70, 180.0, 0.88)

    # Message board (engine z=+6.9 -> Blender y=-6.9).
    board_objs = props.create_message_board(c_props, (0, -6.9, 0), 180.0,
                                            "MAP001_message_board")
    board_meshes = [o for o in board_objs if o.type == "MESH"]
    record("PROP003", "message_board", 0, 6.9, 180.0,
           collider=box_collider(0, 6.9, 2.50, 0.32, 180.0, 1.98),
           interaction_id="board_submit",
           source="art/full/source/props/PROP003_message_board.blend",
           objects=board_objs)
    add_proxy_box(c_col, "COL_message_board", 0, 6.9, 2.50, 0.32, 180.0, 1.98)
    STATE["interactions"].append({
        "id": "board_submit", "type": "message_board",
        "position": [0, 0.95, 6.74], "interaction_position": [0, 0, 5.9],
        "radius": 1.6, "asset_id": "PROP003",
        "states": "cards A/B/C independently visible; empty and full supported",
    })

    # Pergola (engine z=+6.4 -> Blender y=-6.4).
    pergola_objs = props.create_pergola(c_props, (11.6, -6.4, 0), 0.0,
                                        "MAP001_pergola")
    post_shapes = []
    for (dx, dz) in ((1.45, 1.15), (1.45, -1.15),
                     (-1.45, 1.15), (-1.45, -1.15)):
        px, pz = 11.6 + dx, 6.4 + dz
        post_shapes.append(box_collider(px, pz, 0.22, 0.22, 0.0, 2.6))
    record("PROP002", "pergola", 11.6, 6.4, 0.0,
           collider={"type": "compound", "shapes": post_shapes},
           occlusion_group="OCC_pergola_roof",
           source="art/full/source/props/PROP002_pergola.blend",
           objects=pergola_objs,
           note="roof spans x 9.9-13.3 / z 5.3-7.9; card C at (8,5) is clear; "
                "collision is compound (4 posts)")
    for i, (dx, dz) in enumerate(((1.45, 1.15), (1.45, -1.15),
                                  (-1.45, 1.15), (-1.45, -1.15))):
        px, pz = 11.6 + dx, 6.4 + dz
        add_proxy_box(c_col, "COL_pergola_post_%d" % i, px, pz, 0.22, 0.22,
                      0.0, 2.6)
    roof = [o for o in pergola_objs if o.name.endswith("_roof")][0]
    state_occ = {
        "id": "OCC_pergola_roof",
        "objects": [roof.name],
        "rule": "optional roof hide when the player is behind the beam grid; "
                "not required for card C",
        "note": "runtime occlusion is not implemented or engine-tested yet",
    }
    STATE["occlusion"].append(state_occ)

    # Lamps.
    lamps = [(-6.8, -6.8), (6.8, -6.8), (-6.8, 6.8), (6.8, 6.8)]
    for i, (x, z) in enumerate(lamps):
        objs = props.create_lamp(c_props, (x, -z, 0), 0.0,
                                 "MAP001_lamp_%d" % i)
        record("PROP004", "lamp_%d" % i, x, z, 0.0,
               collider=circle_collider(x, z, 0.30, 2.67),
               source="art/full/source/props/PROP004_lamp.blend", objects=objs)
        add_proxy_circle(c_col, "COL_lamp_%d" % i, x, z, 0.30, 2.67)

    # Direction sign (engine z=-7.5 -> Blender y=+7.5).
    sign_objs = props.create_direction_sign(c_props, (-3.4, 7.5, 0), 180.0,
                                            "MAP001_direction_sign")
    record("PROP005", "direction_sign", -3.4, -7.5, 180.0,
           collider=circle_collider(-3.4, -7.5, 0.28, 2.1),
           source="art/full/source/props/PROP005_direction_sign.blend",
           objects=sign_objs)
    add_proxy_circle(c_col, "COL_direction_sign", -3.4, -7.5, 0.28, 2.1)

    # Pickup postcards at A/B/C, 0.15 above the paving.
    pickups = [("A", -7.0, -3.0), ("B", -8.0, 4.0), ("C", 8.0, 5.0)]
    for (design, x, z) in pickups:
        card = pc.create_postcard(c_props, design, "MAP001_pickup_%s" % design,
                                  scale=1.75, pins=False)
        card.location = (x, -z, 0.15)
        card.rotation_euler = (0, 0, math.radians(180.0))
        record("PROP006", "pickup_%s" % design, x, z, 180.0, y=0.15,
               collider={"type": "none"}, interaction_id="pickup_" + design,
               source="art/full/source/props/PROP006_postcards.blend",
               objects=[card], note="card front faces south; floats at y=0.15")
        STATE["interactions"].append({
            "id": "pickup_" + design, "type": "pickup", "card_design": design,
            "position": [x, 0.15, z], "radius": 1.6, "asset_id": "PROP006",
            "collected_state": "hidden after pickup; shown by board card node",
        })

    STATE["interactions"].append({
        "id": "npc_gardener", "type": "npc", "position": [3.0, 0.0, -5.0],
        "radius": 1.6, "asset_id": None,
        "status": "character asset pending; no stand-in character placed",
    })

    # Shrubs / dry grass / fallen leaves (planting and edge softening).
    shrub_specs = [
        ("ENV009", -12.4, -6.2, 15.0, 0.85), ("ENV010", -12.3, 1.0, -20.0, 1.10),
        ("ENV009", -12.5, 8.4, 40.0, 0.95), ("ENV010", 12.4, 0.2, 160.0, 1.15),
        ("ENV009", 6.4, 9.0, 80.0, 1.00), ("ENV010", -5.8, 9.0, -60.0, 0.90),
        ("ENV009", 12.6, -7.3, 200.0, 1.05), ("ENV010", 4.2, 9.2, 115.0, 0.85),
    ]
    for i, (asset, x, z, rot, scale) in enumerate(shrub_specs):
        builder = env.create_shrub_a if asset == "ENV009" else env.create_shrub_b
        objs = builder(c_plants, (x, -z, 0.0), rot, "MAP001_%s_%02d" % (
            asset.lower(), i))
        if scale != 1.0:
            for o in objs:
                o.scale = (scale, scale, scale)
        radius = (0.46 if asset == "ENV009" else 0.60) * scale
        record(asset, "shrub_%02d" % i, x, z, rot, scale=scale,
               collider=circle_collider(x, z, radius, 1.1 * scale),
               occlusion_group="OCC_shrub_%02d" % i,
               source="art/full/source/plants/%s.blend" % (
                   "ENV009_shrub_a" if asset == "ENV009" else "ENV010_shrub_b"),
               objects=objs)
        add_proxy_circle(c_col, "COL_shrub_%02d" % i, x, z, radius, 1.1 * scale)
        leaves = [o for o in objs if o.name.endswith("_leaves")]
        STATE["occlusion"].append({
            "id": "OCC_shrub_%02d" % i,
            "objects": [o.name for o in leaves],
            "rule": "optional per-shrub hide if it covers the player; not runtime-tested",
        })

    # Layered planter planting: two shrubs + grass tufts + leaf litter per
    # side planter, so the soil bed reads full instead of bare.
    planter_plantings = [
        # west planter (long axis along x): soil x -13.0..-10.6, z 4.07..5.13
        [("ENV009", -12.50, 4.75, 15.0, 0.90), ("ENV010", -11.15, 4.40, -20.0, 0.85),
         ("ENV011", -11.85, 5.00, 30.0, 1.00), ("ENV011", -12.35, 4.20, 80.0, 1.00),
         ("ENV012", -11.80, 4.55, 10.0, 1.00)],
        # east planter (rot 90, long axis along z): soil x 11.21..12.39, z -6.0..-3.6
        [("ENV010", 11.75, -5.50, 100.0, 0.90), ("ENV009", 11.90, -4.10, 65.0, 0.85),
         ("ENV011", 11.45, -4.85, 140.0, 1.00), ("ENV011", 12.15, -5.90, 200.0, 1.00),
         ("ENV012", 11.80, -4.80, 70.0, 1.00)],
    ]
    for pi, planting in enumerate(planter_plantings):
        for si, (asset, x, z, rot, scale) in enumerate(planting):
            y = 0.40
            if asset == "ENV009":
                objs = env.create_shrub_a(c_plants, (x, -z, y), rot,
                                          "MAP001_planter_%02d_shrub_a" % pi)
            elif asset == "ENV010":
                objs = env.create_shrub_b(c_plants, (x, -z, y), rot,
                                          "MAP001_planter_%02d_shrub_b" % pi)
            elif asset == "ENV011":
                objs = env.create_dry_grass(c_plants, (x, -z, y), rot,
                                            "MAP001_planter_%02d_grass_%d" % (pi, si))
            else:
                y = 0.42
                objs = env.create_fallen_leaves(c_plants, (x, -z, y), rot,
                                                "MAP001_planter_%02d_litter_%d" % (pi, si))
            if scale != 1.0:
                for o in objs:
                    o.scale = (scale, scale, scale)
            record(asset, "planter_plant_%02d_%02d" % (pi, si), x, z, rot, y=y,
                   scale=scale, collider={"type": "none"},
                   source="art/full/source/plants/ENV011_dry_grass.blend"
                   if asset == "ENV011" else
                   "art/full/source/plants/ENV012_fallen_leaves.blend"
                   if asset == "ENV012" else
                   "art/full/source/plants/%s.blend" % (
                       "ENV009_shrub_a" if asset == "ENV009" else "ENV010_shrub_b"),
                   objects=objs,
                   note="inside side planter; planter collider covers it")

    # Dry grass and fallen leaf clusters: soil margins, fence lines and the
    # central ring, with varied scales so the beds stop reading as bare ground.
    grass_specs = [(-13.2, -7.6, 20.0, 1.20), (-13.3, -2.4, 80.0, 1.10),
                   (-13.1, 2.8, 140.0, 1.30), (-13.2, 7.2, 15.0, 1.15),
                   (13.2, -7.4, -30.0, 1.25), (13.3, -2.0, 60.0, 1.10),
                   (13.1, 3.2, 200.0, 1.20), (13.2, 7.4, 100.0, 1.15),
                   (-8.6, 9.1, 10.0, 1.10), (0.4, 9.2, 120.0, 1.25),
                   (8.6, 9.1, -70.0, 1.15), (-8.4, -9.0, 40.0, 1.10),
                   (0.6, -9.0, 160.0, 1.20), (8.4, -9.0, -15.0, 1.10),
                   (-11.9, 2.0, 30.0, 1.00), (11.0, 8.4, 120.0, 1.00),
                   (-3.7, 9.0, -20.0, 1.00), (6.0, -9.0, 75.0, 1.00),
                   (-10.6, -8.6, 10.0, 1.00), (10.8, 6.9, 200.0, 1.00)]
    for i, (x, z, rot, scale) in enumerate(grass_specs):
        # These spots predate the paving layout and four of them sit inside a
        # module. A tuft is ~0.5 m across, so inset by its own radius: this is
        # what put dry grass on the flagstones.
        if on_paving(x, z, margin=0.55):
            print("PLANTING_SKIP dry_grass_%02d at %.2f,%.2f on paving" % (i, x, z))
            continue
        objs = env.create_dry_grass(c_plants, (x, -z, 0.0), rot,
                                    "MAP001_dry_grass_%02d" % i)
        if scale != 1.0:
            for o in objs:
                o.scale = (scale, scale, scale)
        record("ENV011", "dry_grass_%02d" % i, x, z, rot, scale=scale,
               collider={"type": "none"},
               source="art/full/source/plants/ENV011_dry_grass.blend",
               objects=objs)
    leaf_specs = [(0.4, 2.3, 10.0, 1.20), (2.4, 0.2, 70.0, 1.00),
                  (-2.2, -1.0, 140.0, 1.10), (-8.3, -3.2, -30.0, 1.20),
                  (-13.0, 0.5, 20.0, 1.30), (12.9, 3.0, 80.0, 1.20),
                  (-6.5, 8.7, 10.0, 1.10), (6.5, 8.7, 60.0, 1.15),
                  (-11.8, 4.6, 30.0, 1.10), (11.8, -5.0, 90.0, 1.10)]
    for i, (x, z, rot, scale) in enumerate(leaf_specs):
        # Same story as the dry grass: four leaf piles were authored on top of
        # paving modules. Leaves on stone read as debris, not as planting.
        if on_paving(x, z, margin=0.35):
            print("PLANTING_SKIP fallen_leaves_%02d at %.2f,%.2f on paving" % (i, x, z))
            continue
        objs = env.create_fallen_leaves(c_plants, (x, -z, 0.0), rot,
                                        "MAP001_fallen_leaves_%02d" % i)
        if scale != 1.0:
            for o in objs:
                o.scale = (scale, scale, scale)
        record("ENV012", "fallen_leaves_%02d" % i, x, z, rot, scale=scale,
               collider={"type": "none"},
               source="art/full/source/plants/ENV012_fallen_leaves.blend",
               objects=objs)
    ring_cover = [("ENV012", 0.90, 0.60, 10.0, 0.80),
                  ("ENV012", -0.80, 0.80, 70.0, 0.70),
                  ("ENV012", 0.20, -1.10, 130.0, 0.75),
                  ("ENV011", -0.55, -0.90, 40.0, 0.70)]
    for i, (asset, x, z, rot, scale) in enumerate(ring_cover):
        builder = env.create_dry_grass if asset == "ENV011" else env.create_fallen_leaves
        objs = builder(c_plants, (x, -z, 0.63), rot,
                       "MAP001_ring_cover_%02d" % i)
        for o in objs:
            o.scale = (scale, scale, scale)
        record(asset, "ring_cover_%02d" % i, x, z, rot, y=0.63, scale=scale,
               collider={"type": "none"},
               source="art/full/source/plants/ENV011_dry_grass.blend"
               if asset == "ENV011" else
               "art/full/source/plants/ENV012_fallen_leaves.blend",
               objects=objs,
               note="inside central ring planter; planter collider covers it")

    # Edge beds visible in the formal camera: break up the remaining bare soil.
    extra_cover = [("ENV011", -6.8, 5.8, 20.0, 1.10),
                   ("ENV011", -8.5, 4.5, 70.0, 1.20),
                   ("ENV011", -10.5, 6.5, 140.0, 1.00),
                   ("ENV012", -7.3, 6.9, 10.0, 1.20),
                   ("ENV011", 6.8, 5.8, 40.0, 1.15),
                   ("ENV012", 9.5, 3.5, 90.0, 1.10),
                   ("ENV011", -9.5, -1.5, 160.0, 1.20),
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
                   ("ENV012", 6.0, 9.3, 80.0, 1.10)]
    for i, (asset, x, z, rot, scale) in enumerate(extra_cover):
        builder = env.create_dry_grass if asset == "ENV011" else env.create_fallen_leaves
        objs = builder(c_plants, (x, -z, 0.0), rot,
                       "MAP001_edge_cover_%02d" % i)
        for o in objs:
            o.scale = (scale, scale, scale)
        record(asset, "edge_cover_%02d" % i, x, z, rot, scale=scale,
               collider={"type": "none"},
               source="art/full/source/plants/ENV011_dry_grass.blend"
               if asset == "ENV011" else
               "art/full/source/plants/ENV012_fallen_leaves.blend",
               objects=objs)

    # Path / clearance metadata.
    STATE["paths"] = [
        {"id": "central_plaza", "rect_x": [-6, 6], "rect_z": [-6, 6],
         "width_min": 4.0, "note": "ring around planter leaves 4.0 m clear"},
        {"id": "south_approach", "rect_x": [-2, 2], "rect_z": [-10, -6],
         "width_min": 4.0},
        {"id": "north_approach", "rect_x": [-2, 2], "rect_z": [6, 10],
         "width_min": 4.0},
        {"id": "west_approach", "rect_x": [-10, -6], "rect_z": [-6, 6],
         "width_min": 4.0},
        {"id": "east_approach", "rect_x": [6, 10], "rect_z": [2, 6],
         "width_min": 4.0},
        {"id": "pergola_pad", "rect_x": [10, 14], "rect_z": [4, 8],
         "width_min": 3.0},
    ]

    # Clearance checks required by the brief.
    checks = clearance_report([
        ("spawn_south", 0.0, -8.0, 1.0),
        ("pickup_A", -7.0, -3.0, 1.5),
        ("pickup_B", -8.0, 4.0, 1.5),
        ("pickup_C", 8.0, 5.0, 1.5),
        ("npc_gardener", 3.0, -5.0, 0.8),
        ("board_stand", 0.0, 5.9, 0.8),
        ("pergola_card_gap", 8.0, 5.0, 1.5),
    ])
    STATE["validation"] = checks

    # Fixed demo camera and light rig (saved with the layout for inspection).
    cam = cl.setup_demo_camera(target=(0, 0, 0.80), distance=33.0, fov_deg=35.0,
                               resolution=(1500, 950), samples=72)
    cam.name = "CAM_map001"
    cam["map_id"] = "MAP001"
    cam["elevation_deg"] = 45.0
    cam["vertical_fov_deg"] = 35.0
    cam["view_from"] = "engine south (+Z), facing north"
    scene.view_settings.exposure = -0.30
    for obj in scene.objects:
        if obj.type == "LIGHT":
            obj["map_id"] = "MAP001"

    # Triangle / object facts before save.
    export_meshes = [o for o in scene.objects
                     if o.type == "MESH" and not o.name.startswith("COL_")]
    text_objects = [o for o in scene.objects if o.type == "FONT"]
    total_tris = sum(cl.object_triangles(o) for o in export_meshes)
    total_verts = sum(len(o.data.vertices) for o in export_meshes)
    print("MAP001 objects=%d meshes=%d text=%d tris=%d verts=%d" % (
        len(scene.objects), len(export_meshes), len(text_objects), total_tris,
        total_verts))

    # World-space box UVs so engine material textures keep uniform texel
    # density (V02); wood objects project grain along their long axis.
    wood_names = {"MAT_wood_old", "MAT_wood_dark", "MAT_wood_pale",
                  "MAT_bench_wood"}
    for o in export_meshes:
        names = {m.name for m in o.data.materials if m}
        if "ENG_MAT_leaf_atlas" in names or "MAT_leaf_atlas" in names:
            continue  # cards carry their own atlas UVs
        cl.bake_box_uvs(o, density=1.0, grain=bool(names & wood_names))
    print("MAP001 UVs baked: %d meshes" % len(export_meshes))

    audit_path = os.path.join(BUILD_OUTPUT_ROOT or cl.N3, "vegetation_audit.json")
    # `on_paving` is the expanded exclusion-zone test used before placement.
    # A hit is normally dropped, so it is a blocked candidate, not rendered
    # grass. Keep actual violations separate from successful prevention.
    on_pave = sum(1 for r in VEG_AUDIT
                  if r["on_paving"] and not r.get("dropped", False))
    blocked_by_paving = sum(1 for r in VEG_AUDIT
                            if r["on_paving"] and r.get("dropped", False))
    containers = {}
    for r in VEG_AUDIT:
        containers[r["container"]] = containers.get(r["container"], 0) + 1
    with open(audit_path, "w", encoding="utf-8") as fh:
        json.dump({"kind": "n5_vegetation_audit", "total": len(VEG_AUDIT),
                   "violations": on_pave,
                   "blocked_by_paving": blocked_by_paving,
                   "by_container": containers,
                   "tufts": VEG_AUDIT}, fh, ensure_ascii=False)
    print("VEG_AUDIT total=%d violations=%d blocked_by_paving=%d containers=%s"
          % (len(VEG_AUDIT), on_pave, blocked_by_paving, containers))

    if N5_VARIANT:
        # Ablation/variant run: preview only, never overwrite the canonical
        # blend/GLB/layout that the formal build depends on.
        cl.render_to(os.path.join(BUILD_PREVIEW,
                                  "MAP001_courtyard_%s.png" % N5_VARIANT))
        print("VARIANT_RENDER=%s" % N5_VARIANT)
        return

    cl.save_blend(BLEND)

    # Geometry cleanup, after the .blend is written so the source keeps its
    # editable text objects. The GLB gets tessellated glyphs with their slivers
    # already removed.
    cleaned = []
    for o in export_meshes:
        deg, dup = cl.clean_mesh_object(o)
        if deg or dup:
            cleaned.append((o.name, deg, dup))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for f in text_objects:
        me = bpy.data.meshes.new_from_object(f.evaluated_get(depsgraph))
        conv = bpy.data.objects.new(f.name, me)
        conv.matrix_world = f.matrix_world.copy()
        scene.collection.objects.link(conv)
        deg, dup = cl.clean_mesh_object(conv)
        if deg or dup:
            cleaned.append((conv.name, deg, dup))
        export_meshes.append(conv)
    print("GEOMETRY_CLEAN objects=%d removed=%d sample=%s" % (
        len(cleaned), sum(d + u for _, d, u in cleaned),
        [(n[:28], d, u) for n, d, u in cleaned[:6]]))

    ao_stats = cl.apply_vertex_ao(export_meshes)
    print("VERTEX_AO objects=%d contact_cells=%d ground_contact_verts=%d min_factor=%.3f"
          % (ao_stats["objects"], ao_stats["contact_cells"],
             ao_stats["ground_contact_vertices"], ao_stats["min_factor"]))

    cl.export_glb(export_meshes, GLB)
    _try_render(PNG, "overview")

    # Top-down diagnostic view (preview only; not saved as a map camera).
    top_cam_data = bpy.data.cameras.new("MAP001_top_camera")
    top_cam_data.type = "ORTHO"
    top_cam_data.ortho_scale = 30.0
    top_cam = bpy.data.objects.new("MAP001_top_camera", top_cam_data)
    c_light.objects.link(top_cam)
    top_cam.location = (0, 0, 30.0)
    top_cam.rotation_euler = (0, 0, math.pi)
    scene.camera = top_cam
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 860
    scene.cycles.samples = 32
    _try_render(PNG_TOP, "topdown")

    # Restore main camera for the saved file?  The .blend was already saved with
    # the demo camera; this in-memory change is not saved.
    scene.camera = cam

    # Layout JSON.
    payload = {
        "schema": "courtyard_layout/1",
        "map_id": "MAP001",
        "name": "秋庭完整布局",
        "generated_by": "tools/blender/build_map001.py",
        "units": "1 Blender unit = 1 world unit",
        "coordinate_system": {
            "engine": "Y up, ground XZ, centre (0,0,0)",
            "bounds_x": [-14, 14], "bounds_z": [-10, 10],
            "blender_to_engine": "engine = (x, z, -y); engine yaw = Blender Z rotation",
            "module_front": "-Y Blender / +Z engine before layout rotation",
            "ground_top_y": 0.0,
            "soil_top_y": SOIL_TOP,
            "paving_note": "ENV001 modules sunk by 0.14 so their top is y=0",
        },
        "look": {
            "profile": "art/full/source/layout/LOOK001_look_profile.json",
            "camera": "45 deg elevation, vertical FOV 35, from south",
            "renderer": "Cycles CPU preview; not Cocos/WeChat evidence",
        },
        "ground": STATE["ground"],
        "instances": STATE["instances"],
        "interactions": STATE["interactions"],
        "occlusion_groups": STATE["occlusion"],
        "collision_proxies": STATE["proxies"],
        "paths": STATE["paths"],
        "clearances": STATE["validation"],
        "stats": {
            "instances": len(STATE["instances"]),
            "mesh_objects": len(export_meshes),
            "text_objects": len(text_objects),
            "triangles": total_tris,
            "vertices": total_verts,
            "materials": sorted({m.name for o in export_meshes
                                 for m in o.data.materials if m}),
        },
        "missing": [
            "NPC gardener character (no stand-in placed; character work pending)",
            "engine-ready baked textures/UVs for all procedural materials",
            "Cocos/WeChat import, Y-up axis check and engine screenshots",
            "runtime occlusion/collision logic (layout data only)",
            "background buildings beyond the wall/railing edge closure",
        ],
    }
    cl.write_json(LAYOUT, payload)
    print("LAYOUT_INSTANCES=%d PROXIES=%d" % (
        len(STATE["instances"]), len(STATE["proxies"])))


if __name__ == "__main__":
    build()
