"""游戏界面流程：开始界面、关卡选择、结算和退出确认。"""

import random
import sys

import pygame

from plane_war.core.constants import MAX_LEVEL
from plane_war.ui.widgets import create_button_surface


class Interfaces:
    """游戏界面类"""

    # 关卡选择界面的分页和按钮布局。
    LEVELS_PER_PAGE = 10
    LEVEL_BUTTON_SIZE = 80
    LEVEL_BUTTON_SELECTED_SIZE = 125

    def __init__(self, game):
        self.game = game

    def _game_view_left_offset(self):
        runtime_tools = getattr(self.game, "runtime_tools", None)
        if runtime_tools and hasattr(runtime_tools, "get_game_view_left_offset"):
            return runtime_tools.get_game_view_left_offset()
        return 0

    def _show_game_text_center(self, text, font, color, y):
        text_surf = font.render(text, True, color)
        x = self._game_view_left_offset() + self.game.WIDTH // 2 - text_surf.get_width() // 2
        self.game.screen.blit(text_surf, (x, y))

    def _draw_button(self, rect, fill_color, border_color, border_radius=10, text=None, text_color=None, font=None):
        surf = create_button_surface((rect.w, rect.h), fill_color, border_color, border_radius=border_radius)
        self.game.screen.blit(surf, rect.topleft)
        if text and font and text_color:
            label = font.render(text, True, text_color)
            self.game.screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    def _draw_nav_button(self, rect, text, font):
        """绘制关卡选择界面上的蓝色导航按钮（返回、左右翻页）。"""
        self._draw_button(
            rect,
            (0, 60, 120, 180),
            (0, 160, 255, 200),
            text=text,
            text_color=self.game.COLORS["WHITE"],
            font=font,
        )

    def _create_deco_rocks(self, count=6):
        """生成主界面和关卡选择界面共用的背景装饰陨石。

        这些陨石只是背景，不参与碰撞和得分。每个陨石固定一张贴图，避免每帧换图闪烁。
        """
        return [
            {
                "x": random.randint(0, self.game.WIDTH),
                "y": random.randint(0, self.game.HEIGHT),
                "vx": random.uniform(-0.4, 0.4),
                "vy": random.uniform(0.3, 0.9),
                "kind": random.randint(0, 1),
                "rotation": 0,
                "rotation_speed": random.uniform(0.01, 0.04) * random.choice([1, -1]),
                "img": self.game.get_random_meteorite_image(),
            }
            for _ in range(count)
        ]

    def _draw_deco_rocks(self, deco_rocks):
        """推进并绘制背景装饰陨石，整体半透明叠在星空之上。"""
        rock_surf = pygame.Surface((self.game.WIDTH, self.game.HEIGHT), pygame.SRCALPHA)
        for rock in deco_rocks:
            rock["x"] = (rock["x"] + rock["vx"]) % self.game.WIDTH
            rock["y"] = (rock["y"] + rock["vy"]) % self.game.HEIGHT
            rock["rotation"] += rock["rotation_speed"]
            self.game.renderer.draw_enemy(
                rock_surf,
                int(rock["x"]),
                int(rock["y"]),
                rock["kind"],
                rock["rotation"],
                img=rock["img"],
            )
        rock_surf.set_alpha(60)
        self.game.screen.blit(rock_surf, (0, 0))

    def _level_button_rect(self, index_in_page):
        """按页内序号算出关卡按钮的位置。

        点击检测和绘制共用这一套布局，改动按钮排布时只需要改这里。
        """
        x = 100 + (index_in_page % 5) * 100
        y = 200 + (index_in_page // 5) * 80
        size = self.LEVEL_BUTTON_SIZE
        return pygame.Rect(x - size // 2, y - size // 2, size, size)

    def handle_interface_events(self, event_handler=None):
        """处理界面通用事件"""
        # 处理事件，但不清空事件队列
        event = pygame.event.poll()
        while event:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event_handler:
                result = event_handler(event)
                if result is not None:
                    return result
            event = pygame.event.poll()
        return None

    def confirm_exit_screen(self):
        """退出确认界面"""
        alpha = 0
        paused_frame = self.game.screen.copy()
        fade_surf = pygame.Surface((self.game.WIDTH, self.game.HEIGHT))
        fade_surf.fill(self.game.COLORS["BLACK"])
        game_left = self._game_view_left_offset()
        game_center_x = game_left + self.game.WIDTH // 2

        selected = 0  # 0: 继续游戏, 1: 退出游戏
        panel_rect = pygame.Rect(0, 0, 430, 250)
        panel_rect.center = (game_center_x, self.game.HEIGHT // 2)
        continue_rect = pygame.Rect(panel_rect.left + 42, panel_rect.bottom - 78, 155, 48)
        exit_rect = pygame.Rect(panel_rect.right - 197, panel_rect.bottom - 78, 155, 48)

        def event_handler(event):
            nonlocal selected
            if event.type == pygame.KEYDOWN:
                key_text = getattr(event, "unicode", "").lower()
                key_name = pygame.key.name(event.key).lower()
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    selected = 0
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    selected = 1
                elif key_text in ("y", "ｙ") or key_name == "y":
                    return True
                elif key_text in ("n", "ｎ") or key_name == "n":
                    return False
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return selected == 1
                elif event.key == pygame.K_ESCAPE:
                    return False  # 退出键默认继续游戏
            if event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                if continue_rect.collidepoint(mouse_pos):
                    selected = 0
                elif exit_rect.collidepoint(mouse_pos):
                    selected = 1
            if event.type == pygame.MOUSEBUTTONDOWN:
                if continue_rect.collidepoint(pygame.mouse.get_pos()):
                    return False
                elif exit_rect.collidepoint(pygame.mouse.get_pos()):
                    return True
            return None

        def draw_label_center(text, font, color, y):
            label = font.render(text, True, color)
            self.game.screen.blit(label, (game_center_x - label.get_width() // 2, y))

        def draw_dialog_button(rect, text, active, danger=False):
            mouse_hover = rect.collidepoint(pygame.mouse.get_pos())
            if danger:
                fill = (210, 60, 70, 235) if active or mouse_hover else (105, 36, 45, 215)
                border = (255, 160, 165, 255) if active or mouse_hover else (160, 85, 95, 230)
            else:
                fill = (55, 145, 110, 235) if active or mouse_hover else (34, 86, 78, 215)
                border = (145, 235, 205, 255) if active or mouse_hover else (85, 150, 135, 230)

            self._draw_button(rect, fill, border, border_radius=8, text=text, text_color=self.game.COLORS["WHITE"], font=self.game.font_s_bold)

        while True:
            self.game.clock.tick(self.game.FPS)

            # 处理事件
            result = self.handle_interface_events(event_handler)
            if result is not None:
                return result

            # 渐入
            if alpha < 200:
                alpha = min(200, alpha + 5)

            self.game.screen.blit(paused_frame, (0, 0))
            fade_surf.set_alpha(alpha)
            self.game.screen.blit(fade_surf, (game_left, 0))

            panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (18, 24, 36, 238), panel_surf.get_rect(), border_radius=12)
            pygame.draw.rect(panel_surf, (115, 175, 220, 230), panel_surf.get_rect(), 2, border_radius=12)
            self.game.screen.blit(panel_surf, panel_rect.topleft)

            # 标题与提示
            draw_label_center("暂停", self.game.font_l, self.game.COLORS["CYAN"], panel_rect.top + 28)
            draw_label_center("要退出当前游戏吗？", self.game.font_m, self.game.COLORS["WHITE"], panel_rect.top + 96)
            draw_label_center("退出键 / N 继续，Y 退出", self.game.font_s, (185, 215, 235), panel_rect.top + 143)

            # 按钮
            draw_dialog_button(continue_rect, "继续游戏", selected == 0)
            draw_dialog_button(exit_rect, "退出游戏", selected == 1, danger=True)

            pygame.display.flip()

    def level_select_screen(self):
        """关卡选择界面。

        返回选中的关卡号；返回 0 表示玩家按了返回，要回到主界面。
        """
        scroll = 0
        selected_level = 1
        page = 0  # 当前页码，每页显示 LEVELS_PER_PAGE 个关卡
        per_page = self.LEVELS_PER_PAGE
        last_page = (MAX_LEVEL - 1) // per_page

        deco_rocks = self._create_deco_rocks()

        back_rect = pygame.Rect(10, 10, 100, 40)
        left_rect = pygame.Rect(50, self.game.HEIGHT // 2 - 20, 60, 40)
        right_rect = pygame.Rect(self.game.WIDTH - 110, self.game.HEIGHT // 2 - 20, 60, 40)

        def levels_on_page():
            """当前页上的关卡号列表。"""
            first = page * per_page + 1
            return [level for level in range(first, first + per_page) if level <= MAX_LEVEL]

        def turn_page(delta):
            """翻页并把选中项移到新一页的第一关，越界时首尾循环。"""
            nonlocal page, selected_level
            page = (page + delta) % (last_page + 1)
            selected_level = page * per_page + 1

        def move_selection(delta):
            """在当前页内移动选中项，越界时在本页首尾循环。"""
            nonlocal selected_level
            levels = levels_on_page()
            index = levels.index(selected_level) if selected_level in levels else 0
            selected_level = levels[(index + delta) % len(levels)]

        def event_handler(event):
            nonlocal selected_level
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    turn_page(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    turn_page(1)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    move_selection(-1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    move_selection(1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return selected_level
                elif event.key == pygame.K_ESCAPE:
                    return 0
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if back_rect.collidepoint(mouse_pos):
                    return 0
                if left_rect.collidepoint(mouse_pos):
                    turn_page(-1)
                elif right_rect.collidepoint(mouse_pos):
                    turn_page(1)

                # 点一次选中关卡，再点一次进入该关卡。
                for index, level_num in enumerate(levels_on_page()):
                    if self._level_button_rect(index).collidepoint(mouse_pos):
                        if selected_level == level_num:
                            return selected_level
                        selected_level = level_num
            return None

        while True:
            self.game.clock.tick(self.game.FPS)
            scroll += 1

            result = self.handle_interface_events(event_handler)
            if result is not None:
                return result

            self.game.renderer.draw_background(scroll)
            self._draw_deco_rocks(deco_rocks)

            self.game.renderer.show_text_center("选择关卡", self.game.font_l, self.game.COLORS["CYAN"], 80)

            self._draw_nav_button(back_rect, "返回", self.game.font_s)
            self._draw_nav_button(left_rect, "←", self.game.font_m)
            self._draw_nav_button(right_rect, "→", self.game.font_m)

            for index, level_num in enumerate(levels_on_page()):
                self._draw_level_button(self._level_button_rect(index).center, level_num, level_num == selected_level)

            page_text = self.game.font_s.render(f"第 {page + 1} / {last_page + 1} 页", True, (255, 220, 100))
            self.game.screen.blit(page_text, (self.game.WIDTH // 2 - page_text.get_width() // 2, self.game.HEIGHT - 60))

            self.game.renderer.show_text_center("使用方向键或鼠标选择关卡", self.game.font_s, (180, 220, 255), self.game.HEIGHT - 30)

            pygame.display.flip()

    def _draw_level_button(self, center, level_num, is_selected):
        """绘制一个关卡按钮：优先用模板底图，缺图时退回到圆形按钮。"""
        x, y = center

        if self.game.LEVEL_BUTTON_TEMPLATE is not None:
            size = self.LEVEL_BUTTON_SELECTED_SIZE if is_selected else self.LEVEL_BUTTON_SIZE
            scaled_button = pygame.transform.smoothscale(self.game.LEVEL_BUTTON_TEMPLATE, (size, size))
            self.game.screen.blit(scaled_button, scaled_button.get_rect(center=center))
            if is_selected:
                text = self.game.font_m.render(str(level_num), True, (255, 200, 0))
            else:
                text = self.game.font_s.render(str(level_num), True, (255, 255, 255))
        elif is_selected:
            pygame.draw.circle(self.game.screen, (255, 200, 0), center, 35)
            pygame.draw.circle(self.game.screen, (255, 255, 255), center, 35, 3)
            text = self.game.font_s.render(str(level_num), True, (0, 60, 120))
        else:
            pygame.draw.circle(self.game.screen, (0, 100, 180), center, 25)
            pygame.draw.circle(self.game.screen, (0, 160, 255), center, 25, 2)
            text = self.game.font_s.render(str(level_num), True, (180, 220, 255))

        self.game.screen.blit(text, (x - text.get_width() // 2, y - text.get_height() // 2))

    def start_screen(self):
        """开始界面"""
        scroll = 0
        blink = 0
        selected_mode = 0  # 0: 关卡模式, 1: 无尽模式

        deco_rocks = self._create_deco_rocks()

        def event_handler(event):
            nonlocal selected_mode
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    selected_mode = 0  # 切换到关卡模式
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    selected_mode = 1  # 切换到无尽模式

                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if selected_mode == 0:
                        # 进入关卡选择界面
                        level = self.level_select_screen()
                        if level > 0:
                            return level  # 返回选择的关卡
                    else:
                        return "endless"  # 返回无尽模式
                elif event.key == pygame.K_ESCAPE:
                    if self.confirm_exit_screen():
                        pygame.quit()
                        sys.exit()
            # 鼠标点击检测
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                # 检测模式选择
                mode_box = pygame.Rect(100, 370, self.game.WIDTH - 200, 60)
                if mode_box.collidepoint(mouse_x, mouse_y):
                    # 计算点击的是哪个模式
                    mode_width = mode_box.w // 2
                    if mouse_x < mode_box.left + mode_width:
                        selected_mode = 0  # 关卡模式
                    else:
                        selected_mode = 1  # 无尽模式
                # 检测开始按钮
                btn_width, btn_height = 300, 50
                btn_y = 580
                btn_rect = pygame.Rect(self.game.WIDTH // 2 - btn_width // 2, btn_y, btn_width, btn_height)
                if btn_rect.collidepoint(mouse_x, mouse_y):
                    if selected_mode == 0:
                        # 进入关卡选择界面
                        level = self.level_select_screen()
                        if level > 0:
                            return level  # 返回选择的关卡
                    else:
                        return "endless"  # 返回无尽模式
            return None

        while True:
            self.game.clock.tick(self.game.FPS)
            scroll += 1
            blink += 1

            # 处理事件
            result = self.handle_interface_events(event_handler)
            if result is not None:
                return result

            self.game.renderer.draw_background(scroll)
            self._draw_deco_rocks(deco_rocks)

            # 标题背景光晕
            glow = pygame.Surface((420, 100), pygame.SRCALPHA)
            for i in range(30, 0, -1):
                alpha = int(120 * i / 30)
                pygame.draw.ellipse(glow, (0, 180, 255, alpha), (30 - i, 20 - i // 2, 360 + i * 2, 60 + i))
            self.game.screen.blit(glow, (self.game.WIDTH // 2 - 210, 80))

            # 标题文字（描边 + 主色）
            title = "飞机大战"
            for dx, dy, col in [(-2, 2, (0, 60, 120)), (2, 2, (0, 60, 120)), (-2, -2, (0, 60, 120)), (2, -2, (0, 60, 120))]:
                s = self.game.font_l.render(title, True, col)
                self.game.screen.blit(s, (self.game.WIDTH // 2 - s.get_width() // 2 + dx, 90 + dy))
            self.game.renderer.show_text_center(title, self.game.font_l, self.game.COLORS["CYAN"], 90)

            # 分隔线
            line_y = 200
            pygame.draw.line(self.game.screen, (0, 120, 180), (80, line_y), (self.game.WIDTH - 80, line_y), 1)
            pygame.draw.line(self.game.screen, (0, 60, 100), (80, line_y + 2), (self.game.WIDTH - 80, line_y + 2), 1)

            # 模式选择
            mode_box = pygame.Rect(100, 250, self.game.WIDTH - 200, 60)
            mode_surf = pygame.Surface((mode_box.w, mode_box.h), pygame.SRCALPHA)
            pygame.draw.rect(mode_surf, (0, 60, 120, 180), (0, 0, mode_box.w, mode_box.h), border_radius=15)
            pygame.draw.rect(mode_surf, (0, 160, 255, 200), (0, 0, mode_box.w, mode_box.h), 2, border_radius=15)
            self.game.screen.blit(mode_surf, mode_box.topleft)

            # 模式选项
            mode_texts = ["关卡模式", "无尽模式"]
            for i in range(2):
                # 计算每个选项的中心位置，使它们在框中均匀分布
                x = mode_box.left + mode_box.w // 4 + i * (mode_box.w // 2)
                y = mode_box.top + mode_box.h // 2
                if i == selected_mode:
                    text = self.game.font_m.render(mode_texts[i], True, (255, 200, 0))
                else:
                    text = self.game.font_m.render(mode_texts[i], True, (180, 220, 255))
                self.game.screen.blit(text, (x - text.get_width() // 2, y - text.get_height() // 2))

            # 模式提示
            if selected_mode == 0:
                mode_hint = self.game.font_s.render("选择关卡模式，进入详细的关卡选择界面", True, (255, 220, 100))
            else:
                mode_hint = self.game.font_s.render("选择无尽模式，挑战你的极限", True, (255, 220, 100))
            self.game.screen.blit(mode_hint, (self.game.WIDTH // 2 - mode_hint.get_width() // 2, 460))

            # 闪烁开始提示
            if (blink // 30) % 2 == 0:
                # 发光底
                btn_width, btn_height = 300, 50
                btn = pygame.Surface((btn_width, btn_height), pygame.SRCALPHA)
                pygame.draw.rect(btn, (255, 200, 0, 60), (0, 0, btn_width, btn_height), border_radius=25)
                pygame.draw.rect(btn, (255, 200, 0, 180), (0, 0, btn_width, btn_height), 2, border_radius=25)
                # 调整按钮位置，避免与关卡简介重叠
                btn_y = 580
                self.game.screen.blit(btn, (self.game.WIDTH // 2 - btn_width // 2, btn_y))
                # 确保文字在闪烁圆框的正中间
                # 调整文字位置，使其在圆框中看起来更居中
                text_y = btn_y + btn_height // 2 - 16
                self.game.renderer.show_text_center("按 回车 / 空格 开始", self.game.font_s, self.game.COLORS["YELLOW"], text_y)

            pygame.display.flip()

    def _result_screen(self, draw_content):
        """结算界面的公共外壳。

        游戏结束和关卡完成两个界面的骨架完全一样：黑色渐入遮罩、回车/空格回主界面、
        退出键弹退出确认。差异只有中间那几行文字，所以交给 draw_content 去画。
        """
        alpha = 0
        fade_surf = pygame.Surface((self.game.WIDTH, self.game.HEIGHT))
        fade_surf.fill(self.game.COLORS["BLACK"])
        game_left = self._game_view_left_offset()

        def event_handler(event):
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "main_menu"
                if event.key == pygame.K_ESCAPE:
                    if self.confirm_exit_screen():
                        pygame.quit()
                        sys.exit()
            return None

        while True:
            self.game.clock.tick(self.game.FPS)

            result = self.handle_interface_events(event_handler)
            if result is not None:
                return result

            # 渐入
            if alpha < 200:
                alpha = min(200, alpha + 5)

            fade_surf.set_alpha(alpha)
            self.game.screen.blit(fade_surf, (game_left, 0))

            draw_content()

            pygame.display.flip()

    def game_over_screen(self, player):
        """游戏结束界面"""
        center_y = self.game.HEIGHT // 2

        def draw_content():
            self._show_game_text_center("游戏结束", self.game.font_l, self.game.COLORS["RED"], center_y - 80)
            self._show_game_text_center(f"最终得分: {player.score}", self.game.font_m, self.game.COLORS["WHITE"], center_y - 20)

            # 只有无尽模式会带上最高记录，带了就要把提示文字往下让一行。
            prompt_y = center_y + 40
            if getattr(player, "show_high_score", False):
                high_score_text = f"最高记录: {self.game.high_score}"
                if getattr(player, "is_new_high_score", False):
                    high_score_text += "  新纪录！"
                self._show_game_text_center(high_score_text, self.game.font_s, self.game.COLORS["YELLOW"], center_y + 20)
                prompt_y = center_y + 60

            self._show_game_text_center("按 回车 / 空格 回到主界面", self.game.font_s, self.game.COLORS["YELLOW"], prompt_y)

        return self._result_screen(draw_content)

    def level_complete_screen(self, player, score_target, prompt_text="按 回车 / 空格 进入下一关"):
        """关卡完成界面"""
        center_y = self.game.HEIGHT // 2

        def draw_content():
            self._show_game_text_center("关卡完成！", self.game.font_l, self.game.COLORS["GREEN"], center_y - 80)
            self._show_game_text_center(f"得分: {player.score} / {score_target}", self.game.font_m, self.game.COLORS["WHITE"], center_y - 20)
            self._show_game_text_center(prompt_text, self.game.font_s, self.game.COLORS["YELLOW"], center_y + 40)

        return self._result_screen(draw_content)
