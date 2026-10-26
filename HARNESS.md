# 美术 harness：当前实现、命令与限制（P06 更新）

> 本文件的“当前审查事实”固定于 2026-10-25 的旧阶段，不能覆盖后续 n2 独立报告及 n4 预审。当前返修候选、90 分制作侧筛选和执行入口以 `planning/execution/CURRENT_INSTRUCTION_INDEX.md`、`planning/execution/ACTIVE_REWORK_CYCLE.json`、`PRODUCER_SELF_REVIEW.md` 为准；本文件第 1–5/7 节仅供核对工具能力与语义，实际运行仍须检查代码和证据。

更新：2026-10-25｜账本以 PROJECT_TASKS.json 为准。当前生效合同仍是 `art_review/harness_contract.json` **1.3.0**，rubric **1.2.0**；`art_review/vnext/*` 是 1.4.0-draft，**尚未生效**，不能据此宣称 Q01-Q09 或证书链已是生产门禁。

## 1. 现在实际实现了什么

| 能力 | 入口 | 说明 |
|---|---|---|
| 源/phase 门禁、manifest 冻结、独立 review、控制器 attestation/证书链 | `tools/art_harness.py` | 1.3.0 原功能保留；P03 增加前序证书重核与消费版本绑定 |
| 统一 CLI | `run-art-harness.ps1` | 自动发现 Python（`ART_HARNESS_PYTHON` 可覆盖）；新式参数与旧式透传都可用 |
| Q01-Q09 质量证据 | `art_review/vnext/quality_checks.json`、`tools/art_gate/check_quality.py` | 缺证据 pending，硬失败 fail，统计阈值只报 warning |
| 采集绑定/失效闭包 | `art_review/vnext/capture_binding.schema.json`、`tools/art_gate/check_bindings.py` | 绑定 source/export/build/camera/canvas/output hash；按内容 hash 计算 dirty 闭包 |
| 构建日志门 | `tools/art_gate/build_log_gate.py` | 失败事件或非零退出码优先于 Finished；已知噪声只记 warning |
| 真实 canvas 采集 | `tools/capture/canvas_capture.js` | 对 canvas 元素截图并记录 CSS rect/backing/DPR/viewport；禁止整页截图 |
| 定向 Blender 构建 | `tools/blender/run_courtyard_build.ps1` | `-Stage` 选阶段、首个失败即停、每阶段计时与日志 hash；默认仍全量 |

## 2. 退出码契约（必须一致）

| 码 | 含义 |
|---|---|
| 0 | harness `accepted=true`（仅控制器批准的确切输入）；quality/binding/build-gate 的 `pass` |
| 2 | 阻断/非法输入：GateError、缺密钥、坏签名、schema/证据不符 |
| 3 | 有效运行但未接受：draft、needs review、failed checks |

`audit` 永不返回 accepted=true；它只返回 `failed_checks`、`pending_checks` 与可执行 `next_actions`。PowerShell 包装会打印 `EXIT_CODE` 并原样传播。

## 3. 证据链

`source → export → build → capture → independent review → controller certificate`

- 采集必须绑定构建 ID、日志 hash、source/export hash、相机、viewport、canvas CSS rect/backing 与输出 hash（`capture_binding.schema.json`）。
- 改变相机/构建/共享材质/字体后，旧截图不能证明新结果；用 `check_bindings.py impact` 得到 dirty 闭包。
- 整页截图（`page_screenshot=true`）不是 canvas 证据；F05 受影响图必须用新入口重采。
- `Finished` 不是构建成功；失败事件、退出码、产物 hash 与真实加载共同判定（F08）。

## 4. 常用命令

```powershell
# 汇总：目标阶段最新独立 review、失败项、可执行下一步
.\run-art-harness.ps1 -Command audit -Stage art_complete -Out delivery\next_cycle\T0\audit.json

# 草稿（不等于批准）
.\run-art-harness.ps1 -Command prepare -Stage scene_demo -Artifacts <spec.json> -Out art_review\submissions\current\manifest.json

# 质量证据与采集绑定
python -X utf8 tools\art_gate\check_quality.py --results <behavior_results.json> --binding <binding.json>
python -X utf8 tools\art_gate\check_bindings.py verify --binding <binding.json>
python -X utf8 tools\art_gate\check_bindings.py impact --bindings <dir-or-list> --changed a.blend,b.png --fail-on-dirty

# 构建日志门（真实构建后）
python -X utf8 tools\art_gate\build_log_gate.py --log <build.log> --profile cocos --exit-code <code>

# 定向构建（示例；默认全量）
powershell -NoProfile -File tools\blender\run_courtyard_build.ps1 -Stage env_tree,map001
```

## 5. 评测语义

- 四卡各 ≥85、核心 ≥3、任维 ≥2；3 档全满足只得 75，不代表达标。不得为凑分无证据升 4。
- 技术自检不产生视觉 pass；缺行为/遮挡/暂停/空满重置证据保持 pending 或 fail。
- Q06 的 draw calls/triangles 预警线只产生 warning，不单独阻塞；缺最终 GLB hash 或统计不来自最终构建才是硬失败。
- 不强制单一贴图方案：procedural/node material、SVG、Krita 图层等原生可编辑路线均可，只要证据匹配。
- 视觉/行为真实性最终仍由独立审核实际看图/复现交互；程序不能证明审美。

## 6. 当前审查事实（2026-10-25）

- 独立审核 `art_review/reports/independent_20261024/` 结论：art_complete **blocked**，H02/H07 fail，H03 not_checked；四卡 37.5/75/61.25/38.75。
- `audit --stage art_complete` 实测：status=blocked，19 项 failed_checks（含 H02/H07、四卡低于门槛、开放 major 缺陷），3 项 pending（H03、R09/R10）。
- 当前无 active submission；旧 art_complete manifest 仍为 draft_not_accepted。F02：394 条中 18 条曾漂移，17/17 已从 git f8c72d7 恢复到 `reference/frozen_history/`，旧 manifest 未改写；恢复包只是历史参考。
- Q01-Q09 与 capture binding 尚未接入生产放行（vNext 未生效）；不影响如实报告 pending。

## 7. 不能做到的事

- 不能独立判断审美、遮挡是否“好看”或 UI 是否符合 P1；这些需要独立审核实际看图。
- 不能防住拥有完全写权限并伪造日志/坐标/截图的模型；可信门禁与密钥应在制作环境外。
- 制作模型不能自签独立 review、controller attestation 或 stage certificate；V07后可制作A-*候选，V09留最终签认。
- 不接管其他 IDE 进程，不做后台自动调度；工作流见 EXECUTION_PROTOCOL.md。
