# 本轮美术产出独立审查报告

日期：2026-10-24。范围：当前art_complete候选包（本庭院章节全部美术），不要求本轮完成G1玩法或G2微信发布。审查者：Codex；未制作本轮资产，未创建控制器密钥/签认。

## 1. 审查结论

**返修，当前不通过完整美术验收。** 本次确实交出了可编辑3D资产、真实Cocos场景、原Spine和全套UI状态，已超出过去的概念图阶段。文件覆盖与引擎导入取得进展，但P1目标的构图、植被、材质与融合质量未达到既定要求；存在角色遮挡和暂停锁定的可复现问题。

“47/47 engine_verified”只能表达制作方登记的引擎显示/技术状态，不等于47项独立视觉批准，更不等于P1级美术完成。制作方报告如实保留accepted=false，本轮没有证据表明其伪造了控制器批准。

本轮独立review已绑定现有manifest，重新交harness验证结果为：

```json
{"status":"blocked","accepted":false,"error":"Visual gate not passed: H02"}
```

结果文件：[review_gate.json](review_gate.json)。没有降低门槛，也未修改资产、合同或制作方历史报告。

## 2. 实际审查方法与边界

- 读取当前合同1.3.0、rubric1.2.0、完整目录、47份逐项review、交付报告、运行说明、采集脚本和主要Cocos脚本。
- 独立重算13条主产物＋381条catalog依赖记录，共394条冻结记录的SHA256，全部匹配。这里是记录数，不是394份独立素材。
- 看过P1 t015/t044/t054及当前角色对照页；用联系表筛查41张UI状态和34张资产镜头，对主场景/对白/树/木材/人物/Toast等原尺寸复核。联系表只用于浏览，原图未改。
- 用Blender4.5.15禁用脚本自动执行，实际重开MAP001、ENV006、PROP001三个原生源，确认不是改名文件；并检查网格、UV、材质和图像依赖。未对全部23个源逐一手工修改再导出。
- 解析最终MAP001 GLB的JSON/index accessor，检查网格、材质、纹理与三角面口径；检查源码ZIP中的CourtyardBootstrap.ts与当前源一致。
- 自行启动隔离本地静态服务，加载现有Cocos web-desktop构建，以Puppeteer实际触发键盘与查看器操作；不覆盖制作方截图。页面无pageerror。未从零独立重建Cocos工程。
- 未测微信构建/真机/帧率/显存/触控安全区，不据软件WebGL桌面运行推断手机表现。

本轮复查命令与结果：

| 操作 | 结果 |
|---|---|
| run-art-harness.ps1 audit | submission_present_not_accepted，accepted=false，退出1 |
| verify，无独立review | mechanical_checks=pass，needs_review；当前调用退出1 |
| runtime_probe.cjs | 退出0；正常/暂停/对白输入对照已记录 |
| Blender --background --disable-autoexec --python native_reopen.py | 退出0；三个真实源均成功重开 |
| verify，加本轮independent_review.json | 退出1；blocked，H02未通过 |

注意：文档旧有“verify退出3”的描述与这次实际进程返回不一致；本报告以本次返回和JSON状态为准，不凭退出码0/1替代accepted字段。

## 3. 哪些成果可以保留

| 交付部分 | 独立判断 |
|---|---|
| 角色来源 | 当前1015红黑角色的发型/头饰/服装/装备与P1对照支持匹配；原Spine路线正确，不应再自由重画人物 |
| 角色动作 | 已见真实30帧Move序列与引擎动作切换；这部分能继续使用，但世界遮挡/镜头尺度仍需修 |
| NPC | t054同人物静态切片可继续用，限制应保留为静态，不能称有原骨骼或独立呼吸动作 |
| 原生资产 | 地图、树、长椅确有可重开的.blend；保留模块结构与脚本，在其上改质量 |
| 引擎导入 | 真实Cocos项目和浏览器渲染成立；不是离线效果图冒充引擎 |
| UI组件 | 41状态存在，字体/图标/纸片组件可编辑，适合作为返修基础 |
| 门禁记录 | 制作方跑过prepare/verify，并保留needs_review；流程没有被完全省略 |

## 4. 独立评分

按当前rubric：维度0–4整数，权重折算；每卡需≥85，核心维度≥3，任一维度≥2。以下是本轮合同评分，**不是与P1的相似度百分比**，阈值仍为项目暂定标尺。

| 卡片 | 分数/100 | 结论 | 主要扣分 |
|---|---:|---|---|
| ENV 环境 | 37.50 | 返修 | 全图总览、树冠/草层次、纯色材质、灰褐光照 |
| CHAR 角色 | 75.00 | 返修 | 来源匹配较好，默认镜头过小，接地/遮挡融合不够 |
| UI 界面 | 61.25 | 返修 | 全状态有覆盖，纸片透感/手绘特征弱，暂停状态输入未锁定 |
| MIX 同屏融合 | 38.75 | 返修 | 原角色与简化环境精细程度差异、屏幕贴片遮挡、正式镜头可读性 |

没有用平均分掩盖某张卡失败。逐维分数、权重依据和绑定证据见[independent_review.json](independent_review.json)。

## 5. 主要缺陷及具体返修要求

### R01｜blocking｜角色/NPC使用UI层投影，未实现世界遮挡

**观察：** PlayerSpine和makeWorldSprite均挂characterLayer，通过projectToCanvas定位。独立将角色置(0,3)，角色仍画在树枝前。

**修改：** 将原Spine渲染到透明RenderTexture并放入世界面片，或实现已验证的世界骨骼渲染；正确深度测试，按需要隐藏树冠组；保留原动作。

**复核：** 同一机位连续走树前/树后、栏杆前/后；角色不盖住本应在前方的物体，脚底阴影跟随。

证据：`delivery/courtyard_scene_demo_sources_v3.zip`, `art/full/previews/engine/scene_gameplay_1280x720.png`。

### R02｜major｜默认相机为全图总览，角色与道具过小

**观察：** 源码相机(0,28,-28)，全图边界/灰褐外裙占据大量画面，主角约60像素高，偏离既定约12%-18%屏高。

**修改：** 将全图镜头保留为编辑检查模式；增加正式近景/跟随镜头，先以(0,10,-10)偏移和FOV35校准，再检查边缘封边。不要只放大UI层人物。

**复核：** 1280x720中主角约86-130px初始目标；出生/NPC/A/B/C/留言板均可读，正式机位不露大片无内容外裙。

证据：`art/full/previews/engine/scene_gameplay_1280x720.png`, `delivery/courtyard_scene_demo_sources_v3.zip`。

### R03｜major｜植被轮廓和层次明显未达到P1

**观察：** 主树枝条粗直、叶片稀疏且碎片化，灌木像零散小苗，侧花坛大面积空土；P1为成片秋叶、分层树冠和饱满草丛。

**修改：** 在现有可编辑源上重做主树冠：先大/中叶簇体块、再少量叶卡与空隙；补花坛灌木/干草层次，保留通路。

**复核：** 固定正式机位对照t015；树冠有连续可读体块，花坛不空，透明叠层与三角面实测。

证据：`art/full/previews/engine/assets/ENV006.png`, `art/full/previews/engine/assets/ENV008.png`, `art/full/previews/engine/assets/ENV009.png`。

### R04｜major｜引擎材质接近纯色，光照层次不足

**观察：** 独立重开地图/树/长椅：UV网格均为0，无外部图像；最终GLB textures=0。石/木/金属的外观变化有限，硬影和灰褐底色缺少P1暖光冷影与细腻材质。

**修改：** 为石/木/树干做UV及受控基础色/法线/粗糙度贴图或等效引擎原生材质；木纹沿木条、石地保持暖灰；先固定曝光再调冷灰填充和阴影。不能仅提高饱和度。

**复核：** 同机位石、木、金属近景与主场景均通过；Blender效果可追溯到引擎实际支持的材质。

证据：`art/full/previews/engine/assets/MAT002.png`, `art/full/previews/engine/assets/MAT001.png`, `art/full/previews/engine/assets/ENV006.png`。

### R05｜major｜暂停预览未锁定移动输入

**观察：** 独立正向对照：正常ArrowRight约0.9单位；pause_default状态仍约0.9单位；对白状态0。不是仅凭源码猜测。

**修改：** 所有阻塞面板统一输入锁；打开时清keys/joy/manualMoving，关闭时重新接受新输入；不要只遮住控件。

**复核：** 键盘和触控分别展示暂停前/暂停中/继续，暂停中位移0；不得依赖焦点缺失形成假通过。

证据：`art/full/previews/engine/ui_states/pause_default.png`, `delivery/courtyard_scene_demo_sources_v3.zip`。

### R06｜major｜三角面统计口径与最终GLB不一致

**观察：** 报告92,976；独立重开原blend基础网格93,912；最终GLB所有TRIANGLES索引解码120,304，24材质、173 primitive。统计口径不同，不能用源数据证明导出预算通过。

**修改：** 将实际导出模型/修改器后几何/运行时可见三角形分开统计；优先减少地砖重复细节和不影响轮廓的细分，记录实测drawcalls。

**复核：** 同一最终GLB与Cocos截图绑定统计；说明可见面数，不能把120304直接当GPU测量或把92976当最终导出值。

证据：`art/full/source/layout/MAP001_courtyard.glb`, `delivery/courtyard_scene_demo_sources_v3.zip`。

### R07｜major｜留言板完成变化缺少前后及重置证据

**观察：** FX003逐项review仅绑定一张静态图；源码focus只开FX贴片，未见空板/三卡分步/完成/恢复的完整状态演示。报告也将提交放G1。

**修改：** 无需先做整条任务，但资产查看器应可独立切board_empty/board_full/reset，并分别控制真实三张卡子物件；录制变化。

**复核：** 空→满→空连续录屏及三状态截图，初始任务HUD与板状态一致。

证据：`art/full/previews/engine/assets/FX003.png`, `art/full/reviews/FX003.json`, `delivery/courtyard_scene_demo_sources_v3.zip`。

### R08｜major｜技术自检覆盖了文件，却没有完成风格放行

**观察：** 47份review均为producer technical engine check；ENV006理由仅为在引擎中渲染。未有四卡独立review/控制器签认，scene_demo样板未获准就已扩批。

**修改：** 保留历史技术检查，增加本轮独立四卡与缺陷返修；先改正式同屏样板并复核，达标后才扩散修改。不得将engine_verified改成approved来解决。

**复核：** 四卡各>=85、核心>=3、任维>=2；开放blocking/major清零后重新冻结、复审并由控制器签认。

证据：`art/full/reviews/ENV006.json`, `art/full/art_complete_catalog.json`。

### R09｜minor｜UI纸片样式单一，透景与涂鸦弱

**观察：** 41状态有组件和真实文案，但几乎复用同一切角/双线框，底板偏不透明；Toast与左上HUD局部重叠。

**修改：** 保留组件，减弱重复边框，按层级调整透明度与原创手绘装饰；Toast下移到不重叠区域。

**复核：** 对白透出场景、主次清晰，所有Toast不覆盖HUD；真实手机可读性单列。

证据：`art/full/previews/engine/dialogue_npc_1280x720.png`, `art/full/previews/engine/ui_states/toast_task_update.png`。

### R10｜minor｜目录/规则仍有旧信息，审核状态存在歧义

**观察：** 完整目录47项均有非空blockers且status=engine_verified；MAP001仍写未做引擎截图。rubric.character_policy/AGENTS另存旧291候选，与当前合同1015不一致。

**修改：** 只将有新证据解决的阻碍转为resolved/history，保留独立审核未完成；角色ID以当前合同唯一读取，不在多处复制旧候选。

**复核：** 目录状态/阻碍/报告/来源一致；不能为通过而删除真实未解问题。

证据：`art/full/art_complete_catalog.json`。

## 6. 三个直接复现的结果

### 角色穿过前景遮挡

`runtime_probe.cjs`通过现有setPlayer将角色放到(0,3)，即主树后方；截图[behind_tree.png](behind_tree.png)显示人物仍位于树枝前。源码buildCharacter/makeWorldSprite使用UI节点和投影定位，UICamera清深度后叠加；这不是一个已通过世界深度的骨骼方案。

本次setPlayer用于隔离渲染检查，不代表正常移动可穿越花坛；不将调试API传送行为误报为碰撞错误。

### 暂停没有冻结输入

在有正常移动正向对照、画布已聚焦的条件下：

| 状态 | ArrowRight前后位移 |
|---|---:|
| 正常 | 约0.9单位 |
| pause_default | 约0.9单位，错误 |
| 对白 | 0，正确 |

使用headless软件WebGL，0.9不是目标速度测量，只用于同环境暂停与正常的比较。第一次未聚焦的零位移不构成通过结论；报告采用补上正向对照后的结果。完整数据见[runtime_probe.json](runtime_probe.json)。

### 原始模型统计不等于最终导出

| 口径 | 本轮结果 |
|---|---:|
| 制作方报告 | 92,976三角面 |
| 独立重开blend的基础网格 | 93,912三角面 |
| 最终GLB索引，74 mesh、173 triangle primitive | 120,304三角面 |
| GLB材质 / textures | 24 / 0 |

GLB120,304高于初始10万可见面预警，但不是GPU实际可见/提交面数；需制作方解释修改器/导出/剔除口径并实测，不能直接宣布手机性能不合格。当前截图全图入镜，尤其应提供实际运行时统计。零纹理与零UV不自动等于格式失败，但与当前平涂外观一致，无法证明P1材质质感已实现。

## 7. 其他模型有没有执行审核机制

**执行了机械检查和技术自检，没有完成独立视觉放行。**

- prepare冻结文件、verify检查绑定文件的机制有效，本轮394条记录未发现哈希差异。
- 逐项review的pass通常仅因“在引擎中渲染并截图”，不是P1轮廓/材质/构图达标的视觉理由。
- 完整目录47项仍保留非空blockers，有些是已经过时的“未导入引擎”，有些是真正的独立审核未完成；数据需要区分已解决与未解决。
- `scene_demo`风格样板未获独立放行便扩到全量，导致树、材质、镜头同类问题传播。后续先返修一张正式同屏画面，再改全图。
- 本轮将真实失败写入独立review后，harness确实返回blocked；没有控制器签认不能最终批准。

## 8. 下一轮派给制作模型的任务（按顺序）

1. **先只交一张正式同屏样板**：近景/跟随镜头＋真实主角＋一棵修好的主树＋石地＋长椅＋HUD/对白。保留全图镜头供编辑查看，禁止全图总览当正式游戏主视角。
2. **修世界融合**：原骨骼或其真实RenderTexture进入世界深度，提交树前/树后/栏杆前后连续片段。不要用UI层放大人物来掩盖镜头问题。
3. **补材质和植物**：在原生源局部修改，提供同一机位改前/改后/P1对照；先改轮廓、材质分离和冷暖层次，再加细碎装饰。
4. **补状态行为**：暂停锁定键盘/触控；留言板空→满→重置，提供查看器独立演示，不要求先接整条任务。
5. **校准最终导出统计**：同一GLB/构建统计三角形、drawcalls与材质，修复超预算；手机没有测就保持未测。
6. **样板复审后再扩全图**，再清理真实已解决的目录blockers并重跑prepare；新hash使旧审核失效，必须重新复核。

不要求重画主角、不推翻所有原生源、不在本轮先实现商城/完整任务/网页编辑器。完整玩法与微信发布的缺失已被报告，不额外作为本轮美术失败的理由。

## 9. 报告文件与安全边界

- `independent_review.json`：绑定当前manifest/组合合同摘要的正式审查字段与四卡分数。
- `defects.json`：10条开放问题，含修复动作与复核方法。
- `review_gate.json`：实际独立审核门禁结果。
- `integrity_full_hashes.json`：394冻结记录复核和最终GLB统计。
- `native_reopen.json`：3个源文件真实重开结果。
- `runtime_probe.json`、`runtime_probe.cjs`：隔离运行检查与复现代码。
- `ui_states_*.jpg`、`assets_*.jpg`、`move_sequence.png`：本轮浏览联系表，不替代原件。

所有本轮审查输出仅写入art_review/reports/independent_20261024/。未改生产资产/源工程/既有review/当前合同，也未自造任何controller批准。
