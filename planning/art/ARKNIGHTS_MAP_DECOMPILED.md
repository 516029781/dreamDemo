# [仅数据研究，推论待核实] 明日方舟地图文件拆解

> **隔离研究草稿，禁止作为当前技术结论。** 本地没有本文提到的原始 `level_main_00-01.json`、`map.json` 固定版本、来源 commit/SHA 和可复现解析记录。本文中的地图字段摘录尚未在项目内独立重跑；“tile prefab”“0.4 米”“PBR/Lightmap”“完整场景组成”“法律上能用”及旧 v05 性能数字等均未核验或已过时。JSON 只能证明经版本绑定后实际包含的字段和值，不能单独证明客户端的 3D 美术管线。不得把本文作为本篇美术目标、3D 地图编辑器规格或 v06 执行依据。当前视觉目标仅见 `ARKNIGHTS_BASE_MAP_ART_STANDARD_20261029.md`；资料分类和复核规则见 `knowledge/ARKNIGHTS_MAP_DATA_AND_HARNESS_AUDIT_20261029.md`。

日期：2026-10-28　数据源：`Kengxxiao/ArknightsGameData` 的 `gamedata/levels/obt/main/level_main_00-01.json`（真实文件，约 5 KB）、PRTS wiki 的关卡 JSON 展示、`ArknightsGameResource` 的 `levels.json` / `map.json`
定位：回答"它到底怎么做到的"，并把结论映射成我方可以执行的东西

---

## 0. 一句话结论

**谨慎结论：关卡 JSON 可表达战术格网和 tile 元数据；仅凭这些字段不能判断最终场景是如何建模、组装或渲染的。**
一张 9×6 的关卡，数据是 **54 个整数索引 + 54 条 tile 定义 + 6 行相机参数**，不到 5 KB。美术成本不在"摆场景"，在"做 tile 和摆件库"。

---

## 1. 真实文件长什么样

顶层只有 7 个键：

| 键 | 作用 | 本例取值 |
|---|---|---|
| `mapData` | **地图本体** | 见下 |
| `options` | 玩法参数（与美术无关） | `characterLimit:8`、`maxLifePoint:20`、`initialCost:10`、`maxCost:99`、`costIncreaseTime:1`、`moveMultiplier:0.5`、`steeringEnabled:true` … |
| `predefines` | 预置干员/装置 | 四个空数组 |
| `runes` | 难度词条（危机合约那套） | `gbuff_lifepoint`、`ebuff_attribute`、`cbuff_cost_recovery`，带 `difficultyMask`/`professionMask` |
| `environmentSe` / `mapId` / `operaConfig` | 演出与环境音 | 全 `null` |

`mapData` 内部：

| 键 | 作用 | 本例 |
|---|---|---|
| `map` | **整数索引网格**，6 行 × 9 列 | `[[45..53],[36..44],[27..35],[18..26],[9..17],[0..8]]` |
| `tiles` | **tile 定义表**，54 条 | 见 2 |
| `blockEdges` / `effects` / `layerRects` / `tags` | 阻挡边、特效、分层矩形 | 全 `null`（高级关卡才用） |

**关键机制：`map[i][j]` 不是 tile 类型，而是 `tiles` 数组的下标。**
所以同一种 tile 可以被任意多个格子复用——本例 54 格给了 54 条独立定义（没去重），但**机制上允许「6 条定义 + 网格引用」**。这是"一张关卡数据 5 KB"的原因。

---

## 2. 每格只有这几个字段

```json
{ "tileKey": "tile_road", "heightType": "LOWLAND", "buildableType": "MELEE",
  "passableMask": "ALL", "playerSideMask": "ALL",
  "blackboard": null, "effects": null }
```

| 字段 | 取值 | 含义 |
|---|---|---|
| `tileKey` | `tile_road` / `tile_wall` / `tile_forbidden` / `tile_start` / `tile_end` / `tile_floor` / `tile_fence` / `tile_reed` / `tile_reedf` / `tile_reedw` / `tile_telin` / `tile_xbdpsea` / `tile_corrosion_2` … | **决定用哪个 prefab、哪张贴图**。这就是美术的入口 |
| `heightType` | `LOWLAND` / `HIGHLAND` | **只有两档**。世界坐标 `z = heightType * -0.4` |
| `buildableType` | `NONE` / `MELEE` / `RANGED` / `ALL` | 能不能放近战/远程干员 |
| `passableMask` | `ALL` / `FLY_ONLY` | 地面单位能不能走 |
| `playerSideMask` | `ALL` / `NONE` | 哪一方能用 |
| `blackboard` | `[{key,value,valueStr}]` | 单格特殊参数（如 `sandbox_hidden_tile`、`def:0.5`） |
| `effects` | `null` / 数组 | 格子特效 |

注意 `heightType` 和 `buildableType` 是**两套独立语义**，不是冗余：
- `tile_wall` = `HIGHLAND` + `RANGED` + `FLY_ONLY` → **高台**，地面走不过去，但远程可以站上去；
- `tile_forbidden` = `HIGHLAND` + `NONE` + `FLY_ONLY` → 边界；
- `tile_road` = `LOWLAND` + `MELEE` + `ALL` → 敌人走的路，近战可部署。

---

## 3. 把这 5 KB 还原成网格

`map[0]` 是数据的第一行（约定 y=0 在南边，所以显示时要上下翻）。逐格解码：

| | c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 |
|---|---|---|---|---|---|---|---|---|---|
| **map[0]** | F | F | F | F | F | F | F | F | F |
| **map[1]** | F | W | W | W | W | W | W | W | F |
| **map[2]** | **E** | R | W | R | R | R | R | R | F |
| **map[3]** | F | R | R | R | W | R | R | R | **S** |
| **map[4]** | F | W | W | W | W | W | W | W | F |
| **map[5]** | F | F | F | F | F | F | F | F | F |

F=forbidden　W=wall（高台）　R=road　S=start（敌人入场）　E=end（我方终点）

敌人从右下 S 出发，沿 map[3] 向左，被 (3,4) 的墙挡住 → 上到 map[2]，向左被 (2,2) 挡住 → 下回 map[3] → 再上到 (2,1) → 抵达 (2,0) 的 E。**一张教学关的节奏，全在这 54 个字符里。**

“0.4 米高差”及 `tileKey` 到实际场景对象的对应关系未由本地原始资源验证；不要把这句话用于场景比例或资产设计。

---

## 4. 相机：一行数据

`view` 是两组三维坐标 `[[相机位置], [目标点/边界]]`：

```json
"view": [[0.0, -4.81, -7.76], [0.5975, -5.31, -8.642]]
```

本例的原始关卡文件里没有 `view`，相机参数统一放在仓库的 `map.json` 里，按 `levelId` 索引（`"obt/main/level_main_00-01" → [pos, boundary]`）。**相机是关卡数据的一部分，不是美术摆的。**

---

## 5. 为什么"数据是 2D 网格，画面是 3D 场景"

以下为旧文档的制作假设，不是经过验证的官方实现：

1. **tile prefab 本身是 3D 的**，走标准 PBR + 烘焙（Lightmap + Shadowmap），所以格子看着有体积、有 AO、有磨损；
2. **只有两档高度**，深度关系极简单——不需要处理任意高度差带来的穿模和排序；
3. **摆件（树、栏杆、废墟、管线）挂在格点或格边，不参与地面合批**，因此地面可以整片静态合批，摆件按材质合批。

旧资源查找指南对目录的描述基于较早客户端版本，作者也标注文档过时。关于 AssetBundle 内场景/贴图/模型内容、公开范围、许可证和法律可用性的判断必须独立核对；本文不提供授权结论。项目应分别记录数据参考、图像参考、工具代码和实际导出资产。

---

## 6. 我方实测：draw call 到底卡在哪

把 `candidate_n5s1q/source/MAP001_courtyard.glb` 逐 primitive 统计（169 meshes / 447 primitives / 36 materials / 716,463 tri）：

| 组 | 材质数 | primitives | 占比 | 三角面 | 占比 |
|---|---:|---:|---:|---:|---:|
| **leaf 系** | **10** | **242** | **54%** | 338,372 | 47% |
| **grass 系** | 2 | 70 | 16% | 207,102 | 29% |
| stone 系 | 4 | 39 | 9% | 48,088 | 7% |
| wood 系 | 3 | 34 | 8% | 42,894 | 6% |
| metal 系 | 4 | 23 | 5% | 45,010 | 6% |
| ink | 1 | 10 | 2% | 28,330 | 4% |
| 其他 | 12 | 29 | 6% | 6,667 | 1% |

（实机 540 draws = 这 447 个 submesh + 阴影/额外 pass，比例一致。）

**两条硬结论：**

1. **draw call 是「材质数 × 用到该材质的网格数」的乘积，不是面数。** 10 个 leaf 材质各自都要为每一片树冠/绿篱开一次——这就是 242 个 prims 的来源。方舟用一个图集 + 全局 tint 把这类东西压成个位数。
2. **铺装根本不是问题。** `MAP001_paving_slabs` 只有 **1,800 三角面**（占 0.25%），`paving_mortar` 152 面。前几轮折腾的砖缝白点、缝宽不齐，是**视觉问题**（逐块随机内缩 + 运行时法线走样），不是几何成本问题。

> **修正上一版 v2 的一个错误**：路线 A′ 第 4 项写的"石板改 8–10 个模块 + 图集"打偏了靶——它只能动到 0.25% 的面。**真正该动的是叶材质 10→1、草材质 2→1。**

---

## 7. 该抄什么，不该抄什么

### 抄（结构层面）

| 方舟的做法 | 我方对应 |
|---|---|
| 索引网格 + tile 定义表 | 庭院改成"面层网格 + tile 表"，而不是每块石板生成独立顶点 |
| tileKey 决定 prefab + 贴图 | 建立 `surfaceKey → (mesh, material, uv block)` 注册表 |
| 只有两档高度 | 庭院其实只有"铺装面 / 花池面 / 台阶"三档，不需要任意高差 |
| 摆件挂格点、不参与地面合批 | 树/长椅/栏杆/指示牌登记为 props，地面单独合批 |
| **共享图集 + 全局 tint 替代逐物体材质** | 10 个叶材质 → 1 个叶图集材质 + 顶点色/tint |
| 玩法参数（options）与美术分离 | `THREE_STYLES.json` 现在把美术和玩法混在一起，应拆开 |
| 相机是关卡数据 | 机位写进关卡配置，而不是写在脚本常量里 |

### 不抄

- **2D 网格塔防本身。** 我们是庭院探索，不是格子塔防；网格粒度应该更细（建议 2 m），而且允许非整数坐标的摆件。
- **单格双人高的棱柱路径。** 方舟的墙面是纯棱柱，为塔防服务；我们的花池、台阶、路缘需要斜面。

---

## 8. 我方 `MAP001` 的 schema 草案

保留庭院自由布局，但把"生成顶点"变成"生成数据"：

```jsonc
{
  "id": "courtyard_autumn_01",
  "grid": { "cell": 2.0, "cols": 18, "rows": 14, "origin": [0, 0] },

  // 面层：每格一个 surfaceKey，复用定义表
  "surfaces": [
    ["paving_stone","paving_stone","paving_stone","soil"],
    // ... rows
  ],
  "surfaceTypes": {
    "paving_stone": { "mesh": "tile_slab_2x2", "material": "atlas_env", "uvBlock": [0,0], "height": 0.00, "edge": "joint" },
    "paving_brick": { "mesh": "tile_brick_2x2", "material": "atlas_env", "uvBlock": [1,0], "height": 0.00, "edge": "joint" },
    "soil":         { "mesh": "tile_soil_2x2",  "material": "atlas_env", "uvBlock": [2,0], "height": 0.15, "edge": "curb"  }
  },

  // 摆件：自由坐标 + 变体 + 朝向，不参与地面合批
  "props": [
    { "key": "tree_maple_a", "at": [6.0, 4.0], "rotY": 32, "scale": 1.0, "variant": 2 },
    { "key": "bench_wood",   "at": [3.5, 9.0], "rotY": 90 },
    { "key": "railing_iron", "path": [[0,0],[18,0]], "spacing": 2.0 }
  ],
  "propTypes": {
    "tree_maple_a": { "mesh": "prop_tree_a", "material": "atlas_env", "lod": ["prop_tree_a_lod1", "prop_tree_a_billboard"] }
  },

  "camera": { "pos": [0, 12, -14], "target": [0, 1.2, 0], "fov": 35 },
  "lighting": { "preset": "autumn_afternoon" }   // 指向烘焙预设，不写实时灯
}
```

生成器（`tools/blender_n5/*.py`）的职责从"生成每一块石板"变成"读这个 JSON，按 `surfaceTypes` 拼 tile、按 `props` 摆件、最后统一合并 + 烘焙"。**这样一轮改造同时解决四件事**：面数、draw call、可编辑性、石板缝不齐（缝由网格边界给出，不再逐块随机内缩）。

---

## 9. 立刻能验证的最小实验（不动布局，1–2 小时）

| 步骤 | 预期 |
|---|---|
| 1. 把 10 个 leaf 材质合成 1 个：共用图集 + `COLOR_0`（导出为 **ubyte normalized**，避开之前 uint16 被当 float 读的发白问题） | leaf prims 242 → 约 36 |
| 2. 草材质 2 → 1（同法） | grass prims 70 → 约 22 |
| 3. 同类网格按材质合并（`join`） | 再砍一批 |
| 合计 | 447 → **约 150**，实机 draws 540 → 约 180 |

**验收**：同机位截图 ΔE < 2；`q06_stats.json` 的 `prims` 与 `stats_ui_visible` 同步下降。

这一步做完，再谈"tile 化 + 烘焙"才有意义——因为如果只是材质合并就能把 draws 砍到 1/3，说明我们**不需要换资产，只需要换材质的组织方式**。

---

## 10. 参考

- 关卡数据：`Kengxxiao/ArknightsGameData` → `zh_CN/gamedata/levels/obt/main/level_main_00-01.json`
- 关卡/相机汇总：`yuanyan3060/ArknightsGameResource` → `levels.json`、`map.json`
- 坐标换算：`z = heightType * -0.4`（`Arknights-Tile-Pos`）
- 场景渲染方案：鹰角 黄一峰，Unity 线上技术大会 2020《明日方舟中 3D 和 2D 结合方案》
- 法律边界：官方 Re-creation Terms 禁止"直接使用游戏内素材进行复制、扫描、采样"，且仅限非商业
