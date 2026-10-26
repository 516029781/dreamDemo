# 鼠鼠项目执行规则

当前处于独立审核退回后的制作返修。先读 `planning/execution/ACTIVE_REWORK_CYCLE.json` 指向的报告与返修工作单，以其 `next_candidate`、`open_findings` 为准；冻结候选只读。`tools/workflow.py summary --write` 的当前返修提示优先于首次 V06/V07 路线；账本仍为唯一任务状态。自审低于提交门槛时，在同一制作轮实际修改原生源并同机位预览，不能仅记录下一步后结束。

更新：2026-10-25，用户明确要求“完整制作后统一评审”。workflow_mode=candidate_first_final_review。先读START_HERE及MODEL_EXECUTION_GUIDE，运行tools/workflow.py summary --write读取当前工作包。PROJECT_TASKS是唯一任务状态。

## 持续制作到完整候选

- 当前范围仍为art_required，制作终点I07完整美术候选：地图、47组资产、角色、全部UI状态、反馈、可编辑源及同源检查/运行证据。后续玩法/微信当前不自动启用。
- P08、V08、V09、I08、I09集中在I07之后处理；不得因等待它们停在半成品。V06依制作侧P07等，A-*依V07候选预检，不等V09证书。
- depends_on是制作前序；review_dependencies/release_dependencies是最终审核/放行要求。制作侧done表示完成相应制作验收，不代表独立批准。
- 逐项保存证据、命令/退出码、问题及checkpoint，重算摘要并继续ready任务。不要做完一项或一包就停。
- 从 candidate_n5 起每轮提交 `performance/events.jsonl`、`commands.txt`、原始 `logs/`、`decisions.jsonl`、`summary.json`；阶段字段、起止/耗时、输入输出hash、返修原因与未记录时间的处理按 `art_review/reports/candidate_n4_provisional_20261026/REPORT.md`。缺日志不能声称已缩短整轮耗时。
- 每个变更批次按 `planning/execution/SELF_LEARNING_LOOP.md` 先写可证伪预期，再做原生源修改、同机位验证、主动找反例和批次复盘；将可复用经验提案写入 `planning/execution/LESSONS.md`。经验不得覆盖生效合同或替代独立审核。
- 真正缺资源、设备、构建/运行失败仍须如实处理；可修错误继续修，其他无依赖任务继续。仅在完整候选提交且制作侧自审筛选通过、真实外部资源阻塞且无可做工作、用户暂停或运行限制必须交接时停。

## 最终审核仍独立

- 制作模型不能自签review、attestation或certificate，不能造生产密钥、改独立分数或把未测填pass。
- 保留当前合同/评分与正式release证书验证；无批准可prepare/freeze候选，不能accepted=true或宣称正式放行。
- vNext规则未获审可用于明确标注版本的候选自检，不能偷偷替换生效合同。完整候选后集中审规则、样板、全量包。

## 资产与性能

- 禁AI Image、扩散/图生图/局部生成修补（含概念）。使用Blender真实对象/材质、SVG/Krita原生图层、锁定原Spine和可追溯资源；PNG不是唯一可编辑源。
- 角色唯一来源是有效harness_contract的locked_sources/character_source。复用已有工具与有效成果，不重装/重选引擎/重画角色，不让Forge/MCP平台挡住主线。
- 新内容按候选目录版本化，保留当前冻结载荷/报告；源→导出→构建→canvas采集按hash绑定。**Git 只提交代码、配置、场景结构、必要 `.meta` 与规范/规则；Blender 源、图片、模型、字体、视频、构建及审阅大包保存在本地素材目录并由独立素材备份负责，不能因不入 Git 就删除。**单命令exit0或文件存在不代表画质通过。
- 当前包显示execution_optimization动作；共享组件/会话、定向构建、受影响检查减少重复，正式全量覆盖不减。wrapper只计命令时间，不代表整个模型工期。

## 磁盘与临时文件

- 项目文件夹（含 `.git` 与项目内工具）目标低于 **12 GiB**；10 GiB 开始预警。细则见 `tools/maintenance/STORAGE_POLICY.md`，用 `tools/maintenance/storage_report.py` 按目录统计。
- 每轮开始、每次预计新增 ≥50 MiB 的完整构建/导出/审阅包前、每轮结束，运行 `tools/workflow.py storage --planned-growth-mib <本次预计值> --enforce`；状态会写入 `delivery/workflow/STORAGE_STATUS.json` 并显示在工作包摘要。超 12 GiB 时只暂停新的大产物生成，继续原生源返修、局部验证、归档核对和容量恢复；不得删当前候选或冻结证据凑数。经 `tools/workflow.py run` 发起大命令时必须传同一 `--planned-growth-mib`，预检不通过则不执行命令。
- 保留最近 2 个候选的可复查结果；当前 n5 制作期间为 n4/n5。n3 原生项目不再属于常驻窗口；清退前核对当前构建依赖和引用。项目内 Cocos 编辑器迁出只改变项目文件夹大小，不算释放整块磁盘空间；迁出前后验证构建路径和功能。
- 每个产出批次结束后运行 `python tools/workflow.py clean` 先看报告；确认范围后 `--apply` 只删除旧 demo 构建/缓存、非活动候选的 Blender 备份与 Python 缓存。`tools/n5_build.py` 在写 pin 之后会执行受保护的清理（保留 demo_n5 的 build）。
- `.git/lfs/tmp` **只报告、不由清理器自动删除**：它可能被 Git LFS 写入；没有写入进程且完成远端/引用核对后才能在合适维护窗口处理。2026-10-26 曾累积至 66 GB 导致 ENOSPC；`git lfs prune --verify-remote` 只处理不再需要的 LFS 对象，不能清掉这一临时区。自动审批若拒绝删除，不能换命令绕过。
- 过时但仍属审计链的内容（旧候选、旧源包 ZIP）只报告不删除，由人决定。

## 修改边界

用户已授权本次改变制作排程，把中途独立审核移到最终；原因与旧依赖保留于dependency_history。门禁算法和评分未因此降低。

tools/art_harness.py、tests、合同/rubric仍只在明确P任务中版本化修改；不能改历史包或伪造批准让失败包通过。workflow摘要不是权限隔离、后台执行器或批准器。

## 制作模型自行审核与返修

用户要求低质量先自己改。按PRODUCER_SELF_REVIEW和producer_review_policy执行：样板各卡>=85，完整提交各卡>=90，核心>=3、任维>=2，Q/绑定通过且无未解严重问题。使用真实证据逐维评分，缺证据不填高分；连续三轮无改善换方法，不自动停下来找外部审核。完整自审通过才请求最终评审；保持producer_self_review身份，不能给自己签独立批准。90是制作侧筛选线，独立验收按 art_review/rubric.json。
