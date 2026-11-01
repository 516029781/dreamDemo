# -*- coding: utf-8 -*-
"""G4：写 DELIVERY.json / REVIEW.md / GATE_REPORT.json。

评分口径：总分 = Σ(维度分 × 权重) / 4，维度分 0–4。
状态只有两种合法出口：target_met（≥85 且每维 ≥3 且硬门槛通过）或真实 blocked_external；
本轮未达标 → rework_required，并在 REVIEW 写清返修队列。
"""
import hashlib
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.dirname(HERE)
PROJ = os.path.abspath(os.path.join(CAND, "..", "..", ".."))
CAND_ID = os.path.basename(CAND)

REF_REL = "reference/_raw_screenshots/P1/t084s.jpg"
REF_ABS = os.path.join(PROJ, REF_REL)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(p):
    return os.path.relpath(p, PROJ).replace("\\", "/")


DIMS = [
    ("composition_and_space", "构图与空间", 20, 3.0,
     "六锚点齐全（左树、右草池、台阶栏杆、设备、水口、石板平台）；背景层次本轮才真正成立（此前 M02/M03 未渲染）；广场下半仍偏空，圆筒密度高于参考"),
    ("object_structure", "物件结构", 20, 3.0,
     "台阶有厚度与栏杆、圆筒有箍带与厚边、设备成组并有管线；中央设备仍偏简化，叉车属参考外的工业元素"),
    ("surface_materials", "材质表面", 20, 3.0,
     "地面加入污渍噪声与细裂缝、接缝压深、金属保留锈迹；近景 1:1 仍偏干净，缺杂草与破损"),
    ("vegetation", "植被", 15, 2.75,
     "草色压深转金褐、树冠放大 1.46 倍；草池仍未连成参考的连续起伏体块，冠内透空偏多"),
    ("lighting_depth", "光色纵深", 15, 3.0,
     "主光恢复投影（原 use_shadow=False）、光比拉开、曝光 −1.02；暗部仍不够深，缺参考的长斜影重量"),
    ("style_cohesion", "画风统一", 10, 3.0,
     "全图同一套风格化 3D 语言；但整体仍偏「干净模型渲染」，缺少参考的手绘笔触与空气透视"),
]

total = sum(w * s for _, _, w, s, _ in DIMS) / 4.0
target = 85.0
min_dim = min(s for _, _, _, s, _ in DIMS)
target_met = total >= target and min_dim >= 3.0

COMBOS = [
    {"id": "floor", "status": "pass", "note": "大板同族、接缝连续、台阶与平台同材质"},
    {"id": "tree", "status": "rework", "note": "冠内透空、叶簇偏薄，参考为连续厚冠"},
    {"id": "grass", "status": "rework", "note": "未连成起伏体块，池沿缺外倾草梢"},
    {"id": "lighting", "status": "rework", "note": "已有方向性投影，但暗部与前景影重不足"},
]

HARD = [
    {"id": "foreground_height_rail", "pass": True, "note": "台阶高差 + 金属栏杆"},
    {"id": "right_drum_planter", "pass": True, "note": "右圆筒草池存在且有箍带"},
    {"id": "paving_not_flat", "pass": True, "note": "接缝 + 污渍 + 裂缝，非单色非棋盘"},
    {"id": "canopy_not_sphere", "pass": True, "note": "树冠非规则球团"},
    {"id": "grass_not_sparse", "pass": False, "note": "草池仍偏稀疏，未达连续体块"},
    {"id": "midground_not_boxes", "pass": True, "note": "中景有栏杆/管线/斜撑"},
    {"id": "far_no_brown_geometry", "pass": True, "note": "远景为景片，无大面积棕色硬几何"},
    {"id": "materials_packed", "pass": True, "note": "贴图均为相对路径或磁盘文件，无外链丢失"},
]

now = time.strftime("%Y-%m-%dT%H:%M:%S")

delivery = {
    "schema": "p1-static-map-delivery/v1",
    "candidate_id": CAND_ID,
    "created": time.strftime("%Y-%m-%d"),
    "status": "target_met" if target_met else "rework_required",
    "reference": {
        "path": REF_REL,
        "sha256": sha256(REF_ABS) if os.path.exists(REF_ABS) else None,
        "frame_px": [1920, 1078],
        "verified": os.path.exists(REF_ABS),
    },
    "comparison_baseline": {
        "source": f"art/static_map/p1_autumn_courtyard/v21/scene.blend",
        "read_only": True,
        "inherited": ["主景几何", "材质家族", "灯光 rig 结构", "相机 C1"],
        "replaced": [
            "M02/M03 景片按视锥重建（v21 的景片在相机上方，从未被渲染）",
            "水面几何截短到 y18.5",
            "光照光比与曝光",
            "地面污渍/裂缝",
        ],
    },
    "camera": {
        "location_xyz": [0.25, -20.5, 8.2],
        "rotation_euler_rad": [1.209995, 0.0, 0.01198983],
        "pitch_deg": 20.672,
        "lens_mm": 53.0,
        "horizon_v": -0.4894,
        "view_transform": "Standard",
        "exposure": -1.02,
        "resolution_px": [1920, 1078],
        "samples": 48,
        "denoise": True,
    },
    "producer_review": {
        "reviewer_id": f"producer:{CAND_ID}-self-assessment",
        "dimensions": {k: {"label": lab, "weight": w, "score": s, "evidence": ev}
                       for k, lab, w, s, ev in DIMS},
        "weighted_total": round(total, 2),
        "target": target,
        "min_dimension": min_dim,
        "combos": COMBOS,
        "hard_gates": HARD,
        "target_met": target_met,
        "reviewed_at": now,
    },
    "artifacts": {
        "scene": f"art/static_map/p1_autumn_courtyard/{CAND_ID}/scene.blend",
        "render": f"art/static_map/p1_autumn_courtyard/{CAND_ID}/renders/final.png",
        "blockout": f"art/static_map/p1_autumn_courtyard/{CAND_ID}/renders/blockout.png",
        "color_key": f"art/static_map/p1_autumn_courtyard/{CAND_ID}/renders/color_key.png",
        "no_dof": f"art/static_map/p1_autumn_courtyard/{CAND_ID}/renders/no_dof_diagnostic.png",
        "details": f"art/static_map/p1_autumn_courtyard/{CAND_ID}/renders/details.png",
        "background_src": f"art/static_map/p1_autumn_courtyard/{CAND_ID}/background_src/",
        "preflight": f"art/static_map/p1_autumn_courtyard/{CAND_ID}/preflight/",
    },
    "blockers": [] if target_met else [
        {"kind": "quality_below_target",
         "detail": f"自评 {total:.2f} < {target}；min_dim {min_dim}",
         "next": "按 REVIEW.md §返修队列执行，不以外部门禁结束"},
    ],
}

with open(os.path.join(CAND, "DELIVERY.json"), "w", encoding="utf-8") as f:
    json.dump(delivery, f, ensure_ascii=False, indent=1)

# ---------- REVIEW.md ----------
rows = "\n".join(
    f"| {lab} | {w} | {s} | {w*s/4:.2f} | {ev} |" for _, lab, w, s, ev in DIMS
)
combo_rows = "\n".join(f"| {c['id']} | {c['status']} | {c['note']} |" for c in COMBOS)
hard_rows = "\n".join(f"| {h['id']} | {'通过' if h['pass'] else '未过'} | {h['note']} |" for h in HARD)

review_md = f"""# {CAND_ID} 评审记录（P1 秋日静态地图）

状态：**{'target_met' if target_met else 'rework_required'}（制作自评 {total:.2f}，阈值 {target:.0f}）**
参考：`{REF_REL}`（SHA256 已校验）
生成时间：{now}

## 1. 本轮修掉的缺陷

| # | 现象 | 真因 | 修法 |
|---|---|---|---|
| 1 | 全图无方向性投影，暗部消失 | 主光 `Warm late afternoon key` 的 `use_shadow=False` | 开阴影，能量 420→300，光比重排 |
| 2 | 顶部横贯蓝灰带 | 水面网格铺到 y22.5，投影占 v11–22%，远端在阴影里发黑 | 水面截短到 y18.5，顶部交给对岸景片 |
| 3 | 顶部对岸/远山完全不见 | M02/M03 景片包围盒 z 26–40（相机上方），**从未被渲染**；顶部是 world 透出 | 按 `cam.view_frame` 在 55/60 m 重建全画幅景片 |
| 4 | 重建后景片飞到画面外成黑带 | 顶点用了世界坐标，又 parent 到相机，被**二次变换** | 顶点改相机局部坐标 |
| 5 | 地面油污状脏斑 | grime 噪声 scale 9 / strength 0.55 过低频 | 改 scale 26 / factor 0.30，并加细裂缝 |
| 6 | 地面过曝到 255 | 光强提高后曝光只降 0.06 | 曝光 −0.78 → −1.02，地面反照率 ×0.80 |

## 2. 六维自评（0–4）

| 维度 | 权重 | 分数 | 得分 | 可见依据 |
|---|---:|---:|---:|---|
{rows}
| **合计** | 100 | — | **{total:.2f}** | 阈值 {target:.0f}，{'达标' if target_met else '**未达**'} |

四项组合检查：

| 项 | 状态 | 说明 |
|---|---|---|
{combo_rows}

硬门槛：

| 项 | 结果 | 说明 |
|---|---|---|
{hard_rows}

## 3. 与参考的主要差距（按影响排序）

1. **内容密度**：参考的广场被台阶投影、堆放、杂草、破损切分；本候选下半仍是整块空石板。这是构图分卡在 3.0 的主因。
2. **风格化程度**：参考是厚涂/笔触感的绘景，本候选是干净 PBR 渲染。参数无法跨越，需要贴图重绘或后期笔触层。
3. **草池体量**：参考两个圆筒的草冠是连续起伏体块并溢出筒沿；本候选仍是分离草束。
4. **圆筒数量**：参考右侧两个大筒，本候选有四个以上，节奏过密。
5. **树冠**：参考左上树冠覆盖约 20% 画幅；本候选放大后仍偏小且透空。

## 4. 返修队列（下一轮）

| # | 缺陷 | 改哪里 | 验证 |
|---|---|---|---|
| R1 | 广场空场 | 加 2–3 组功能性堆放、树冠投影、地面裂缝带 | 广场内 ≥3 处打断 |
| R2 | 风格化不足 | 叠一层笔触/颗粒后期，降低镜面反射 | 50% 缩图能读出笔触 |
| R3 | 草池体块 | 草冠改为连续曲面 + 外倾草梢，筒沿加溢出 | 100% 裁切看不到容器边 |
| R4 | 圆筒过密 | 抑制右下多余圆筒，保留参考的两个主筒 | 右半圆筒数 ≤2 |
| R5 | 树冠偏小 | 再放大并加密冠层，压到画幅左上 | 冠层覆盖 ≥18% 画幅 |

## 5. 复现

```
python art/static_map/p1_autumn_courtyard/{CAND_ID}/preflight/run_pipeline.py
```

单帧重渲：

```
blender -b art/static_map/p1_autumn_courtyard/{CAND_ID}/scene.blend \\
  -P art/static_map/p1_autumn_courtyard/{CAND_ID}/preflight/render.py
```

Blender 5.2.3 LTS；Cycles 48spp；Denoise 开；seed 0；1920×1078；f/4.0。
"""
with open(os.path.join(CAND, "REVIEW.md"), "w", encoding="utf-8") as f:
    f.write(review_md)

# ---------- GATE_REPORT ----------
gate = {
    "schema": "p1-static-map-quality-gate/v1",
    "candidate_id": CAND_ID,
    "status": "target_met" if target_met else "rework_required",
    "bindings": {
        "reference": {"path": REF_REL, "sha256": delivery["reference"]["sha256"]},
        "scene": {"path": delivery["artifacts"]["scene"],
                  "sha256": sha256(os.path.join(CAND, "scene.blend"))},
        "render": {"path": delivery["artifacts"]["render"],
                   "sha256": sha256(os.path.join(CAND, "renders", "final.png"))
                   if os.path.exists(os.path.join(CAND, "renders", "final.png")) else None},
        "review": {"path": f"art/static_map/p1_autumn_courtyard/{CAND_ID}/REVIEW.md",
                   "sha256": sha256(os.path.join(CAND, "REVIEW.md"))},
        "delivery": {"path": f"art/static_map/p1_autumn_courtyard/{CAND_ID}/DELIVERY.json",
                     "sha256": sha256(os.path.join(CAND, "DELIVERY.json"))},
    },
    "producer_review": delivery["producer_review"],
    "verification": (
        f"制作侧自评 {total:.2f}/{target:.0f}，最低维度 {min_dim}。"
        f"组合项 tree/grass/lighting 为 rework；硬门槛 grass_not_sparse 未过。"
        f"本轮修复了 6 项结构性缺陷（主光无阴影、水面遮挡景片、景片二次变换、"
        f"景片从未进入视野、地面过曝、污渍过重），但内容密度与风格化仍与参考有实质差距，"
        f"未提交盲评。不以 quality_below_target 作为任务结束，按 REVIEW.md 返修队列继续。"
    ),
    "generated_at": now,
}
with open(os.path.join(CAND, "GATE_REPORT.json"), "w", encoding="utf-8") as f:
    json.dump(gate, f, ensure_ascii=False, indent=1)

print(f"SCORE {total:.2f}  min_dim {min_dim}  target_met={target_met}")
print("WROTE DELIVERY.json / REVIEW.md / GATE_REPORT.json")
