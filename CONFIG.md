# 飞机大战项目配置

## 项目信息

NAME = "飞机大战"  
VERSION = "1.0"  
AUTHOR = "Game Developer"  
LICENSE = "Personal Project"  
DESCRIPTION = "一个使用 Python Pygame 开发的飞机大战游戏"

## Python 要求

PYTHON_MIN_VERSION = "3.8"  
PYTHON_TESTED_VERSION = "3.11"

## 依赖列表

DEPENDENCIES = {
    "pygame": ">=2.0.0",
}

## 文件结构说明

STRUCTURE = {
    "根目录文件": [
        "main.py              # 游戏主入口",
        "dev_main.py          # 开发者模式入口",
        "constants.py         # 常量和配置参数",
    ],

    "游戏系统": [
        "game.py              # 游戏主控制器",
        "entities.py          # 游戏实体定义",
        "systems.py           # 游戏系统（碰撞、生成等）",
        "renderer.py          # 渲染系统",
        "effects.py           # 特效系统",
        "interfaces.py        # UI界面系统",
        "rules.py             # 游戏规则和难度",
        "storage.py           # 数据存储（最高分）",
    ],

    "工具模块": [
        "assets.py            # 资源加载管理",
        "utils.py             # 工具函数",
        "devtools.py          # 开发者工具",
    ],

    "资源目录": [
        "pictures/            # 游戏图片资源",
        "user_data/           # 用户数据存储",
    ],
}

## 游戏配置参数

GAME_CONFIG = {
    "窗口": {
        "宽": 800,
        "高": 600,
        "标题": "飞机大战",
        "FPS": 60,
    },

    "玩家": {
        "宽": 60,
        "高": 72,
        "速度": 5,
        "射击冷却": 8,
        "初始血量": 3,
    },

    "敌人": {
        "最大数量": 40,
        "生成间隔": 55,
        "移动速度": "随机 0.6-5.5",
    },

    "特效": {
        "最大粒子数": 120,
        "爆炸类型": "2种 (小/大陨石)",
    },

    "关卡": {
        "总数": 100,
        "模式": ["关卡模式", "无尽模式"],
        "难度提升": "逐级递增",
    },
}

## 快速启动命令

### 1. 安装依赖

    pip install pygame

### 2. 运行游戏

    # 普通模式
    python main.py

    # 开发者模式（包含调试工具）
    python dev_main.py

### 3. 代码检查（可选）

    # 使用 pylint 检查代码
    pylint *.py

    # 使用 black 格式化代码
    black *.py

## 重要文件清单

### 资源文件路径

    pictures/
    ├── plane/               # 飞机图片
    ├── bullets/             # 子弹图片（7组）
    ├── meteorite/           # 陨石图片
    ├── powerup/             # 道具图片（5种）
    └── level button/        # 关卡按钮底图

    user_data/
    └── high_scores.json     # 最高分保存文件

### 生成的文件

    __pycache__/            # Python缓存（自动生成）
    .git/                   # Git版本控制

## 关键配置参数位置

| 参数 | 文件 | 行号 |
| --- | --- | --- |
| 窗口大小 | constants.py | 1-5 |
| 玩家属性 | constants.py | 38-44 |
| 敌人参数 | constants.py | 48-52 |
| 陨石等级 | constants.py | 55-60 |
| 游戏难度 | rules.py | 见函数定义 |
| 字体大小 | game.py | 82-84 |
| UI位置 | interfaces.py | 各界面方法 |

## 扩展配置

### 添加新道具

1. 在 `pictures/powerup/` 添加图片
2. 在 `assets.py` 的 `POWERUP_IMAGE_FILES` 添加映射
3. 在 `systems.py` 的 `apply_powerup()` 添加逻辑

### 调整难度

编辑 `constants.py`:

- `ENEMY_SPAWN_INTERVAL` - 敌人生成速率
- `METEORITE_SIZE_SPEEDS` - 移动速度
- `METEORITE_SIZE_HP` - 血量

### 修改关卡数

编辑 `constants.py`:

- `MAX_LEVEL = 100` 改成其他数值

## 项目统计

| 项目 | 数值 |
| --- | --- |
| Python 文件 | 14个 |
| 代码行数 | ~3000+ |
| 类定义 | 20+ |
| 函数/方法 | 150+ |
| 关卡数 | 100 |
| 道具类型 | 5 |
| 敌人等级 | 5 |

## 性能指标

| 指标 | 目标值 |
| --- | --- |
| FPS (目标帧率) | 60 |
| 启动时间 | <2秒 |
| 关卡加载 | <0.5秒 |
| 内存占用 | <100MB |

## 问题排查

### 问题：游戏卡顿

**解决**: 在 `constants.py` 中调整 `MAX_ENEMIES` 和 `MAX_PARTICLES`

### 问题：找不到资源文件

**解决**: 确保 `pictures/` 目录在游戏文件同级目录

### 问题：无法加载字体

**解决**: 程序会自动回退到默认字体，不影响游戏运行

### 问题：最高分未保存

**解决**: 确保 `user_data/` 目录可写，检查 `storage.py`

## 版本控制

### Git 配置

- `.gitignore` 包含 Python 缓存和用户数据
- 提交时排除 `__pycache__/` 和 `.pyc` 文件

### 更新日志

- v1.0 (2026-08-14) - 初始版本发布
  - 完成100个关卡
  - 实现关卡选择界面
  - 添加道具系统
  - 优化启动速度

---

**配置文件版本**: 1.0  
**更新日期**: 2026年8月14日
