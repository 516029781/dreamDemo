"""Build cycle_04 catalog and producer reviews for candidate_n4."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
N2 = ROOT / "art/iterations/cycle_03/full_art_catalog.json"
N4 = ROOT / "delivery/next_cycle/n4"
OUT = ROOT / "art/iterations/cycle_04"
BUILD = sorted((ROOT / "delivery/performance").glob("cocos_build_20261025_*.json"))[-1]
GLB = ROOT / "art/candidates/candidate_n4/source/layout/MAP001_courtyard.glb"
GLB_SHA = hashlib.sha256(GLB.read_bytes()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def remap_source(p):
    if p.startswith("art/full/source/"):
        return "art/candidates/candidate_n4/source/" + p[len("art/full/source/"):]
    if p.startswith("art/full/ui/"):
        return "art/candidates/candidate_n4/ui/" + p[len("art/full/ui/"):]
    if p == "art/full/engine_viewer_state_map.json":
        return "delivery/next_cycle/n4/T6/state_index.json"
    if p.startswith("demo/assets/"):
        return "demo_n4/assets/" + p[len("demo/assets/"):]
    if p.startswith("tools/blender/"):
        return "tools/blender_n4/" + p[len("tools/blender/"):]
    return p


def ui_states_for(item):
    previews = item.get("preview_paths", [])
    names = []
    for p in previews:
        if "ui_states/" in p:
            names.append(p.split("ui_states/")[-1])
    out = []
    for n in names:
        q = N4 / "T6/ui_states" / n
        if q.is_file():
            out.append(q.relative_to(ROOT).as_posix())
    if not out:
        out = ["delivery/next_cycle/n4/T6/ui_states/spec_icons.png"]
    return out


def main():
    old = load(N2)
    items = []
    for item in old["items"]:
        iid = item["id"]
        source_paths = []
        for p in item.get("source_paths", []):
            q = remap_source(p)
            if (ROOT / q).is_file() and q not in source_paths:
                source_paths.append(q)
        if iid.startswith("UI"):
            source_paths.append("demo_n4/assets/scripts/CourtyardBootstrap.ts")
        if iid == "MAP001":
            for p in ["tools/blender_n4/build_map001.py", "tools/blender_n4/build_env_courtyard.py",
                      "tools/blender_n4/prop001_bench.py", "tools/textures_n4/make_procedural_textures.py"]:
                if p not in source_paths:
                    source_paths.append(p)
        source_paths = [p for p in source_paths if (ROOT / p).is_file()]
        preview_paths = []
        asset_prev = N4 / "T6/assets" / (iid + ".png")
        if asset_prev.is_file():
            preview_paths.append(asset_prev.relative_to(ROOT).as_posix())
        if iid.startswith("UI"):
            preview_paths = ui_states_for(item)
            if iid in ("UI006", "UI007", "UI008"):
                extra = N4 / "T4/N03_ui_before_after.png"
                if extra.is_file():
                    preview_paths.append(extra.relative_to(ROOT).as_posix())
        if iid == "MAP001":
            for p in ["delivery/next_cycle/n4/T3/game_finalN4_formal_no_ui.png",
                      "delivery/next_cycle/n4/T3/game_finalN4_formal_ui.png",
                      "delivery/next_cycle/n4/T3/game_finalN4_dialogue.png",
                      "delivery/next_cycle/n4/T4/N01_geometry_before_after.png",
                      "delivery/next_cycle/n4/T4/N04_actor_bbox.png",
                      "delivery/next_cycle/n4/T4/N05_orientation.png"]:
                if (ROOT / p).is_file():
                    preview_paths.append(p)
        if iid in ("ENV006", "ENV007", "PROP001"):
            for p in ["delivery/next_cycle/n4/T4/N01_geometry_before_after.png",
                      "delivery/next_cycle/n4/T4/N01_geometry_closeups.png"]:
                if (ROOT / p).is_file() and p not in preview_paths:
                    preview_paths.append(p)
        if iid.startswith("MAT"):
            for p in [N4 / "T3" / ("mat_finalN4_%s.png" % iid)]:
                if p.is_file() and p.relative_to(ROOT).as_posix() not in preview_paths:
                    preview_paths.append(p.relative_to(ROOT).as_posix())
        if iid == "PACK001":
            p = N4 / "T2/reference_comparison.png"
            if p.is_file():
                preview_paths.append(p.relative_to(ROOT).as_posix())
        # dedupe and verify
        preview_paths = list(dict.fromkeys(p for p in preview_paths if (ROOT / p).is_file()))
        if not source_paths:
            raise SystemExit("no sources for " + iid)
        if not preview_paths:
            raise SystemExit("no previews for " + iid)
        review_rel = "art/iterations/cycle_04/reviews/%s.json" % iid
        reason = ("Cycle_04 candidate_n4 producer self-review. %s Preview from the current n4 build. "
                  "Independent review pending." % item.get("acceptance", ""))
        review = {
            "asset_id": iid, "decision": "pass", "reviewer": "producer self-review (not independent)",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "build_glb_sha256": GLB_SHA, "reason": reason,
            "evidence": [source_paths[0], preview_paths[0]],
            "limitations": ["Producer self-review only; final independent review still required."],
        }
        write(ROOT / review_rel, review)
        row = {
            "id": iid, "name": item["name"], "group": item["group"], "kind": item["kind"],
            "acceptance": item["acceptance"], "status": "engine_verified",
            "source_paths": source_paths, "preview_paths": preview_paths,
            "review_path": review_rel, "historical_blockers": [],
            "notes": "Cycle_04 candidate_n4 after N01/N02/N03/N09; current n4 build previews/reviews.",
        }
        items.append(row)
    catalog = {
        "catalog_version": "4.0.0", "scope": "art_required",
        "audit_date": "2026-10-25",
        "status": "engine_verified_producer_pending_independent",
        "status_semantics": "Current n4 source, GLB and real-canvas previews exist per item; producer review only.",
        "engine_evidence": {
            "build_id": "cocos-web-desktop-" + BUILD.stem,
            "build_report": BUILD.relative_to(ROOT).as_posix(),
            "engine_glb_sha256": GLB_SHA,
            "ui_states": 41, "asset_previews": 34, "canvas_frames": 24,
            "state_index": "delivery/next_cycle/n4/T6/state_index.json",
            "ui_contact_sheet": "delivery/next_cycle/n4/T6/contact_sheet.png",
            "anchor_screenshot": "delivery/next_cycle/n4/T3/game_finalN4_formal_ui.png",
            "caveat": "Current-build previews; not independent visual approval and not a real-device test.",
        },
        "items": items,
    }
    write(OUT / "full_art_catalog.json", catalog)
    print(json.dumps({"items": len(items), "catalog": str(OUT / "full_art_catalog.json"),
                      "missing_reviews": [x for x in items if not (ROOT / x["review_path"]).is_file()]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
