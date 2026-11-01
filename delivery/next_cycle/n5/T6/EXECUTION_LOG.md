# T6 执行日志：n5s1q / n5s1r

日期 2026-10-28（日志 run_id 的 UTC 时间见原始 event.json）。所有时间仅统计一条工具命令，不代表全轮耗时。源候选 n5 冻结包未改写；q、r 是独立候选副本。

| run_id | 动作 | 结果/退出码 | 耗时 | 证据 |
|---|---|---:|---:|---|
| 20261027T181354Z_d8017924 | s1q 阶梯/构图 Blender 构建 | 命令0；仅命令完成 | 178.273s | `delivery/performance/20261027T181354Z_d8017924/` |
| 20261027T181903Z_5093f844 | s1q Cocos 首次错误路径 | 1 | 0.182s | 原始 event/stdout/stderr |
| 20261027T181953Z_8233e92b | s1q Cocos 再次错误路径 | 1 | 0.147s | 原始 event/stdout/stderr |
| 20261027T182047Z_b5cd72f7 | s1q Cocos 构建尝试 | 1 | 28.775s | 原始 event；候选构建日志后来有完成标记 |
| 20261027T184635Z_4533b4d3 | s1r 默认路径 Blender 导出 | 0但导出失败 | 31.800s | `delivery/performance/20261027T184635Z_4533b4d3/stderr.log`：叶片atlas相对路径无法读取 |
| 20261027T185132Z_c4a9dff6 | 修正路径后从保存 blend 导出 s1r | 0；export gate pass | 19.145s | `delivery/performance/20261027T185132Z_c4a9dff6/`、s1r export gate |
| build_s1q | Cocos web-desktop输出 | 门禁 pass_with_known_exit_36；内部日志报告构建任务完成 | 日志写9s内部耗时 | `candidate_n5s1q/cocos_build.log`、`cocos_gate.json` |
| Q01-Q09 | 浏览器证据检查 | Q01-06/Q08/Q09 pass；Q07 pending；overall pending | 复采脚本记录于捕获 JSON | `candidate_n5s1q/quality_check_n5s1q.json` |
| storage | 项目总空间 | over_limit，超15GiB 11,193,801 bytes | — | `delivery/workflow/STORAGE_STATUS.json` |

## 失败反例与返修决定

1. 相对 atlas 路径失败：保留失败原始日志；以显式绝对路径导出一次，不覆盖原生源。
2. s1r 三角面数/包体突增：不构建、不作为候选放行；先固定变量、预算，再重新导出。数据见 `candidate_n5s1q/ASSESSMENT.md`。
3. q06 原 stats 文件串入 n5 GLB hash：原文件重命名保留为 `q06_stats_stale_reference_failed.json`，现 q06 记录重绑 s1q GLB；失败记录不作为验收证据。
4. Cocos 构建两次短失败和一次退出码1的尝试全部保留；最终成功判定只采用当前 `cocos_gate.json` 的有序 SIGTERM+成功标记+输出检查，不依据“进程退出0”单项判断。
5. Q07缺受控源编辑无关对象比对，标 pending；严禁把 Blender 能打开/导出直接写成可编辑流程通过。
6. 全景美术未达标，s1q不送独立审核；现有最大阻碍是空间审批拦截了旧构建缓存回收，下一轮大构建前先处理这个外部阻塞。

### 追加：证据校验工具迭代与空间预检

- `tools/art_gate/check_quality.py` 首次退出2，环境缺 `jsonschema`；校验依赖装在项目外 `%LOCALAPPDATA%\Temp\codex-jsonschema-20261028`，没有把包加进项目。之后遇到缺 `binding_id`、证据 JSON 多出字面 `\n`、Q03/Q05 measurements 结构不符合 schema、Q08 清单 SHA 过期；逐项修正并重跑。最终状态为有意的 exit2 / `pending`，唯一 pending 是 Q07，Q01–Q06/Q08/Q09 pass、failed=0。
- 最终候选清单30项逐项 hash 核验，0 个缺失/不匹配。`candidate_manifest_n5s1q.json` 是候选文件索引，不是独立审批准入。
- 旧构建清单复测大小：build_s1i 159,972,649 bytes；s1j 159,972,655；s1n 159,988,575；s1o 159,973,948；合计639,907,827 bytes。排除本次 PowerShell 会话后，没发现其他进程命令行引用这些目录。
- 清理缓存调用之前已被自动审批策略拒绝；即使这些输出可重建、共约610 MiB，也没有再换删除接口执行。需要恢复至少约172 MiB 才能容纳一轮160 MiB级别构建并回到15 GiB限额以内。
