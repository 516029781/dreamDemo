"""Isolated reopen-and-rerender reproduction for v15 (content SHA, not container).

    python tools/run_v15_repro.py

Renders the SAME fixed 420x620 / 8 spp / seed 0 / Camera master from
(a) the delivered v15 scene and (b) a freshly rebuilt v15 scene in an isolated
directory, then compares the decoded raw RGB bytes (HARNESS_LIFECYCLE §3).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path("C:/软件/鼠鼠")
BL = str(ROOT / ".tools/blender/blender-4.5.15-windows-x64/blender.exe")
V15 = ROOT / "art/static_map/space_base_minigame/v15"
REPRO = V15 / "repro"
REPRO.mkdir(parents=True, exist_ok=True)
SCENE = V15 / "scene.blend"
REBUILT = REPRO / "scene_rebuilt.blend"
ORIG = REPRO / "orig.png"
REBUILT_PNG = REPRO / "rebuilt.png"
REQ = "20261109-space-base-v152-rooms"
RUN = "20261109-1125"
RUNDIR = ROOT / "knowledge/active" / REQ / "runs" / RUN

RENDER_SCRIPT = "tools/repro_v13_render.py"  # fixed conditions, works for v15 too
BUILDER = "tools/blender_space_base/build_scene_v15.py"

cmds = [
    [BL, "-b", str(SCENE), "--python", RENDER_SCRIPT, "--", str(ORIG)],
    [BL, "-b", "--factory-startup", "--python", BUILDER, "--", "--out", str(REBUILT)],
    [BL, "-b", str(REBUILT), "--python", RENDER_SCRIPT, "--", str(REBUILT_PNG)],
]
timings = []
for cmd in cmds:
    t = time.perf_counter()
    p = subprocess.run(cmd, cwd=str(ROOT), stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    timings.append({"exit_code": p.returncode, "wall_seconds": round(time.perf_counter() - t, 2),
                    "command": " ".join(cmd[:6]) + " ..."})
    if p.returncode != 0:
        print("REPRO_STEP_FAILED", p.returncode, p.stdout.decode("utf-8", "ignore")[-400:])
        raise SystemExit(1)


def content_sha(p):
    a = np.asarray(Image.open(p).convert("RGB"), dtype=np.uint8)
    return hashlib.sha256(a.tobytes()).hexdigest(), a.shape


h1, shp = content_sha(ORIG)
h2, _ = content_sha(REBUILT_PNG)
a = np.asarray(Image.open(ORIG).convert("RGB"), dtype=np.int16)
b = np.asarray(Image.open(REBUILT_PNG).convert("RGB"), dtype=np.int16)
rms = float(np.sqrt(((a - b).astype(np.float64) ** 2).mean()))
ok = (h1 == h2)

rep = {
    "schema": "reproduction-v2", "request_id": REQ, "run_id": RUN,
    "method": "isolated reopen + rerender; compare CONTENT SHA of decoded raw RGB",
    "declared_tolerance": "identical decoded RGB bytes at 420x620 / 8 samples / seed 0 / same camera + compositor",
    "fixed_conditions": {"resolution": [420, 620], "samples": 8, "seed": 0,
                         "camera": "Camera", "compositor": "on"},
    "commands": timings,
    "container_sha256_orig": hashlib.sha256(ORIG.read_bytes()).hexdigest(),
    "container_sha256_rebuilt": hashlib.sha256(REBUILT_PNG.read_bytes()).hexdigest(),
    "content_sha256_orig": h1, "content_sha256_rebuilt": h2,
    "shape": list(shp), "rms": round(rms, 4), "content_sha_match": ok, "pass": bool(ok),
    "note": "container SHA differs by design (PNG metadata); only content SHA is a gate.",
}
RUNDIR.mkdir(parents=True, exist_ok=True)
(RUNDIR / "reproduction.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
(V15 / "evidence" / "reproduction.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
print("REPRO", "PASS" if ok else "FAIL", "rms", round(rms, 4), "timings", [t["wall_seconds"] for t in timings])
