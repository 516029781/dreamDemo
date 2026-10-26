"""Normalise the build pin's recorded paths to repo-relative.

The first n5 build wrote absolute paths because the generator stripped
dirname(ROOT) instead of ROOT. Bindings reject absolute paths, and the build
itself is unchanged, so only the two path fields are rewritten; build_id,
output hash and the build report contents are left exactly as they were.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIN = os.path.join(ROOT, "delivery/next_cycle/n5/performance/formal_build.json")

with open(PIN, encoding="utf-8-sig") as fh:
    pin = json.load(fh)

for key in ("build_report", "build_log"):
    value = pin[key].replace("\\", "/")
    if os.path.isabs(value) or (len(value) > 1 and value[1] == ":"):
        pin[key] = os.path.relpath(value, ROOT).replace("\\", "/")

with open(PIN, "w", encoding="utf-8") as fh:
    json.dump(pin, fh, ensure_ascii=False, indent=2)
    fh.write("\n")

print(json.dumps({"build_id": pin["build_id"], "build_report": pin["build_report"],
                  "build_log": pin["build_log"],
                  "output_index_sha256": pin["output_index_sha256"]},
                 ensure_ascii=False))
