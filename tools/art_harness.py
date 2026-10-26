"""Local evidence gate. Visual acceptance additionally requires controller attestation."""
import argparse
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile

CERTIFICATE_VERSION = "vnext.stage_certificate/1.0.0"
CERTIFICATE_FIELDS = {"certificate_version", "certificate_id", "stage", "issued_at",
                      "manifest", "review", "approver", "approval_scope", "dependencies", "signature"}


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
    def __init__(self, root, contract_path=None):
        self.root = Path(root).resolve()
        self.config_path = Path(contract_path) if contract_path else self.root / "art_review/harness_contract.json"
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

    def certificate_policy(self, stage):
        return self.contract.get("stages", {}).get(stage, {}).get("certificate_policy")

    def certificate_binding(self, cert):
        return {"certificate_id": cert["certificate_id"], "stage": cert["stage"],
                "manifest_sha256": cert["manifest"]["sha256"], "review_sha256": cert["review"]["sha256"],
                "approval_scope": cert["approval_scope"], "issued_at": cert["issued_at"],
                "approver_id": cert["approver"]["id"], "approver_key_id": cert["approver"]["key_id"],
                "dependency_signatures": sorted(d["signature"] for d in cert["dependencies"])}

    def consumption_check(self, manifest, dependencies):
        """F01: a stage must consume the certified predecessor artifacts, byte-identical."""
        current = {x["role"]: x["sha256"] for x in manifest.get("artifacts", [])}
        for dep_stage, dep_manifest in dependencies:
            previous = {x["role"]: x["sha256"] for x in dep_manifest.get("artifacts", [])}
            shared = sorted(set(current) & set(previous))
            require(shared, "Manifest does not consume any artifact from certified stage "
                            + dep_stage + "; cannot bind the consumed predecessor version")
            mismatch = [role for role in shared if current[role] != previous[role]]
            require(not mismatch, "Consumed predecessor artifacts differ from the certified "
                                  + dep_stage + " version: " + ", ".join(mismatch))

    def certificate_check(self, certificate_path, manifest_path=None, review_path=None, _seen=None):
        _seen = set() if _seen is None else _seen
        cert_path = Path(certificate_path)
        require(cert_path.is_file(), "Missing certificate file: " + str(certificate_path))
        resolved = cert_path.resolve()
        require(resolved not in _seen, "Certificate dependency cycle detected")
        _seen.add(resolved)
        cert = read_json(cert_path)
        require(set(cert.keys()) == CERTIFICATE_FIELDS,
                "Certificate fields must match the schema exactly; boolean flags like previous_passed are not accepted")
        require(cert.get("certificate_version") == CERTIFICATE_VERSION, "Unknown certificate version")
        require(isinstance(cert.get("certificate_id"), str) and cert["certificate_id"].strip(), "Certificate id required")
        stage = cert.get("stage")
        require(stage in self.contract.get("stages", {}), "Certificate stage unknown: " + str(stage))
        policy = self.certificate_policy(stage)
        require(isinstance(policy, dict) and policy.get("required_for_release"),
                "Stage has no active certificate policy in this contract")
        approver = cert.get("approver")
        require(isinstance(approver, dict) and approver.get("id") and approver.get("key_id")
                and approver.get("role") == "external_controller",
                "Certificate approver must be an external_controller record")
        require(isinstance(cert.get("approval_scope"), str) and cert["approval_scope"].strip(),
                "Certificate approval_scope required")
        require(isinstance(cert.get("issued_at"), str) and cert["issued_at"].strip(), "Certificate issued_at required")
        deps = cert.get("dependencies")
        require(isinstance(deps, list), "Certificate dependencies must be a list of objects, not a boolean")
        manifest_sha = digest(self.file(cert["manifest"]["path"]))
        require(manifest_sha == cert["manifest"]["sha256"], "Certificate manifest hash mismatch")
        review_sha = digest(self.file(cert["review"]["path"]))
        require(review_sha == cert["review"]["sha256"], "Certificate review hash mismatch")
        require(read_json(self.file(cert["manifest"]["path"])).get("stage") == stage,
                "Certificate stage differs from bound manifest stage")
        if manifest_path is not None:
            require(digest(Path(manifest_path)) == manifest_sha,
                    "Certificate binds a different manifest than the inputs being verified")
        if review_path is not None:
            require(digest(Path(review_path)) == review_sha,
                    "Certificate binds a different review than the inputs being verified")
        required = list(policy.get("requires_certificates", []))
        for dep in deps:
            require(isinstance(dep, dict) and set(dep.keys()) == {"stage", "certificate_id", "path", "signature"},
                    "Dependency certificate entries must be objects with stage/certificate_id/path/signature")
        dep_stages = [d["stage"] for d in deps]
        require(len(dep_stages) == len(set(dep_stages)), "Duplicate dependency certificate stage")
        require(set(dep_stages) == set(required),
                "Certificate dependency chain does not satisfy policy; requires: " + (", ".join(required) or "none"))
        checked = []
        dep_manifests = []
        for dep in deps:
            dep_file = Path(dep["path"])
            if not dep_file.is_absolute():
                dep_file = self.root / dep_file
            sub = self.certificate_check(dep_file, _seen=_seen)
            require(sub["stage"] == dep["stage"], "Dependency certificate stage mismatch")
            require(sub["certificate_id"] == dep["certificate_id"], "Dependency certificate id mismatch")
            require(sub["signature"] == dep["signature"], "Dependency signature is not bound into this certificate")
            dep_cert = read_json(dep_file)
            dep_manifest_path = self.file(dep_cert["manifest"]["path"])
            dep_manifest = read_json(dep_manifest_path)
            self.check_manifest(dep_manifest)
            self.check_review(dep_manifest_path, dep_manifest,
                              read_json(self.file(dep_cert["review"]["path"])))
            dep_manifests.append((sub["stage"], dep_manifest))
            checked.append({"stage": sub["stage"], "certificate_id": sub["certificate_id"],
                            "manifest_sha256": sub["manifest_sha256"]})
        self.consumption_check(read_json(self.file(cert["manifest"]["path"])), dep_manifests)
        key = os.environ.get("ART_HARNESS_REVIEW_KEY")
        require(key and len(key) >= 32,
                "Controller verification key missing; certificates cannot be verified inside the producer workflow")
        expected = hmac.new(key.encode(), canonical(self.certificate_binding(cert)), hashlib.sha256).hexdigest()
        require(hmac.compare_digest(str(cert.get("signature", "")), expected), "Invalid stage certificate signature")
        return {"certificate_id": cert["certificate_id"], "stage": stage, "signature": cert["signature"],
                "manifest_sha256": manifest_sha, "review_sha256": review_sha,
                "dependencies": checked}

    def verify(self, manifest_path, review_path=None, attestation_path=None, certificate_path=None):
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
        policy = self.certificate_policy(manifest["stage"])
        if isinstance(policy, dict) and policy.get("required_for_release"):
            require(certificate_path,
                    "Stage release requires a real controller certificate; a boolean previous_passed is not accepted")
            result["certificate"] = self.certificate_check(certificate_path, manifest_path, review_path)
        result.update(status="accepted", accepted=True, next_action="Stage accepted for these exact inputs only.")
        return result

    def _gate_module(self, filename, name):
        import importlib.util
        path = self.root / "tools/art_gate" / filename
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def latest_review(self, stage):
        reports = self.root / "art_review/reports"
        candidates = []
        for path in reports.glob("*/independent_review.json"):
            try:
                data = read_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("review_scope") != stage:
                continue
            gate_path = path.parent / "review_gate.json"
            gate = read_json(gate_path) if gate_path.is_file() else None
            candidates.append((path.stat().st_mtime, path, data, gate))
        if not candidates:
            return None
        _, path, data, gate = max(candidates, key=lambda item: item[0])
        failed, pending = self.review_failures(data)
        return {
            "path": path.relative_to(self.root).as_posix(),
            "sha256": digest(path),
            "reviewer": data.get("reviewer"),
            "manifest_sha256": data.get("manifest_sha256") or data.get("asset_manifest_sha256"),
            "rubric_version": data.get("rubric_version"),
            "stale_rubric": data.get("rubric_version") != self.rubric["rubric_version"],
            "overall_decision": data.get("overall_decision"),
            "review_gate": gate,
            "review_gate_sha256": digest(path.parent / "review_gate.json") if gate is not None else None,
            "failed": failed,
            "pending": pending,
        }

    def review_failures(self, review):
        failed = []
        pending = []
        for gate, value in review.get("gates", {}).items():
            item = {"check": "gate:" + gate, "status": value.get("status"),
                    "reason": value.get("reason")}
            if value.get("status") == "fail":
                failed.append(item)
            elif value.get("status") != "pass":
                pending.append(item)
        for card, value in review.get("cards", {}).items():
            total = value.get("computed_total")
            decision = value.get("computed_decision")
            if decision == "rework" or (total is not None and total < self.rubric["pass_total"]):
                failed.append({"check": "card:" + card, "status": decision or "below_threshold",
                               "reason": "computed_total=" + str(total) + " < " + str(self.rubric["pass_total"])})
            elif total is None:
                pending.append({"check": "card:" + card, "status": "missing_total", "reason": "no computed total"})
            for dimension in value.get("dimensions", []):
                score = dimension.get("score")
                if score is None:
                    pending.append({"check": "dimension:" + card + "." + str(dimension.get("id")),
                                    "status": "not_scored", "reason": "no score"})
                elif score < self.rubric["minimum_dimension"]:
                    failed.append({"check": "dimension:" + card + "." + str(dimension.get("id")),
                                   "status": "below_floor", "reason": "score=" + str(score)})
        for defect in review.get("defects", []):
            if defect.get("status") == "resolved":
                continue
            item = {"check": "defect:" + str(defect.get("id") or defect.get("issue_id")),
                    "status": defect.get("status", "open"),
                    "reason": defect.get("title") or defect.get("summary"),
                    "severity": defect.get("severity")}
            if defect.get("severity") in ("blocking", "major"):
                failed.append(item)
            else:
                pending.append(item)
        return failed, pending

    def audit(self, stage=None, quality_results=None, bindings=None):
        rows = self.source_checks()
        stage = stage or "art_complete"
        active = self.root / self.contract["active_manifest"]
        contract_block = {
            "path": self.config_path.relative_to(self.root).as_posix(),
            "version": self.contract.get("contract_version"),
            "sha256": digest(self.config_path),
            "rubric": {"path": self.rubric_path.relative_to(self.root).as_posix(),
                       "version": self.rubric["rubric_version"], "sha256": digest(self.rubric_path)},
            "combined_contract_rubric_sha256": self.contract_digest(),
        }
        vnext_path = self.root / "art_review/vnext/harness_contract.json"
        if vnext_path.is_file():
            vnext = read_json(vnext_path)
            contract_block["vnext_contract"] = {"path": vnext_path.relative_to(self.root).as_posix(),
                                                "version": vnext.get("contract_version"),
                                                "effective": vnext.get("vnext_effective") is True,
                                                "sha256": digest(vnext_path)}

        failed_checks = []
        pending_checks = []
        for source in rows:
            if source["status"] != "pass":
                failed_checks.append({"check": "locked_source", "status": "fail",
                                      "reason": source.get("reason"), "path": source["path"]})
        if not active.is_file():
            failed_checks.append({"check": "active_manifest", "status": "missing",
                                  "reason": "no active submission: " + self.contract["active_manifest"]})
        else:
            active_doc = read_json(active)
            if active_doc.get("stage") != stage:
                pending_checks.append({"check": "active_manifest_stage", "status": "mismatch",
                                       "reason": "active manifest stage " + str(active_doc.get("stage"))
                                                 + " != audit stage " + stage})
            if active_doc.get("status") not in ("accepted", "released"):
                pending_checks.append({"check": "active_submission", "status": str(active_doc.get("status")),
                                       "reason": "active submission is not accepted"})
            if active_doc.get("contract_sha256") != self.contract_digest():
                failed_checks.append({"check": "active_manifest_contract", "status": "stale",
                                      "reason": "active manifest was frozen under a different contract/rubric digest"})

        review = self.latest_review(stage)
        if review is None:
            pending_checks.append({"check": "independent_review", "status": "missing",
                                   "reason": "no independent review for stage " + stage})
        else:
            failed_checks.extend(review["failed"])
            pending_checks.extend(review["pending"])
            if review["stale_rubric"]:
                failed_checks.append({"check": "independent_review", "status": "stale",
                                      "reason": "review rubric " + str(review["rubric_version"])
                                                + " != current " + self.rubric["rubric_version"]})

        quality = {"status": "not_supplied",
                   "reason": "behavior_results for Q01-Q09 not supplied to audit"}
        if quality_results:
            try:
                module = self._gate_module("check_quality.py", "check_quality")
                quality_path = Path(quality_results)
                if not quality_path.is_absolute():
                    quality_path = self.root / quality_path
                quality_doc = read_json(quality_path)
                checks_doc = read_json(self.root / self.contract.get("quality_checks_path",
                                                                     "art_review/vnext/quality_checks.json"))
                quality = module.evaluate(self.root, quality_doc, checks_doc)
                for check_id in quality.get("failed", []):
                    failed_checks.append({"check": "quality:" + check_id, "status": "fail",
                                          "reason": quality["checks"].get(check_id, {}).get("reason")})
                for check_id in quality.get("pending", []):
                    pending_checks.append({"check": "quality:" + check_id, "status": "pending",
                                           "reason": quality["checks"].get(check_id, {}).get("reason")})
            except (GateError, OSError, ValueError, KeyError, TypeError) as exc:
                failed_checks.append({"check": "quality_input", "status": "invalid", "reason": str(exc)})

        binding_report = {"status": "not_supplied", "reason": "capture bindings not supplied to audit"}
        if bindings:
            module = self._gate_module("check_bindings.py", "check_bindings")
            results = []
            for raw in bindings.split(","):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    results.append(module.verify_binding(
                        self.root, self.root / raw,
                        self.root / "art_review/vnext/capture_binding.schema.json"))
                except (ValueError, OSError, KeyError, TypeError) as exc:
                    failed_checks.append({"check": "capture_binding", "status": "invalid",
                                          "path": raw, "reason": str(exc)})
            binding_report = {"status": "pass" if results else "fail", "verified": results}

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
        catalog_path = self.contract.get("catalog_definition_path")
        catalog_statuses = {}
        if catalog_path:
            for item in read_json(self.file(catalog_path)).get("items", []):
                status = item.get("status", "unknown")
                catalog_statuses[status] = catalog_statuses.get(status, 0) + 1

        next_actions = []
        if any(x["status"] != "pass" for x in rows):
            next_actions.append("Restore locked character sources to the contract hashes before any capture.")
        if not active.is_file():
            next_actions.append("Create the active draft: python tools/art_harness.py prepare --stage "
                                + stage + " --artifacts <spec.json> --out " + self.contract["active_manifest"])
        if review is None:
            next_actions.append("Obtain an independent review for stage " + stage
                                + " bound to the exact manifest hash; producer self-review is rejected.")
        else:
            gates = [item["check"] for item in review["failed"] if item["check"].startswith("gate:")]
            if gates:
                next_actions.append("Resolve failed visual gates: " + ", ".join(gates)
                                    + "; re-review the same build, not an old screenshot.")
            defects = [item for item in review["failed"] if item["check"].startswith("defect:")]
            if defects:
                next_actions.append("Resolve blocking/major defects with same-build evidence: "
                                    + ", ".join(item["check"] for item in defects))
        if quality["status"] == "not_supplied":
            next_actions.append("Provide behavior_results for Q01-Q09, then run: python tools/art_gate/check_quality.py --results <file> --binding <capture_binding.json>")
        elif quality["status"] != "pass":
            next_actions.append("Quality evidence is " + quality["status"]
                                + "; missing/pending items stay pending, never pass.")
        if binding_report["status"] == "not_supplied":
            next_actions.append("Bind every new capture: python tools/art_gate/check_bindings.py verify --binding <binding.json>")
        next_actions.append("Controller attestation and certificate remain external; never self-sign release.")

        status = "blocked" if failed_checks else ("needs_review" if pending_checks else "ready_for_controller")
        return {
            "status": status,
            "accepted": False,
            "stage": stage,
            "contract": contract_block,
            "exit_code_contract": {
                "0": "accepted=true only for controller-approved exact inputs",
                "2": "blocked or invalid inputs (gate error, missing key, bad signature)",
                "3": "valid run but not accepted: draft, failed checks or needs review",
            },
            "failed_checks": failed_checks,
            "pending_checks": pending_checks,
            "next_actions": next_actions,
            "next_action": next_actions[0] if next_actions else None,
            "latest_independent_review": review,
            "quality_checks": quality,
            "capture_bindings": binding_report,
            "locked_sources": rows,
            "active_manifest_exists": active.is_file(),
            "active_manifest": self.contract["active_manifest"],
            "legacy_review": {"path": str(legacy_path.relative_to(self.root)),
                              "version": legacy.get("rubric_version"),
                              "stale": legacy.get("rubric_version") != self.rubric["rubric_version"],
                              "reviewer_mode": legacy.get("reviewer", {}).get("mode"),
                              "has_reference_identity_gate": "H09" in legacy.get("gates", {})},
            "legacy_artifact_integrity": {"checked": len(legacy_items), "failures": legacy_failures,
                                          "meaning": "Integrity only, not aesthetic or engine acceptance"},
            "full_art_catalog": {"declared_status_counts": catalog_statuses,
                                 "meaning": "Planning/inventory states, not independently approved progress percentages"},
        }


def _rel(root, path):
    path = Path(path)
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["audit", "prepare", "verify", "attest", "certify"])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--contract", type=Path, help="Override contract path (e.g. art_review/vnext/harness_contract.json); default keeps 1.3.0")
    parser.add_argument("--stage", default=None)
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--attestation", type=Path)
    parser.add_argument("--certificate", type=Path, help="Stage certificate for verify when the contract requires one")
    parser.add_argument("--quality", help="behavior_results JSON for audit (Q01-Q09)")
    parser.add_argument("--bindings", help="Comma-separated capture binding JSONs for audit")
    parser.add_argument("--dependencies", help="Comma-separated dependency certificate paths for certify")
    parser.add_argument("--certificate-id")
    parser.add_argument("--approval-scope")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        harness = Harness(args.root, contract_path=args.contract)
        if args.command == "audit":
            result = harness.audit(args.stage, args.quality, args.bindings)
        elif args.command == "prepare":
            require(args.artifacts and args.out, "prepare needs --artifacts and --out")
            result = harness.prepare(args.stage or "character_playback", read_json(args.artifacts))
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
            if args.command == "certify":
                require(args.review and args.out, "certify needs --review and --out")
                manifest = read_json(args.manifest)
                harness.check_manifest(manifest)
                harness.check_review(args.manifest, manifest, read_json(args.review))
                policy = harness.certificate_policy(manifest["stage"])
                require(isinstance(policy, dict) and policy.get("required_for_release"),
                        "Stage has no certificate policy in this contract; use attest instead")
                key = os.environ.get("ART_HARNESS_REVIEW_KEY")
                require(key and len(key) >= 32, "Controller key required; producer must not invent one")
                deps = []
                for raw in (args.dependencies.split(",") if args.dependencies else []):
                    dep_path = raw.strip()
                    require(dep_path, "Empty dependency certificate path")
                    sub = harness.certificate_check(dep_path)
                    deps.append({"stage": sub["stage"], "certificate_id": sub["certificate_id"],
                                 "path": _rel(harness.root, Path(dep_path)), "signature": sub["signature"]})
                require(set(d["stage"] for d in deps) == set(policy.get("requires_certificates", [])),
                        "Dependency certificates do not satisfy the stage policy")
                dep_manifests = []
                for dep in deps:
                    dep_cert = read_json(harness.root / dep["path"])
                    dep_manifest_path = harness.file(dep_cert["manifest"]["path"])
                    dep_manifests.append((dep["stage"], read_json(dep_manifest_path)))
                harness.consumption_check(manifest, dep_manifests)
                cert = {
                    "certificate_version": CERTIFICATE_VERSION,
                    "certificate_id": args.certificate_id or ("cert-" + manifest["stage"] + "-" + digest(args.manifest)[:12]),
                    "stage": manifest["stage"],
                    "issued_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "manifest": {"path": _rel(harness.root, args.manifest), "sha256": digest(args.manifest)},
                    "review": {"path": _rel(harness.root, args.review), "sha256": digest(args.review)},
                    "approver": {"id": os.environ.get("ART_HARNESS_CONTROLLER_ID", "external-controller"),
                                 "role": "external_controller",
                                 "key_id": os.environ.get("ART_HARNESS_KEY_ID", "unspecified")},
                    "approval_scope": args.approval_scope or ("stage:" + manifest["stage"]),
                    "dependencies": deps,
                }
                cert["signature"] = hmac.new(key.encode(), canonical(harness.certificate_binding(cert)), hashlib.sha256).hexdigest()
                write_json(args.out, cert)
                print(json.dumps({"status": "certificate_written", "path": str(args.out)}, ensure_ascii=False))
                return 0
            result = harness.verify(args.manifest, args.review, args.attestation, args.certificate)
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
