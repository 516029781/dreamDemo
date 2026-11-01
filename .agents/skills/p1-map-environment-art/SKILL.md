---
name: p1-map-environment-art
description: Create and critique the project's P1 autumn-style static map image and editable Blender scene. Follow the fixed P1 screenshot, current zero-vegetation adaptation, and project-local quality gate.
---

# P1 秋日静态地图环境美术

制作前按 `planning/art/STATIC_MAP_WORKFLOW_20261028.md` 执行 G0–G3，并读取 `planning/art/P1_T084_ART_DIRECTION_STANDARD_20261028.md`。唯一整图视觉参考是 `t084s.jpg`；CW-8/CW-9 只用于 Harness 数据结构研究。本阶段只交静态图和可编辑 Blender 源。

## 强制画面约束

- 整图完全无植被：不得有树、叶、草、花、灌木、苔藓、藤蔓、盆栽、花池、裸土或植物纹样/贴图。
- 左侧原树区用有用途、可读开合面和底座的高型维护设备组替代；右侧原草池用封闭式圆筒过滤/储液设备替代。设备有接口、承托和落地阴影，避免随机盒子。
- P1 的植物只记录为参考事实。评分评价无植被改编画面的完成质量，不评价或宣称植物复刻度。

## 制作和返修

1. 校验固定参考 SHA、候选新目录、活动状态和冻结证据。
2. 先做灰模：场地层次、石板和台阶、栏杆、替代设备轮廓、支撑连接、遮挡与镜头；确认后锁定相机。
3. 组合测试地面、结构、光色与背景。每批只试一个主假设，同一方法两轮无改善后更换几何/设备模块/材质/布光方法。
4. 完成正式静帧后，制作模型亲自查看 SHA 绑定图片并自评六维。总分低于 85、任一维低于 3、组合项/硬门槛失败时，按根因修改 Blender 源、同机位重渲、更新评分与 SHA，循环至达标。
5. 隔离复制 `.blend` 并重开复现；运行 v3 项目 gate。无需其他模型独立终审；gate 机械核验不具备视觉判断能力。

每批记录前后图、对象/参数、相机参数、命令/退出码、耗时、源/图 SHA、失败反例和返修决定。冻结候选不可覆盖。按工作流保存必需文件；mask、DOF A/B 和细节板按诊断需要保存。
