#!/usr/bin/env python3
"""P06/F08: build-log gate. 'Finished' never overrides a failure event or a bad exit code.

Profiles are deliberately small and versioned here; a benign line is a warning,
not a permanent exception. Exit 0 only when the process exit code, the success
marker and the failure scan all agree.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PROFILES = {
    "cocos": {
        "success": [r"build task \(web-desktop\) finished", r"\bbuild task finished\b"],
        "hard": [r"build assets failed", r"\bbuild failed\b", r"\bcompile error\b",
                 r"\bfatal error\b", r"error: exit process with code: [1-9]"],
        "warn": [r"trackTimeEnd failed", r"validation failed, .*default value",
                 r"signal:SIGTERM"],
    },
    "blender": {
        "success": [r"\bBlender quit\b", r"\bDELIVERED\b"],
        "hard": [r"Traceback \(most recent call last\)", r"Error: Python script failed",
                 r"\bRuntimeError:"],
        "warn": [r"signal:SIGTERM"],
    },
    "verify": {
        "success": [r"VERIFY_RESULT=PASS"],
        "hard": [r"VERIFY_RESULT=FAIL"],
        "warn": [],
    },
    "generic": {
        "success": [r"\bBUILD_OK\b", r"\bBUILD SUCCEEDED\b"],
        "hard": [r"\bBUILD_FAILED\b", r"\bBUILD FAILED\b", r"\bFATAL\b"],
        "warn": [],
    },
}


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_text(path):
    data = Path(path).read_bytes()
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16", errors="replace")
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig", errors="replace")
    return data.decode("utf-8", errors="replace")


def check_log(path, profile, exit_code=None, expect_output=None, known_exits=None):
    rules = PROFILES[profile]
    known_exits = set(known_exits or [])
    text = read_text(path)
    lines = text.splitlines()
    hard = []
    warnings = []
    success = []
    for number, line in enumerate(lines, 1):
        for pattern in rules["hard"]:
            if re.search(pattern, line, re.IGNORECASE):
                hard.append({"line": number, "pattern": pattern, "text": line.strip()[:300]})
                break
        for pattern in rules["warn"]:
            if re.search(pattern, line, re.IGNORECASE):
                warnings.append({"line": number, "pattern": pattern, "text": line.strip()[:300]})
                break
        for pattern in rules["success"]:
            if re.search(pattern, line, re.IGNORECASE):
                success.append({"line": number, "text": line.strip()[:300]})
                break
    failures = []
    known_exit_applied = False
    if exit_code is not None and exit_code != 0:
        anomaly_sigterm = any(
            re.search(r"signal:SIGTERM", entry["text"], re.IGNORECASE) and entry["line"] < success[-1]["line"]
            for entry in warnings
        ) if success else False
        if exit_code in known_exits and success and not hard and expect_output and Path(expect_output).exists() and anomaly_sigterm:
            known_exit_applied = True
            warnings.append({"line": success[-1]["line"], "pattern": "known_exit",
                             "text": "exit " + str(exit_code) + " accepted only with ordered SIGTERM, "
                                     "success marker and present output"})
        else:
            failures.append("process exit code " + str(exit_code) + " is not zero")
    for entry in hard:
        failures.append("failure event line " + str(entry["line"]) + ": " + entry["text"])
    if exit_code is None and not hard and not known_exit_applied:
        failures.append("exit code not supplied; a log alone cannot prove success")
    if not success:
        failures.append("no success marker for profile " + profile)
    if expect_output:
        output = Path(expect_output)
        if not output.exists():
            failures.append("expected build output missing: " + str(output))
    return {
        "log": str(path),
        "log_sha256": sha256_file(path),
        "profile": profile,
        "exit_code": exit_code,
        "known_exit_applied": known_exit_applied,
        "line_count": len(lines),
        "success_markers": success,
        "failure_events": hard,
        "warnings": warnings,
        "output_checked": str(expect_output) if expect_output else None,
        "status": "fail" if failures else "pass",
        "failures": failures,
        "meaning": "Evidence chain only; a pass here is not art or engine acceptance.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True)
    parser.add_argument("--profile", choices=sorted(PROFILES), default="cocos")
    parser.add_argument("--exit-code", type=int)
    parser.add_argument("--known-exit", type=int, action="append", default=[],
                        help="Version-specific exit anomaly; still requires ordered SIGTERM, success marker and output")
    parser.add_argument("--expect-output")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    try:
        result = check_log(args.log, args.profile, args.exit_code, args.expect_output, args.known_exit)
    except OSError as exc:
        result = {"status": "invalid", "error": str(exc)}
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
