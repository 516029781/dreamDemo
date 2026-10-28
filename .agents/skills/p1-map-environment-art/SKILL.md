---
name: p1-map-environment-art
description: Create and critique one static P1 autumn map image and its editable Blender scene using t084s.jpg as the fixed visual target. Use for composition, models, materials, vegetation, lighting, and same-camera art review; not for gameplay, UI, Cocos, or WeChat implementation.
---

# P1 地图环境美术

先按项目根目录 `planning/art/STATIC_MAP_WORKFLOW_20261028.md` 执行 S0–S5，再用 `planning/art/P1_MAP_ART_ONLY_REVIEW_20261028.md` 查具体画面差距；外部 skill、Blender 插件和素材的试用边界见 `planning/art/STATIC_MAP_ART_SKILLS_AND_TOOLS_20261028.md`。固定整图参考是 `reference/_raw_screenshots/P1/t084s.jpg`。当前只交静态地图画面和可编辑 Blender 源。只在用户重新开启完整游戏阶段后，才把游戏行为、UI 和微信性能加入交付范围。若阶段说明被用户更新，以最新用户要求为准。

## 工作方式

1. **先看图。** 实际打开 t084 原图和候选的无 UI 固定机位图，记录四到六个有名的画面区域：近景台阶、平台/石板、花池草、树、设施、远景。对每区写出参考中的形体、尺度、表面、光线和候选的具体缺口。角色仅作比例尺；不拿旧 t015/t090 代替整画面目标。
2. **先改空间。** 用灰模反推新相机，确定高差、阶梯、栏杆、平台厚度、主体设施和近中远遮挡。灰模与早期色块/灯光图通过后才锁相机；方块和简单球体只作灰模。记录位置、焦距/FOV、目标点、输出尺寸；布局没过关时不大量生成树叶或铺地细节。
3. **物件有结构。** 每类主物件至少能读出主体、接合/边缘和使用痕迹。石板用同一尺寸家族加有限边板/破损板；树先做枝干层级再布叶；枯草先做根密顶疏的簇，再按花池成片种植。以可见轮廓和局部画面验证，不用增加随机实例数或三角面数代替造型。
4. **材质能进入最终静帧。** Blender 内使用可编辑节点、UV、手工或程序化贴图；先在固定机位验证石/金属/木/土/叶的实际原尺寸像素。本阶段不要求 GLB/Cocos 导出。将来若要导入引擎，再检查 base color、normal、roughness/AO 等贴图；旧 `courtyard_lib.py` 的 `_flat_material` 会简化多数程序材质，不能拿 Blender 静帧冒充引擎效果。
5. **同机位返修。** 每次只处理一个主因，保留修改前后全图和相应局部图，写参数、原生源路径、命令、退出码、耗时和 SHA。主图不合格继续改源；连续数轮无改善就换建模/材质方法，不通过改评分结束。冻结的候选和哈希证据不覆盖。
6. **独立看图判断。** 先在同镜头组合试图中逐项验证地板、树、草、整体光色；失败就内部返修，不等用户批准。按总方案止损后仍低于目标，也须交完整可编辑静帧并标 `quality_below_target`。全图出现方块拼装、尖片、大片同色平面即记返修；组合关过后再按六维目标 ≥90 且各项 ≥3 评最终静帧。分数是制作自评，不是独立批准。

交付一张最终静帧、`.blend`、源贴图/来源与许可记录、固定机位灰模/材质/最终图、石板/树/草/设施局部图和修改记录。静帧只称“地图美术预览”。项目禁止 AI Image、扩散生图及图生图修补，包括概念图；用可编辑原生素材。
