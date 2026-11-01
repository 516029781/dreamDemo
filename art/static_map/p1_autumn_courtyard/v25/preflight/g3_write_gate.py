# -*- coding: utf-8 -*-
"""生成 GATE_REPORT.json（按 p1-static-map-quality-gate/v1 schema），SHA 全部现算。"""
import hashlib
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(BASE, "..", "..", "..", ".."))
REL = "art/static_map/p1_autumn_courtyard/v21"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


paths = {
    "reference": "reference/_raw_screenshots/P1/t084s.jpg",
    "scene": f"{REL}/scene.blend",
    "render": f"{REL}/renders/final.png",
    "review": f"{REL}/REVIEW.md",
    "delivery": f"{REL}/DELIVERY.json",
    "profile": f"{REL}/reference_analysis/P1_REFERENCE_PROFILE.json",
}
bindings = {k: {"path": v, "sha256": sha(os.path.join(ROOT, v))} for k, v in paths.items()}

W = {"composition_and_space": 20, "object_structure": 20, "surface_materials": 20,
     "vegetation": 15, "lighting_depth": 15, "style_cohesion": 10}
dims = {
    "composition_and_space": {"score": 3.0, "evidence": "六个锚点齐全（左树、右草池、台阶栏杆、设备、水口、石板平台），但顶部无天空与远树、广场下半 55% 空场、透视偏俯视"},
    "object_structure": {"score": 3.0, "evidence": "台阶有厚度与栏杆，圆筒池有肋条与厚边，设备成组并有管线连接，新增挡土墙承托水岸；中央设备仍偏简化"},
    "surface_materials": {"score": 3.0, "evidence": "石板同族、接缝连续、台阶与平台同材质；近景缺污渍与磨损，金属锈迹不足，1:1 裁切仍偏干净"},
    "vegetation": {"score": 2.75, "evidence": "左树有主干主枝与冠形并已加暖呈琥珀；右草池仍偏白偏疏，未连成参考的深金褐起伏体块，根部偏空"},
    "lighting_depth": {"score": 2.75, "evidence": "冷蓝灰水与暖石地分工成立；阴影偏软、暗部锚点不足，前景与背景明度接近，缺参考的长斜影重量"},
    "style_cohesion": {"score": 3.0, "evidence": "全图同一套风格化 3D 语言，硬表面与植被质感一致，没有突兀低模或贴片语言混入"},
}
total = round(sum(W[k] * v["score"] / 4 for k, v in dims.items()), 2)

portable = os.path.join(ROOT, "..", "..", "..", "tmp", "v21_portable", "renders", "portable.png")
portable = os.path.abspath(portable)
if not os.path.exists(portable):
    for cand in ("C:/tmp/v21_portable/renders/portable.png",):
        if os.path.exists(cand):
            portable = cand
            break

report = {
    "schema": "p1-static-map-quality-gate/v1",
    "candidate_id": "v21",
    "status": "rework_required",
    "bindings": bindings,
    "producer_review": {
        "reviewer_id": "producer:v21-self-assessment",
        "reference_sha256": bindings["reference"]["sha256"],
        "render_sha256": bindings["render"]["sha256"],
        "dimensions": dims,
        "total_score": total,
    },
    "combo_checks": {
        "floor": {"status": "pass", "evidence": "主铺地是一套大板家族，接缝方向与板材尺度在画面内连贯，平台与台阶同材质，近图可见倒角与磨边"},
        "tree": {"status": "rework", "evidence": "左树有主干与主次枝，但冠内叶簇偏薄、透空过多，外缘缺少受光层次，50% 缩图仍读成稀疏枝条"},
        "grass": {"status": "rework", "evidence": "右侧圆筒池顶草偏白偏疏，未连成连续起伏体块，池沿在局部仍可见，根部缺少暗部"},
        "lighting": {"status": "rework", "evidence": "冷蓝灰水与暖石地分工成立，但阴影偏软、暗部锚点不足，前景与背景明度接近，缺长斜影"},
    },
    "hard_gates": {
        "foreground_steps_railings": {"status": "pass", "evidence": "前景台阶有厚度、多级踏步与栏杆，50% 缩图可读出平台高差与扶手透视"},
        "right_grass_cylinder": {"status": "pass", "evidence": "右侧两组圆筒草池有弧面、竖向肋条与厚边，占位与参考同一区域"},
        "cohesive_non_checkerboard_ground": {"status": "pass", "evidence": "石板为同一尺寸家族的通缝排布，无棋盘格与全屏随机噪声，接缝走向与透视一致"},
        "tree_branching_negative_space": {"status": "pass", "evidence": "树冠由主干与主次枝撑起，冠形有不等大负空间，不是规则球团或重复尖片"},
        "dense_wavy_grass_canopy": {"status": "rework", "evidence": "草池顶部未形成连续起伏体块，局部可见池沿，草束偏白偏疏"},
        "functional_midground_structure": {"status": "pass", "evidence": "中景管线、格栅、机柜、压力罐成组并落在同一基座上，有支撑与连接，不是孤立方盒"},
        "cool_soft_background": {"status": "pass", "evidence": "水面为冷蓝灰且比主景软，挡土墙与台地压住水沿，未出现棕色硬几何填满远景"},
        "materials_resolve": {"status": "rework", "evidence": "石板无污渍、金属无锈，近景 1:1 仍显干净，缺少参考的磨损与旧化层"},
    },
    "reproducibility": {
        "scene_reopened": True,
        "reopen_dir": "C:/tmp/v21_portable",
        "exit_code": 0,
        "missing_external_images": 0,
        "render_sha256": sha(portable) if os.path.exists(portable) else "missing",
        "note": "复制 scene.blend、background_src、assets 到临时目录重开并渲染 25% 预览，0 缺失贴图；该 sha 属预览图，不是最终图。",
    },
    "background_measurement": {
        "method": "全画幅色彩/位置分类（含 world）+ 射线首命中分类 + world 洋红暴露检查",
        "reference_fraction_of_observable_mask": 0.10287,
        "candidate_fraction_color": 0.18523,
        "candidate_fraction_raycast": 0.01668,
        "difference_pp_color": 8.24,
        "max_allowed_pp": 3.0,
        "world_included": True,
        "card_toggle_difference_used": False,
        "validity": "approximate_bounds_only",
        "caveat": "色彩法把阴影与暖色前景误判为 A/K；射线法未命中相机子级景片（K=0）。两者只作上下界，不构成通过依据。",
    },
    "independent_review": {"status": "not_submitted",
                           "reason": "制作自评 73.12 < 85、植被与光色两维 < 3，按工作单先修源再送盲评",
                           "self_approval": False},
    "repair_queue": [
        {"dimension": "composition_and_space",
         "defect": "画面顶部没有天空与远树，背景被压在 0–17%；广场下半约 55% 为空场，透视偏俯视",
         "cause": "相机高 8.2 m、俯角 20.67°，视平线落在画幅上方 48.9%，顶部只能容纳地面与水面",
         "action": "另立对照基线：相机降到 3.5–4.5 m、俯角 10–12°，把台阶/平台/岸沿/水面作为一组重排并重投影",
         "expected_effect": "视平线进入 8–18%，天空与远岸可见，广场占比下降",
         "verification": "重做 G1 三图并核对六锚点投影误差 ≤3pt"},
        {"dimension": "vegetation",
         "defect": "右草池偏白偏疏，未连成金褐起伏体块；树冠叶簇偏薄、透空过多",
         "cause": "草卡基色偏亮且根部无暗层，叶卡数量不足、缺内层遮挡",
         "action": "压深 Dry grass/Grass 基色，加根部暗层与外倾草梢；树冠补内层暗叶并提高叶卡密度",
         "expected_effect": "50% 缩图草池成为连续体块，树冠不透空",
         "verification": "50% 缩图与 100% 裁切前后对照"},
        {"dimension": "lighting_depth",
         "defect": "阴影偏软、暗部锚点不足，前景与背景明度接近",
         "cause": "三盏面积补光能量仍偏高，场景缺深色大体块",
         "action": "补光再降 30%，设备内腔与树冠内侧加暗，保持右上主光方向的投影长度",
         "expected_effect": "暗部 <40 占比升到 3.5–5%，出现明确长斜影",
         "verification": "灰度直方图与 50% 灰度图复核"},
        {"gate_id": "materials_resolve",
         "defect": "石板无污渍、金属无锈，近景 1:1 仍显干净",
         "cause": "材质只有基础 PBR，没有旧化与遮罩层",
         "action": "加污渍与锈迹遮罩，裂纹改真几何刻痕，边缘加磨亮",
         "expected_effect": "近景 1:1 能读出污渍、锈与磨损",
         "verification": "100% 裁切并排对照石地与金属件，能读出污渍、锈迹与磨边"},
        {"gate_id": "dense_wavy_grass_canopy",
         "defect": "草池顶部未形成连续起伏体块，局部可见池沿",
         "cause": "草卡高度与池沿接近，缺少外倾草梢层",
         "action": "加一圈高度 1.15 倍、外倾 8–12 度的草卡压过池沿 6–10 cm",
         "expected_effect": "池沿被草遮住，形成连续波浪冠",
         "verification": "100% 裁切并排检查池沿是否被草遮住，50% 缩图确认草冠连成起伏体块"},
    ],
    "final_decision": ("v21 rework_required：背景已从椭圆水卡改为真实水平水面 + 挡土墙 + 可编辑对岸/空气层，"
                       "world 不再外露；但制作自评 73.12 < 85，植被与光色两维低于 3，草池与材质硬门槛未过，"
                       "背景面积超出 3pp 容差，未提交盲评。"),
}
out = os.path.join(BASE, "GATE_REPORT.json")
json.dump(report, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("GATE written", total, "portable", report["reproducibility"]["render_sha256"][:16])
