# v13 开发记录（design r15）

- run：`knowledge/active/20261108-space-base-v13-testworkshop/runs/20261108-1755`
- 源：`tools/blender_space_base/build_scene_v13.py`（由 v12 派生）
- 检查：`tools/check_v13_workshop.py`、`tools/check_v13_organic.py`、`tools/repro_v13_render.py`

## 返修单（HARNESS_LIFECYCLE §4 格式）

| id | TEST-ID → 现象 → 区域/对象 → 根因 → 源级修改 → 预期 → 重跑 | 结果 |
|---|---|---|
| H1 | TV13-07：院落被宽浅色带切成两半、西侧有带顶仓库；`av_road` / `k05_roof` / 489 个非 ws 对象落在 dock 矩形；v07 引道与码头与试车间共用同一坐标系；新增 `purge_workshop_intruders()` 清 452 个；恢复围合；TV13-01/02/03/07 | improved |
| H2 | TV13-07：左侧仍有米色码头板；`quay_w` / `st_q*` 在 v -34…-48 逃过第一轮；清理范围扩到 v ±50 / u ≤125，保留 `scale_` 锚点；再清 480 个 | improved |
| H3 | TV13-03：4 个 roof 命中（岗亭/岗棚/比例车）；"全图不做屋顶"应覆盖小建筑；删除 4 个顶盖，保留本体敞顶；命中 0 | improved |
| H4 | TV13-05：E13 0.579 / E14 0.400 未达标；`sd_cont_`/`ws_cab_`/`ws_drum_`/`ws_palletbox_` 全同朝向且成排；给四组加 seeded 朝向/位置抖动，油桶改方箱；E15 修正为只数可辨体积物件（修实现，非放宽阈值）；E13 0.281 / E14 0.250 | improved |

## 复现

隔离目录重开重渲，比 **content SHA**（解码 raw RGB），不比 container SHA。
结果：`pass=true`，`rms=0.0`，`content_sha_match=true`。

## 代码约定

R1 破周期 / R2 破镜像 / R3 破朝向 / R4 破共线 / R5 工程构件例外；
seed `random.Random(20261108)`；地面实体板 ≥0.14 m（v12 薄贴片不受光的坑）。
