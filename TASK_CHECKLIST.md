# 完整任务索引：候选先完成，最终集中评审

实时状态权威：PROJECT_TASKS.json；当前制作目标I07。下表depends_on是制作依赖，审核/放行另列；不得自行签认外部任务。

本表是任务名称与依赖索引，早期任务名称（如 P03 的“前序批准”）保留历史命名，不恢复中途独立审核阻塞。当前执行规则与开放返修见 `planning/execution/CURRENT_INSTRUCTION_INDEX.md`。

| ID | 任务 | 制作依赖 | 最终审核/放行依赖 | 角色 |
|---|---|---|---|---|
| P00 | 锁定本轮基线和既有证据 |  |  | producer |
| P01 | 统一活动文档与角色来源 | P00 |  | producer |
| P02 | 实现技术/视觉/行为/放行状态及问题迁移 | P01 |  | producer |
| P03 | 实现样板前序批准与扩批依赖 | P02 |  | producer |
| P04 | 实现源/导出/构建/截图绑定与失效 | P02 |  | producer |
| P05 | 将Q01-Q09检查接入审核合同 | P03, P04 |  | producer |
| P06 | 改进audit汇总与CLI/PowerShell状态 | P05 |  | producer |
| P07 | 新增失败夹具并运行规则回归 | P06 |  | producer |
| P08 | 独立审核规则差异与迁移 | P07, I07 |  | independent_reviewer |
| K01 | 正式GameCamera和InspectionCamera分开 | P00 |  | producer |
| K02 | 主角/NPC/世界FX进入世界深度 | K01 |  | producer |
| K03 | 固定脚底锚点与原动画尺度 | K02 |  | producer |
| K04 | 统一输入锁并核对正常/暂停/对白/恢复 | P00 |  | producer |
| K05 | 留言板真实empty/full/reset与FX回收 | P00 |  | producer |
| K06 | 真实viewport与安全区/提示检查 | P00 |  | producer |
| K07 | 导出/运行时面数drawcall统计 | P00 |  | producer |
| K08 | 验证最小自有地图编辑/重导出能力M0 | P00 |  | producer |
| V01 | 重做主树冠与分枝层次 | K01 |  | producer |
| V02 | 石/木/金属在引擎中建立材质分离 | K01 |  | producer |
| V03 | 花坛/灌木/干草与落叶密度 | V01 |  | producer |
| V04 | 锁曝光并校准暖光/冷灰填充 | V02 |  | producer |
| V05 | 纸片/图标/对白UI局部精修 | K01 |  | producer |
| V06 | 冻结同屏样板候选及同源证据（待集中评审） | P07, K01, K02, K03, K04, K05, K06, K07, K08, V01, V02, V03, V04, V05 | P08 | producer |
| V07 | 制作方完成样板预检和问题表 | V06 |  | producer |
| V08 | 独立复核正式样板 | V07, I07, P08 |  | independent_reviewer |
| V09 | 控制器批准样板与批量基线 | V08 |  | controller |
| A-MAP001 | 复核/返修并交付：完整秋庭地图 | V07, A-ENV001, A-ENV002, A-ENV003, A-ENV004, A-ENV005, A-ENV006, A-ENV007, A-ENV008, A-ENV009, A-ENV010, A-ENV011, A-ENV012, A-PROP001, A-PROP002, A-PROP003, A-PROP004, A-PROP005, A-PROP006, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005, A-LOOK001 | V09 | producer |
| A-ENV001 | 复核/返修并交付：石铺地模块 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-ENV002 | 复核/返修并交付：路缘模块 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-ENV003 | 复核/返修并交付：矮墙模块 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-ENV004 | 复核/返修并交付：栏杆模块 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-ENV005 | 复核/返修并交付：边缘装饰台阶 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-ENV006 | 复核/返修并交付：秋日主树 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-ENV007 | 复核/返修并交付：中央环形花坛 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-ENV008 | 复核/返修并交付：侧花坛 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-ENV009 | 复核/返修并交付：灌木A | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-ENV010 | 复核/返修并交付：灌木B | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-ENV011 | 复核/返修并交付：干草簇 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-ENV012 | 复核/返修并交付：落叶簇或贴花 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-PROP001 | 复核/返修并交付：长椅 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-PROP002 | 复核/返修并交付：小廊架 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-PROP003 | 复核/返修并交付：留言板 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-PROP004 | 复核/返修并交付：路灯 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-PROP005 | 复核/返修并交付：导视牌 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-PROP006 | 复核/返修并交付：明信片物件 | V07, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005 | V09 | producer |
| A-MAT001 | 复核/返修并交付：石材材质族 | V07 | V09 | producer |
| A-MAT002 | 复核/返修并交付：木材材质族 | V07 | V09 | producer |
| A-MAT003 | 复核/返修并交付：金属材质族 | V07 | V09 | producer |
| A-MAT004 | 复核/返修并交付：树叶草材质族 | V07 | V09 | producer |
| A-MAT005 | 复核/返修并交付：纸片材质族 | V07 | V09 | producer |
| A-LOOK001 | 复核/返修并交付：相机灯光预览场景 | V07 | V09 | producer |
| A-CHAR001 | 复核/返修并交付：目标主角原Spine资产 | V07 | V09 | producer |
| A-CHAR002 | 复核/返修并交付：主角动作与状态映射 | V07 | V09 | producer |
| A-CHAR003 | 复核/返修并交付：固定NPC形象 | V07 | V09 | producer |
| A-CHAR004 | 复核/返修并交付：主角头像 | V07 | V09 | producer |
| A-CHAR005 | 复核/返修并交付：NPC头像 | V07 | V09 | producer |
| A-UI001 | 复核/返修并交付：标题与进入界面 | V07 | V09 | producer |
| A-UI002 | 复核/返修并交付：加载与失败重试 | V07 | V09 | producer |
| A-UI003 | 复核/返修并交付：任务HUD全部状态 | V07 | V09 | producer |
| A-UI004 | 复核/返修并交付：摇杆全部状态 | V07 | V09 | producer |
| A-UI005 | 复核/返修并交付：交互按钮状态族 | V07 | V09 | producer |
| A-UI006 | 复核/返修并交付：对话组件 | V07 | V09 | producer |
| A-UI007 | 复核/返修并交付：暂停菜单 | V07 | V09 | producer |
| A-UI008 | 复核/返修并交付：完成界面 | V07 | V09 | producer |
| A-UI009 | 复核/返修并交付：拾取与任务提示 | V07 | V09 | producer |
| A-UI010 | 复核/返修并交付：首次操作提示 | V07 | V09 | producer |
| A-UI011 | 复核/返修并交付：旋转与安全区适配 | V07 | V09 | producer |
| A-UI012 | 复核/返修并交付：基础图标族 | V07 | V09 | producer |
| A-UI013 | 复核/返修并交付：UI变量与中文字体 | V07 | V09 | producer |
| A-FX001 | 复核/返修并交付：角色脚底接触阴影 | V07 | V09 | producer |
| A-FX002 | 复核/返修并交付：目标与拾取反馈 | V07 | V09 | producer |
| A-FX003 | 复核/返修并交付：留言板完成变化 | V07 | V09 | producer |
| A-PACK001 | 复核/返修并交付：全美术清单与依赖包 | V07, A-MAP001, A-ENV001, A-ENV002, A-ENV003, A-ENV004, A-ENV005, A-ENV006, A-ENV007, A-ENV008, A-ENV009, A-ENV010, A-ENV011, A-ENV012, A-PROP001, A-PROP002, A-PROP003, A-PROP004, A-PROP005, A-PROP006, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005, A-LOOK001, A-CHAR001, A-CHAR002, A-CHAR003, A-CHAR004, A-CHAR005, A-UI001, A-UI002, A-UI003, A-UI004, A-UI005, A-UI006, A-UI007, A-UI008, A-UI009, A-UI010, A-UI011, A-UI012, A-UI013, A-FX001, A-FX002, A-FX003 | V09 | producer |
| I01 | 全图正式机位/遮挡/站位回归 | A-MAP001, A-CHAR001, A-CHAR002, A-CHAR003, A-FX001 |  | producer |
| I02 | 全UI状态与行为回归 | A-UI001, A-UI002, A-UI003, A-UI004, A-UI005, A-UI006, A-UI007, A-UI008, A-UI009, A-UI010, A-UI011, A-UI012, A-UI013, A-FX002, A-FX003 |  | producer |
| I03 | 最终构建预算与手机代表性检查 | A-MAP001, K07 |  | producer |
| I04 | 原生修改/依赖/导入一致性复查 | A-MAP001, A-ENV001, A-ENV002, A-ENV003, A-ENV004, A-ENV005, A-ENV006, A-ENV007, A-ENV008, A-ENV009, A-ENV010, A-ENV011, A-ENV012, A-PROP001, A-PROP002, A-PROP003, A-PROP004, A-PROP005, A-PROP006, A-MAT001, A-MAT002, A-MAT003, A-MAT004, A-MAT005, A-LOOK001, A-CHAR001, A-CHAR002, A-CHAR003, A-CHAR004, A-CHAR005, A-UI001, A-UI002, A-UI003, A-UI004, A-UI005, A-UI006, A-UI007, A-UI008, A-UI009, A-UI010, A-UI011, A-UI012, A-UI013, A-FX001, A-FX002, A-FX003, A-PACK001 |  | producer |
| I05 | 横竖viewport/字体/安全区全覆盖 | I02 |  | producer |
| I06 | 10条独立缺陷逐项关闭核查 | I01, I02, I03, I04, I05 |  | producer |
| I07 | 冻结完整美术候选包并完成制作侧检查（集中评审入口） | I06, A-PACK001 | P08, V08, V09, I08, I09 | producer |
| I08 | 独立全量美术复审 | I07, P08, V08 |  | independent_reviewer |
| I09 | 控制器正式放行完整美术 | I08, V09 |  | controller |
| G01 | 单一任务/场景状态数据 | I07 | I09 | producer |
| G02 | 正式触控/键盘移动与碰撞 | G01 |  | producer |
| G03 | NPC对话与接受任务 | G01, G02 |  | producer |
| G04 | 三明信片拾取去重与HUD | G03 |  | producer |
| G05 | 留言板提交/完成/继续漫步 | G04 |  | producer |
| G06 | 暂停/静音/重玩全量重置 | G05 |  | producer |
| G07 | 加载失败/重试/微信前后台恢复 | G06 |  | producer |
| G08 | 完整任务闭环与功能独立验收 | G07, W05 |  | independent_reviewer |
| W01 | 微信开发者工具构建与入口 | G07 | G08, I09 | producer |
| W02 | 手机触控/安全区/旋转与生命周期 | W01 |  | producer |
| W03 | 代表性手机性能/包体优化 | W02 |  | producer |
| W04 | 离线完整闭环/重玩复验 | W03 |  | producer |
| W05 | 最终源码/构建/运行指南与发布准备结论 | W04 |  | producer |
| O01 | Forge探索编辑页M1 | I09 |  | producer |
| O02 | MCP包装/高级网页3D预览 | I09 |  | producer |
