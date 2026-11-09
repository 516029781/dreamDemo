# 开发可行性确认（N4）

- request_id：`20261102-pilot-simple-map`
- 依据：`REQUIREMENTS_BRIEF.md`（sha `871a33a2…`）、`SOLUTION_DESIGN.md`（sha `161a9a52…`）
- 确认时间：2026-11-02T07:0x+08:00

## 1. 结论

**status：`confirmed`**

依据：用户 2026-11-02 06:58「你做一个简单的图 验证一下流程吧」= 明确授权制作本图。
不是"我替用户批准"，是把用户原话记为授权来源；若用户随后改口，本状态应改为
`changes_required` 并回到 N2。

## 2. 可行性逐项

| 项 | 判断 | 依据 |
|---|---|---|
| 引擎可用 | 可用 | Blender 5.2.3 无头，路径已验证（本项目多轮使用） |
| 几何量 | 15 网格对象，无贴图 | `build_scene.py` 输出 `PILOT_OBJECTS 15` |
| 渲染预算 | 预览 16 spp/480×270 约 3 s；终图 64 spp/960×540 预估 < 90 s | 实测预览耗时 |
| 磁盘 | scene.blend 预计 < 2 MB | 无外部贴图、无高模 |
| 依赖 | 无第三方资产、无跨版本链接 | 全部程序化几何+节点材质 |
| 已知风险 | 重渲非逐位一致 | 已在 OPEN_QUESTIONS Q-02 声明容差 |

## 3. 前置条件（进入 N5 前必须成立）

- [x] Brief 已 frozen
- [x] 设计文档含机位/物件坐标/材质/渲染参数
- [x] 灰模预览已出（`runs/20261102-0710/baselines/design_r01/DESIGN_PREVIEW_PACK/blockout.png`）
- [x] 用例覆盖 6/6 REQ（`knowledge/business/pilot_simple_map/test_cases.json`）
- [x] 容差事前声明（RMS ≤ 2/255）

## 4. 明确不做

不追加角色、不做多机位、不做手绘贴图、不接入 Hook（本次只验证人工路由与手动 gate）。
