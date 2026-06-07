"""开发者模式工具。

运行开发者入口文件时会启用这些调试工具。
直接运行普通入口文件（main.py）进行普通游玩时不会创建开发者工具对象，
所以开发者快捷键和侧边面板都不可用。
"""

import itertools
import ctypes

import pygame

from entities import Enemy, PowerUp


DEV_POWERUP_KINDS = ["score", "shield", "repair", "rapid_fire", "bullet_stream"]


class DeveloperTools:
    STATUS_PANEL_WIDTH = 310
    PANEL_WIDTH = 270
    BUTTON_H = 34
    SLIDER_MIN = 1
    SLIDER_MAX = 20
    METEOR_SPEED_MIN = 0.2
    METEOR_SPEED_MAX = 3.0

    def __init__(self, game, log_func, enabled=False):
        self.game = game
        self.log = log_func
        self.enabled = enabled
        self.panel_visible = False
        self.meteor_pause = False
        self.meteor_speed_multiplier = 1.0
        self.dragging_shoot_cd = False
        self.dragging_meteor_speed = False
        self._powerup_cycle = itertools.cycle(DEV_POWERUP_KINDS)
        self._controls = {}
        self._window_rect_before_panel = None

    def handle_event(self, event, context):
        """处理开发者快捷键和侧边面板鼠标操作。"""
        if event.type == pygame.KEYDOWN:
            return self._handle_keydown(event, context)

        if not self.enabled or not self.panel_visible or context is None:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_panel_click(event.pos, context)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_shoot_cd = False
            self.dragging_meteor_speed = False
            return self._is_in_panel(event.pos)
        if event.type == pygame.MOUSEMOTION and self.dragging_shoot_cd:
            self._set_shoot_cd_from_mouse(event.pos[0], context)
            return True
        if event.type == pygame.MOUSEMOTION and self.dragging_meteor_speed:
            self._set_meteor_speed_from_mouse(event.pos[0])
            return True

        return False

    def prepare_player(self, player):
        """进入开发者模式游戏时，给玩家套用默认调试状态。"""
        player.god_mode = True
        player.invincible = 0
        player.can_shoot = True
        self.log("开发者模式默认无敌：开启")

    def get_enemy_update_settings(self):
        return not self.meteor_pause, self.meteor_speed_multiplier

    def get_game_view_left_offset(self):
        return self.STATUS_PANEL_WIDTH if self.panel_visible else 0

    def disables_high_score(self):
        return True

    def restore_game_window(self):
        if self.panel_visible:
            self._toggle_panel()

    def draw_overlay(self, surf, context):
        if not self.enabled or context is None:
            return

        if self.panel_visible:
            self._shift_game_view(surf)
            self._draw_status_panel(surf, context)
            self._draw_side_panel(surf, context)

    def _handle_keydown(self, event, context):
        if event.key == pygame.K_F10:
            self._toggle_panel()
            return True
        if event.key == pygame.K_F3:
            self.enabled = not self.enabled
            if not self.enabled and self.panel_visible:
                self._toggle_panel()
            self.log(f"开发者模式: {'启用' if self.enabled else '关闭'}")
            return True

        if not self.enabled or context is None:
            return False

        if event.key == pygame.K_F4:
            self._spawn_meteorite(context)
            return True
        if event.key == pygame.K_F5:
            self._spawn_powerup(context)
            return True
        if event.key == pygame.K_F6:
            self._restore_player(context)
            return True
        if event.key == pygame.K_F7:
            self._add_score(context, 1000)
            return True
        if event.key == pygame.K_F8:
            self._clear_hostiles(context)
            return True
        if event.key == pygame.K_F9:
            self.game.toggle_debug_collision()
            return True

        return False

    def _toggle_panel(self):
        opening = not self.panel_visible
        old_rect = self._get_window_rect() if opening else self._window_rect_before_panel
        self.panel_visible = opening
        width = (
            self.game.WIDTH + self.STATUS_PANEL_WIDTH + self.PANEL_WIDTH
            if self.panel_visible else self.game.WIDTH
        )
        self.game.screen = pygame.display.set_mode((width, self.game.HEIGHT))
        pygame.display.set_caption("飞机大战 - 开发者模式" if self.panel_visible else "飞机大战")
        self._move_window_after_resize(width, old_rect, opening)
        self.log(f"开发者侧边面板: {'显示' if self.panel_visible else '隐藏'}")

    def _get_window_rect(self):
        try:
            hwnd = pygame.display.get_wm_info().get("window")
            if not hwnd:
                return None

            class Rect(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            rect = Rect()
            if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return rect.left, rect.top, rect.right, rect.bottom
        except Exception:
            return None
        return None

    def _move_window_after_resize(self, width, old_rect, opening):
        if old_rect is None:
            self._window_rect_before_panel = None
            return

        try:
            hwnd = pygame.display.get_wm_info().get("window")
            current_rect = self._get_window_rect()
            if not hwnd or current_rect is None:
                return

            current_width = current_rect[2] - current_rect[0]
            current_height = current_rect[3] - current_rect[1]
            if opening:
                self._window_rect_before_panel = old_rect
                target_left = max(0, old_rect[0] - self.STATUS_PANEL_WIDTH)
                target_top = old_rect[1]
            else:
                target_left = old_rect[0]
                target_top = old_rect[1]
                self._window_rect_before_panel = None

            ctypes.windll.user32.MoveWindow(
                hwnd,
                int(target_left),
                int(target_top),
                int(current_width),
                int(current_height),
                True,
            )
        except Exception:
            pass

    def translate_game_mouse_pos(self, pos):
        if self.panel_visible:
            return pos[0] - self.STATUS_PANEL_WIDTH, pos[1]
        return pos

    def _shift_game_view(self, surf):
        game_view = surf.subsurface((0, 0, self.game.WIDTH, self.game.HEIGHT)).copy()
        surf.fill(self.game.COLORS['BLACK'])
        surf.blit(game_view, (self.STATUS_PANEL_WIDTH, 0))

    def _draw_status_panel(self, surf, context):
        player = context.get("player")
        enemies = context.get("enemies", [])
        bullets = context.get("bullets", [])
        particles = context.get("particles", [])
        powerups = context.get("powerups", [])
        difficulty = context.get("difficulty")

        lines = [
            "开发者状态",
            "F10 隐藏面板",
            "F3 关闭开发者模式",
            "F4 陨石  F5 道具",
            "F6 回满  F7 +1000",
            "F8 清场  F9 碰撞",
            "",
            f"帧率: {self.game.clock.get_fps():.1f}",
            f"陨石: {len(enemies)}",
            f"子弹: {len(bullets)}",
            f"粒子: {len(particles)}",
            f"道具: {len(powerups)}",
        ]
        if player:
            god = "开" if getattr(player, "god_mode", False) else "关"
            meteor_pause = "开" if self.meteor_pause else "关"
            lines.extend([
                "",
                f"分数: {player.score}",
                f"血量: {player.hp:.0f}/{player.actual_max_hp:.0f}",
                f"护盾: {player.shield:.0f}/{player.max_shield:.0f}",
                f"生命: {player.lives}",
                f"弹道: {player.bullet_streams}",
                f"无敌: {god}",
                f"陨石暂停: {meteor_pause}",
            ])
        if difficulty is not None:
            collision_debug = "开" if self.game.DEBUG_COLLISION else "关"
            lines.extend([
                "",
                f"难度: {difficulty}",
                f"碰撞调试: {collision_debug}",
                f"陨石速度: {self.meteor_speed_multiplier:.1f}x",
            ])

        x = 0
        panel_rect = pygame.Rect(x, 0, self.STATUS_PANEL_WIDTH, self.game.HEIGHT)
        pygame.draw.rect(surf, (10, 14, 22), panel_rect)
        pygame.draw.line(
            surf,
            (70, 180, 220),
            (x, 0),
            (x, self.game.HEIGHT),
            2,
        )
        pygame.draw.line(
            surf,
            (50, 120, 150),
            (x + self.STATUS_PANEL_WIDTH - 1, 0),
            (x + self.STATUS_PANEL_WIDTH - 1, self.game.HEIGHT),
            1,
        )

        y = 18
        line_height = self.game.font_s.render("测", True, self.game.COLORS['WHITE']).get_height() + 4
        for index, line in enumerate(lines):
            if not line:
                y += line_height // 2
                continue
            color = self.game.COLORS['CYAN'] if index == 0 else (190, 220, 235)
            font = self.game.font_s_bold if index == 0 else self.game.font_s
            text = font.render(line, True, color)
            surf.blit(text, (x + 18, y))
            y += line_height

    def _draw_side_panel(self, surf, context):
        self._controls.clear()
        x = self.STATUS_PANEL_WIDTH + self.game.WIDTH
        panel_rect = pygame.Rect(x, 0, self.PANEL_WIDTH, self.game.HEIGHT)
        pygame.draw.rect(surf, (14, 18, 26), panel_rect)
        pygame.draw.line(surf, (70, 180, 220), (x, 0), (x, self.game.HEIGHT), 2)

        title = self.game.font_s_bold.render("开发者面板", True, self.game.COLORS['CYAN'])
        surf.blit(title, (x + 18, 18))

        player = context.get("player")
        score = player.score if player else 0
        streams = player.bullet_streams if player else 0
        shoot_cd = player.shoot_cd if player else 0
        god_mode = bool(getattr(player, "god_mode", False)) if player else False

        y = 58
        self._draw_info(surf, x + 18, y, f"分数: {score}")
        y += 32
        self._button(surf, "score_plus", pygame.Rect(x + 18, y, 230, self.BUTTON_H), "加 1000 分")
        y += 50

        self._draw_info(surf, x + 18, y, f"弹道: {streams}")
        self._button(surf, "stream_minus", pygame.Rect(x + 112, y - 4, 46, 30), "-1")
        self._button(surf, "stream_plus", pygame.Rect(x + 166, y - 4, 46, 30), "+1")
        y += 46

        self._draw_info(surf, x + 18, y, f"射速: {shoot_cd:.1f} 帧")
        y += 30
        self._slider(
            surf,
            "shoot_cd",
            pygame.Rect(x + 18, y, 230, 26),
            shoot_cd,
            self.SLIDER_MIN,
            self.SLIDER_MAX,
        )
        y += 56

        self._draw_info(surf, x + 18, y, f"陨石速度: {self.meteor_speed_multiplier:.1f}x")
        y += 30
        self._slider(
            surf,
            "meteor_speed",
            pygame.Rect(x + 18, y, 230, 26),
            self.meteor_speed_multiplier,
            self.METEOR_SPEED_MIN,
            self.METEOR_SPEED_MAX,
        )
        y += 56

        god_text = "无敌: 开" if god_mode else "无敌: 关"
        self._button(surf, "god_mode", pygame.Rect(x + 18, y, 230, self.BUTTON_H), god_text, active=god_mode)
        y += 50

        pause_text = "陨石暂停: 开" if self.meteor_pause else "陨石暂停: 关"
        self._button(surf, "meteor_pause", pygame.Rect(x + 18, y, 230, self.BUTTON_H), pause_text, active=self.meteor_pause)
        y += 50

        self._button(surf, "heal", pygame.Rect(x + 18, y, 105, self.BUTTON_H), "回满")
        self._button(surf, "clear", pygame.Rect(x + 143, y, 105, self.BUTTON_H), "清场")
        y += 50
        self._button(surf, "meteor", pygame.Rect(x + 18, y, 105, self.BUTTON_H), "陨石")
        self._button(surf, "powerup", pygame.Rect(x + 143, y, 105, self.BUTTON_H), "道具")

        help_lines = ["F10 隐藏面板", "滑杆越左射速越快", "普通 main.py 不启用"]
        y = self.game.HEIGHT - 92
        for line in help_lines:
            self._draw_small(surf, x + 18, y, line)
            y += 24

    def _draw_info(self, surf, x, y, text):
        label = self.game.font_s.render(text, True, self.game.COLORS['WHITE'])
        surf.blit(label, (x, y))

    def _draw_small(self, surf, x, y, text):
        label = self.game.font_s.render(text, True, (170, 190, 205))
        surf.blit(label, (x, y))

    def _button(self, surf, key, rect, text, active=False):
        self._controls[key] = rect
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        if active:
            fill = (40, 120, 82)
            border = (135, 245, 185)
        else:
            fill = (42, 102, 128) if hovered else (30, 58, 76)
            border = (115, 225, 255) if hovered else (70, 145, 180)
        pygame.draw.rect(surf, fill, rect, border_radius=6)
        pygame.draw.rect(surf, border, rect, width=1, border_radius=6)
        label = self.game.font_s.render(text, True, self.game.COLORS['WHITE'])
        surf.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    def _slider(self, surf, key, rect, value, minimum, maximum):
        self._controls[key] = rect
        pygame.draw.rect(surf, (24, 32, 44), rect, border_radius=6)
        track = pygame.Rect(rect.left + 12, rect.centery - 3, rect.width - 24, 6)
        pygame.draw.rect(surf, (72, 88, 108), track, border_radius=3)
        t = (value - minimum) / (maximum - minimum)
        knob_x = int(track.left + max(0, min(1, t)) * track.width)
        pygame.draw.circle(surf, (120, 225, 255), (knob_x, rect.centery), 9)
        pygame.draw.circle(surf, (245, 252, 255), (knob_x, rect.centery), 4)

    def _handle_panel_click(self, pos, context):
        if not self._is_in_panel(pos):
            return False

        self._ensure_controls(context)
        for key, rect in self._controls.items():
            if not rect.collidepoint(pos):
                continue
            if key == "score_plus":
                self._add_score(context, 1000)
            elif key == "stream_minus":
                self._change_streams(context, -1)
            elif key == "stream_plus":
                self._change_streams(context, 1)
            elif key == "shoot_cd":
                self.dragging_shoot_cd = True
                self._set_shoot_cd_from_mouse(pos[0], context)
            elif key == "meteor_speed":
                self.dragging_meteor_speed = True
                self._set_meteor_speed_from_mouse(pos[0])
            elif key == "god_mode":
                self._toggle_god_mode(context)
            elif key == "meteor_pause":
                self._toggle_meteor_pause()
            elif key == "heal":
                self._restore_player(context)
            elif key == "clear":
                self._clear_hostiles(context)
            elif key == "meteor":
                self._spawn_meteorite(context)
            elif key == "powerup":
                self._spawn_powerup(context)
            return True

        return True

    def _ensure_controls(self, context):
        if self._controls:
            return
        temp = pygame.Surface(
            (self.game.WIDTH + self.STATUS_PANEL_WIDTH + self.PANEL_WIDTH, self.game.HEIGHT),
            pygame.SRCALPHA,
        )
        self._draw_side_panel(temp, context)

    def _is_in_panel(self, pos):
        return self.panel_visible and pos[0] >= self.game.WIDTH + self.STATUS_PANEL_WIDTH

    def _set_shoot_cd_from_mouse(self, mouse_x, context):
        player = context.get("player")
        rect = self._controls.get("shoot_cd")
        if player is None or rect is None:
            return

        track_left = rect.left + 12
        track_width = rect.width - 24
        t = max(0, min(1, (mouse_x - track_left) / track_width))
        player.shoot_cd = self.SLIDER_MIN + t * (self.SLIDER_MAX - self.SLIDER_MIN)
        player.shoot_timer = min(player.shoot_timer, player.shoot_cd)

    def _set_meteor_speed_from_mouse(self, mouse_x):
        rect = self._controls.get("meteor_speed")
        if rect is None:
            return

        track_left = rect.left + 12
        track_width = rect.width - 24
        t = max(0, min(1, (mouse_x - track_left) / track_width))
        speed = self.METEOR_SPEED_MIN + t * (self.METEOR_SPEED_MAX - self.METEOR_SPEED_MIN)
        self.meteor_speed_multiplier = round(speed, 2)

    def _spawn_meteorite(self, context):
        enemies = context.get("enemies")
        if enemies is None:
            return

        enemy = Enemy(self.game)
        enemy.y = 40
        enemies.append(enemy)
        self.log(f"开发者模式生成陨石: kind={enemy.kind}")

    def _spawn_powerup(self, context):
        player = context.get("player")
        powerups = context.get("powerups")
        if player is None or powerups is None:
            return

        kind = next(self._powerup_cycle)
        image = self.game.POWERUP_IMAGES.get(kind)
        powerups.append(PowerUp(player.x + player.W // 2, player.y - 42, kind, image=image))
        self.log(f"开发者模式生成道具: {kind}")

    def _restore_player(self, context):
        player = context.get("player")
        if player is None:
            return

        player.reduce_max_hp = 0
        player.actual_max_hp = player.max_hp
        player.hp = player.actual_max_hp
        player.shield = player.max_shield
        player.lives = max(player.lives, 3)
        self.log("开发者模式恢复玩家状态")

    def _add_score(self, context, amount):
        player = context.get("player")
        if player is None:
            return

        player.score += amount
        self.log(f"开发者模式加分: +{amount}，分数={player.score}")

    def _change_streams(self, context, delta):
        player = context.get("player")
        if player is None:
            return

        player.bullet_streams = max(1, player.bullet_streams + delta)
        self.log(f"开发者模式调整弹道: {player.bullet_streams}")

    def _toggle_god_mode(self, context):
        player = context.get("player")
        if player is None:
            return

        player.god_mode = not getattr(player, "god_mode", False)
        if player.god_mode:
            player.invincible = 0
            player.can_shoot = True
        self.log(f"开发者无敌: {'开启' if player.god_mode else '关闭'}")

    def _toggle_meteor_pause(self):
        self.meteor_pause = not self.meteor_pause
        self.log(f"开发者陨石暂停: {'开启' if self.meteor_pause else '关闭'}")

    def _clear_hostiles(self, context):
        for key in ("enemies", "bullets", "particles"):
            items = context.get(key)
            if items is not None:
                items.clear()
        self.log("开发者模式清理陨石、子弹和粒子")
