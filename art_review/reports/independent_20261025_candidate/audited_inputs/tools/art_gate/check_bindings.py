#!/usr/bin/env python3
"""P04: verify capture bindings and compute the dirty closure of changed inputs.

A binding ties one captured image to the editable sources, exported artifacts,
build log, camera, browser viewport, canvas rect/backing size and hashes that
produced it. `impact` answers "which captures/reviews are invalidated by these
changes?" using recorded content hashes, never mtimes.

Exit codes: 0 ok / 1 dirty with --fail-on-dirty / 2 invalid input or failed proof.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

BINDING_VERSION = "vnext.capture_binding/1.0.0"
FROZEN_OUTPUT_PREFIXES = (
    "art_review/submissions/",
    "art_review/reports/",
    "reference/frozen_history/",
    "art/full/source/",
    "art/full/previews/",
)


class BindingError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise BindingError(message)


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _rel(root, path):
    try:
        return Path(path).resolve().relative_to(root).as_posix()
    except ValueError:
        return Path(path).as_posix()


def resolve(root, relative, must_exist=True):
    require(isinstance(relative, str) and relative, "Path must be a nonempty string")
    rel = relative.replace("\\", "/")
    require(not Path(rel).is_absolute() and ":" not in rel, "Absolute/drive paths forbidden: " + rel)
    path = (root / rel).resolve()
    require(path.is_relative_to(root), "Path escapes project root: " + rel)
    if must_exist:
        require(path.is_file(), "Missing file: " + rel)
    return path, rel


def png_size(path):
    with Path(path).open("rb") as f:
        head = f.read(33)
    require(head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR" and len(head) == 33,
            "Not a valid PNG: " + str(path))
    return struct.unpack(">II", head[16:24])


def schema_validate(document, schema_path):
    try:
        import jsonschema
    except ImportError:
        raise BindingError("a real Draft-07 validator is required (pip install jsonschema)")
    schema = load_json(schema_path)
    validator = jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda e: list(e.path))
    require(not errors, "Schema violations: " + "; ".join(
        "/".join(map(str, e.path)) + ": " + e.message for e in errors))


def check_entry(root, entry, label, checks):
    path, rel = resolve(root, entry["path"])
    actual = sha256_file(path)
    require(actual == entry["sha256"], label + " hash mismatch: " + rel)
    checks.append({label: rel, "sha256": actual})


def verify_binding(root, binding_path, schema_path):
    schema_path = Path(schema_path) if Path(schema_path).is_absolute() else root / schema_path
    binding = load_json(binding_path)
    schema_validate(binding, schema_path)
    require(binding["binding_version"] == BINDING_VERSION, "Unknown binding version")

    checks = []
    warnings = []
    raw_output = binding["output"]["path"].replace("\\", "/")
    for prefix in FROZEN_OUTPUT_PREFIXES:
        require(not raw_output.startswith(prefix),
                "Capture output must not overwrite frozen evidence: " + raw_output)
    output_path, output_rel = resolve(root, raw_output)
    for section in ("sources", "exports", "shared_inputs"):
        for entry in binding[section]:
            check_entry(root, entry, section, checks)
    check_entry(root, {"path": binding["build"]["log_path"], "sha256": binding["build"]["log_sha256"]},
                "build_log", checks)
    check_entry(root, {"path": binding["output"]["path"], "sha256": binding["output"]["sha256"]},
                "output", checks)

    require(output_path.is_file(), "Missing capture output")
    width, height = png_size(output_path)
    require((width, height) == (binding["output"]["width"], binding["output"]["height"]),
            "Recorded output dimensions do not match the PNG")
    require((width, height) == (binding["canvas"]["backing_width"], binding["canvas"]["backing_height"]),
            "Captured image must match the real canvas backing size; page crops are not canvas evidence")
    require(binding["canvas"]["capture_method"] in ("canvas_to_data_url", "element_screenshot"),
            "Capture must come from the canvas itself")
    require(binding["canvas"]["page_screenshot"] is False, "page_screenshot=true is forbidden (F05)")

    if binding["build"]["result"] == "failure":
        raise BindingError("Build log is marked failure; a Finished message is not success (F08)")
    if binding["build"]["result"] == "unknown":
        warnings.append("Build result unknown; confirm failure events before using this capture")

    return {"binding_id": binding["binding_id"], "stage": binding["stage"], "verified": True,
            "checks": len(checks), "output": output_rel, "warnings": warnings}


def load_bindings(root, spec):
    files = []
    for raw in spec.split(","):
        raw = raw.strip()
        require(raw, "Empty binding path in --bindings")
        path = Path(raw) if Path(raw).is_absolute() else root / raw
        if path.is_dir():
            files.extend(sorted(p for p in path.glob("*.json") if "schema" not in p.name))
        else:
            require(path.is_file(), "Missing binding file: " + raw)
            files.append(path)
    require(files, "No binding files found")
    return files


def impact(root, binding_files, changed):
    bindings = [load_json(f) for f in binding_files]
    consumed = {}
    produced = {}
    scopes = {}
    for idx, binding in enumerate(bindings):
        for section in ("sources", "exports", "shared_inputs"):
            for entry in binding[section]:
                consumed.setdefault(entry["path"], []).append((idx, entry["sha256"], section))
                if section == "shared_inputs":
                    scopes.setdefault(entry["path"], set()).update(entry.get("scope", []))
        out = binding["output"]
        produced.setdefault(out["path"], []).append((idx, out["sha256"]))

    rows = []
    dirty = {}
    for raw in changed.split(","):
        raw = raw.strip()
        require(raw, "Empty path in --changed")
        path, rel = resolve(root, raw, must_exist=False)
        recorded = {sha for _, sha, _ in consumed.get(rel, [])}
        recorded |= {sha for _, sha in produced.get(rel, [])}
        current = sha256_file(path) if path.is_file() else None
        if current is not None and recorded and current in recorded:
            status = "content_unchanged"
        elif not recorded and current is not None:
            status = "unreferenced"
        else:
            status = "content_changed"
        rows.append({"path": rel, "status": status, "current_sha256": current,
                     "recorded_sha256": sorted(recorded),
                     "shared_scopes": sorted(scopes.get(rel, []))})
        if status == "content_changed":
            seeds = [idx for idx, _, _ in consumed.get(rel, [])] + [idx for idx, _ in produced.get(rel, [])]
            for idx in seeds:
                dirty.setdefault(idx, set()).add(rel)

    changed_flag = True
    while changed_flag:
        changed_flag = False
        for idx, reasons in list(dirty.items()):
            out_path = bindings[idx]["output"]["path"]
            for downstream, _, _ in consumed.get(out_path, []):
                if downstream not in dirty:
                    dirty[downstream] = {"downstream:" + out_path}
                    changed_flag = True

    dirty_rows = [{"binding_id": bindings[idx]["binding_id"], "stage": bindings[idx]["stage"],
                   "binding_file": _rel(root, binding_files[idx]),
                   "reasons": sorted(reasons)} for idx, reasons in sorted(dirty.items())]
    dirty_ids = {row["binding_id"] for row in dirty_rows}
    return {
        "binding_version": BINDING_VERSION,
        "changed": rows,
        "dirty_bindings": dirty_rows,
        "unaffected_bindings": sorted(b["binding_id"] for i, b in enumerate(bindings)
                                      if b["binding_id"] not in dirty_ids),
        "stages_to_rereview": sorted({row["stage"] for row in dirty_rows}),
        "orphan_changes": [row["path"] for row in rows if row["status"] == "unreferenced"],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    sub = ap.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify", help="verify one binding's full evidence chain")
    verify.add_argument("--binding", required=True)
    verify.add_argument("--schema", default="art_review/vnext/capture_binding.schema.json")
    verify.add_argument("--json-out", type=Path)

    imp = sub.add_parser("impact", help="compute the dirty closure for changed paths")
    imp.add_argument("--bindings", required=True, help="comma-separated binding files or a directory")
    imp.add_argument("--changed", required=True, help="comma-separated changed paths")
    imp.add_argument("--fail-on-dirty", action="store_true")
    imp.add_argument("--json-out", type=Path)

    args = ap.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "verify":
            result = verify_binding(root, root / args.binding if not Path(args.binding).is_absolute() else Path(args.binding),
                                    args.schema)
            code = 0
        else:
            result = impact(root, load_bindings(root, args.bindings), args.changed)
            code = 1 if (args.fail_on_dirty and result["dirty_bindings"]) else 0
        if args.json_out:
            write_json(args.json_out, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except (BindingError, OSError, ValueError, KeyError, TypeError) as exc:
        result = {"status": "invalid", "error": str(exc)}
        if getattr(args, "json_out", None):
            write_json(args.json_out, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
