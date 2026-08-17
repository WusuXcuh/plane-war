# 开发文档

面向要改这份代码的人。玩法说明和目录树在 [README](../README.md)。

## 分层原则

代码按 `core → world → ui` 单向依赖分层，`dev` 挂在最外面：

- **core** 不认识具体的界面和实体绘制，只管总控流程、数值和公式。
- **world** 是游戏世界的规则，只依赖 core。
- **ui** 负责画面和交互，可以依赖 core 和 world。
- **dev** 只被 `dev_main.py` 导入，普通入口完全不加载。

一条实际约束：`Game` 对象是所有子系统的共享上下文。子系统构造时都拿到 `game`，通过它访问字体、屏幕、颜色和陨石等级配置。加新子系统时沿用这个模式，不要在模块级别放全局状态。

## 模块职责

### core

| 模块 | 内容 |
| --- | --- |
| `game.py` | `Game` 类。`__init__` 搭建全部子系统；`run()` 是主流程；`game_screen(level)` 和 `endless_mode()` 是两个模式各自的主循环；`handle_events()` 处理游戏内事件；`draw_game()` 定义绘制层级 |
| `constants.py` | 只放纯数值和路径片段，不写逻辑 |
| `rules.py` | 关卡号和难度到具体数值的换算函数 |
| `logs.py` | `log(message)`，带时间戳输出到终端 |
| `utils.py` | `clamp()` |

`Game.run()` 没有正常出口。退出游戏统一走事件处理里的 `sys.exit()`，这样不论玩家在哪一屏按退出键，退出路径都是同一条。

### world

| 模块 | 内容 |
| --- | --- |
| `entities.py` | `Player` / `Enemy`（陨石）/ `Bullet` / `PowerUp`。实体自己管位置、状态和绘制，`update()` 返回 True 表示该被移除 |
| `systems.py` | `GameSystems`，主循环调用的规则门面：射击、生成、更新、碰撞、伤害、道具掉落与结算 |
| `effects.py` | `Effects`，爆炸粒子的创建、推进和绘制。粒子就是字典，列表由主循环持有 |

碰撞检测优先用像素级遮罩：陨石实体每帧在 `prepare_render()` 里预生成旋转后的图像和遮罩，碰撞时直接复用。遮罩不可用或抛异常时回退到圆形距离检测（`_point_near_enemy` / `_player_near_enemy`）。

### ui

| 模块 | 内容 |
| --- | --- |
| `interfaces.py` | `Interfaces`，每个界面是一个自带 `while True` 循环的方法，通过返回值告诉主流程下一步去哪 |
| `renderer.py` | `Renderer`，游戏内绘制：星空背景、两种状态栏、血条护盾条、返回按钮，以及缺贴图时的多边形陨石兜底 |
| `asset_manager.py` | `AssetManager`，字体和图片加载。子弹图片按子目录分组，每 10 秒随机换一组 |
| `widgets.py` | `create_button_surface()` |

界面方法的返回值约定：`level_select_screen()` 返回关卡号，0 表示返回主界面；`start_screen()` 返回关卡号或 `"endless"`；结算界面返回 `"main_menu"`。

### data / dev

- `storage.py` — `HighScoreStore`（最高分读写）+ `LevelProgressStore`（关卡进度存档）。最高分存在 `user_data/high_score.json`；关卡进度存在 `user_data/level_progress.json`，记录已通关关卡集合，用于解锁后续关卡。
- `devtools.py` — `DeveloperTools`。通过 `Game(runtime_tools_factory=...)` 注入，`Game` 只通过 `hasattr` 检查可选接口来调用它，所以普通入口不需要这个模块也能跑。

## 游戏流程

```text
main.py → Game() → Game.run()
                     │
                     ├─ start_screen()  选模式
                     │    └─ level_select_screen()  选关
                     │
                     ├─ 关卡模式：game_screen(level) 循环
                     │    通关 → level_complete_screen() → 下一关
                     │    失败 → game_over_screen() → 回主界面
                     │
                     └─ 无尽模式：endless_mode()
                          结束 → game_over_screen() → 回主界面
```

单帧内的调度顺序（两个模式一致）：

```text
clock.tick(FPS)
update_bullet_group()            切换子弹贴图组
handle_events(dev_context)       退出确认、返回按钮、开发者面板优先拦截
player.update(keys) + 射击
try_spawn_enemy()                生成陨石
update_entities() / update_powerups()
handle_collisions()              子弹打陨石、陨石碎裂、掉落、玩家被撞
handle_powerup_collisions()      玩家拾取道具
draw_game()                      背景→子弹→陨石→道具→爆炸→玩家→状态栏→开发者面板
display.flip()
判断通关 / 生命耗尽
```

## 开发者模式

```bash
python dev_main.py
```

| 快捷键 | 作用 |
| --- | --- |
| F10 | 显示 / 隐藏调试面板（窗口会左右扩展出两块面板） |
| F4 | 在屏幕上方生成一颗陨石 |
| F5 | 在玩家上方生成道具，按固定顺序轮换五种 |
| F6 | 回满血量、护盾和生命上限 |
| F7 | 加 1000 分 |
| F8 | 清空陨石、子弹和粒子 |
| F9 | 切换碰撞调试标记 |

面板上还有滑杆可以实时调射击冷却和陨石速度，以及无敌、陨石暂停两个开关。

开发者模式下 `disables_high_score()` 和 `disables_level_progress()` 都返回 True：最高分和关卡进度都不会写盘，所有关卡都解锁。进入游戏时默认开启无敌。

## 扩展指南

### 加一种道具

1. 图片放进 `assets/pictures/powerup/`，用 ASCII 文件名。
2. 在 `ui/asset_manager.py` 的 `POWERUP_IMAGE_FILES` 里加一条映射。
3. 在 `world/systems.py` 的 `apply_powerup()` 里加效果分支。
4. 在 `world/entities.py` 的 `PowerUp.COLORS_BY_KIND` 和 `LABELS_BY_KIND` 里加兜底颜色和单字标签（图片缺失时用）。
5. 在 `world/systems.py` 的 `drop_powerup()` 里把新类型加进 `powerup_kinds`，并调整权重。

### 加一种敌人

1. 在 `world/entities.py` 里扩展或继承 `Enemy`。
2. 在 `world/systems.py` 的 `try_spawn_enemy()` 里决定何时生成。
3. 如果外观不同，在 `ui/renderer.py` 里加绘制分支。

### 改难度

- 陨石本身的强度（尺寸、血量、速度、伤害）→ `core/constants.py` 的 `METEORITE_SIZE_*` 数组，五个数组的同一个索引代表同一等级。
- 节奏（生成间隔、目标分数、无尽难度推进）→ `core/rules.py`。

## 代码风格

- 类名 PascalCase，函数和变量 snake_case，常量 UPPER_CASE，私有方法前缀下划线。
- 注释和文档字符串用中文，写「为什么这么做」而不是复述代码。
- 导入分三段：标准库、第三方库、本项目模块，段间空一行。项目内一律用绝对导入（`from plane_war.core.constants import ...`）。
