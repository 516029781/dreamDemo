# 待决问题：space_base_minigame v02

| # | 问题 | 状态 | 决定/依据 |
|---|---|---|---|
| Q1 | v02 是否改布局/相机/17 条必检 | resolved | 不改；只加 L2/L3 细节，沿用 v01 spec/相机/验收 |
| Q2 | 真机登录/设备 | **blocked_external（当前）** | DevTools 已安装，CLI open 报“需要重新登录”；需用户扫码登录并在手机上打开预览 QR。未测不写 pass |
| Q3 | W3/W4 | external | 由 runtime_space_base 的首帧/内存/benchmark 日志 + 真机截图提供；本机无设备 |
| Q4 | 细节是否全量 180 L2 | resolved（scope cut） | 只补可见 L2/L3；非识别件仍简化；REVIEW 列清单 |

**blocking conflicts：无（真机是外部依赖，不阻 v02 静态图）。**
