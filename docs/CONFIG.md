# 配置速查

改数值的时候对着这份表找位置。玩法说明看 [README](../README.md)，模块职责看 [DEVELOPMENT](DEVELOPMENT.md)。

## 项目信息

| 项 | 值 |
| --- | --- |
| 名称 | 飞机大战 |
| 依赖 | pygame >= 2.0.0 |
| Python | 最低 3.8，开发环境 3.11 |
| 入口 | `main.py` / `dev_main.py` |

## constants.py — 写死的数值

位置：[plane_war/core/constants.py](../plane_war/core/constants.py)

### 窗口

| 常量 | 值 | 说明 |
| --- | --- | --- |
| `WIDTH` / `HEIGHT` | 640 / 800 | 游戏画布尺寸。开发者面板会额外扩展窗口，但游戏内坐标仍以这里为准 |
| `FPS` | 60 | 所有以「帧」为单位的冷却和计时都受它影响 |
| `COLORS` | 9 色 | 界面和渲染按名字取色 |
| `RETURN_BUTTON_RECT` | — | 游戏内返回按钮的位置 |

### 玩家

| 常量 | 值 | 说明 |
| --- | --- | --- |
| `PLAYER_SPEED` | 5 | 每帧移动像素 |
| `PLAYER_SHOOT_CD` | 8 | 射击冷却帧数 |
| `PLAYER_IMAGE_NAME` | `player.png` | 位于 `assets/pictures/plane/` |
| `PLAYER_TARGET_WIDTH` | 60 | 飞机图片按这个宽度等比缩放 |

初始生命 3 条，生命上限 `100 - 5 × ((关卡 - 1) // 10)`，护盾上限是生命上限的两倍 —— 这三个值在 `world/entities.py` 的 `Player.__init__` 里。

### 陨石

五个数组按尺寸等级 0~4 排列，同一个索引在五个数组中表示同一等级：

| 常量 | 含义 |
| --- | --- |
| `METEORITE_SIZE_SCALE` | 图片缩放比例 |
| `METEORITE_SIZE_HP` | 需要几发子弹打掉 |
| `METEORITE_SIZE_SCORE` | 击碎得分 |
| `METEORITE_SIZE_SPEEDS` | 下落速度范围 |
| `METEORITE_DAMAGE_RANGES` | 撞到玩家的伤害范围 |

生成时的等级概率写在 `world/entities.py` 的 `Enemy.__init__`（小陨石更常见）。

### 数量上限

| 常量 | 值 | 说明 |
| --- | --- | --- |
| `MAX_ENEMIES` | 40 | 同屏陨石上限，卡顿时优先调它 |
| `MAX_PARTICLES` | 120 | 爆炸粒子上限 |

### 道具与子弹

| 常量 | 值 | 说明 |
| --- | --- | --- |
| `REPAIR_HEAL_AMOUNT` | 20 | 治疗回血量 |
| `SCORE_POWERUP_RATIO` | 0.10 | 加分道具按当前分数的比例加分 |
| `SHIELD_POWERUP_AMOUNT` | 25 | 每次拾取增加的护盾值 |
| `RAPID_FIRE_CD_MULTIPLIER` | 0.90 | 射速道具对冷却的乘数，可叠加 |
| `BULLET_STREAM_SPACING` | 18 | 多弹道之间的横向间距 |
| `POWERUP_TARGET_SIZE` | 36 | 道具图标统一缩放尺寸 |
| `BULLET_SPEED` | 10 | 子弹每帧上移像素 |
| `BULLET_TARGET_WIDTH/HEIGHT` | 48 / 56 | 子弹图片的目标包围盒 |
| `SHIELD_ALPHA` | 180 | 护盾条透明度 |
| `MAX_LEVEL` | 100 | 关卡总数，同时决定关卡选择界面的页数 |

## rules.py — 算出来的规则

位置：[plane_war/core/rules.py](../plane_war/core/rules.py)

| 常量 / 函数 | 说明 |
| --- | --- |
| `BASE_LEVEL_SPAWN_INTERVAL` = 55 | 第 1 关的陨石生成间隔（帧） |
| `MIN_LEVEL_SPAWN_INTERVAL` = 10 | 关卡模式生成间隔下限 |
| `calculate_level_spawn_interval(level)` | 每 10 关生成间隔减 5 帧 |
| `calculate_score_target(level)` | `1000 + (level - 1) × 1000` |
| `ENDLESS_BASE_DIFFICULTY` = 90 | 无尽模式的起始难度基准 |
| `ENDLESS_DIFFICULTY_INCREASE_INTERVAL` = 600 | 每 600 帧（10 秒）提升一次难度 |
| `ENDLESS_SPAWN_INTERVAL_STEP` = 3 | 每次提难度，生成间隔减少的帧数 |
| `MIN_ENDLESS_SPAWN_INTERVAL` = 15 | 无尽模式生成间隔下限 |
| `HIGH_SCORE_CHECKPOINT_STEP` = 1000 | 最高分每涨 1000 分才写一次盘 |

想让游戏更难，改这里比改 `constants.py` 更有效 —— 生成间隔直接决定压力。

## 资源路径

所有路径都从 [plane_war/paths.py](../plane_war/paths.py) 派生，模块内不再自己拼项目根目录。

```text
assets/pictures/
├── plane/player.png
├── bullets/1..7/*.png       每个子目录是一个轮换组，每 10 秒随机换组
├── meteorite/meteorite_*.png 随机分配给新生成的陨石
├── powerup/*.png            文件名与道具标识的映射在 ui/asset_manager.py
└── level_button/button.png  关卡选择界面 100 个按钮共用

user_data/README.md          无尽模式最高分
```

文件名请保持 ASCII，中文名和空格在跨平台和某些工具链下会出问题。

## 字体

`ui/asset_manager.py` 的 `load_font()` 依次尝试 simhei、simsun、微软雅黑，都失败就退回 pygame 默认字体，再失败用 `DummyFont`（渲染透明表面，不崩溃但看不到字）。这套路径是 Windows 优先的，换到 Linux/macOS 需要在列表里补本地中文字体路径。

## 排查

| 现象 | 处理 |
| --- | --- |
| 卡顿 | 调低 `MAX_ENEMIES` 和 `MAX_PARTICLES` |
| 找不到资源 | 确认在项目根目录运行，且 `assets/pictures/` 完整 |
| 中文显示成方块 | 见上面「字体」一节，补字体路径 |
| 最高分没保存 | 确认 `user_data/` 可写；开发者模式下本来就不写盘 |
| `ModuleNotFoundError: plane_war` | 必须在项目根目录执行 `python main.py` |
