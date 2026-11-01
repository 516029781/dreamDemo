# 地图美术方法模块（common/methods/map_art）

按 `deliverable_type = 静态地图 / 可行走地图` 加载；不适用于 UI、角色、道具任务。

## 模块与权威正文

| 模块 | 用途 | 权威正文 |
|---|---|---|
| 可复用静态地图制作流程 | 灰模、小样先行、根因诊断、候选隔离、复现 | `knowledge/REUSABLE_MAP_ART_PIPELINE.md`（原地保留；物理迁移见待办） |
| 地图参数 → Harness 规则 | 结构化地图数据如何转成校验规则 | `knowledge/MAP_PARAMETER_HARNESS_RULES_20261029.md` |

## 使用边界

- 复用**流程与诊断方法**，不复用任何业务包的参考图、相机、色板、锚点与评分。
- 本模块不定义视觉风格；风格由选中业务包的 `STYLE_PROFILE` 决定。
- 方法成熟度按 `observed/proposed` 标记；未复测的方法不得写成通用最佳实践。

## 待办

- `REUSABLE_MAP_ART_PIPELINE.md` 的物理路径迁移（→ 本目录）延后至全部引用更新后执行；
  迁移前本目录只做索引，避免出现两份正文。
