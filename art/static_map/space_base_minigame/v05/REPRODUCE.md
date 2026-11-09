# REPRODUCE — space_base_minigame v05（r02 / 视觉升级）

前置：Blender 5.2.3；Python 3.13 + numpy + Pillow。
贴图为相对路径 `//assets/*.png`（3 张自制 alpha 卡），可整目录搬移后重开。

1. 生成叶卡（固定 seed，可重复）
   `python tools/make_cards_v5.py` → `art/static_map/space_base_minigame/v05/assets/card_{grass,bush,palm}.png`

2. 构建场景（唯一构建入口，程序化，无外贴图）
   `blender -b --factory-startup --python tools/blender_space_base/build_scene_v5.py -- --out art/static_map/space_base_minigame/v05/scene.blend`

3. 渲染三视图
   `blender -b art/.../v05/scene.blend --python tools/blender_space_base/render_v5_views.py -- <v05>/renders`
   → `master_raw.png` 3360×5880 / `core_raw.png` 2072×1876 / `hero_raw.png` 1920×1080

4. 后处理 + 机械证据
   `python tools/space_base_v5_post.py`
   → master 1680×2478（7 px/m，纵向 5.7344，70 px 出血）、jpg、5 张 checks、evidence JSON

5. 场景证据
   `blender -b <v05>/scene.blend --python tools/blender_space_base/evidence_v5.py -- <run>/evidence`

6. 隔离复现
   复制 scene.blend + assets 到 `runs/20261103-1010/repro/`，重开渲染 420×735@12spp，与 master_raw 缩图比 RMS（阈值 8）

7. 机械门禁
   `python tools/space_base_check_v3.py --request knowledge/active/20261103-space-base-v5 --candidate art/static_map/space_base_minigame/v05 --run 20261103-1010`

关键常量：`px=x*7`；`py=(166−y)*5.7344`；ortho_scale=420；北朝上；`x=120` 实墙；撤离 `(221,−214)`。
