"""Local evidence gate. Visual acceptance additionally requires controller attestation."""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile


class GateError(ValueError):
    pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def require(condition, message):
    if not condition:
        raise GateError(message)


class Harness:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.config_path = self.root / "art_review/harness_contract.json"
        self.rubric_path = self.root / "art_review/rubric.json"
        self.contract = read_json(self.config_path)
        self.rubric = read_json(self.rubric_path)

    def file(self, relative):
        require(isinstance(relative, str) and relative, "Artifact path must be a nonempty relative string")
        relative = relative.replace("\\", "/")
        require(not Path(relative).is_absolute() and ":" not in relative, "Absolute/drive paths forbidden in manifest")
        path = (self.root / relative).resolve()
        require(path.is_relative_to(self.root), "Artifact escapes project root")
        require(path.is_file(), "Missing artifact: " + relative)
        return path

    def contract_digest(self):
        return hashlib.sha256(canonical({"contract": self.contract, "rubric": self.rubric})).hexdigest()

    def source_checks(self):
        rows = []
        for item in self.contract["locked_sources"]:
            try:
                path = self.file(item["path"])
                require(digest(path) == item["sha256"].lower(), "Hash mismatch")
                rows.append({"path": item["path"], "status": "pass"})
            except (GateError, OSError) as exc:
                rows.append({"path": item["path"], "status": "fail", "reason": str(exc)})
        return rows

    def inspect(self, row):
        path = self.file(row["path"])
        require(path.stat().st_size > 0, "Empty artifact: " + row["path"])
        suffix = path.suffix.lower()
        data = path.read_bytes()
        details = {}
        if suffix == ".png":
            require(data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR" and len(data) >= 33,
                    "Invalid PNG header: " + row["path"])
            width, height = struct.unpack(">II", data[16:24])
            require(width > 0 and height > 0, "Invalid PNG dimensions")
            details = {"width": width, "height": height, "alpha_channel_declared": data[25] in (4, 6) or b"tRNS" in data}
        if row["role"] == "idle_preview":
            require(suffix == ".png" and details.get("alpha_channel_declared"), "Idle preview must be PNG with alpha")
        if row["role"] in ("reference_comparison", "scene_screenshot", "dialogue_screenshot"):
            require(suffix == ".png", "Comparison/screenshots must be PNG")
        if row["role"] in ("move_preview", "demo_recording"):
            require((suffix == ".gif" and data[:6] in (b"GIF87a", b"GIF89a")) or
                    (suffix == ".mp4" and data[4:8] == b"ftyp"), "Expected GIF/MP4 media header")
        if row["role"] == "map_editable_source":
            if suffix == ".blend":
                require(data.startswith(b"BLENDER"), "Save uncompressed native .blend; a renamed image is not a scene")
            elif suffix == ".scene":
                scene = read_json(path)
                require(isinstance(scene, list) and any(isinstance(x, dict) and x.get("__type__") == "cc.Scene" for x in scene),
                        "Expected native Cocos scene structure")
            else:
                raise GateError("Map source must be editable .blend or .scene, not a generated background")
        if row["role"] == "ui_editable_source":
            if suffix == ".svg":
                tree = ET.fromstring(data)
                tags = {node.tag.rsplit("}", 1)[-1] for node in tree.iter()}
                require(tree.tag.rsplit("}", 1)[-1] == "svg" and bool(tags & {"path", "rect", "circle", "text", "polygon"}),
                        "UI SVG needs editable vector/text elements; image wrapping is not editable art")
            elif suffix == ".kra":
                require(zipfile.is_zipfile(path), "Invalid native Krita source")
                with zipfile.ZipFile(path) as archive:
                    require("maindoc.xml" in archive.namelist(), "Krita source lacks layer document")
                    ET.fromstring(archive.read("maindoc.xml"))
            else:
                raise GateError("UI source must be editable .svg or .kra")
        return {"role": row["role"], "path": path.relative_to(self.root).as_posix(),
                "sha256": digest(path), "bytes": len(data), **details}

    def inventory_check(self, rows):
        item = next(x for x in rows if x["role"] == "clip_inventory")
        inventory = read_json(self.file(item["path"]))
        skeleton = next(x for x in self.contract["locked_sources"] if x["path"].endswith(".skel"))
        require(inventory.get("source_skeleton_sha256", "").lower() == skeleton["sha256"].lower(),
                "Animation inventory is not bound to locked skeleton")
        runtime = inventory.get("runtime", {})
        require(runtime.get("name") and runtime.get("version"), "Inventory must identify actual runtime and version")
        require(inventory.get("extraction_method") == "runtime_parse", "Binary string scanning is not runtime enumeration")
        animations = inventory.get("animations", [])
        require(isinstance(animations, list) and animations, "No parsed animations")
        names = set()
        for clip in animations:
            require(isinstance(clip.get("name"), str) and clip["name"] not in names, "Duplicate/missing clip name")
            require(type(clip.get("duration")) in (int, float) and clip["duration"] > 0, "Clip duration must be positive")
            names.add(clip["name"])
        for state in ("idle", "move"):
            require(inventory.get("mapping", {}).get(state) in names, "Missing/invalid state mapping: " + state)

    def catalog_check(self, rows):
        item = next(x for x in rows if x["role"] == "full_art_catalog")
        catalog = read_json(self.file(item["path"]))
        entries = catalog.get("items", [])
        require(isinstance(entries, list), "Full catalog items must be a list")
        ids = [x.get("id") for x in entries]
        expected = set(self.contract.get("expected_art_ids", []))
        require(expected and len(ids) == len(set(ids)) and set(ids) == expected,
                "Full art catalog must cover exact expected IDs; a sample scene is not full art delivery")
        snapshots = []
        for entry in entries:
            asset_id = entry["id"]
            require(entry.get("status") in ("engine_verified", "approved"), "Unfinished art item: " + asset_id)
            require(isinstance(entry.get("source_paths"), list) and entry["source_paths"], "Missing editable sources: " + asset_id)
            require(isinstance(entry.get("preview_paths"), list) and entry["preview_paths"], "Missing previews: " + asset_id)
            review_path = entry.get("review_path")
            require(review_path, "Missing item review: " + asset_id)
            review = read_json(self.file(review_path))
            require(review.get("asset_id") == asset_id and review.get("decision") == "pass", "Item review not passed: " + asset_id)
            evidence = review.get("evidence")
            require(isinstance(review.get("reason"), str) and review["reason"].strip() and
                    isinstance(evidence, list) and evidence and
                    all(path in entry["source_paths"] + entry["preview_paths"] for path in evidence) and
                    any(path in entry["preview_paths"] for path in evidence),
                    "Item review needs a reason and bound preview evidence: " + asset_id)
            paths = entry["source_paths"] + entry["preview_paths"] + [review_path]
            for i, path in enumerate(paths):
                snapshots.append(self.inspect({"role": "catalog_member:" + asset_id + ":" + str(i), "path": path}))
        return snapshots

    def prepare(self, stage, specification):
        require(stage in self.contract["stages"], "Unknown stage")
        require(all(x["status"] == "pass" for x in self.source_checks()), "Locked source check failed")
        require(specification.get("character_mode") == "reference_spine", "Character must reuse reference Spine")
        methods = specification.get("production_methods")
        allowed = self.contract.get("production_policy", {}).get("allowed_methods", [])
        require(isinstance(methods, list) and bool(methods) and all(isinstance(x, str) for x in methods),
                "Declare actual production_methods; direct image generation is not an allowed route")
        require(set(methods).issubset(set(allowed)), "Unapproved production method; AI image generation is disabled")
        require("reference_spine" in methods, "Reference Spine method required")
        if stage in ("scene_demo", "art_complete"):
            require(bool(set(methods) & {"blender_editable", "blender_mcp_native", "cocos_scene_edit"}), "Editable scene method required")
            require(bool(set(methods) & {"krita_layered", "svg_editable"}), "Editable UI method required")
        require(isinstance(specification.get("artifacts"), list), "artifacts must be a list")
        rows = [self.inspect(x) for x in specification["artifacts"]]
        roles = [x["role"] for x in rows]
        require(len(roles) == len(set(roles)), "Duplicate artifact role; use a documented archive for multi-file roles")
        for role in self.contract["stages"][stage]["required_roles"]:
            require(role in roles, "Missing required artifact role: " + role)
        self.inventory_check(rows)
        catalog_members = self.catalog_check(rows) if stage == "art_complete" else []
        return {"manifest_version": "1.0.0", "status": "draft_not_accepted", "stage": stage,
                "character_mode": "reference_spine", "production_methods": methods, "contract_sha256": self.contract_digest(),
                "rubric_version": self.rubric["rubric_version"], "artifacts": rows, "catalog_members": catalog_members}

    def check_manifest(self, manifest):
        require(manifest.get("contract_sha256") == self.contract_digest(), "Stale contract/rubric digest; resubmit and re-review")
        require(manifest.get("rubric_version") == self.rubric["rubric_version"], "Stale rubric version")
        rebuilt = self.prepare(manifest["stage"], manifest)
        require(rebuilt["artifacts"] == manifest["artifacts"], "Artifacts changed after snapshot; regenerate manifest and review")
        require(rebuilt["catalog_members"] == manifest.get("catalog_members", []), "Full catalog sources/previews/reviews changed after snapshot")
        return rebuilt

    def check_review(self, manifest_path, manifest, review):
        require(review.get("manifest_sha256") == digest(manifest_path), "Review is not bound to exact manifest bytes")
        require(review.get("contract_sha256") == self.contract_digest(), "Review contract stale")
        require(review.get("rubric_version") == self.rubric["rubric_version"], "Review rubric stale")
        require(review.get("review_scope") == manifest["stage"], "Review scope mismatch")
        reviewer = review.get("reviewer", {})
        require(reviewer.get("id") and reviewer.get("mode") == "independent", "Self-review cannot release stage")
        evidence_paths = {x["path"] for x in manifest["artifacts"] + manifest.get("catalog_members", [])} | {x["path"] for x in self.contract["locked_sources"]}

        def evidence_check(evidence):
            require(isinstance(evidence, list) and evidence, "Missing review evidence")
            for path in evidence:
                require(path in evidence_paths, "Review evidence must reference snapshotted artifacts/source")

        stage = self.contract["stages"][manifest["stage"]]
        for gate in stage["review_gates"]:
            value = review.get("gates", {}).get(gate, {})
            require(value.get("status") == "pass", "Visual gate not passed: " + gate)
            require(isinstance(value.get("reason"), str) and value["reason"].strip(), "Gate requires reason: " + gate)
            evidence_check(value.get("evidence"))
        totals = {}
        for card in stage["cards"]:
            scores = review.get("cards", {}).get(card, {}).get("dimensions", [])
            require(isinstance(scores, list), "Invalid dimensions")
            by_id = {x["id"]: x for x in scores}
            definitions = self.rubric["cards"][card]
            require(len(by_id) == len(scores) and set(by_id) == {x["id"] for x in definitions}, "Missing/duplicate/unknown score dimensions: " + card)
            total = 0
            for dim in definitions:
                item = by_id[dim["id"]]
                score = item.get("score")
                require(type(score) is int and 0 <= score <= 4, "Score must be integer 0..4 (not bool/null)")
                require(score >= self.rubric["minimum_dimension"], "Dimension below floor: " + dim["id"])
                require(not dim["core"] or score >= self.rubric["minimum_core_dimension"], "Core dimension below floor: " + dim["id"])
                evidence_check(item.get("evidence"))
                require(isinstance(item.get("reason"), str) and item["reason"].strip(), "Score requires evidence-based reason")
                total += dim["weight"] * score / 4
            require(total >= self.rubric["pass_total"], "Computed score below threshold: " + card + "=" + str(total))
            totals[card] = total
        require(isinstance(review.get("defects"), list), "Defect list required; use [] only if actually checked")
        for defect in review["defects"]:
            if defect.get("status") == "resolved":
                evidence_check(defect.get("resolution_evidence"))
            else:
                require(defect.get("severity") == "minor" and defect.get("status") == "deferred" and
                        defect.get("accepted_reason"), "Unresolved defect blocks release")
        return totals

    def binding(self, manifest_path, review_path):
        return {"decision": "approved", "manifest_sha256": digest(manifest_path),
                "review_sha256": digest(review_path), "contract_sha256": self.contract_digest()}

    def verify(self, manifest_path, review_path=None, attestation_path=None):
        manifest = read_json(manifest_path)
        self.check_manifest(manifest)
        result = {"status": "needs_review", "accepted": False, "stage": manifest["stage"], "mechanical_checks": "pass"}
        if not review_path:
            result["next_action"] = "Independent reviewer must inspect actual media and create a manifest-bound review."
            return result
        result["computed_scores"] = self.check_review(manifest_path, manifest, read_json(review_path))
        result["status"] = "needs_controller_attestation"
        if not attestation_path:
            result["next_action"] = "Controller must approve exact manifest/review after visual inspection."
            return result
        key = os.environ.get("ART_HARNESS_REVIEW_KEY")
        require(key and len(key) >= 32, "Controller verification key missing; never create a key inside producer workflow")
        attestation = read_json(attestation_path)
        binding = self.binding(manifest_path, review_path)
        require(attestation.get("binding") == binding, "Attestation refers to different inputs")
        expected = hmac.new(key.encode(), canonical(binding), hashlib.sha256).hexdigest()
        require(hmac.compare_digest(str(attestation.get("signature", "")), expected), "Invalid controller attestation")
        result.update(status="accepted", accepted=True, next_action="Stage accepted for these exact inputs only.")
        return result

    def audit(self):
        rows = self.source_checks()
        legacy_path = self.root / "art/phase1/a_stage/reviews/A_stage_review.json"
        legacy = read_json(legacy_path) if legacy_path.is_file() else {}
        legacy_manifest = self.root / "art/phase1/a_stage/reviews/A_asset_manifest.json"
        legacy_items = read_json(legacy_manifest).get("artifacts", []) if legacy_manifest.is_file() else []
        legacy_failures = []
        for item in legacy_items:
            try:
                path = self.file(item["path"])
                require(digest(path) == item["sha256"].lower(), "Changed since legacy manifest")
            except (GateError, OSError, KeyError) as exc:
                legacy_failures.append({"path": item.get("path"), "reason": str(exc)})
        active = self.root / self.contract["active_manifest"]
        catalog_path = self.contract.get("catalog_definition_path")
        catalog_statuses = {}
        if catalog_path:
            for item in read_json(self.file(catalog_path)).get("items", []):
                status = item.get("status", "unknown")
                catalog_statuses[status] = catalog_statuses.get(status, 0) + 1
        return {"status": "blocked" if not active.is_file() or any(x["status"] != "pass" for x in rows) else "submission_present_not_accepted",
                "accepted": False, "locked_sources": rows,
                "legacy_review": {"path": str(legacy_path.relative_to(self.root)),
                                  "version": legacy.get("rubric_version"),
                                  "stale": legacy.get("rubric_version") != self.rubric["rubric_version"],
                                  "reviewer_mode": legacy.get("reviewer", {}).get("mode"),
                                  "has_reference_identity_gate": "H09" in legacy.get("gates", {})},
                "legacy_artifact_integrity": {"checked": len(legacy_items), "failures": legacy_failures,
                                              "meaning": "Integrity only, not aesthetic or engine acceptance"},
                "active_manifest_exists": active.is_file(),
                "full_art_catalog": {"declared_status_counts": catalog_statuses,
                                     "meaning": "Planning/inventory states, not independently approved progress percentages"},
                "next_action": "Verify reference Spine playback, submit bound artifacts; preserve old concept as historical."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["audit", "prepare", "verify", "attest"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--stage", default="character_playback")
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--attestation", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        harness = Harness(args.root)
        if args.command == "audit":
            result = harness.audit()
        elif args.command == "prepare":
            require(args.artifacts and args.out, "prepare needs --artifacts and --out")
            result = harness.prepare(args.stage, read_json(args.artifacts))
            write_json(args.out, result)
            print(json.dumps({"status": "draft_prepared_not_accepted", "path": str(args.out)}, ensure_ascii=False))
            return 0
        else:
            require(args.manifest, "--manifest required")
            if args.command == "attest":
                require(args.review and args.out, "attest needs --review and --out")
                harness.check_manifest(read_json(args.manifest))
                harness.check_review(args.manifest, read_json(args.manifest), read_json(args.review))
                key = os.environ.get("ART_HARNESS_REVIEW_KEY")
                require(key and len(key) >= 32, "Controller key required; producer must not invent one")
                binding = harness.binding(args.manifest, args.review)
                result = {"binding": binding, "signature": hmac.new(key.encode(), canonical(binding), hashlib.sha256).hexdigest()}
                write_json(args.out, result)
                print(json.dumps({"status": "attestation_written", "path": str(args.out)}, ensure_ascii=False))
                return 0
            result = harness.verify(args.manifest, args.review, args.attestation)
        if args.out:
            write_json(args.out, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("accepted") else 3
    except (GateError, OSError, ValueError, KeyError, TypeError, StopIteration, ET.ParseError, zipfile.BadZipFile) as exc:
        result = {"status": "blocked", "accepted": False, "error": str(exc)}
        if args.out:
            write_json(args.out, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
