# Codex 项目级 P1 静态地图质量闭环

更新：2026-11-01，v3。作用范围只限本仓库中的 Codex 会话，不配置用户级或全局 hook。

> v3 用户决策：**不要求其他模型独立终审；整图完全无植被。** 旧 schema、独立终审和稀疏植被规则均不适用于新候选。

## 1. 运行边界

- Hook 定义在 `.codex/hooks.json`，处理程序为 `.codex/hooks/static_map_quality_hook.py`，机械验收脚本为 `tools/static_map_quality_gate.py`。
- Hook 核对项目根、事件 `cwd`、`.git` 与 `AGENTS.md`。只在用户明确启动/继续 P1 静态地图制作、且当前会话已 armed 时工作；方案讨论、普通审核和其他项目不受阻。
- 会话状态在 `.codex/state/static_map_runs/<session_id>.json`，该目录 ignored，不提交、不与其他会话共享。用户明确暂停/取消时清除当前会话状态；正常达标或完整真实外部阻塞后归档并解除 hook。
- Hook 未受信任或未 armed 时，执行者按 `AGENTS.md` 手动运行 gate。无需修改用户级 Codex 设置。

## 2. 允许结束的质量条件

正常 `target_met` 必须同时满足：

1. 固定参考是 `reference/_raw_screenshots/P1/t084s.jpg`，SHA256 为 `13706e7eab96726565156a9e6440727de5d5bac82ee9c09c293a5745dd7446de`。
2. `scene.blend`、`renders/final.png`、`REVIEW.md`、`DELIVERY.json`、参考 profile 全部在候选内，真实 SHA 与 gate 一致；DELIVERY/profile 再绑定同一参考、源、图。
3. **无独立审核要求。** 制作者须亲自查看绑定的最终图，提交六维自评，总分 `≥85/100` 且每维 `≥3/4`；每维要有至少 20 字符的可见证据。再由同一制作模型做一次逐维反证自检：列出最可能推翻/降低当前评分的可见反例、处理理由及最终分，并绑定同一 render SHA。评分权重为 20/20/20/15/15/10，维度名见 P1 美术标准。
4. 组合检查 `floor`、`structures`、`lighting`、`background` 和八项硬门槛均为 `pass`，每项含至少 20 字符图像证据。必须包含 `no_vegetation`：整图不得出现树、叶、草、花、灌木、苔藓、藤蔓、盆栽、裸土/花池或植物图案/贴图。REVIEW 还须记录 Outliner、隐藏集合、实例/Geometry Nodes、材质和图片纹理的资产清点，以及最终图全画面目视结果；仅靠关键词搜索不能结案。P1 原图植物仅为参考事实，不进入当前评分目标。
5. 隔离复制后重开 Blender 成功，复现渲染退出码为 0，复现 SHA 与绑定最终图一致。
6. 若失败，`repair_queue` 对每项写明缺陷、原因、修复动作、预期效果和验证方法。`rework_required` 会阻止当前制作任务结束并提示同一制作模型继续修改源、重渲、重评。

只有确实无法由当前制作模型解决的外部依赖，且报告记录至少两种替代尝试、候选内带 SHA 的证据和恢复条件，才可 `blocked_external` 结束；等待独立审稿、普通低分或实现困难不属于外部阻塞。门槛不设返修次数上限。

## 3. 文件布局和报告契约

```text
art/static_map/p1_autumn_courtyard/vNN/
├─ scene.blend
├─ renders/final.png
├─ REVIEW.md
├─ DELIVERY.json
├─ GATE_REPORT.json
└─ reference_analysis/P1_REFERENCE_PROFILE.json
```

报告路径采用仓库根相对路径，分隔符为 `/`。以下仅为字段形状示意，不可直接当作通过报告：

```json
{
  "schema": "p1-static-map-quality-gate/v3",
  "candidate_id": "vNN",
  "status": "target_met",
  "bindings": {
    "reference": {"path": "reference/_raw_screenshots/P1/t084s.jpg", "sha256": "..."},
    "scene": {"path": "art/static_map/p1_autumn_courtyard/vNN/scene.blend", "sha256": "..."},
    "render": {"path": "art/static_map/p1_autumn_courtyard/vNN/renders/final.png", "sha256": "..."},
    "review": {"path": "art/static_map/p1_autumn_courtyard/vNN/REVIEW.md", "sha256": "..."},
    "delivery": {"path": "art/static_map/p1_autumn_courtyard/vNN/DELIVERY.json", "sha256": "..."},
    "profile": {"path": "art/static_map/p1_autumn_courtyard/vNN/reference_analysis/P1_REFERENCE_PROFILE.json", "sha256": "..."}
  },
  "producer_review": {
    "producer_id": "codex-p1-producer",
    "reference_sha256": "13706e7eab96726565156a9e6440727de5d5bac82ee9c09c293a5745dd7446de",
    "render_sha256": "same-as-bindings.render.sha256",
    "dimensions": {
      "composition_and_space": {"score": 3.5, "evidence": "固定镜头下六个空间锚点与高差的可见对照……"},
      "object_structure": {"score": 3.5, "evidence": "维护柜和圆筒设备均接地且有检修面……"},
      "surface_materials": {"score": 3, "evidence": "石材与金属明度、粗糙度可区分……"},
      "scene_layering_and_object_organization": {"score": 3.5, "evidence": "全图无植被，设备替代体块有明确主次……"},
      "lighting_depth": {"score": 3.5, "evidence": "暖地面、暗设备和冷软远景保持分层……"},
      "style_cohesion": {"score": 3.5, "evidence": "近中远细节密度一致且无突兀风格……"}
    },
    "total_score": 85.0
  },
  "producer_countercheck": {
    "producer_id": "codex-p1-producer",
    "render_sha256": "same-as-bindings.render.sha256",
    "checks": {
      "composition_and_space": {"challenge": "寻找主锚点偏位/空间关系不成立的可见反例……", "decision": "score_retained", "score_before": 3.5, "reason": "检查后发现台阶与设备的层级成立，未找到足以降分的反例……", "score_after": 3.5},
      "object_structure": {"challenge": "寻找设备悬空、接口缺失或用途不明的反例……", "decision": "score_retained", "score_before": 3.5, "reason": "检查底座与检修面后保留当前分数……", "score_after": 3.5},
      "surface_materials": {"challenge": "寻找石材与金属区分不清或表面过平的反例……", "decision": "score_retained", "score_before": 3, "reason": "对照近景材质后保留当前分数……", "score_after": 3},
      "scene_layering_and_object_organization": {"challenge": "寻找植物残留、设备随机填空或前中远拥挤的反例……", "decision": "score_retained", "score_before": 3.5, "reason": "全图和缩图检查后保留当前分数……", "score_after": 3.5},
      "lighting_depth": {"challenge": "寻找接触影缺失、远景过硬或明暗无层次的反例……", "decision": "score_retained", "score_before": 3.5, "reason": "检查全图明暗分层后保留当前分数……", "score_after": 3.5},
      "style_cohesion": {"challenge": "寻找物件细节密度或材质风格互相冲突的反例……", "decision": "score_retained", "score_before": 3.5, "reason": "全图检查后保留当前分数……", "score_after": 3.5}
    }
  },
  "combo_checks": {},
  "hard_gates": {},
  "reproducibility": {"scene_reopened": true, "exit_code": 0, "render_sha256": "..."},
  "repair_queue": []
}
```

允许状态为 `target_met`、`rework_required`、`blocked_external`。维度 key 与权重固定为：`composition_and_space:20`、`object_structure:20`、`surface_materials:20`、`scene_layering_and_object_organization:15`、`lighting_depth:15`、`style_cohesion:10`。gate 重算总分，不信任手填值。`producer_countercheck.checks` 必须包含全部六维；每项 `challenge`、`reason` 至少 20 字符，`decision` 为 `score_retained` 或 `deduction_applied`；保分时前后分一致，扣分时后分必须更低，且 `score_after` 等于该维最终自评分。目标状态还要求 `repair_queue` 是空列表。`producer_id` 必须与 `producer_review.producer_id` 一致，render SHA 必须与当前图一致。gate 仍无法验证这些文字是否诚实或视觉判断是否正确。

组合检查 key：`floor`、`structures`、`lighting`、`background`。硬门槛 key：`foreground_steps_railings`、`right_cylindrical_equipment`、`cohesive_non_checkerboard_ground`、`left_area_functional_replacement`、`no_vegetation`、`functional_midground_structure`、`cool_soft_background`、`materials_resolve`。每项格式为 `{ "status": "pass", "evidence": "..." }`。

`DELIVERY.json` 的 `bindings` 必须含 `reference_sha256`、`scene_sha256`、`final_render_sha256`、`reference_profile_sha256`；profile 本身也须含固定 `reference_sha256`。schema v2 及更早报告只供历史追溯，不可用于新候选。

## 4. Gate 能力边界

脚本能核真实路径和 SHA、参考身份、分数算术/阈值、清单字段、复现声明及修复队列；它**不看图片、不启动 Blender、不检测场景对象，也不证明自评真实**。因此制作模型必须真的查看 SHA 绑定的图，并用具体可见区域写证据；机械 gate 通过只表示证据结构和数字通过，不表示脚本自动判断画质。

Codex `decision: block` 会向同一已 armed 会话提示失败项和修复队列，不会自动编辑 Blender 文件。制作模型需继续执行“看图找根因 → 修改原生源 → 同机位渲染 → 更新 SHA/自评 → 再跑 gate”。它不会阻止用户手动停止或外部强行中断。

手动核验命令：

```powershell
python tools/static_map_quality_gate.py --candidate art/static_map/p1_autumn_courtyard/vNN
```

当前流程权威来源是 `AGENTS.md`、`planning/art/STATIC_MAP_WORKFLOW_20261028.md` 和 `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md`；本文件只定义项目 Hook 接线和机器契约。
