# 风格 Profile：<业务名称>

- business_id：
- lifecycle：`draft | active | superseded | deprecated | historical`
- maturity：`proposed | observed | reproduced | reusable | not_applicable`
- 激活依据 `activation_basis`（用户确认/日期/原话摘要）：
- 视觉参考（visual_reference）：路径 + 完整 SHA256

## 1. 参考可见事实（只写能看见的）

| feature_id | 观察项 | 参考位置/区域 | 可见特征 | 证据（裁剪图/SHA） |
|---|---|---|---|---|
| F-01 | 明度结构 |  |  |  |
| F-02 | 色彩角色 |  |  |  |
| F-03 | 材质语言 |  |  |  |
| F-04 | 光照与阴影 |  |  |  |
| F-05 | 构图与层次 |  |  |  |

## 2. 未知事实（不得编造）

| 未知项 | 为什么不知道 | 处理方式 |
|---|---|---|
| 原游戏内部建模/贴图流程 | 参考只是屏幕截图 | 只记录本项目可复现做法，不声称还原 |

## 3. 本项目适配决定

| feature_id | 本项目如何响应 | 决定来源 | 备注 |
|---|---|---|---|
|  |  | 用户指令/业务决定 |  |

## 4. 禁止项

- （本业务专属禁用内容；不得写成跨业务规则）

## 5. 诊断指标（未校准前仅诊断）

| 指标 | 当前值 | 校准状态 | 是否可作门槛 |
|---|---|---|---|
| 明度分布/饱和度/色相直方图 |  | 未校准 | 否，`diagnostic_only` |

## 6. 评分与门槛指针

- scorecard：`scorecard.json`
- 工作流：`<path>`
- 标准正文：`<path>`
