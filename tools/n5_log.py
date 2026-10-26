"""n5 run logging: append-only events plus unique per-run raw logs.

Implements the T0/T1 minimum from N5_EXECUTION_DESIGN_AND_GAP_AUDIT.md:
every run carries an explicit candidate_id/run_id, writes a uniquely named
stdout/stderr log, records real exit codes, and appends one events.jsonl row
with monotonic duration and input/output SHAs. Nothing is inferred from "the
newest file".

Usage:
  python tools/n5_log.py run --stage blender --run-id n5-env-01 \
      --reason "tree A/B/C ablation" --defect N01 \
      --in tools/blender_n5/build_env_courtyard.py \
      --out art/candidates/candidate_n5/previews/environment/ENV006_autumn_tree.png \
      -- <command...>

  python tools/n5_log.py event --stage visual_review --run-id n5-env-01 \
      --status completed --reason "compared A/B/C silhouettes"
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERF = os.path.join(ROOT, "delivery", "next_cycle", "n5", "performance")
LOGS = os.path.join(PERF, "logs")
EVENTS = os.path.join(PERF, "events.jsonl")
COMMANDS = os.path.join(PERF, "commands.txt")
CANDIDATE_ID = "candidate_n5"


def _sha(path):
    full = path if os.path.isabs(path) else os.path.join(ROOT, path)
    if not os.path.isfile(full):
        return None
    h = hashlib.sha256()
    with open(full, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _rel(path):
    disp = os.path.relpath(path, ROOT) if os.path.isabs(path) else path
    return disp.replace("\\", "/")


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_event(row):
    os.makedirs(PERF, exist_ok=True)
    target = os.environ.get("N5_EVENTS_PATH") or EVENTS
    if not os.path.isabs(target):
        target = os.path.join(ROOT, target)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def cmd_run(args):
    os.makedirs(LOGS, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = os.path.join(LOGS, "%s.%s.%s.log" % (args.run_id, args.stage, stamp))
    started_utc = _now()
    t0 = time.monotonic()
    inputs = {_rel(p): _sha(p) for p in (args.inp or [])}
    proc = subprocess.run(args.command, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    duration = int((time.monotonic() - t0) * 1000)
    with open(log_path, "w", encoding="utf-8") as fh:
        if args.command:
            fh.write("$ " + " ".join(args.command) + "\n")
        fh.write(proc.stdout or "")
        if proc.stderr:
            fh.write("\n--- stderr ---\n" + proc.stderr)
        fh.write("\n--- exit %d ---\n" % proc.returncode)
    output = {_rel(p): _sha(p) for p in (args.out or [])}
    row = {
        "candidate_id": CANDIDATE_ID,
        "run_id": args.run_id,
        "stage": args.stage,
        "started_at_utc": started_utc,
        "ended_at_utc": _now(),
        "duration_ms_monotonic": duration,
        "input_sha256": inputs,
        "output_sha256": output,
        "cache_hit": False,
        "command_or_action": " ".join(args.command),
        "exit_code": proc.returncode,
        "status": "completed" if proc.returncode == 0 else "failed",
        "log_path": _rel(log_path),
        "defect_id": args.defect or "",
        "reason": args.reason or "",
    }
    if getattr(args, "agent_id", None):
        row["agent_id"] = args.agent_id
    if getattr(args, "resource_lock", None):
        row["resource_lock"] = args.resource_lock
    append_event(row)
    if not os.environ.get("N5_EVENTS_PATH"):
        os.makedirs(PERF, exist_ok=True)
        with open(COMMANDS, "a", encoding="utf-8") as fh:
            fh.write("[%s] %s | cwd=%s | exit=%d | log=%s\n" % (
                started_utc, " ".join(args.command), ROOT, proc.returncode, _rel(log_path)))
    sys.stdout.write(proc.stdout or "")
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc.returncode


def cmd_event(args):
    inputs = {_rel(p): _sha(p) for p in (args.inp or [])}
    output = {_rel(p): _sha(p) for p in (args.out or [])}
    row = {
        "candidate_id": CANDIDATE_ID,
        "run_id": args.run_id,
        "stage": args.stage,
        "started_at_utc": args.started or _now(),
        "ended_at_utc": _now(),
        "duration_ms_monotonic": args.duration_ms,
        "input_sha256": inputs,
        "output_sha256": output,
        "cache_hit": False,
        "command_or_action": args.reason or args.stage,
        "exit_code": 0,
        "status": args.status,
        "log_path": "",
        "defect_id": args.defect or "",
        "reason": args.reason or "",
    }
    if getattr(args, "agent_id", None):
        row["agent_id"] = args.agent_id
    append_event(row)
    print(json.dumps({"appended": row["run_id"], "stage": row["stage"]}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run")
    r.add_argument("--stage", required=True)
    r.add_argument("--run-id", required=True, dest="run_id")
    r.add_argument("--reason", default="")
    r.add_argument("--defect", default="")
    r.add_argument("--agent-id", dest="agent_id", default="")
    r.add_argument("--resource-lock", dest="resource_lock", default="")
    r.add_argument("--in", dest="inp", action="append")
    r.add_argument("--out", action="append")
    r.add_argument("command", nargs=argparse.REMAINDER)

    e = sub.add_parser("event")
    e.add_argument("--stage", required=True)
    e.add_argument("--run-id", required=True, dest="run_id")
    e.add_argument("--status", default="completed")
    e.add_argument("--reason", default="")
    e.add_argument("--defect", default="")
    e.add_argument("--agent-id", dest="agent_id", default="")
    e.add_argument("--started", default="")
    e.add_argument("--duration-ms", dest="duration_ms", type=int, default=0)
    e.add_argument("--in", dest="inp", action="append")
    e.add_argument("--out", action="append")

    args = ap.parse_args()
    if args.cmd == "run":
        if args.command and args.command[0] == "--":
            args.command = args.command[1:]
        if not args.command:
            ap.error("run requires a command after --")
        return cmd_run(args)
    return cmd_event(args)


if __name__ == "__main__":
    sys.exit(main())
