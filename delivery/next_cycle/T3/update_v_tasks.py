"""Update V03-V05 ledger entries, F05-F07 fixes and optimization rollout."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    path = ROOT / "PROJECT_TASKS.json"
    ledger = json.loads(path.read_text(encoding="utf-8-sig"))
    for task in ledger["tasks"]:
        if task["id"] == "V03":
            task["status"] = "done"
            task["evidence_paths"] = [
                "art/iterations/cycle_02/plants/source_export_index.json (v2, sha256 " + sha(ROOT / "art/iterations/cycle_02/plants/source_export_index.json") + ")",
                "delivery/next_cycle/T2/plant_group_v2.png (sha256 " + sha(ROOT / "delivery/next_cycle/T2/plant_group_v2.png") + ")",
                "delivery/next_cycle/T2/plant_closeups_v2.png (sha256 " + sha(ROOT / "delivery/next_cycle/T2/plant_closeups_v2.png") + ")",
                "delivery/next_cycle/T3/plant_final3_ENV007.png / ENV008.png / ENV009.png / ENV011.png",
            ]
            task["commands_run"] += [
                "powershell -File tools/blender/run_courtyard_build.ps1 -Stage map001 -> exit 0; gate pass",
                "node capture focusAsset ENV007/ENV008/ENV009/ENV011 -> 4 shots, 0 page errors",
            ]
            task["actual_exit_codes"] = [0, 0]
            task["self_check_note"] = "新增20处干草+10处落叶沿土缘/围栏分布并缩放0.9-1.3，环坛内加地被，灌木实例缩放0.85-1.15；背景加两排树篱与远景橄榄树冠带（无裸干）。路中留白保留。视觉通过仍需独立审核。"
            task["related_defects"] = ["F06"]
            task["attempts"] = 2
            task["resume_action"] = "V04/V05完成后进入V06冻结；P08独立审核不可自签。"
            task["completed_at"] = NOW
        if task["id"] == "V04":
            task["status"] = "done"
            task["evidence_paths"] = [
                "delivery/next_cycle/T2/lighting_profile_v2.json (固定ROI/绝对亮度/对比/比值解释, sha256 " + sha(ROOT / "delivery/next_cycle/T2/lighting_profile_v2.json") + ")",
                "delivery/next_cycle/T2/lighting_comparison_v2.png (sha256 " + sha(ROOT / "delivery/next_cycle/T2/lighting_comparison_v2.png") + ")",
                "tools/measure_lighting.js (可复跑, sha256 " + sha(ROOT / "tools/measure_lighting.js") + ")",
                "delivery/next_cycle/T3/game_final3_formal_no_ui.png (before/after 同机位)",
            ]
            task["commands_run"] += [
                "node tools/measure_lighting.js before final3 -> fixed ROI measurement",
                "python tools/cocos/build_web_desktop.py -> gate pass",
            ]
            task["actual_exit_codes"] = [0, 0]
            task["self_check_note"] = "固定正式机位(-2.5,11.5,-14.6; fov35)与静态ROI；key 72000->82000暖色、fill 26000->28000冷色、ambient 21000->23000。实测绝对亮度：paving lit 0、shadow -9.28、soil -1.37、tree +3.08、metal +5.47；shadow/lit 0.835->0.782，解释为阴影更深/对比更高，不再声称变亮。未加橙滤镜/DOF。角色clip time未单独测，标注限制。"
            task["related_defects"] = ["F06", "F07"]
            task["attempts"] = 2
            task["resume_action"] = "V06冻结前等待P08独立规则审核；制作侧不扩批。"
            task["completed_at"] = NOW
        if task["id"] == "V05":
            task["status"] = "done"
            task["evidence_paths"] = [
                "art/iterations/cycle_02/ui/source_export_index.json (v2, sha256 " + sha(ROOT / "art/iterations/cycle_02/ui/source_export_index.json") + ")",
                "delivery/next_cycle/T2/ui_comparison_v2.png (sha256 " + sha(ROOT / "delivery/next_cycle/T2/ui_comparison_v2.png") + ")",
                "delivery/next_cycle/T3/game_final3_dialogue.png",
                "demo/assets/scripts/CourtyardBootstrap.ts (UI colors/accents, sha256 " + sha(ROOT / "demo/assets/scripts/CourtyardBootstrap.ts") + ")",
            ]
            task["commands_run"] += [
                "python tools/cocos/build_web_desktop.py -> gate pass",
                "node delivery/next_cycle/_v06_game_shots.js final3 -> dialogue real canvas capture",
            ]
            task["actual_exit_codes"] = [0, 0]
            task["self_check_note"] = "对白/任务/菜单面板更半透明(alpha 222/218/225)，页签/提示/图标用青色点缀，新增薄荷下划线+手绘金线与图标；字号层级28/24/13。保留中文与纸纹理，厚边框观感降低但未完全移除；Toast避让沿用上轮。视觉通过仍需独立审核。"
            task["related_defects"] = ["F06"]
            task["attempts"] = 2
            task["resume_action"] = "V06冻结需V01-V05+P08；P08为外部独立审核，制作侧不得自签。"
            task["completed_at"] = NOW
    ledger["revision"] = "1.0.127"
    ledger["updated_at"] = NOW
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    fixes_path = ROOT / "planning/execution/workflow_fixes.json"
    fixes = json.loads(fixes_path.read_text(encoding="utf-8-sig"))
    for issue in fixes["issues"]:
        if issue["id"] == "F05":
            issue["resolution_evidence"] = issue.get("resolution_evidence", []) + [
                "delivery/next_cycle/T3/final3_bindings_summary.json",
                "delivery/next_cycle/T3/bindings/"]
            issue["status"] = "fixed_pending_independent_confirmation"
            issue["producer_fix_at"] = NOW
            issue["producer_progress"] = ("Final formal/dialogue shots recaptured with real canvas element capture "
                                          "(CSS rect 5,84.875,1280x720; backing 1280x720); 3/3 bindings verified. "
                                          "Old T1/T2 page screenshots remain historical, not final evidence.")
        if issue["id"] == "F06":
            issue["resolution_evidence"] = [
                "delivery/next_cycle/T4/tree_before_after_v2.png",
                "delivery/next_cycle/T4/material_closeups_v2.png",
                "delivery/next_cycle/T4/plant_background_v2.png",
                "delivery/next_cycle/T4/plant_closeups_v2.png",
                "delivery/next_cycle/T4/ui_comparison_v2.png",
                "delivery/next_cycle/T3/final3_bindings_summary.json"]
            issue["status"] = "fixed_pending_independent_confirmation"
            issue["producer_fix_at"] = NOW
            issue["producer_progress"] = ("V01-V05 producer rework complete: crown mass/clumps, warm palette, layered "
                                          "background/groundcover, material separation, translucent UI accents, real-canvas "
                                          "comparisons. Independent visual review still required; not self-signed.")
        if issue["id"] == "F07":
            issue["resolution_evidence"] = [
                "delivery/next_cycle/T2/lighting_profile_v2.json",
                "tools/measure_lighting.js",
                "delivery/next_cycle/T2/lighting_comparison_v2.png"]
            issue["status"] = "fixed_pending_independent_confirmation"
            issue["producer_fix_at"] = NOW
            issue["producer_progress"] = ("Fixed camera and static ROIs; absolute luminance and per-ROI contrast reported "
                                          "separately; ratio 0.835->0.782 now interpreted as deeper shadows/higher contrast, "
                                          "not brighter. Character clip time still not separately measured.")
    fixes["updated_at"] = NOW
    fixes_path.write_text(json.dumps(fixes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rollout_path = ROOT / "planning/execution/optimization_rollout.json"
    rollout = json.loads(rollout_path.read_text(encoding="utf-8-sig"))
    for measure in rollout["measures"]:
        if measure["id"] == "OPT04":
            measure["evidence"] = ["tools/blender/build_env_courtyard.py (3 crown candidates)",
                                   "tools/blender/run_courtyard_build.ps1 -Stage",
                                   "delivery/next_cycle/T4/tree_before_after_v2.png"]
            measure["remaining"] = "定向阶段构建与最多3候选已实际使用；候选对比仍由人工选择，未自动化。"
        if measure["id"] == "OPT05":
            measure["evidence"] = ["demo/assets/scripts/CourtyardBootstrap.ts",
                                   "delivery/next_cycle/T4/ui_comparison_v2.png"]
            measure["remaining"] = "UI在现有Cocos组件上统一改色/透明度/点缀，未逐界面重画；扩到全部状态仍待V09后。"
    rollout["updated_at"] = NOW
    rollout_path.write_text(json.dumps(rollout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("V03/V04/V05 done; revision", ledger["revision"])


if __name__ == "__main__":
    main()
