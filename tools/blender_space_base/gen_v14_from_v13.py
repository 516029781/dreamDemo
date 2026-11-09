"""Generate tools/blender_space_base/build_scene_v14.py from the frozen v13 builder.

Single-batch art overhaul per planning/art/SPACE_BASE_V14_ONESHOT_PLAN_20261108.md.
Kept as a tool so the v14 builder is reproducible from source (AGENTS.md §2).

    python tools/blender_space_base/gen_v14_from_v13.py
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "build_scene_v13.py"
DST = HERE / "build_scene_v14.py"

REPLS = [
    # ---- M02 L0-b: D candidate (P0 measured) ----
    ("sc.view_settings.exposure = 0.22", "sc.view_settings.exposure = 0.0"),
    # ---- M04 L1 lighting ----
    ("sun.rotation_euler = (math.radians(46), 0, math.radians(-70))",
     "sun.rotation_euler = (math.radians(57), 0, math.radians(-70))"),
    ("sun_data.energy = 4.4", "sun_data.energy = 4.2"),
    ("sun_data.angle = math.radians(2.2)", "sun_data.angle = math.radians(5.0)"),
    ('bg.inputs["Strength"].default_value = 0.62',
     'bg.inputs["Strength"].default_value = 0.55'),
    ("def ao_ground(m, distance=1.6, strength=0.42):",
     "def ao_ground(m, distance=2.6, strength=0.55):"),
    # ---- M08 L5 bevel ----
    ("w = min(0.08, mind * 0.22)", "w = min(0.22, mind * 0.30)"),
    # ---- r3: S1 hard constraint needs a slightly brighter light-concrete base ----
    ('"platform": make_mat("v6.platform", "#B4B0A2", 0.9),       # S1 提亮',
     '"platform": make_mat("v6.platform", "#BBB7A8", 0.9),       # v14 r3 +4% for S1'),
    # ---- M05 L2 value separation (conservative: platform/apron untouched to protect S1) ----
    ('"road": make_mat("v9.road", "#87898B", 0.88),              # 沥青路（偏浅，护 S1）',
     '"road": make_mat("v9.road", "#7C7F81", 0.90),              # v14 M05 压暗'),
    ('"floor_ind": make_mat("v12.floor_ind", "#A0A5A2", 0.88)',
     '"floor_ind": make_mat("v12.floor_ind", "#939A98", 0.88)'),
    ('"steel": make_mat("v6.steel", "#98A1A3", 0.45, 0.55)',
     '"steel": make_mat("v6.steel", "#8B9698", 0.42, 0.60)'),
    ('"metal": make_mat("v6.metal", "#59676D", 0.5, 0.45)',
     '"metal": make_mat("v6.metal", "#525F64", 0.42, 0.60)'),
    # ---- M07 L4 texture amplitude ----
    ('def _tex_mix(mat, mode="grain", scale=6.0, lo=0.80, hi=1.06, mortar=0.72):',
     'def _tex_mix(mat, mode="grain", scale=6.0, lo=0.80, hi=1.06, mortar=0.55):'),
    ('_tex_mix(m["road"], "grain", 2.2, 0.74, 1.05)', '_tex_mix(m["road"], "grain", 2.2, 0.62, 1.12)'),
    ('_tex_mix(m["apron"], "panel", 1.6, 0.86, 1.02, 0.80)', '_tex_mix(m["apron"], "panel", 1.6, 0.66, 1.10, 0.58)'),
    ('_tex_mix(m["platform"], "panel", 0.9, 0.88, 1.02, 0.84)', '_tex_mix(m["platform"], "panel", 0.9, 0.68, 1.10, 0.58)'),
    ('_tex_mix(m["dock"], "panel", 0.7, 0.84, 1.03, 0.78)', '_tex_mix(m["dock"], "panel", 0.7, 0.66, 1.10, 0.58)'),
    ('_tex_mix(m["wall"], "panel", 0.7, 0.88, 1.02, 0.82)', '_tex_mix(m["wall"], "panel", 0.7, 0.66, 1.10, 0.58)'),
    ('_tex_mix(m["steel"], "grain", 3.0, 0.84, 1.05)', '_tex_mix(m["steel"], "grain", 3.0, 0.70, 1.12)'),
    ('_tex_mix(m["white"], "grain", 1.4, 0.90, 1.02)', '_tex_mix(m["white"], "grain", 1.4, 0.74, 1.08)'),
    ('_tex_mix(m["water"], "grain", 0.03, 0.86, 1.05)', '_tex_mix(m["water"], "grain", 0.03, 0.78, 1.10)'),
    # ---- M07: drive Roughness from the SAME mask, centred on each material's base value ----
    ('    nt.links.new(ramp.outputs["Color"], mix.inputs[2])\n'
     '    nt.links.new(mix.outputs["Color"], b.inputs["Base Color"])\n',
     '    nt.links.new(ramp.outputs["Color"], mix.inputs[2])\n'
     '    nt.links.new(mix.outputs["Color"], b.inputs["Base Color"])\n'
     '    # v14 M07: roughness variation from the same mask (not a constant)\n'
     '    try:\n'
     '        if not b.inputs["Roughness"].is_linked:\n'
     '            _base = float(b.inputs["Roughness"].default_value)\n'
     '            _mr = nt.nodes.new("ShaderNodeMapRange")\n'
     '            _mr.inputs["From Min"].default_value = 0.0\n'
     '            _mr.inputs["From Max"].default_value = 1.0\n'
     '            _mr.inputs["To Min"].default_value = max(0.02, _base * 0.85)\n'
     '            _mr.inputs["To Max"].default_value = min(1.0, _base * 1.15)\n'
     '            nt.links.new(ramp.outputs["Color"], _mr.inputs["Value"])\n'
     '            nt.links.new(_mr.outputs["Result"], b.inputs["Roughness"])\n'
     '    except Exception as _exc:\n'
     '        print("V14_ROUGH_MASK_SKIP", str(_exc)[:60])\n'),
    # ---- hook ----
    ("    build_camera_light(a.samples)\n",
     "    build_camera_light(a.samples)\n    apply_v14_art(m, a)\n"),
]

ART = r'''

# =====================================================================
# v14 single-batch art overhaul (M03 / M04 / M06 / M09)
# See planning/art/SPACE_BASE_V14_ONESHOT_PLAN_20261108.md
# =====================================================================

def _v14_area(name, loc, size, energy, color, target):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "SQUARE"
    ld.size = size
    ld.energy = energy
    ld.color = hex_rgba(color)[:3]
    o = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    d = Vector(target) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o


def build_v14_compositor(sat=1.0):
    """M03: P1-style grading stack. No vignette, no .cube (Blender 4.5 has no LUT node).

    r2 convergence: saturation boost is gated by a luminance mask so it only
    affects dark/mid tones. Bright low-sat concrete must stay low-sat, otherwise
    S1 (light = L>=0.62 AND sat<=0.28) collapses -- r1 measured 0.017.
    """
    sc = bpy.context.scene
    sc.use_nodes = True
    sc.render.use_compositing = True
    nt = sc.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    glare = nt.nodes.new("CompositorNodeGlare")
    try:
        glare.glare_type = "FOG_GLOW"
        glare.threshold = 0.90
        glare.size = 6
        glare.inputs["Strength"].default_value = 0.08
    except Exception as exc:
        print("V14_GLARE_SKIP", str(exc)[:80])
        nt.nodes.remove(glare)
        glare = None
    cb = nt.nodes.new("CompositorNodeColorBalance")
    cb.lift = (0.992, 0.997, 1.004)    # r2: much milder cool shadows
    cb.gain = (1.018, 1.006, 0.994)    # r2: much milder warm highlights
    cb.gamma = (1.10, 1.10, 1.10)   # r5: lift midtones across L=0.62 without pushing highlights
    hs = nt.nodes.new("CompositorNodeHueSat")
    hs.inputs["Saturation"].default_value = sat
    bc = nt.nodes.new("CompositorNodeBrightContrast")
    try:
        bc.inputs["Contrast"].default_value = 0.02
        bc.inputs["Bright"].default_value = 0.0
    except Exception:
        pass
    out = nt.nodes.new("CompositorNodeComposite")
    chain = [n for n in (rl, glare, cb, hs, bc, out) if n is not None]
    for a_, b_ in zip(chain, chain[1:]):
        nt.links.new(a_.outputs["Image"], b_.inputs["Image"])

    # luminance-gated saturation: dark -> boost, bright -> leave alone
    try:
        bw = nt.nodes.new("CompositorNodeRGBToBW")
        nt.links.new(rl.outputs["Image"], bw.inputs["Image"])
        ramp = nt.nodes.new("CompositorNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.32
        ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
        ramp.color_ramp.elements[1].position = 0.68
        ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
        nt.links.new(bw.outputs[0], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs[0], hs.inputs["Fac"])
        print("V14_SAT_MASK_OK")
    except Exception as exc:
        print("V14_SAT_MASK_SKIP", str(exc)[:90])
        hs.inputs["Fac"].default_value = 0.0
    print("V14_COMPOSITOR_OK", " -> ".join(n.bl_idname for n in chain))


def _v14_family(name):
    n = name.lower()
    if any(k in n for k in ("platform", "apron", "concrete", "walk", "causeway",
                            "terrace", "garden_wall", "coping", "floor_ind", "cope")):
        return "concrete"
    if any(k in n for k in ("road", "asphalt", "joint")):
        return "asphalt"
    if any(k in n for k in ("metal", "steel", "truss", "brass", "mesh", "rib",
                            "dome", "silo", "pipe", "rack")):
        return "metal"
    if any(k in n for k in ("glass", "win_", "frost")):
        return "glass"
    if any(k in n for k in ("grass", "hedge", "foliage", "palm", "bush", "card")):
        return "vegetation"
    if any(k in n for k in ("yellow", "orange", "evac", "emis", "blue", "green",
                            "zone", "strip", "visor")):
        return "accent"
    return "other"


def apply_v14_art(m, a):
    """Single-batch post-build pass. Runs AFTER build_camera_light."""
    import os
    sc = bpy.context.scene

    # ---- M04: two shaping fills (P1 uses 6 Area lights; v13 had only 2) ----
    _v14_area("V14_CoolSkyFill", (60.0, -180.0, 120.0), 200.0, 4500.0,
              "#8FA3B0", (120.0, 0.0, 0.0))
    _v14_area("V14_WarmBounce", (240.0, 60.0, 70.0), 160.0, 3500.0,
              "#FFE0B8", (120.0, 0.0, 0.0))

    # ---- M03: compositor grading (toggle with V14_NO_COMP=1 for A/B) ----
    if not os.environ.get("V14_NO_COMP"):
        build_v14_compositor(sat=float(os.environ.get("V14_SAT", "1.0")))
    else:
        print("V14_COMPOSITOR_OFF")

    # ---- M06: family tags + surface-response redistribution ----
    for mat in bpy.data.materials:
        mat["material_family"] = _v14_family(mat.name)

    def set_resp(key, rough, metal):
        mat = m.get(key)
        if mat is None or not mat.use_nodes:
            return
        b = mat.node_tree.nodes.get("Principled BSDF")
        if not b:
            return
        try:
            if not b.inputs["Roughness"].is_linked:
                b.inputs["Roughness"].default_value = rough
            if not b.inputs["Metallic"].is_linked:
                b.inputs["Metallic"].default_value = metal
        except Exception:
            pass

    for k in ("metal", "steel", "dome", "dome_base", "truss_dark", "rib_blue"):
        set_resp(k, 0.42, 0.60)
    for k in ("container_blue", "container_olive", "container_gray"):
        set_resp(k, 0.48, 0.55)
    for k in ("platform", "apron", "garden_walk", "causeway"):
        set_resp(k, 0.86, 0.0)
    set_resp("road", 0.90, 0.0)
    set_resp("glass", 0.08, 0.0)
    set_resp("frost", 0.12, 0.0)

    # ---- M06: alias-merge near-identical concretes, then drop unused materials ----
    def remap(old_key, new_key):
        old, new = m.get(old_key), m.get(new_key)
        if old is None or new is None or old == new:
            return 0
        n = 0
        for ob in bpy.data.objects:
            if ob.type != "MESH":
                continue
            for slot in ob.material_slots:
                if slot.material == old:
                    slot.material = new
                    n += 1
        m[old_key] = new
        return n

    merged = (remap("garden_walk", "platform") +
              remap("causeway", "apron") +
              remap("garden_stone", "apron"))
    before = len(bpy.data.materials)
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    print("V14_MATERIALS", "merged_slots=%d" % merged,
          "materials=%d->%d" % (before, len(bpy.data.materials)))

    # ---- M09: three-step shallow-water band around the site ----
    shallow_mats = [
        make_mat("v14.shallow_far", "#245055", 0.25, 0.0, 1.0, "#183B40", 0.30),
        make_mat("v14.shallow_mid", "#2E5A5F", 0.25, 0.0, 1.0, "#1C3C40", 0.35),
        make_mat("v14.shallow_near", "#3E6360", 0.25, 0.0, 1.0, "#264A48", 0.35),
    ]
    band = 0
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name.startswith("shore_fan_"):
            try:
                idx = int(ob.name.rsplit("_", 1)[1])
            except ValueError:
                continue
            if ob.material_slots:
                ob.material_slots[0].material = shallow_mats[idx % 3]
                band += 1
    print("V14_SHORE_BANDS", band)

    # ---- fog: master keeps it hidden (top-down legibility), hero enables it ----
    for ob in bpy.data.objects:
        if ob.get("is_fog"):
            ob["v14_fog"] = True
            ob.hide_render = True

    print("V14_ART_OK", "lights=%d" % sum(1 for o in bpy.data.objects if o.type == "LIGHT"),
          "compositor=%s" % sc.use_nodes)


'''


def main() -> int:
    s = SRC.read_text(encoding="utf-8")
    for old, new in REPLS:
        if old not in s:
            raise SystemExit("GEN_MISSING_PATTERN: " + old[:90])
        s = s.replace(old, new, 1)
    marker = "\ndef main():\n"
    if marker not in s:
        raise SystemExit("GEN_NO_MAIN")
    s = s.replace(marker, ART + marker, 1)
    s = s.replace("Generated by gen_v14_from_v13.py", "", 1)
    DST.write_text(s, encoding="utf-8")
    print("GEN_V14_OK", DST.name, len(s), "chars,", len(REPLS), "replacements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
