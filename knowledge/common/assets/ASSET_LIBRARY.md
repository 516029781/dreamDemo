# 资产库索引（common/assets）

本索引只登记元数据与兼容性，不默认加载资产本体。

## 策略

- 可编辑源（`.blend`）、贴图与导出图**不入 Git**，按 `AGENTS.md` 代码库策略保留在磁盘并登记 SHA。
- 每份交付使用 `ASSET_MANIFEST.template.json` 记录：role、path、sha256、bytes、editable、source/license、used_by。
- 引用外部素材（CC0、公开图集）须记录来源与许可；不得把未授权资源写入交付。

## 当前条目

| 范围 | 资产 | 位置（示例） | 备注 |
|---|---|---|---|
| P1 | 手绘叶团/草簇贴图 | `art/static_map/p1_autumn_courtyard/v25/assets/handpainted/` | 程序化生成，可重跑 `preflight/v27_textures.py`、`v27_canopy_tex.py` |
| P1 | 场景源 | `.../v25/scene.blend` | 本地，未入库 |

新增资产请先建 manifest 条目，再在业务包 references/asset 清单中引用。
