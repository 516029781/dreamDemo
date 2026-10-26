# n5 微信小游戏包体实测（隔离构建）

日期：2026-10-26。输入为 `demo_n5` 的独立副本，位于 `.tooling/wechat_probe_n5_20261026T152015Z`。未修改 n5 原工程、固定的 Web 构建及审阅证据。地图 GLB、字体和启动脚本与原工程的 SHA-256 一致。

## 实测结果

- Cocos Creator 3.8.8，`platform=wechatgame`，`debug=false`，横屏；测试 AppID 仅用于本地包体探针。
- 输出：`.tooling/wechat_probe_n5_20261026T152015Z/build/wechatgame`，336 个文件，共 **188,475,921 B = 179.74 MiB**。
- `game.json` 无 `subpackages`；没有 `remote` 目录。审计结果：**主包 179.74 MiB、分包 0、远程资源 0**。按 4 MiB 主包门槛，`audit_wechat_package.py` 返回 2（未通过）。逐文件结果见 [JSON](WECHAT_N5_PACKAGE_AUDIT.json)。
- `assets/resources` 为 **174.44 MiB**；`cocos-js` 为 **3.54 MiB**；`assets/main` 为 **0.92 MiB**；`assets/internal` 为 **0.65 MiB**。即便把 `assets/resources` 全部移出本地，余下仍约 **5.30 MiB**。
- 最显著的源资源：地图 GLB **88.7 MiB**，两套完整中文 TTF 合计 **40.9 MiB**。构建中多个单独 `.bin` 为 10–33 MiB，需要进一步按 UUID 对应回模型，不能单凭扩展名认定内容。
- Cocos 日志出现 `build Task (wechatgame) Finished`，但进程返回 36，退出后另有 `window.json` recovery 解析报错。因此本报告只证明产出了可统计的目录；**尚未通过微信开发者工具预览、上传或真机运行**。
- 本次构建的完整日志为 [WECHAT_N5_BUILD.log](WECHAT_N5_BUILD.log)，配置快照为 [WECHAT_N5_BUILD_CONFIG.json](WECHAT_N5_BUILD_CONFIG.json)。隔离输出仍在 `.tooling/wechat_probe_n5_20261026T152015Z`：清理该目录的操作被自动审批以 `blocked by policy` 拒绝，未改用其他方式删除。

## 下一轮顺序与验收

1. **先建立发布包边界**：代码与启动必需内容留主包；地图、角色、UI 图、音频按加载时机拆到微信分包或远程 Asset Bundle。脚本不可作为远程资源下载。把 `game.json` 分包配置及远程目录纳入审计，目标主包 ≤4 MiB；内部预留余量，宜低于 3.5 MiB。
2. **缩减首场景必需内容**：把 88.7 MiB 地图拆成可见区模块与远景替身，按区加载；保留原生 `.blend`，只优化发布导出。逐模块记录导出字节、三角形数、手机帧率和与当前画面的差异，画质不合格则回退。
3. **处理字体**：从实际对白、UI 文案与常用兜底字符生成字体子集；动态文本补齐字符覆盖测试。不得直接删除字体后用系统字体替代而不做视觉复核。
4. **瘦主包引擎**：使用 Cocos 功能裁剪和微信小游戏的引擎原生代码分包选项；每次只改一组配置并重建，确认启动和功能回归。当前移走全部 `resources` 后仍约 5.30 MiB，仅移动资源不能过主包门槛。
5. **正式门禁**：每次微信构建运行 `tools/maintenance/audit_wechat_package.py <wechatgame目录> --output <报告.json>`，检查主包/分包/远程资源体积、最大文件清单；再用微信开发者工具核验平台真实包体，并做真机首启、地图加载、内存与帧率测试。超过门槛不得声称“可发布”。

当前 179.74 MiB 是**微信构建的未压缩目录字节数**，并非平台最终上传计费值。它已经足以说明当前配置把大资源全部放进主包；微信开发者工具仍是最终包体判定。Git 历史、Blender 源和审核日志不会自动进入游戏包，工作区 12 GiB 目标与小游戏发布包预算应分别管理。
