# 制作经验索引

更新：2026-10-26。按 `SELF_LEARNING_LOOP.md` 维护。以下历史案例为 `proposed`，待 n5 实测及后续独立审核确认；不要把它们当成已通过的自动规则。

| ID | 状态 | 触发条件 | 症状与来源 | 改法和最小复核 | 反例/适用边界 |
|---|---|---|---|---|---|
| L01 | proposed | 修改移动、暂停、恢复、横竖屏 | n2 N09 曾漏先移动场景；见 `planning/execution/ACTIVE_REWORK_CYCLE.json` | 先移动再暂停/恢复/转竖屏；核玩家、相机、任务保持，恢复新输入有效 | UI 静态截图不能证明行为 |
| L02 | proposed | 新候选冻结/打包 | n4 ZIP/Q02 SHA 漂移及 build_id 不同；见 `art_review/reports/candidate_n4_provisional_20261026/REPORT.md` | 源 ZIP→SHA→manifest→审阅包，所有 Q/截图显式绑定 build report；已知坏样本应 fail | 只改 JSON 里的 hash 不算修复 |
| L03 | proposed | ENV/UI/MIX 自评或跨候选对照 | n4 自评与看图预评分差；见 n4 预审报告 | P1/上一候选/当前候选同机位原图，先找反例和写观察，再评分；后续比较独立分差 | 预评不是正式独立审核分数 |

新增条目保持一行可检索；详细诊断、原始记录和 hash 留在候选 `performance/` 与审阅包。每轮末更新状态、证据和失效原因，不覆盖旧报告。
