"""Regression tests for gate bypasses, using synthetic files, never production art."""
import base64
import copy
import hashlib
import hmac
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

spec = importlib.util.spec_from_file_location("art_harness", Path(__file__).with_name("art_harness.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

ROOT = Path(__file__).resolve().parents[1]


def load_gate(name):
    gate_spec = importlib.util.spec_from_file_location(name, ROOT / "tools/art_gate" / (name + ".py"))
    gate_module = importlib.util.module_from_spec(gate_spec)
    gate_spec.loader.exec_module(gate_module)
    return gate_module


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_bytes(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(data)


def big_png(width=64, height=36):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    raw = (b"\x00" + b"\x00\x00\x00\x00" * width) * height
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def png():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"\0\0\0\0\0")) + chunk(b"IEND", b"")


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "art_review").mkdir()
        (self.root / "src.skel").write_bytes(b"test-skeleton")
        self.source_hash = module.digest(self.root / "src.skel")
        self.contract = {
            "production_policy": {"allowed_methods": ["reference_spine", "blender_editable", "svg_editable"]},
            "locked_sources": [{"path": "src.skel", "sha256": self.source_hash}],
            "active_manifest": "manifest.json",
            "stages": {"character_playback": {
                "required_roles": ["clip_inventory", "idle_preview", "move_preview", "reference_comparison", "runtime_log"],
                "review_gates": ["H09"], "cards": ["CHAR"]}}
        }
        self.rubric = {"rubric_version": "test-1", "minimum_dimension": 2, "minimum_core_dimension": 3,
                       "pass_total": 85, "cards": {"CHAR": [{"id": "identity", "weight": 100, "core": True}]}}
        module.write_json(self.root / "art_review/harness_contract.json", self.contract)
        module.write_json(self.root / "art_review/rubric.json", self.rubric)
        module.write_json(self.root / "clips.json", {
            "source_skeleton_sha256": self.source_hash, "runtime": {"name": "test", "version": "3.8"},
            "extraction_method": "runtime_parse", "animations": [{"name": "Move", "duration": 1.0}],
            "mapping": {"idle": "Move", "move": "Move"}})
        (self.root / "idle.png").write_bytes(png())
        (self.root / "comparison.png").write_bytes(png())
        (self.root / "move.gif").write_bytes(base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"))
        (self.root / "runtime.txt").write_text("synthetic fixture, not production playback", encoding="utf-8")
        self.artifacts = {"character_mode": "reference_spine", "production_methods": ["reference_spine"], "artifacts": [
            {"role": role, "path": path} for role, path in [
                ("clip_inventory", "clips.json"), ("idle_preview", "idle.png"),
                ("move_preview", "move.gif"), ("reference_comparison", "comparison.png"), ("runtime_log", "runtime.txt")]]}
        self.h = module.Harness(self.root)
        self.manifest = self.h.prepare("character_playback", self.artifacts)
        self.mp = self.root / "manifest.json"
        module.write_json(self.mp, self.manifest)
        self.review = {"manifest_sha256": module.digest(self.mp), "contract_sha256": self.h.contract_digest(),
                       "rubric_version": "test-1", "review_scope": "character_playback",
                       "reviewer": {"id": "test-reviewer", "mode": "independent"},
                       "gates": {"H09": {"status": "pass", "reason": "fixture", "evidence": ["comparison.png"]}},
                       "cards": {"CHAR": {"dimensions": [{"id": "identity", "score": 4, "reason": "fixture", "evidence": ["comparison.png"]}]}},
                       "defects": []}
        self.rp = self.root / "review.json"
        module.write_json(self.rp, self.review)

    def test_mechanical_pass_never_accepts_without_review(self):
        result = self.h.verify(self.mp)
        self.assertEqual(result["status"], "needs_review")
        self.assertFalse(result["accepted"])

    def test_direct_image_generation_route_is_rejected(self):
        self.artifacts["production_methods"].append("ai_image")
        with self.assertRaisesRegex(module.GateError, "generation is disabled"):
            self.h.prepare("character_playback", self.artifacts)

    def test_missing_production_method_is_rejected(self):
        self.artifacts.pop("production_methods")
        with self.assertRaisesRegex(module.GateError, "production_methods"):
            self.h.prepare("character_playback", self.artifacts)

    def test_flat_background_cannot_be_map_source(self):
        with self.assertRaisesRegex(module.GateError, "not a generated background"):
            self.h.inspect({"role": "map_editable_source", "path": "comparison.png"})

    def test_renamed_png_cannot_be_blender_source(self):
        (self.root / "fake.blend").write_bytes(png())
        with self.assertRaisesRegex(module.GateError, "renamed image"):
            self.h.inspect({"role": "map_editable_source", "path": "fake.blend"})

    def test_image_only_svg_is_not_editable_ui(self):
        (self.root / "fake.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="picture.png"/></svg>', encoding="utf-8")
        with self.assertRaisesRegex(module.GateError, "image wrapping"):
            self.h.inspect({"role": "ui_editable_source", "path": "fake.svg"})

    def test_native_svg_ui_is_accepted(self):
        (self.root / "ui.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L4 4"/></svg>', encoding="utf-8")
        self.assertEqual(self.h.inspect({"role": "ui_editable_source", "path": "ui.svg"})["role"], "ui_editable_source")

    def setup_catalog(self):
        self.h.contract["expected_art_ids"] = ["ASSET01"]
        (self.root / "module.blend").write_bytes(b"BLENDER-test-native-fixture")
        module.write_json(self.root / "item_review.json", {"asset_id": "ASSET01", "decision": "pass", "reason": "synthetic fixture only", "evidence": ["comparison.png"]})
        self.catalog = {"items": [{"id": "ASSET01", "status": "engine_verified", "source_paths": ["module.blend"],
                                   "preview_paths": ["comparison.png"], "review_path": "item_review.json"}]}
        module.write_json(self.root / "catalog.json", self.catalog)
        return [{"role": "full_art_catalog", "path": "catalog.json"}]

    def test_full_catalog_missing_item_is_rejected(self):
        rows = self.setup_catalog()
        self.h.contract["expected_art_ids"].append("ASSET02")
        with self.assertRaisesRegex(module.GateError, "exact expected IDs"):
            self.h.catalog_check(rows)

    def test_full_catalog_unfinished_item_is_rejected(self):
        rows = self.setup_catalog()
        self.catalog["items"][0]["status"] = "candidate"
        module.write_json(self.root / "catalog.json", self.catalog)
        with self.assertRaisesRegex(module.GateError, "Unfinished"):
            self.h.catalog_check(rows)

    def test_full_catalog_review_is_required(self):
        rows = self.setup_catalog()
        module.write_json(self.root / "item_review.json", {"asset_id": "ASSET01", "decision": "pending"})
        with self.assertRaisesRegex(module.GateError, "not passed"):
            self.h.catalog_check(rows)

    def test_full_catalog_empty_pass_claim_is_rejected(self):
        rows = self.setup_catalog()
        module.write_json(self.root / "item_review.json", {"asset_id": "ASSET01", "decision": "pass"})
        with self.assertRaisesRegex(module.GateError, "bound preview evidence"):
            self.h.catalog_check(rows)

    def test_catalog_dependency_change_invalidates_snapshot(self):
        self.setup_catalog()
        self.h.contract["stages"]["art_complete"] = copy.deepcopy(self.h.contract["stages"]["character_playback"])
        self.h.contract["stages"]["art_complete"]["required_roles"].append("full_art_catalog")
        artifacts = copy.deepcopy(self.artifacts)
        artifacts["production_methods"] += ["blender_editable", "svg_editable"]
        artifacts["artifacts"].append({"role": "full_art_catalog", "path": "catalog.json"})
        manifest = self.h.prepare("art_complete", artifacts)
        self.h.check_manifest(manifest)
        (self.root / "module.blend").write_bytes(b"BLENDER-edited-after-review")
        with self.assertRaisesRegex(module.GateError, "catalog sources"):
            self.h.check_manifest(manifest)

    def test_self_review_cannot_release(self):
        self.review["reviewer"]["mode"] = "self"
        with self.assertRaises(module.GateError):
            self.h.check_review(self.mp, self.manifest, self.review)

    def test_all_threes_is_75_not_85(self):
        self.review["cards"]["CHAR"]["dimensions"][0]["score"] = 3
        with self.assertRaisesRegex(module.GateError, "75.0"):
            self.h.check_review(self.mp, self.manifest, self.review)

    def test_boolean_is_not_score(self):
        self.review["cards"]["CHAR"]["dimensions"][0]["score"] = True
        with self.assertRaises(module.GateError):
            self.h.check_review(self.mp, self.manifest, self.review)

    def test_artifact_change_invalidates_review(self):
        (self.root / "runtime.txt").write_text("edited", encoding="utf-8")
        with self.assertRaisesRegex(module.GateError, "changed"):
            self.h.check_manifest(self.manifest)

    def test_changed_contract_invalidates_snapshot(self):
        self.h.contract["contract_version"] = "changed"
        with self.assertRaisesRegex(module.GateError, "Stale"):
            self.h.check_manifest(self.manifest)

    def test_locked_skeleton_tampering(self):
        (self.root / "src.skel").write_bytes(b"replacement")
        with self.assertRaises(module.GateError):
            self.h.check_manifest(self.manifest)

    def test_escape_is_rejected(self):
        with self.assertRaisesRegex(module.GateError, "escapes"):
            self.h.file("../outside.png")

    def test_string_scan_is_not_runtime_inventory(self):
        inv = module.read_json(self.root / "clips.json")
        inv["extraction_method"] = "binary_strings"
        module.write_json(self.root / "clips.json", inv)
        with self.assertRaisesRegex(module.GateError, "runtime enumeration"):
            self.h.prepare("character_playback", self.artifacts)

    def test_open_major_defect_blocks(self):
        self.review["defects"] = [{"severity": "major", "status": "open"}]
        with self.assertRaises(module.GateError):
            self.h.check_review(self.mp, self.manifest, self.review)

    def test_unbound_review_evidence_blocks(self):
        self.review["gates"]["H09"]["evidence"] = ["imaginary.png"]
        with self.assertRaises(module.GateError):
            self.h.check_review(self.mp, self.manifest, self.review)

    def test_independent_label_is_insufficient_without_controller(self):
        self.assertEqual(self.h.verify(self.mp, self.rp)["status"], "needs_controller_attestation")

    def test_legacy_manifest_integrity_detects_change(self):
        legacy = self.root / "art/phase1/a_stage/reviews/A_asset_manifest.json"
        module.write_json(legacy, {"artifacts": [{"path": "idle.png", "sha256": module.digest(self.root / "idle.png")}]})
        self.assertEqual(self.h.audit()["legacy_artifact_integrity"]["failures"], [])
        (self.root / "idle.png").write_bytes(b"changed")
        self.assertEqual(len(self.h.audit()["legacy_artifact_integrity"]["failures"]), 1)

    def test_valid_controller_signature_and_forgery(self):
        key = "synthetic-test-key-" * 3
        binding = self.h.binding(self.mp, self.rp)
        attestation = {"binding": binding, "signature": hmac.new(key.encode(), module.canonical(binding), hashlib.sha256).hexdigest()}
        ap = self.root / "attestation.json"
        module.write_json(ap, attestation)
        with patch.dict(os.environ, {"ART_HARNESS_REVIEW_KEY": key}):
            self.assertTrue(self.h.verify(self.mp, self.rp, ap)["accepted"])
            attestation["signature"] = "0" * 64
            module.write_json(ap, attestation)
            with self.assertRaisesRegex(module.GateError, "Invalid controller"):
                self.h.verify(self.mp, self.rp, ap)


    def test_deferred_minor_with_accepted_reason_is_allowed(self):
        self.review["defects"] = [{"id": "D1", "severity": "minor", "status": "deferred",
                                   "accepted_reason": "tracked for next cycle"}]
        totals = self.h.check_review(self.mp, self.manifest, self.review)
        self.assertEqual(totals, {"CHAR": 100.0})

    def test_deferred_minor_without_reason_is_rejected(self):
        self.review["defects"] = [{"id": "D1", "severity": "minor", "status": "deferred"}]
        with self.assertRaisesRegex(module.GateError, "Unresolved defect"):
            self.h.check_review(self.mp, self.manifest, self.review)

    def test_boolean_previous_passed_certificate_rejected(self):
        cert = {key: {} for key in module.CERTIFICATE_FIELDS}
        cert["previous_passed"] = True
        cert_path = self.root / "cert_boolean.json"
        module.write_json(cert_path, cert)
        with self.assertRaisesRegex(module.GateError, "schema exactly"):
            self.h.certificate_check(cert_path)

    def test_consumption_mismatch_is_rejected(self):
        current = {"artifacts": [{"role": "idle_preview", "sha256": "a" * 64}]}
        previous = {"artifacts": [{"role": "idle_preview", "sha256": "b" * 64}]}
        with self.assertRaisesRegex(module.GateError, "differ from the certified"):
            self.h.consumption_check(current, [("character_playback", previous)])

    def test_consumption_without_shared_artifact_is_rejected(self):
        current = {"artifacts": [{"role": "scene_screenshot", "sha256": "a" * 64}]}
        previous = {"artifacts": [{"role": "idle_preview", "sha256": "b" * 64}]}
        with self.assertRaisesRegex(module.GateError, "does not consume any artifact"):
            self.h.consumption_check(current, [("character_playback", previous)])

    def test_cli_exit_code_three_when_review_missing(self):
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", str(ROOT / "tools/art_harness.py"), "verify",
             "--manifest", str(self.mp), "--root", str(self.root),
             "--contract", str(self.root / "art_review/harness_contract.json")],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "needs_review")


class QualityGateTests(unittest.TestCase):
    ROLES = {
        "Q01": ["no_ui_shot", "with_ui_shot", "dialogue_shot", "camera_json"],
        "Q02": ["reference_regions", "candidate_comparison"],
        "Q03": ["front_shot", "behind_shot", "world_position_log"],
        "Q04": ["normal_move_log", "pause_log", "dialogue_log", "resume_log"],
        "Q05": ["empty_shot", "full_shot", "reset_shot", "child_visibility_log"],
        "Q06": ["final_glb", "runtime_stats_log", "decode_stats"],
        "Q07": ["edited_source", "reexport", "same_camera_shot", "reopen_log"],
        "Q08": ["evidence_binding_manifest"],
        "Q09": ["state_index", "landscape_shot", "portrait_shot", "text_native_size_shot"],
    }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.qc = load_gate("check_quality")
        self.checks = json.loads((ROOT / "art_review/vnext/quality_checks.json").read_text(encoding="utf-8"))
        self.evidence = {}
        for qid, roles in self.ROLES.items():
            self.evidence[qid] = []
            for role in roles:
                path = self.root / "evidence" / qid / (role + ".txt")
                write_bytes(path, b"synthetic evidence")
                self.evidence[qid].append({"role": role, "path": path.relative_to(self.root).as_posix()})

    def measurements(self):
        return {
            "Q01": {"character_height_px": 97.8, "same_camera": True},
            "Q02": {"regions_compared": 3, "differences": [
                {"region": "tree", "difference": "canopy masses are still fragmented"},
                {"region": "planter", "difference": "ground cover density is low"},
                {"region": "materials", "difference": "metal is still flat black"}]},
            "Q03": {"cases": {"front": {"occluded": False}, "behind": {"occluded": True}},
                    "foot_shadow_drift_m": 0.001},
            "Q04": {"runs": [
                {"input_mode": "keyboard", "normal_move_m": 0.9, "pause_displacement_m": 0.0,
                 "dialogue_displacement_m": 0.0, "resumed_without_input_m": 0.0,
                 "resumed_after_new_input_m": 0.45, "clip_after_pause": False},
                {"input_mode": "touch", "normal_move_m": 0.8, "pause_displacement_m": 0.0,
                 "dialogue_displacement_m": 0.0, "resumed_without_input_m": 0.0,
                 "resumed_after_new_input_m": 0.4, "clip_after_pause": False}]},
            "Q05": {"states": {"empty": {"count": 0}, "full": {"count": 3}, "reset": {"count": 0}},
                    "reset_residue": False},
            "Q06": {"final_glb_sha256": "a" * 64, "stats_source": "runtime_measured_from_final_build",
                    "scopes": {"MAP001": {"draws": 337, "tris": 203566}}},
            "Q07": {"edit": {"parameter_or_component": "bench roughness", "reopened": True,
                             "reexported": True, "same_camera_result": True,
                             "unrelated_objects_unchanged": True}},
            "Q08": {"evidence_binding": {"source_sha256": "b" * 64, "export_sha256": "c" * 64,
                                         "contract_sha256": "d" * 64, "rubric_version": "1.2.0",
                                         "review_sha256": "e" * 64, "capture_id": "cap-1",
                                         "build_id": "build-1"}},
            "Q09": {"viewports": [
                {"name": "1280x720", "width": 1280, "height": 720, "canvas_backing": [1280, 720],
                 "screenshot_dimensions": [1280, 720], "safe_area": {"top": 0}, "text_native_size": True},
                {"name": "720x1280", "width": 720, "height": 1280, "canvas_backing": [720, 1280],
                 "screenshot_dimensions": [720, 1280], "safe_area": {"top": 0}, "text_native_size": True}],
                "device_tested": False},
        }

    def doc(self):
        measurements = self.measurements()
        return {"results_version": "vnext.behavior_results/1.0.0", "stage": "scene_demo",
                "build_id": "build-1", "generated_at": "2026-10-25T00:00:00Z",
                "results": [{"check_id": qid, "asset_id": "MAP001", "status": "pass",
                             "evidence": self.evidence[qid], "measurements": measurements[qid],
                             "tested_by": "synthetic", "tested_at": "2026-10-25T00:00:00Z"}
                            for qid in self.ROLES]}

    def binding(self):
        return {"binding_id": "cap-1", "build_id": "build-1"}

    def test_all_quality_checks_pass_without_texture_atlas(self):
        result = self.qc.evaluate(self.root, self.doc(), self.checks, self.binding())
        self.assertEqual(result["status"], "pass")
        self.assertIn("device_tested", " ".join(result["warnings"]))

    def test_missing_quality_check_stays_pending(self):
        doc = self.doc()
        doc["results"] = [r for r in doc["results"] if r["check_id"] != "Q03"]
        result = self.qc.evaluate(self.root, doc, self.checks, self.binding())
        self.assertEqual(result["status"], "pending")
        self.assertIn("Q03", result["pending"])

    def test_technical_screenshot_cannot_claim_behavior(self):
        doc = self.doc()
        for record in doc["results"]:
            if record["check_id"] == "Q03":
                record["evidence"] = [{"role": "scene_screenshot",
                                       "path": self.evidence["Q01"][0]["path"]}]
        result = self.qc.evaluate(self.root, doc, self.checks, self.binding())
        self.assertEqual(result["status"], "pending")
        self.assertIn("Q03", result["pending"])

    def test_missing_touch_run_fails(self):
        doc = self.doc()
        for record in doc["results"]:
            if record["check_id"] == "Q04":
                record["measurements"]["runs"] = record["measurements"]["runs"][:1]
        result = self.qc.evaluate(self.root, doc, self.checks, self.binding())
        self.assertEqual(result["status"], "fail")
        self.assertIn("Q04", result["failed"])

    def test_portrait_mock_fails(self):
        doc = self.doc()
        for record in doc["results"]:
            if record["check_id"] == "Q09":
                record["measurements"]["viewports"][1]["screenshot_dimensions"] = [1280, 720]
        result = self.qc.evaluate(self.root, doc, self.checks, self.binding())
        self.assertEqual(result["status"], "fail")

    def test_statistical_threshold_is_warning_only(self):
        doc = self.doc()
        for record in doc["results"]:
            if record["check_id"] == "Q06":
                record["measurements"]["scopes"]["MAP001"]["draws"] = 450
        result = self.qc.evaluate(self.root, doc, self.checks, self.binding())
        self.assertEqual(result["status"], "pass")
        self.assertTrue(any("draws" in warning for warning in result["warnings"]))


class BindingGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cb = load_gate("check_bindings")
        self.schema = ROOT / "art_review/vnext/capture_binding.schema.json"
        self.files = {
            "source.blend": b"BLENDER-source",
            "export.glb": b"glTF-export",
            "build.log": b"build Task (web-desktop) Finished\n",
            "out.png": big_png(),
        }
        for name, data in self.files.items():
            write_bytes(self.root / name, data)
        self.binding = {
            "binding_version": "vnext.capture_binding/1.0.0", "binding_id": "cap-1",
            "stage": "scene_demo", "created_at": "2026-10-25T00:00:00Z",
            "backend": {"name": "cocos", "version": "3.8.8"},
            "viewport": {"browser_width": 64, "browser_height": 36, "device_pixel_ratio": 1},
            "canvas": {"selector": "#GameCanvas",
                       "css_rect": {"x": 5, "y": 84.875, "width": 64, "height": 36},
                       "backing_width": 64, "backing_height": 36,
                       "capture_method": "element_screenshot", "page_screenshot": False},
            "camera": {"node": "Main Camera", "position": [0, 1, -2], "rotation": [0, 0, 0],
                       "fov": 35, "clip_time": None},
            "sources": [{"role": "source", "path": "source.blend",
                         "sha256": module.digest(self.root / "source.blend")}],
            "exports": [{"role": "export", "path": "export.glb",
                         "sha256": module.digest(self.root / "export.glb")}],
            "shared_inputs": [],
            "build": {"build_id": "b1", "log_path": "build.log",
                      "log_sha256": module.digest(self.root / "build.log"), "result": "success"},
            "output": {"path": "out.png", "sha256": module.digest(self.root / "out.png"),
                       "width": 64, "height": 36},
        }

    def path(self):
        path = self.root / "binding.json"
        write_json(path, self.binding)
        return path

    def test_valid_binding_passes(self):
        result = self.cb.verify_binding(self.root, self.path(), self.schema)
        self.assertTrue(result["verified"])
        self.assertEqual(result["checks"], 4)

    def test_page_screenshot_rejected(self):
        self.binding["canvas"]["page_screenshot"] = True
        with self.assertRaisesRegex(self.cb.BindingError, "page_screenshot"):
            self.cb.verify_binding(self.root, self.path(), self.schema)

    def test_failed_build_capture_rejected(self):
        self.binding["build"]["result"] = "failure"
        with self.assertRaisesRegex(self.cb.BindingError, "marked failure"):
            self.cb.verify_binding(self.root, self.path(), self.schema)

    def test_old_export_after_binding_is_rejected(self):
        path = self.path()
        write_bytes(self.root / "export.glb", b"glTF-export-v2")
        with self.assertRaisesRegex(self.cb.BindingError, "exports hash mismatch"):
            self.cb.verify_binding(self.root, path, self.schema)

    def test_shared_change_expands_dirty_closure(self):
        second = copy.deepcopy(self.binding)
        second["binding_id"] = "cap-2"
        second["shared_inputs"] = [{"role": "texture", "path": "source.blend",
                                    "sha256": module.digest(self.root / "source.blend"),
                                    "scope": ["MAP001", "ENV006"]}]
        write_json(self.root / "binding2.json", second)
        write_bytes(self.root / "source.blend", b"BLENDER-source-v2")
        result = self.cb.impact(self.root, [self.path(), self.root / "binding2.json"], "source.blend")
        self.assertEqual(sorted(r["binding_id"] for r in result["dirty_bindings"]), ["cap-1", "cap-2"])
        self.assertEqual(result["changed"][0]["shared_scopes"], ["ENV006", "MAP001"])

    def test_same_bytes_are_not_dirty(self):
        path = self.path()
        os.utime(self.root / "source.blend", (2000000000, 2000000000))
        result = self.cb.impact(self.root, [path], "source.blend")
        self.assertEqual(result["changed"][0]["status"], "content_unchanged")
        self.assertEqual(result["dirty_bindings"], [])


class BuildLogGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.gate = load_gate("build_log_gate")

    def check(self, name, lines, profile, exit_code):
        path = self.root / (name + ".log")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self.gate.check_log(path, profile, exit_code)

    def test_failure_event_beats_finished(self):
        result = self.check("fail_finished", ["Build Assets failed", "build Task (web-desktop) Finished"],
                            "cocos", 0)
        self.assertEqual(result["status"], "fail")

    def test_nonzero_exit_beats_finished(self):
        result = self.check("exit36", ["build Task (web-desktop) Finished"], "cocos", 36)
        self.assertEqual(result["status"], "fail")

    def test_benign_noise_warns_but_passes(self):
        result = self.check("benign", ["trackTimeEnd failed", "signal:SIGTERM",
                                       "build Task (web-desktop) Finished"], "cocos", 0)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["warnings"])

    def test_blender_traceback_beats_quit(self):
        result = self.check("traceback", ["Traceback (most recent call last):", "Blender quit"],
                            "blender", 0)
        self.assertEqual(result["status"], "fail")

    def test_utf16_log_is_decoded(self):
        path = self.root / "utf16.log"
        path.write_bytes("\n".join(["DELIVERED fixture", "Blender quit"]).encode("utf-16"))
        result = self.gate.check_log(path, "blender", 0)
        self.assertEqual(result["status"], "pass")

    def test_known_exit_requires_ordered_sigterm_and_output(self):
        output = self.root / "build_out.txt"
        output.write_text("built", encoding="utf-8")
        good = self.root / "known_exit_good.log"
        good.write_text("\n".join(["signal:SIGTERM in task build-script",
                                   "build Task (web-desktop) Finished"]), encoding="utf-8")
        self.assertEqual(self.gate.check_log(good, "cocos", 36, str(output), [36])["status"], "pass")
        self.assertEqual(self.gate.check_log(good, "cocos", 36, None, [36])["status"], "fail")
        reversed_log = self.root / "known_exit_reversed.log"
        reversed_log.write_text("\n".join(["build Task (web-desktop) Finished",
                                           "signal:SIGTERM in task build-script"]), encoding="utf-8")
        self.assertEqual(self.gate.check_log(reversed_log, "cocos", 36, str(output), [36])["status"], "fail")
        failure_log = self.root / "known_exit_failure.log"
        failure_log.write_text("\n".join(["signal:SIGTERM in task build-script",
                                          "Build Assets failed",
                                          "build Task (web-desktop) Finished"]), encoding="utf-8")
        self.assertEqual(self.gate.check_log(failure_log, "cocos", 36, str(output), [36])["status"], "fail")


class OtherGateTests(unittest.TestCase):
    def test_migration_review_whitelist(self):
        migrate = load_gate("migrate_catalog")
        ok, _ = migrate.review_check(ROOT, "ASSET01", {"asset_id": "ASSET01", "decision": "pass",
                                                       "reviewer": "producer", "evidence": ["HARNESS.md"]})
        self.assertTrue(ok)
        for review in (
            {"asset_id": "ASSET01", "decision": "fail", "reviewer": "producer", "evidence": ["HARNESS.md"]},
            {"asset_id": "ASSET01", "decision": "pass", "reviewer": "producer", "evidence": []},
            {"asset_id": "OTHER", "decision": "pass", "reviewer": "producer", "evidence": ["HARNESS.md"]},
        ):
            ok, _ = migrate.review_check(ROOT, "ASSET01", review)
            self.assertFalse(ok)

    @unittest.skipUnless(os.name == "nt", "PowerShell wrapper is Windows-only")
    def test_powershell_wrapper_propagates_exit_code(self):
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
             str(ROOT / "run-art-harness.ps1"), "-Command", "audit", "-Stage", "art_complete",
             "-Out", str(Path(tempfile.gettempdir()) / "p07_wrapper_audit.json")],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(proc.returncode, 3)
        self.assertIn("EXIT_CODE 3", proc.stdout)

    @unittest.skipUnless(os.name == "nt", "PowerShell wrapper is Windows-only")
    def test_directed_build_selection_and_unknown_stage(self):
        good = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
             str(ROOT / "tools/blender/run_courtyard_build.ps1"), "-Stage", "env_tree,map001", "-DryRun"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(good.returncode, 0)
        self.assertEqual(len([line for line in good.stdout.splitlines() if line.startswith("DRYRUN")]), 2)
        bad = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
             str(ROOT / "tools/blender/run_courtyard_build.ps1"), "-Stage", "nope", "-DryRun"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(bad.returncode, 2)


if __name__ == "__main__":
    unittest.main()
