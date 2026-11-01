"""
Shared helpers for the native courtyard asset set (ENV002-012, PROP002-006,
MAT001-005, LOOK001, MAP001).

Rules honoured here:
  * Every asset is real Blender geometry; no image textures, no generated
    concept images, no PNG-as-source.
  * Units: 1 Blender unit = 1 world unit (project treats 1 unit as ~1 m).
  * Module origin: bottom centre (0,0,0), front faces -Y in Blender.  With the
    glTF Y-up export used here Blender (x, y, z) -> engine (x, z, -y), so the
    module front becomes +Z in engine space.  Map layout uses engine X/Z.
  * Materials are procedural for Cycles previews.  Each material also carries
    constant PBR fallbacks (custom props) used only for GLB export, because
    Blender procedural nodes do not transfer to glTF.  No bake has been done.

All preview renders in this project are Cycles CPU renders, not engine output.
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(TOOLS_DIR))
ROOT = PROJECT
N3 = os.path.join(PROJECT, "art", "candidates", "candidate_n5")
SRC_ENV = os.path.join(N3, "source", "environment")
SRC_PROP = os.path.join(N3, "source", "props")
SRC_PLANT = os.path.join(N3, "source", "plants")
SRC_MAT = os.path.join(N3, "source", "materials")
SRC_LAYOUT = os.path.join(N3, "source", "layout")
PREVIEW_ENV = os.path.join(N3, "previews", "environment")
PREVIEW_PROP = os.path.join(N3, "previews", "props")
PREVIEW_PLANT = os.path.join(N3, "previews", "plants")
PREVIEW_MAT = os.path.join(N3, "previews", "materials")
PREVIEW_LAYOUT = os.path.join(N3, "previews", "layout")

# P1_ART_STYLE_GUIDE.md 3.1 starter palette (sRGB hex).
PALETTE = {
    "stone_base": "#A2907A",
    "stone_light": "#B7A488",
    "stone_dark": "#6B5B4A",
    "mortar": "#75685A",
    "soil": "#4C3A2B",
    "wood": "#866C50",
    "wood_dark": "#5A4634",
    "wood_pale": "#A58C6B",
    "metal": "#494744",
    "metal_rust": "#7A5540",
    "metal_brass": "#A9834B",
    "leaf_ochre": "#B8702F",
    "leaf_amber": "#9A5326",
    "leaf_olive": "#5F5230",
    "leaf_deep": "#5A3221",
    "leaf_gold": "#D89B54",
    "leaf_mass": "#402C1F",
    "leaf_far": "#6B5B48",
    # n5 aerial perspective. n4 graded distance DARKER than the near hedge,
    # which inverted depth and produced the "dark band" at the top of frame.
    # Farther layers must move toward the sky value instead.
    "leaf_mid_haze": "#7E6B4E",
    "leaf_haze": "#A08E6C",
    "grass_dry": "#CDB784",
    "grass_pale": "#E3CFA0",
    "paper_cream": "#F3F0E6",
    "paper_kraft": "#D8C39D",
    "ink": "#2E3234",
    "gold": "#D8AA58",
    "mint": "#9FD8C8",
    "glass_warm": "#F2D9A8",
    "roof_tile": "#8C5B48",
    "flower_rose": "#D98F9B",
    "flower_cream": "#EFE2C6",
}


def _apply_palette_override():
    """Overlay colour tokens from N5_PALETTE so one build can render a variant.

    Value format: "leaf_olive=#6E5A44;leaf_deep=#5A4438". Env vars are used
    instead of a JSON file because Blender's bundled Python cannot open paths
    containing the CJK characters in this project root (Errno 22).
    """
    spec = os.environ.get("N5_PALETTE", "").strip()
    if not spec:
        return []
    applied = []
    for pair in spec.split(";"):
        pair = pair.strip()
        if not pair or "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        key, value = key.strip(), value.strip()
        if key in PALETTE and value.startswith("#"):
            applied.append("%s %s->%s" % (key, PALETTE[key], value))
            PALETTE[key] = value
    return applied


PALETTE_OVERRIDES = _apply_palette_override()
ART_VARIANT = os.environ.get("N5_ART_VARIANT", "")
# Look-dev knobs: leaf cards are the dominant geometry, so one scale factor on
# the shared cluster builder moves tree crowns, hedge skin and shrub masses
# together instead of editing twenty call sites.
LEAF_SCALE = float(os.environ.get("N5_LEAF_SCALE", "1") or 1)
LEAF_COUNT_SCALE = float(os.environ.get("N5_LEAF_COUNT_SCALE", "1") or 1)
# Shape knobs, separate from size/density: the silhouette is a different defect
# from "too small / too many" and has to be judged on its own build.
LEAF_SHAPE = os.environ.get("N5_LEAF_SHAPE", "diamond").strip().lower()
LEAF_FOLD = float(os.environ.get("N5_LEAF_FOLD", "0.11") or 0.11)
# Whole-scene style switch. o = the shipped procedural look, c = low-poly
# cartoon (solid blobs, flat colour, no cards), r = textured (alpha atlas on
# the cards). It lives here rather than in build_map001 because every foliage
# generator funnels through add_leaf_cluster.
STYLE = os.environ.get("N5_STYLE", "o").strip().lower()
# Low-poly only needs a fraction of the clusters: one blob replaces a whole
# cluster of cards, so the blob count is what sets the triangle budget.
BLOB_KEEP = float(os.environ.get("N5_BLOB_KEEP", "0.30") or 0.30)
BLOB_RADIUS_SCALE = float(os.environ.get("N5_BLOB_RADIUS_SCALE", "1.55") or 1.55)
BLOB_SUBDIV = int(os.environ.get("N5_BLOB_SUBDIV", "1") or 1)

FONT_PATH_CANDIDATES = [
    os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts",
                 "Noto Sans SC (TrueType).otf"),
    os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "simhei.ttf"),
]


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


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def new_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

def make_procedural_material(name, base_hex, roughness=0.7, metallic=0.0,
                             noise_scale=6.0, detail=4.0, map_scale=(1, 1, 1),
                             color_variation=0.10, roughness_variation=0.10,
                             bump_strength=0.12, bump_scale=24.0,
                             emission_hex=None, emission_strength=0.0,
                             double_sided=False):
    """Principled material with procedural colour/roughness/bump break-up.

    Engine constants are stashed on the material so export_glb() can build a
    flat glTF-safe copy (procedural nodes cannot be exported to glTF).
    """
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing

    base = hex_to_linear_rgba(base_hex)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (760, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (420, 0)

    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-900, 0)
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.location = (-720, 0)
    mapping.inputs["Scale"].default_value = map_scale
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.location = (-540, 40)
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = 0.55

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-300, 120)
    ramp.color_ramp.elements[0].position = 0.34
    ramp.color_ramp.elements[0].color = tuple(
        min(1.0, max(0.0, c * (1.0 - color_variation))) for c in base[:3]
    ) + (1.0,)
    ramp.color_ramp.elements[1].position = 0.70
    ramp.color_ramp.elements[1].color = tuple(
        min(1.0, c * (1.0 + color_variation)) for c in base[:3]
    ) + (1.0,)

    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.location = (-300, -120)
    rough.inputs["From Min"].default_value = 0.0
    rough.inputs["From Max"].default_value = 1.0
    rough.inputs["To Min"].default_value = max(0.0, roughness - roughness_variation)
    rough.inputs["To Max"].default_value = min(1.0, roughness + roughness_variation)

    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (120, -260)
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.02

    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(noise.outputs["Fac"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    bsdf.inputs["Metallic"].default_value = metallic

    emission = hex_to_linear_rgba(emission_hex or "#000000")
    bsdf.inputs["Emission Color"].default_value = emission
    bsdf.inputs["Emission Strength"].default_value = emission_strength

    mat.use_backface_culling = not double_sided
    mat.diffuse_color = base
    mat["engine_base_color"] = list(base)
    mat["engine_roughness"] = float(roughness)
    mat["engine_metallic"] = float(metallic)
    mat["engine_emission_color"] = list(emission)
    mat["engine_emission_strength"] = float(emission_strength)
    mat["source_hex"] = base_hex
    mat["procedural_preview_only"] = True
    return mat


def mat_stone_base():
    return make_procedural_material(
        "MAT_stone_base", PALETTE["stone_base"], roughness=0.72,
        noise_scale=2.6, map_scale=(2.2, 2.2, 1.0), color_variation=0.10,
        roughness_variation=0.14, bump_strength=0.16)


def mat_stone_light():
    return make_procedural_material(
        "MAT_stone_light", PALETTE["stone_light"], roughness=0.66,
        noise_scale=3.4, map_scale=(3.0, 3.0, 1.0), color_variation=0.07,
        roughness_variation=0.10, bump_strength=0.10)


def mat_stone_dark():
    return make_procedural_material(
        "MAT_stone_dark", PALETTE["stone_dark"], roughness=0.80,
        noise_scale=2.0, map_scale=(1.5, 1.5, 1.0), color_variation=0.12,
        roughness_variation=0.12, bump_strength=0.20)


def mat_mortar():
    return make_procedural_material(
        "MAT_mortar", PALETTE["mortar"], roughness=0.93, noise_scale=9.0,
        color_variation=0.07, roughness_variation=0.05, bump_strength=0.22)


def mat_soil():
    return make_procedural_material(
        "MAT_soil", PALETTE["soil"], roughness=0.96, noise_scale=7.0,
        color_variation=0.16, roughness_variation=0.04, bump_strength=0.35,
        bump_scale=40.0)


def mat_wood():
    return make_procedural_material(
        "MAT_wood_old", PALETTE["wood"], roughness=0.58, noise_scale=3.0,
        map_scale=(1.0, 7.0, 1.0), color_variation=0.14,
        roughness_variation=0.10, bump_strength=0.10)


def mat_wood_dark():
    return make_procedural_material(
        "MAT_wood_dark", PALETTE["wood_dark"], roughness=0.64, noise_scale=3.6,
        map_scale=(1.0, 6.0, 1.0), color_variation=0.12,
        roughness_variation=0.10, bump_strength=0.12)


def mat_wood_pale():
    return make_procedural_material(
        "MAT_wood_pale", PALETTE["wood_pale"], roughness=0.55, noise_scale=3.2,
        map_scale=(1.0, 6.0, 1.0), color_variation=0.12,
        roughness_variation=0.10, bump_strength=0.10)


def mat_metal():
    return make_procedural_material(
        "MAT_metal_iron", PALETTE["metal"], roughness=0.38, metallic=0.85,
        noise_scale=5.0, color_variation=0.05, roughness_variation=0.08,
        bump_strength=0.06)


def mat_metal_rust():
    return make_procedural_material(
        "MAT_metal_rust", PALETTE["metal_rust"], roughness=0.78, metallic=0.35,
        noise_scale=9.0, color_variation=0.16, roughness_variation=0.10,
        bump_strength=0.18)


def mat_metal_brass():
    return make_procedural_material(
        "MAT_metal_brass", PALETTE["metal_brass"], roughness=0.34, metallic=0.80,
        noise_scale=6.0, color_variation=0.07, roughness_variation=0.06,
        bump_strength=0.05)


def mat_leaf_atlas():
    """Single textured leaf material: the card UVs index a procedural atlas
    (alpha shape + tip-to-base gradient). Engine keeps the embedded texture."""
    name = "MAT_leaf_atlas"
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    tex_path = os.environ.get(
        "N5_LEAF_ATLAS_PATH",
        os.path.join(ROOT, "demo_n5/assets/resources/textures/tex_leaf_atlas.png"))
    # Do not reuse a same-named image appended from an asset .blend. Blender's
    # check_existing matches datablocks by source path/basename and can silently
    # keep the old atlas after a candidate path override.
    img = bpy.data.images.load(tex_path, check_existing=False)
    tex = next((node for node in nt.nodes if node.type == "TEX_IMAGE"), None)
    if tex is None:
        tex = nt.nodes.new("ShaderNodeTexImage")
    tex.name = "N5_P1_leaf_atlas"
    tex.image = img
    tex.interpolation = "Linear"
    for link in list(nt.links):
        if link.to_node == bsdf and link.to_socket.name in ("Base Color", "Alpha"):
            nt.links.remove(link)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.62
    mat.blend_method = "CLIP"
    mat.alpha_threshold = 0.5
    mat["engine_base_color"] = (1.0, 1.0, 1.0, 1.0)
    mat["engine_roughness"] = 0.62
    mat["engine_texture_path"] = os.environ.get(
        "N5_LEAF_ATLAS_ENGINE_PATH", tex_path)
    return mat


def mat_leaf_ochre():
    return make_procedural_material(
        "MAT_leaf_ochre", PALETTE["leaf_ochre"], roughness=0.56, noise_scale=4.0,
        color_variation=0.16, roughness_variation=0.10, bump_strength=0.10,
        double_sided=True)


def mat_leaf_amber():
    return make_procedural_material(
        "MAT_leaf_amber", PALETTE["leaf_amber"], roughness=0.60, noise_scale=4.4,
        color_variation=0.15, roughness_variation=0.10, bump_strength=0.10,
        double_sided=True)


def mat_leaf_olive():
    return make_procedural_material(
        "MAT_leaf_olive", PALETTE["leaf_olive"], roughness=0.62, noise_scale=4.8,
        color_variation=0.13, roughness_variation=0.10, bump_strength=0.10,
        double_sided=True)


def mat_leaf_deep():
    return make_procedural_material(
        "MAT_leaf_deep", PALETTE["leaf_deep"], roughness=0.62, noise_scale=5.2,
        color_variation=0.12, roughness_variation=0.10, bump_strength=0.10,
        double_sided=True)


def mat_leaf_gold():
    return make_procedural_material(
        "MAT_leaf_gold", PALETTE["leaf_gold"], roughness=0.54, noise_scale=4.6,
        color_variation=0.14, roughness_variation=0.10, bump_strength=0.08,
        double_sided=True)


def mat_leaf_far():
    return make_procedural_material(
        "MAT_leaf_far", PALETTE["leaf_far"], roughness=0.70, noise_scale=5.6,
        color_variation=0.09, roughness_variation=0.06, bump_strength=0.06,
        double_sided=True)


def mat_leaf_mid_haze():
    return make_procedural_material(
        "MAT_leaf_mid_haze", PALETTE["leaf_mid_haze"], roughness=0.74,
        noise_scale=5.4, color_variation=0.08, roughness_variation=0.05,
        bump_strength=0.05, double_sided=True)


def mat_leaf_haze():
    return make_procedural_material(
        "MAT_leaf_haze", PALETTE["leaf_haze"], roughness=0.78, noise_scale=5.0,
        color_variation=0.06, roughness_variation=0.04, bump_strength=0.04,
        double_sided=True)


def mat_leaf_mass():
    return make_procedural_material(
        "MAT_leaf_mass", PALETTE["leaf_mass"], roughness=0.82, noise_scale=3.2,
        color_variation=0.10, roughness_variation=0.08, bump_strength=0.06,
        double_sided=False)


def mat_roof_tile():
    return make_procedural_material(
        "MAT_roof_tile", PALETTE["roof_tile"], roughness=0.82, noise_scale=7.0,
        map_scale=(6.0, 2.0, 1.0), color_variation=0.12,
        roughness_variation=0.08, bump_strength=0.10)


def mat_flower_rose():
    return make_procedural_material(
        "MAT_flower_rose", PALETTE["flower_rose"], roughness=0.62,
        noise_scale=9.0, color_variation=0.10, roughness_variation=0.06,
        bump_strength=0.03, double_sided=True)


def mat_flower_cream():
    return make_procedural_material(
        "MAT_flower_cream", PALETTE["flower_cream"], roughness=0.60,
        noise_scale=9.0, color_variation=0.08, roughness_variation=0.06,
        bump_strength=0.03, double_sided=True)


def mat_grass_dry():
    return make_procedural_material(
        "MAT_grass_dry", PALETTE["grass_dry"], roughness=0.72, noise_scale=6.0,
        color_variation=0.16, roughness_variation=0.08, bump_strength=0.10,
        double_sided=True)


def mat_grass_pale():
    return make_procedural_material(
        "MAT_grass_pale", PALETTE["grass_pale"], roughness=0.70, noise_scale=6.4,
        color_variation=0.14, roughness_variation=0.08, bump_strength=0.10,
        double_sided=True)


def mat_paper_cream():
    return make_procedural_material(
        "MAT_paper_cream", PALETTE["paper_cream"], roughness=0.86,
        noise_scale=32.0, color_variation=0.035, roughness_variation=0.05,
        bump_strength=0.06, double_sided=True)


def mat_paper_kraft():
    return make_procedural_material(
        "MAT_paper_kraft", PALETTE["paper_kraft"], roughness=0.90,
        noise_scale=26.0, color_variation=0.06, roughness_variation=0.05,
        bump_strength=0.08, double_sided=True)


def mat_ink():
    return make_procedural_material(
        "MAT_ink", PALETTE["ink"], roughness=0.52, noise_scale=18.0,
        color_variation=0.04, roughness_variation=0.04, bump_strength=0.03)


def mat_gold():
    return make_procedural_material(
        "MAT_pickup_gold", PALETTE["gold"], roughness=0.32, metallic=0.75,
        noise_scale=8.0, color_variation=0.06, roughness_variation=0.05,
        bump_strength=0.03)


def mat_lamp_glass():
    return make_procedural_material(
        "MAT_lamp_glass", PALETTE["glass_warm"], roughness=0.24,
        noise_scale=5.0, color_variation=0.03, roughness_variation=0.03,
        bump_strength=0.0, emission_hex="#FFD9A0", emission_strength=3.0,
        double_sided=True)


def mat_ground_soil():
    return make_procedural_material(
        "MAT_ground_soil", "#5E5040", roughness=0.95, noise_scale=3.0,
        map_scale=(8.0, 8.0, 1.0), color_variation=0.20,
        roughness_variation=0.04, bump_strength=0.25)


def mat_ground_skirt():
    return make_procedural_material(
        "MAT_ground_skirt", "#A8A18A", roughness=0.96, noise_scale=2.0,
        color_variation=0.10, roughness_variation=0.03, bump_strength=0.2)


MATERIAL_FAMILIES = {
    "MAT001": ("stone", [mat_stone_base, mat_stone_light, mat_stone_dark,
                         mat_mortar, mat_soil]),
    "MAT002": ("wood", [mat_wood, mat_wood_dark, mat_wood_pale]),
    "MAT003": ("metal", [mat_metal, mat_metal_rust, mat_metal_brass]),
    "MAT004": ("leaf_grass", [mat_leaf_ochre, mat_leaf_amber, mat_leaf_olive,
                              mat_leaf_deep, mat_grass_dry, mat_grass_pale]),
    "MAT005": ("paper", [mat_paper_cream, mat_paper_kraft, mat_ink, mat_gold]),
}


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def add_box(bm, center, size, rot_deg=(0.0, 0.0, 0.0), mat_index=0):
    rot = Euler((math.radians(rot_deg[0]), math.radians(rot_deg[1]),
                 math.radians(rot_deg[2])), "XYZ").to_matrix().to_4x4()
    matrix = (Matrix.Translation(Vector(center)) @ rot
              @ Matrix.Diagonal((size[0], size[1], size[2], 1.0)))
    res = bmesh.ops.create_cube(bm, size=1.0, matrix=matrix)
    for v in res["verts"]:
        for f in v.link_faces:
            f.material_index = mat_index
    return res


def add_cylinder(bm, p0, p1, radius0, radius1=None, segments=10, mat_index=0):
    p0, p1 = Vector(p0), Vector(p1)
    direction = p1 - p0
    length = direction.length
    if length <= 1e-6:
        raise ValueError("zero-length cylinder")
    if radius1 is None:
        radius1 = radius0
    quat = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized())
    matrix = (Matrix.Translation((p0 + p1) / 2.0)
              @ quat.to_matrix().to_4x4())
    res = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=segments,
        radius1=radius0, radius2=radius1, depth=length, matrix=matrix)
    for v in res["verts"]:
        for f in v.link_faces:
            f.material_index = mat_index
    return res


def add_smooth_tube(bm, points, radii, segments=10, mat_index=0,
                    ring_noise=0.0, rng=None, cap_start=True, cap_end=True):
    """Continuous tube through a polyline with parallel-transported rings.

    Unlike chaining separate cones, shared rings keep the silhouette and
    shading continuous across a tapered trunk or a curved branch.
    """
    pts = [Vector(p) for p in points]
    if len(pts) < 2 or len(pts) != len(radii):
        raise ValueError("tube needs matching points/radii")
    tangents = []
    for i in range(len(pts)):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == len(pts) - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        tangents.append(t.normalized())
    ref = Vector((0.0, 0.0, 1.0))
    if abs(tangents[0].dot(ref)) > 0.9:
        ref = Vector((1.0, 0.0, 0.0))
    u = (ref - tangents[0] * ref.dot(tangents[0])).normalized()
    rings = []
    for i, (p, r, t) in enumerate(zip(pts, radii, tangents)):
        u = u - t * u.dot(t)
        if u.length < 1e-6:
            u = t.cross(Vector((1.0, 0.0, 0.0)))
            if u.length < 1e-6:
                u = t.cross(Vector((0.0, 1.0, 0.0)))
        u.normalize()
        v = t.cross(u).normalized()
        ring = []
        for s in range(segments):
            a = math.tau * s / segments
            rr = r * (1.0 + (rng.uniform(-ring_noise, ring_noise) if rng else 0.0))
            ring.append(bm.verts.new(p + u * (math.cos(a) * rr)
                                     + v * (math.sin(a) * rr)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for s in range(segments):
            a = rings[i][s]
            b = rings[i][(s + 1) % segments]
            c = rings[i + 1][(s + 1) % segments]
            d = rings[i + 1][s]
            f = bm.faces.new((a, b, c, d))
            f.material_index = mat_index
    for do_cap, idx, flip in ((cap_start, 0, True), (cap_end, -1, False)):
        if not do_cap:
            continue
        center = bm.verts.new(pts[idx])
        ring = rings[idx]
        for s in range(segments):
            a, b = ring[s], ring[(s + 1) % segments]
            f = bm.faces.new((center, b, a) if flip else (center, a, b))
            f.material_index = mat_index
    return rings


def add_solid_ring(bm, r_in, r_out, z0, z1, segments=48, mat_index=0):
    """Washer-like solid ring (bottom, top, inner and outer walls)."""
    ring_verts = []
    for z in (z0, z1):
        inner, outer = [], []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            inner.append(bm.verts.new((r_in * math.cos(a), r_in * math.sin(a), z)))
            outer.append(bm.verts.new((r_out * math.cos(a), r_out * math.sin(a), z)))
        ring_verts.append((inner, outer))
    (bi, bo), (ti, to) = ring_verts
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.append(bm.faces.new((bi[i], bo[i], bo[j], bi[j])))       # bottom
        faces.append(bm.faces.new((ti[i], ti[j], to[j], to[i])))       # top
        faces.append(bm.faces.new((bo[i], bo[j], to[j], to[i])))       # outer
        faces.append(bm.faces.new((bi[i], ti[i], ti[j], bi[j])))       # inner
    for f in faces:
        f.material_index = mat_index
    return faces


def add_arc_block(bm, angle_deg, r_in, r_out, z0, z1, half_gap_deg=0.5,
                  mat_index=0, taper=0.0):
    """One stone block of a circular planter, with a real joint gap."""
    a0 = math.radians(angle_deg - 90.0 / 2.0 + half_gap_deg)
    a1 = math.radians(angle_deg + 90.0 / 2.0 - half_gap_deg)
    ri0, ro0 = r_in, r_out
    ri1, ro1 = r_in + taper, r_out + taper
    verts = []
    for (z, ri, ro) in ((z0, ri0, ro0), (z1, ri1, ro1)):
        verts.append([
            bm.verts.new((ri * math.cos(a0), ri * math.sin(a0), z)),
            bm.verts.new((ro * math.cos(a0), ro * math.sin(a0), z)),
            bm.verts.new((ro * math.cos(a1), ro * math.sin(a1), z)),
            bm.verts.new((ri * math.cos(a1), ri * math.sin(a1), z)),
        ])
    b, t = verts
    quads = [
        (b[0], b[1], b[2], b[3]),  # bottom
        (t[0], t[3], t[2], t[1]),  # top
        (b[0], b[3], t[3], t[0]),  # inner
        (b[1], t[1], t[2], b[2]),  # outer
        (b[0], t[0], t[1], b[1]),  # end a0
        (b[3], b[2], t[2], t[3]),  # end a1
    ]
    faces = []
    for q in quads:
        f = bm.faces.new(q)
        f.material_index = mat_index
        faces.append(f)
    return faces


def _leaf_profile(shape):
    """Leaf silhouette as a list of (x, y) points around the centre, tip = +Y.

    The default 'diamond' is the original 4-triangle card: a smooth outline with
    no notches, which at 720p reads as a brown chip rather than a leaf. The lobed
    profiles alternate tip/recess radii so the silhouette carries visible teeth -
    the reference frame's foliage has deep lobes (see plan appendix D).
    """
    if shape == "trilobe":
        spec = [(90, 0.55), (30, 0.28), (-30, 0.40), (-90, 0.18),
                (-150, 0.40), (150, 0.28)]
    elif shape == "pentalobe":
        spec = [(90, 0.55), (54, 0.30), (18, 0.42), (-18, 0.26), (-54, 0.36),
                (-90, 0.18), (-126, 0.36), (-162, 0.26), (162, 0.42), (126, 0.30)]
    else:
        return None
    return [(math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r)
            for a, r in spec]


def add_leaf(bm, center, normal, size, spin, mat_index, tilt=0.0,
             uv_cell=None, shape=None):
    """Leaf card: lobed fan (shape dependent) or the original folded diamond.

    When uv_cell is given, the card's loops are UV-mapped into that cell of the
    4x2 leaf atlas so the engine samples an alpha shape with a gradient.
    """
    q = Vector(normal).normalized().to_track_quat("Z", "Y")
    rot = (q.to_matrix().to_4x4()
           @ Matrix.Rotation(spin, 4, "Z")
           @ Matrix.Rotation(tilt, 4, "X"))
    m = Matrix.Translation(Vector(center)) @ rot @ Matrix.Scale(size, 4)
    profile = _leaf_profile(shape or LEAF_SHAPE)
    if profile is None:
        local = [
            (0.0, 0.50, 0.00),    # tip
            (0.31, 0.02, 0.03),   # right
            (0.0, -0.50, 0.00),   # base
            (-0.31, 0.02, 0.03),  # left
            (0.0, 0.00, LEAF_FOLD),  # raised centre
        ]
        faces_idx = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    else:
        n = len(profile)
        local = [(x, y, 0.0) for (x, y) in profile] + [(0.0, 0.0, LEAF_FOLD)]
        faces_idx = [(i, (i + 1) % n, n) for i in range(n)]
    vs = [bm.verts.new(m @ Vector(p)) for p in local]
    for idx in faces_idx:
        f = bm.faces.new(tuple(vs[i] for i in idx))
        f.material_index = mat_index
    if uv_cell is not None:
        uv = bm.loops.layers.uv.verify()
        col = uv_cell % 4
        row = uv_cell // 4
        for f in {f for v in vs for f in v.link_faces}:
            for loop in f.loops:
                lp = m.inverted() @ loop.vert.co
                u = (col + 0.5 + lp.x * 1.35) / 4.0
                v = (row + 0.5 + lp.y * 0.92) / 2.0
                loop[uv].uv = (u, v)
    return vs


def rand_unit(rng, z_min=-1.0):
    while True:
        v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(z_min, 1)))
        if 0.05 < v.length <= 1.0:
            return v.normalized()


def _add_leaf_blob(bm, center, radius, rng, mat_indices, flatten=0.78):
    """One flat-shaded low-poly blob instead of a cluster of leaf cards.

    Cartoon style: the silhouette has to read as a solid lump at 720p, and a
    lump is 80 triangles where a card cluster is 42x7. BLOB_KEEP thins the
    clusters out so the crown does not become a bag of beads, and the radius
    is scaled up by roughly the cube root of that thinning to keep the volume.
    """
    if rng.random() > BLOB_KEEP:
        return 0
    r = radius * BLOB_RADIUS_SCALE
    jitter = 0.10 if BLOB_SUBDIV > 0 else 0.0
    res = bmesh.ops.create_icosphere(bm, subdivisions=BLOB_SUBDIV, radius=r)
    verts = res["verts"]
    center = Vector(center)
    for vert in verts:
        co = vert.co.copy()
        n = co.normalized() if co.length else Vector((0.0, 0.0, 1.0))
        vert.co = co * (1.0 + rng.uniform(-jitter, jitter))
        # 2026-10-27: the blob used to be a fixed ball, so ground litter -
        # authored as a flat 0.1-height patch of leaves - came out as a
        # scattering of little grey rocks lying on the flagstones. The blob now
        # honours the cluster's flatten, which keeps crowns round and makes
        # litter read as a patch again.
        vert.co.z *= max(0.10, flatten)
        vert.co += center
    mat = mat_indices[0] if isinstance(mat_indices, (list, tuple)) else mat_indices
    faces = set()
    for vert in verts:
        faces.update(vert.link_faces)
    for face in faces:
        face.material_index = mat
        face.smooth = False
    return 1


def add_leaf_cluster(bm, center, radius, count, rng, mat_indices,
                     leaf_size=0.13, flatten=0.78, shell_inner=0.55,
                     z_min=-0.45, keep=1.0):
    """Build `count` leaf cards around `center`.

    `keep` drops a deterministic fraction of the cards while still drawing
    every random number the full cluster would draw. That keeps the shared RNG
    stream - and therefore every mesh built afterwards - byte-identical, so a
    density test differs from its baseline only by the removed leaves.
    """
    center = Vector(center)
    if STYLE == "c":
        return _add_leaf_blob(bm, center, radius, rng, mat_indices, flatten)
    if LEAF_COUNT_SCALE != 1.0:
        count = max(1, int(round(count * LEAF_COUNT_SCALE)))
    built = 0
    for i in range(count):
        d = rand_unit(rng, z_min=z_min)
        r = radius * rng.uniform(shell_inner, 1.0)
        pos = center + Vector((d.x * r, d.y * r, d.z * r * flatten))
        normal = Vector((d.x, d.y, d.z * 0.6 + 0.4)).normalized()
        size = leaf_size * LEAF_SCALE * rng.uniform(0.72, 1.15)
        spin = rng.uniform(0.0, math.tau)
        mat = rng.choice(mat_indices)
        tilt = rng.uniform(-0.25, 0.25)
        if keep < 1.0 and ((i * 2654435761) % 1000) / 1000.0 >= keep:
            continue
        shape = None
        if LEAF_SHAPE == "mix":
            # 70/30 lobed vs plain: identical leaves everywhere read as a
            # repeating stamp, so the mix keeps some cards plain.
            shape = "trilobe" if rng.random() < 0.7 else "diamond"
        add_leaf(bm, pos, normal, size, spin, mat, tilt=tilt,
                 uv_cell=(i * 3 + int(spin * 7)) % 8, shape=shape)
        built += 1
    return built


def add_mass_lobe(bm, center, radius, rng, flatten=0.78, subdiv=3,
                  displace=0.10, mat_index=0):
    """Opaque displaced ellipsoid that gives a continuous crown volume behind
    the leaf cards.  Native mesh, no textures; cards remain the readable
    surface, this only removes see-through fragmentation."""
    result = bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    verts = result["verts"]
    center = Vector(center)
    for vert in verts:
        co = vert.co.copy()
        normal = co.normalized() if co.length else Vector((0.0, 0.0, 1.0))
        vert.co = co * (1.0 + rng.uniform(-displace, displace))
        vert.co.z *= flatten
        vert.co += center
    faces = set()
    for vert in verts:
        faces.update(vert.link_faces)
    for face in faces:
        face.material_index = mat_index
    return faces


def build_tapered_branch(bm, p0, p1, r0, r1, segments=8, mat_index=0,
                         mid_bulge=0.0):
    p0, p1 = Vector(p0), Vector(p1)
    mid = (p0 + p1) / 2.0
    if mid_bulge:
        mid += Vector((0, 0, mid_bulge))
    add_cylinder(bm, p0, mid, r0, (r0 + r1) / 2.0, segments, mat_index)
    add_cylinder(bm, mid, p1, (r0 + r1) / 2.0, r1, segments, mat_index)


def clean_mesh_object(obj, min_area=1e-9):
    """Drop zero-area triangles and exact duplicate faces in place.

    The rework spec's N01 asks to clear "duplicate coplanar faces" but the build
    had no way to say how many existed.  Measured on the shipped map: 137 exact
    duplicates (railing 68, planting-bed rims 32+32, signs 5) and 7,630
    zero-area triangles, 7,210 of them inside the extruded font glyphs.

    A zero-area triangle contributes no pixels and no normal, and one face of a
    coincident pair always loses the depth test — so removing both is visually
    lossless.  Returns (removed_degenerate, removed_duplicate).
    """
    import bmesh as _bmesh
    me = obj.data
    if not me.polygons:
        return (0, 0)
    bm = _bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()

    degenerate = []
    for f in bm.faces:
        if f.calc_area() <= min_area:
            degenerate.append(f)
    if degenerate:
        _bmesh.ops.delete(bm, geom=degenerate, context='FACES')

    bm.faces.ensure_lookup_table()
    seen = {}
    dup = []
    for f in bm.faces:
        key = tuple(sorted(tuple(round(c, 4) for c in v.co) for v in f.verts))
        if len(key) < 3:
            dup.append(f)
            continue
        if key in seen:
            dup.append(f)
        else:
            seen[key] = True
    if dup:
        _bmesh.ops.delete(bm, geom=dup, context='FACES')

    # Sweep the vertices and edges the deleted faces left behind; loose geometry
    # still costs buffer space and trips the "floating" read in review.
    loose_v = [v for v in bm.verts if not v.link_faces]
    loose_e = [e for e in bm.edges if not e.link_faces]
    if loose_e:
        _bmesh.ops.delete(bm, geom=loose_e, context='EDGES')
    if loose_v:
        _bmesh.ops.delete(bm, geom=loose_v, context='VERTS')

    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.update()
    return (len(degenerate), len(dup))


def finish_mesh(name, bm, materials, collection=None):
    bm.normal_update()
    # A style pass can legitimately empty a mesh (low-poly skips the hedge card
    # skin entirely). Emitting a zero-face object would then trip the UV baker,
    # which takes max() over an empty corner list, and would also ship an empty
    # node in the GLB. Drop it here.
    if not bm.faces:
        bm.free()
        return None
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.collection).objects.link(obj)
    for m in materials:
        mesh.materials.append(m)
    return obj


def bake_box_uvs(obj, density=1.0, grain=False):
    """World-space box UV projection so engine textures keep uniform texel
    density without hand UV editing.  grain=True orients U along the object's
    longer horizontal axis (plank grain follows the plank)."""
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uvl = mesh.uv_layers.active
    mw = obj.matrix_world
    nmat = mw.to_3x3().inverted().transposed()

    corners = [mw @ v.co for v in mesh.vertices]
    ex = (max(c.x for c in corners) - min(c.x for c in corners))
    ey = (max(c.y for c in corners) - min(c.y for c in corners))
    long_x = ex >= ey

    for poly in mesh.polygons:
        n = (nmat @ poly.normal).normalized()
        nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)
        if nz >= nx and nz >= ny:
            # horizontal face: U/V from the two horizontal axes
            axes = (1, 0) if (grain and not long_x) else (0, 1)
        elif nx >= ny:
            # face varies across y/z
            axes = (1, 2)
        else:
            # face varies across x/z
            axes = (0, 2)
        for li in poly.loop_indices:
            co = corners[mesh.loops[li].vertex_index]
            uvl.data[li].uv = (co[axes[0]] * density, co[axes[1]] * density)
    return obj


def add_bevel(obj, width=0.006, segments=2, angle_deg=40.0):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    mod = obj.modifiers.new("BEV_edges", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angle_deg)
    mod.harden_normals = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.shade_auto_smooth(angle=math.radians(32.0))
    obj.select_set(False)
    return obj


def add_empty(name, location=(0, 0, 0), collection=None, size=0.2):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = size
    obj.location = location
    (collection or bpy.context.collection).objects.link(obj)
    return obj


def set_instance(obj, origin, rot_z_deg=0.0):
    obj.location = Vector(origin)
    obj.rotation_euler = Euler((0.0, 0.0, math.radians(rot_z_deg)), "XYZ")
    return obj


def place_instance(objects, origin, rot_z_deg=0.0):
    """Apply a module placement without discarding per-object local offsets.

    Needed for text and loose card objects whose placement is stored on the
    object rather than in mesh coordinates.  Object rotation is composed by
    adding the yaw (Euler XYZ => Rz @ Ry @ Rx), which keeps an upright text
    object upright while turning it with the module.
    """
    if not isinstance(objects, (list, tuple)):
        objects = [objects]
    origin = Vector(origin)
    rot = Matrix.Rotation(math.radians(rot_z_deg), 3, "Z")
    for obj in objects:
        obj.location = origin + rot @ Vector(obj.location)
        obj.rotation_euler.z += math.radians(rot_z_deg)
    return objects


# ---------------------------------------------------------------------------
# Text (native editable text objects, outlines converted for GLB only)
# ---------------------------------------------------------------------------

def load_font():
    font = bpy.data.fonts.get("NotoSansSC")
    if font:
        return font
    for path in FONT_PATH_CANDIDATES:
        if os.path.isfile(path):
            try:
                font = bpy.data.fonts.load(path)
                font.name = "NotoSansSC"
                return font
            except Exception as exc:  # pragma: no cover - environment dependent
                print("FONT_LOAD_FAIL %s %r" % (path, exc))
    raise RuntimeError("no CJK font found for editable text")


def add_text(name, body, size=0.16, location=(0, 0, 0), rot_deg=(90, 0, 0),
             extrude=0.003, mat=None, collection=None, align="CENTER",
             line_spacing=1.0):
    curve = bpy.data.curves.new(name + "_curve", "FONT")
    curve.body = body
    curve.font = load_font()
    curve.size = size
    curve.extrude = extrude
    curve.bevel_depth = 0.0012
    curve.bevel_resolution = 1
    curve.align_x = align
    curve.align_y = "CENTER"
    curve.space_line = line_spacing
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    obj.rotation_euler = Euler(tuple(math.radians(v) for v in rot_deg), "XYZ")
    (collection or bpy.context.collection).objects.link(obj)
    if mat is not None:
        curve.materials.append(mat)
    return obj


# ---------------------------------------------------------------------------
# Export / verify helpers
# ---------------------------------------------------------------------------

def _flat_material(mat):
    name = "ENG_" + mat.name
    existing = bpy.data.materials.get(name)
    flat = existing or bpy.data.materials.new(name)
    flat.use_nodes = True
    bsdf = flat.node_tree.nodes.get("Principled BSDF")
    tex_rel = mat.get("engine_texture_path")
    base = tuple(mat.get("engine_base_color", (0.7, 0.7, 0.7, 1.0)))
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = float(mat.get("engine_roughness", 0.7))
    bsdf.inputs["Metallic"].default_value = float(mat.get("engine_metallic", 0.0))
    emis = tuple(mat.get("engine_emission_color", (0.0, 0.0, 0.0, 1.0)))
    bsdf.inputs["Emission Color"].default_value = emis
    bsdf.inputs["Emission Strength"].default_value = float(
        mat.get("engine_emission_strength", 0.0))
    if tex_rel:
        img_path = tex_rel if os.path.isabs(tex_rel) else os.path.join(ROOT, tex_rel)
        img = bpy.data.images.load(img_path, check_existing=False)
        tex = next((node for node in flat.node_tree.nodes
                    if node.type == "TEX_IMAGE"), None)
        if tex is None:
            tex = flat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.name = "N5_P1_engine_leaf_atlas"
        tex.image = img
        for link in list(flat.node_tree.links):
            if link.to_node == bsdf and link.to_socket.name in ("Base Color", "Alpha"):
                flat.node_tree.links.remove(link)
        flat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        flat.node_tree.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        flat.blend_method = "CLIP"
        flat.alpha_threshold = 0.5
        flat.show_transparent_back = False
    flat.use_backface_culling = mat.use_backface_culling
    flat.diffuse_color = base
    flat["engine_fallback_for"] = mat.name
    return flat


def _text_copies(objects):
    copies = []
    for obj in objects:
        if obj.type == "FONT":
            dup = obj.copy()
            dup.data = obj.data.copy()
            bpy.context.collection.objects.link(dup)
            copies.append(dup)
    if copies:
        bpy.ops.object.select_all(action="DESELECT")
        for obj in copies:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = copies[0]
        bpy.ops.object.convert(target="MESH")
    return copies


def apply_vertex_ao(objects, ground_names=("paving", "soil"),
                    foliage_names=("canopy", "leaf", "hedge", "moss",
                                   "grass", "treeline", "bg_tree", "flowers"),
                    contact_exclude=("paving", "soil", "grass", "leaf",
                                     "hedge", "moss", "flowers", "treeline",
                                     "bg_tree"),
                    cell=0.35, near=0.45, far=0.95):
    """Bake cheap, deterministic ambient occlusion into a POINT colour layer.

    Grounding, not lighting: object bases darken by height, foliage faces that
    point down read darker than sky-facing cards, and ground near solid props
    gets a contact ring built from a 2-D occupancy grid of those props' low
    geometry.  Values are multiplied in the engine via USE_VERTEX_COLOR, so no
    extra texture or light costs anything on the build.

    Returns a summary dict for the build log.
    """
    import numpy as np

    def world_xyz(obj):
        me = obj.data
        n = len(me.vertices)
        if not n:
            return np.zeros((0, 3))
        co = np.empty(n * 3, dtype=np.float64)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        mw = np.array(obj.matrix_world, dtype=np.float64)
        return co @ mw[:3, :3].T + mw[:3, 3]

    def world_nz(obj):
        me = obj.data
        n = len(me.vertices)
        if not n:
            return np.zeros(0)
        try:
            nor = np.empty(n * 3, dtype=np.float64)
            me.vertex_normals.foreach_get("vector", nor)
        except Exception:  # noqa: BLE001 - normals unavailable on ancient meshes
            return np.zeros(n)
        nor = nor.reshape(-1, 3)
        mw = np.array(obj.matrix_world, dtype=np.float64)
        return nor @ mw[:3, :3].T[:, 2]

    # Occupancy grid of solid objects' low geometry: the cells a prop stands on.
    solid = [o for o in objects
             if o.type == "MESH"
             and not any(k in o.name.lower() for k in contact_exclude)]
    cells = set()
    for obj in solid:
        xyz = world_xyz(obj)
        low = xyz[xyz[:, 2] < 1.4]
        for x, y in zip(low[:, 0], low[:, 1]):
            cells.add((int(math.floor(x / cell)), int(math.floor(y / cell))))
    cell_list = np.array(sorted(cells), dtype=np.int64) if cells else np.zeros((0, 2), dtype=np.int64)
    cell_keys = np.sort(cell_list[:, 0] * 100003 + cell_list[:, 1]) if len(cell_list) else np.zeros(0, dtype=np.int64)

    stats = {"objects": 0, "contact_cells": len(cell_list),
             "min_factor": 1.0, "ground_contact_vertices": 0}
    for obj in objects:
        if obj.type != "MESH" or not obj.data.vertices:
            continue
        name = obj.name.lower()
        xyz = world_xyz(obj)
        nz = world_nz(obj)
        n = len(xyz)

        f = 0.78 + 0.22 * np.clip(xyz[:, 2] / 0.9, 0.0, 1.0)

        is_ground = any(k in name for k in ground_names)
        is_foliage = any(k in name for k in foliage_names)
        if is_foliage:
            f *= 0.86 + 0.14 * np.clip(nz * 0.5 + 0.5, 0.0, 1.0)
        if is_ground and len(cell_keys):
            ci = np.floor(xyz[:, :2] / cell).astype(np.int64)
            base_key = ci[:, 0] * 100003 + ci[:, 1]
            best = np.full(n, np.inf)
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    probe = base_key + (dx * 100003 + dy)
                    pos = np.clip(np.searchsorted(cell_keys, probe), 0, len(cell_keys) - 1)
                    hit = cell_keys[pos] == probe
                    dist = math.hypot(dx, dy) * cell
                    best = np.where(hit, np.minimum(best, dist), best)
            contact = np.clip((far - best) / max(far - near, 1e-6), 0.0, 1.0)
            f *= 1.0 - 0.22 * contact
            stats["ground_contact_vertices"] += int((contact > 0).sum())
            # Per-slab value variation so big surfaces stop reading as paper.
            h = np.sin(xyz[:, 0] * 3.1 + xyz[:, 1] * 1.7) * np.sin(xyz[:, 1] * 2.3 - xyz[:, 0] * 1.1)
            f *= 0.955 + 0.045 * (h * 0.5 + 0.5)
        f = np.clip(f, 0.55, 1.0)

        rgba = np.empty((n, 4), dtype=np.float32)
        rgba[:, 0] = f
        rgba[:, 1] = f * 0.985
        rgba[:, 2] = f * 0.960
        rgba[:, 3] = 1.0
        me = obj.data
        layer = me.color_attributes.get("Col")
        if layer is None:
            layer = me.color_attributes.new(name="Col", type="FLOAT_COLOR", domain="POINT")
        layer.data.foreach_set("color", rgba.ravel())
        me.color_attributes.active_color = layer
        try:
            me.color_attributes.render_color_index = me.color_attributes.find("Col")
        except Exception:  # noqa: BLE001 - older API without render index
            pass
        stats["objects"] += 1
        stats["min_factor"] = min(stats["min_factor"], float(f.min()))
    return stats


def export_glb(objects, path, use_flat_materials=True):
    """Export selected meshes with constant PBR fallbacks for procedural mats.

    Returns the list of temporary text-mesh copies (already unlinked).
    """
    ensure_dir(os.path.dirname(path))
    roots = [o for o in objects if o.type in {"MESH", "FONT"}]
    original_slots = []
    if use_flat_materials:
        for obj in roots:
            for slot in obj.material_slots:
                if slot.material is not None:
                    original_slots.append((slot, slot.material))
                    slot.material = _flat_material(slot.material)

    text_copies = _text_copies(roots)
    export_objects = [o for o in roots if o.type == "MESH"] + text_copies

    if not export_objects:
        raise RuntimeError("nothing to export: " + path)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in export_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = export_objects[0]
    tmp = path + ".tmp.glb"
    if os.path.exists(tmp):
        os.remove(tmp)
    bpy.ops.export_scene.gltf(
        filepath=tmp, export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_cameras=False,
        export_lights=False, export_extras=True, export_tangents=False,
        export_vertex_color="ACTIVE", export_all_vertex_colors=True)
    import time
    last = None
    for _ in range(8):
        try:
            os.replace(tmp, path)
            last = None
            break
        except OSError as exc:
            last = exc
            time.sleep(0.5)
    if last is not None:
        raise RuntimeError("cannot replace GLB target %s: %s" % (path, last))
    print("GLB_WRITTEN=%s bytes=%d" % (path, os.path.getsize(path)))

    for slot, mat in original_slots:
        slot.material = mat
    for obj in text_copies:
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data.users == 0:
            bpy.data.meshes.remove(data)
    return text_copies


def save_blend(path):
    ensure_dir(os.path.dirname(path))
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=False)
    print("BLEND_SAVED=%s bytes=%d" % (path, os.path.getsize(path)))
    with open(path, "rb") as fh:
        header = fh.read(12)
    if not header.startswith(b"BLENDER"):
        raise RuntimeError("unexpected blend header %r" % header)


def write_json(path, data):
    """Serialise JSON to `path`, immune to Blender's EINVAL on wide paths.

    Blender's bundled Python intermittently raises
    ``OSError: [Errno 22] Invalid argument`` when opening an output file under a
    path with non-ASCII characters, while the very same path works from a normal
    interpreter and Blender's own operators write it fine.  Serialise into the
    ASCII temp directory first and copy the bytes over, which sidesteps it and is
    also atomic enough for the gate: the target never holds a half-written file.
    """
    import shutil
    import tempfile
    ensure_dir(os.path.dirname(path))
    tmp = os.path.join(tempfile.gettempdir(),
                       "n5_%s_%d.json" % (os.path.basename(path), os.getpid()))
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    shutil.copyfile(tmp, path)
    os.remove(tmp)
    print("JSON_WRITTEN=%s bytes=%d" % (path, os.path.getsize(path)))


# ---------------------------------------------------------------------------
# Preview studio (Cycles CPU; render previews only, never engine evidence)
# ---------------------------------------------------------------------------

def _look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_preview_ground(size=60.0, z=0.0, color_hex="#C9C2B4", collection=None):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    plane = bpy.context.object
    plane.name = "PREVIEW_ground"
    mat = make_procedural_material(
        "MAT_preview_ground", color_hex, roughness=0.9, noise_scale=2.2,
        color_variation=0.06, bump_strength=0.05)
    plane.data.materials.append(mat)
    if collection is not None:
        for c in list(plane.users_collection):
            c.objects.unlink(plane)
        collection.objects.link(plane)
    return plane


def setup_studio(target=(0, 0, 0.4), distance=5.0, elevation_deg=24.0,
                 azimuth_deg=32.0, fov_deg=35.0, resolution=(1000, 760),
                 samples=48, ground=True, ground_z=0.0,
                 ground_color="#C9C2B4", world_hex=(0.36, 0.41, 0.47)):
    scene = bpy.context.scene
    if ground:
        add_preview_ground(size=max(40.0, distance * 5.0), z=ground_z,
                           color_hex=ground_color)

    az = math.radians(azimuth_deg)
    elev = math.radians(elevation_deg)
    cam_loc = Vector((
        target[0] + distance * math.cos(elev) * math.sin(az),
        target[1] - distance * math.cos(elev) * math.cos(az),
        target[2] + distance * math.sin(elev) + 0.02,
    ))
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.name = "PREVIEW_camera"
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle = math.radians(fov_deg)
    cam.data.clip_start = 0.05
    cam.data.clip_end = 300.0
    _look_at(cam, target)
    scene.camera = cam

    # Warm key from screen-left / above, matching the P1 lighting brief.
    key = bpy.data.lights.new("PREVIEW_key_sun", "SUN")
    key.energy = 2.6
    key.angle = math.radians(3.0)
    key.color = (1.0, 0.93, 0.82)
    key_obj = bpy.data.objects.new("PREVIEW_key_sun", key)
    bpy.context.collection.objects.link(key_obj)
    key_obj.rotation_euler = Euler((
        math.radians(52.0), 0.0, math.radians(-52.0)), "XYZ")

    fill = bpy.data.lights.new("PREVIEW_fill_area", "AREA")
    fill.energy = max(60.0, (distance ** 2) * 3.5)
    fill.shape = "DISK"
    fill.size = max(3.0, distance * 0.7)
    fill.color = (0.72, 0.80, 0.92)
    fill_obj = bpy.data.objects.new("PREVIEW_fill_area", fill)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (target[0] + distance * 0.7, target[1] + distance * 0.35,
                         target[2] + distance * 0.6)
    _look_at(fill_obj, target)

    world = bpy.data.worlds.new("PREVIEW_world") if scene.world is None else scene.world
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*world_hex, 1.0)
    bg.inputs["Strength"].default_value = 0.42

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.cycles.use_adaptive_sampling = True
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.35
    return cam


def setup_demo_camera(target=(0, 0, 0.5), distance=10.0, fov_deg=35.0,
                      resolution=(1280, 720), samples=64, sun=True):
    """Fixed 45-degree demo camera; camera sits south of the target.

    Engine south is -Z, which maps to +Y in this Blender scene, so the camera
    is placed at +Y and aimed north.
    """
    scene = bpy.context.scene
    elev = math.radians(45.0)
    cam_loc = Vector((target[0], target[1] + distance * math.cos(elev),
                      target[2] + distance * math.sin(elev)))
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.name = "CAM_look001"
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle = math.radians(fov_deg)
    cam.data.clip_start = 0.1
    cam.data.clip_end = 400.0
    _look_at(cam, target)
    scene.camera = cam

    if sun:
        key = bpy.data.lights.new("LGT_key_sun", "SUN")
        key.energy = 3.6
        key.angle = math.radians(2.5)
        key.color = (1.0, 0.92, 0.80)
        key_obj = bpy.data.objects.new("LGT_key_sun", key)
        bpy.context.collection.objects.link(key_obj)
        # Screen-left key: from the south-west, above.
        key_obj.rotation_euler = Euler((
            math.radians(48.0), 0.0, math.radians(-38.0)), "XYZ")

        fill = bpy.data.lights.new("LGT_fill_cool", "AREA")
        fill.energy = 900.0
        fill.shape = "DISK"
        fill.size = 14.0
        fill.color = (0.68, 0.76, 0.90)
        fill_obj = bpy.data.objects.new("LGT_fill_cool", fill)
        bpy.context.collection.objects.link(fill_obj)
        fill_obj.location = (target[0] + 9.0, target[1] + 6.0, target[2] + 9.0)
        _look_at(fill_obj, target)

    world = bpy.data.worlds.new("LOOK_world") if scene.world is None else scene.world
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.37, 0.41, 0.46, 1.0)
    bg.inputs["Strength"].default_value = 0.55

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.cycles.use_adaptive_sampling = True
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.15
    return cam


def render_to(path, scene=None):
    """Render to `path`, working around Blender's non-ASCII save failure.

    Blender's image writer opens the output path with the ANSI code page, so a
    project living under a Chinese path intermittently fails with
    "Render error (Invalid argument) cannot save: ..." even though the pixels
    rendered fine.  Render into the ASCII temp directory first and move the file
    into place; the move is a plain rename on the same volume.
    """
    import shutil
    import tempfile
    scene = scene or bpy.context.scene
    ensure_dir(os.path.dirname(path))
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, "n5_preview_%d.png" % os.getpid())
    scene.render.filepath = tmp_path
    bpy.ops.render.render(write_still=True)
    if not os.path.isfile(tmp_path):
        raise RuntimeError("render did not produce " + tmp_path)
    if os.path.isfile(path):
        os.remove(path)
    try:
        os.replace(tmp_path, path)
    except OSError:
        shutil.move(tmp_path, path)
    if not os.path.isfile(path):
        raise RuntimeError("render did not reach " + path)
    print("RENDER_WRITTEN=%s bytes=%d" % (path, os.path.getsize(path)))


# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------

def object_triangles(obj):
    if obj.type != "MESH":
        return 0
    deps = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(deps)
    me = ev.to_mesh()
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    ev.to_mesh_clear()
    return tris


def world_bounds(objects):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    found = False
    for obj in objects:
        if obj.type == "MESH":
            for v in obj.data.vertices:
                w = obj.matrix_world @ v.co
                lo = Vector((min(lo[i], w[i]) for i in range(3)))
                hi = Vector((max(hi[i], w[i]) for i in range(3)))
                found = True
        elif obj.type == "FONT":
            for c in obj.bound_box:
                w = obj.matrix_world @ Vector(c)
                lo = Vector((min(lo[i], w[i]) for i in range(3)))
                hi = Vector((max(hi[i], w[i]) for i in range(3)))
                found = True
    if not found:
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    return lo, hi


def print_module_facts(label, objects):
    lo, hi = world_bounds(objects)
    tris = sum(object_triangles(o) for o in objects)
    mats = sorted({m.name for o in objects for m in o.data.materials if m}
                  if objects else [])
    print("%s bounds_min=%s bounds_max=%s dims=%s tris=%d materials=%s objects=%s" % (
        label,
        tuple(round(v, 4) for v in lo),
        tuple(round(v, 4) for v in hi),
        tuple(round(hi[i] - lo[i], 4) for i in range(3)),
        tris, mats, [(o.name, o.type) for o in objects]))
    return {"bounds_min": [round(v, 4) for v in lo],
            "bounds_max": [round(v, 4) for v in hi],
            "dimensions": [round(hi[i] - lo[i], 4) for i in range(3)],
            "triangles": tris,
            "materials": mats,
            "objects": [o.name for o in objects],
            "object_types": {o.name: o.type for o in objects}}


def validate_file_header(path, magic=b"BLENDER"):
    with open(path, "rb") as fh:
        return fh.read(12).startswith(magic)
