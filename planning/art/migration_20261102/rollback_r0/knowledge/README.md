# 鼠鼠项目知识库

更新：2026-11-01。当前项目 P1 静态地图的唯一整图目标仍是秋日参考 `reference/_raw_screenshots/P1/t084s.jpg`。Arknights CW-8/CW-9 仅作为结构化地图参数与 Harness 规则研究样本，不作为画面风格或色板目标。完整游戏阶段暂停。制作其他地图时，通用制作流程见 `REUSABLE_MAP_ART_PIPELINE.md`；新图必须另建地图 brief、视觉参考与评分标准，不能借用 P1 的美术参数。**当前 P1 目标明确为完全无植被**，以大型功能设备/箱体组织画面、细节克制。其他地图默认避免密集叶草；是否完全无植被由该地图 brief 和最新用户指令决定。

## 当前只读这几份

| 需要 | 权威文件 |
|---|---|
| 了解任务范围和制作步骤 | planning/art/STATIC_MAP_WORKFLOW_20261028.md |
| 查看 P1 秋日画面目标、锚点和评分 | planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md |
| 查地图参数如何转成 Harness 校验规则 | MAP_PARAMETER_HARNESS_RULES_20261029.md |
| 查 Arknights 数据来源、固定样本、解包资源边界 | ARKNIGHTS_MAP_DATA_AND_HARNESS_AUDIT_20261029.md |
| 按精简流程制作 | RECIPES.md |
| 将静态地图制作流程迁移到其他地图 | REUSABLE_MAP_ART_PIPELINE.md |
| 查看项目必读入口、新产品知识分层/路由与 Harness 接入（提案，尚未启用） | planning/art/ART_STYLE_SYSTEM_AND_NEW_PRODUCT_ONBOARDING_PLAN_20261102.md |
| 理解当前 P1 Art Harness 的边界与落地路线 | planning/art/P1_ART_HARNESS_ARCHITECTURE_20261102.md |
| 查已确认的通用规则 | STANDARDS.md |
| 查本项目知识库维护状态 | PROJECT_AUDIT.md |
| 记录跨轮经验 | planning/execution/LESSONS.md |

本地两个项目美术 skill 是制作辅助，不代替画面标准。旧工具调研已退出当前入口；若后续需要选工具，先核验当前官网/仓库与本机可用性，再更新独立工具说明。

历史文档与过期指令的处理以 `planning/art/ART_DOCUMENTATION_ARCHIVE_INDEX_20261029.md` 为准；已被覆盖的方案只作追溯，不作为当前制作入口。

## 使用规则

- 先读当前工作单和 P1 秋日美术标准；Arknights 参数只用于 Harness 的结构/解析规则，不能拼入视觉目标。
- 不在知识库重复完整评分表、候选日志、失败截图或旧游戏任务。原始证据只放在对应工作产物目录。
- 本库只存稳定、可复用的制作规则。流程尚未复现或美术尚未达标的观察标为 proposed，不写成成功案例。
- P1 秋日主参考已锁定；当前没有经现行标准确认达标的静态地图成功案例。CASEBOOK 暂不收录地图案例。
- `REUSABLE_MAP_ART_PIPELINE.md` 沉淀候选身份、空间灰模、小样先行、根因定位、分档渲染和证据闭环等跨地图方法；其中的观察级经验不能当作已经跨地图复现的保证。
- `ART_STYLE_SYSTEM_AND_NEW_PRODUCT_ONBOARDING_PLAN_20261102.md` 是新产品接入方案提案，尚未成为现行制作标准；用户确认前不能把候选项目级不变量当作已批准的全局 Style Bible。
- 当前 P1 执行目标为零植被，旧“稀疏植被”与独立终审核验规则已废止；详情以 P1 工作流和美术标准为准。P1 的 85 分衡量无植被改编质量，不把移除植物本身作为扣分或伪称植物特征复刻。
- P1 V25–V27 候选日志记录了一些返工教训，但 V27 当前工作图没有绑定有效评分；可复用流程经验，不能将其植被、色调或整图效果宣传成成功模板。
- 地图 JSON、地图 PNG、AssetBundle 解包工具、实际生产素材是不同证据类型；来源与用途边界见 `ARKNIGHTS_MAP_DATA_AND_HARNESS_AUDIT_20261029.md`。
- `reference/_arknights_samples/` 有 6 张当前研究图、CW-8/CW-9 结构化 JSON 和 8 张已退出范围的夏日探索图。它们只作只读样本；CW 参数用于解析器 golden fixture 和 Harness 设计，不是产品地图参数或视觉评审依据。夏日图仍在本地忽略目录，已标为 out-of-scope，不参与分析。
- 旧完整游戏配方与诊断已退出当前知识入口，见同名文件中的停用说明。
