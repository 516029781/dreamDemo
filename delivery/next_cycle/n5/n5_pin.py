"""Read the single formal n5 build pin.

Every n5 evidence step must resolve its build identity here, never by picking
the newest file under delivery/performance (that is the n4 P0-2 defect).
"""
import json
from pathlib import Path

ROOT = Path("C:/软件/鼠鼠")
PIN = ROOT / "delivery/next_cycle/n5/performance/formal_build.json"


def load_pin():
    if not PIN.is_file():
        raise SystemExit("no formal build pin at %s; run tools/n5_build.py first" % PIN)
    return json.loads(PIN.read_text(encoding="utf-8-sig"))


def build_id(pin=None):
    return (pin or load_pin())["build_id"]


def build_report(pin=None):
    return (pin or load_pin())["build_report_json"]


def build_log_path(pin=None):
    return ROOT / (pin or load_pin())["build_log"]
