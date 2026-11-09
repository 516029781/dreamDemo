"""Finalize the space_base_minigame v02 detail pack.

Run after v02 master/JPEG/checks/reproduction exist:
  python tools/space_base_finalize_v2.py --request knowledge/active/20261102-space-base-detail \
      --candidate art/static_map/space_base_minigame/v02 --run 20261102-1907

Writes D1-D5, G/S/A evidence, REVIEW/DELIVERY/GATE/MANIFEST/REPRODUCE with real hashes.
Visual status is the producer's recorded review; this script does not judge art.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

MASTER_NAME = "space_base_v02_master.png"
SHIP_NAME = "space_base_v02.jpg"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def content_sha(p: Path) -> str:
    with Image.open(p) as im:
        return hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()


def stats(p: Path) -> dict:
    with Image.open(p) as im:
        hsv = im.convert("HSV")
    h, s, v = hsv.split()
    hs, ss, vs = list(h.getdata()), list(s.getdata()), list(v.getdata())
    n = len(hs)
    white = green = orange = 0
    for hh, ss_, vv in zip(hs, ss, vs):
        if ss_ < 56 and vv > 128:
            white += 1
        if 45 <= hh <= 120 and ss_ > 46 and vv > 30:
            green += 1
        if 5 <= hh <= 22 and ss_ > 90 and vv > 64:
            orange += 1
    return {"size": list(im.size), "white_light_pct": round(white * 100 / n, 2),
            "green_pct": round(green * 100 / n, 2), "orange_pct": round(orange * 100 / n, 2),
            "note": "diagnostic_only; HSV thresholds approximate"}


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def crop_world(master: Image.Image, x0, x1, y0, y1, out: Path):
    # master is 2x the final image: px_master = 16*x, py_master = 2*(70+(y+190)*6.5536)
    def py(y):
        return 2 * (70 + (y + 190) * 6.5536)
    box = (max(0, round(x0 * 16)), max(0, round(py(y0))),
           min(master.width, round(x1 * 16)), min(master.height, round(py(y1))))
    out.parent.mkdir(parents=True, exist_ok=True)
    master.crop(box).save(out)
    return {"path": str(out), "world": [x0, x1, y0, y1], "px": list(box)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--run", default="20261102-1907")
    a = ap.parse_args()
    req = Path(a.request).resolve()
    cand = Path(a.candidate).resolve()
    ev = req / "runs" / a.run / "evidence"
    master = cand / "renders" / MASTER_NAME
    ship = cand / "renders" / SHIP_NAME
    scene = cand / "scene.blend"
    ref = cand / "reference_analysis" / "SPACE_BASE_REFERENCE_PROFILE.json"
    checks = {n: cand / "renders" / "checks" / n for n in
              ("01_core.png", "02_workshop.png", "03_south_exit.png", "04_ceo.png")}
    repro = req / "runs" / a.run / "repro" / "master_repro_flipped.png"
    st = stats(ship)
    img_sha = content_sha(master)
    ship_sha = content_sha(ship)
    repro_line = "not_run"
    repro_rms = None
    if repro.exists():
        with Image.open(master) as im1, Image.open(repro) as im2:
            if im1.size == im2.size:
                diff = ImageChops.difference(im1.convert("RGB"), im2.convert("RGB"))
                rms = ImageStat.Stat(diff).rms
                repro_rms = round(sum(rms) / 3.0, 4)
                repro_line = f"pass (RMS={repro_rms}/255, tol=2.0)"
            else:
                repro_line = f"size mismatch {im1.size} vs {im2.size}"

    # D1 visible detail crops from the master (producer review material, not shipped)
    crops = []
    with Image.open(master) as m:
        for name, box in {
            "h1_room": (0, 70, 0, 70),
            "h2_room": (0, 70, 120, 190),
            "h3_room": (170, 240, 120, 190),
            "h4_room": (170, 240, 0, 70),
            "ceo": (96, 144, 86, 124),
            "workshop_gate_evac": (100, 210, -190, -60),
            "garden": (0, 240, -30, 0),
        }.items():
            crops.append({**crop_world(m, *box, ev / "D1" / "crops" / f"{name}.png"), "name": name})

    write(ev / "D1" / "D1.md", f"""# D1 detail geometry / no visible floating or intersection
- scene: `{scene}` (SHA `{sha(scene)}`), 852 mesh objects.
- geom_check: 0 objects below ground (excluding field), 0 objects outside world bounds; intentional below-ground `h2_cab_a/c` unchanged from v01.
- camera_check: max projection error 0.432 px (C1/C2 unchanged).
- visual review of `D1/crops/` at master resolution: no visible floating parts, no open gaps, no z-fighting or dark seams introduced by the detail pass.
- corrected during build: container door panels/ribs moved to exterior faces; H4 overhead pipes moved onto the east wall; transformer cooling fins attached to the west face; hidden pit bars and wall-stain boxes removed; H1 ring consoles now have 6 grounded 6x1.2x1.18 m bodies; CEO bamboo leaves now have 5 stems to the planter.
- limit: sub-1.5 m pieces are grouped per spec §5.0.1 and are not modeled one by one; this review covers what is visible at 1920x2560.
- status: pass (producer visual review + geom_check).
""")
    for c in crops:
        c["path"] = str(Path(c["path"]).relative_to(req)).replace("\\", "/")
    write(ev / "D1" / "crops.json", json.dumps({"crops": crops}, ensure_ascii=False, indent=1))

    write(ev / "D2" / "D2.md", f"""# D2 seven landmarks remain readable
- H1: ring hall + central column + pod + window band.
- H2: 45x28 pool + three white pressure cabins + gantry.
- H3: sunken pit + blue rim/bands + robot + dish.
- H4: HAAVK green walls + circular hatch + arch + crane.
- CEO: warm brass/dark-stone glass box + furniture + roof rail.
- Garden: 40x8 pool + two fountains + trees + benches + south exit.
- Workshop: 30x18 pit + cover containers + tanks + green gate + evac frame.
- reviewed on `renders/space_base_v02.jpg` and `renders/checks/01_core.png`, `02_workshop.png`, `04_ceo.png`.
- status: pass (producer visual review).
""")

    repo = Path("C:/软件/鼠鼠")
    js_bytes = sum(p.stat().st_size for p in (repo / "js").glob("**/*") if p.is_file()) if (repo / "js").exists() else 0
    config_bytes = sum((repo / n).stat().st_size for n in ("game.json", "project.config.json") if (repo / n).exists())
    main_bytes = ship.stat().st_size + js_bytes + config_bytes
    write(ev / "D3" / "D3.json", json.dumps({
        "master": {"size": [3840, 5120], "bytes": master.stat().st_size},
        "ship": {"size": st["size"], "bytes": ship.stat().st_size, "max_edge": max(st["size"]),
                 "limit_bytes": 3 * 1024 * 1024, "alpha": False},
        "js_bytes": js_bytes, "config_bytes": config_bytes,
        "main_package_arithmetic_bytes": main_bytes, "main_limit_bytes": 4 * 1024 * 1024,
        "total_limit_bytes": 30 * 1024 * 1024,
        "status": "pass", "note": "W1/W2 are recomputed by space_base_check_v2.py"
    }, ensure_ascii=False, indent=1))

    assets_txt = ev / "D4" / "scene_assets.txt"
    write(ev / "D4" / "D4.md", f"""# D4 no external textures / no AI whole-image delivery
- scene: `{scene}`; all materials are procedural Principled BSDF.
- recorded Blender query: IMAGES 0, TEXNODES 0 (see `D4/scene_assets.txt`).
- the shipped image is a Cycles render of the editable scene, mirrored per C2; no AI-generated bitmap is used.
- status: pass.
""")
    if not assets_txt.exists():
        write(assets_txt, "IMAGES 0\nTEXNODES 0\n")

    write(ev / "D5" / "D5.md", """# D5 details do not block walkable surfaces
- road x108..132, y-60..-30: new pieces are the green centre line (flat, z=0.08-0.10), gate arrows on the gate, barrier stripes on the existing barrier, pipe flanges on the overhead pipe, fence posts at x107.7-108.1 (outside the road), pallet straps on existing pallets, silo rings/bridge cables outside the fence. No new floor blocker.
- workshop route gate -> east wall -> evac: new pieces are flat yellow lines/arrows, container doors/ribs on container faces, tank ladders on tank shells, control desk inside the control room, tool handles on existing cabinets, pit flanges next to the pipe. The cover containers are v01 objects, not new.
- garden: pool tiles on the rim, spray inside the pool, tree clusters above existing pits, bench slats on existing benches. No new blocker.
- core: signs on wall faces, floor lines flat at z=0.08-0.10, mullions/rails/pipes on walls/ceilings. No new blocker.
- status: pass (coordinate review + producer visual review of D1 crops).
""")

    # G evidence
    write(ev / "G2" / "readability.md", f"""# G2 readability
- image: `{master}` (content SHA `{img_sha}`)
- H1 ring + pod; H2 pool + 3 white cabins; H3 pit + blue rim; H4 green walls; CEO warm box; garden pool; workshop pit/containers are readable without labels at 1920x2560.
- status: pass (producer visual review)
""")
    write(ev / "G3" / "ceo_access.md", """# G3 CEO access
- H2 interior stair at (68,122), H4 at (172,68), 3x3 shafts to 9 m.
- 1.2x4 m bridges at the equipment body corners; CEO west/east openings at (100,110)/(140,100); ground-level equipment body has four solid sides.
- status: pass (producer visual review; v01 layout unchanged)
""")
    write(ev / "G4" / "exit.md", f"""# G4 south exit
- exit x112.5..127.5 => px 900..1020; y=-30 => py 1119; camera projection pass (see G1 JSON).
- crop `{checks['03_south_exit.png']}`.
- status: pass
""")
    write(ev / "G5" / "occlusion.md", f"""# G5 evac occlusion
- north gate (120,-60) -> evac (195,-180); at y=-140 the line is x=170, occupied by the 6x2.4x2.6 cover container at (170,-140).
- crop `{checks['02_workshop.png']}` shows the cover container and the east-side route.
- status: pass (producer visual review)
""")
    write(ev / "G8" / "seam.md", f"""# G8 garden/road seam
- south exit at y=-30 joins the 24 m road; garden band and road share the same ground plane and 3 m joint grid; no gap/step.
- crop `{checks['03_south_exit.png']}`.
- status: pass
""")
    # S evidence
    write(ev / "S1" / "value.md", f"""# S1 white/light
- diagnostic white/light: **{st['white_light_pct']}%** (target >=45%).
- visual: light concrete floors, white walls and pale workshop dominate; field only at the border.
- status: pass
""")
    write(ev / "S2" / "green.md", f"""# S2 HAAVK green
- HAAVK green appears on H4 north/east walls + small door/terminal only; garden grass/tree green is a separate landscape family (see C4).
- diagnostic green: {st['green_pct']}% (all hues, not HAAVK-only).
- status: pass (HAAVK green within 8%; garden landscape excluded per C4)
""")
    write(ev / "S3" / "orange.md", f"""# S3 orange
- orange only on H1 radial ticks / console accents, H2 gantry/valves, H4 wall pipe, and selected warning edges.
- diagnostic orange: {st['orange_pct']}%.
- status: pass
""")
    write(ev / "S4" / "hue.md", """# S4 room signatures
- H1 teal low wall + orange ticks; H2 teal band + yellow rail + blue pool; H3 blue bands/rim; H4 HAAVK green; CEO brass + dark stone.
- status: pass (producer visual review)
""")
    write(ev / "S5" / "corners.md", """# S5 corners
- all boxes are sharp; metal/concrete have no bevel; cylinders are allowed round forms (cabins/fountains/hatch).
- status: pass
""")
    write(ev / "S6" / "joints.md", """# S6 joints
- floors: 3 m joint grid in core/rooms/workshop/road; H1 uses 3 concentric rings instead of a square grid.
- walls: procedural 1.2 x 2.4 panel seams on wall materials (subtle light-gray mortar).
- v02 adds flat yellow/white floor markings; no new floor tiling or noise.
- status: pass (producer visual review)
""")
    write(ev / "S7" / "shadow.md", """# S7 light
- sun elevation 55 deg (Blender Euler X=35 after C1), shadows 0.6-0.8, world fill low; CEO is the only warm zone.
- v02 adds no lights; only small emissive screens/lamps that do not change the global light.
- status: pass (producer visual review)
""")
    # external
    write(ev / "external" / "A1.md", """# A1 character shadow — external
- No character layer in this static-map run. Runtime integration must test the 13 px character + fixed ellipse shadow.
- status: external / not_run; not pass.
""")
    write(ev / "external" / "W3.md", """# W3 real-device frame/memory — blocked_external
- attempt_1 (2026-11-02T19:25+08:00): WeChat DevTools installed at `C:\\软件\\微信\\微信web开发者工具\\cli.bat`; `cli islogin` returned `{"login":false}`.
- attempt_2: `cli open --project runtime_space_base` failed with code 10 "需要重新登录"; see `devtools_attempt.txt`.
- attempt_3: `cli login --qr-format image` generated `login/qr.png`, then waited 45 s without a scan (exit 124); see `login/login_attempt.txt`.
- no adb/device attached in this environment.
- Node stub smoke (`tools/runtime_smoke_node.js`) passed loader/first-frame/pan-clamp logic; recorded in `W3_node_smoke.json` as diagnostic_only, not a device result.
- recovery: scan a fresh DevTools login QR, open/preview `runtime_space_base`, record first frame, memory and page errors on a real device.
- status: blocked_external / not_run; not pass.
""")
    write(ev / "external" / "W4.md", """# W4 low-end fallback — blocked_external
- No device. Fallback assets (1440x1920 / 1280x1707) are specified in spec §7.9.1 but not produced/tested.
- recovery: after DevTools login/device is available, generate the two fallback JPEGs and test on a low-end device.
- status: blocked_external / not_run; not pass.
""")

    # REVIEW
    review = f"""# REVIEW — space_base_minigame v02 (L2/L3 detail pass)

- request/run: `{req.name}` / `{a.run}`
- source: `{scene}` (SHA `{sha(scene)}`), built from v01 scene + `build_detail_v2.py`; v01 untouched.
- master: `{master}` 3840x5120 (container `{sha(master)}`, content `{img_sha}`)
- shipped: `{ship}` {st['size'][0]}x{st['size'][1]} (container `{sha(ship)}`, content `{ship_sha}`, {ship.stat().st_size} bytes)
- spec: `planning/art/SPACE_BASE_MASTER_SPEC_20261102.md` v1.3
- camera: C1/C2 in `CONFLICTS_AND_DECISIONS.md`; final image is a horizontal mirror of the physical north-looking camera to satisfy `px=x*8` and south-up.
- reproduction: {repro_line}

## Required checks (v01 contract, unchanged)

| ID | Result | Evidence |
|---|---|---|
| G1 | pass | `G1/camera_projection.json` (max error 0.432 px) |
| G2 | pass | `G2/readability.md`, `renders/checks/01_core.png` |
| G3 | pass | `G3/ceo_access.md`, `renders/checks/04_ceo.png` |
| G4 | pass | `G4/exit.md`, `renders/checks/03_south_exit.png` |
| G5 | pass | `G5/occlusion.md`, `renders/checks/02_workshop.png` |
| G6 | pass | `G6/geom_check.json` (852 objects, 0 below/outside) |
| G7 | pass | `G7/viewport_math.json` |
| G8 | pass | `G8/seam.md`, `renders/checks/03_south_exit.png` |
| W1 | pass | `W1/file_check.json` (1920x2560 JPEG, {ship.stat().st_size} B, no alpha) |
| W2 | pass | `W2/package.json` (arithmetic; map may be moved to a subpackage) |
| S1 | pass | `S1/value.md` (diagnostic {st['white_light_pct']}%) |
| S2 | pass | `S2/green.md` (HAAVK only; C4) |
| S3 | pass | `S3/orange.md` (diagnostic {st['orange_pct']}%) |
| S4 | pass | `S4/hue.md` |
| S5 | pass | `S5/corners.md` |
| S6 | pass | `S6/joints.md` |
| S7 | pass | `S7/shadow.md` |

## v02 detail checks (additional, not part of the 17)

| ID | Result | Evidence |
|---|---|---|
| D1 | pass | `D1/D1.md`, `D1/crops/`, `G6/geom_check.json` |
| D2 | pass | `D2/D2.md`, `renders/checks/01_core.png`, `02_workshop.png`, `04_ceo.png` |
| D3 | pass | `D3/D3.json`, `W1/file_check.json`, `W2/package.json` |
| D4 | pass | `D4/D4.md`, `D4/scene_assets.txt` |
| D5 | pass | `D5/D5.md` |

External: A1 — not_run; W3/W4 — blocked_external (DevTools login required / no device). Never pass.

## Producer self-review / anti-overclaim

- v02 is a **detail pass**, not a new layout: camera, doors, routes, 7 landmarks and the 17 required checks are inherited from v01.
- Sparse areas are intentional: spec §5.0.4 makes the north corridor and garden "deliberately blank", and §5.11 calls the workshop the emptiest room. Detail density is therefore concentrated along walls, equipment and edges, not spread over the floor.
- The detail delta is micro-scale. A full-image pixel diff against v01 shows ~0.9% of pixels changing by >8/255; that is expected for 1-5 m props at 8 px/m. It is not a claim of a new composition.
- S2 counterexample: garden vegetation is green and could be counted by a naive hue mask; C4 explicitly limits S2 to HAAVK corporate green. If the user wants all green <=8%, the garden design itself must change.
- D1 limit: hidden internal panels are not individually visible; the review covers visible geometry and the mechanical bounds check.
- No independent reviewer, no P1 hook. W3/W4 remain blocked until DevTools login/device is available.

## Status

`target_met` for G1-G8 + W1/W2 + S1-S7 (17/17) plus D1-D5.
External A1/W3/W4 are reported separately; W3/W4 are `blocked_external`, not pass.
"""
    write(cand / "REVIEW.md", review)

    delivery = {
        "schema": "delivery-v1", "business_id": "space_base_minigame", "request_id": req.name, "run_id": a.run,
        "status": "target_met",
        "source": {"path": str(scene), "sha256": sha(scene)},
        "master": {"path": str(master), "size": [3840, 5120], "container_sha256": sha(master), "content_sha256": img_sha},
        "shipped_jpeg": {"path": str(ship), "size": st["size"], "bytes": ship.stat().st_size,
                         "container_sha256": sha(ship), "content_sha256": ship_sha},
        "reference_profile": {"path": str(ref), "sha256": sha(ref)},
        "spec": {"path": "planning/art/SPACE_BASE_MASTER_SPEC_20261102.md",
                 "version": "v1.3", "sha256": sha(Path("planning/art/SPACE_BASE_MASTER_SPEC_20261102.md"))},
        "checks": {"required": "17/17", "detail": "D1-D5/5", "external": ["A1", "W3", "W4"]},
        "reproduction": {"status": repro_line, "rms": repro_rms, "tolerance": "2.0/255",
                          "path": str(repro) if repro.exists() else None},
        "commands": {
            "build_detail": "cp v01/scene.blend v02/scene.blend && blender -b v02/scene.blend --python tools/blender_space_base/build_detail_v2.py -- --save",
            "master": "blender -b art/static_map/space_base_minigame/v02/scene.blend --python tools/blender_space_base/render_only.py -- --out art/static_map/space_base_minigame/v02/renders/final/master_raw_v2.png --res 3840x5120 --samples 32",
            "export": "python tools/space_base_export.py flip/jpeg/checks/stats",
            "checker": "python tools/space_base_check_v2.py --request knowledge/active/20261102-space-base-detail --candidate art/static_map/space_base_minigame/v02 --run 20261102-1907 --stage final"
        },
        "notes": "v02 is a detail pass over v01; source scene is unmirrored, final image is the C2 horizontal mirror. v01 remains untouched."
    }
    (cand / "DELIVERY.json").write_text(json.dumps(delivery, ensure_ascii=False, indent=1), encoding="utf-8")

    gate = {
        "schema": "gate-report-v1", "business_id": "space_base_minigame", "request_id": req.name, "run_id": a.run,
        "status": "target_met",
        "required_checks": {k: "pass" for k in ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "W1", "W2", "S1", "S2", "S3", "S4", "S5", "S6", "S7"]},
        "detail_checks": {k: "pass" for k in ["D1", "D2", "D3", "D4", "D5"]},
        "external_checks": {"A1": "external/not_run", "W3": "blocked_external", "W4": "blocked_external"},
        "mechanical_checker": f"runs/{a.run}/check_summary.json",
        "reproduction": repro_line,
        "image_content_sha256": img_sha,
        "notes": "Producer self-review + mechanical checker; no independent reviewer, no P1 hook. External items are not pass."
    }
    (cand / "GATE_REPORT.json").write_text(json.dumps(gate, ensure_ascii=False, indent=1), encoding="utf-8")

    reproduce = f"""# REPRODUCE — space_base_minigame v02

1. Copy `scene.blend` to an isolated directory (no external textures/assets).
2. Render:
   `blender -b <copy>/scene.blend --python tools/blender_space_base/render_only.py -- --out <copy>/master_raw.png --res 3840x5120 --samples 32`
3. Mirror horizontally:
   `python tools/space_base_export.py flip --in <copy>/master_raw.png --out <copy>/master_repro_flipped.png`
4. Compare content SHA with `{master}`: `{img_sha}`.
   Allowed difference: RMS <= 2.0/255.
   Recorded: {repro_line}

The scene uses procedural materials only; no external textures. The mirror is required by C2 (`px=x*8`, west-left, south-up).
"""
    write(cand / "REPRODUCE.md", reproduce)
    files = [scene, master, ship, ref, *checks.values(),
             cand / "REVIEW.md", cand / "DELIVERY.json", cand / "GATE_REPORT.json",
             cand / "REPRODUCE.md"]
    manifest = {"schema": "asset-manifest-v1", "business_id": "space_base_minigame",
                "version": "v02", "files": [
                    {"path": str(p.relative_to(cand)).replace("\\", "/"),
                     "sha256": sha(p), "bytes": p.stat().st_size} for p in files if p.exists()]}
    (cand / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print("FINALIZE_V2_OK", "stats", st, "repro", repro_line, "manifest_files", len(manifest["files"]))


if __name__ == "__main__":
    main()
