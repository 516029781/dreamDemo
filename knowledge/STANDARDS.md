# 当前规范速查

更新：2026-10-29。本文只定位规范，不复制完整阈值，避免产生第二套标准。

| 事项 | 当前规则 | 唯一依据 |
|---|---|---|
| 范围 | 一张静态环境地图和可编辑 Blender 源；人物、UI、玩法、Cocos、微信与完整游戏 Harness 暂停 | planning/art/STATIC_MAP_WORKFLOW_20261028.md |
| 主参考 | 秋日 `t084s.jpg` 是唯一整图视觉目标；CW-8/CW-9 不替代它 | planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md |
| 风格与评分 | 六维量表、秋日锚点和硬门槛只从 P1 标准读取 | planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md |
| 地图参数与 Harness | CW-8/CW-9 参数只作解析器 fixture；项目结构约束按自有 schema，分数不从地图数据计算 | MAP_PARAMETER_HARNESS_RULES_20261029.md |
| 地图资料与解包 | 关卡 JSON/地图 PNG/解包工具/生产素材分开标记；游戏资源只读，不进入产品、构建或 Git | ARKNIGHTS_MAP_DATA_AND_HARNESS_AUDIT_20261029.md + 样本目录 SOURCE_MANIFEST.md |
| Harness 范围 | 当前静帧不使用旧 ENV/CHAR/UI/MIX、47 项、Q01–Q09 或完整游戏门槛；静帧数据检查与视觉评审分层 | 静态图工作流、MAP_PARAMETER_HARNESS_RULES 和 P1 标准 |
| 可编辑源 | 交付 Blender 原生场景；导出图不替代源；本地素材记录来源并绑定 SHA | planning/art/STATIC_MAP_WORKFLOW_20261028.md |
| 返修与证据 | 固定相机比较；机械检查与视觉评审分开；失败记为 rework 并继续返修；只有真实外部阻塞可结束未完成 | 工作流与对应候选的 REVIEW.md |
| 磁盘 | 项目目录含工具与 `.git` 上限 15 GiB、12 GiB 预警；清理先 dry-run；保护源、候选和证据 | tools/maintenance/STORAGE_POLICY.md |

发生冲突时按 AGENTS.md 的当前执行范围处理；细节回到右栏唯一依据，不在本页再复制数值。
