"""粒子特效系统。

负责创建、更新和绘制爆炸粒子，包括子弹命中小爆炸和陨石销毁大爆炸。
粒子只是字典数据，主循环保存列表；本模块负责让它们移动、衰减和绘制。
"""

import math
import random

import pygame


class Effects:
    """爆炸粒子的工厂和更新器。"""

    def __init__(self, game):
        self.game = game

    def draw_explosion(self, surf, particles):
        """按剩余生命绘制粒子。

        粒子越接近生命周期结束，半径和透明度越小，看起来像逐渐消散。
        """
        for p in particles:
            alpha = max(0, int(255 * p["life"] / p["max_life"]))
            r = max(1, int(p["r"] * p["life"] / p["max_life"]))
            color = (*p["color"], alpha)
            particle_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, color, (r, r), r)
            surf.blit(particle_surf, (int(p["x"]) - r, int(p["y"]) - r))

    def make_explosion(self, cx, cy, n=24, colors=None, r_range=(4, 12), speed_range=(1.5, 5)):
        """在指定中心创建一组向四周飞散的粒子。"""
        if colors is None:
            colors = [
                self.game.COLORS["RED"],
                self.game.COLORS["ORANGE"],
                self.game.COLORS["YELLOW"],
                self.game.COLORS["WHITE"],
            ]

        particles = []
        for _ in range(n):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(*speed_range)
            life = random.randint(20, 45)
            particles.append(
                {
                    "x": cx,
                    "y": cy,
                    "vx": speed * math.cos(angle),
                    "vy": speed * math.sin(angle),
                    "r": random.randint(*r_range),
                    "color": random.choice(colors),
                    "life": life,
                    "max_life": life,
                }
            )
        return particles

    def make_meteorite_explosion(self, enemy):
        """根据陨石尺寸生成销毁爆炸。

        陨石越大，粒子数量、半径和速度范围越大；中大型陨石额外生成一层亮色闪光。
        """
        kind = max(0, min(enemy.kind, len(self.game.SIZE_SCALE) - 1))
        cx = enemy.x + enemy.W // 2
        cy = enemy.y + enemy.H // 2

        particles = self.make_explosion(
            cx,
            cy,
            n=28 + kind * 24,
            r_range=(5 + kind * 3, 12 + kind * 7),
            speed_range=(2.0 + kind * 0.45, 4.8 + kind * 1.15),
        )

        if kind >= 2:
            particles += self.make_explosion(
                cx,
                cy,
                n=8 + kind * 5,
                colors=[self.game.COLORS["YELLOW"], self.game.COLORS["WHITE"]],
                r_range=(12 + kind * 4, 22 + kind * 8),
                speed_range=(0.7, 1.6 + kind * 0.35),
            )

        return particles

    def update_particles(self, particles):
        """推进粒子位置和生命，并返回仍然存活的粒子列表。"""
        alive = []
        for p in particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.15
            p["life"] -= 1
            if p["life"] > 0:
                alive.append(p)
        return alive
