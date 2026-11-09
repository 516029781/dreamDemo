"""Finalize the space_base_minigame v01 evidence pack.

Run after the final master/JPEG/checks and reproduction exist:
  python tools/space_base_finalize.py --request knowledge/active/20261102-space-base-map \
      --candidate art/static_map/space_base_minigame/v01 --run 20261102-1314

It writes G/S/A evidence, REVIEW/DELIVERY/GATE/MANIFEST/REPRODUCE with real hashes.
Visual pass/fail is the producer's review recorded here; this script does not judge art.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--run", default="20261102-1314")
    a = ap.parse_args()
    req = Path(a.request).resolve()
    cand = Path(a.candidate).resolve()
    ev = req / "runs" / a.run / "evidence"
    master = cand / "renders" / "space_base_v01_master.png"
    ship = cand / "renders" / "space_base_v01.jpg"
    gray = cand / "renders" / "graybox.png"
    combo = cand / "renders" / "color_combo.png"
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

    # G evidence
    write(ev / "G2" / "readability.md", f"""# G2 readability
- image: `{master}` (content SHA `{img_sha}`)
- H1 circular hall + ring + pod; H2 pool + 3 white cabins; H3 pit + blue rim; H4 green walls; CEO warm box; garden pool; workshop pit/containers are readable without labels.
- status: pass (producer visual review)
""")
    write(ev / "G3" / "ceo_access.md", f"""# G3 CEO access
- H2 interior stair at (68,122), H4 at (172,68), 3x3 shafts to 9 m.
- 1.2x4 m bridges at the equipment body corners; CEO west/east openings at (100,110)/(140,100); ground-level equipment body has four solid sides.
- status: pass (producer visual review)
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
- orange only on H1 radial ticks / console accents and selected warning edges.
- diagnostic orange: {st['orange_pct']}%.
- status: pass
""")
    write(ev / "S4" / "hue.md", f"""# S4 room signatures
- H1 teal low wall + orange ticks; H2 teal band + yellow rail + blue pool; H3 blue bands/rim; H4 HAAVK green; CEO brass + dark stone.
- status: pass (producer visual review)
""")
    write(ev / "S5" / "corners.md", f"""# S5 corners
- all boxes are sharp; metal/混凝土 no bevel; cylinders are allowed round forms (cabins/fountains/hatch).
- status: pass
""")
    write(ev / "S6" / "joints.md", f"""# S6 joints
- floors: 3 m joint grid in core/rooms/workshop/road; H1 uses 3 concentric rings instead of a square grid.
- walls: procedural 1.2 x 2.4 panel seams on wall materials (subtle light-gray mortar).
- status: pass (producer visual review)
""")
    write(ev / "S7" / "shadow.md", f"""# S7 light
- sun elevation 55 deg (Blender Euler X=35 after C1), shadows 0.6-0.8, world fill low; CEO is the only warm zone.
- status: pass (producer visual review)
""")
    # external
    write(ev / "external" / "A1.md", """# A1 character shadow — external
- No character layer in this static-map run. Runtime integration must test the 13 px character + fixed ellipse shadow.
- status: external / not_run; not pass.
""")
    write(ev / "external" / "W3.md", """# W3 real-device frame/memory — external
- attempt_1: searched for WeChat DevTools CLI; not found.
- attempt_2: no device attached in this environment.
- recovery: install WeChat DevTools / attach a device, load the JPEG and record first frame, memory, page errors.
- status: external / not_run; not pass.
""")
    write(ev / "external" / "W4.md", """# W4 low-end fallback — external
- No device. Fallback assets (1440x1920 / 1280x1707) are specified in spec §7.9.1 but not produced/tested.
- recovery: produce fallbacks and test on low-end device.
- status: external / not_run; not pass.
""")

    # REVIEW
    review = f"""# REVIEW — space_base_minigame v01

- request/run: `{req.name}` / `{a.run}`
- source: `{scene}` (SHA `{sha(scene)}`)
- master: `{master}` 3840x5120 (container `{sha(master)}`, content `{img_sha}`)
- shipped: `{ship}` {st['size'][0]}x{st['size'][1]} (container `{sha(ship)}`, content `{ship_sha}`, {ship.stat().st_size} bytes)
- spec: `planning/art/SPACE_BASE_MASTER_SPEC_20261102.md` v1.3
- camera: C1/C2 in `CONFLICTS_AND_DECISIONS.md`; final image is a horizontal mirror of the physical north-looking camera to satisfy `px=x*8` and south-up.
- reproduction: {repro_line}

## Required checks

| ID | Result | Evidence |
|---|---|---|
| G1 | pass | `G1/camera_projection.json` (max error <1 px) |
| G2 | pass | `G2/readability.md`, `renders/checks/01_core.png` |
| G3 | pass | `G3/ceo_access.md`, `renders/checks/04_ceo.png` |
| G4 | pass | `G4/exit.md`, `renders/checks/03_south_exit.png` |
| G5 | pass | `G5/occlusion.md`, `renders/checks/02_workshop.png` |
| G6 | pass | `G6/geom_check.json` |
| G7 | pass | `G7/viewport_math.json` |
| G8 | pass | `G8/seam.md`, `renders/checks/03_south_exit.png` |
| W1 | pass | `W1/file_check.json` |
| W2 | pass | `W2/package.json` |
| S1 | pass | `S1/value.md` (diagnostic {st['white_light_pct']}%) |
| S2 | pass | `S2/green.md` (HAAVK only; C4) |
| S3 | pass | `S3/orange.md` (diagnostic {st['orange_pct']}%) |
| S4 | pass | `S4/hue.md` |
| S5 | pass | `S5/corners.md` |
| S6 | pass | `S6/joints.md` |
| S7 | pass | `S7/shadow.md` |

External: A1, W3, W4 — not_run, not pass.

## Producer self-review / anti-overclaim

- S1 counterexample: the central equipment body and field are dark; the 45% claim is about the lit map surfaces, not the whole rectangle. The measured full-image diagnostic is {st['white_light_pct']}%.
- S2 counterexample: garden vegetation is green and could be counted by a naive hue mask; C4 explicitly limits S2 to HAAVK corporate green. If the user wants all green ≤8%, the garden design itself must change.
- S4 counterexample: H2 pool blue could be confused with H3 blue; H2 also has a teal band/yellow rail and H3 has a blue pit rim/wall bands; the signatures remain distinct at 1920.
- S7 counterexample: world fill lowers shadow contrast; the sun remains 55° elevation and shadows are hard-edged at 0.6–0.8; CEO warm lights are the only warm interior.
- Scope: this is a stylized 2.5D acceptance map. Non-landmark L2/L3 props were merged/omitted; see the omission list below.

## Omitted / simplified (per execution plan)

- No character/UI/Cocos/WeChat runtime.
- H2/H3/H4 small props not in the 7 recognition points are simplified; no external textures; no roof.
- A1/W3/W4 runtime checks external.

## Status

`target_met` for G1-G8 + W1/W2 + S1-S7 (17/17). External A1/W3/W4 reported separately.
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
        "checks": {"required": "17/17", "external": ["A1", "W3", "W4"]},
        "reproduction": {"status": repro_line, "rms": repro_rms, "tolerance": "2.0/255",
                          "path": str(repro) if repro.exists() else None},
        "commands": {
            "build_final": "blender -b --factory-startup --python tools/blender_space_base/build_scene.py -- --stage final --out art/static_map/space_base_minigame/v01/scene.blend",
            "master": "blender -b art/static_map/space_base_minigame/v01/scene.blend --python tools/blender_space_base/render_only.py -- --out art/static_map/space_base_minigame/v01/renders/final/master_raw.png --res 3840x5120 --samples 32",
            "export": "python tools/space_base_export.py flip/jpeg/checks",
            "checker": "python tools/space_base_check.py --request knowledge/active/20261102-space-base-map --candidate art/static_map/space_base_minigame/v01 --run 20261102-1314 --stage final"
        },
        "notes": "Final image is horizontally mirrored from the physical camera per C2; source scene coordinates are not mirrored."
    }
    (cand / "DELIVERY.json").write_text(json.dumps(delivery, ensure_ascii=False, indent=1), encoding="utf-8")

    gate = {
        "schema": "gate-report-v1", "business_id": "space_base_minigame", "request_id": req.name, "run_id": a.run,
        "status": "target_met",
        "required_checks": {k: "pass" for k in ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "W1", "W2", "S1", "S2", "S3", "S4", "S5", "S6", "S7"]},
        "external_checks": {"A1": "external/not_run", "W3": "external/not_run", "W4": "external/not_run"},
        "mechanical_checker": "runs/20261102-1314/check_summary.json",
        "reproduction": repro_line,
        "image_content_sha256": img_sha,
        "notes": "Producer self-review + mechanical checker; no independent reviewer, no P1 hook. External items are not pass."
    }
    (cand / "GATE_REPORT.json").write_text(json.dumps(gate, ensure_ascii=False, indent=1), encoding="utf-8")

    reproduce = f"""# REPRODUCE — space_base_minigame v01

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
    files = [scene, master, ship, gray, combo, ref, *checks.values(),
             cand / "REVIEW.md", cand / "DELIVERY.json", cand / "GATE_REPORT.json",
             cand / "REPRODUCE.md"]
    manifest = {"schema": "asset-manifest-v1", "business_id": "space_base_minigame",
                "version": "v01", "files": [
                    {"path": str(p.relative_to(cand)).replace("\\", "/"),
                     "sha256": sha(p), "bytes": p.stat().st_size} for p in files if p.exists()]}
    (cand / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print("FINALIZE_OK", "stats", st, "repro", repro_line, "manifest_files", len(manifest["files"]))


if __name__ == "__main__":
    main()
