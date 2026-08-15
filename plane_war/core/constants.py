# 游戏常量
#
# 这个文件只放“纯数值/路径配置”，不写运行逻辑。
# 这样调难度、调尺寸、改资源路径时，不需要翻主循环或实体代码。

# 主游戏画布尺寸；开发者面板会额外扩展窗口，但游戏内部坐标仍以这里为准。
WIDTH = 640
HEIGHT = 800

# 目标帧率；所有以“帧”为单位的冷却和计时都会受这个值影响。
FPS = 60

# 通用颜色表。界面和渲染模块通过名字取色，避免到处散落 RGB 数值。
COLORS = {
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
    "CYAN": (0, 255, 255),
    "MAGENTA": (255, 0, 255),
    "YELLOW": (255, 255, 0),
    "ORANGE": (255, 165, 0),
}

# 护盾条透明度，0 为完全透明，255 为完全不透明。
SHIELD_ALPHA = 180

# 道具效果数值。
# 道具类型使用加分、护盾、维修、射速、弹道这些固定字符串标识；
# 新增道具时需要同步资源加载模块的图片映射和规则系统里的效果逻辑。
REPAIR_HEAL_AMOUNT = 20
SCORE_POWERUP_RATIO = 0.10
SHIELD_POWERUP_AMOUNT = 25
RAPID_FIRE_CD_MULTIPLIER = 0.90
BULLET_STREAM_SPACING = 18
POWERUP_TARGET_SIZE = 36

# 玩家基础设置。飞机图片会按资源加载模块中的目标宽度等比缩放。
PLAYER_SPEED = 5
PLAYER_SHOOT_CD = 8  # 帧
PLAYER_IMAGE_NAME = "player.png"
PLAYER_TARGET_WIDTH = 60

# 游戏内“返回”按钮的位置，使用主游戏画布坐标，不包含开发者扩展面板。
RETURN_BUTTON_RECT = (WIDTH - 115, 50, 100, 40)

# 陨石/粒子数量上限用于防止后期大量陨石和爆炸粒子导致卡顿。
# 陨石的生成间隔是按关卡算出来的，公式在 rules.py，不在这里配置。
MAX_ENEMIES = 40
MAX_PARTICLES = 120

# 陨石等级数组均按尺寸等级 0 到 4 排列：0 最小，4 最大。
# 同一个索引在尺寸、血量、得分、速度和伤害数组中表示同一种陨石等级。
METEORITE_SIZE_SCALE = [0.135, 0.24, 0.36, 0.525, 0.75]
METEORITE_SIZE_HP = [1, 1, 2, 4, 7]
METEORITE_SIZE_SCORE = [60, 50, 80, 120, 240]
METEORITE_SIZE_SPEEDS = [(3.2, 5.5), (2.4, 4.0), (1.7, 3.2), (1.0, 2.0), (0.6, 1.2)]
METEORITE_DAMAGE_RANGES = [(5, 15), (15, 25), (35, 45), (55, 65), (76, 85)]

# 子弹图片的目标包围尺寸；资源加载时会等比缩放并旋转到游戏需要的方向。
BULLET_SPEED = 10
BULLET_TARGET_WIDTH = 24 * 2
BULLET_TARGET_HEIGHT = 28 * 2

# 关卡模式最大关卡数。主循环会阻止通关后进入不存在的 101 关。
MAX_LEVEL = 100
