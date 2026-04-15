# 游戏实体类

import pygame
import random
import os
from constants import PLAYER_SPEED, PLAYER_SHOOT_CD, BULLET_SPEED, COLORS
from utils import clamp

class Player:
    """玩家类"""
    SPEED = PLAYER_SPEED
    SHOOT_CD = PLAYER_SHOOT_CD   # 帧（原14帧，加快发射频率）
    
    def __init__(self, game):
        self.game = game
        # 从游戏对象获取飞机图片的实际大小
        self.W, self.H = game.PLAYER_IMG.get_size()
        self.x = game.WIDTH // 2
        # 初始位置在最下方的三分之一部分
        min_y = game.HEIGHT * 2/3
        self.y = max(min_y, game.HEIGHT - self.H - 10)
        self.lives = 3
        self.score = 0
        self.shoot_timer = self.SHOOT_CD  # 进入时有冷却，不立即发射
        self.invincible = 0   # 受伤后无敌帧
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
        if self.shoot_timer <= 0 and self.can_shoot:  # 无敌时无法发射子弹
            self.shoot_timer = self.SHOOT_CD
            return True
        return False
    
    def draw(self, surf):
        """绘制玩家"""
        # 无敌时闪烁
        if self.invincible > 0 and self.invincible % 4 < 2:
            return
        
        # 绘制玩家飞机图片
        self.game.draw_player(surf, self.x + self.W // 2, self.y + self.H // 2)

class Enemy:
    """敌人类"""
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

        # 创建图片的mask用于碰撞检测
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
    
    def update(self):
        """更新敌人状态"""
        # 更新位置
        self._update_position()
        
        # 更新旋转
        self._update_rotation()
        
        # 边界检测
        return self._check_boundaries()
    
    def _update_position(self):
        """更新敌人位置"""
        self.y += self.vy
        self.x += self.vx
    
    def _update_rotation(self):
        """更新敌人旋转"""
        self.rotation += self.rotation_speed
    
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
        # 计算陨石的中心位置
        center_x = self.x + self.W // 2
        center_y = self.y + self.H // 2
        # 调用游戏对象的draw_enemy方法，传递图片
        self.game.draw_enemy(surf, center_x, center_y, size=self.kind, rotation=self.rotation, img=self.meteorite_img)

class Bullet:
    """子弹类"""
    W, H = 4, 12
    SPEED = BULLET_SPEED
    
    def __init__(self, x, y, game):
        # 确保子弹从玩家中心发射
        self.x = x - self.W // 2
        self.y = y - self.H
        self.game = game
    
    def update(self):
        """更新子弹状态"""
        # 更新位置
        self._update_position()
        
        # 检查是否超出屏幕
        return self._check_boundaries()
    
    def _update_position(self):
        """更新子弹位置"""
        self.y -= self.SPEED
    
    def _check_boundaries(self):
        """检查边界"""
        if self.y < -self.H:
            return True  # 超出屏幕，需要移除
        return False
    
    def draw(self, surf):
        """绘制子弹"""
        self.game.draw_bullet(surf, self.x + self.W // 2, self.y + self.H // 2, friendly=True)
