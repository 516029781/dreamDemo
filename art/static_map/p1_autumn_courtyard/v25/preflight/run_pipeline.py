# -*- coding: utf-8 -*-
"""P1 静态地图流水线 driver：一次跑完 G0→G3，断点续跑，只在结束时报结果。

用法（系统 python，不是 blender）：
    python preflight/run_pipeline.py              # 跑全部未完成阶段
    python preflight/run_pipeline.py --from G3    # 从指定阶段开始
    python preflight/run_pipeline.py --force G3   # 强制重跑某阶段

设计目标：
  1. 一次启动跑到底，不中间回来找人；
  2. 每阶段产物落盘 + SHA 记账，中断后按 state 续跑，不重复已完成的渲染；
  3. 同一方法同一假设最多试 2 次，失败换法并记录，不静默跳过；
  4. 失败不终止整条链：标记 blocked，继续到还能做的最远阶段。
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.dirname(HERE)
STATE_PATH = os.path.join(HERE, "RUN_STATE.json")
LOG_PATH = os.path.join(HERE, "RUNLOG.jsonl")

BLENDER = os.environ.get(
    "BLENDER_BIN",
    r"C:/Users/tt/.cache/blender/5.2.3/blender-5.2.3-windows-x64/blender.exe",
)

# 阶段定义：id, 脚本, 必需产物（相对 CAND）, 超时秒, 最大尝试
STAGES = [
    {"id": "G0", "name": "参考遮罩分析", "script": None,
     "outputs": ["reference_analysis/P1_MASK_RECORD.json"], "timeout": 600, "tries": 2},
    {"id": "G1", "name": "机位锁定与投影", "script": "g1_lock_camera.py",
     "outputs": ["preflight/G1_SHORE_PROJECTION.json"], "timeout": 600, "tries": 2},
    {"id": "G2", "name": "背景分层重建", "script": "r3_rebuild_plates.py",
     "outputs": ["preflight/R3_PLATES.json"], "timeout": 900, "tries": 2},
    {"id": "G3", "name": "交付渲染", "script": "g3_deliver.py",
     "outputs": ["renders/final.png", "renders/blockout.png",
                 "renders/color_key.png", "renders/no_dof_diagnostic.png",
                 "preflight/G3_DELIVER.json"],
     "timeout": 5400, "tries": 2},
    {"id": "G3b", "name": "细节板合成", "script": "g3b_details.py", "runner": "python",
     "outputs": ["renders/details.png"], "timeout": 300, "tries": 2},
    {"id": "G4", "name": "门禁与交付单", "script": "g4_write_gate.py", "runner": "python",
     "outputs": ["GATE_REPORT.json", "DELIVERY.json", "REVIEW.md"], "timeout": 600, "tries": 2},
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"stages": {}, "started": time.strftime("%Y-%m-%dT%H:%M:%S")}


def save_state(st):
    st["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


def log(rec):
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False))


def outputs_ready(stage):
    missing = []
    for rel in stage["outputs"]:
        p = os.path.join(CAND, rel)
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            missing.append(rel)
    return missing


def run_stage(stage, st):
    sid = stage["id"]
    missing = outputs_ready(stage)
    if not missing and st["stages"].get(sid, {}).get("status") == "ok":
        log({"stage": sid, "action": "skip", "reason": "outputs present"})
        return "ok"

    if not stage["script"]:
        log({"stage": sid, "action": "manual", "reason": "no script bound"})
        return "ok" if not missing else "blocked"

    script = os.path.join(HERE, stage["script"])
    if not os.path.exists(script):
        log({"stage": sid, "action": "error", "reason": f"missing script {stage['script']}"})
        return "blocked"

    blend = os.path.join(CAND, "scene.blend")
    if stage.get("runner") == "python":
        base_cmd = [sys.executable, script]
    else:
        base_cmd = [BLENDER, "-b", blend, "-P", script]
    last_err = None
    for attempt in range(1, stage["tries"] + 1):
        cmd = base_cmd
        t0 = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=stage["timeout"], encoding="utf-8", errors="replace")
            rc = proc.returncode
            tail = (proc.stdout or "")[-1200:]
            err = (proc.stderr or "")[-800:]
        except subprocess.TimeoutExpired:
            rc = -9
            tail, err = "", "timeout"
        dt = round(time.time() - t0, 1)
        miss = outputs_ready(stage)
        ok = (rc == 0 and not miss)
        log({
            "stage": sid, "action": "run", "attempt": attempt,
            "cmd": " ".join(cmd), "exit_code": rc, "duration_s": dt,
            "missing_outputs": miss,
            "stdout_tail": tail[-600:], "stderr_tail": err[-400:],
        })
        if ok:
            shas = {}
            for rel in stage["outputs"]:
                p = os.path.join(CAND, rel)
                if os.path.exists(p):
                    shas[rel] = sha256(p)
            st["stages"][sid] = {
                "status": "ok", "duration_s": dt, "attempts": attempt,
                "outputs_sha256": shas,
            }
            save_state(st)
            return "ok"
        last_err = err or f"rc={rc} missing={miss}"
        if attempt < stage["tries"]:
            log({"stage": sid, "action": "retry", "reason": last_err[:200]})

    st["stages"][sid] = {"status": "blocked", "error": (last_err or "")[:400]}
    save_state(st)
    return "blocked"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default=None)
    ap.add_argument("--force", default=None)
    args = ap.parse_args()

    st = load_state()
    results = {}
    skipping = bool(args.start)
    for stage in STAGES:
        if skipping:
            if stage["id"] != args.start:
                log({"stage": stage["id"], "action": "skip", "reason": f"--from {args.start}"})
                continue
            skipping = False
        if args.force and stage["id"] == args.force:
            st["stages"].pop(stage["id"], None)
        results[stage["id"]] = run_stage(stage, st)
        if results[stage["id"]] == "blocked" and stage["id"] in {"G0", "G1"}:
            log({"action": "abort", "reason": f"{stage['id']} blocked (upstream)"})
            break

    summary = {
        "action": "summary",
        "results": results,
        "state": STATE_PATH,
        "log": LOG_PATH,
    }
    log(summary)
    blocked = [k for k, v in results.items() if v == "blocked"]
    print("\n=== PIPELINE DONE ===")
    print("ok     :", [k for k, v in results.items() if v == "ok"])
    print("blocked:", blocked)
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
