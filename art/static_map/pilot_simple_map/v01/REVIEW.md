# REVIEW：pilot_simple_map v01

- request_id：`20261102-pilot-simple-map`｜run_id：`20261102-0710`
- 目的：验证新流程（N0–N8 + 证据契约），不是美术交付

## N2 设计预览

5 版灰模迭代，全部记录在 `runs/20261102-0710/baselines/design_r01/`（最终版即该目录下 `blockout.png`）。

| 版本 | 改动 | 结果 |
|---|---|---|
| v1 | 初版 40 m 地面 + 两条远景方块 | 远景悬在地面外，读作深色平板 |
| v2 | 地面 120 m、机位拉近、曝光 0.30→0.18 | 平板仍在，主体变大 |
| v3 | 远景改 3 个扁球山丘 | 高机位下变成"悬浮暗块"，更差 |
| v4 | 山丘降为 2 道山脊 | 仍读作悬空椭圆 |
| v5 | **取消远景体块**，地面按相机距离雾化 | 背景自然退远，通过 |

结论：高机位俯视小场景，背景靠**距离雾化**比堆远景体块稳；这条已写进 `STYLE_PROFILE.md` §2。

## N5 终图

- 960×540，Cycles CPU 64 spp，AgX，exposure +0.10，耗时约 20 s
- 13 个网格对象（初版设计 15 个中含 2 个被取消的山丘）
- 原始 13 个对象全部 zmin ≥ 0，无悬空：地面/台/三级踏步/后墙 = 0，台面物件 = 0.9，叠箱 = 1.75，灯头 = 3.44（与灯柱 3.50 顶部重叠）

## N6 返修

无。N5 一次通过 TEST-01/02/03/04，未触发返修（返修预算 2 轮未使用）。

## N7 验证结果

| 用例 | 结果 | 证据 |
|---|---|---|
| TEST-01 尺寸 | **PASS** 960×540 RGB | `evidence/TEST-01/size.json` |
| TEST-02 体块与接地 | **PASS** 13 对象，zmin 全部 ≥0 或叠放 | `evidence/TEST-02/objects.json` |
| TEST-03 投影同向 | **PASS** 三处裁切均朝右下 | `evidence/TEST-03/shadow.md` + `shadow_crops.png` |
| TEST-04 材质与明度 | **PASS（视觉）** 四族可指认；数值 diagnostic：近黑 0.057%、近白 0%、luma 4.2–171.6 | `evidence/TEST-04/value_stats.json` |
| TEST-05 复现 | **PASS** RMS 0.0、max channel diff 0、pixel SHA 一致 | `runs/…/reproduction.json` |
| TEST-06 文档闭环 | **PASS** 6/6 REQ 覆盖、0 悬空证据、request_id 一致 | `evidence/TEST-06/linkage.json` |

## 关键发现（影响证据契约）

1. **PNG 元数据使文件 SHA 不可复现**：两次渲染像素完全一致，但 PNG 内含
   `File/Date/RenderTime/cycles.*`，导致 file SHA 不同（`9b184c15…` vs 另一值）。
   处理：复现契约以 **pixel_sha256** 为判定，file SHA 只作参考。工具 `tools/normalize_render.py`
   可去元数据让 file SHA 一致（实测两份归一化后同为 `7c1f3b31…`），但会丢 sRGB/gamma 色块，
   故不用于交付图。
2. **P1 机械 gate 无法复用到新业务**：参考 SHA、六维权重、8 条硬门槛全部写死为 P1。
   处理：本业务自建 `tools/pilot_simple_map_check.py`（尺寸/明度/文档闭环），并声明它不是 P1 gate。
3. **模板里的 command 字段是占位符**：`HARNESS_SPEC.template.json` 写 `<gate script>`，
   落到业务包时必须替换成真实命令，否则 harness 不可执行。本次已改为实际脚本路径。

## 状态

- 结束状态：`target_met`（本单目标是"验证流程可执行"，不是美术质量）
- 未验证项：`maturity: observed` 只覆盖单张图；复杂地形/植被/夜景未测
- 回退：本单未改动 P1 任何文件；删除 `art/static_map/pilot_simple_map/` 即可完全清除
