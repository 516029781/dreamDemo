# 鼠鼠项目当前进度总结

更新：2026-10-25。范围：`art_required`，当前返修周期为 candidate_n2 独立审核退回后的 N01/N02/N03/MIX + N09。  
性质：制作侧进度记录，不是独立审核结论，也不是发布批准。

## 1. 一句话状态

candidate_n2 已退回；**candidate_n3 已完成一轮完整返修、构建和 Q01–Q09 验证，但制作侧自审只有 ENV 75 / CHAR 93.75 / UI 75 / MIX 75，未达到 90，未提交独立审核**。  
用户已同意开始 candidate_n4 的风格级重构；目前 n4 只完成了工作区和主树拓扑的新版，尚未完成完整构建、Q 检查和自审。

## 2. 候选与冻结状态

| 候选 | 状态 | 说明 |
|---|---|---|
| candidate_n2 | 已独立退回，保持冻结 | 原 n2 manifest、源、构建、证据未覆盖 |
| candidate_n3 | 制作侧返修候选，未提交 | manifest 机械检查 pass；自审未过 90；无最终审阅包 |
| candidate_n4 | 制作中 | 从 n3 派生；已重写主树，其余尚未完成 |

账本：`PROJECT_TASKS.json` revision **1.0.137**。  
返修指针：`planning/execution/ACTIVE_REWORK_CYCLE.json`，状态 `open`，`next_candidate=candidate_n4`。  
candidate_n2 的旧报告和证据仍在原目录，不被 n3/n4 覆盖。

## 3. candidate_n3 已完成内容

### 3.1 行为缺陷 N09

已把“恢复”和“重新开始”分开：

- `setPause(false)` 只恢复输入，保留玩家坐标、任务、相机目标、留言板状态；
- `resetView()` 只用于显式重新开始/重置；
- 竖屏返回横屏也走保留状态路径，不再调用 `resetView()`。

实测：

| 测试 | 移动后位置 | 暂停期间位移 | 恢复位移 | 新输入后位移 |
|---|---:|---:|---:|---:|
| 键盘 | 1.05 m | 0 m | 0 m | 1.05 m |
| 触控 | 1.80 m | 0 m | 0 m | 1.80 m |

竖屏返回：玩家位移 **0 m**，相机位移 **0 m**，`player_preserved=true`。  
证据：`delivery/next_cycle/n3/T5/q04_behavior_moved.json`。

### 3.2 Q01–Q09

finalN3 构建上全部通过：

- Q01：真实可见/隐藏 `PlayerWorldQuad` 差分 bbox **130×130 px**；
- Q02：P1 t015/t044/t084 对照；
- Q03：树前/树后遮挡成立（前 5116 → 后 1572 个近白角色像素）；
- Q04：键盘/触控、移动后暂停/恢复、对白锁、竖屏返回；
- Q05：留言板 empty 0 / full 3 / reset 0；
- Q06：final GLB 已绑定，runtime stats 768 draws / 520,946 tris（warning）；
- Q07：n3 长椅副本局部改 X 1.20、保存/重开/导出/同预览机位；
- Q08：源→导出→构建→采集→合同绑定；
- Q09：1280×720 与 720×1280 真实 canvas，竖屏 `rotate_notice` + 输入锁。

结果文件：

- `delivery/next_cycle/n3/T5/behavior_results_n3.json`
- `delivery/next_cycle/n3/T5/quality_check_n3.json`（pass；Q06/Q09 warnings）
- `delivery/next_cycle/n3/T3/finalN3` 三张正式图

### 3.3 视觉返修

- N01：中心花坛改为连续石鼓 + 浅接缝，去掉锯齿轮廓；长椅增加扶手、横撑、螺栓、更细分板；主树更细枝叶卡、平滑树冠核心；绿篱 4 排；前景增加长椅/叶堆。
- N02：1024 石材/木纹、512 金属/树皮/土壤纹理；运行时 normal+pbr map；树影/接触影/反弹补光。
- N03：对白高度压到 176px（24.4%），半透明外缘 + 内层纸 + 纸胶带/纤维/叶枝/手绘角；任务卡双层纸；用内层纸和图层隔离压掉可见的 UI 双渲染残影（根因仍未完全定位）。
- MIX：保留角色锁定源；增加脚底/长椅/花坛接触影，调整 UI 与场景的暖色关系。

对照图：

- `delivery/next_cycle/n3/T2/reference_comparison.png`
- `delivery/next_cycle/n3/T4/N01_geometry_before_after.png`
- `delivery/next_cycle/n3/T4/N01_geometry_closeups.png`
- `delivery/next_cycle/n3/T4/N02_material_closeups.png`
- `delivery/next_cycle/n3/T4/N02_shadow_before_after.png`
- `delivery/next_cycle/n3/T4/N03_ui_before_after.png`
- `delivery/next_cycle/n3/T4/N04_actor_bbox.png`
- `delivery/next_cycle/n3/T4/N05_orientation.png`
- `delivery/next_cycle/n3/T6/character_n/N07_animation_sheet.png`

## 4. candidate_n3 自审与门槛

| 卡片 | 制作侧自审 | 门槛 | 结论 |
|---|---:|---:|---|
| ENV | 75.00 | ≥90 | 未达 |
| CHAR | 93.75 | ≥90 | 达 |
| UI | 75.00 | ≥90 | 未达 |
| MIX | 75.00 | ≥90 | 未达 |

`producer_review.py check`：`producer_rework_required`，仅剩 3 条分数阈值 finding；Q/绑定、47 项逐项检查、已知问题清单均通过机械校验。

关键文件：

- `art_review/submissions/candidate_n3/manifest.json`
- `delivery/next_cycle/n3/T4/producer_self_review_n3.json`
- `delivery/next_cycle/n3/T4/producer_submission_check_n3.json`
- `delivery/next_cycle/n3/T5/quality_check_n3.json`

**结论：没有把 75 写成 90，没有提交 independent review，也没有自签。**

## 5. candidate_n4 当前进展

已创建独立工作区：

- `art/candidates/candidate_n4/source/`
- `art/candidates/candidate_n4/ui/`
- `demo_n4/`
- `tools/blender_n4/`
- `tools/ui_n4/`
- `tools/textures_n4/`
- `delivery/next_cycle/n4/`

主树已从“球形叶簇团块”改成**枝梢挂叶**路线：

- 主枝/侧枝更细分叉，枝条可见；
- 叶簇改为枝梢短枝上的小型叶枝（每枝 3 个小簇，叶片更小）；
- 删除了中央大块实体树冠 blob；
- 当前 n4 树是“无实体 core、44 个内部填充叶枝”的版本；
- 原有的“继续增加叶密度”补丁在用户中断时未应用。

当前预览：

- `art/candidates/candidate_n4/previews/environment/ENV006_autumn_tree.png`

尚未完成：

- n4 绿篱/背景/前景重排；
- n4 光照/材质/角色融合；
- n4 UI 纸片重做；
- n4 完整 map 构建、Cocos 构建、Q01–Q09、自审和 manifest；
- n4 审阅包或最终审核请求。

## 6. 已知限制与风险

- 无手机/微信真机测试；Q09 只声明桌面浏览器适配。
- 无完整任务玩法、微信开发者工具、性能/包体验收。
- Q06 n3：MAP001/LOOK001 **768 draws / 520,946 tris**，高于 400 预警线；仅 warning。
- n3 视觉仍低于 90：树冠/前景密度、光照层次、UI 纸片不规则度、角色与低模场景融合仍是主要差距。
- 独立审核、控制器证书、正式放行均未完成；所有候选 `accepted=false`。
- 角色仍为锁定 1015_aglna2 Spine；未重画、未缩放、未用 AI 图。

## 7. 下一步建议

1. 在 candidate_n4 先完成**树/绿篱/前景**的同一镜头低成本预览，确认不再是“团块树”。
2. 再做 n4 光照、材质、角色 tint/接触影，压掉灰褐和“角色贴纸感”。
3. 再做 n4 UI 纸片撕裂边/内层纸/涂鸦密度；保留 n3 的 24.4% 对白布局和 N09 行为。
4. 只有 n4 自审四卡均 ≥90、核心 ≥3、Q/绑定通过且无未解严重问题时，才生成完整 manifest/包并请求独立审核。
5. 不覆盖 n2/n3 冻结内容；不把制作自审写成独立批准。

## 8. 关键命令记录

```text
candidate_n3:
  Blender env_tree 19–52s per run
  Blender map001 ~69s
  Cocos web-desktop build ~19–21s
  Q01–Q09 / N04 / N05 / N07 / Q04-moved: pass
  producer_review check -> producer_rework_required (75 / 93.75 / 75 / 75)

candidate_n4:
  workspace created
  ENV006 sprig-tree build: success, latest preview written
  no full n4 map/Cocos/Q run yet
```

## 9. 边界声明

本文是制作侧进度总结。candidate_n2 的独立报告、P08/V08/V09/I08/I09 审核、控制器证书与正式放行均未由制作模型签署；任何新候选在独立审核前都不能称为 accepted/released。
