> 已停用的交接单（2026-10-29）：不要按本文 v03/v04 阶段任务执行。当前执行入口为 planning/art/STATIC_MAP_WORKFLOW_20261028.md v6。

# 交接文档：静态地图 v03.8 → S1 构图重排

生成：2026-10-28 21:10。用途：把当前状态完整交给下一个执行者（人或模型），避免重新踩已踩过的坑。

## 1. 项目与目标

- 项目根：`C:\软件\鼠鼠`（下称 ROOT）。一切命令在 ROOT 下执行。
- 任务：按参考图 `reference/_raw_screenshots/P1/t084s.jpg`（1920×1078）制作一张静态地图画面。**只做这一张图**，不做角色玩法、不做微信构建、不做 O/C/R 多档。
- 参考基准：`t084s`，SHA256 `13706e7e…7446de`。
- 环境六维评分目标 **≥90（每维 ≥3/4）**，现实区间 85–89；植被 4 分需要 2D 补绘，卡片路线到不了，已和用户确认按 85–90% 卡片路线执行。
- 总方案：`planning/art/MASTER_PLAN_20261028.md` §9（v04 确认版）；工作单 `planning/art/STATIC_MAP_WORKFLOW_20261028.md`（v2）；构图基线 `planning/art/target_layout_v04.json`（v04.1，六锚点 + 三条基准线 27/51/67）。

## 2. 当前状态（v03.8）

| 项 | 值 |
|---|---|
| 六维自评 | **58.1/100**，`quality_below_target`（v02 为 50，增量全部来自材质与光向） |
| 对象数 / 渲染 | 4,986 / 83 s（Cycles 40spp，1920×1078） |
| 主文件 | `art/static_map/p1_autumn_courtyard/v03/build_scene.py` → `scene.blend` |
| 相机 | loc (0.25, −20.5, 8.2)，look_at (0, 0.35, 0.95)，53 mm，f/3.2，focus 22.2 m。完整参数见 `v03/camera_and_render.json`，**机位冻结** |
| 色彩 | view_transform **Standard**（AgX 已证伪勿改回）、曝光 −0.25 |
| 光 | 太阳右上 (7.8, −5.6, 9.4) 能量 2.15，暖色；阴影落左下，与参考一致 |
| 后处理 | 全在 JS：`tools/art/apply_post.js`（Bloom .16 / Vig .20 / Grain 3 / CA 1）+ `tools/art/compose_ui.js` |
| 已结案 | 铺装读感（大板、通缝、无小砖纹）；台阶暗槽与黑洞；光向；Standard 色彩 |
| 未动 | **构图（S1）**、缝软化（S2）、植被（S3）、远景三层（S2/S3）、道具（S2） |

关键实测（对照参考）：石板 4.3 块/画面宽 vs 参考 8.7；缝 ΔL 121 vs 6–9；广场占屏 45% vs 31%；台阶 12% vs 26%；L p50 130 vs 102。

## 3. 下一步就是 S1：构图重排（六锚点）

目标（`planning/art/target_layout_v04.json` v04.1，六锚点 + 误差 ±3–4pt）：

| 锚点 | 屏幕 x / y（%） |
|---|---|
| 左树 | 5–30 / 3–46 |
| 前景台阶 | 13–40 / 67–100 |
| 主平台 | 0–76 / 51–88 |
| 中景设施 | 32–55 / 28–55 |
| 右侧草池 | 50–100 / 14–63 |
| 冷色远景 | 30–54 / 13–27 |

S1 要做的动作：广场进深缩短（45%→31%）、台阶前移放大（12%→26%）、草池左缘 68%→50%、树冠下缘 32%→46%、中景设施下移 6–7pt、机位微调。
**判据**：六锚点 ±3–4pt；产出素模 + `planning/art/TARGET_OVERLAY_v04.svg` 半透明叠图对比。
**止损**：最多 2 轮；仍不达，改用参考图做相机背景板描图定位，不再调参。
**S1 期间禁止动材质与植被**——构图一动，所有区域数值作废（已发生两次）。

## 4. 已证伪的做法（禁止重复）

| 编号 | 坑 |
|---|---|
| F1 | 全局直方图做验收闸门：一条 LUT 就能骗过 |
| F2 | 撒碎片刷"四边遮挡"：0.64 也算 PASS |
| F3 | `view_transform='AgX'`：整幅高调、暗部塌 |
| F4 | 太阳放左上：影子方向与参考相反 |
| F5 | 材质白名单 `startswith('Warm limestone…')` 漏掉 `Sunlit limestone slab`：贴图等于没贴 |
| F6 | 纹理用 Object 坐标：每块板图案相同，要用 `ShaderNodeNewGeometry.Position` |
| F7 | 贴图直接 MIX 会把亮度拉走 50 级，要用灰度 MapRange 后相乘 |
| F8 | **"太密"≠"板太小"**：放大到 2.325 m 方向反了，主因是缝太黑 + 广场太大 |
| F9 | 板随机旋转 ±0.004 rad 会造成 9 mm 错台，长缝必须 ≤±0.0006 |

## 5. 排队中的缺陷（按段）

- **S2**：缝软化 ΔL≤20、板回 1.2–1.3 m、污渍裂纹、台阶鼻线仍贴小方砖（白名单漏项，与大板冲突）、叉车去玩具感、远景三层、接入冻结 LUT（`planning/art/grade_lut.json`）。
- **S3**：草改金色加密到看不见容器边；树冠明度压 0.7×；**ATLAS-01**——图集 (0,0) 与 (1,1) 是同一张叶卡、(0,1) 有卡未引用，树冠只有一种叶形。修法：`assets/foliage/atlas_manifest.json` 里把 (1,1) 换成未用卡，`CARD_LEAF_CELLS` 改为三卡，改完必须重渲。
- **S4**：角色阴影方向、提亮回调、UI `--no-ui` 参数（见 `v03/PRESENTATION_CHECK.md` P-03/P-05/P-10）。

## 6. 常用命令（ROOT 下）

```
blender -b -P art/static_map/p1_autumn_courtyard/v03/build_scene.py     # 建场景+半尺寸预览
blender -b -P art/static_map/p1_autumn_courtyard/v03/render_post.py     # 1920x1078 beauty
node tools/art/apply_post.js art/static_map/p1_autumn_courtyard/v03/renders/beauty.png art/static_map/p1_autumn_courtyard/v03/renders/clean.png --bloom .16 --vig .20 --grain 0 --ca 0
node tools/art/compose_ui.js art/static_map/p1_autumn_courtyard/v03/renders/clean.png art/static_map/p1_autumn_courtyard/v03/renders/final_ui.png
blender -b -P art/static_map/p1_autumn_courtyard/v03/make_stages.py     # 01/01b/02 阶段图
node tools/art/pack_card_atlas.js --check                               # 图集可复现校验
python tools/maintenance/storage_report.py --depth 1                    # 容量
```

Blender 路径：`C:/Users/tt/.cache/blender/5.2.3/blender-5.2.3-windows-x64/blender.exe`。

## 7. 流程纪律

- 一批只验证一个主假设；同机位前后图都要存；失败也要记录（写进 `METHOD_PROOF.md` 失败反例表）。
- 每轮结束更新 `v03/DELIVERY_v03.json`（含 SHA）、`REVIEW.md`、`MASTER_PLAN` §9 追加小节。
- 新增指标先做"作弊实验"再上闸门——本项目已 3 次"指标全过、画面更差"。
- 容量：当前 11.45 GiB，预警线 12 GiB，上限 15 GiB，余量仅 0.55 GiB；预计新增 ≥50 MiB 前先跑 `python tools/workflow.py storage --planned-growth-mib <N> --enforce`。最大可清退项是 `tools/cocos/` 5.49 GiB（可重建缓存），清退前需用户确认。
- AI 图仅限植被 alpha 簇卡（用户 2026-10-28 授权例外），且必须记录模型名与 prompt——**这项还没记录，是缺口**。

## 8. 交付物清单（v03.8）

`v03/renders/`：`final_ui / final / clean / beauty / layer_char`（1920×1078）+ `01_blockout / 01b_color_key / 02_material`（960×539）+ `details/` 5 张 1:1 局部。
`v03/`：`DELIVERY_v03.json`（含全部 SHA）、`camera_and_render.json`、`REVIEW.md`、`METHOD_PROOF.md`、`PRESENTATION_CHECK.md`、`ASSET_SOURCES.md`、`scene.blend`。
图集：`v03/assets/foliage/atlas.png` + `atlas_manifest.json` + `tools/art/pack_card_atlas.js`（重建逐像素一致）。
