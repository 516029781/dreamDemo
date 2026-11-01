# P1 绘制 Playbook（本项目如何画）

- business_id：`p1_autumn_static`
- 版本：r02（2026-11-02，按“整图无植被”政策整理）
- 说明：只记录**本项目可复现的做法**，不声称还原原游戏内部流程。
- 状态：`lifecycle`（draft/active/superseded）+ `maturity`（proposed/observed/reproduced/reusable）

## 1. 当前有效方法（无植被设备化）

| recipe_id | 目标 | 方法 | 涉及对象/参数 | 证据 | maturity | lifecycle |
|---|---|---|---|---|---|---|
| R-NOVEG-01 | 清除全部植物 | 先枚举植物对象、集合、GN 实例、材质槽与图像纹理引用，再删除；删除后全图四角/顶部/设备内部目视复查；关键词搜索不作为唯一证据 | `v25` 中 `P1 HP canopy *`、草簇卡、`T01 / shore grass` 实例、`assets/handpainted/*` | 工作单 P1-A；REVIEW §13–§15 | observed | active |
| R-REPLACE-01 | 左树区改维护柜组 | 2–3 个不同宽高模块，连续底座、检修门、少量格栅/接口；禁止堆成树形/方盒墙 | `P1-WORKORDER` P1-B | 工作单 | proposed | active |
| R-REPLACE-02 | 右草池改封闭圆筒 | 连续筒壁 + 顶盖 + 支撑环 + 少量接口管路；内部/顶部无土无植物 | 同上 | 工作单 | proposed | active |
| R-LIGHT-01 | 明暗与接触影 | 固定几何后只调 sun/World/AO；sun 为 QUATERNION 时必须写 `rotation_quaternion`（euler 无效） | `preflight/r1_light.py` | REVIEW §12 R1 | observed | active |
| R-PAVE-01 | 石板家族 | 同尺寸家族 + 有限边板/修补板；凹缝/倒角为真形体；磨损按边缘与动线 | 68 板 5 色调区块 + 3 修补板 | REVIEW §12 R4 | observed | active |
| R-FAR-01 | 冷软远景 | 合成器雾 0.42→0.33 + 近档剪影；过浓冲白 | `r5_equip.py` | REVIEW §12 R6 | observed | active |
| R-DIAG-01 | 根因定位 | 对象→材质→灯光→World→雾→合成器→色彩管理逐层 A/B；相机射线定位法（view_frame + `scene.ray_cast`） | `r16_binsearch.py`、射线脚本 | REVIEW §13–§14 | observed | active |
| R-EVID-02 | 证据保护 | 清理前由 manifest 生成保留集、核对 SHA；批量删除前 dry-run 并核对保留集生效 | REVIEW §15 事故 | observed | active |

## 2. 被取代的中间方向（历史，不可再作为目标）

| recipe_id | 内容 | 状态 | 取代依据 |
|---|---|---|---|
| R-CROWN-01 | 手绘整冠大卡 + 辅助卡（3.6m，程序化云朵贴图） | **superseded for P1**（2026-11-01T23:23） | 整图无植被政策 |
| R-GRASS-01 | 草簇卡替换细丝草、密度×2、景深三级压暗 | **superseded for P1** | 同上 |

这两条保留为方法记录：若未来某业务 brief 明确需要手绘植被，可作参考，但**不得**直接搬回 P1。

## 3. 方法边界

- 全部为单一候选内观察，未跨业务复测；不得标 `reusable`。
- 无绑定当前图 SHA 的评审，不得称“成功配方”。
- 参考图不可推断原游戏实现；本 Playbook 只是本项目做法。

## 4. 与测试的对应

| 目标 | recipe | test |
|---|---|---|
| 无植被 | R-NOVEG-01 | TEST-P1-NOVEG |
| 设备替代 | R-REPLACE-01/02 | TEST-P1-REPLACE |
| 明暗 | R-LIGHT-01 | TEST-P1-VALUE |
| 石板 | R-PAVE-01 | TEST-P1-REPLACE（局部）/ 评分 |
| 远景 | R-FAR-01 | 评分 + 组合检查 background |
