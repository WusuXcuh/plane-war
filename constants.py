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
REPAIR_HEAL_AMOUNT = 20
SCORE_POWERUP_AMOUNT = 200
SHIELD_POWERUP_AMOUNT = 25

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

# 子弹设置
BULLET_SPEED = 10
BULLET_TARGET_WIDTH = 24 * 2
BULLET_TARGET_HEIGHT = 28 * 2

# 关卡设置
MAX_LEVEL = 100
