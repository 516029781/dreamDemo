# 《明日方舟》地图数据、解包资源与项目 Harness 核查

审计日期：2026-10-29。范围：共享项目目录 `C:\软件\鼠鼠`、本地《明日方舟》研究文件、公开 GitHub 仓库，以及当前静态地图工作流。本文记录可复核证据和推论边界，不把社区数据仓库称作官方资源授权。

> **方向校正（2026-10-29）**：用户确认唯一整图视觉目标仍为 P1 秋日图 `reference/_raw_screenshots/P1/t084s.jpg`。本文中的 Arknights 图片与 CW-8/CW-9 JSON 均是只读的结构化数据/Harness 研究材料，不是项目画风、色板、主参考或地图尺寸目标。可执行规则见 `knowledge/MAP_PARAMETER_HARNESS_RULES_20261029.md`；秋日画面标准见 `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md`。若下文历史段落与此说明冲突，以这两份当前文件为准。

## 结论摘要

1. **项目中此前没有查到本篇地图模型、贴图或场景包。** 在 2026-10-29 这次补充前，`reference/_arknights_samples/` 为空；扫描项目中的 PNG/JPG/WEBP/TGA/PSD/BLEND/FBX/OBJ/GLB/AB/AssetBundle/Spine 等文件，没有找到当天更新的地图美术文件。此后按用户要求从公开仓库固定提交抽取 6 张只读研究图（620,667 字节），并提取 CW-8/9 两关结构化数据；这些图不参与 P1 画面比较。另有 8 张夏日方向探索图是在用户转向航天基地风格前下载的，目前已标记为 out-of-scope，但仍留在 Git 忽略目录且不参与评审。没有生产地图模型或场景包。这个盘点只覆盖共享项目目录，无法证明其他模型的独立机器或私有会话里没有下载。
2. GitHub 上确实有**可查看的战术关卡数据和已渲染地图图像**，也有可解析游戏 AssetBundle 的**解包工具**；但这些不是同一类东西。
3. 我核查到的公开项目没有证明存在一个可直接导入 Blender、带完整场景层级、网格摆位、材质和纹理依赖、并有明确再发布授权的《明日方舟》本篇整关场景包。不要把“有地图 PNG/关卡 JSON/解包器”写成“有完整可复用 3D 地图”。
4. Arknights 数据与 P1 视觉目标必须分层：CW-8/CW-9 的 JSON 用于数据解析和 Harness 规则研究；P1 秋日 t084 仍是唯一整图视觉参考。v05 旧评审/绑定证据保持原样；任何新返修按 P1 标准另记新候选，不覆盖冻结材料。
5. 当前完整游戏 Harness 与本次静态地图 Harness 必须分开。静态图用 P1 秋日标准的 85 分与六维门槛；旧 `art_review` 的 47 项、角色/UI 卡、Q01–Q09 和制作提交 90 分过滤器不适用于本任务。

## GitHub 资料分层

| 来源 | 实际内容 | 对本项目可用之处 | 不能据此得出的结论 |
|---|---|---|---|
| [Kengxxiao/ArknightsGameData](https://github.com/Kengxxiao/ArknightsGameData) | 社区维护的游戏数据仓库，README 说明其部分数据由 OpenArknightsFBS 项目解析；`levels/` 下的关卡 JSON 属于战术/玩法结构数据 | 研究格网、tile 类型、部署区、出入口、路线和关卡参数；用于拓扑参考 | 不含由该 JSON 自动证明的场景模型、贴图、灯光或官方建模流程 |
| [yuanyan3060/ArknightsGameResource](https://github.com/yuanyan3060/ArknightsGameResource) | 固定提交 `5e2a435c51580f7776d46a88cc19ee9d2033137a` 的树中有 3233 个 `map/*.png`，共 361,495,845 字节；`levels.json` 为 74,169,893 字节，`map.json` 为 552,170 字节。当前样本为 320×180 的已渲染关卡画面 | JSON 可作为地图网格、地块属性、路线/坐标字段的解析器样例；PNG 仅保留来源信息和只读研究用途。本项目当前不以这些图做视觉对照 | PNG 不是可编辑场景、独立贴图或 3D 模型。README 明确静态资源版权属于《明日方舟》/鹰角；仓库 `LICENSE` 的 AGPL-3.0 针对仓库代码，不因此授权游戏图像进入产品、包体或 Git |
| [Awedtan/stage-viewer](https://github.com/Awedtan/stage-viewer) 与 [winny727/ArknightsMapViewer](https://github.com/winny727/ArknightsMapViewer) | 读取/模拟《明日方舟》关卡的地图查看器；前者说明其根据原始游戏数据复现并模拟关卡，后者自称地图文件查看工具并链接关卡数据仓库 | 看关卡结构如何解读、格子如何可视化、入口/路线如何表达 | 不是环境美术源文件，也不是一键导出完整 3D 场景的证明 |
| [isHarryh/Ark-Unpacker](https://github.com/isHarryh/Ark-Unpacker) | AB 资源解包器；当前仓库 README 列出 Texture2D→PNG、Mesh→OBJ、音频、TextAsset、Spine 等导出类型，需要已有游戏资源文件；本次 GitHub 发布页显示 v5.2.0 | 作为资产格式研究/本地受控检查工具的候选；如果以后研究客户端环境资产，应先做一个小样本验证网格、材质、贴图和摆位是否能重建 | 解包器 BSD-3-Clause 许可不等于游戏导出资源拥有相同许可；导出 Mesh 也不等于自动还原整关场景。其资源查找指南明示基于 Android v2.4.01 且已过时，不能当作当前目录保证 |
| [isHarryh/Ark-Studio](https://github.com/isHarryh/Ark-Studio) | 本地缓存的 README 指向旧 v0 分支并标明已弃用；较新项目状态须重新核对 | 只作为历史工具调研线索 | 不能把旧 v0 的功能清单当作当前可用能力 |
| [arkntools/asset-studio-web](https://github.com/arkntools/asset-studio-web) / [arkntools/unity-js](https://github.com/arkntools/unity-js) | 通用 Unity AssetBundle 浏览器/解析库；仓库使用 AGPL-3.0 | 可用于候选工具调研，适合查看 AssetBundle 对象 | 不是明日方舟地图内容仓库；项目代码许可证不授予游戏资源再发布权 |

### 地图资料具体长什么样

- `ArknightsGameResource` 根目录公开 `map/`、`levels.json`、`map.json`。固定提交 `5e2a435c51580f7776d46a88cc19ee9d2033137a` 的完整 Git tree 显示 `map/` 有 3233 个 PNG，合计 361,495,845 字节（约 344.8 MiB）；`levels.json` 为 74,169,893 字节（约 70.7 MiB），`map.json` 为 552,170 字节（约 539 KiB）。本地留存 6 张 320×180 PNG、620,667 字节，作为数据来源核查和结构化数据研究的索引样本，不作为任何画面的视觉比较集；另有 8 张已退出范围的夏日候选留在被 Git 忽略的本地参考目录。它们是已渲染的关卡画面，能看到格块地面、设施/掩体、战术入口/出口标记、阴影和环境层级；不是原始贴图集、网格模型或可编辑 Blender 工程。画面中的红/蓝战术标记属于玩法覆盖层，也不构成当前项目的美术标准。
- 样本图像所属主题不同，不能混作一套项目风格标准。用户已确认 P1 秋日图仍是唯一视觉目标；CW-8/CW-9 的图像不参与当前画面评分。其 JSON 可支撑结构字段如何组织、网格索引如何解析、路线坐标如何检查的 Harness 研究。

### CW-8 / CW-9 结构化地图参数实查

固定提交中的 `gamedata/levels/activities/act25side/level_act25side_08.json`、`level_act25side_09.json` 和 `map.json` 已保存于本地样本目录 `data/`，对应 SHA 与 URL 见 `SOURCE_MANIFEST.md`。关卡编号映射由 [`map.json`](https://github.com/yuanyan3060/ArknightsGameResource/blob/5e2a435c51580f7776d46a88cc19ee9d2033137a/map.json) 的 `activities/act25side/level_act25side_08|09` 项、仓库的 [`levels_split_gen.py`](https://github.com/yuanyan3060/ArknightsGameResource/blob/5e2a435c51580f7776d46a88cc19ee9d2033137a/levels_split_gen.py) 以及 [CW-8](https://prts.wiki/w/CW-8)/[CW-9](https://prts.wiki/w/CW-9) 关卡资料交叉确认。配套 [ArknightsResource README](https://github.com/fexli/ArknightsResource/blob/main/README.md) 将 `map_camera_views` 描述为地图相机定位数据，并声明仓库内游戏文件版权属于鹰角。

| 项 | CW-8 | CW-9 | 解释范围 |
|---|---:|---:|---|
| 格子 | 12 列 × 8 行（96 格） | 12 列 × 8 行（96 格） | 战术 tile 网格，不是以米为单位的现实尺寸 |
| enemy routes | 31 | 32 | 敌方路线；不是玩家自由行走路线 |
| `heightType` 原始值 | 0:46，1:50 | 0:48，1:48 | 游戏地块枚举；本报告保留原值，不换算成米 |
| `buildableType` 原始值 | 0:62，1:20，2:14 | 0:55，1:30，2:11 | 部署规则枚举，不等于地面材质或建筑类型 |
| `passableMask` 原始值 | 2:58，3:38 | 2:48，3:48 | 游戏通行规则枚举，不是角色碰撞网格的完整替代品 |
| `map.json` view | `[[0.0,-6.6,-10.63],[1.0958801286,-7.1,-11.4685064145]]` | 同左 | 两个三维向量；来源脚本称其为 `view`，配套资源仓库称 `map_camera_views`。坐标轴、单位、向量各自含义尚未由该文件说明，不能直接当 Blender 相机位置/焦距参数 |

`tileKey` 分布：

| `tileKey` | CW-8 | CW-9 |
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

下面是把 `mapData.map` 与 `mapData.tiles[index].tileKey` 连接后得到的**原始矩阵行序**；字母仅为本次研究简写，不代表游戏画面贴图颜色，也不应直接当作 Delta Force 路线：

```text
CW-8   . forbidden  S start  E end  R road  W wall  F floor
       B fence     Q ristar_road  q ristar_road_forbidden  G gravity button
............
.RRRRWWWWB..
.qBqqqqqqqB.
EQGBWSFFSWW.
EQGBWSFFSWW.
.qBqqqqqqqB.
.RRRRWWWWB..
............

CW-9
............
SFFRRRGRRRRE
....WRqWWRR.
SFFFFqqRERR.
.R..WqWWWWR.
SRRRRRGRRRR.
SFFRRRRWWW..
............
```

**Harness 可抽象的结构规律**：地图网格与 tile 属性分字段；tile 属性索引可解析；通行/高度/建造规则需与视觉材质分离；路线端点坐标要在地图边界内；视角向量要保留来源且语义未知时不得换算。这里抽取的是数据校验设计模式，不是项目建筑、色彩、照明或材质规范。Delta 的空间布局由 Delta 参考决定；秋日画面由 P1 决定。

**这里仍没有**：建筑/管线/家具的网格、物件世界坐标与旋转/缩放、现实米制尺度、材质球参数、纹理分配、光源布置或完整镜头焦距。`level` 文件中的 `mapId`、`environmentSe`、`cameraPlugin` 在这两关均为空；`map.json` 的 `view` 数值是可用的视角线索，但在没有对应渲染器/坐标定义前，不能称为已复现的 3D 相机。
- 样本来源 URL、仓库路径、固定提交、大小、SHA256、用途与权利边界见本地只读清单 `reference/_arknights_samples/ArknightsGameResource_5e2a435c51580f7776d46a88cc19ee9d2033137a/SOURCE_MANIFEST.md`。该目录受 `.gitignore` 的 `/reference/` 规则排除；样本不进入产品、构建或 Git。仓库根目录 `LICENSE` 是 AGPL-3.0，但 README 明确游戏静态资源版权属于《明日方舟》/上海鹰角；代码许可不能解释成图像授权。
- `ArknightsGameData` 的地图 JSON 和 Stage Viewer 能支持我们理解**战术地图拓扑数据的表达与校验**。P1 秋日图独立决定镜头、环境造型、材质、色彩和空间层级。战术数据可作数据 schema/解析器研究，不能替代视觉参考。
- Ark-Unpacker 声明支持导出 Mesh 与 Texture2D，但完整场景还需要验证哪些关卡对象、Transform、材质、Shader、贴图引用和灯光信息能被正确保留。工具能解析对象不等于场景可还原。

## 本地今天的素材盘点

| 路径 | 观察 | 判定 |
|---|---|---|
| `reference/_arknights_samples/ArknightsGameResource_5e2a435c51580f7776d46a88cc19ee9d2033137a/map/` | 6 张只读研究图，320×180 PNG、620,667 字节；另有 8 张已标记 out-of-scope 的夏日探索图。完整清单及 SHA 在同目录 | 来源与数据研究索引；不作为 P1 画面比较集、视觉标准或整图参考 |
| `reference/character_sources/ark_models/` | 存在 `.atlas`、`.png`、`.skel` 角色 Spine 文件；文件时间为 2026-10-24 | 角色资产，不是关卡地图，不是今天下载的环境包 |
| `reference/tool_research/2026-10-24/` | 存有 Ark-Studio、stage-viewer 等工具/代码快照 | 旧工具研究，不是导出的游戏场景内容 |
| `planning/art/ARKNIGHTS_MAP_DECOMPILED.md` | Markdown 数据研究文档，不含其描述的原始关卡 JSON、版本提交号、SHA 或可复现解析证据 | 研究草稿，不是“今天已下载地图”的凭证；其 3D 管线推论已隔离 |
| `art/static_map/p1_autumn_courtyard/v05/` | 有 Blender 源、PBR 贴图、阶段图和旧评审；其参考是 t084 | 秋日目标的历史候选；冻结证据保留，不把旧分数迁移成新评审结果 |

## 对旧解包研究文档的纠正

`planning/art/ARKNIGHTS_MAP_DECOMPILED.md` 把关卡网格数据进一步写成“每格 tile prefab”“固定 0.4 米高度”“PBR/Lightmap”“相机属于关卡数据”“社区素材法律上能用”等结论。当前本地没有该文档提及的原始 `level_main_00-01.json`、`map.json` 固定版本、仓库 commit、哈希和复现命令；引用的旧资源查找指南也明确提示内容过时。因此：

- 关卡 JSON 中可观察到的字段和值，只有在保存原始文件、来源 commit/版本、SHA 和解析器后，才标为 `verified_data`。
- 从字段推导出的渲染/模型结构标为 `hypothesis`，需用对应版本的实际资源对象和可复现解析来验证。
- PBR、烘焙、prefab、0.4m、draw-call 和“法律上可用”等表述不得进入风格标准或验收报告，除非有直接证据。
- 原始研究文档仍可追溯，但不作为制作入口、场景规格或授权依据。

## Harness / 验收标准审计

| 标准 | 当前定义 | 判断 |
|---|---|---|
| 静态地图工作流 | G0 P1 参考/哈希核验 → G1 空间灰模 → G2 主要物件组合 → G3 完整静帧/源文件/绑定/自评；一次连续执行，低分自修 | 主参考已固定；校验文件 SHA 后执行，不再等待 Arknights 视觉参考包 |
| 静态图画质门槛 | P1 秋日标准的 85/100、六维每项至少 3/4、所有硬门槛通过 | P1 标准是视觉评分依据；CW fixture 校验不产生视觉分数 |
| 完整游戏 `art_review/rubric.json` | ENV/CHAR/UI/MIX 四卡、85 通过、各维最低 2/核心维度最低 3 | 对完整游戏卡片有效，不适用于只交环境静帧的任务 |
| `producer_review_policy.json` | 完整游戏制作侧 sample 85、提交独立审核前 90；要求 Q01–Q09、47 项和构建绑定 | 当前静态地图阶段不运行该入口。将 90、四卡、Q 检查或角色策略套到静态图会造成错误阻塞 |

### P1 秋日静态图 Harness 需要的最小证据

当前静态图 Harness 主要是工作流和目标标准中的**文档规则**，不是已经接入专用 CLI 的自动验收器。现有 `tools/art_harness.py` 默认读取 `art_review/harness_contract.json` 与 `art_review/rubric.json`，检查完整游戏阶段、四张卡和完整美术目录；`tools/test_art_harness.py` 是该旧 Harness 的合成回归测试。没有发现一个专用于静态地图的通用门禁脚本。v05 的局部接地脚本只验证列出的对象，不等于新目标的总 Harness。

静态地图模型不要运行旧 `art_harness.py` / `producer_review.py`；旧脚本不应改成接受静态图假分数。新 validator 设计按 `knowledge/MAP_PARAMETER_HARNESS_RULES_20261029.md` 拆成源数据 fixture、项目自有场景结构、P1 视觉辅助三个 profile。视觉评分与 P1 特征匹配仍由 REVIEW 中的证据化评审处理；机械脚本不得自动给 85 分或代替人眼判断。

1. **G0 参考身份门**：校验 P1 秋日主图路径、分辨率和 SHA；局部裁切注明回链和坐标。Arknights 样本另标 `data_fixture` 或 `read_only_research`，不得标作主视觉参考。
2. **输入类型字段**：在素材清单分开标记 `project_visual_reference`（当前仅 P1 t084）、`research_render_sample`（Arknights 关卡 PNG，只用于来源/数据研究）、`topology_data`（level JSON）、`tool_source`（解析器/查看器）、`production_asset`（进入 Blender/交付的原创或有许可素材）；不得互相冒充。
3. **资产来源门**：若生产文件出现从客户端/社区镜像导出的图片、Mesh、Spine 或贴图，记录来源仓库与 commit、原文件路径/哈希、工具及版本、输出哈希、许可/用途状态。无明确可再发布许可的游戏资产不得打包进项目成品；项目代码工具的开源许可证不覆盖游戏内容。
4. **画面门与机械门分离**：文件存在、哈希相符、Blender 可重开属于机械通过；P1 秋日风格、空间层次、材质和完成度必须由固定主参考下的视觉评审通过。
5. **评分校准不设中途阻塞**：每个候选在同一连续执行中做一次按量表评分和一次反证复核，记录证据与扣分原因；只有完成的候选才可沉淀为评分样例。若后续出现不同评审结果，同维度差异超过 1 档或总分差异超过 5 分时，补充可观察锚点并复核，不通过改权重或降低 85 分线消除差异。没有多个已验收案例前，将评分标为“项目内自评、尚未跨评审校准”。
6. **连续执行与诚实结案**：自评、反证、返修、重渲、复核在一次制作运行中完成；没有外部授权/文件缺失等真实阻塞时，不等待中途审批。静态地图的结案状态按当前 `STATIC_MAP_WORKFLOW_20261028.md` 执行：只有 `target_met` 或有证据的真实外部阻塞可结束；未达标必须返修。分数与证据绑定同一 Blender 源和最终渲染。

## 今天整体变更后的判断与下一步优化

### 方向正确的部分

- 区分 P1 秋日视觉目标与 Arknights 参数研究样本；CW 数据用于 Harness 结构约束，不覆盖画面目标。
- 保持 P1 主参考与秋日锚点作为视觉标准；CW 数据和图像不进入画面评分。
- 把当前工作收敛为一张原创布局、Blender 可编辑的静态环境图，停用角色/UI/Cocos/微信整游戏 Harness。
- 把制作阶段压成四关口并在一个连续执行里完成，保留失败返修记录，不在中途等待外部评审。

### 仍需补上的关键点

1. **先核验秋日参考文件。** 当前已有锁定的 P1 整图及 SHA；如增补局部裁切，需回链到原图坐标和哈希，不得因 CW 参数样本而换整图目标。
2. **把数据研究和画面参考放在不同目录/清单。** `level_*.json`、`levels.json`、`map.json` 作为拓扑/关卡语义资料，不参与色板和材质统计；游戏地图 PNG 只能按实际内容标记为关卡图像，不默认是可商用素材。
3. **先做一张“参考事实板”，再制作。** 每张参考写可见事实（镜头、地表分区、结构接触、材质颜色/明暗、前中远层级）；另列制作推断和未知项。这样可以避免旧文档中由数据字段跳到官方 PBR/Prefab 管线的推理错误。
4. **把评分校准和返修闭环并入静态图流程。** 85 门槛暂时保留；参考未锁定前不评分。参考锁定后先跑两次独立盲评，发现分歧就补清晰锚点，不调低标准。自评低于门槛时自动继续改源、重渲、复核。
5. **控制素材盘增长。** 不全量克隆或下载数 GB 客户端包；先用 GitHub 浏览器确认类别、许可证说明与样例尺寸，再只取最小的公开数据样本。没有用户要求的情况下，本轮不把游戏原始素材下载到项目。

## 源与访问日期

- [ArknightsGameData](https://github.com/Kengxxiao/ArknightsGameData)：游戏数据仓库；README 说明部分数据由 OpenArknightsFBS 解析。
- [ArknightsGameResource](https://github.com/yuanyan3060/ArknightsGameResource)：根目录含地图 PNG 目录和关卡 JSON；README 声明静态资源属于游戏版权方且仅供学习交流。
- [Ark-Unpacker README](https://github.com/isHarryh/Ark-Unpacker)：工具功能与输入要求；[发布页](https://github.com/isHarryh/Ark-Unpacker/releases)本次核查显示最新标记为 v5.2.0；[资源查找指南](https://github.com/isHarryh/Ark-Unpacker/blob/v5.x/docs/zh/AssetsGuide.md)标注基于旧客户端版本且过时。
- [Stage Viewer](https://github.com/Awedtan/stage-viewer)：作者说明该网站复现并模拟关卡，鸣谢原始游戏数据仓库。
- [ArknightsMapViewer](https://github.com/winny727/ArknightsMapViewer)：地图文件查看工具，README 链接地图关卡 JSON。
- [Ark-Studio](https://github.com/isHarryh/Ark-Studio)：当前状态要以最新分支/发布重新核对；本地旧快照的 v0 已弃用。
