"""Re-verify the frozen-history recovery archive against the old manifest hashes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RECORD = ROOT / "reference/frozen_history/art_complete_20261024_manifest/RECOVERY_RECORD.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    record = json.loads(RECORD.read_text(encoding="utf-8-sig"))
    failures = []
    for item in record["items"]:
        archive = ROOT / item["archive_path"]
        if not archive.is_file():
            failures.append({"path": item["path"], "reason": "archive file missing"})
            continue
        actual = sha256(archive)
        if actual != item["expected_sha256"]:
            failures.append({"path": item["path"], "reason": "hash mismatch", "actual": actual})
    result = {
        "kind": "frozen_history_recovery_check",
        "record": RECORD.relative_to(ROOT).as_posix(),
        "record_sha256": sha256(RECORD),
        "checked": len(record["items"]),
        "failures": failures,
        "old_manifest_untouched": sha256(ROOT / record["manifest"]) == record["manifest_sha256"],
        "meaning": "Payload recovery only. The restored files are historical references, not current art approval.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures and result["old_manifest_untouched"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
