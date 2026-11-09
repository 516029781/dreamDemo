# -*- coding: utf-8 -*-
"""Compare the 420x735 isolated reproduction with master_raw (RMS <= 8)."""
import json
import sys

import numpy as np
from PIL import Image

repro, master, out = sys.argv[1], sys.argv[2], sys.argv[3]
a = Image.open(repro).convert("RGB").resize((420, 735))
b = Image.open(master).convert("RGB").resize((420, 735))
ra = np.asarray(a, dtype=np.float32)
rb = np.asarray(b, dtype=np.float32)
rms = float(np.sqrt(((ra - rb) ** 2).mean()))
payload = {"schema": "reproduction-v1", "master": master, "repro": repro,
           "size": [420, 735], "rms": round(rms, 3), "tolerance": 8.0,
           "samples": 24, "pass": rms <= 8.0,
           "note": "Cycles same-scene re-render; pass by RMS tolerance (v09 baseline 3.557)."}
open(out, "w", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False, indent=1))
print("REPRO_RMS %.3f" % rms, "PASS" if payload["pass"] else "FAIL")
