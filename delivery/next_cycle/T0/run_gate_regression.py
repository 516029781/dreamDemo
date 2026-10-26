"""P07: run the gate regression suite and all self-check scripts, writing gate_regression.json."""
import importlib.util
import json
import subprocess
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PY = sys.executable


def load_tests():
    spec = importlib.util.spec_from_file_location("test_art_harness", ROOT / "tools/test_art_harness.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return unittest.defaultTestLoader.loadTestsFromModule(module)


class RecordingResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.records = []
        self._start = None

    def startTest(self, test):
        self._start = time.perf_counter()
        super().startTest(test)

    def _record(self, test, status, detail=""):
        self.records.append({"test": test.id(), "status": status,
                             "seconds": round(time.perf_counter() - self._start, 4),
                             "detail": detail[:300]})

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, "pass")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._record(test, "fail", str(err[1]))

    def addError(self, test, err):
        super().addError(test, err)
        self._record(test, "error", str(err[1]))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record(test, "skip", reason)


def main():
    started = time.perf_counter()
    result = RecordingResult()
    suite = load_tests()
    suite.run(result)
    unittest_seconds = round(time.perf_counter() - started, 3)

    selfchecks = [
        ("p02_f03_f04", "delivery/next_cycle/T0/p02_selfcheck.py"),
        ("p03_certificate_chain", "delivery/next_cycle/T0/p03_chain_test.py"),
        ("p04_capture_binding", "delivery/next_cycle/T0/p04_selfcheck.py"),
        ("p05_quality_checks", "delivery/next_cycle/T0/p05_selfcheck.py"),
        ("p06_audit_build_capture", "delivery/next_cycle/T0/p06_selfcheck.py"),
    ]
    runs = []
    for name, script in selfchecks:
        cmd = [PY, "-X", "utf8", script]
        check_started = time.perf_counter()
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        runs.append({"name": name, "command": " ".join(cmd), "exit_code": proc.returncode,
                     "seconds": round(time.perf_counter() - check_started, 3),
                     "stdout_tail": proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "",
                     "stderr_tail": proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else ""})

    ledger = json.loads((ROOT / "PROJECT_TASKS.json").read_text(encoding="utf-8-sig"))
    report = {
        "kind": "gate_regression",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ledger_revision": ledger.get("revision"),
        "python": sys.version.split()[0],
        "unittest": {
            "total": len(result.records),
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "seconds": unittest_seconds,
            "tests": result.records,
        },
        "selfchecks": runs,
        "all_passed": not result.failures and not result.errors
                      and all(run["exit_code"] == 0 for run in runs),
        "limitations": "Tool runtimes only. No model reading, manual review or controller waiting is included.",
    }
    out = ROOT / "delivery/next_cycle/T0/gate_regression.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_passed": report["all_passed"], "tests": len(result.records),
                      "failures": report["unittest"]["failures"], "errors": report["unittest"]["errors"],
                      "selfcheck_exits": {run["name"]: run["exit_code"] for run in runs},
                      "output": str(out)}, ensure_ascii=False))
    return 0 if report["all_passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
