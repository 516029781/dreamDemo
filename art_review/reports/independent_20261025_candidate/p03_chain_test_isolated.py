__file__='C:\\软件\\鼠鼠\\delivery\\next_cycle\\T0\\p03_chain_test.py'
__name__="__main__"
"""P03 self-check: certificate chain end-to-end on synthetic fixtures (never production art)."""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import zlib

REPO = Path(r"C:/软件/鼠鼠")
HARNESS = REPO / "tools/art_harness.py"
PY = r"C:/Users/tt/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"
KEY = "synthetic-p03-selfcheck-key-" + "x" * 20
results = []


def png():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"\0\0\0\0\0")) + chunk(b"IEND", b"")


def wj(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def w(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def run(args, key=KEY):
    env = dict(os.environ)
    if key is None:
        env.pop("ART_HARNESS_REVIEW_KEY", None)
    else:
        env["ART_HARNESS_REVIEW_KEY"] = key
    proc = subprocess.run([PY, "-X", "utf8", str(HARNESS)] + args,
                          capture_output=True, text=True, encoding="utf-8", env=env)
    return proc.returncode, proc.stdout, proc.stderr


root = Path(tempfile.mkdtemp(prefix="p03_chain_"))
(root / "art_review").mkdir()
w(root / "src.skel", b"test-skeleton")
source_hash = hashlib.sha256((root / "src.skel").read_bytes()).hexdigest()
contract = {
    "production_policy": {"allowed_methods": ["reference_spine", "blender_editable", "svg_editable", "cocos_scene_edit", "krita_layered"]},
    "locked_sources": [{"path": "src.skel", "sha256": source_hash}],
    "active_manifest": "manifest.json",
    "stages": {
        "character_playback": {
            "required_roles": ["clip_inventory", "idle_preview", "move_preview", "reference_comparison", "runtime_log"],
            "review_gates": ["H09"], "cards": ["CHAR"],
            "certificate_policy": {"required_for_release": True, "requires_certificates": []}},
        "scene_demo": {
            "required_roles": ["clip_inventory", "idle_preview", "move_preview", "reference_comparison", "runtime_log",
                               "scene_screenshot", "dialogue_screenshot", "demo_recording", "engine_sources",
                               "run_instructions", "map_editable_source", "ui_editable_source"],
            "review_gates": ["H02", "H09"], "cards": ["ENV", "CHAR"],
            "certificate_policy": {"required_for_release": True, "requires_certificates": ["character_playback"]}},
    },
}
rubric = {"rubric_version": "test-1", "minimum_dimension": 2, "minimum_core_dimension": 3, "pass_total": 85,
          "cards": {"CHAR": [{"id": "identity", "weight": 100, "core": True}],
                    "ENV": [{"id": "composition", "weight": 100, "core": True}]}}
wj(root / "art_review/harness_contract.json", contract)
wj(root / "art_review/rubric.json", rubric)
wj(root / "clips.json", {"source_skeleton_sha256": source_hash, "runtime": {"name": "test", "version": "3.8"},
                         "extraction_method": "runtime_parse", "animations": [{"name": "Move", "duration": 1.0}],
                         "mapping": {"idle": "Move", "move": "Move"}})
w(root / "idle.png", png())
w(root / "comparison.png", png())
w(root / "move.gif", base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"))
w(root / "runtime.txt", b"synthetic fixture")
w(root / "scene.png", png())
w(root / "dialogue.png", png())
w(root / "demo.mp4", b"\x00\x00\x00\x18ftypisomsynthetic")
w(root / "engine.txt", b"engine sources fixture")
w(root / "instructions.txt", b"run instructions fixture")
w(root / "map.blend", b"BLENDER-test-native-fixture")
w(root / "ui.svg", b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L4 4"/></svg>')
w(root / "char_extra.txt", b"character-only runtime evidence not consumed by scene")
w(root / "idle2.png", png() + b"different-version-suffix")
COMMON = ["--root", str(root), "--contract", str(root / "art_review/harness_contract.json")]


def manifest_for(stage, extra, idle_path="idle.png"):
    artifacts = {"character_mode": "reference_spine",
                 "production_methods": ["reference_spine", "blender_editable", "svg_editable"],
                 "artifacts": [{"role": "clip_inventory", "path": "clips.json"},
                               {"role": "idle_preview", "path": idle_path},
                               {"role": "move_preview", "path": "move.gif"},
                               {"role": "reference_comparison", "path": "comparison.png"},
                               {"role": "runtime_log", "path": "runtime.txt"}] + extra}
    spec = root / f"spec_{stage}.json"
    wj(spec, artifacts)
    out = root / f"manifest_{stage}.json"
    code, out_o, err = run(["prepare", "--stage", stage, "--artifacts", str(spec), "--out", str(out)] + COMMON)
    assert code == 0, (code, out_o, err)
    assert json.loads(out_o)["status"] == "draft_prepared_not_accepted"
    results.append({"step": f"prepare {stage} draft", "exit": code, "status": "draft_prepared_not_accepted"})
    return out


def review_for(stage, mp, gates, cards):
    dims = {"CHAR": "identity", "ENV": "composition"}
    review = {"manifest_sha256": hashlib.sha256(mp.read_bytes()).hexdigest(),
              "contract_sha256": hashlib.sha256(json.dumps({"contract": json.loads((root / "art_review/harness_contract.json").read_text(encoding="utf-8")), "rubric": rubric}, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest(),
              "rubric_version": "test-1", "review_scope": stage,
              "reviewer": {"id": "test-independent", "mode": "independent"},
              "gates": {g: {"status": "pass", "reason": "fixture", "evidence": ["comparison.png"]} for g in gates},
              "cards": {c: {"dimensions": [{"id": dims[c], "score": 4, "reason": "fixture", "evidence": ["comparison.png"]}]} for c in cards},
              "defects": []}
    rp = root / f"review_{stage}.json"
    wj(rp, review)
    return rp


def attest(stage, mp, rp, ap):
    code, out_o, err = run(["attest", "--manifest", str(mp), "--review", str(rp), "--out", str(ap)] + COMMON)
    assert code == 0, (code, out_o, err)
    results.append({"step": f"attest {stage}", "exit": code})


def certify(stage, mp, rp, cp, deps=None):
    args = ["certify", "--manifest", str(mp), "--review", str(rp), "--out", str(cp), "--certificate-id", f"cert-{stage}-001", "--approval-scope", f"fixture scope {stage}"] + COMMON
    if deps:
        args += ["--dependencies", deps]
    code, out_o, err = run(args)
    assert code == 0, (code, out_o, err)
    results.append({"step": f"certify {stage}", "exit": code})
    return cp


# character_playback chain (plus a character-only artifact the scene never consumes)
mp1 = manifest_for("character_playback", [{"role": "character_extra_probe", "path": "char_extra.txt"}])
rp1 = review_for("character_playback", mp1, ["H09"], ["CHAR"])
ap1 = root / "att1.json"; attest("character_playback", mp1, rp1, ap1)
cp1 = certify("character_playback", mp1, rp1, root / "cert_char.json")

# scene_demo chain with dependency on character_playback certificate
extra = [{"role": "scene_screenshot", "path": "scene.png"}, {"role": "dialogue_screenshot", "path": "dialogue.png"},
         {"role": "demo_recording", "path": "demo.mp4"}, {"role": "engine_sources", "path": "engine.txt"},
         {"role": "run_instructions", "path": "instructions.txt"}, {"role": "map_editable_source", "path": "map.blend"},
         {"role": "ui_editable_source", "path": "ui.svg"}]
mp2 = manifest_for("scene_demo", extra)
rp2 = review_for("scene_demo", mp2, ["H02", "H09"], ["ENV", "CHAR"])
ap2 = root / "att2.json"; attest("scene_demo", mp2, rp2, ap2)
cp2 = certify("scene_demo", mp2, rp2, root / "cert_scene.json", deps=str(cp1))

# 1) full verify with certificate chain -> accepted
code, out_o, err = run(["verify", "--manifest", str(mp2), "--review", str(rp2), "--attestation", str(ap2), "--certificate", str(cp2)] + COMMON)
body = json.loads(out_o)
results.append({"step": "verify scene_demo with certificate chain", "exit": code, "accepted": body.get("accepted"),
                "certificate_id": body.get("certificate", {}).get("certificate_id")})
assert code == 0 and body["accepted"] is True and body["certificate"]["certificate_id"] == "cert-scene_demo-001", (code, out_o[:800], err[:400])

# 2) forged certificate signature -> rejected
bad = json.loads(cp2.read_text(encoding="utf-8"))
bad["signature"] = "0" * 64
cp_bad = root / "cert_scene_forged.json"; wj(cp_bad, bad)
code, out_o, err = run(["verify", "--manifest", str(mp2), "--review", str(rp2), "--attestation", str(ap2), "--certificate", str(cp_bad)] + COMMON)
body = json.loads(out_o)
results.append({"step": "forged certificate rejected", "exit": code, "error": body.get("error", "")[:60]})
assert code == 2 and "Invalid stage certificate signature" in body.get("error", "")

# 3) boolean previous_passed instead of dependency objects -> rejected
boolcert = json.loads(cp2.read_text(encoding="utf-8"))
boolcert["dependencies"] = True
cp_bool = root / "cert_scene_bool.json"; wj(cp_bool, boolcert)
code, out_o, err = run(["verify", "--manifest", str(mp2), "--review", str(rp2), "--attestation", str(ap2), "--certificate", str(cp_bool)] + COMMON)
body = json.loads(out_o)
results.append({"step": "boolean dependencies rejected", "exit": code, "error": body.get("error", "")[:60]})
assert code == 2 and ("must match the schema exactly" in body.get("error", "") or "not a boolean" in body.get("error", "")), (code, out_o[:400])

# 4) verify without certificate when policy requires one -> rejected
code, out_o, err = run(["verify", "--manifest", str(mp2), "--review", str(rp2), "--attestation", str(ap2)] + COMMON)
body = json.loads(out_o)
results.append({"step": "missing certificate rejected", "exit": code, "error": body.get("error", "")[:60]})
assert code == 2 and "real controller certificate" in body.get("error", "")

# 5) producer context (no key) cannot verify certificates -> rejected
code, out_o, err = run(["verify", "--manifest", str(mp2), "--review", str(rp2), "--attestation", str(ap2), "--certificate", str(cp2)] + COMMON, key=None)
body = json.loads(out_o)
results.append({"step": "no-key context rejected", "exit": code, "error": body.get("error", "")[:60]})
assert code == 2 and "key missing" in body.get("error", "")

# 6) dependency-chain gap: scene_demo cert declared without real character cert path
gapcert = json.loads(cp2.read_text(encoding="utf-8"))
gapcert["dependencies"] = [{**gapcert["dependencies"][0], "path": "missing_cert.json"}]
cp_gap = root / "cert_scene_gap.json"; wj(cp_gap, gapcert)
code, out_o, err = run(["verify", "--manifest", str(mp2), "--review", str(rp2), "--attestation", str(ap2), "--certificate", str(cp_gap)] + COMMON)
body = json.loads(out_o)
results.append({"step": "missing dependency certificate rejected", "exit": code, "error": body.get("error", "")[:60]})
assert code == 2 and "Missing certificate file" in body.get("error", "")

# 7) F01: change a character-only artifact the scene never consumes -> scene verify must reject
original_extra = (root / "char_extra.txt").read_bytes()
w(root / "char_extra.txt", b"edited after both certificates were issued")
code, out_o, err = run(["verify", "--manifest", str(mp2), "--review", str(rp2), "--attestation", str(ap2), "--certificate", str(cp2)] + COMMON)
body = json.loads(out_o)
results.append({"step": "predecessor payload changed after certification rejected", "exit": code, "error": body.get("error", "")[:80]})
assert code == 2 and "changed after snapshot" in body.get("error", ""), (code, out_o[:600])

# 7b) restore the artifact -> the same chain is accepted again
w(root / "char_extra.txt", original_extra)
code, out_o, err = run(["verify", "--manifest", str(mp2), "--review", str(rp2), "--attestation", str(ap2), "--certificate", str(cp2)] + COMMON)
body = json.loads(out_o)
results.append({"step": "restored predecessor payload accepted again", "exit": code, "accepted": body.get("accepted")})
assert code == 0 and body["accepted"] is True, (code, out_o[:600])

# 8) F01: scene consumes a different character asset version than the certified one
mp2b = manifest_for("scene_demo", extra, idle_path="idle2.png")
rp2b = review_for("scene_demo", mp2b, ["H02", "H09"], ["ENV", "CHAR"])
ap2b = root / "att2b.json"; attest("scene_demo", mp2b, rp2b, ap2b)
code, out_o, err = run(["certify", "--manifest", str(mp2b), "--review", str(rp2b),
                        "--out", str(root / "cert_scene_mismatch_should_fail.json"),
                        "--certificate-id", "cert-scene-mismatch", "--approval-scope", "mismatch probe",
                        "--dependencies", str(cp1)] + COMMON)
body = json.loads(out_o)
results.append({"step": "consumption mismatch refused at certify", "exit": code, "error": body.get("error", "")[:80]})
assert code == 2 and "Consumed predecessor artifacts differ" in body.get("error", ""), (code, out_o[:600])

dep_cert = json.loads(cp1.read_text(encoding="utf-8"))
cert2 = {
    "certificate_version": "vnext.stage_certificate/1.0.0",
    "certificate_id": "cert-scene-handcrafted-mismatch",
    "stage": "scene_demo",
    "issued_at": "2026-10-25T00:00:00Z",
    "manifest": {"path": "manifest_scene_demo.json", "sha256": hashlib.sha256(mp2b.read_bytes()).hexdigest()},
    "review": {"path": "review_scene_demo.json", "sha256": hashlib.sha256(rp2b.read_bytes()).hexdigest()},
    "approver": {"id": "test-controller", "role": "external_controller", "key_id": "test-key"},
    "approval_scope": "handcrafted mismatch probe",
    "dependencies": [{"stage": "character_playback", "certificate_id": dep_cert["certificate_id"],
                      "path": "cert_char.json", "signature": dep_cert["signature"]}],
}
cert2_binding = {"certificate_id": cert2["certificate_id"], "stage": cert2["stage"],
                 "manifest_sha256": cert2["manifest"]["sha256"], "review_sha256": cert2["review"]["sha256"],
                 "approval_scope": cert2["approval_scope"], "issued_at": cert2["issued_at"],
                 "approver_id": cert2["approver"]["id"], "approver_key_id": cert2["approver"]["key_id"],
                 "dependency_signatures": [dep_cert["signature"]]}
cert2["signature"] = hmac.new(KEY.encode(), json.dumps(cert2_binding, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(), hashlib.sha256).hexdigest()
cp2b = root / "cert_scene_handcrafted.json"; wj(cp2b, cert2)
code, out_o, err = run(["verify", "--manifest", str(mp2b), "--review", str(rp2b), "--attestation", str(ap2b), "--certificate", str(cp2b)] + COMMON)
body = json.loads(out_o)
results.append({"step": "consumption mismatch rejected at verify", "exit": code, "error": body.get("error", "")[:80]})
assert code == 2 and "Consumed predecessor artifacts differ" in body.get("error", ""), (code, out_o[:600])

# 9) contract/rubric change invalidates the predecessor certificate chain
contract_path = root / "art_review/harness_contract.json"
contract_original = contract_path.read_bytes()
changed = json.loads(contract_original.decode("utf-8"))
changed["fixture_contract_change"] = True
wj(contract_path, changed)
code, out_o, err = run(["verify", "--manifest", str(mp2b), "--review", str(rp2b), "--attestation", str(ap2b), "--certificate", str(cp2b)] + COMMON)
body = json.loads(out_o)
results.append({"step": "contract change invalidates certificate chain", "exit": code, "error": body.get("error", "")[:80]})
assert code == 2 and "Stale contract/rubric digest" in body.get("error", ""), (code, out_o[:600])
contract_path.write_bytes(contract_original)

print(json.dumps({"results": results, "fixture_root": str(root)}, ensure_ascii=False, indent=1))
