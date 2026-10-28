# Codex 项目级 P1 静态地图质量闭环

更新：2026-10-29。作用范围只限本仓库中的 Codex 会话，不配置用户级或全局 hook。

## 1. 运行边界

- Hook 定义在 `.codex/hooks.json`，处理程序是 `.codex/hooks/static_map_quality_hook.py`；评分与证据核验器是 `tools/static_map_quality_gate.py`。
- 处理程序用脚本所在仓库根与事件 `cwd` 做路径包含校验，并确认根目录含 `.git` 和 `AGENTS.md`；中文 Windows 路径不经 Git 子进程编码转换。
- `UserPromptSubmit` 只在用户明确要求开始/继续制作、返修或重渲 P1 静态地图时，为该 Codex `session_id` 建立本地状态。可直接说“继续优化 P1 静态地图达到目标”，或在执行提示中加 `!p1-static-map-run`。纯讨论、方案、审核问题不启动。
- 会话状态写入 `.codex/state/static_map_runs/<session_id>.json`，该目录在 `.gitignore` 中，不提交、不共享给其他会话。未启动该任务的同项目会话在 Stop 时直接放行；其他项目从不加载本项目配置。
- 用户明确说暂停/取消制作时，只清除本会话状态。完成或外部阻塞后归档到同一 ignored state 目录并解除本会话 hook。
- 项目 hook 是非托管 hook。Codex 首次要求审阅/信任时，应在 Codex 的 `/hooks` 页面核对本文件和脚本后信任；这一步只信任此项目定义，不需要修改 `C:\Users\tt\.codex`。

## 2. 目标与返回规则

正常放行必须同时满足：

1. 固定参考 `reference/_raw_screenshots/P1/t084s.jpg` 的 SHA256 为 `13706e7eab96726565156a9e6440727de5d5bac82ee9c09c293a5745dd7446de`。
2. Blender 源、最终渲染、REVIEW、DELIVERY、P1 profile 全部存在，路径在当前候选目录内且 SHA 与 `GATE_REPORT.json` 一致；`DELIVERY.json` 和 profile 再次绑定相同源/图/参考。
3. 两份盲评分别按 P1 标准权重 20/20/20/15/15/10 计算，且各自达到总分 ≥85、每维 ≥3/4；总分由 gate 重算，不信任手填总分。制作者自评须有证据并绑定同一参考/最终图，但只用于返修导航，不作为通过票。
4. 两份盲评各自记录 floor/tree/grass/lighting 四项组合检查及八项 P1 硬门槛；每份评审均须全为 `pass` 并附可读证据，报告汇总项也必须通过。
5. Blender 场景重新打开成功，复现渲染的 SHA 与最终图一致。

返修阶段按制作侧预检分流：当报告状态为 `rework_required`，且制作自评低于 85、任一维低于 3、或汇总组合/硬门槛尚未通过时，gate 反馈这些制作侧修复项，暂不要求两份盲评。制作侧预检达到目标后，即使仍有盲评/复现/哈希问题，gate 才要求补齐最终评审并继续阻止结束。最终状态 `target_met` 始终必须含两份完整盲评；制作者自评分数本身不作为放行票。

任何报告缺失、字段错误、源图或参考 hash 不一致、分数不足、组合项失败、硬门槛失败、复现失败，Stop hook 都返回 `decision: block`，让同一 Codex 会话继续；提示中包含失败项和报告里的修复队列。没有固定次数上限。达标后自动解除本会话状态。只有结构完整的 `blocked_external`（具体外部依赖、至少两种替代尝试、候选目录内的带 SHA 证据和恢复条件）可允许任务以“未完成”结束；不会被写成 `target_met`。

## 3. 当前候选与文件结构

启动时从未被占用的最高版本号之后预留新目录（当前预计 `v06`，若已存在则递增），不覆盖旧版：

```
art/static_map/p1_autumn_courtyard/vNN/
├─ scene.blend
├─ renders/final.png
├─ REVIEW.md
├─ DELIVERY.json
├─ GATE_REPORT.json
└─ reference_analysis/P1_REFERENCE_PROFILE.json
```

报告里所有路径使用相对仓库根的 `/` 分隔符。`GATE_REPORT.json` 的字段示意（下面故意省略部分维度、盲评、门槛项目，**不能直接作为通过报告**）：

```json
{
  "schema": "p1-static-map-quality-gate/v1",
  "candidate_id": "v06",
  "status": "target_met",
  "bindings": {
    "reference": {"path": "reference/_raw_screenshots/P1/t084s.jpg", "sha256": "..."},
    "scene": {"path": "art/static_map/p1_autumn_courtyard/v06/scene.blend", "sha256": "..."},
    "render": {"path": "art/static_map/p1_autumn_courtyard/v06/renders/final.png", "sha256": "..."},
    "review": {"path": "art/static_map/p1_autumn_courtyard/v06/REVIEW.md", "sha256": "..."},
    "delivery": {"path": "art/static_map/p1_autumn_courtyard/v06/DELIVERY.json", "sha256": "..."},
    "profile": {"path": "art/static_map/p1_autumn_courtyard/v06/reference_analysis/P1_REFERENCE_PROFILE.json", "sha256": "..."}
  },
  "producer_review": {
    "reviewer_id": "producer",
    "reference_sha256": "13706e7eab96726565156a9e6440727de5d5bac82ee9c09c293a5745dd7446de",
    "render_sha256": "与 bindings.render.sha256 相同",
    "dimensions": {"composition_and_space": {"score": 3.5, "evidence": "基于固定机位全图和锚点对照的具体观察……"}},
    "total_score": 88.0
  },
  "blind_reviews": [],
  "combo_checks": {},
  "hard_gates": {},
  "reproducibility": {"scene_reopened": true, "exit_code": 0, "render_sha256": "..."},
  "repair_queue": []
}
```

`status` 仅允许 `target_met`、`rework_required` 或 `blocked_external`。`producer_review.dimensions` 与两个盲评都必须包含六个维度对象，每个有 `score: 0..4`、至少 20 字符的可见证据；每份评审有重算一致的 `total_score`。制作者评审也必须包含当前 `reference_sha256` 和 `render_sha256`，但其低分不触发最终放行失败；在 `rework_required` 且制作侧预检未过时，gate 不要求盲评。制作侧预检通过后，两个盲评必须有不同 reviewer_id、`blind: true`、当前 reference/render SHA，不能把制作者 ID 作为审阅人；每份盲评内部还必须含完整 `combo_checks` 和 `hard_gates`。低分/门槛失败时，`repair_queue` 必须逐项说明 defect、cause、action、expected_effect、verification，否则仍不放行。四项组合检查 key 为 `floor/tree/grass/lighting`；硬门槛 key 为 `foreground_steps_railings`、`right_grass_cylinder`、`cohesive_non_checkerboard_ground`、`tree_branching_negative_space`、`dense_wavy_grass_canopy`、`functional_midground_structure`、`cool_soft_background`、`materials_resolve`；每项为 `{ "status": "pass", "evidence": "..." }`。

`DELIVERY.json` 须包含：

```json
{
  "candidate_id": "v06",
  "bindings": {
    "reference_sha256": "...",
    "scene_sha256": "...",
    "final_render_sha256": "...",
    "reference_profile_sha256": "..."
  }
}
```

P1 profile 须含同一 `reference_sha256`。`blocked_external` 可不具备最终源/图/评分，但必须绑定固定参考，并在 `external_blocker` 中写清具体外部依赖、至少两种替代尝试（各有 action/result）、候选目录内带 SHA 的失败证据和恢复条件；通过此例外只表示任务被记录为外部阻塞，绝不表示质量达标。

## 4. 可信度边界

脚本能客观核验文件路径、真实 SHA、固定参考身份、分数算术、阈值、状态字段、评审自报的组合/硬门槛和返修证据是否齐全。它不能从 JSON 证明审阅者真的独立，也不能替代视觉判断；模型必须看绑定的图像并按 `P1_T084_ART_DIRECTION_STANDARD_20261028.md` 给出逐项可见证据。不要把“机械门禁通过”表述成独立的人类艺术验收。双盲声明仍依赖执行者诚实。

Codex Stop hook 的 `decision: block` 会自动生成继续提示；它不会拒绝用户、停止按钮或外部强制中断。项目级 hook 仅在此 `.codex` 层受信任时生效。若 Codex 未加载/未信任 hook，可手动执行：

```
python tools/static_map_quality_gate.py --candidate art/static_map/p1_autumn_courtyard/v06
```

继续规范以 `AGENTS.md`、`STATIC_MAP_WORKFLOW_20261028.md` 和 `P1_T084_ART_DIRECTION_STANDARD_20261028.md` 为准；本文件只定义 Codex 接线与 gate 的机器契约。
