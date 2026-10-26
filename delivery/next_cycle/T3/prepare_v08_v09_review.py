"""Prepare V08/V09 review requests and set P08 waiting_review (no approvals)."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def entry(path):
    return {"path": path, "sha256": sha(ROOT / path)}


def write(path, value):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    rubric = json.loads((ROOT / "art_review/rubric.json").read_text(encoding="utf-8-sig"))
    sample_manifest = "delivery/next_cycle/T2/sample_manifest.json"
    full_manifest = "art_review/submissions/candidate_full/manifest.json"
    gates = [f"H{i:02d}" for i in range(1, 10)]
    quality = [f"Q{i:02d}" for i in range(1, 10)]
    cards = {}
    for card, dims in rubric["cards"].items():
        cards[card] = {"dimensions": [{"id": d["id"], "score": None, "observation": "",
                                       "gap": "", "action_or_acceptance_reason": "",
                                       "reference_evidence": [], "candidate_evidence": []}
                                      for d in dims]}
    v08_template = {
        "schema_version": "1.1.0",
        "kind": "independent_visual_review_template_not_actual",
        "report_kind": "template_not_actual_review",
        "template_only": True,
        "status": "pending_independent_review",
        "stage": "scene_demo",
        "reviewer": {"id": None, "mode": "independent"},
        "reviewed_at": None,
        "manifest": entry(sample_manifest),
        "full_candidate_manifest": entry(full_manifest),
        "contract": entry("art_review/harness_contract.json"),
        "rubric": entry("art_review/rubric.json"),
        "style_baseline": "P1 t015/t044/t084; current rubric 1.2.0",
        "gates": {g: {"status": "not_checked", "evidence": [], "reason": None} for g in gates},
        "quality_checks": {q: {"status": "not_checked", "evidence": [], "reason": None, "measurements": {}} for q in quality},
        "cards": cards,
        "defects": [],
        "thresholds": {"per_card_minimum": 85, "core_minimum": 3, "dimension_minimum": 2,
                       "unresolved_blocking_major_allowed": 0},
        "overall_decision": "pending",
        "limitations": ["Template only. The producer did not fill scores or approve this candidate."],
    }
    write("delivery/next_cycle/T3/V08_review_request/independent_review_template.json", v08_template)

    fixes = json.loads((ROOT / "planning/execution/workflow_fixes.json").read_text(encoding="utf-8-sig"))["issues"]
    defects = json.loads((ROOT / "art_review/reports/independent_20261024/defects.json").read_text(encoding="utf-8-sig"))["defects"]
    defect_rows = []
    for item in fixes + defects:
        defect_rows.append({"id": item["id"],
                            "severity": item.get("severity") or ("major" if item.get("priority") in ("high", "medium") else "minor"),
                            "status": "pending_independent_check",
                            "evidence": [],
                            "note": ""})
    write("delivery/next_cycle/T3/V08_review_request/defects_template.json",
          {"kind": "V08_defects_template_not_actual", "defects": defect_rows})

    v08_doc = f"""# V08 独立样板视觉复核请求

状态：**等待 P08 通过后执行**。制作侧未评分、未签认。审核者应实际看原尺寸图、重开代表源、复现遮挡/输入/重置。

## 输入

- 样板 manifest：`{sample_manifest}` (sha256 `{sha(ROOT / sample_manifest)}`)
- 完整候选 manifest：`{full_manifest}` (sha256 `{sha(ROOT / full_manifest)}`)
- 当前画面：`delivery/next_cycle/T3/game_final4_formal_no_ui.png`、`game_final4_formal_ui.png`、`game_final4_dialogue.png`
- 对比：`delivery/next_cycle/T4/*_final4.png`
- Q 证据：`delivery/next_cycle/T5/behavior_results.json`、`q03_occlusion.json`、`q04_behavior.json`、`q05_board.json`、`q09_viewports.json`
- 源包：`delivery/courtyard_scene_demo_sources_v4.zip`
- 合并包：`delivery/candidate_full_review_pack_20261025_final.zip`
- 角色锁定播放：`art/phase1/character_playback_1015/idle_preview.png`、`move_preview.gif`、`move_contact.png`

## 要求

1. 自己打开原尺寸图（不是只看 producer 报告/缩略图），对照 P1 t015/t044/t084。
2. 重开代表源（MAP001/ENV006/PROP001/UI），复现树前/树后遮挡、暂停/对白/恢复、留言板 empty→full→reset、横竖 viewport。
3. 按 rubric 四卡逐维填分；样板门槛：每卡 >=85，核心 >=3，任意维 >=2，开放 blocking/major = 0；不得照抄制作自评。
4. 输出到 `delivery/next_cycle/T3/independent_review.json` 和 `delivery/next_cycle/T3/defects.json`；可复制本目录模板。
5. 未通过：列出具体缺陷并回退关联 V/A 任务；通过：进入 V09。制作方不会代签。
"""
    (ROOT / "delivery/next_cycle/T3/V08_review_request/REVIEW_REQUEST.md").write_text(v08_doc, encoding="utf-8")

    v09_request = {
        "kind": "sample_release_certificate_request_not_signed",
        "status": "pending_external_controller",
        "created_at": NOW,
        "stage": "scene_demo",
        "manifest": entry(sample_manifest),
        "independent_review": {"path": "delivery/next_cycle/T3/independent_review.json", "sha256": None,
                               "note": "V08 output; must exist and pass before V09."},
        "contract": entry("art_review/harness_contract.json"),
        "rubric": entry("art_review/rubric.json"),
        "approval_scope": "sample:scene_demo + current style baseline",
        "approver": None,
        "approver_key_id": None,
        "signature": None,
        "issued_at": None,
        "policy_note": ("Current effective contract is 1.3.0. If P08 activates the vNext 1.4.0 certificate policy, "
                        "use tools/art_harness.py certify with the controller-held ART_HARNESS_REVIEW_KEY; otherwise "
                        "the controller must issue an equivalent signed certificate/attestation externally. "
                        "No key or signature was generated by the producer."),
        "required_binding": ["manifest_sha256", "review_sha256", "contract_sha256", "approval_scope",
                             "approver_id", "approver_key_id", "issued_at"],
        "reject_if": ["no external key", "unsigned template", "producer-generated key", "review mismatch",
                      "open blocking/major", "stale manifest/contract"],
    }
    write("delivery/next_cycle/T3/V09_review_request/sample_release_certificate_request.json", v09_request)
    v09_doc = """# V09 控制器放行请求

状态：**等待 V08 独立复核通过**。制作侧不生成密钥、不签名、不改 accepted。

控制器需要：
1. 检查 `sample_release_certificate_request.json` 绑定的 manifest/review/contract 是否为 V08 通过的确切字节。
2. 在制作环境外提供 `ART_HARNESS_REVIEW_KEY`（≥32 字符）或等价外部签名设施；不得让制作模型创建生产密钥。
3. 若 P08 已启用 vNext 证书策略，按合同执行 `tools/art_harness.py certify`；否则由控制器在外部签发绑定当前内容的证书/attestation。
4. 输出 `delivery/next_cycle/T3/sample_release_certificate.json`；若缺密钥或独立 review，保持 waiting_review，不能填 pass。
"""
    (ROOT / "delivery/next_cycle/T3/V09_review_request/REVIEW_REQUEST.md").write_text(v09_doc, encoding="utf-8")

    # Ledger: P08 waiting_review only.
    ledger_path = ROOT / "PROJECT_TASKS.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8-sig"))
    for task in ledger["tasks"]:
        if task["id"] == "P08":
            task["status"] = "waiting_review"
            task["evidence_paths"] = [
                "delivery/next_cycle/T0/P08_review_request/REVIEW_REQUEST.md",
                "delivery/next_cycle/T0/P08_review_request/independent_rule_review_template.json",
                "delivery/next_cycle/T0/P08_precondition_check.json",
                "delivery/P08_review_pack_20261025.zip",
                "delivery/next_cycle/T0/gate_regression.json",
                "delivery/next_cycle/T4/producer_submission_check.json",
                "delivery/next_cycle/T7/I07_manifest_verify.json",
            ]
            task["resume_action"] = ("Independent reviewer: run tests/fixtures, fill delivery/next_cycle/T0/independent_rule_review.json; "
                                     "if fail reopen P02-P07; if pass proceed V08. Producer must not sign.")
            task["blocker"] = "Waiting for independent rule reviewer; no producer-side work remains."
        if task["id"] == "V08":
            task["evidence_paths"] = ["delivery/next_cycle/T3/V08_review_request/REVIEW_REQUEST.md",
                                      "delivery/next_cycle/T3/V08_review_request/independent_review_template.json",
                                      "delivery/next_cycle/T3/V08_review_request/defects_template.json"]
            task["resume_action"] = "Blocked by P08; independent reviewer fills sample review after P08 passes."
        if task["id"] == "V09":
            task["evidence_paths"] = ["delivery/next_cycle/T3/V09_review_request/REVIEW_REQUEST.md",
                                      "delivery/next_cycle/T3/V09_review_request/sample_release_certificate_request.json"]
            task["resume_action"] = "Blocked by V08; controller signs externally, no producer key."
    ledger["revision"] = "1.0.135"
    ledger["updated_at"] = NOW
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    checkpoint_path = ROOT / "delivery/next_cycle/last_checkpoint.json"
    cp = json.loads(checkpoint_path.read_text(encoding="utf-8-sig"))
    cp.update({"updated_at": NOW, "ledger_revision": "1.0.135",
               "status": "waiting_external_p08_independent_rule_review",
               "external_action_ids": ["P08"],
               "next_ready_task_ids": [],
               "p08_review_request": {
                   "request": "delivery/next_cycle/T0/P08_review_request/REVIEW_REQUEST.md",
                   "template": "delivery/next_cycle/T0/P08_review_request/independent_rule_review_template.json",
                   "precondition": "delivery/next_cycle/T0/P08_precondition_check.json",
                   "pack": "delivery/P08_review_pack_20261025.zip",
               },
               "next_review_chain": ["V08", "V09", "I08", "I09"],
               "how_to_resume": [
                   "Independent reviewer runs the P08 commands and writes delivery/next_cycle/T0/independent_rule_review.json.",
                   "If P08 passes, V08 independent reviewer uses delivery/next_cycle/T3/V08_review_request/.",
                   "After V08, controller uses delivery/next_cycle/T3/V09_review_request; never generate keys in producer workflow.",
               ]})
    checkpoint_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("P08 waiting_review; V08/V09 review requests written")


if __name__ == "__main__":
    main()
