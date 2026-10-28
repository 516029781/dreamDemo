# 地图参数知识与 Harness 校验规则

更新：2026-10-29。状态：当前规则设计。本文把 Arknights CW-8/CW-9 的公开结构化参数用作**数据解析黄金样例**，并规定项目自有地图 Harness 应如何吸收其字段分层和拓扑校验方法。它不改变项目视觉目标。

## 1. 两种依据各管一件事

| 用途 | 唯一依据 | 能决定什么 |
|---|---|---|
| 整图画面、秋日色彩、构图锚点、设施/树/草/地板表现和视觉评分 | `reference/_raw_screenshots/P1/t084s.jpg`，SHA256 `13706e7eab96726565156a9e6440727de5d5bac82ee9c09c293a5745dd7446de`；详细规则见 `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md` | P1 秋日画面如何呈现、相机下各区域是否达到目标 |
| 地图参数如何组织、解析器如何验证结构数据、Harness 如何输出可修复失败 | 本文及 `knowledge/ARKNIGHTS_MAP_DATA_AND_HARNESS_AUDIT_20261029.md` 的已固定源数据 | 数据 schema/索引/坐标完整性、项目地图字段之间的语义约束 |

**禁止混用**：CW-8/CW-9 的格子尺寸、tile 分布、敌方路线数和 `view` 数值不得进入秋日画面的色板、构图锚点、相机参数或成图验收阈值。CW 截图可帮助理解“如何把关卡参数映射成格子/区域可视化”的数据组织，不是 P1 的第二主参考。当前静态图没有角色行走玩法，不能把塔防敌方路线强制成当前成图的要求。

## 2. 可复核的 CW-8/CW-9 黄金 fixture

来源固定为 `yuanyan3060/ArknightsGameResource` commit `5e2a435c51580f7776d46a88cc19ee9d2033137a`。本地原始 JSON、SHA 和来源登记见被 `/reference/` 忽略的目录 `reference/_arknights_samples/ArknightsGameResource_5e2a435c51580f7776d46a88cc19ee9d2033137a/data/` 与其中的 `SOURCE_MANIFEST.md`。这些原始文件不随 Git 克隆；新环境找不到它们时，`source_fixture` 应报告 `not_run`，不得将文档中的统计表冒充实际解析器回归结果。

| Fixture | Level 文件 | SHA-256 | 网格 | `tiles` | 敌方 routes |
|---|---|---|---:|---:|---:|
| CW-8 | `level_act25side_08.json` | `e797f550152363626ee21014c1c86d0288b4a5a7ce5831f89208da213abc9df9` | 12×8 | 96 | 31 |
| CW-9 | `level_act25side_09.json` | `81ae0bd9049d52351196f01e97189c6374b95ffecfb17003d75b97bf78c26a9b` | 12×8 | 96 | 32 |

CW-8 的 `map.json` SHA-256 为 `6c6c1a2aac844f45c94bb7bd6474f857097a69d2021928d9741b0e899c124a01`。当前记录的两个 `view` 向量是 `[[0.0,-6.6,-10.63],[1.0958801286,-7.1,-11.4685064145]]`；只知其为两个三维向量/视角线索，轴、单位、向量语义和相机投影定义不明。Harness 只能校验 JSON 结构与 fixture 值，不能据此设置 Blender 相机。

这两个 fixture 的解析器校验规则：

| Rule ID | 必须检查 | Fixture 预期 / 失败处理 |
|---|---|---|
| `AKDATA-SOURCE-01` | 记录上游仓库、commit、文件相对路径和原始 SHA；解析后记录解析器版本/哈希 | SHA 不符时报告 `source_changed`，不得默默覆盖 golden 值；先审查上游变更 |
| `AKDATA-GRID-01` | `mapData.map` 是矩形整数矩阵；行数/列数与解析出的 height/width 一致 | CW-8/9 都是 8 行×12 列；任何非矩形或尺寸不符为 fail |
| `AKDATA-INDEX-01` | 每个格子整数都可索引 `mapData.tiles`，索引在 `[0, len(tiles)-1]` | 两个 fixture 均为 96 格、96 条 tile 记录、索引有效；越界/缺项 fail |
| `AKDATA-TILE-01` | 每条 tile 记录有 `tileKey`、`heightType`、`buildableType`、`passableMask` 等源字段；解析器保留原值和未知字段 | 不把枚举改名成 Blender 材质或自行推测物理高度；未知枚举需报告而非静默折叠 |
| `AKDATA-ROUTE-01` | 每条 route 的 `startPosition`、`endPosition` 和 checkpoint 位置均为整数 row/col，位于对应网格边界内 | CW-8 31 条、CW-9 32 条；这些是敌方路线，不代表玩家路线。路线连续性须尊重 `motionMode`、checkpoint 与机制语义，不得用简单相邻格规则误报 |
| `AKDATA-VIEW-01` | `map.json` 中 `view` 保持 2×3 数值向量结构；JSON 序列化/反序列化不丢精度或顺序 | fixture 比对以原始 JSON 数值为准；不把值转换成 Blender 世界坐标、焦距或 FOV |
| `AKDATA-GOLDEN-01` | 对解析后摘要做 golden 比较：网格尺寸、tileKey 分布、枚举分布、路线数、source hashes | CW-8/9 的已知分布见本文件下表；变更先标记 fixture drift，不能自动判为当前地图规则变化 |

已记录的 golden 分布（只供对应源文件的回归样例）：

| 字段/值 | CW-8 | CW-9 |
|---|---:|---:|
| `tile_forbidden` | 36 | 37 |
| `tile_ristar_road_forbidden` | 16 | 4 |
| `tile_wall` | 14 | 11 |
| `tile_road` | 8 | 28 |
| `tile_fence_bound` | 8 | 0 |
| `tile_start` | 4 | 4 |
| `tile_floor` | 4 | 8 |
| `tile_end` | 2 | 2 |
| `tile_ristar_road` | 2 | 0 |
| `tile_grvtybtn` | 2 | 2 |
| `heightType` 0 / 1 | 46 / 50 | 48 / 48 |
| `buildableType` 0 / 1 / 2 | 62 / 20 / 14 | 55 / 30 / 11 |
| `passableMask` 2 / 3 | 58 / 38 | 48 / 48 |

这些数量可用来证明解析器正确读取了两个**样本文件**，不能变成我方地图的必需 tile 数、空间比例、物件配额或配色比例。

## 3. Harness 应抽象复用的规则

Arknights 数据研究的价值是告诉我们：地图网格、地块属性、通行语义、路线和镜头元数据应分字段保存并分别校验。项目 Harness 应按下面三个 profile 分开运行：

### Profile A：`source_fixture`

仅在项目确实实现 Arknights 数据解析器且本地固定源文件可用时运行。应用第 2 节的固定 hash、结构、索引与 golden 分布；fixture 改动必须走人工审阅和显式更新记录。解析器尚未实现或输入文件不存在时记 `not_run`，不能记 `pass`。它不是静态地图候选的一项“美术通过”证据。

### Profile B：`project_static_scene`

用于当前 P1 秋日静态图的原创 Blender 场景。项目参数必须来自 P1 图像分析和我方场景源，不从 CW8/CW9 拷值。

| Rule ID | 当前候选的校验约束 | 失败报告必须指出 |
|---|---|---|
| `MAP-SCENE-01` | manifest 标注唯一 P1 参考路径与 SHA、候选 ID、Blender 版本、渲染相机、画幅、色彩管理和源/渲染 SHA | 哪个绑定字段缺失或 hash 不一致 |
| `MAP-SCENE-02` | Blender 场景可无界面重开并复现登记的最终图；关键源素材路径存在，外部素材有来源记录 | 具体缺失路径、命令、退出码及复现差异 |
| `MAP-SCENE-03` | 主要建筑/设施必须有明确地面或结构支撑；用对象足迹向下射线/接触面检查记录支撑对象与最大间隙。容差需在场景单位锁定时配置，不硬编码 CW 的高度值 | 对象名、预期支撑对象、实测间隙、可改的 Blender 对象/参数 |
| `MAP-SCENE-04` | 场景对象按我方语义分层标记（例如 `ground`, `terrain`, `structure`, `vegetation`, `prop`, `background`）；不能把材质类型、是否可走、支撑关系混为一个 enum | 缺失/未知标签、对象路径与建议字段 |
| `MAP-SCENE-05` | 当前静态图不强制 tile grid、寻路图或玩家 route；若候选声称支持行走，才验证 walkable 面连通、坡度/台阶限制、阻挡物与路线端点 | `not_applicable` 时写明“本候选仅静帧”；声明可行走但无数据时 fail |
| `MAP-SCENE-06` | 若项目用自定义网格，宽/高/单元尺寸由项目 manifest 声明；每个 cell 引用合法的我方地块类型，矩阵尺寸与数据条数一致，不能遗漏/重复坐标 | 失效坐标、重复 ID、孤立格、网格尺寸与数组长度差异 |

### Profile C：`visual_p1`

只用 P1 秋日主参考及其标准验收视觉。G0 应在候选目录生成 `reference_analysis/P1_REFERENCE_PROFILE.json`，记录锚点、ROI、遮挡区、测量方法、阈值依据和来源。当前标准中的锚点框是近似人工标注，不足以自动推导像素级容差；不得自行发明阈值。每个指标需注明坐标/单位、标注或计算方法、容差依据、遮挡处理和校准状态；没有可复核阈值的指标设 `evaluation_mode: manual_only`，自动结果记 `not_run`，继续由同机位看图评审。仓库现有旧 P1 视觉脚本仍读取互相不完全一致的 `style.json`、`regions.json`、`target_layout_v04.json`，当前不得用于 v06 自动评分或 PASS/FAIL；新 profile/实现先同图基线复核。CW-8/9 PNG 与 tile 统计不得作为视觉阈值。最终画风、自然度和场所感仍由可见证据评审，不自动给分。

## 4. 失败日志与 AI 自修闭环

每条 Harness 结果统一输出：

```json
{
  "rule_id": "MAP-SCENE-03",
  "profile": "project_static_scene",
  "status": "fail",
  "observed": {"object": "Facility_Main", "support": null, "max_gap": 0.42},
  "expected": {"support_required": true, "max_gap": "see candidate manifest"},
  "evidence": ["renders/final.png", "scene.blend"],
  "repair": "将 Facility_Main 底面贴合其目标平台，或给 DELIVERY.json 登记真实支撑对象后重新渲染复核。"
}
```

状态仅允许 `pass`、`fail`、`not_applicable`、`not_run`。每个 `fail` 必须给出定位字段、证据与可执行修法；`not_applicable` 必须说明当前范围理由，`not_run` 必须说明缺少实现、输入或执行证据；两者均不得计作 `pass`。AI 执行规则：先修所有 fail，再重跑受影响的 profile；输出新日志和哈希，不覆写旧候选证据。机械检查通过只说明对应参数成立，不等同视觉达标。

## 5. 当前实现状态与后续落地

### 已实现

- `tools/static_map_quality_gate.py`：只读校验 P1 静态图最终报告的路径、文件 SHA、固定参考身份、DELIVERY/profile 绑定、六维加权分数、盲评阈值、组合项、硬门槛、复现记录和返修队列。它读取模型写入的 `GATE_REPORT.json`，不启动 Blender、不分析图像像素、不生成评审，也不冻结候选。
- `.codex/hooks.json` 与 `.codex/hooks/static_map_quality_hook.py`：Codex 项目层的 `UserPromptSubmit`/`Stop` 适配器。只有鼠鼠项目层及 hook 定义都受信任、且当前会话明确启动 P1 静态地图任务时才会 armed；失败会把 gate 诊断交回同一会话继续。它不是全局 hook。
- 未配置 Git `pre-commit`；`tools/art_harness.py` 仍只用于完整游戏，静态图不得套用其 ENV/CHAR/UI/MIX 合同。

### 尚未实现或仅部分实现

| 流程组件 | 状态 | 当前边界 / 缺口 |
|---|---|---|
| `preflight` | 未实现 | 尚无单入口自动检查候选目录、Blender/素材、容量和冻结文件；执行者按当前工作单人工预检 |
| `post_render` | 未实现 | 尚无自动图片完整性、场景支持关系或 render run ID 检查；手动记录命令、退出码、尺寸、耗时和 SHA |
| `blind_visual_review` | 仅有报告格式与门禁校验 | 必须由两个真实分开的视觉审阅过程各自只看固定参考、同一最终图和标准；gate 只核对不同 reviewer_id、`blind` 声明、逐维证据、各自组合/硬门槛和评分，不证明审阅者身份、盲评真实独立性或模型确实看过图 |
| `final_quality_loop` | 部分实现 | Stop hook 失败后提示同一会话继续；实际诊断、改 Blender 源、重渲、复评仍由模型执行，当前没有自动 Blender 闭环调度器 |
| `freeze_candidate` | 未实现 | gate 通过不锁目录、不移动候选、不设只读；源/渲染/报告哈希绑定仅证明验收时文件一致 |
| Codex `Stop` hook | 已配置、待信任/运行验证 | 需在 Codex `/hooks` 信任项目 hook；本会话还需工作目录位于鼠鼠项目并由明确制作提示 armed。未满足时 hook 不运行；可手动调用 gate |
| 单入口 wrapper / Git pre-commit | 未实现 | 尚无 `tools/static_map.py` 完整串接 preflight、render、review、返修与 freeze；提交门不能代替未提交美术产物的质量控制 |

### 评分、返修和结束条件

- 唯一视觉目标和评分数值只读 `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md`：固定 P1 秋日参考、85 分、每维至少 3/4、组合项与硬门槛。Arknights CW-8/CW-9 只作为数据/Harness fixture，不得拿来补画或替换 P1 参数。
- 制作者自评仅用于决定返修方向，不作为放行票；若制作侧预检未过，gate 只要求继续修复，不提前强制盲评。制作侧预检通过后，两个盲评各自独立计算，**两份都须**总分 ≥85、每维 ≥3/4，且各自的四项组合检查和八项硬门槛通过。不能平均两份分数来掩盖一份失败。
- gate 不会检查评审器版本/提示词或真实会话来源，也不能阻止报告编造。因此目前能保证的是“结构化报告与机械条件满足”，不能承诺“视觉评分已独立验证”。需独立审阅器调用和来源证明落地后，才能把盲评认证为自动验证。
- 静态图正常结束只允许 `target_met`；低分或任何失败都继续返修。只有真实外部阻塞并留下替代尝试和证据时才可结束为未完成；不得把 `quality_below_target` 当成正常结案状态。

自动化只能强制来源、哈希、评分运算、结构化门槛和复现记录；自然度、材质美感和 P1 画风仍需看图。P1 profile 必须在新候选中建立，并明确标出参考截图中 UI/角色造成的不可观察遮挡 mask、锚点/区域、测量方法和可证依据；这些 mask 只用于排除被遮住的参考区域，不要求制作实际 UI 或角色。旧 `target_layout_v04.json`、`style.json`、`regions.json` 和相关脚本未认证，不得直接给当前 v06 报 PASS/FAIL。
