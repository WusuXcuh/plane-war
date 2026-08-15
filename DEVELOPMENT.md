# 项目开发文档

## 📚 模块说明

### 核心模块 (Core)

#### `game.py` - 游戏主控制器

- **职责**: 搭建所有子系统、维护全局状态、调度游戏流程
- **主要类**: `Game`
- **关键方法**:
  - `__init__()` - 初始化所有系统
  - `run()` - 主游戏循环
  - `level_mode()` - 关卡模式流程
  - `endless_mode()` - 无尽模式流程

#### `main.py` - 游戏入口

- 简单的程序入口、创建 Game 对象并运行

#### `dev_main.py` - 开发者入口

- 启用开发者工具和调试面板

---

### 游戏系统 (Systems)

#### `entities.py` - 实体系统

定义游戏中所有可动对象：

- **Player** - 玩家飞机
- **Bullet** - 子弹
- **Enemy** - 敌人（陨石）
- **Powerup** - 道具

**主要方法**:

- `update()` - 更新实体状态
- `draw()` - 绘制实体

#### `systems.py` - 游戏系统

- **GameSystems** - 管理所有游戏逻辑
  - 碰撞检测
  - 敌人/道具生成
  - 玩家射击
  - 伤害处理

#### `renderer.py` - 渲染系统

- **Renderer** - 负责所有绘制工作
  - 绘制背景、星空
  - 绘制玩家、敌人、子弹
  - 绘制UI（血条、得分等）
  - 绘制特殊效果

#### `effects.py` - 特效系统

- **Effects** - 管理所有特效
  - 爆炸特效
  - 粒子效果
  - 伤害数字浮动

#### `interfaces.py` - 界面系统

- **Interfaces** - 管理游戏UI界面
  - `start_screen()` - 开始界面
  - `level_select_screen()` - 关卡选择
  - `game_over_screen()` - 游戏结束
  - `level_complete_screen()` - 关卡完成
  - `confirm_exit_screen()` - 退出确认

#### `rules.py` - 规则系统

- 游戏难度和规则计算
- `calculate_level_spawn_interval()` - 计算敌人生成间隔
- `calculate_score_target()` - 计算关卡得分目标
- `increase_endless_difficulty()` - 提升无尽难度

#### `storage.py` - 存储系统

- **HighScoreStore** - 最高分管理
  - `load()` - 加载最高分
  - `save()` - 保存最高分

---

### 资源管理 (Assets)

#### `assets.py` - 资源管理器

- **AssetManager** - 集中加载和管理游戏资源
  - `load_font()` - 加载字体
  - `load_player_image()` - 加载玩家飞机
  - `load_meteorite_images()` - 加载陨石图片
  - `load_bullet_images()` - 加载子弹图片
  - `load_level_button_template()` - 加载关卡按钮
  - `load_powerup_images()` - 加载道具图片
  - `create_stars()` - 生成星空
  - `create_default_bullet_mask()` - 创建碰撞遮罩

#### `constants.py` - 常量定义

所有游戏参数都在这里定义：

- 窗口大小、FPS
- 玩家属性、敌人属性
- 游戏难度参数
- 颜色定义
- UI元素位置

#### `utils.py` - 工具函数

- `create_button_surface()` - 创建按钮表面
- 几何工具函数
- 通用助手函数

---

### 开发工具 (Dev)

#### `devtools.py` - 开发者工具

- **RuntimeTools** - 运行时调试工具
  - 实时修改游戏参数
  - 快速加分、切换模式
  - 生成指定敌人/道具
  - 帧率显示等

---

## 🔄 游戏流程

    main.py
      ↓
    Game.__init__()  ← 初始化所有系统
      ├─ AssetManager  (资源加载)
      ├─ Renderer      (渲染系统)
      ├─ Effects       (特效系统)
      ├─ GameSystems   (游戏系统)
      └─ Interfaces    (UI界面)
      ↓
    Game.run()  ← 主游戏循环
      ├─ Interfaces.start_screen()  ← 开始界面
      │   ├─ 选择模式
      │   └─ 进入关卡选择或无尽模式
      │
      ├─ Interfaces.level_select_screen()  ← 关卡选择
      │   └─ 选择具体关卡
      │
      └─ Game.level_mode() 或 Game.endless_mode()  ← 游戏循环
          ├─ GameSystems.update()  (更新逻辑)
          ├─ Renderer.draw_*()     (绘制画面)
          └─ 处理事件、碰撞、生成等

---

## 📊 数据流

### 游戏状态管理

    Game
    ├─ player          → Player实体
    ├─ enemies         → Enemy列表
    ├─ bullets         → Bullet列表
    ├─ powerups        → Powerup列表
    ├─ score           → 当前得分
    ├─ level           → 当前关卡
    ├─ high_score      → 最高分
    └─ game_state      → 游戏状态

### 碰撞检测流程

    GameSystems.update()
    ├─ 玩家与敌人碰撞检测
    ├─ 子弹与敌人碰撞检测
    ├─ 玩家与道具碰撞检测
    └─ 触发相应回调函数

---

## 🎮 关卡系统

### 关卡参数

    # 关卡 N 的参数计算
    spawn_interval = calculate_level_spawn_interval(level)  # 敌人生成间隔
    score_target = calculate_score_target(level)            # 过关得分目标
    difficulty = DIFFICULTY_MULTIPLIER * level             # 难度系数

### 无尽模式

- 每隔 `ENDLESS_DIFFICULTY_INCREASE_INTERVAL` 帧提升一次难度
- 难度提升会增加敌人生成速率
- 敌人会变得更强（更快、伤害更高）

---

## 🔌 扩展指南

### 添加新的道具类型

1. 在 `constants.py` 中的 `POWERUP_IMAGE_FILES` 添加映射
2. 在 `pictures/powerup/` 放入对应图片
3. 在 `systems.py` 中的 `apply_powerup()` 添加效果逻辑
4. 在 `entities.py` 的 `Powerup` 类中添加类型检查

### 添加新的敌人类型

1. 在 `entities.py` 中继承或扩展 `Enemy` 类
2. 在 `systems.py` 中的敌人生成函数添加新类型逻辑
3. 在 `renderer.py` 中添加绘制逻辑（如果有不同外观）

### 调整游戏难度

编辑 `constants.py` 中的参数：

- `ENEMY_SPAWN_INTERVAL` - 基础生成间隔
- `METEORITE_SIZE_SPEEDS` - 敌人速度
- `METEORITE_SIZE_HP` - 敌人血量
- `calculate_score_target()` 在 `rules.py` 中的难度系数

---

## 🐛 调试技巧

### 启用开发者模式

    python dev_main.py

### 常用调试工具

- **FPS显示** - 查看帧率
- **碰撞可视化** - 查看碰撞框
- **快速加分** - 跳过关卡
- **生成敌人** - 测试不同难度
- **无敌模式** - 测试特效和交互

### 日志系统

    from game import log
    log("调试信息")  # 输出带时间戳的日志

---

## 📝 代码规范

### 命名规则

- **类名**: PascalCase (例: `GameSystems`)
- **函数名**: snake_case (例: `calculate_level_spawn_interval`)
- **常量**: UPPER_CASE (例: `MAX_ENEMIES`)
- **私有方法**: _snake_case (例: `_make_white_transparent`)

### 注释规范

    def method_name(param):
        """简明的功能描述。
        
        更详细的说明（如果需要）。
        
        Args:
            param: 参数说明
            
        Returns:
            返回值说明
        """

### 导入组织

    # 标准库
    import os
    import random

    # 第三方库
    import pygame

    # 本地模块
    from constants import WIDTH

---

## 📦 依赖关系图

    main.py
      └─ game.py
          ├─ assets.py
          ├─ constants.py
          ├─ entities.py
          ├─ systems.py
          ├─ effects.py
          ├─ renderer.py
          ├─ interfaces.py
          ├─ rules.py
          ├─ storage.py
          ├─ utils.py
          └─ devtools.py (可选)

---

**文档版本**: 1.0  
**更新日期**: 2026年8月14日
