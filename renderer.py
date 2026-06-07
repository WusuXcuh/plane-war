"""游戏内绘制系统。

集中绘制背景、状态栏、血条、返回按钮，以及没有贴图时的实体兜底外观。
"""

import math

import pygame

from rules import calculate_level_spawn_interval
from utils import create_button_surface


class Renderer:
    def __init__(self, game):
        self.game = game

    def draw_player(self, surf, cx, cy):
        w, h = self.game.PLAYER_IMG.get_size()
        surf.blit(self.game.PLAYER_IMG, (cx - w // 2, cy - h // 2))

    def draw_enemy(self, surf, cx, cy, size=1, rotation=0, img=None):
        if img:
            sc = self.game.SIZE_SCALE[size]
            img_width, img_height = img.get_size()
            scaled_width = int(img_width * sc)
            scaled_height = int(img_height * sc)

            cache_key = (id(img), size, scaled_width, scaled_height)
            scaled_img = self.game.SCALED_METEORITE_CACHE.get(cache_key)
            if scaled_img is None:
                scaled_img = pygame.transform.smoothscale(img, (scaled_width, scaled_height))
                self.game.SCALED_METEORITE_CACHE[cache_key] = scaled_img

            rotation_deg = int(rotation * 180 / math.pi)
            rotated_img = pygame.transform.rotate(scaled_img, rotation_deg)
            rect = rotated_img.get_rect(center=(cx, cy))
            surf.blit(rotated_img, rect.topleft)
        else:
            self._draw_enemy_polygon(surf, cx, cy, size, rotation)

    def _draw_enemy_polygon(self, surf, cx, cy, size=1, rotation=0):
        sc = self.game.SIZE_SCALE[size]
        colors = [
            ((140, 110, 75), (80, 58, 32), (195, 165, 120)),
            ((120, 90, 60), (70, 50, 30), (180, 150, 110)),
            ((108, 76, 44), (60, 40, 18), (168, 132, 90)),
            ((95, 62, 30), (50, 30, 10), (155, 115, 68)),
            ((80, 48, 20), (38, 20, 5), (135, 95, 50)),
        ]
        rock, rock_dark, rock_lit = colors[size]

        def sp(x, y):
            rx = x * math.cos(rotation) - y * math.sin(rotation)
            ry = x * math.sin(rotation) + y * math.cos(rotation)
            return (cx + int(rx * sc), cy + int(ry * sc))

        pts = [sp(-13, -24), sp(8, -26), sp(24, -10), sp(26, 8),
               sp(13, 26), sp(-8, 29), sp(-24, 13), sp(-29, -5)]
        pygame.draw.polygon(surf, rock, pts)
        pygame.draw.polygon(surf, rock_dark, pts, max(1, int(2 * sc)))

        pygame.draw.circle(surf, rock_dark, sp(5, -5), max(1, int(6 * sc)))
        pygame.draw.circle(surf, rock_dark, sp(-10, 10), max(1, int(4 * sc)))
        if size >= 2:
            pygame.draw.circle(surf, rock_dark, sp(3, 18), max(1, int(3 * sc)))
        if size >= 3:
            pygame.draw.circle(surf, rock_dark, sp(-5, -16), max(1, int(3 * sc)))

        pygame.draw.polygon(surf, rock_lit, [sp(-10, -18), sp(3, -21), sp(10, -8), sp(-3, -5)])

    def draw_bullet(self, surf, x, y, friendly=True):
        if friendly:
            pygame.draw.rect(surf, self.game.COLORS['YELLOW'], (x - 2, y - 8, 4, 16), border_radius=2)
            glow = pygame.Surface((10, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 255, 0, 60), (0, 0, 10, 20))
            surf.blit(glow, (x - 5, y - 10))
        else:
            rock = (150, 115, 75)
            rock_dark = (80, 55, 30)
            rock_lit = (210, 175, 120)
            pts = [
                (x - 2, y - 4),
                (x + 2, y - 5),
                (x + 5, y - 1),
                (x + 4, y + 3),
                (x + 1, y + 5),
                (x - 3, y + 3),
                (x - 5, y - 0),
            ]
            pygame.draw.polygon(surf, rock, pts)
            pygame.draw.polygon(surf, rock_dark, pts, 1)
            pygame.draw.line(surf, rock_lit, (x - 1, y - 3), (x + 2, y - 4), 1)

    def draw_background(self, scroll):
        self.game.screen.fill(self.game.COLORS['BLACK'])
        for sx, sy, sp in self.game.stars:
            ny = (sy + scroll * sp * 0.5) % self.game.HEIGHT
            b = int(100 + 155 * sp)
            r = 1 if sp < 0.5 else 2
            pygame.draw.circle(self.game.screen, (b, b, b), (sx, int(ny)), r)

    def draw_hud(self, player, level, score_target):
        txt = self.game.font_s.render(f"得分: {player.score}", True, self.game.COLORS['WHITE'])
        self.game.screen.blit(txt, (15, 15))

        txt = self.game.font_s.render(f"关卡: {level}", True, self.game.COLORS['YELLOW'])
        self.game.screen.blit(txt, (self.game.WIDTH // 2 - txt.get_width() // 2, 15))

        txt = self.game.font_s.render(f"命: {player.lives}", True, self.game.COLORS['CYAN'])
        self.game.screen.blit(txt, (self.game.WIDTH - txt.get_width() - 15, 15))

        progress = min(100, int(player.score / score_target * 100))
        txt = self.game.font_s.render(f"目标: {player.score}/{score_target} ({progress}%)", True, self.game.COLORS['GREEN'])
        self.game.screen.blit(txt, (15, 50))

        self._draw_hp_bar(player, 15, 90, 220, 16)
        self._draw_return_button()

    def _draw_hp_bar(self, player, x, y, width, height):
        hp_ratio = max(0, min(1, player.hp / player.max_hp))
        fill_width = int(width * hp_ratio)

        if hp_ratio > 0.6:
            fill_color = self.game.COLORS['GREEN']
        elif hp_ratio > 0.3:
            fill_color = self.game.COLORS['YELLOW']
        else:
            fill_color = self.game.COLORS['RED']

        pygame.draw.rect(self.game.screen, (40, 40, 40), (x, y, width, height), border_radius=4)
        if fill_width > 0:
            pygame.draw.rect(self.game.screen, fill_color, (x, y, fill_width, height), border_radius=4)

        reduce_max_hp = max(0, getattr(player, "reduce_max_hp", 0))
        max_hp = max(1, getattr(player, "max_hp", 1))
        reduce_width = min(width, int(width * reduce_max_hp / max_hp))
        if reduce_width > 0:
            reduce_rect = pygame.Rect(x + width - reduce_width, y, reduce_width, height)
            reduce_surface = pygame.Surface((reduce_width, height), pygame.SRCALPHA)
            pygame.draw.rect(reduce_surface, (58, 58, 62, 235), (0, 0, reduce_width, height), border_radius=4)

            start_x = -height
            while start_x < reduce_width:
                pygame.draw.line(
                    reduce_surface,
                    (26, 26, 30, 210),
                    (start_x, height),
                    (start_x + height, 0),
                    3
                )
                start_x += 7

            pygame.draw.line(reduce_surface, (150, 150, 155, 180), (0, 0), (0, height), 1)
            pygame.draw.rect(reduce_surface, (18, 18, 22, 190), (0, 0, reduce_width, height), width=1, border_radius=4)
            self.game.screen.blit(reduce_surface, reduce_rect.topleft)

        shield = getattr(player, "shield", 0)
        max_shield = max(1, getattr(player, "max_shield", player.max_hp * 2))
        if shield > 0:
            shield_width = int(width * min(1, shield / max_shield))
            shield_surface = pygame.Surface((shield_width, height), pygame.SRCALPHA)
            pygame.draw.rect(shield_surface, (230, 248, 255, self.game.SHIELD_ALPHA), (0, 0, shield_width, height), border_radius=4)
            pygame.draw.rect(
                shield_surface,
                (255, 255, 255, min(255, self.game.SHIELD_ALPHA + 35)),
                (0, 1, shield_width, max(1, height // 3)),
                border_radius=4
            )
            pygame.draw.rect(shield_surface, (255, 255, 255, 245), (0, 0, shield_width, height), width=2, border_radius=4)
            self.game.screen.blit(shield_surface, (x, y))

    def draw_endless_hud(self, player, spawn_interval, difficulty_level=None):
        if difficulty_level is None:
            base_interval = calculate_level_spawn_interval(80)
            difficulty_level = 80 + max(0, (base_interval - spawn_interval) // 2)

        txt = self.game.font_s.render(f"难度: {difficulty_level}", True, self.game.COLORS['ORANGE'])
        self.game.screen.blit(txt, (15, 15))

        txt = self.game.font_s.render(f"得分: {player.score}", True, self.game.COLORS['WHITE'])
        self.game.screen.blit(txt, (15, 50))

        txt = self.game.font_s.render(f"最高记录: {self.game.high_score}", True, self.game.COLORS['YELLOW'])
        self.game.screen.blit(txt, (15, 85))

        txt = self.game.font_s.render("模式: 无尽", True, self.game.COLORS['MAGENTA'])
        self.game.screen.blit(txt, (self.game.WIDTH // 2 - txt.get_width() // 2, 15))

        txt = self.game.font_s.render(f"命: {player.lives}", True, self.game.COLORS['CYAN'])
        self.game.screen.blit(txt, (self.game.WIDTH - txt.get_width() - 15, 15))

        self._draw_hp_bar(player, 15, 120, 220, 16)
        self._draw_return_button()

    def _draw_return_button(self):
        btn_surface = create_button_surface(
            (self.game.RETURN_BUTTON_RECT.width, self.game.RETURN_BUTTON_RECT.height),
            (255, 100, 100, 120),
            (255, 150, 150, 200),
            border_radius=8,
        )
        self.game.screen.blit(btn_surface, self.game.RETURN_BUTTON_RECT.topleft)
        return_txt = self.game.font_s.render("返回", True, self.game.COLORS['WHITE'])
        self.game.screen.blit(return_txt, (
            self.game.RETURN_BUTTON_RECT.centerx - return_txt.get_width() // 2,
            self.game.RETURN_BUTTON_RECT.centery - return_txt.get_height() // 2
        ))

    def show_text_center(self, text, font, color, y):
        text_surf = font.render(text, True, color)
        self.game.screen.blit(text_surf, (self.game.WIDTH // 2 - text_surf.get_width() // 2, y))
