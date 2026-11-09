# 待决问题：space_base_minigame v01

| # | 问题 | 状态 | 决定/依据 |
|---|---|---|---|
| Q1 | 8 px/m、55°、1920×2560 是否冻结 | **resolved** | 用户 2026-11-02「开始吧」接受执行计划默认；改则回 N2/N4 |
| Q2 | A1 角色阴影是否本轮做 | **resolved（external）** | 本轮无角色层；运行时另测，不写成 pass |
| Q3 | W3/W4 真机首帧/内存/降级是否本轮做 | **resolved（external）** | 本机未检测到 DevTools/真机；W1/W2 本机预检，W3/W4 记 external |
| Q4 | 是否接入完整 Cocos/微信游戏工程 | **resolved（out of scope）** | 本轮只做静态图 + 源；运行时另开 |
| Q5 | 是否建满 spec §5 的 62 类 L1/180 L2 | **resolved（scope cut）** | 只保证 7 识别点 + 17 必检；非识别件合并/贴图化，REVIEW 列清单 |
| Q6 | 是否套用 P1 hook/scorecard | **resolved（not applicable）** | 新业务包 `space_base_minigame`；人工自评 + 本业务 checker |
| Q7 | 55° 相机 Euler 与像素公式冲突 | **resolved** | 见 `CONFLICTS_AND_DECISIONS.md` C1：Euler 35°/location (120,568.66,819.2)，以 px/py 公式为准 |
| Q8 | 上南下北与 px=x×8 左右手性冲突 | **resolved** | 见 C2：物理相机 + 导出水平镜像；最终图西左东右、上南下北 |

**blocking conflicts：无。**
