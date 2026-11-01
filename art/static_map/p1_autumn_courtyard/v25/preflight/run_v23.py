# -*- coding: utf-8 -*-
"""v23 driver：一次跑完 ①→④（水池→景片→中景实体→定光），中途不找人。

用法（系统 python）：
    python preflight/run_v23.py              # 跑全部（已完成的阶段自动跳过）
    python preflight/run_v23.py --only S3A   # 只跑某段
    python preflight/run_v23.py --final      # 追加 48spp 正式图

设计：
  · 每段 = 改场景 → 低采样渲染 → measure.py 量 → 按比例回调旋钮 → 再渲，最多 4 轮；
  · 旋钮全部落在 preflight/KNOBS.json，脚本只读它，所以可以断点续跑；
  · 每轮写 RUNLOG.jsonl（含渲染图名、指标、旋钮变化），最后写 GATE_V23.json。
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KNOBS = os.path.join(HERE, "KNOBS.json")
LOG = os.path.join(HERE, "RUNLOG_V23.jsonl")
BLENDER = os.environ.get(
    "BLENDER_BIN",
    r"C:/Users/tt/.cache/blender/5.2.3/blender-5.2.3-windows-x64/blender.exe")
PY = sys.executable

DEFAULTS = {
    "exposure": -1.02,
    "sun_dir": [-0.885, 0.275, -0.393],
    "sun_energy": 17.0,
    "key_energy": 300.0,
    "bounce_energy": 46.0,
    "fill_energy": 12.0,
    "far_fill_energy": 0.0,
    "grass_emis": 0.10,
    "kicker_energy": 70.0,
    "m02_em": 1.72,
    "m03_em": 1.72,
    "yard_gain": 0.62,
    "yard_h": 1.0,
    "hide_far_shore": True,
}


def load_knobs():
    if os.path.exists(KNOBS):
        k = dict(DEFAULTS)
        k.update(json.load(open(KNOBS, encoding="utf-8")))
        return k
    return dict(DEFAULTS)


def save_knobs(k):
    json.dump(k, open(KNOBS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def log(rec):
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False))


def run(cmd, timeout=1800):
    t0 = time.time()
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    dt = round(time.time() - t0, 1)
    ok = p.returncode == 0
    log({"action": "exec", "cmd": " ".join(os.path.basename(c) if "blender" in c else c
                                           for c in cmd)[:160],
         "rc": p.returncode, "s": dt,
         "tail": (p.stdout or "")[-300:] if not ok else "",
         "err": (p.stderr or "")[-300:] if not ok else ""})
    return ok, p.stdout or ""


def blender(script):
    return run([BLENDER, "-b", os.path.join(ROOT, "scene.blend"), "-P",
                os.path.join(HERE, script)])[0]


def render(tag, samples=24, pct=50):
    out = "_%s.png" % tag
    env = dict(os.environ, SAMPLES=str(samples), PCT=str(pct), OUT=out)
    t0 = time.time()
    p = subprocess.run([BLENDER, "-b", os.path.join(ROOT, "scene.blend"), "-P",
                        os.path.join(HERE, "render.py")],
                       cwd=ROOT, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=3600)
    dt = round(time.time() - t0, 1)
    path = os.path.join(ROOT, "renders", out)
    if p.returncode != 0 or not os.path.exists(path):
        log({"action": "render_fail", "tag": tag, "s": dt,
             "err": (p.stderr or "")[-400:]})
        return None, dt
    return path, dt


def measure(path, json_name):
    jp = os.path.join(HERE, json_name)
    subprocess.run([PY, os.path.join(HERE, "measure.py"), "--render", path,
                    "--json", jp, "--quiet"], cwd=ROOT, capture_output=True)
    m = json.load(open(jp, encoding="utf-8"))
    # JSON 往返会把带号变成字符串，统一转回 int
    for key in ("bands", "bands_left", "bands_right"):
        if key in m:
            for side in m[key]:
                m[key][side] = {int(k): v for k, v in m[key][side].items()}
    return m


def stage_metrics(m):
    return m["anchors"]["now"], m["bands"]["now"]


def tune_light(k):
    """④ 定光：曝光收敛到舞台均值 165-178。"""
    for rnd in range(1, 5):
        blender("s4_light.py")
        path, dt = render("S4_r%d" % rnd)
        if not path:
            return False
        m = measure(path, "M_S4.json")
        a = m["anchors"]["now"]
        left = m["bands_left"]["now"]
        log({"action": "tune", "stage": "S4", "round": rnd, "render": os.path.basename(path),
             "stage": a["stage_v56_90"], "valley": a["valley_v44_50"],
             "far": a["far_v10_22"], "top": a["top_v0_8"],
             "v24_left": left[24], "exposure": round(k["exposure"], 3),
             "far_fill": k["far_fill_energy"], "s": dt})
        ok_stage = 161 <= a["stage_v56_90"] <= 178
        if ok_stage and (left[24] >= 92 or k["far_fill_energy"] >= 90):
            return True
        if not ok_stage:
            d_ev = 2.2 * _log2(168.0 / max(a["stage_v56_90"], 1.0))
            k["exposure"] = round(k["exposure"] + max(-0.28, min(0.28, d_ev)), 4)
        elif left[24] < 92:
            k["far_fill_energy"] = min(120, k["far_fill_energy"] + 35)
        save_knobs(k)
    return False


def _log2(x):
    import math
    return math.log2(max(x, 1e-6))


def tune_plates(k):
    """② 景片：M03 命中 v0-8 → 88；M02 尽量把 v10-22 抬到 127。"""
    for rnd in range(1, 5):
        blender("s2e_plates_apply.py")
        path, dt = render("S2_r%d" % rnd)
        if not path:
            return False
        m = measure(path, "M_S2.json")
        a = m["anchors"]["now"]
        log({"action": "tune", "stage": "S2", "round": rnd, "render": os.path.basename(path),
             "top": a["top_v0_8"], "far": a["far_v10_22"],
             "m02": k["m02_em"], "m03": k["m03_em"], "s": dt})
        top, far = a["top_v0_8"], a["far_v10_22"]
        if 82 <= top <= 98 and 112 <= far <= 142:
            return True
        if not (82 <= top <= 98):
            r = (88.0 / max(top, 1)) ** 2.2
            k["m03_em"] = round(max(0.5, min(3.2, k["m03_em"] * min(1.30, max(0.72, r)))), 4)
        # 远景带 90% 是几何体，景片只能微调 ±12%/轮，上限 2.6（再高就成白板）
        if far < 112:
            k["m02_em"] = round(min(2.6, k["m02_em"] * 1.12), 4)
        elif far > 142:
            k["m02_em"] = round(max(1.0, k["m02_em"] * 0.90), 4)
        save_knobs(k)
    return False


def tune_yard(k):
    """③ 造谷：yard_gain（明度）与 yard_h（覆盖高度）交替，目标 v44-50 ≤95 且 ≥80。"""
    for rnd in range(1, 6):
        blender("s3a_yard.py")
        path, dt = render("S3_r%d" % rnd)
        if not path:
            return False
        m = measure(path, "M_S3.json")
        a = m["anchors"]["now"]
        log({"action": "tune", "stage": "S3", "round": rnd, "render": os.path.basename(path),
             "valley": a["valley_v44_50"], "stage": a["stage_v56_90"],
             "local_min_v": a["local_min_v"], "gain": k["yard_gain"],
             "h": k["yard_h"], "s": dt})
        v = a["valley_v44_50"]
        if v <= 95 and v >= 80:
            return True
        if v > 95:
            k["yard_gain"] = round(max(0.30, k["yard_gain"] * max(0.62, (90.0 / v) ** 1.6)), 4)
            if rnd >= 3 and k["yard_gain"] <= 0.55:
                k["yard_h"] = round(min(1.45, k["yard_h"] * 1.12), 3)
        else:
            k["yard_gain"] = round(min(2.2, k["yard_gain"] * 1.12), 4)
        save_knobs(k)
    return False


def gate(k, final_png):
    m = measure(final_png, "M_FINAL.json")
    b = m["bands"]["now"]
    a = m["anchors"]["now"]
    cold = m["cold"]["now"]
    checks = {
        "1_谷位置_v42_50": 42 <= a["local_min_v"] <= 50,
        "2_谷值_le95": a["local_min_val"] <= 95,
        "3_舞台_ge160": a["stage_v56_90"] >= 160,
        "4_顶部_80_100": 80 <= a["top_v0_8"] <= 100,
        "5_舞台减谷_ge70": a["stage_minus_valley"] >= 70,
        "6_单调_rise_le15": a["v22_to_44_max_rise"] <= 15,
        "7_陡度_ge55": a["v48_to_58_rise"] >= 55,
        "8_冷色_0.25_0.50": 0.25 <= cold["ratio_pct"] <= 0.50,
    }
    rep = {"render": final_png, "bands": b, "anchors": a, "cold": cold,
           "checks": checks, "pass": all(checks.values()), "knobs": k}
    json.dump(rep, open(os.path.join(HERE, "GATE_V23.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n=== GATE v23 ===")
    for kk, vv in checks.items():
        print("  %-22s %s" % (kk, "PASS" if vv else "FAIL"))
    print("  stage=%.1f valley=%.1f top=%.1f far=%.1f cold=%.3f%%"
          % (a["stage_v56_90"], a["valley_v44_50"], a["top_v0_8"],
             a["far_v10_22"], cold["ratio_pct"]))
    print("  PASS" if rep["pass"] else "  FAIL")
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--final", action="store_true")
    args = ap.parse_args()
    k = load_knobs()
    save_knobs(k)

    plan = [("S2T", lambda kk: run([PY, os.path.join(HERE, "s2d_plates.py")])[0]),
            ("S4", tune_light),
            ("S2", tune_plates),
            ("S3", tune_yard)]
    if args.only:
        plan = [p for p in plan if p[0] == args.only]

    for name, fn in plan:
        log({"action": "stage_start", "stage": name})
        ok = fn(k)
        log({"action": "stage_end", "stage": name, "ok": ok})
        save_knobs(k)

    last = os.path.join(ROOT, "renders", "S3_final_check.png")
    path, dt = render("S3_final_check", samples=32, pct=50)
    if path:
        rep = gate(k, path)
        log({"action": "gate", "pass": rep["pass"], "checks": rep["checks"]})

    if args.final:
        log({"action": "stage_start", "stage": "FINAL"})
        p, dt = render("final", samples=48, pct=100)
        if p:
            rep = gate(k, p)
            log({"action": "final", "pass": rep["pass"], "s": dt, "file": p})
    print("\n=== DRIVER DONE ===")


if __name__ == "__main__":
    main()
