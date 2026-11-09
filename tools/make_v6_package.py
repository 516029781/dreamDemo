# -*- coding: utf-8 -*-
"""make_v6_package.py — 生成 20261103-space-base-v6 知识包（M0）。

做七件事：
 1. 建 knowledge/active/20261103-space-base-v6/
 2. REQUIREMENTS_BRIEF.md（REQ-01..28 = 25 必检 + 3 外置）
 3. test_cases.json（28 用例）
 4. RUN_CONTEXT.json
 5. RESOLVED_KNOWLEDGE.json（loaded 绑定 sha256）
 6. baselines/design_r03/（统一方案 v1.1 + v3.10 + build_scene_v6.py + spec r02 备份 + BASELINE_MANIFEST.json）
 7. HARNESS_SPEC.json 升 r03（20→25 必检，S11–S15 定义）
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUS = os.path.join(ROOT, "knowledge", "business", "space_base_minigame")
REQ = os.path.join(ROOT, "knowledge", "active", "20261103-space-base-v6")
RUN_ID = "20261103-2100"
BL = os.path.join(REQ, "runs", RUN_ID, "baselines", "design_r03")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    unified = os.path.join(ROOT, "planning", "art", "SPACE_BASE_UNIFIED_PLAN_20261103.md")
    newplan = os.path.join(ROOT, "planning", "art", "SPACE_BASE_NEW_PLAN_20261103.md")
    build_v6 = os.path.join(ROOT, "tools", "blender_space_base", "build_scene_v6.py")
    assert os.path.exists(unified) and os.path.exists(newplan) and os.path.exists(build_v6), \
        "先复制出 build_scene_v6.py 再跑本脚本"

    # ---- 7. spec r03 ----
    spec_p = os.path.join(BUS, "HARNESS_SPEC.json")
    spec = json.load(open(spec_p, encoding="utf-8"))
    r03 = dict(spec)
    r03["spec_version"] = "r03"
    r03["supersedes"] = "r02"
    new_checks = [
        {"check_id": "S11", "rule_ref": "unified plan §9.1 / r03", "type": "mechanical",
         "statement": "明度跨度：逐区 L 的 p25–p75 ≥0.22，任一区域中位 ≤0.80",
         "evidence_fields": ["value_span"], "on_fail": "rework", "diagnostic_only": True},
        {"check_id": "S12", "rule_ref": "unified plan §9.1 / r03", "type": "mechanical",
         "statement": "英雄图水面边界 1px 最大跳变 ≤8/255；水面出画",
         "evidence_fields": ["water_border"], "on_fail": "rework", "diagnostic_only": False},
        {"check_id": "S13", "rule_ref": "unified plan §9.1 / r03", "type": "mechanical",
         "statement": "插画指标：三峰直方图峰距 ≥0.12；暗部 b* −6±2；笔触覆盖 ≥30%",
         "evidence_fields": ["illustration_metrics"], "on_fail": "rework", "diagnostic_only": True},
        {"check_id": "S14", "rule_ref": "unified plan §9.1 / r03", "type": "mechanical",
         "statement": "总裁盒可读：盒内 std ≥0.15、mean ≤0.88、可见家具 ≥3 件",
         "evidence_fields": ["ceo_readout"], "on_fail": "rework", "diagnostic_only": False},
        {"check_id": "S15", "rule_ref": "unified plan §9.1 / r03", "type": "mechanical",
         "statement": "逐区配色：五区 |ΔH|≤12°、|ΔS|≤0.08、|ΔL|≤0.06（color_probe vs PALETTE.json 换算目标）",
         "evidence_fields": ["color_probe"], "on_fail": "rework", "diagnostic_only": True},
    ]
    have = {c["check_id"] for c in r03["checks"]}
    r03["checks"] = r03["checks"] + [c for c in new_checks if c["check_id"] not in have]
    r03["required_checks"] = spec["required_checks"] + ["S11", "S12", "S13", "S14", "S15"]
    r03["end_policy"] = dict(spec["end_policy"])
    r03["end_policy"]["required_for_target_met"] = r03["required_checks"]
    r03["notes_r03"] = [
        "新增 S11–S15（统一方案 §9.1）；S11/S13/S15 首两切片 diagnostic_only",
        "总裁盒开顶、保形换色、插画 I2+（统一方案 v1.1 §13.1 预置决策）",
        "r03 生效需控制器签认；未签认前交付标 draft_pending_controller",
    ]
    w(spec_p, json.dumps(r03, ensure_ascii=False, indent=1))

    # ---- 6. baseline ----
    os.makedirs(BL, exist_ok=True)
    copies = {
        unified: "SPACE_BASE_UNIFIED_PLAN_20261103.md",
        newplan: "SPACE_BASE_NEW_PLAN_20261103.md",
        build_v6: "build_scene_v6.py",
        os.path.join(ROOT, "tools", "blender_space_base", "render_v6_views.py"): "render_v6_views.py",
        os.path.join(ROOT, "tools", "space_base_v6_post.py"): "space_base_v6_post.py",
        os.path.join(ROOT, "tools", "space_base_check_v4.py"): "space_base_check_v4.py",
        spec_p: "HARNESS_SPEC.json",
    }
    entries = []
    for src, name in copies.items():
        assert os.path.exists(src), f"缺 {src}"
        dst = os.path.join(BL, name)
        shutil.copyfile(src, dst)
        entries.append({"path": name, "sha256": sha(dst)})
    manifest = {"schema": "baseline-manifest-v1", "request_id": "20261103-space-base-v6",
                "run_id": RUN_ID, "design_version": "design_r03",
                "unified_plan": "SPACE_BASE_UNIFIED_PLAN_20261103.md (v1.1)",
                "geometry_plan": "SPACE_BASE_NEW_PLAN_20261103.md (v3.10)",
                "entries": entries}
    w(os.path.join(BL, "BASELINE_MANIFEST.json"),
      json.dumps(manifest, ensure_ascii=False, indent=1))

    # ---- 2. brief ----
    req_rows = [
        ("REQ-01", "G1", "240 m = 1680 px；master 3360×5880；误差 ≤2 px", "必检"),
        ("REQ-02", "G2", "遮住文字仍能辨 H1/H2/H3/H4/总裁/花园/试车间", "必检"),
        ("REQ-03", "G3", "总裁两竖梯入口可读；落地层实墙；环廊摸不到门", "必检"),
        ("REQ-04", "G4", "花园北口可通行；撤离黄框为黄色", "必检"),
        ("REQ-05", "G5", "从坞门看，集装箱挡住撤离黄框（A/B 对照）", "必检"),
        ("REQ-06", "G6", "无悬浮/断墙/穿模；布尔开洞无破面", "必检"),
        ("REQ-07", "G7", "四边跟随边界不越界；主图无黑边", "必检"),
        ("REQ-08", "G8", "花园与堤道接缝材质/分缝连续", "必检"),
        ("REQ-09", "W1", "JPEG ≤3 MB、1680×2478、无 alpha", "必检"),
        ("REQ-10", "W2", "主包算术 ≤4 MB；主包+分包 ≤30 MB", "必检"),
        ("REQ-11", "S1", "陆地相对浅色占比 ≥45%；室内地面 L ≥0.60 护栏", "必检"),
        ("REQ-12", "S2", "HAAVK 绿 ≤8%，只在黑室涂装板/竖板（3–4 块）", "必检"),
        ("REQ-13", "S3", "橙 ≤2%，只在警示/扶手/门头", "必检"),
        ("REQ-14", "S4", "五室各一个色相签名", "必检"),
        ("REQ-15", "S5", "无圆角倒角；管线本身圆管不算", "必检"),
        ("REQ-16", "S6", "地面 3×3 分区与墙脚带成立", "必检"),
        ("REQ-17", "S7", "阴影硬边；总裁为唯一暖区", "必检"),
        ("REQ-18", "S8", "≥8 类材质有 base/roughness 变化", "必检"),
        ("REQ-19", "S9", "≥500 个硬表面对象带 Bevel", "必检"),
        ("REQ-20", "S10", "核心区 ≥14 px/m，与主图同源", "必检"),
        ("REQ-21", "A1", "角色阴影方向（无角色层，外置）", "外置"),
        ("REQ-22", "W3", "真机首帧 ≤1.5 s（外置）", "外置"),
        ("REQ-23", "W4", "低端机自动降级（外置）", "外置"),
        ("REQ-24", "S11", "逐区明度跨度 p25–p75 ≥0.22；任一区中位 ≤0.80", "必检*"),
        ("REQ-25", "S12", "英雄图水面边界 ≤8/255；水面 2000² 出画", "必检"),
        ("REQ-26", "S13", "三峰峰距 ≥0.12；暗部 b* −6±2；笔触覆盖 ≥30%", "必检*"),
        ("REQ-27", "S14", "总裁盒内 std ≥0.15、mean ≤0.88、可见家具 ≥3", "必检"),
        ("REQ-28", "S15", "五区 |ΔH|≤12°、|ΔS|≤0.08、|ΔL|≤0.06（M8.5 硬门）", "必检*"),
    ]
    lines = [
        "# N0 需求 Brief：航天基地静态地图 r03（保形换色 + 开顶 + 插画 I2+）",
        "",
        "- business_id：`space_base_minigame`",
        "- request_id：`20261103-space-base-v6`",
        "- task_mode：`production`　｜　deliverable_type：`static_map`",
        "- 变更依据：用户 2026-11-03「将方案给harness工作流程开发」（统一方案 v1.1 §13 确认）",
        "- 设计口径：`SPACE_BASE_UNIFIED_PLAN_20261103.md` **v1.1（画面/开发唯一口径）**",
        "  + `SPACE_BASE_NEW_PLAN_20261103.md` v3.10（几何/玩法，形不动）",
        "- 状态：`confirmed`（预置决策 P1–P7 按默认执行；Q1=I2+、Q2=20°、Q3=开顶）",
        "",
        "## 1. 相对 v05 的变更",
        "",
        "| # | 变更 | 验收 |",
        "|---|---|---|",
        "| 1 | 五区保形换色（H1 #547684 / H2 #477A8A / H3 #3A6DBF / H4 #58837D / C5 #95755B） | S15 全 OK |",
        "| 2 | 总裁盒开顶：删玻璃顶、0.6 m 女儿墙 + 黄铜压顶、0.8 m 檐口、自发光 0.35→0.07 | S14 |",
        "| 3 | 桁架 6 道/室 + 行车梁（H4×2、H3×1）+ 吊灯 4 组/室 | T4 ≥6 道投影 |",
        "| 4 | 水面 2000² 出画 + 冷渐变天空 + 仅 hero 雾 + 三层山脊重放 | S12 |",
        "| 5 | 插画 shader：压 V 三档 + Soft Light 0.40 + 阴影 #5A6470 + 露白 + 方向笔触 | S13 |",
        "| 6 | 2D 层：抖动 1–2 px、纸纹 6%、颗粒 σ1.8、暗角 0.12、D1–D10 标注 | A1–A10 |",
        "| 7 | 花园压暗 → 0.74；黑室绿墙只留 3–4 块涂装板；蓝室灯带改蓝；撤离点铺 #467CCD | S2/T1 |",
        "",
        "## 2. 固定输入（design_r03）",
        "",
        "| 项 | 值 |",
        "|---|---|",
        "| 几何/玩法 | v3.10（§1–§8），世界 240×420，北朝上 |",
        "| 相机 | 正交 ortho_scale=420；核心 ortho 148；hero 85 mm f/4（58 mm→85 mm 调整见 REPRODUCE） |",
        "| 整图 | 1680×2478（70 px 出血）；master 3360×5880；核心 2072×1876（14 px/m）；英雄 1920×1080 |",
        "| 渲染 | 主图 32 spp；核心 32；英雄 48 |",
        "| 画风 | I2+（9 项手法）；字体不随包（数字自绘 + OFL 中文） |",
        "",
        "## 3. 需求与验收",
        "",
        "| REQ | 检查 | 要求 | 本轮 |",
        "|---|---|---|---|",
    ]
    for rid, chk, txt, kind in req_rows:
        lines.append(f"| {rid} | {chk} | {txt} | {kind} |")
    lines += [
        "",
        "> 必检* = 首两切片 diagnostic_only（S11/S13/S15）；S15 在 M8.5 为硬门。",
        "",
        "## 4. 不做",
        "",
        "- 不改 v3.10 几何/玩法口径；不用 AI 直出整图；不随包商业字体；I3 手绘贴图不做。",
        "- A1/W3/W4 外置；导出图不替代可编辑源。",
        "",
    ]
    w(os.path.join(REQ, "REQUIREMENTS_BRIEF.md"), "\n".join(lines))
    brief_p = os.path.join(REQ, "REQUIREMENTS_BRIEF.md")

    # ---- 3. test cases ----
    files = {
        "v06": "art/static_map/space_base_minigame/v06",
    }
    def case(tid, rid, ctype, m, pc, ev_rel, diag=False, resp="automated"):
        return {"test_id": tid, "covers": [rid], "stage": "final", "check_type": ctype,
                "responsible": "producer" if ctype == "visual" else resp,
                "input": {"files": [f"{files['v06']}/renders/space_base_v06_master.png"]},
                "method": m, "pass_criteria": pc,
                "evidence_path": f"runs/{RUN_ID}/evidence/{ev_rel}",
                "diagnostic_only": diag, "failure_rule": "重渲并重跑对应证据"}
    cases = [
        case("TEST-G1", "REQ-01", "mechanical", "camera_projection 正交换算", "240m=1680px；误差≤2px", "G1/camera_projection.json"),
        case("TEST-G2", "REQ-02", "visual", "遮字逐区辨认", "七区可辨；独立审核复核", "G2/mentions.md"),
        case("TEST-G3", "REQ-03", "visual", "总裁盒开顶后两梯与家具辨认", "两梯可见、x=120 实墙、家具 ≥3 件", "G3/notes.md"),
        case("TEST-G4", "REQ-04", "mechanical", "探针：花园北口非水非墙；撤离黄框黄色", "全部探针命中", "G4/probes.json"),
        case("TEST-G5", "REQ-05", "visual", "A/B 对照：集装箱遮挡黄框", "B 图黄框不可见", "G5/pair_note.md"),
        case("TEST-G6", "REQ-06", "mechanical", "geom_check 扫视 6 格", "无悬浮/断墙/穿模", "G6/geom_check.json"),
        case("TEST-G7", "REQ-07", "mechanical", "四边均值非黑", "四边 mean>18", "G7/borders.json"),
        case("TEST-G8", "REQ-08", "visual", "南出口接缝同屏", "材质/分缝连续", "G8/notes.md"),
        case("TEST-W1", "REQ-09", "mechanical", "JPEG 文件检查", "≤3MB、1680×2478、RGB", "W1/file_check.json"),
        case("TEST-W2", "REQ-10", "mechanical", "包体算术", "主包 ≤4MB；总 ≤30MB", "W2/package.json"),
        case("TEST-S1", "REQ-11", "mechanical", "陆地相对浅色占比", "≥45%；室内地面 L≥0.60", "S1/value_stats.json"),
        case("TEST-S2", "REQ-12", "mechanical", "绿占比", "≤8%", "S2/hue_stats.json"),
        case("TEST-S3", "REQ-13", "mechanical", "橙占比", "≤2%", "S3/hue_stats.json"),
        case("TEST-S4", "REQ-14", "visual", "五室色相签名", "五室各一签名", "S4/notes.md"),
        case("TEST-S5", "REQ-15", "visual", "特写无圆角", "R≤0.05", "S5/notes.md"),
        case("TEST-S6", "REQ-16", "visual", "3×3 分区与墙脚带", "成立；竖缝降级记录", "S6/notes.md"),
        case("TEST-S7", "REQ-17", "visual", "阴影硬边；总裁唯一暖区", "成立", "S7/notes.md"),
        case("TEST-S8", "REQ-18", "mechanical", "材质分层统计", "≥8 类", "S8/material_layers.json"),
        case("TEST-S9", "REQ-19", "mechanical", "Bevel 计数", "≥500", "S9/bevel_count.json"),
        case("TEST-S10", "REQ-20", "mechanical", "核心区密度", "≥14 px/m 同源", "S10/core_density.json"),
        case("TEST-A1", "REQ-21", "external", "运行时核对", "无角色层，记外置", "external/A1.md"),
        case("TEST-W3", "REQ-22", "external", "真机首帧", "≤1.5s，记外置", "external/W3.md"),
        case("TEST-W4", "REQ-23", "external", "低端机降级", "记外置", "external/W4.md"),
        case("TEST-S11", "REQ-24", "mechanical", "逐区 L 分位统计", "p25–p75 ≥0.22；中位 ≤0.80", "S11/value_span.json", diag=True),
        case("TEST-S12", "REQ-25", "mechanical", "英雄图水域边界梯度扫描", "≤8/255", "S12/water_border.json"),
        case("TEST-S13", "REQ-26", "mechanical", "三峰/b*/笔触覆盖", "峰距≥0.12；b* −6±2；覆盖≥30%", "S13/illustration_metrics.json", diag=True),
        case("TEST-S14", "REQ-27", "mechanical", "总裁盒投影矩形统计", "std≥0.15；mean≤0.88；家具≥3", "S14/ceo_readout.json"),
        case("TEST-S15", "REQ-28", "mechanical", "color_probe 五区比对", "五区全 OK（M8.5 硬门）", "S15/color_probe.json", diag=True),
    ]
    tc = {"schema": "test-cases-v1", "request_id": "20261103-space-base-v6",
          "business_id": "space_base_minigame", "version": "r03",
          "bound_brief_sha256": sha(brief_p),
          "bound_design_sha256": sha(unified),
          "bound_design_snapshot": f"runs/{RUN_ID}/baselines/design_r03/SPACE_BASE_UNIFIED_PLAN_20261103.md",
          "cases": cases}
    w(os.path.join(REQ, "test_cases.json"), json.dumps(tc, ensure_ascii=False, indent=1))

    # ---- 4. run context ----
    bl_manifest_p = os.path.join(BL, "BASELINE_MANIFEST.json")
    rc = {
        "schema": "run-context-v1", "project_root": "C:/软件/鼠鼠",
        "session_id": "workbuddy-2026-11-03-space-base",
        "request_id": "20261103-space-base-v6", "run_id": RUN_ID,
        "task_mode": "production", "business_id": "space_base_minigame",
        "deliverable_type": "static_map",
        "knowledge_snapshot": {
            "manifest": "knowledge/business/manifest.json",
            "manifest_sha256": sha(os.path.join(ROOT, "knowledge/business/manifest.json"))
            if os.path.exists(os.path.join(ROOT, "knowledge/business/manifest.json")) else "absent",
            "business_version": "r03", "art_base": "v05",
            "lifecycle_contract": "knowledge/common/dev_core/HARNESS_LIFECYCLE.md"},
        "design_baseline": {
            "path": f"knowledge/active/20261103-space-base-v6/runs/{RUN_ID}/baselines/design_r03/BASELINE_MANIFEST.json",
            "status": "confirmed",
            "confirmed_basis": "用户 2026-11-03「将方案给harness工作流程开发」= 统一方案 v1.1 确认（Q1=I2+/Q2=20°/Q3=开顶）",
            "baseline_manifest_sha256": sha(bl_manifest_p)},
        "candidate": {"path": "C:/软件/鼠鼠/art/static_map/space_base_minigame/v06",
                      "write_owner_run": RUN_ID, "mode": "write"},
        "checks": {"harness_spec": "knowledge/business/space_base_minigame/HARNESS_SPEC.json",
                   "manual_check_set": ["file existence", "sha binding", "camera projection",
                                        "isolated reopen reproduction", "producer visual self-review"]},
        "created_at": "2026-11-03T21:00+08:00",
        "notes": "r03：保形换色 + 总裁盒开顶 + 插画 I2+；v05 只读留档。",
    }
    w(os.path.join(REQ, "RUN_CONTEXT.json"), json.dumps(rc, ensure_ascii=False, indent=1))

    # ---- 5. resolved knowledge ----
    loaded_paths = [
        unified, newplan,
        os.path.join(ROOT, "planning", "art", "SPACE_BASE_ART_STYLE_DF_REFERENCE_20261102.md"),
        os.path.join(ROOT, "reference", "_df_screenshots", "PALETTE.json"),
        os.path.join(ROOT, "knowledge", "business", "space_base_minigame", "BUSINESS_PROFILE.md"),
        os.path.join(BUS, "HARNESS_SPEC.json"),
    ]
    loaded = []
    for p in loaded_paths:
        if os.path.exists(p):
            loaded.append({"path": os.path.relpath(p, ROOT).replace("\\", "/"),
                           "sha256": sha(p), "role": "design/reference"})
    rk = {
        "schema": "resolved-knowledge-v1", "request_id": "20261103-space-base-v6",
        "run_id": RUN_ID, "business_id": "space_base_minigame",
        "decisions": [
            "Q1=I2+（预置 P1）", "Q2=斜角保持 20°（预置 P2 同源）", "Q3=总裁盒开顶（预置 P2）",
            "换色公式 L'=0.34+0.55L、S≤0.85，保形换色（模拟 S1 48.7% 达标）",
            "新门禁 S11/S13/S15 首两切片 diagnostic_only（预置 P7）",
        ],
        "open_questions": [
            "S6 墙竖缝降级与 S1 全帧口径待控制器签认（沿用 r02 遗留）",
        ],
        "conflicts": [],
        "loaded": loaded,
    }
    w(os.path.join(REQ, "RESOLVED_KNOWLEDGE.json"), json.dumps(rk, ensure_ascii=False, indent=1))

    print("PACKAGE_OK", REQ)
    print("brief_sha", sha(brief_p))
    print("unified_sha", sha(unified))


if __name__ == "__main__":
    main()
