# 业务入口：pilot_simple_map

> 机制验证业务（pilot）。不是画风来源，不要并进 P1。

1. 先读 `BUSINESS_PROFILE.md`（目标/边界/已知限制）。
2. 需要出图时读 `STYLE_PROFILE.md`（做法与禁止外推）。
3. 检查集见 `HARNESS_SPEC.json`；机械部分用
   `python tools/pilot_simple_map_check.py --request <active/request_id> --candidate <dir>`。
4. 用例在 `test_cases.json`（6 条，容差写在 TEST-05）。
5. `scorecard.json` 只是可读性检查表，**没有**总分门槛。

## 当前样例

- `knowledge/active/20261102-pilot-simple-map/`（N0–N7 全记录）
- 候选：`art/static_map/pilot_simple_map/v01/`（scene.blend、final.png、MANIFEST、DELIVERY、REVIEW）
- 结论：`target_met`；`maturity: observed`（单张实证）

## 已知不适用

- 不适用于 P1 任务（互斥）；不用于推断美术上限或生产工期。
- 未接入 Hook，全部人工触发。
