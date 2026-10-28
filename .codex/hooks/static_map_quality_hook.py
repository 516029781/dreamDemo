"""Project-local, per-Codex-session P1 static-map completion hook.

The hook only arms on an explicit production prompt for this project and stores
state under ignored .codex/state/<session_id>. It never reads or writes user config.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / ".codex" / "state" / "static_map_runs"
HISTORY = STATE / "history"
GATE_SCRIPT = ROOT / "tools" / "static_map_quality_gate.py"


def output(value: dict) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def read_event() -> dict:
    try:
        value = json.load(sys.stdin)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def root_is_current_project(cwd: str) -> bool:
    # Avoid invoking Git here: its Windows console encoding can misdecode this
    # project's Chinese path. The hook file's own location is the trusted root.
    try:
        root = ROOT.resolve()
        current = Path(cwd).resolve()
        current.relative_to(root)
        return (root / ".git").exists() and (root / "AGENTS.md").is_file()
    except (OSError, ValueError):
        return False


def session_key(event: dict) -> str | None:
    value = str(event.get("session_id", ""))
    return value if re.fullmatch(r"[A-Za-z0-9_-]{8,160}", value) else None


def marker_path(key: str) -> Path:
    return STATE / f"{key}.json"


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def explicit_cancel(prompt: str) -> bool:
    return any(token in prompt for token in (
        "暂停静态地图", "取消静态地图", "停止静态地图制作", "不要继续制作地图",
        "先只讨论", "只讨论方案", "暂停这个制作任务", "取消这个制作任务",
    ))


def is_explicit_production_prompt(prompt: str) -> bool:
    p = prompt.casefold()
    if any(token in p for token in ("先不要执行", "不要修改", "只讨论", "先讨论", "仅讨论", "只出方案")):
        return False
    if "!p1-static-map-run" in p:
        return True
    has_target = any(token in p for token in ("p1", "静态地图", "秋日地图", "秋日静帧", "t084"))
    has_production_action = any(token in p for token in (
        "开始制作", "继续制作", "继续优化", "返修", "重渲染", "执行静态地图",
        "制作静态地图", "制作地图", "绘制地图", "一次性执行", "实际修改",
    ))
    discussion_only = any(token in p for token in (
        "如何实现", "给我方案", "出方案", "检查流程", "审核流程", "是否合理", "流程优化",
    ))
    return has_target and has_production_action and not discussion_only


def next_candidate() -> str:
    base = ROOT / "art" / "static_map" / "p1_autumn_courtyard"
    versions = []
    if base.is_dir():
        for item in base.iterdir():
            match = re.fullmatch(r"v(\d+)", item.name, re.IGNORECASE)
            if item.is_dir() and match:
                versions.append(int(match.group(1)))
    version = max(versions, default=0) + 1
    candidate = base / f"v{version:02d}"
    while candidate.exists():
        version += 1
        candidate = base / f"v{version:02d}"
    return candidate.relative_to(ROOT).as_posix()


def prompt_submit(event: dict, key: str) -> None:
    active = marker_path(key)
    prompt = str(event.get("prompt", ""))
    if active.exists() and explicit_cancel(prompt):
        active.unlink(missing_ok=True)
        output({"systemMessage": "本会话的 P1 静态地图质量闭环已按用户指示解除；其他会话状态不受影响。"})
        return
    if active.exists() or not is_explicit_production_prompt(prompt):
        return
    candidate = next_candidate()
    state = {
        "scope": "project_and_session_only",
        "session_id": key,
        "candidate": candidate,
        "armed_at": datetime.now(timezone.utc).isoformat(),
        "stop_checks": 0,
    }
    save(active, state)
    output({"systemMessage": f"已为本 Codex 会话启用 P1 静态地图质量闭环，候选目录：{candidate}。只在本项目、本会话生效；Stop 门禁要求按项目标准修复至 target_met，或提供经校验的真实外部阻塞证据。"})


def archive(active: Path, state: dict, result: dict) -> None:
    HISTORY.mkdir(parents=True, exist_ok=True)
    state["finished_at"] = datetime.now(timezone.utc).isoformat()
    state["final_gate"] = result
    suffix = re.sub(r"[^0-9A-Za-z_-]", "_", str(state.get("session_id", "unknown")))
    save(HISTORY / f"{suffix}.json", state)
    active.unlink(missing_ok=True)


def stop(event: dict, key: str) -> None:
    active = marker_path(key)
    if not active.is_file():
        return
    try:
        state = json.loads(active.read_text(encoding="utf-8-sig"))
        candidate = str(state.get("candidate", ""))
    except Exception:
        output({"decision": "block", "reason": "项目 Stop 门禁的会话状态损坏。请在本会话修复 .codex/state/static_map_runs 状态并重新运行项目质量门禁；不要直接结束任务。"})
        return
    gate_path = (ROOT / candidate).resolve()
    try:
        gate_path.relative_to(ROOT.resolve())
    except ValueError:
        output({"decision": "block", "reason": "项目 Stop 门禁候选目录越出仓库。请修复本会话状态中的 candidate 路径后继续。"})
        return
    try:
        result = __import__("runpy").run_path(str(GATE_SCRIPT))["evaluate"](gate_path)
    except Exception as exc:
        output({"decision": "block", "reason": f"P1 静态地图质量 gate 执行失败：{type(exc).__name__}: {exc}。请在本项目修复门禁脚本/报告后重新运行；不要把 gate 错误当成质量通过。"})
        return
    state["stop_checks"] = int(state.get("stop_checks", 0)) + 1
    state["last_gate"] = result
    save(active, state)
    if result.get("state") == "target_met" and result.get("stop_allowed") is True:
        archive(active, state, result)
        return
    if result.get("state") == "blocked_external" and result.get("stop_allowed") is True:
        archive(active, state, result)
        output({"systemMessage": f"P1 静态地图任务以真实外部阻塞结束，未达成 target_met。证据保存在 {candidate}/GATE_REPORT.json；报告中不得标记美术通过。"})
        return
    failures = result.get("failures", [])
    repair_items = result.get("repairs", [])
    lines = [f"P1 静态地图质量门禁未通过（候选 {candidate}，第 {state['stop_checks']} 次检查）。继续在本会话实际修复并重渲，不能正常结束："]
    lines.extend(f"- {item}" for item in failures[:12])
    for item in repair_items[:5]:
        if isinstance(item, dict):
            details = [f"{k}={item[k]}" for k in ("dimension", "gate_id", "defect", "cause", "action", "expected_effect", "verification") if item.get(k)]
            if details:
                lines.append("- 修复队列：" + "; ".join(details))
    lines.append("先核对固定参考 t084s 的 SHA 与同机位证据；按失败项改 Blender 原生源、重渲、更新 REVIEW.md/DELIVERY.json/GATE_REPORT.json 的绑定，然后重新运行 python tools/static_map_quality_gate.py --candidate " + candidate + "。若已由 Stop hook 继续过一次，不要重复复述计划，直接完成下一项具体修复。")
    output({"decision": "block", "reason": "\n".join(lines)[:7000]})


def main() -> int:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    event_name = ""
    if len(sys.argv) >= 3 and sys.argv[1] == "--event":
        event_name = sys.argv[2]
    event = read_event()
    key = session_key(event)
    if not key:
        # Fail open for unknown event/session data: never affect an unscoped conversation.
        return 0
    active = marker_path(key).is_file()
    cwd = str(event.get("cwd", ""))
    in_project = bool(cwd) and root_is_current_project(cwd)
    if event_name == "UserPromptSubmit":
        if active or in_project:
            prompt_submit(event, key)
    elif event_name == "Stop" and active:
        # Once armed, keep the gate bound to this exact session even if its cwd changes.
        stop(event, key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())