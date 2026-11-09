# SOLUTION DESIGN r02（space_base_minigame / static_map）

## 1. 架构

```
方案 v3.10（几何/玩法） + 升级方案 P0/P1/P2（视觉）
        │
        ├── tools/blender_space_base/build_scene_v5.py   ← 唯一构建入口（程序化，无外贴图）
        │      ├─ 地形/四室/总裁/花园/堤道/船坞/外围
        │      ├─ 材质分层（Noise→ColorRamp，base±8%、roughness 区间）
        │      ├─ 材质内 AO（AmbientOcclusion 节点，距离 1.6 m）
        │      ├─ 全局 Bevel（0.06–0.08，2 段，30°）
        │      ├─ 叶卡植被（3 张自制 alpha 卡：草/灌木/棕榈冠）
        │      └─ 三机位：Camera（主图）/ CameraCore（14 px/m）/ CameraHero（45°）
        │
        └── scene.blend → 三次渲染 → 后处理（分级 + 颗粒）→ 交付集
```

## 2. 交付集（design_r02）

| 产物 | 规格 | 用途 |
|---|---|---|
| `renders/space_base_v05_master.png` | 1680×2478 | 主图 master（1×） |
| `renders/master_raw.png` | 3360×5880 | 2× 超采样归档 |
| `renders/space_base_v05.jpg` | 1680×2478 q88 | 随包图（≤3 MB） |
| `renders/space_base_v05_core.png` | 2072×1876（14 px/m） | 核心区高清片 |
| `renders/space_base_v05_hero.png` | 1920×1080 | 45° 英雄图（宣传/观感） |
| `renders/checks/*.png` | 5 张 | G2/G3/G5/G8 证据 |
| `scene.blend` | 1260 对象 / 17,395 面 | 可编辑源 |

## 3. 关键参数

- 像素：`px = x*7`；`py = (166-y)*5.7344`；图底 70 px 出血
- 相机：正交，`ortho_scale=420`，`location=(120,-44,300)`，`rotation=(0,0,0)`（北朝上）
- 光照：Sun 4.6 / 45° 仰角 / angle 2.2°（半影 0.3–0.6 m）/ `#FFE7C4`
- 天空：渐变（地平 `#B9CBD4` → 天顶 `#F0E6D2`），强度 0.75
- 补光：暖 30000 W（180 m 面）/ 冷 10000 W（150 m 面）
- 反弹：max 6 / diffuse 4 / glossy 4 / transmission 8
- 分级：阴影混灰蓝、高光偏暖、S 曲线、饱和 −6%、0.35% 颗粒

## 4. 可复现

`REPRODUCE.md` 三步：build_scene_v5.py → render_v5_views.py → post_v5.py。
叶卡由 `tools/make_cards_v5.py` 生成（固定 seed），hash 记录在 MANIFEST。
