# 游戏界面函数

import pygame
import random
import sys
from constants import WIDTH, HEIGHT, COLORS
from utils import create_button_surface

class Interfaces:
    """游戏界面类"""
    
    def __init__(self, game):
        self.game = game
    
    def _draw_button(self, rect, fill_color, border_color, border_radius=10, text=None, text_color=None, font=None):
        surf = create_button_surface((rect.w, rect.h), fill_color, border_color, border_radius=border_radius)
        self.game.screen.blit(surf, rect.topleft)
        if text and font and text_color:
            label = font.render(text, True, text_color)
            self.game.screen.blit(label, (rect.centerx - label.get_width() // 2,
                                          rect.centery - label.get_height() // 2))

    def handle_interface_events(self, event_handler=None):
        """处理界面通用事件"""
        # 处理事件，但不清空事件队列
        event = pygame.event.poll()
        while event:
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event_handler:
                result = event_handler(event)
                if result is not None:
                    return result
            event = pygame.event.poll()
        return None
    
    def confirm_exit_screen(self):
        """退出确认界面"""
        alpha = 0
        fade_surf = pygame.Surface((self.game.WIDTH, self.game.HEIGHT))
        fade_surf.fill(self.game.COLORS['BLACK'])
        
        selected = 0  # 0: 是, 1: 否
        blink = 0
        
        yes_rect = pygame.Rect(self.game.WIDTH // 2 - 120, self.game.HEIGHT // 2 + 20, 100, 40)
        no_rect = pygame.Rect(self.game.WIDTH // 2 + 20, self.game.HEIGHT // 2 + 20, 100, 40)

        def event_handler(event):
            nonlocal selected
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    selected = 0
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    selected = 1
                elif event.key == pygame.K_y:
                    return True
                elif event.key == pygame.K_n:
                    return False
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return selected == 0
                elif event.key == pygame.K_ESCAPE:
                    return False  # Esc默认选择否
            if event.type == pygame.MOUSEBUTTONDOWN:
                if yes_rect.collidepoint(pygame.mouse.get_pos()):
                    return True
                elif no_rect.collidepoint(pygame.mouse.get_pos()):
                    return False
            return None
        
        while True:
            self.game.clock.tick(self.game.FPS)
            blink += 1
            
            # 处理事件
            result = self.handle_interface_events(event_handler)
            if result is not None:
                return result
            
            # 渐入
            if alpha < 200:
                alpha = min(200, alpha + 5)
            
            fade_surf.set_alpha(alpha)
            self.game.screen.blit(fade_surf, (0, 0))
            
            # 标题
            self.game.show_text_center("确认退出", self.game.font_l, self.game.COLORS['RED'], self.game.HEIGHT // 2 - 80)
            self.game.show_text_center("确定要退出游戏吗？", self.game.font_m, self.game.COLORS['WHITE'], self.game.HEIGHT // 2 - 20)
            
            # 按钮
            yes_rect = pygame.Rect(self.game.WIDTH // 2 - 120, self.game.HEIGHT // 2 + 20, 100, 40)
            no_rect = pygame.Rect(self.game.WIDTH // 2 + 20, self.game.HEIGHT // 2 + 20, 100, 40)
            self._draw_button(yes_rect,
                              self.game.COLORS['RED'] if selected == 0 else (100, 0, 0),
                              self.game.COLORS['WHITE'],
                              border_radius=10,
                              text="是",
                              text_color=self.game.COLORS['BLACK'] if selected == 0 and (blink // 30) % 2 == 0 else self.game.COLORS['WHITE'],
                              font=self.game.font_s)
            self._draw_button(no_rect,
                              self.game.COLORS['GREEN'] if selected == 1 else (0, 100, 0),
                              self.game.COLORS['WHITE'],
                              border_radius=10,
                              text="否",
                              text_color=self.game.COLORS['BLACK'] if selected == 1 and (blink // 30) % 2 == 0 else self.game.COLORS['WHITE'],
                              font=self.game.font_s)
            
            pygame.display.flip()
    
    def level_select_screen(self):
        """关卡选择界面"""
        scroll = 0
        blink = 0
        selected_level = 1
        max_level = 100  # 100个关卡
        page = 0  # 当前页码，每页显示10个关卡
        
        # 生成装饰性陨石（背景用，不参与游戏）
        deco_rocks = [
            {"x": random.randint(0, self.game.WIDTH), "y": random.randint(0, self.game.HEIGHT),
             "vx": random.uniform(-0.4, 0.4), "vy": random.uniform(0.3, 0.9),
             "kind": random.randint(0, 1), "a": random.uniform(0, 6.28),
             "rotation": 0, "rotation_speed": random.uniform(0.01, 0.04) * random.choice([1, -1])}
            for _ in range(6)
        ]
        
        def event_handler(event):
            nonlocal selected_level, page
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    # 上一页，第一页时跳转到最后一页
                    if page > 0:
                        page -= 1
                    else:
                        page = (max_level - 1) // 10
                    selected_level = page * 10 + 1
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    # 下一页，最后一页时跳转到第一页
                    if page < (max_level - 1) // 10:
                        page += 1
                    else:
                        page = 0
                    selected_level = page * 10 + 1
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    # 上一个关卡，第一关时循环到最后一关
                    if selected_level > page * 10 + 1:
                        selected_level -= 1
                    else:
                        # 计算当前页的最后一个关卡
                        last_level = min((page + 1) * 10, max_level)
                        selected_level = last_level
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    # 下一个关卡，最后一关时循环到第一关
                    # 计算当前页的最后一个关卡
                    last_level = min((page + 1) * 10, max_level)
                    if selected_level < last_level:
                        selected_level += 1
                    else:
                        selected_level = page * 10 + 1
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    # 选择关卡
                    return selected_level
                elif event.key == pygame.K_ESCAPE:
                    # 返回主界面
                    return 0
            # 鼠标点击检测
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                # 检测返回按钮
                back_rect = pygame.Rect(10, 10, 100, 40)
                if back_rect.collidepoint(mouse_x, mouse_y):
                    return 0
                # 检测翻页按钮
                left_rect = pygame.Rect(50, self.game.HEIGHT // 2 - 20, 60, 40)
                right_rect = pygame.Rect(self.game.WIDTH - 110, self.game.HEIGHT // 2 - 20, 60, 40)
                if left_rect.collidepoint(mouse_x, mouse_y):
                    # 点击左箭头，第一页时跳转到最后一页
                    if page > 0:
                        page -= 1
                    else:
                        page = (max_level - 1) // 10
                    selected_level = page * 10 + 1
                elif right_rect.collidepoint(mouse_x, mouse_y):
                    # 点击右箭头，最后一页时跳转到第一页
                    if page < (max_level - 1) // 10:
                        page += 1
                    else:
                        page = 0
                    selected_level = page * 10 + 1
                # 检测关卡按钮
                for i in range(10):
                    level_num = page * 10 + i + 1
                    if level_num > max_level:
                        break
                    x = 100 + (i % 5) * 100
                    y = 150 + (i // 5) * 80
                    level_rect = pygame.Rect(x - 30, y - 30, 60, 60)
                    if level_rect.collidepoint(mouse_x, mouse_y):
                        if selected_level == level_num:
                            # 已经选择了该关卡，直接进入
                            return selected_level
                        else:
                            # 选择该关卡，但不进入
                            selected_level = level_num
            return None
        
        while True:
            self.game.clock.tick(self.game.FPS)
            scroll += 1
            blink += 1
            
            # 处理事件
            result = self.handle_interface_events(event_handler)
            if result is not None:
                return result
            
            self.game.draw_background(scroll)
            
            # 背景装饰陨石（半透明）
            rock_surf = pygame.Surface((self.game.WIDTH, self.game.HEIGHT), pygame.SRCALPHA)
            for r in deco_rocks:
                r["x"] = (r["x"] + r["vx"]) % self.game.WIDTH
                r["y"] = (r["y"] + r["vy"]) % self.game.HEIGHT
                r["rotation"] += r["rotation_speed"]
                self.game.draw_enemy(rock_surf, int(r["x"]), int(r["y"]), r["kind"], r["rotation"])
            rock_surf.set_alpha(60)
            self.game.screen.blit(rock_surf, (0, 0))
            
            # 标题
            self.game.show_text_center("选择关卡", self.game.font_l, self.game.COLORS['CYAN'], 80)
            
            # 返回按钮
            back_surf = pygame.Surface((100, 40), pygame.SRCALPHA)
            pygame.draw.rect(back_surf, (0, 60, 120, 180), (0, 0, 100, 40), border_radius=10)
            pygame.draw.rect(back_surf, (0, 160, 255, 200), (0, 0, 100, 40), 2, border_radius=10)
            self.game.screen.blit(back_surf, (10, 10))
            back_text = self.game.font_s.render("返回", True, (255, 255, 255))
            self.game.screen.blit(back_text, (60 - back_text.get_width()//2, 30 - back_text.get_height()//2))
            
            # 翻页按钮
            # 左箭头
            left_surf = pygame.Surface((60, 40), pygame.SRCALPHA)
            pygame.draw.rect(left_surf, (0, 60, 120, 180), (0, 0, 60, 40), border_radius=10)
            pygame.draw.rect(left_surf, (0, 160, 255, 200), (0, 0, 60, 40), 2, border_radius=10)
            self.game.screen.blit(left_surf, (50, self.game.HEIGHT // 2 - 20))
            left_text = self.game.font_m.render("←", True, (255, 255, 255))
            self.game.screen.blit(left_text, (80 - left_text.get_width()//2, self.game.HEIGHT // 2 - left_text.get_height()//2))
            # 右箭头
            right_surf = pygame.Surface((60, 40), pygame.SRCALPHA)
            pygame.draw.rect(right_surf, (0, 60, 120, 180), (0, 0, 60, 40), border_radius=10)
            pygame.draw.rect(right_surf, (0, 160, 255, 200), (0, 0, 60, 40), 2, border_radius=10)
            self.game.screen.blit(right_surf, (self.game.WIDTH - 110, self.game.HEIGHT // 2 - 20))
            right_text = self.game.font_m.render("→", True, (255, 255, 255))
            self.game.screen.blit(right_text, (self.game.WIDTH - 80 - right_text.get_width()//2, self.game.HEIGHT // 2 - right_text.get_height()//2))
            
            # 关卡按钮
            for i in range(10):
                level_num = page * 10 + i + 1
                if level_num > max_level:
                    break
                x = 100 + (i % 5) * 100
                y = 150 + (i // 5) * 80
                if level_num == selected_level:
                    # 选中的关卡
                    pygame.draw.circle(self.game.screen, (255, 200, 0), (x, y), 30)
                    pygame.draw.circle(self.game.screen, (255, 255, 255), (x, y), 30, 2)
                    text = self.game.font_m.render(str(level_num), True, (0, 60, 120))
                else:
                    # 未选中的关卡
                    pygame.draw.circle(self.game.screen, (0, 100, 180), (x, y), 25)
                    pygame.draw.circle(self.game.screen, (0, 160, 255), (x, y), 25, 2)
                    text = self.game.font_s.render(str(level_num), True, (180, 220, 255))
                self.game.screen.blit(text, (x - text.get_width()//2, y - text.get_height()//2))
            
            # 页码
            page_text = self.game.font_s.render(f"第 {page + 1} / {((max_level - 1) // 10) + 1} 页", True, (255, 220, 100))
            self.game.screen.blit(page_text, (self.game.WIDTH//2 - page_text.get_width()//2, self.game.HEIGHT - 60))
            
            # 提示文字
            self.game.show_text_center("使用方向键或鼠标选择关卡", self.game.font_s, (180, 220, 255), self.game.HEIGHT - 30)
            
            pygame.display.flip()
    
    def start_screen(self):
        """开始界面"""
        scroll = 0
        blink = 0
        selected_mode = 0  # 0: 关卡模式, 1: 无尽模式
        
        # 生成装饰性陨石（背景用，不参与游戏）
        deco_rocks = [
            {"x": random.randint(0, self.game.WIDTH), "y": random.randint(0, self.game.HEIGHT),
             "vx": random.uniform(-0.4, 0.4), "vy": random.uniform(0.3, 0.9),
             "kind": random.randint(0, 1), "a": random.uniform(0, 6.28),
             "rotation": 0, "rotation_speed": random.uniform(0.01, 0.04) * random.choice([1, -1])}
            for _ in range(6)
        ]
        
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
                        pygame.quit(); sys.exit()
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
                btn_rect = pygame.Rect(self.game.WIDTH//2 - btn_width//2, btn_y, btn_width, btn_height)
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
            
            self.game.draw_background(scroll)
            
            # 背景装饰陨石（半透明）
            rock_surf = pygame.Surface((self.game.WIDTH, self.game.HEIGHT), pygame.SRCALPHA)
            for r in deco_rocks:
                r["x"] = (r["x"] + r["vx"]) % self.game.WIDTH
                r["y"] = (r["y"] + r["vy"]) % self.game.HEIGHT
                r["rotation"] += r["rotation_speed"]
                self.game.draw_enemy(rock_surf, int(r["x"]), int(r["y"]), r["kind"], r["rotation"])
            rock_surf.set_alpha(60)
            self.game.screen.blit(rock_surf, (0, 0))
            
            # 标题背景光晕
            glow = pygame.Surface((420, 100), pygame.SRCALPHA)
            for i in range(30, 0, -1):
                alpha = int(120 * i / 30)
                pygame.draw.ellipse(glow, (0, 180, 255, alpha),
                                    (30 - i, 20 - i//2, 360 + i*2, 60 + i))
            self.game.screen.blit(glow, (self.game.WIDTH//2 - 210, 80))
            
            # 标题文字（描边 + 主色）
            title = "飞机大战"
            for dx, dy, col in [(-2,2,(0,60,120)), (2,2,(0,60,120)),
                                 (-2,-2,(0,60,120)), (2,-2,(0,60,120))]:
                s = self.game.font_l.render(title, True, col)
                self.game.screen.blit(s, (self.game.WIDTH//2 - s.get_width()//2 + dx, 90 + dy))
            self.game.show_text_center(title, self.game.font_l, self.game.COLORS['CYAN'], 90)
            
            # 分隔线
            line_y = 200
            pygame.draw.line(self.game.screen, (0, 120, 180), (80, line_y), (self.game.WIDTH-80, line_y), 1)
            pygame.draw.line(self.game.screen, (0, 60, 100), (80, line_y+2), (self.game.WIDTH-80, line_y+2), 1)
            
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
                self.game.screen.blit(text, (x - text.get_width()//2, y - text.get_height()//2))
            
            # 模式提示
            if selected_mode == 0:
                mode_hint = self.game.font_s.render("选择关卡模式，进入详细的关卡选择界面", True, (255, 220, 100))
            else:
                mode_hint = self.game.font_s.render("选择无尽模式，挑战你的极限", True, (255, 220, 100))
            self.game.screen.blit(mode_hint, (self.game.WIDTH//2 - mode_hint.get_width()//2, 460))
            
            # 闪烁开始提示
            if (blink // 30) % 2 == 0:
                # 发光底
                btn_width, btn_height = 300, 50
                btn = pygame.Surface((btn_width, btn_height), pygame.SRCALPHA)
                pygame.draw.rect(btn, (255, 200, 0, 60), (0, 0, btn_width, btn_height), border_radius=25)
                pygame.draw.rect(btn, (255, 200, 0, 180), (0, 0, btn_width, btn_height), 2, border_radius=25)
                # 调整按钮位置，避免与关卡简介重叠
                btn_y = 580
                self.game.screen.blit(btn, (self.game.WIDTH//2 - btn_width//2, btn_y))
                # 确保文字在闪烁圆框的正中间
                # 调整文字位置，使其在圆框中看起来更居中
                text_y = btn_y + btn_height // 2 - 16
                self.game.show_text_center("按 Enter / 空格 开始", self.game.font_s, self.game.COLORS['YELLOW'], text_y)
            
            # 底部版本/装饰
            ver = self.game.font_s.render("v1.0", True, (60, 80, 120))
            self.game.screen.blit(ver, (self.game.WIDTH - ver.get_width() - 10, self.game.HEIGHT - 30))
            
            pygame.display.flip()
    
    def game_over_screen(self, player):
        """游戏结束界面"""
        alpha = 0
        fade_surf = pygame.Surface((self.game.WIDTH, self.game.HEIGHT))
        fade_surf.fill(self.game.COLORS['BLACK'])
        
        def event_handler(event):
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "main_menu"
                if event.key == pygame.K_ESCAPE:
                    if self.confirm_exit_screen():
                        pygame.quit(); sys.exit()
            return None
        
        while True:
            self.game.clock.tick(self.game.FPS)
            # 处理事件
            result = self.handle_interface_events(event_handler)
            if result is not None:
                return result
            
            # 渐入
            if alpha < 200:
                alpha = min(200, alpha + 5)
            
            fade_surf.set_alpha(alpha)
            self.game.screen.blit(fade_surf, (0, 0))
            
            self.game.show_text_center("游戏结束", self.game.font_l, self.game.COLORS['RED'], self.game.HEIGHT // 2 - 80)
            self.game.show_text_center(f"最终得分: {player.score}", self.game.font_m, self.game.COLORS['WHITE'], self.game.HEIGHT // 2 - 20)
            self.game.show_text_center("按 Enter / 空格 回到主界面", self.game.font_s, self.game.COLORS['YELLOW'], self.game.HEIGHT // 2 + 40)
            
            pygame.display.flip()
    
    def level_complete_screen(self, player, score_target):
        """关卡完成界面"""
        alpha = 0
        fade_surf = pygame.Surface((self.game.WIDTH, self.game.HEIGHT))
        fade_surf.fill(self.game.COLORS['BLACK'])
        
        def event_handler(event):
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "main_menu"
                if event.key == pygame.K_ESCAPE:
                    if self.confirm_exit_screen():
                        pygame.quit(); sys.exit()
            return None
        
        while True:
            self.game.clock.tick(self.game.FPS)
            # 处理事件
            result = self.handle_interface_events(event_handler)
            if result is not None:
                return result
            
            # 渐入
            if alpha < 200:
                alpha = min(200, alpha + 5)
            
            fade_surf.set_alpha(alpha)
            self.game.screen.blit(fade_surf, (0, 0))
            
            self.game.show_text_center("关卡完成！", self.game.font_l, self.game.COLORS['GREEN'], self.game.HEIGHT // 2 - 80)
            self.game.show_text_center(f"得分: {player.score} / {score_target}", self.game.font_m, self.game.COLORS['WHITE'], self.game.HEIGHT // 2 - 20)
            self.game.show_text_center("按 Enter / 空格 回到主界面", self.game.font_s, self.game.COLORS['YELLOW'], self.game.HEIGHT // 2 + 40)
            
            pygame.display.flip()
