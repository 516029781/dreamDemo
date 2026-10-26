# 可编辑美术工具与明日方舟资源调研

> **角色来源已更新（2026-10-24换源）**：当前角色ID/版本/hash唯一读取 `art_review/harness_contract.json` 的 `locked_sources` 与 `character_source`（1015_aglna2）。本文写作时的“291_aglina候选为现阶段直接可用资产、待播放确认同皮肤”等表述已过时：播放确认已由1015播放包完成（`art/phase1/character_playback_1015/character_playback_1015_report.md`），291证据保留历史（`art/phase1/reference_character/SUPERSEDED_BY_1015.md`）。本文其余工具调研结论仅作只读参考，不复制角色ID。

日期：2026-10-24。范围：微信小游戏Demo、P1同风格庭院、复用参考人物。当前只做调研/方案与门禁加强，未安装运行下列新候选软件，未声称它们已在本机兼容。

## 1. 本次决定

用户明确不接受其他模型直接调用AI Image生成最终画面。当前项目改为“AI操作可编辑软件和已有资产”，不以扩散生图作为生产或概念阶段的默认路线。此前ComfyUI/Krita AI Diffusion为主的提案撤销；Krita原生绘图MCP与Krita AI Diffusion是两种不同工具，不能混称。

地图和道具：Blender对象、修改器、材质节点、复用贴图、场景布局。角色：已核对的Spine骨骼/atlas/贴图和原动作。UI：SVG/代码组件及Krita分层文档。PNG与视频作为导出/预览，而不是唯一源资产。

“可控”指能修改指定对象/图层/路径/骨骼、回退、保存源并重导出；它不自动保证模型具有专业画师的审美和造型能力。质量仍以P1特征、实际同屏与独立审核验证。

## 2. 明日方舟可复用内容

| 来源 | 实际内容/本轮核对 | 我们怎么用 | 不能误认什么 |
|---|---|---|---|
| [Ark-Models](https://github.com/isHarryh/Ark-Models) | 角色基建Spine、时装、敌人及动态立绘等分类；已按需取得291_aglina三文件 | 第一优先：复用目标人物及实际存在动作 | 并非完整游戏源码或全部地图 |
| [Ark-Pets](https://github.com/isHarryh/Ark-Pets) | 开源桌宠程序，复用方舟骨骼资源 | 研究加载、动作挑选/行为切换的实现 | Java桌宠不能直接导出为微信小游戏 |
| [Ark-Unpacker](https://github.com/isHarryh/Ark-Unpacker) | AB资源提取、RGB/Alpha合并、Spine导出等 | 若公共库缺特定资源，对用户本地游戏文件按需整理 | 不会自动重建完整可编辑地图，也不是地图编辑器 |
| [ArknightsAssets2](https://github.com/ArknightsAssets/ArknightsAssets2) | cn/en/voice分支；API目录中实际见tile_floor/road等贴图及uisprite/uimask文件 | 可检索头像、界面图集、地块贴图等，按文件列来源和用途 | 这些栅格图不等于P1庭院的模型/灯光/碰撞；本轮未确认P1完整场景包 |
| [ArknightsGameData](https://github.com/Kengxxiao/ArknightsGameData) | 游戏数据仓库 | 查ID、名称、关卡数据结构 | 数据表不是美术场景或可运行的原作工程 |

重要更新：旧[ArknightsAssets](https://github.com/ArknightsAssets/ArknightsAssets)已明确retired，并指向Assets2；不要固定已退役库作为新工具唯一资源源。先前猜测的Aceship/Arknights-Resources地址本轮返回404，不列为已验证下载源。

现阶段直接可用资产只有已下载的291_aglina候选文件，待实际播放确认同皮肤。其他仓库是资源检索候选，没有批量下载，也不承诺存在P1里的那棵树、每一件长椅或整张探索地图。

开源代码和原游戏美术各自有不同权利归属。Demo按需留存来源，不把社区文件称为官方开放素材。本次不增加上线/商业化流程。

## 3. 是否有开源地图编辑器

### 查到了同人关卡编辑器

[Stronghold-Protocol-Forge](https://github.com/XiaMo233M/Stronghold-Protocol-Forge)提供卫戍协议同人编辑器，编辑地形、路线、装置和出怪，含2D摆放及其游戏自己的3D预览。对应[编辑器文档](https://github.com/XiaMo233M/Stronghold-Protocol-Forge/blob/main/docs/EDITOR.md)也可查。

它与本项目的差异：它的地图格式、预览、寻路和包规范属于塔防/自走棋系统。未看到可直接导出我们Cocos探索庭院的兼容承诺。因此可研究“编辑器和校验器共用作者数据/派生规则”的设计，不能直接宣称拿来就能编辑P1同类场景。素材说明另有范围限制，源码不等于通用素材包。

本轮没有找到已验证可直接编辑P1同类自由行走3D庭院、再导入微信小游戏的明日方舟专用开源编辑器。这是有限检索结论，不是断言不存在。

### 通用工具选择

- [Tiled](https://docs.mapeditor.org/en/stable/manual/introduction/)：成熟的2D地图/对象标注编辑器，支持等距图层。可做格子逻辑、阻挡与交互标注，但不提供P1的真实3D建模/灯光生产。我们本次不作为主场景编辑器。
- **Blender＋Cocos场景编辑器**：推荐主路线。前者建模、摆场、可编辑源与批量变体；后者验证游戏实际材质、镜头、碰撞、交互。不能把Blender材质节点自动等同于Cocos可用材质，需要导出/烘焙和导入验证。

## 4. AI真正操作绘画/建模的软件桥接

### 4.1 Blender：推荐主工具，交互桥接可选

[mcp-for-blender](https://github.com/ahujasid/mcp-for-blender)：社区MCP桥接，文档列出对象、材质、Python执行与视图/渲染检查。适合模型修改真实场景并观察结果。该工具同时集成外部生成服务；我们只采用原生对象/材质/脚本/视图能力，不能因为装了插件就自动启用其生成3D或图像服务。

[BlendRelay MCP](https://github.com/shefq/blendrelay-mcp)：备选，项目声明支持Blender4.5+、Edit Mode、参考图/视口草图与对象操作。本轮API确认MIT、提交1edc0097f549221e44aece67efc7a8b789fb4360；未在本机测试。不同时安装两个桥接，先测试一个。

可靠批生产入口仍是保存过的Blender脚本与模板，MCP负责交互调整。每次完成一个对象就保存源、导出、重新打开检查；不要每次依靠聊天记忆重新造整个场景。

### 4.2 Krita：优先评估原生画笔/图层MCP

[krita-codex-mcp](https://github.com/cyyprezz/krita-codex-mcp)：文档列出图层/选区、原生笔刷、压力路径、预览和保存；其`krita_paint_path`通过Krita Node.paintLine API使用当前笔刷。Windows为原始支持平台，项目给出能力检查；应先验证本机实际Krita版本。

本轮API确认MIT、提交f2ca27a6872bdc7fe2267c485d5fa62fbb68c2a7，并找到真实skill：
[plugins/krita-codex-mcp/skills/krita-control/SKILL.md](https://github.com/cyyprezz/krita-codex-mcp/blob/main/plugins/krita-codex-mcp/skills/krita-control/SKILL.md)。它教授工具使用；没有安装/连接Krita插件与MCP，单独安装SKILL.md不会获得画笔能力。

[SanSaSane/krita-mcp](https://github.com/SanSaSane/krita-mcp)：另一候选，支持图层、形状、文字、滤镜和画布预览。本轮只查仓库文档，作为备用，不能声称和前者工具协议相同。

[painter](https://github.com/buttonscodes/painter)：概念最贴近“模型画笔→看结果→批评→局部修正”，项目明确不使用扩散；启动方式和样例偏Shell环境，尚未核实Windows可用性，故列研究候选，不设为本机主依赖。

这些桥接规模和成熟度不同，仓库里的演示/测试是作者报告，本轮未独立复现。第一次只做一个图标/图层测试，不能据此宣称能自动画出P1专业角色；目标角色已有Spine资源，无需重新画脸。

### 4.3 UI优先矢量结构

UI边框、图标、排版、按钮状态优先用SVG/代码组件；可在[Inkscape](https://github.com/inkscape/inkscape)等矢量编辑器中修改。复杂局部纹理才交Krita分层绘制。每个图形有稳定ID、色板变量、线宽和状态规则，要求修改一个图标不影响其他组件。

不要把生成PNG放进一个SVG的image标签，就称为矢量源。不要把完整图放进一个Krita图层，就称为可局部调整的分层生产。

## 5. 环境资产从哪里复用

- [Poly Haven](https://polyhaven.com/license)：官方说明HDRI、贴图和模型为CC0；适合选石地、木材、金属等基础材质后统一处理。
- [ambientCG](https://docs.ambientcg.com/license/)：官方说明资产为CC0，适合基础PBR材质。
- [Kenney](https://kenney.nl/support)：资产页素材为CC0。更适合灰盒、图标或结构起点，通常不能不经调整就达到P1质感。

这是通用资产库，不是明日方舟资产。复用后还要统一尺度、纹理密度、粗糙度、配色和面数。不能混搭几个包就认为风格已统一。当前不下载整包，等小场景资产清单明确后按需选取。

## 6. 我们自己的工具应该做成什么

推荐“现有编辑器内的窄插件＋CLI”，而非先自造完整绘图软件/地图编辑器：

### Blender地图工坊（自有部分）

只包含：资产托盘、统一尺度/原点、网格吸附、树/长椅/花坛的受控变体、命名/材质规范、角色出生点/交互点/阻挡标记、固定相机预览、导出检查按钮。

保存`.blend`；场景布置记录为layout.json（ID、资产引用、transform、阻挡/交互标签），并导出引擎验证支持的模型与贴图。Cocos导入脚本应单独验证坐标、缩放和材质映射，不能默认JSON会被引擎自动理解。

### Spine素材台（自有部分）

登记人物/皮肤/版本/来源hash→运行时解析动作→待机/行走/交互下拉列表→原速预览→缩放/锚点/边界检查→角色包导出。没有的动作显示缺失，不让模型自由编造。目标是重用现成动画，不是重造Spine编辑器。

### UI组件工坊（自有部分）

tokens.json＋SVG组件＋Krita可编辑装饰，参数改色板/线宽/尺寸/文案；同一母版输出按钮状态、对话框和图标族。支持单项修改和即时预览，输出源与PNG，游戏中文字由引擎排版。

三个工具共用资产登记、预览快照、版本哈希与harness审核，不先做账号、在线商城、模型训练和复杂工作流画布。

## 7. 接手模型的工具验证任务

1. 保持当前参考角色播放任务优先，不自由生成替代角色。
2. 核对是否有Blender/Krita；工具未安装/没连上就如实报告，不编造MCP调用。先选一个Blender入口、一个Krita候选。
3. Blender试验：创建可编辑长椅，修改某根木条宽度/一个材质，保存.blend，重开后确认改动保留并导出预览。
4. Krita试验：建分层图标（线稿/底色/装饰），通过原生工具改一笔和一个颜色，预览，保存.kra，重开验证；禁用生成接口。
5. UI试验：同一SVG母版改成4个图标并导出三种按钮状态，源路径可编辑。
6. 才封装上述模板成为自己的工坊插件，并使用harness提交真实源/操作日志/导出。用一次“能修改、保存、重开、重新导出”的试验判断工具可控性，而非只看一张好看的演示图。

## 8. 对harness的改动

生产方法声明必须属于reference_spine、blender_editable、blender_mcp_native、cocos_scene_edit、krita_layered、svg_editable、existing_asset_import的允许列表。ImageGen/文生图路线不作为当前准入方法。

scene_demo必须另交map_editable_source与ui_editable_source，源格式需结构检查：.blend/.scene、.svg/.kra。仅改后缀、只包含image的SVG会被拒绝。真实工具日志和独立复核仍必要；方法字符串/文件头通过不能证明美术质量或实际操作过程。

本地规则不能阻止完全写权限模型修改门禁，最终仍由外部控制器运行固定门禁并掌握放行权。当前修改没有安装任何第三方MCP，也没有替用户连接其他IDE。


## 8. 地图编辑能力补查（2026-10-24）

### 当前项目的真实能力边界

FULL_ART_DELIVERY.md第11–13节已规划自定义地图：自建/复用模块、Blender摆放与材质修改、布局记录、碰撞与交互标注、固定相机和引擎预览。但地图工坊面板、layout导入器仍待实现，不能声称已经可打开本项目的专用编辑器。现阶段选择Blender原生编辑＋后续Cocos场景验证；自有工具是其上的窄插件/脚本，不另造一套渲染器。

第一版编辑器实现清单：资产托盘；添加/选择/移动/旋转/缩放/复制/删除；网格吸附；源生撤销/重做；地面模块铺设；材质母版切换；出生/交互/碰撞/遮挡标记；layout保存/重载；单项模型导出和Cocos导入日志。树/建筑的形状仍在Blender建模，不把摆放功能称为自动绘制所有素材。验收需真实演示改一条路、挪一棵树、添加长椅、保存重开、重新导入后对应位置一致。不能仅有JSON文件即宣告编辑器完成。

### 新增公开源码候选：ZOOTLAB

来源：[ucynik/ZOOTLAB](https://github.com/ucynik/ZOOTLAB)，本次读取其README；尚未下载运行或核验整包许可。公开代码不自动等于可任意再分发的开源许可。

作者定位为非官方Unity明日方舟地图制作/模拟套件。README要求Unity 2021.3.29f1及可处理OBJ/FBX的建模软件，说明在Blender或Unity拼装地图、导入贴图、配置相机灯光、设置敌人路径与生成点；当前说明仅模拟敌人，干员模拟为计划项。文档自述部分过时，需结合教程和实际版本验证。

对我们有价值：研究真实地图网格/材质整理、Blender摆场导出、3D地图＋Spine表现、固定战斗镜头和路线配置。它并未给出P1庭院专用完整素材库或Cocos/微信导出流程，因此不替换现有主路线，也不宣称能一键做出P1风格。若评估迁移，先只用一小块模型/材质验证可编辑性与Cocos导入，不整套迁入Unity运行时和战斗逻辑。

### 其他结果与选择

- [Stronghold-Protocol-Forge编辑器文档](https://github.com/XiaMo233M/Stronghold-Protocol-Forge/blob/main/docs/EDITOR.md)：确认是独立本地工坊工具，服务其同人游戏内容与包格式；可研究地形/路线/内容登记，不视为通用3D庭院编辑器。
- [PRTS.Map](https://map.ark-nights.com/)页面明确目前无开源计划；不列为可复用源码。
- 截至本次检索，未确认官方公开发布、直接编辑P1同类自由行走场景并导出Cocos的工具。不是断言所有方舟地图工具都不存在。

结论：自定义地图的方法已进入方案，专用工具尚未实现；已有公开方舟同人工具可参考。对当前项目继续使用Blender原生编辑＋自有地图工坊＋Cocos验证，优先验证资产与导入链，再补便捷面板。


## 9. 深入核对：源码、资产结构与采用决定（2026-10-24）

### 9.1 本次实际做了什么

通过GitHub API取得六个项目的完整文件树/仓库元数据，并按固定提交保存部分README和关键源文件；不只阅读搜索摘要。证据在reference/tool_research/2026-10-24/，每个_sources.json有commit、固定URL、字节数与SHA256。未下载运行程序、未安装Unity/编辑器、未提取客户端、未下载整包地图模型，不将源码检查称为运行验证。API树均未截断；许可字段仅描述仓库检测结果，不覆盖第三方与游戏资产。

### 9.2 候选比较与源码证据

| 项目 | 核对内容 | 对本项目的决定 |
|---|---|---|
| [ZOOTLAB](https://github.com/ucynik/ZOOTLAB) | 提交808a77472b54667e149a0383f533db8a0f574ead；真实Unity工程、ExampleMap.unity、TemplateMap.fbx、材质贴图与Spine示例；ProjectVersion为2021.3.29f1 | 优先研究地图资产整理/导出和Spine状态切换；不整包搬运，不替换Cocos工程 |
| [Stronghold-Protocol-Forge](https://github.com/XiaMo233M/Stronghold-Protocol-Forge) | 提交300556c9ccda3bd8b22291ca0039da7d6ca69a15；stage3d.js实际复用游戏board3d渲染；stageAuthoring.js共享地图校验/派生规则；GPL-3.0 | 研究“编辑器与游戏共用渲染和作者数据”，实现本项目自己的布局合同；不是把其棋盘格式直接当庭院格式 |
| [AssetStudioMod / ArknightsStudio](https://github.com/aelurum/AssetStudioMod) | 基础分支MIT；方舟专用分支ArknightsStudio及ak-v1.2.3发布确实存在，包含Windows GUI及CLI包；基础CLI文档提供筛选、Mesh OBJ、模型FBX和材质dump | 优先评估为地图素材盘点/导出工具；方舟压缩格式需匹配专用版本，不能拿普通版本文档当专用版已运行证据 |
| [Awedtan/stage-viewer](https://github.com/Awedtan/stage-viewer) | 提交11b18075e615b0b394b1a9ee52d82113424450ac；App.ts用PIXI，MapTile.ts用PIXI.Graphics绘地块并处理可通行类型 | 属于关卡模拟/数据可视化参考，不是P1三维美术地图编辑器；不作为生产依赖 |
| [Ark-Studio](https://github.com/isHarryh/Ark-Studio) | 默认v0分支明确2026年2月弃用；另有v1分支，README明确开发中。v0列表含尚未实现的导出/搜索功能 | 不把它推荐为现成成熟地图工具；注意与aelurum的ArknightsStudio不是同一项目 |
| [Elit3D](https://github.com/christt105/Elit3D) | BSD-2-Clause；仓库README明确旧版停止维护，Godot重写版待稳定后发布，和宣传页面功能列表不能混为已稳定发行 | 可参考地块笔刷/多层编辑交互，暂不引入当前项目主链 |

#### ZOOTLAB具体能复用什么知识

已核对Assets/Map/Scripts/Animate.cs：使用Spine.Unity.SkeletonAnimation，依据位置变化切换真实idle/move动作，支持可选移动起止动作。可借鉴状态映射方法，但它的默认Idle/Move不能证明我们的291_aglina含同名可用动作。FixCanvasRotation.cs实际修正的是子节点缩放，不能因名称猜成角色朝相机的billboard实现。

Assets/Map下确有TemplateMap.fbx和TX_SecretRoom_*材质贴图等文件路径，说明仓库不只有文字教程；这些是示例/战斗场景路径，未确认有P1秋日庭院的树、长椅或完整场景。仅有路径也不证明模型可正常导入。GitHub未识别ZOOTLAB仓库级许可证，文件树还含Spine/Amplify/Standard Assets等第三方内容；当前只做方法研究，不能把整个工程标为统一宽松许可素材包。

#### Forge的3D预览并非无条件可用

stage3d.js明确依赖本地素材manifest、棋盘图集、可用WebGL2、three.js和实际board pack；任一失败就退到2D。源码还使用该游戏的固定棋盘区域/视角。它展示了可靠的共享预览架构，不代表克隆仓库后一定出现完整3D地图，更不代表包含P1自由漫步庭院。

#### 资源提取不等于恢复原工程

[AssetStudioMod说明](https://github.com/aelurum/AssetStudioMod/blob/AssetStudioMod/README.md)列出Mesh→OBJ、Animator→FBX和材质数据导出；CLI可以按名称/容器筛选，适合AI批量整理。[方舟专用发布](https://github.com/aelurum/AssetStudioMod/releases/tag/ak-v1.2.3)需单独匹配输入版本。不能默认恢复原作Shader、灯光、遮挡、碰撞和完整可编辑场景。合并网格可以编辑顶点，但不能自动拆回原始树木/长椅模块；需单独检查可拆分性。

### 9.3 未确认的线索

ArknightR/ArknightU有社区展示与转载线索，但本次没有核实到作者公开源码、清楚许可和可复现构建入口。保留为未确认，不推荐为已验证开源依赖。PRTS.Map页面明确无开源计划。搜索中出现的“口袋方舟”并非明日方舟地图编辑器，不混入候选；终末地地图工具也不当成本体P1素材工具。

### 9.4 对当前方案的实质调整：增加素材盘点关卡

此前“从零自建所有环境模块”的工作量可以先经资源盘点评估，再决定每项自建或复用：

1. 先定位P1具体场景的来源线索和资源目录；当前并未确定其客户端scene ID，不能用SecretRoom示例宣称匹配。
2. 用方舟专用查看/导出工具列资源，输出environment_source_inventory.json：源包/对象ID、文件hash、网格/贴图/材质依赖、可拆分程度、P1对应区域、可复用/需修复/不匹配及原因。优先盘点地面、长椅、栏杆、树与花坛，不批量导出整个客户端。
3. 实际选一件地面或长椅导入Blender，检查UV/法线/尺度/贴图，局部修改后保存重开，再导入Cocos。这个小件链路通过，才决定扩大复用。
4. 匹配并可用的素材登记为existing_asset_import，保存原件及编辑派生源；不匹配或不能可靠拆分的按Blender原生模块自建。没有找到客户端文件/目录时，记录该阻碍并继续自建，不让整个地图等待资源检索。
5. 用同镜头比较复用件与自建件，统一材质/光照后才扩大摆场。地图编辑、批量处理和审核继续沿FULL_ART_DELIVERY.md执行。

增加这一关是为了减少无效重建；它不保证能找到P1原地图，也不把获取素材许可视为已完成。源代码许可和原游戏资产权利分别登记。

### 9.5 自有地图工坊按什么次序实现

第一步复用Blender原生物件编辑、网格吸附、撤销/重做与资产组织；窄插件只增加项目资产ID、五套材质母版、布局/碰撞/交互标记和可重复导出。第二步实现layout→Cocos导入，并让查看器使用同一份布局数据。第三步才加地砖笔刷、树/草受控散布与一键固定镜头预览。

编辑器预览与最终游戏不能各有一套位置/缩放/碰撞定义。每次变更地图重导出后，应比较对象ID、transform和交互位置，并在实际引擎中查看。复用Forge的架构思想，不以其塔防数据约束庭院玩法。

第一轮评估交付仅需：候选工具版本/来源、少量素材盘点、一个可编辑小件和实际导入证据、采用/放弃理由。若失败，交具体输入与报错；不靠再增加候选工具列表代替决定。
