---
name: p1-art-director
description: Direct and review the single static P1 autumn courtyard image against the locked t084s.jpg reference. Use for shot analysis, visual targets, composition and color decisions, and specific art corrections before or during Blender production.
---

# P1 静态场景美术指导

先读 `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md`，实际查看 `reference/_raw_screenshots/P1/t084s.jpg` 与当前同画幅渲染。本文负责“画面应该是什么”；`.agents/skills/p1-map-environment-art/SKILL.md` 负责 Blender 制作与证据。

1. 先写可观察的画面事实：主物件位置、轮廓、前中远遮挡、材质明暗和颜色角色。单张截图无法证明的原制作技法标为“推断”。角色、UI、字幕不参加环境评分。
2. 在固定相机上先检查主视觉锚点：左树、前景台阶与栏杆、暖石板平台、中景设施、右侧圆筒草池、冷色远景。任一缺失先改构图/结构，再制作细节。
3. 每次评审给出“参考图可见特征 → 当前差异 → 可编辑源里的具体改法 → 同机位通过证据”。不要只写“更自然、再精细、加随机”。每个改法指定影响的物件、材质或灯光参数类别。
4. 先检查标准中的**地板、树、草、全画面光色四项组合试图门槛**；任一项失败先返修，不常规扩批，也不找用户中途审核。原方法与替代方法各两轮仍失败时，按总方案完成最好版本并标 `quality_below_target`。组合关通过后再按六维量表评最终静帧；≥90 指可观察的加权视觉特征达成度，不是原图像素相似率，不通过改分数结束。
5. 对照原图和渲染的全图、50% 缩图、原尺寸局部。P1 原相机未知，灰模时按六锚点调整新相机，确认后锁定；返修前后必须同相机。保存失败反例。相同方法连续两次无改善就换母版或方法。所有资料只指导本项目原创场景，禁止 AI Image/扩散生图。冻结 n5 候选只读。

当前仅交静态地图画面和可编辑 `.blend`；不要把旧游戏、UI、微信验收带入本阶段。外部 GitHub skill 只提供技法，不能替换固定主参考和本项目评分标准。
