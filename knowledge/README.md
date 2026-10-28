# 鼠鼠项目知识库

更新：2026-10-29。当前静态地图唯一整图视觉目标是秋日参考 `reference/_raw_screenshots/P1/t084s.jpg`。Arknights CW-8/CW-9 仅作为结构化地图参数与 Harness 规则研究样本，不作为画面风格或色板目标。当前只制作静态环境图；完整游戏阶段暂停。

## 当前只读这几份

| 需要 | 权威文件 |
|---|---|
| 了解任务范围和制作步骤 | planning/art/STATIC_MAP_WORKFLOW_20261028.md |
| 查看 P1 秋日画面目标、锚点和评分 | planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md |
| 查地图参数如何转成 Harness 校验规则 | MAP_PARAMETER_HARNESS_RULES_20261029.md |
| 查 Arknights 数据来源、固定样本、解包资源边界 | ARKNIGHTS_MAP_DATA_AND_HARNESS_AUDIT_20261029.md |
| 按精简流程制作 | RECIPES.md |
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
- 地图 JSON、地图 PNG、AssetBundle 解包工具、实际生产素材是不同证据类型；来源与用途边界见 `ARKNIGHTS_MAP_DATA_AND_HARNESS_AUDIT_20261029.md`。
- `reference/_arknights_samples/` 有 6 张当前研究图、CW-8/CW-9 结构化 JSON 和 8 张已退出范围的夏日探索图。它们只作只读样本；CW 参数用于解析器 golden fixture 和 Harness 设计，不是产品地图参数或视觉评审依据。夏日图仍在本地忽略目录，已标为 out-of-scope，不参与分析。
- 旧完整游戏配方与诊断已退出当前知识入口，见同名文件中的停用说明。
