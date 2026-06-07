# 游戏常量

# 屏幕尺寸
WIDTH = 640
HEIGHT = 800

# 帧率
FPS = 60

# 颜色定义
COLORS = {
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'CYAN': (0, 255, 255),
    'MAGENTA': (255, 0, 255),
    'YELLOW': (255, 255, 0),
    'ORANGE': (255, 165, 0)
}

# 护盾条透明度，0 为完全透明，255 为完全不透明
SHIELD_ALPHA = 180

# 道具效果数值
# 道具类型使用加分、护盾、维修、射速、弹道这些固定字符串标识；
# 新增道具时需要同步资源加载模块的图片映射和规则系统里的效果逻辑。
REPAIR_HEAL_AMOUNT = 20
SCORE_POWERUP_RATIO = 0.10
SHIELD_POWERUP_AMOUNT = 25
RAPID_FIRE_CD_MULTIPLIER = 0.90
BULLET_STREAM_SPACING = 18
POWERUP_TARGET_SIZE = 36

# 玩家设置
PLAYER_WIDTH = 60
PLAYER_HEIGHT = 72
PLAYER_SPEED = 5
PLAYER_SHOOT_CD = 8  # 帧
PLAYER_IMAGE = "pictures/plane/我方飞机.png"

# 界面设置
RETURN_BUTTON_RECT = (WIDTH - 115, 50, 100, 40)

# 敌人设置
ENEMY_SPEED = 3
ENEMY_SPAWN_INTERVAL = 55
MAX_ENEMIES = 40
MAX_PARTICLES = 120

# 陨石等级数组均按尺寸等级 0 到 4 排列：0 最小，4 最大。
METEORITE_SIZE_SCALE = [0.135, 0.24, 0.36, 0.525, 0.75]
METEORITE_SIZE_HP = [1, 1, 2, 4, 7]
METEORITE_SIZE_SCORE = [60, 50, 80, 120, 240]
METEORITE_SIZE_SPEEDS = [(3.2, 5.5), (2.4, 4.0), (1.7, 3.2), (1.0, 2.0), (0.6, 1.2)]
METEORITE_DAMAGE_RANGES = [(5, 15), (15, 25), (35, 45), (55, 65), (76, 85)]

# 子弹设置
BULLET_SPEED = 10
BULLET_TARGET_WIDTH = 24 * 2
BULLET_TARGET_HEIGHT = 28 * 2

# 关卡设置
MAX_LEVEL = 100
