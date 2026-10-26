# 鼠鼠项目

当前项目入口：[START_HERE.md](START_HERE.md)。任务清单：[TASK_CHECKLIST.md](TASK_CHECKLIST.md)，实时状态：[PROJECT_TASKS.json](PROJECT_TASKS.json)。连续执行：[EXECUTION_PROTOCOL.md](EXECUTION_PROTOCOL.md)。

当前目标是P1风格庭院美术返修，后续完成微信小游戏。根目录game.js/js是保留的旧飞机示例；当前3D工程在demo/。不要从下列历史示例说明启动新项目或以它作为已完成游戏。

---

## 历史示例说明（仅留档）

# 示例游戏

示例相关说明查阅[新手教程](https://developers.weixin.qq.com/minigame/dev/guide/develop/start.html)

## 源码目录介绍

```
├── audio                                      // 音频资源
├── images                                     // 图片资源
├── js
│   ├── base
│   │   ├── animatoin.js                       // 帧动画的简易实现
│   │   ├── pool.js                            // 对象池的简易实现
│   │   └── sprite.js                          // 游戏基本元素精灵类
│   ├── libs
│   │   └── tinyemitter.js                     // 事件监听和触发
│   ├── npc
│   │   └── enemy.js                           // 敌机类
│   ├── player
│   │   ├── bullet.js                          // 子弹类
│   │   └── index.js                           // 玩家类
│   ├── runtime
│   │   ├── background.js                      // 背景类
│   │   ├── gameinfo.js                        // 用于展示分数和结算界面
│   │   └── music.js                           // 全局音效管理器
│   ├── databus.js                             // 管控游戏状态
│   ├── main.js                                // 游戏入口主函数
│   └── render.js                              // 基础渲染信息
├── .eslintrc.js                               // 代码规范
├── game.js                                    // 游戏逻辑主入口
├── game.json                                  // 游戏运行时配置
├── project.config.json                        // 项目配置
└── project.private.config.json                // 项目个人配置
```
