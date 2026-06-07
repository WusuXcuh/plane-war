# 游戏实体类

import pygame
import random
import os
import math
from constants import PLAYER_SPEED, PLAYER_SHOOT_CD, BULLET_SPEED, BULLET_TARGET_WIDTH, BULLET_TARGET_HEIGHT, COLORS, HEIGHT, POWERUP_TARGET_SIZE
from utils import clamp

class Player:
    """玩家实体：维护位置、生命、护盾、射击冷却和临时强化状态。"""
    SPEED = PLAYER_SPEED
    SHOOT_CD = PLAYER_SHOOT_CD   # 帧（原14帧，加快发射频率）
    
    def __init__(self, game):
        self.game = game
        level = self.game.current_level
        # 从游戏对象获取飞机图片的实际大小
        self.W, self.H = game.PLAYER_IMG.get_size()
        self.x = (game.WIDTH - self.W) // 2
        # 初始位置在最下方的三分之一部分
        min_y = game.HEIGHT * 2/3
        self.y = max(min_y, game.HEIGHT - self.H - 10)
        self.lives = 3
        self.max_hp = 100 - 5 * ((level - 1) // 10)  # 随关卡增加难度，降低玩家基础生命上限
        self.reduce_max_hp = 0  # 由于受到伤害而减少的生命上限
        self.actual_max_hp = self.max_hp - self.reduce_max_hp  # 实际的生命上限
        self.hp = self.actual_max_hp
        self.max_shield = self.max_hp * 2
        self.shield = 0
        self.score = 0
        self.shoot_cd = self.SHOOT_CD
        self.bullet_streams = 1  # 当前弹道数量，拾取弹道道具后增加。
        self.shoot_timer = self.shoot_cd  # 进入时有冷却，不立即发射
        self.invincible = 0   # 受伤后无敌帧
        self.god_mode = False  # 开发者模式无敌，不触发受伤闪烁
        self.can_shoot = True  # 是否可以发射子弹
    
    def update(self, keys):
        """更新玩家状态"""
        # 计算移动方向
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= self.SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.SPEED
        
        # 更新位置
        self.x += dx
        self.y += dy
        
        # 边界检测
        self._clamp_position()
        
        # 状态更新
        self._update_timers()
    
    def _clamp_position(self):
        """边界检测：飞机只能在最下方的三分之一的部分移动"""
        self.x = clamp(self.x, 0, self.game.WIDTH - self.W)
        min_y = self.game.HEIGHT * 2 / 3
        self.y = clamp(self.y, min_y, self.game.HEIGHT - self.H)
    
    def _update_timers(self):
        """更新计时器"""
        # 无敌状态倒计时
        if self.invincible > 0:
            self.invincible -= 1
            # 无敌状态结束时恢复射击能力
            if self.invincible == 0:
                self.can_shoot = True
        
        # 射击冷却
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
    
    def try_shoot(self):
        """尝试发射子弹"""
        if self.shoot_timer <= 0 and (self.can_shoot or self.invincible > 0):  # 无敌时可以发射子弹
            self.shoot_timer = self.shoot_cd
            return True
        return False
    
    def draw(self, surf):
        """绘制玩家"""
        # 无敌时闪烁
        if not self.god_mode and self.invincible > 0 and self.invincible % 4 < 2:
            return
        
        # 绘制玩家飞机图片
        self.game.renderer.draw_player(surf, self.x + self.W // 2, self.y + self.H // 2)

class Enemy:
    """陨石实体：尺寸等级决定尺寸、血量、速度、得分和伤害范围。"""
    def __init__(self, game, kind=None, meteorite_img=None):
        self.game = game
        # 随机生成陨石大小（0-4）
        if kind is None:
            # 按照大小分布生成陨石，小陨石出现概率更高
            weights = [0.4, 0.3, 0.15, 0.1, 0.05]  # 大小0-4的概率
            self.kind = random.choices([0, 1, 2, 3, 4], weights=weights)[0]
        else:
            self.kind = kind
        
        # 为这个敌人选择一张陨石图片，碎裂子陨石默认继承父级图片
        if meteorite_img is not None:
            self.meteorite_img = meteorite_img
        elif game.METEORITE_IMG_CACHE:
            self.meteorite_img = random.choice(list(game.METEORITE_IMG_CACHE.values()))
        else:
            self.meteorite_img = None

        # 创建图片遮罩用于碰撞检测。
        if self.meteorite_img:
            self.meteorite_mask = pygame.mask.from_surface(self.meteorite_img)
        else:
            self.meteorite_mask = None
        
        # 根据大小调整陨石尺寸（使用实际图片尺寸）
        scale = game.SIZE_SCALE[self.kind]
        if self.meteorite_img:
            img_width, img_height = self.meteorite_img.get_size()
            self.W = int(img_width * scale)
            self.H = int(img_height * scale)
        else:
            # 如果没有图片，使用基础尺寸
            base_size = 50
            self.W = int(base_size * scale)
            self.H = int(base_size * scale)
        
        # 初始化位置
        max_x = max(0, game.WIDTH - self.W)
        self.x = random.randint(0, max_x)
        self.y = -self.H
        
        # 根据大小调整速度
        min_speed, max_speed = game.SIZE_SPEEDS[self.kind]
        self.vy = random.uniform(min_speed, max_speed)
        self.vx = random.uniform(-1, 1)
        
        # 旋转属性
        self.rotation = 0
        self.rotation_speed = random.uniform(0.01, 0.04) * random.choice([1, -1])
        
        # 生命值：根据大小确定
        self.hp = game.SIZE_HP[self.kind]
        
        # 预先生成缩放后的陨石图片，用于加速绘制和碰撞检测。
        if self.meteorite_img:
            self.base_image = pygame.transform.smoothscale(self.meteorite_img, (self.W, self.H))
            self.base_mask = pygame.mask.from_surface(self.base_image)
            self.rotated_img = None
            self.rotated_mask = None
            self.rotated_rect = None
            self._last_rotation_deg = None
            self.prepare_render()
    
    def prepare_render(self):
        """为当前帧准备旋转后的渲染图像和碰撞掩码"""
        if not self.meteorite_img:
            return
        rotation_deg = int(self.rotation * 180 / math.pi)
        if rotation_deg != self._last_rotation_deg:
            self.rotated_img = pygame.transform.rotate(self.base_image, rotation_deg)
            self.rotated_mask = pygame.mask.from_surface(self.rotated_img)
            self._last_rotation_deg = rotation_deg
        self.rotated_rect = self.rotated_img.get_rect(center=(self.x + self.W // 2, self.y + self.H // 2))
    
    def update(self, speed_multiplier=1.0):
        """更新敌人状态"""
        # 更新位置
        self._update_position(speed_multiplier)
        
        # 更新旋转
        self._update_rotation(speed_multiplier)
        
        # 预先渲染当前帧
        self.prepare_render()
        
        # 边界检测
        return self._check_boundaries()
    
    def _update_position(self, speed_multiplier=1.0):
        """更新敌人位置"""
        self.y += self.vy * speed_multiplier
        self.x += self.vx * speed_multiplier
    
    def _update_rotation(self, speed_multiplier=1.0):
        """更新敌人旋转"""
        self.rotation += self.rotation_speed * speed_multiplier
    
    def _check_boundaries(self):
        """检查边界"""
        # 水平边界检测：碰到边缘直接消失
        if self.x < -self.W or self.x > self.game.WIDTH:
            return True  # 超出屏幕，需要移除
        # 垂直边界检测
        if self.y > self.game.HEIGHT:
            return True  # 超出屏幕，需要移除
        return False
    
    def draw(self, surf):
        """绘制敌人"""
        if self.meteorite_img and self.rotated_img and self.rotated_rect:
            surf.blit(self.rotated_img, self.rotated_rect.topleft)
        else:
            center_x = self.x + self.W // 2
            center_y = self.y + self.H // 2
            self.game.renderer.draw_enemy(surf, center_x, center_y, size=self.kind, rotation=self.rotation, img=self.meteorite_img)

class Bullet:
    """玩家子弹实体：优先使用资源图片，没有图片时使用矩形兜底。"""
    W, H = BULLET_TARGET_WIDTH, BULLET_TARGET_HEIGHT
    SPEED = BULLET_SPEED
    
    def __init__(self, x, y, game, vx=0):
        self.game = game
        self.vx = vx
        self.image = game.get_bullet_image()
        if self.image:
            self.W, self.H = self.image.get_size()
            self.mask = pygame.mask.from_surface(self.image, 127)
        else:
            self.W, self.H = self.__class__.W, self.__class__.H
            fallback_surface = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            pygame.draw.rect(fallback_surface, (255, 255, 255, 255), (0, 0, self.W, self.H))
            self.mask = pygame.mask.from_surface(fallback_surface)

        # 确保子弹从玩家中心发射
        self.x = x - self.W // 2
        self.y = y - self.H
    
    def update(self):
        """更新子弹状态"""
        # 更新位置
        self._update_position()
        
        # 检查是否超出屏幕
        return self._check_boundaries()
    
    def _update_position(self):
        """更新子弹位置"""
        self.x += self.vx
        self.y -= self.SPEED
    
    def _check_boundaries(self):
        """检查边界"""
        if self.y < -self.H or self.x < -self.W or self.x > self.game.WIDTH:
            return True  # 超出屏幕，需要移除
        return False
    
    def draw(self, surf):
        """绘制子弹"""
        if self.image:
            surf.blit(self.image, (int(self.x), int(self.y)))
        else:
            self.game.renderer.draw_bullet(surf, self.x + self.W // 2, self.y + self.H // 2, friendly=True)


class PowerUp:
    """陨石掉落的道具。

    道具类型决定效果；图片为可选贴图，缺图时使用彩色圆形和中文单字兜底。
    """
    W, H = POWERUP_TARGET_SIZE, POWERUP_TARGET_SIZE
    SPEED = 2.7

    COLORS_BY_KIND = {
        "repair": (80, 230, 140),
        "score": (255, 215, 85),
        "shield": (95, 205, 255),
        "rapid_fire": (255, 145, 85),
        "bullet_stream": (190, 125, 255),
    }
    LABELS_BY_KIND = {
        "repair": "修",
        "score": "分",
        "shield": "盾",
        "rapid_fire": "速",
        "bullet_stream": "弹",
    }

    def __init__(self, x, y, kind, image=None):
        self.image = image
        if self.image:
            self.W, self.H = self.image.get_size()
        self.x = x - self.W // 2
        self.y = y - self.H // 2
        self.kind = kind
        self.float_timer = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def update(self):
        self.float_timer += 1
        self.y += self.SPEED
        self.x += math.sin(self.float_timer * 0.08) * 0.55
        return self.y > HEIGHT

    def draw(self, surf, font):
        rect = self.rect
        # 新版道具优先绘制道具图片目录中加载的图片。
        if self.image:
            surf.blit(self.image, rect.topleft)
            return

        # 如果图片缺失，保留旧版圆形图标兜底，方便开发时发现映射问题。
        color = self.COLORS_BY_KIND.get(self.kind, (255, 255, 255))
        pygame.draw.circle(surf, (15, 24, 38), rect.center, self.W // 2)
        pygame.draw.circle(surf, color, rect.center, self.W // 2, 3)
        pygame.draw.circle(surf, (255, 255, 255), rect.center, self.W // 2 - 7, 1)

        label = font.render(self.LABELS_BY_KIND.get(self.kind, "?"), True, color)
        surf.blit(label, (rect.centerx - label.get_width() // 2,
                          rect.centery - label.get_height() // 2))
