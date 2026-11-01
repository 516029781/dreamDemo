# 通用规范速查（common/dev_core）

更新：2026-11-02。只登记跨业务规则与指针；不复制业务阈值，避免第二套标准。

| 事项 | 通用规则 | 唯一依据 |
|---|---|---|
| 阶段与结束 | N0–N8；只有 `target_met` 或真实 `blocked_external` 可结束 | `HARNESS_LIFECYCLE.md` |
| 证据与 SHA | 源/候选/证据分离；完整 SHA；图变即证据失效；复现须隔离重开 | `HARNESS_LIFECYCLE.md` §3 |
| 身份隔离 | 每运行独立 `knowledge/active/.../runs/...`；候选单一写者 | `HARNESS_LIFECYCLE.md` §2 |
| 知识分层 | `common` / `business/<id>` / `active`；三字段 scope·lifecycle·maturity 分离 | `knowledge/README.md` |
| 未知与实验 | 未验证写 `proposed/observed`；未校准数值 `diagnostic_only` | `knowledge/README.md` §状态契约 |
| 磁盘 | 项目目录 ≤15 GiB，12 GiB 预警；清理先 dry-run，保护源与证据 | `AGENTS.md` |
| 交付 | 可编辑源 + 产物 + manifest + 测试结果；导出图不替代源 | `HARNESS_LIFECYCLE.md` §3 |

业务专属项（参考图、相机、评分、硬门槛、专属禁用）只在 `knowledge/business/<id>/`，不在本页。
