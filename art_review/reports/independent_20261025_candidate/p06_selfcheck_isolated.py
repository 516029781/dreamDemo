__file__='C:\\软件\\鼠鼠\\delivery\\next_cycle\\T0\\p06_selfcheck.py'
__name__="__main__"
"""P06 self-check: build-log gate, audit aggregation, binding integration, PS wrapper, canvas capture."""
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TMP = ROOT / "art_review/reports/independent_20261025_candidate/fixtures_p06"
CANVAS = ROOT / "art_review/reports/independent_20261025_candidate/fixtures_p06_canvas"
PY = sys.executable


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wj(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    gate = load("build_log_gate", ROOT / "tools/art_gate/build_log_gate.py")
    harness = load("art_harness", ROOT / "tools/art_harness.py")
    checker = load("check_bindings", ROOT / "tools/art_gate/check_bindings.py")
    output = {"kind": "p06_selfcheck_audit_build_capture", "cases": [], "all_passed": False}
    ok = True

    def gate_case(name, lines, profile, exit_code, expect_status, expect_warning=False):
        nonlocal ok
        log = TMP / (name + ".log")
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = gate.check_log(log, profile, exit_code)
        passed = result["status"] == expect_status
        if expect_warning:
            passed = passed and bool(result["warnings"])
        output["cases"].append({"case": name, "exit": result["status"], "expected": expect_status,
                                "failures": result["failures"], "warnings": len(result["warnings"]),
                                "pass": passed})
        ok = ok and passed

    gate_case("cocos_ok_with_benign_noise", [
        "trackTimeEnd failed! missing track time",
        "Check build parameter x failed, and the default value will be used instead",
        "Error: Exit process with code:null, signal:SIGTERM in task build-script",
        "build Task (web-desktop) Finished in (17 s)ms",
    ], "cocos", 0, "pass", expect_warning=True)
    gate_case("cocos_failed_but_finished", [
        "Build Assets failed: missing resource",
        "build Task (web-desktop) Finished in (2 s)ms",
    ], "cocos", 0, "fail")
    gate_case("cocos_zero_exit_not_trusted_36", [
        "build Task (web-desktop) Finished in (17 s)ms",
    ], "cocos", 36, "fail")
    gate_case("blender_traceback_even_with_quit", [
        "Traceback (most recent call last):",
        "Blender quit",
    ], "blender", 0, "fail")
    gate_case("blender_ok", [
        "DELIVERED ENV006 blend=x glb=y png=z tris=12536",
        "Blender quit",
    ], "blender", 0, "pass")
    gate_case("verify_fail", ["VERIFY_RESULT=FAIL count=3"], "verify", 1, "fail")
    gate_case("missing_success_marker", ["Blender quit"], "cocos", 0, "fail")

    canvas_report = json.loads((CANVAS / "canvas_selftest.json").read_text(encoding="utf-8-sig"))
    canvas_ok = (canvas_report["pixel_is_canvas_content"] is True
                 and canvas_report["page_shot_used"] is False
                 and canvas_report["metadata"]["output"]["width"] == canvas_report["metadata"]["backing_width"]
                 and canvas_report["metadata"]["output"]["height"] == canvas_report["metadata"]["backing_height"]
                 and canvas_report["css_differs_from_backing"] is True)
    output["canvas_capture"] = {"pass": canvas_ok, "metadata": canvas_report["metadata"],
                                "center_pixel": canvas_report["center_pixel"]}
    ok = ok and canvas_ok

    audit = harness.Harness(ROOT).audit("art_complete")
    checks = {item["check"] for item in audit["failed_checks"]}
    review = audit.get("latest_independent_review") or {}
    audit_ok = (audit["status"] == "blocked"
                and audit["contract"]["version"] == "1.3.0"
                and audit["contract"]["vnext_contract"]["effective"] is False
                and {"gate:H02", "gate:H07", "active_manifest_stage"} <= {item["check"] for item in audit["failed_checks"] + audit["pending_checks"]}
                and "independent_20261024" in review.get("path", "")
                and bool(audit["next_actions"]))
    output["audit"] = {"pass": audit_ok, "status": audit["status"],
                       "failed_count": len(audit["failed_checks"]),
                       "pending_count": len(audit["pending_checks"]),
                       "review": review.get("path"),
                       "failed_sample": sorted(checks)[:10],
                       "next_actions": len(audit["next_actions"])}
    ok = ok and audit_ok

    empty_results = {"results_version": "vnext.behavior_results/1.0.0", "stage": "art_complete",
                     "build_id": "build-1", "generated_at": "2026-10-25T00:00:00Z", "results": []}
    empty_path = TMP / "behavior_empty.json"
    wj(empty_path, empty_results)
    audit_quality = harness.Harness(ROOT).audit("art_complete", quality_results=str(empty_path))
    pending = {item["check"] for item in audit_quality["pending_checks"]}
    quality_ok = {"quality:Q01", "quality:Q09", "quality:capture_binding"} <= pending
    output["audit_quality_integration"] = {"pass": quality_ok, "pending_sample": sorted(pending)[:12]}
    ok = ok and quality_ok

    sample = CANVAS / "binding_sample"
    sample.mkdir(parents=True, exist_ok=True)
    (sample / "source.blend").write_bytes(b"BLENDER-p06-binding-sample")
    (sample / "export.glb").write_bytes(b"glTF-p06-binding-sample")
    (sample / "build.log").write_bytes(b"[selftest] BUILD_OK\n")
    canvas_png = CANVAS / "canvas_selftest.png"
    binding = {
        "binding_version": "vnext.capture_binding/1.0.0", "binding_id": "cap-p06-selftest",
        "stage": "art_complete", "created_at": "2026-10-25T00:00:00Z",
        "backend": {"name": "puppeteer-canvas-selftest", "version": "1.0"},
        "viewport": {"browser_width": 800, "browser_height": 600, "device_pixel_ratio": 2},
        "canvas": {"selector": "#GameCanvas",
                   "css_rect": {"x": 0, "y": 88.875, "width": 320, "height": 180},
                   "backing_width": 640, "backing_height": 360,
                   "capture_method": "element_screenshot", "page_screenshot": False},
        "camera": {"node": "selftest-canvas", "position": [0, 0, 0], "rotation": [0, 0, 0],
                   "fov": 45, "clip_time": None},
        "sources": [{"role": "synthetic_source", "path": sample.relative_to(ROOT).as_posix() + "/source.blend",
                     "sha256": sha(sample / "source.blend")}],
        "exports": [{"role": "synthetic_export", "path": sample.relative_to(ROOT).as_posix() + "/export.glb",
                     "sha256": sha(sample / "export.glb")}],
        "shared_inputs": [],
        "build": {"build_id": "selftest-build", "log_path": sample.relative_to(ROOT).as_posix() + "/build.log",
                  "log_sha256": sha(sample / "build.log"), "result": "success"},
        "output": {"path": canvas_png.relative_to(ROOT).as_posix(), "sha256": sha(canvas_png),
                   "width": 640, "height": 360},
        "notes": ["Synthetic canvas selftest binding; not game visual evidence."],
    }
    binding_path = sample / "binding.json"
    wj(binding_path, binding)
    verified = checker.verify_binding(ROOT, binding_path, ROOT / "art_review/vnext/capture_binding.schema.json")
    audit_binding = harness.Harness(ROOT).audit("art_complete", bindings=binding_path.relative_to(ROOT).as_posix())
    binding_ok = verified["verified"] is True and audit_binding["capture_bindings"]["status"] == "pass"
    output["audit_binding_integration"] = {"pass": binding_ok, "verified_checks": verified["checks"],
                                           "audit_status": audit_binding["capture_bindings"]["status"]}
    ok = ok and binding_ok

    ps = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                         str(ROOT / "run-art-harness.ps1"), "-Command", "audit", "-Stage", "art_complete",
                         "-Out", str(TMP / "ps_audit.json")],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    ps_ok = ps.returncode == 3 and "EXIT_CODE 3" in ps.stdout
    output["powershell_wrapper"] = {"pass": ps_ok, "exit": ps.returncode,
                                    "tail": ps.stdout.strip().splitlines()[-1] if ps.stdout.strip() else ""}
    ok = ok and ps_ok

    dry = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                          str(ROOT / "tools/blender/run_courtyard_build.ps1"),
                          "-Stage", "env_tree,map001", "-DryRun"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    dry_lines = [line for line in dry.stdout.splitlines() if line.startswith("DRYRUN")]
    dry_ok = dry.returncode == 0 and len(dry_lines) == 2
    output["directed_build_dry_run"] = {"pass": dry_ok, "exit": dry.returncode,
                                        "selected": [line.split()[1] for line in dry_lines]}
    ok = ok and dry_ok

    output["all_passed"] = bool(ok)
    if TMP.exists():
        shutil.rmtree(TMP)
    out_path = ROOT / "art_review/reports/independent_20261025_candidate/p06_replay.json"
    wj(out_path, output)
    print(json.dumps({"all_passed": output["all_passed"], "cases": len(output["cases"]),
                      "output": str(out_path), "sha256": sha(out_path)}, ensure_ascii=False))
    return 0 if output["all_passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
