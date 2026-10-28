---
name: p1-art-director
description: Direct and review the project's P1 autumn-style static map. Use the fixed autumn screenshot for composition, color, and visual review; use Arknights CW map data only for Harness data-structure research.
---

# P1 秋日静态场景美术指导

先读 `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md`，确认主参考 SHA，再比较参考与当前同画幅渲染。本文负责“画面应该是什么”；`.agents/skills/p1-map-environment-art/SKILL.md` 负责 Blender 制作与证据。CW-8/CW-9 参数不得改变 P1 的视觉目标。

1. 先写 P1 中可观察的事实：主物件位置、轮廓、前中远遮挡、材质明暗和颜色角色。截图无法证明的制作技法标为“推断”。角色、UI、字幕不参加环境评分。
2. 以秋日主参考标注台阶/栏杆、石板平台、树、圆筒草池、中景设施和冷色远景；锚点与色彩样本只从 P1 标准读取。
3. 每次评审给出“参考图可见特征 → 当前差异 → 可编辑源里的具体改法 → 同机位通过证据”。不要只写“更自然、再精细、加随机”。每个改法指定影响的物件、材质或灯光参数类别。
4. 按 P1 标准验证组合图中的地面、设施、植被与光色；视觉分数与硬门槛只读该标准。地图数据 Harness 检查按 `knowledge/MAP_PARAMETER_HARNESS_RULES_20261029.md` 执行，不能用 CW fixture 替代画面评分。低于门槛就给出具体源级修复；同一方法连续两轮无改善时换方法并继续，直到评分和硬门槛通过。
5. 对照参考与渲染的全图、50% 缩图、原尺寸局部；固定新场景相机后再做返修对比。保存失败反例。相同方法连续两次无改善就换母版或方法。所有资料只指导本项目原创场景，遵守当前工作单的素材边界。冻结 v05 与哈希证据只读。

当前交付静态地图画面和可编辑 `.blend`；角色/UI/玩法/Cocos/微信不在范围。外部 GitHub skill 只提供技法，不能替换 P1 秋日参考和评分标准。素材使用遵循当前工作单。
