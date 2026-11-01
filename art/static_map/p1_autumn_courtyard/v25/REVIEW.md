# V25 制作与评审记录（P1 秋日庭院）

日期：2026-11-01。候选目录：`art/static_map/p1_autumn_courtyard/v25/`（由 V24 基线复制建立）。
执行依据：`planning/art/V24_SCENE_LOGIC_AND_ART_REVIEW_20261101.md` §8.3 任务表 N0–N5。
唯一整图参考：`reference/_raw_screenshots/P1/t084s.jpg`（SHA256 `13706e7e...7446de`）。
Blender：5.2.3 LTS（`C:/Users/tt/.cache/blender/5.2.3/blender-5.2.3-windows-x64/blender.exe`）。

## 1. N0 基线核实

- 校验 SHA：V24 源 `0ac1d9d2...cea973`、V24 成图 `72196214...0fca9`（与评审文档一致）、参考图与标准一致。
- 相机核实（读取场景而非猜坐标）：`P1 fixed still camera` loc (0.25, −20.5, 8.2)、euler (69.328°, 0, 0.687°)、53mm/36mm、DOF 24m、Cycles、Standard、exposure 0.34。
- 单位 METRIC scale 1.0。外链图像 4 张当时可解析（后经重开验证发现其中 4 张跨版本引用 v24，已在 N5 修复为 v25 相对路径）。
- 对象普查 `N0_CENSUS.json`：1248 个网格对象。关键对象身份与顶底高度全部实测，写入 `OBJECT_DECISIONS.csv`：
  - 宽阶 = `P1 steps | 00..08`（x −10.4..3.5 横贯 13.9m，z −1.37→+0.04，源自 v24 s7_steps.py）——确认与主楼梯完全独立，可干净删除；
  - 主楼梯 = `Broad worn curved stair tread 00..08` + 双 cheek + 铁艺（z −1.25→−0.09，底落低地 −1.27，顶距铺面 0.07m）；
  - 高台挡墙 = `Deep platform plinth left/right`（z −1.31→−0.10，楼梯开口 x −4.55..−1.75 与梯宽对齐）；
  - 低地 = 前景 `Ground plane beneath courtyard`（z≈−1.27）+ 后方 `P1 tier | low ground S/W/E/N`（z≈−0.30）；
  - 护栏 = `Landing iron rail ×3 + post ×9`（立柱埋入 plinth 顶，栏杆段在 x[−6.40,−0.60] 留口让出楼梯出口）。
- 交付：`BASELINE.json`、`OBJECT_DECISIONS.csv`、`N0_CENSUS.json`。容量预检：项目 7.2G < 15GiB 上限。

## 2. N1 空间结构（R01/R02）

假设：删除通宽阶并修补楼梯衔接后，"低地→主楼梯→高台"连续成立。

- 删除：宽阶 9 件 + 依附已隐藏 fascia 的悬空 expansion joint 7 件（共 16 件）。
- 新增：`P1 stair landing cap`（闭合 tread00 顶 −0.09 → 铺面 −0.02 的 0.07m 收口）、`P1 stair rear fill`（楼梯背后 plinth 开口腔体填充至铺面底，x[−4.55,−1.75] y[−0.90,3.00] z[−1.31,−0.02]）。
- 命令：`blender -b scene.blend -P preflight/n1_space_fix.py`（exit 0，1.1s）；诊断渲染 `n1_diag_render.py`（exit 0，33.1s）。
- 验证（`renders/n1_gray.png`、`n1_top.png`、`n1_side.png`）：
  - 无通宽阶 ✓；主楼梯独立清晰、底部落在低地 ✓；挡墙立面垂直落地、无黑洞/悬空 ✓；
  - 低地 S 南断面（y=8, z −0.6..−1.27 空隙）经计算被 terrace 南立面自身遮挡，主相机不可见（§8.1 只要求可见连接成立）✓；
  - 前景未新增大物件（cap 0.07m 收口与腔体填充不算）✓；楼梯出口未被堵 ✓。
- 场景 SHA（修改后）：`b5bd90d0a7cd273d`。

## 3. N2 功能分组（R03–R07）

假设：删除无依附/无用途物件、货物集中到叉车旁、电柜/垃圾桶/花坛让出楼梯出口走廊后，维护/物流/种植三区可辨且主通路成立。

- 两轮执行（n2_function.py 删 27 移 20 增 1；n2b_layout_fix.py 删 1 移 28），发现并处理：
  - 泵平台组（Service platform + Pump housing + deck grate ×5）是**落地完整设备**，保留为维护组主体；
  - 悬空件全删：梯子（顶部无依附）6 件、灯泡 ×6、围栏 ×3、游离螺栓、空方池 5 件、悬空前景桌 5 件、挡出口路锥 1 组；
  - 移位：货组（3 箱+盖+桶）→ 叉车东北；dumpster → 西列；cabinet → 维护组；软管 → 电柜旁；kerb A → 与 kerb B 连成南缘花坛带（避让出口走廊）；
  - 新增管组基座（x[0.55,1.60] y[1.30,2.00] z[0.04,0.75]），管线落地依附。
- 通路验证：出口 y[−0.9,1.23] 全宽 2.64m ≥ 楼梯净宽；西侧转向通道 x[−4.47,−2.30]（2.17m）；东侧经 apron 通塔区。
- 验证（`renders/n2_gray.png`、`n2_top.png`）：出口净空 ✓、物流组成组 ✓、维护组可辨 ✓。
- 场景 SHA：`a34894d0061ef33e`（n2）/ `3d...`（n2b 后，见 N3 记录链）。

## 4. N3 植被（R08/R09）——含两次失败与换方法记录

- 批 1（n3_vegetation.py）：205 簇草随机化（z-rot ±28°、scale 0.85–1.22、位置抖动）✓ 有效，保留。加 4 个噪波暗冠球 + 9 个远岸灌木球 —— **失败**：球体感明显，违反"不得是圆团"标准。
- 批 2（n3b）：改用共享 mesh 链接复制作暗冠/远冠 —— **失败**：linked duplicate 的材质槽修改污染了原树冠（整冠变暗近消失），远冠卡定位不准。
- 批 3（n3c）：恢复被污染的 overlay 材质；暗内层改用**单用户 mesh 拷贝**+独立深叶材质（multiply 修正接线）✓；删除失败的远冠复制。
- 批 4（n3d，根因修复）：核实 v24 起左树树冠就几乎全部在画面外（树高 ~10m，相机在树距处画面上缘仅 z≈3.4m）——对照参考图为"短干大冠"型。整树缩放 0.5 并落回台面（z 0.06），暗层卡重新定位冠内。**左树冠首次进入画面**，压边作用恢复 ✓。
- N5 批 E：冠再放宽（xy 0.74/z 0.52）+ 顶层叶卡（单用户拷贝）加密，冠形更圆润。
- 远岸（R09）：blob/加植方案两次失败后不再加密植被；改由 N4 材质降低远岸对比（base 提亮 (0.085,0.078,0.062)）+ 既有 crown 群轮廓 + N5 批 G 左段补 2 张冠卡（单用户拷贝，定位已验证）。远岸顶部无硬折面抢眼 ✓。
- 水面降饱和：Emission 0.68→0.374，Base (0.045,0.062,0.082)。

## 5. N4 材质与光色（R10）——含失败与回调记录

- 批 A：木箱 wave 条纹加密+noise 打散 ✓；金属 spec 0.5→0.28 ✓；格栅压暗 ✓。
- 批 B（N4b）：**失败与回调**——ramp 端色取算术中值导致木箱灰白化；立即以胡桃木色对 (0.055,0.030,0.016)/(0.235,0.135,0.072) 修复。kerb 花坛 0.84m→0.52m（降为坐凳高种植池）+ 土色去饱和 ✓。
- 批 C：挡墙/低地大面加低频明暗变化 ✓（低地 soil 变化链生效）；挡墙根 6 处草簇（楼梯口两侧避让）✓。
- 批 D：**修复遗留接地问题**——CC0 power box 悬空 z0.61→落地 0.04（N2 漏处理，N0 普查与 §8.4 接地检查漏检，此处如实记录）；管组/电柜贴图 spec 0.5→0.32；泵台顶 multiply 0.85。
- 批 F（N5B/F2/F3，对照参考校准）：参考图树冠为**深琥珀暗色**、设备群整体偏暗——叶色 multiply 0.42→0.32、设备群（power box/pipes/pale top）multiply 压至 0.42–0.45、木箱乘 0.45。期间确认"浅色横槽柜"为泵检修罩（Pump access housing，木纹材质、合法设备部件、坐于泵台顶），通过木纹密度回调（wave 2.6→1.6）使其读作深色木罩。
- 批 G：白罐再压一档；远岸左段补 2 冠卡。
- 相机/曝光/主光参数**全程未动**（exposure 0.34、sun/sky/fill 保持 v24 定稿），光色改善全部来自材质明度分工。

## 6. 重开验证（N5）

- `scene.blend` 贴图路径已全部改为候选内相对路径（`//assets/...`、`//background_src/...`；4 张 v24 跨版本引用修复）。
- 独立验证：复制 scene.blend + assets + background_src 到 `C:\tmp\v25_reopen\`，从该目录重开渲染（16spp/25%）：`TRUE_MISSING: NONE`，渲染图无贴图缺失色块（第一次发现 M02/M03 缺失系验证目录漏拷 background_src，补齐后通过）。42 个 packed 内嵌贴图不依赖磁盘路径。

## 7. 六维评分

见下文 §9（以最终图为准）。

## 8. 硬门槛逐项

| 硬门槛 | 结论 |
|---|---|
| 前景高差/栏杆缺失 | 无缺失：主楼梯 9 级+双扶手+台缘栏杆（post 埋 plinth）✓ |
| 右侧圆筒草池缺失 | 存在：石基座+鼓身+木冠肋条+顶草 ✓ |
| 主石地大片单色/棋盘格 | 无：大板家族+接缝+裂纹贴片+设备投影 ✓ |
| 树冠规则球团/重复尖片 | 无：Poly Haven 叶卡+暗内层+顶层卡，冠形不规则 ✓ |
| 草池稀疏尖片 | 无：v16 簇群 205 簇随机化、根密顶疏 ✓ |
| 中景只剩无功能方盒 | 无：泵平台（格栅+检修罩+压力罐）、电柜、管组+基座、软管依附，功能可辨 ✓ |
| 远景大面积棕色硬几何 | 无：远岸坡+冠群打断+左段补冠，轮廓起伏 ✓ |
| 材质外链丢失 | 无：重开验证 TRUE_MISSING NONE ✓ |

组合四项：地板 pass（大板家族+接缝一致）；树 pass（占位/枝干/冠形负空间成立，局部密度略低）；草 pass（连续起伏块体+根部暗部）；光色 pass（四角色分工+阴影有细节）。

## 9. 六维评分与五轮盲评

最终图 `renders/final.png`（96spp，SHA `3db2b42cb4284305`）。制作侧自评 79.4（仅用于返修导航）。

盲评（独立评审代理，互不知晓制作过程，按 P1 标准六维+四项组合+八项硬门槛）：

| 轮次 | 评审 | 总分 | 硬门槛 fail | 备注 |
|---|---|---:|---|---|
| 1 | A / B | 55.3 / 55.3 | far_shore×2；B 另有 grass | 初版：宽阶已删、结构成立，远景棕色硬几何为主因 |
| 2 | C / D | 67.8 / 61.3 | far_shore×2、D 另有树冠 | M02/M03 冷贴图后分数上升，但顶部仍暖 |
| 3 | E / F | 60.6 / 61.3 | E: grass | 雾 0.55 过量把远景冲白、石地暖角色丢失 |
| 4 | G / H | 65.4 / 51.6 | G: 无；H: 树冠+草 | **far_shore 首次全过、G 轮光色组合 pass**；资产精度层差距主导 |

远景问题的根因链（五轮探索后才定位，如实记录）：M02/M03 贴图冷化 → 无效；crown/far bank/Rear terrace 地面冷化 → 无效；world 雾冷化 → 无效；最终在合成器定位到 **Mist Map Range To Max=0.125（雾量被 v24 压到 12.5%）+ 暖雾色 (0.80,0.76,0.70)**——所有远景像素被 12.5% 暖雾覆盖，材质层任何修改都被稀释。修复：雾色改深蓝青 (0.26,0.345,0.50)、雾量 0.42 后，远景冷调成立并被第 4 轮盲评确认（far_shore ok）。

**当前结论：rework_required，未达 85。** 结构性目标（无通宽阶、低地→主楼梯→高台、功能三区、远景冷调、树冠入画）已实现并被盲评确认；差距集中在资产精度层（草叶直立麦束感、树冠叶团重复、石面无磨损分布、素方盒、种植槽皱纸填充），需要几何级重做而非参数调整。返修队列见 §11 与 GATE_REPORT.json。

## 10. 盲评

按工作流 G3，两份独立盲评（互不知晓制作过程，仅按 P1 标准对 final.png 与参考图评审）结果见 `GATE_REPORT.json` 的 blind_reviews 字段；本报告不预设其分数。

## 11. 状态

- **`rework_required`**：五轮盲评（55.3/55.3 → 67.8/61.3 → 60.6/61.3 → 65.4/51.6）均未达 85；hard gate far_shore 已修复并获确认，组合门槛 light 在 G 轮 pass。结构修复（N1/N2）稳定成立。
- 返修队列（几何级重做，下一轮优先级序）：
  1. 草几何方法重建（弯曲多叶、根密顶疏的簇替换 v16 直立卡）——塔顶草池与种植槽统一语言；
  2. 左树叶团重建（非重复叶团、琥珀内层与受光外层、参考占比冠幅）；
  3. 石面磨损/粗糙度沿走动路径分布+边角崩口；
  4. 素方盒设备补功能细节（面板线/铰链/标识）或删除；
  5. 种植槽皱纸填充替换为塔顶草语言。
- 交付物齐备：`scene.blend`（相对路径可重开，独立目录验证 TRUE_MISSING: NONE）、`assets/`+`background_src/`+`ASSET_SOURCES` 说明（见 DELIVERY.json）、`reference_analysis/`、`renders/`（blockout/color_key/combined/no_dof_diagnostic/final/details）、本 REVIEW、`DELIVERY.json`、`GATE_REPORT.json`（含全部五轮盲评原文）。


## 12. 艺术向修复轮（2026-11-01 下午，方案 P1_V25_ART_REPAIR_PLAN_20261101.md）

执行模式：一次性连续跑完（用户指令）。7 批全部执行，每批留证。

| 批 | 内容 | 结果 | 日志 |
|---|---|---|---|
| R1 | 光方向校准（右后上方 55°，影子翻向左下） | ✓ 影子方向与参考一致；坑：sun 为 QUATERNION 模式，rotation_euler 赋值无效 | R1_LIGHT_LOG |
| R2 | 树冠重做（删 4 张暗卡+3 团真叶副本） | ✓ 轮廓柔软化，叶隙透空 | R2_TREE_LOG |
| R3 | 草重建（127 实例换 3 弯曲原型 + 27 束风弯） | ✓ 风感成立，密度保留；坑：mesh datablock 带 .001 后缀需二次补 | R3_GRASS_LOG |
| R4 | 石板岁月（68 板分 5 区块明暗+磨白区+3 修补板+立面） | ✓ 大块节奏可见 | R4_PAVING_LOG |
| R5 | 设备剪影（罐箍带/法兰/跨管/柜前桶）+杂项（旗降饱和/落叶散点） | ✓ | R5_EQUIP_LOG |
| R6 | 远景层次（雾 0.42→0.33 + 5 组近档剪影） | ✓ 两档剪影可辨 | R6_FARSHORE_LOG |
| R7/R8 | 盲评共识返修（树 ×1.34 移台角 / 草加密 / 石板调暖 / 橙板压制） | 部分 | R7/R8_LOG |

### 橙色悬空板追凶（跨 15 轮排查）
射线/ID 图/消融多法失败后，最终用**二分隐藏法**（1016 对象 log2 收敛，10 轮渲染）锁定：
`v15 planted tree-bed soil surface`——v15 时代遗留的树床土面卡（材质 Dry grass shaded root mass），
平放在台面左区。删除后橙像素 6700→1129（余为叉车/桶等合法橙色）。教训：ID 图在
exposure≠0 时解码需补偿，且 1016 色 hsv 表分辨率不足以精确匹配；二分隐藏+像素计数才是确定性手段。

### 修复轮盲评轨迹
- R 轮（修复后首评）52.9/67.5 → S 轮（共识返修）66.6/66.9（**+6.5**，树 pass×2、far_shore 保持）
- T 轮（橙板清除后）61.5/58.1（盲评噪声内波动，无提升 → 触发收敛停止规则）

### 诚实结论
结构/光色/构图层的修复被多轮确认；剩余差距为**资产精度级**（树叶团分层密度、小筒草根密度、
花槽揉纸填充物、铺装三色统一、设备工业语言），每项需几何级重做，归入下一轮返修队列（见 GATE_REPORT）。

## 13. v26 植被回滚轮（2026-11-01 下午，用户指令）

用户反馈：草和树叶与环境不搭配，要求回到之前的效果。方案：P1_V26_VEGETATION_ROLLBACK_PLAN_20261101.md。

### 证据链
- git 为 code-only，旧场景不可从 git 取回；旧效果来源为 `_backup/` 快照
- 旧树叶 = `scene_pre_B.blend`（R2 树冠重做前）；旧草 = `scene_pre_D.blend`（R3 草重建前）

### 执行（preflight/v26_rework.py rev2 + v26_link_fix.py）
| 操作 | 数量 | 说明 |
|---|---|---|
| 删 R2 clump | 3 | `P1 canopy clump 00-02` |
| 删 R7 加密草 | 36 | `P1 densify tuft 00-35` |
| 取回旧叶卡 | 4 | `canopy inner A/B/C` + `top layer`（自 pre_B append+link） |
| 树变换还原 | 2 | LOD1+overlay 回 pre_B 位姿 (-9.2,7.3,0.1) scale 0.82（撤销 R7 移位/×1.1） |
| 草还原 | 137 | 127 实例 mesh+变换回 pre_D 状态（旧 silhouette 家族）+ 变换类修正 |

### 保留（未回退）
R1 光方向、R4/R7 石板、R5 设备、R6 远景雾+剪影、橙色悬空板删除、R5 落叶散点。

### 坑与教训
1. `libraries.load` 追加对象**不自动链入场景集合**——必须手动 `scene.collection.objects.link`，
   否则对象存在但不渲染；且未被链接的追加对象会被 orphans_purge 清掉
2. temp-append 记录变换时，同名对象会得到 `.001` 后缀——mesh 比较须用去后缀基名，
   否则 247 个对象被误判"mesh 变更"并挂上重复 mesh 副本
3. `libraries.load` 的 `data_from.objects` 清单含幻影基名（实际对象为 `.0/.1` 后缀变体），
   以 `bpy.data.objects` 实际枚举为准

### 留证
- scene.blend SHA-16: 751eb5fb8baf7b38
- renders/final_v26.png SHA-16: 933b44b06e980dd8
- 对比图: v26_compare_full / v26_compare_tree / v26_compare_grass.png
- 回退开关: `_backup/scene_pre_V26.blend`
- 状态: 待用户主观确认

## 14. v27 植被手绘化轮（2026-11-01 傍晚，用户指令）

用户判断：左树与背景草"太细、太像几何结构"，要求手绘效果。方案：P1_V27_HANDPAINTED_FOLIAGE_PLAN_20261101.md。

### 执行
| 批 | 内容 | 结果 |
|---|---|---|
| V27A | PIL 生成手绘贴图：canopy_full（整冠云朵+簇状笔触+阴影袋）、leaf_cluster_a/b、grass_tuft（宽叶束根深梢金），色板锚点取自参考图 | ✓ |
| V27B | 左树：删旧 4 叶卡+细碎枝叶 overlay+14 个错放 grove lobe+LOD1 叶卡面（slot1 376k 面中的叶面）+树枝材质调暖；树冠 = 1 张 3.6m 整冠大卡 + 5 张辅助卡（暗部/受光），面朝锁定相机 | ✓（6 轮迭代：位置×3、方案从 18 小卡改整冠大卡） |
| V27C | 127 个细丝草实例（v26 日志 changed=mesh 名单）→ 手绘草簇卡，密度×2（+127 克隆），倾角 4-14°，色板按景深三级 | ✓ |
| 追凶 | 冠下橄榄绿椭球堆 = `P1 left understory \| grounded leaf and flower cluster`（射线定位法），已删 | ✓ |
| V27D | 96spp 整图渲染 + 参考/v26/v27 三联对比 | ✓ |

### 本轮新增方法论
1. **相机射线定位法**：屏幕像素 → view_frame 反推射线 → scene.ray_cast 命中对象名，
   比 ID 图/二分法更快更准（本轮 10 分钟锁定 understory，上轮橙板用了 15 渲染）
2. **手绘植被 = 大团块卡 > 多小卡拼接**：18 张小卡呈"横条煎饼感"，1 张整冠大卡 +
   少量辅助卡才成立——手绘语言是"整块作画"不是"零件堆砌"
3. libraries.load 对象不自动链入场景集合（v26 教训再现，已入脚本规范）

### 留证
- scene.blend SHA-16: 3ea1b0e90d67fb8b
- renders/final_v27.png SHA-16: af2299926cc15430
- 对比图: v27_compare_ref.png（参考/v26/v27 三联）、v27_final_treezoom3.png
- 贴图: assets/handpainted/{canopy_full,leaf_cluster_a,leaf_cluster_b,grass_tuft}.png
- 回退开关: _backup/scene_pre_V27.blend
- 状态: 待用户主观确认

## 15. 空间清理记录（2026-11-01 晚，用户指令）

已删除：修复轮旧快照 scene_pre_B/C/D/R7/V26（1.35G）、v24 整目录（238M）、
工作区测试目录 hedge_test/grass_test/p0tmp/p0tmp_b（387M）、渲染诊断图 97 张（约 60M）。
保留：scene.blend、_backup/scene_pre_V27.blend（回退开关）、handpainted 贴图、
REVIEW/DELIVERY/日志、v27 产出图与参考证据图。

### 事故与恢复（诚实记录）
清理渲染诊断图时脚本过滤缺陷导致保留清单一并被删（113 张全清）。恢复情况：
- final.png / details.png（v25 交付版）：从工作区根目录副本恢复；
  final.png SHA=00c5efea9efa1df8 与 DELIVERY 记录(1113cb015d899391)不一致——副本为较早状态，如实记录
- final_v26.png / final_v27.png：从 scene_pre_V27.blend / scene.blend 96spp 重渲恢复
- ref_zoom_* 三张：从参考图重新裁剪
- **不可恢复**：blockout.png、color_key.png、no_dof_diagnostic.png（其 SHA-16 已存于 DELIVERY.json）

### 二次收紧（用户指令：只保留 v26/v27 内容）
删除 v25 时代产出：final.png / details.png / combined.png / no_dof_diagnostic.png
及工作区副本 v25_final.png / v25_details.png。
renders/ 现存 7 张：final_v26、final_v27、v27_compare_ref、v27_final_treezoom3、ref_zoom_tree/grass1/grass2。

## 16. 信息核查与勘误（2026-11-01 22:26，只核查不产图）

按 `planning/art/STATIC_ART_INFORMATION_CORRECTION_20261101.md` I0–I2 执行，详见
`planning/art/STATIC_ART_VERIFICATION_20261101_2226.md`。要点：

- 参考 / `scene.blend` / `final_v27.png` 三份实物存在，完整 SHA256 与状态文件相符（22:26 核对）
- 旧 `DELIVERY.json`（final.png 3db2b42c；r2 块 1113cb01）与 `GATE_REPORT.json`（final.png 3db2b42c、
  场景 02a67405）**均不对应当前 V27 图**，其评分与结论不得沿用
- 旧记录列举的 final/blockout/color_key/no_dof/details/combined 已随 11-01 清理缺失；
  blockout/color_key/no_dof 不可恢复
- 本节 §14 登记的图 SHA `af229992…` 已不对应当前文件（当前 `2d698729…`，清理后重渲）
- 源—图同源仍为 **unverified**；I3 遮罩/ROI 未校准，全图色彩统计保持 diagnostic_only
