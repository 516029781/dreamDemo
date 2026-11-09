# 风格 Profile：pilot_simple_map

- profile_id：`pilot_plain_diorama`
- lifecycle：`pilot`
- maturity：`proposed`（单张实证，未经评审/复现以外的确认）
- 参考图：**无**（原创方向；理由见 Brief §2，避免把未校准的"参考→色板"环节混入验证）

## 1. 观察事实（来自本单唯一一次成图）

| 项 | 事实 | 来源 |
|---|---|---|
| 主光 | 单方向阳光，投影统一朝画面右下 | `renders/final.png` |
| 环境光 | 冷灰蓝，强度 0.38，无第二硬影 | build_scene.py `bg` |
| 材质族 | 石（浅灰）/木（暖褐）/金属（深灰）/地（灰褐） | 同上 |
| 明度 | 高调偏中，无近黑近白面积 | TEST-04 统计 |
| 背景 | 地面按相机距离渐入雾色，无远景体块 | build_scene.py `ground aerial haze` |

## 2. 本项目做法（不是通用规则）

1. 相机俯视约 20°，主体占画面下半 60%，上半留雾化地面。
2. 全部几何用 box/cylinder/uv_sphere + Bevel(0.02)，不贴图，保证可重开可复现。
3. 颜色一律 hex→linear 后写入 Principled，避免 sRGB 直填导致的偏亮。
4. 背景用 `Camera Data → Map Range → MixRGB` 做距离雾化；**不要**放远景大块，
   高机位下会变成悬浮暗块（本次已证伪两种做法）。

## 3. 未知 / 不做

- 不知道这套语言在复杂地形、植被、夜间光下是否成立。
- 不做手绘贴图、不做角色、不做 UI。

## 4. 禁止外推

本 Profile 只描述本单这一张图。**不得**被新业务当作默认画风继承，
也不得反向影响 `p1_autumn_static` 的 `STYLE_PROFILE.md`。
