import pygame
import sys
import os
import datetime
from assets import AssetManager
from constants import (
    COLORS,
    FPS,
    HEIGHT,
    MAX_ENEMIES,
    MAX_PARTICLES,
    MAX_LEVEL,
    METEORITE_DAMAGE_RANGES,
    METEORITE_SIZE_HP,
    METEORITE_SIZE_SCALE,
    METEORITE_SIZE_SCORE,
    METEORITE_SIZE_SPEEDS,
    RETURN_BUTTON_RECT,
    SHIELD_ALPHA,
    WIDTH,
)
from entities import Player
from effects import Effects
from interfaces import Interfaces
from renderer import Renderer
from rules import (
    ENDLESS_BASE_DIFFICULTY,
    ENDLESS_DIFFICULTY_INCREASE_INTERVAL,
    calculate_next_high_score_checkpoint,
    calculate_level_spawn_interval,
    calculate_score_target,
    increase_endless_difficulty,
    should_update_high_score_checkpoint,
)
from storage import HighScoreStore
from systems import GameSystems

def log(message):
    """输出日志到终端。"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

class Game:
    """游戏总控：负责初始化各子系统，并调度关卡、无尽模式和界面流程。"""

    def __init__(self, runtime_tools_factory=None):
        pygame.init()
        self.runtime_tools = None
        
        # 基础配置
        self.WIDTH, self.HEIGHT = WIDTH, HEIGHT
        self.FPS = FPS
        self.COLORS = COLORS
        self.SHIELD_ALPHA = SHIELD_ALPHA
        
        # 陨石等级配置：索引 0 最小，索引 4 最大。
        self.SIZE_SCALE = METEORITE_SIZE_SCALE
        self.SIZE_HP = METEORITE_SIZE_HP
        self.SIZE_SCORE = METEORITE_SIZE_SCORE
        self.SIZE_SPEEDS = METEORITE_SIZE_SPEEDS
        
        # 屏幕和时钟
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("飞机大战")
        self.clock = pygame.time.Clock()
        
        # 资源管理器负责字体、图片、子弹组、星空等加载和随机选择。
        base_dir = os.path.dirname(__file__)
        self.assets = AssetManager(self, base_dir)

        self.font_s = self.assets.load_font(24)
        self.font_s_bold = self.assets.load_font(24)
        try:
            self.font_s_bold.set_bold(True)
        except Exception:
            pass
        self.font_m = self.assets.load_font(40)
        self.font_l = self.assets.load_font(60)
        
        # 玩家飞机资源和像素级碰撞遮罩。
        self.PLAYER_IMG = self.assets.load_player_image()
        self.PLAYER_MASK = pygame.mask.from_surface(self.PLAYER_IMG, 127)
        self.RETURN_BUTTON_RECT = pygame.Rect(*RETURN_BUTTON_RECT)
        
        # 陨石原图缓存由资源管理器加载，缩放后的陨石图由渲染器按需缓存。
        self.METEORITE_IMG_CACHE = self.assets.load_meteorite_images()
        self.SCALED_METEORITE_CACHE = {}

        # 子弹图片仍挂在游戏对象上，兼容子弹构造时的访问方式。
        self.assets.load_bullet_images()
        self.BULLET_IMAGES = self.assets.bullet_images
        self.BULLET_IMAGE_GROUPS = self.assets.bullet_image_groups
        self.BULLET_GROUP_INDEXES = self.assets.bullet_group_indexes
        self.POWERUP_IMAGES = self.assets.load_powerup_images()
        
        # 星空背景
        self.stars = self.assets.create_stars(self.WIDTH, self.HEIGHT)
        
        # 系统运行参数，供规则系统和特效系统等子模块共享。
        self.MAX_ENEMIES = MAX_ENEMIES
        self.MAX_PARTICLES = MAX_PARTICLES
        self.DEBUG_COLLISION = False
        self.METEORITE_DAMAGE_RANGES = METEORITE_DAMAGE_RANGES
        self.high_score_store = HighScoreStore(base_dir, log)
        self.high_score = self.load_high_score()
        
        # 默认子弹遮罩，供没有图片的子弹使用。
        self.BULLET_MASK = self.assets.create_default_bullet_mask()
        
        # 子系统按职责拆分：特效、渲染、规则系统、界面。
        self.effects = Effects(self)
        self.renderer = Renderer(self)
        self.systems = GameSystems(self)
        self.interfaces = Interfaces(self)
        if runtime_tools_factory:
            self.runtime_tools = runtime_tools_factory(self, log)
        
        log("游戏初始化完成")
    
    def load_high_score(self):
        """从存储模块读取最高分。"""
        return self.high_score_store.load()

    def save_high_score(self):
        """通过存储模块保存最高分。"""
        self.high_score_store.save(self.high_score)

    def update_high_score(self, score):
        """在玩家刷新纪录时保存最高分。"""
        if self.runtime_tools and getattr(self.runtime_tools, "disables_high_score", lambda: False)():
            return False
        if score > self.high_score:
            self.high_score = score
            self.save_high_score()
            log(f"无尽模式最高记录: {self.high_score}")
            return True
        return False

    def toggle_debug_collision(self):
        """切换碰撞调试模式"""
        self.DEBUG_COLLISION = not self.DEBUG_COLLISION
        log(f"碰撞调试模式: {'启用' if self.DEBUG_COLLISION else '禁用'}")
        
    def reset_bullet_group_timer(self):
        """重置子弹图片组轮换计时器。"""
        self.assets.reset_bullet_group_timer()

    def update_bullet_group(self):
        """按固定间隔切换当前子弹图片组。"""
        self.assets.update_bullet_group(self.FPS)

    def get_bullet_image(self):
        """供子弹创建时获取当前子弹图片。"""
        return self.assets.get_bullet_image()

    def _get_random_meteorite_image(self):
        """供菜单背景陨石获取随机贴图。"""
        return self.assets.get_random_meteorite_image(self.METEORITE_IMG_CACHE)

    def level_select_screen(self):
        """关卡选择界面"""
        return self.interfaces.level_select_screen()
    
    def start_screen(self):
        """开始界面"""
        self.restore_runtime_tools_view()
        return self.interfaces.start_screen()

    def restore_runtime_tools_view(self):
        if self.runtime_tools and hasattr(self.runtime_tools, "restore_game_window"):
            self.runtime_tools.restore_game_window()
    
    def handle_events(self, dev_context=None):
        """处理游戏事件"""
        # 用逐个轮询的方式处理事件，避免一次性清空事件队列。
        event = pygame.event.poll()
        while event:
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if self.runtime_tools and self.runtime_tools.handle_event(event, dev_context):
                event = pygame.event.poll()
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.confirm_exit_screen():
                        pygame.quit(); sys.exit()
                    return "resume_game"
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.runtime_tools and hasattr(self.runtime_tools, "translate_game_mouse_pos"):
                    mouse_pos = self.runtime_tools.translate_game_mouse_pos(mouse_pos)
                if self.RETURN_BUTTON_RECT.collidepoint(mouse_pos):
                    return "main_menu"
            event = pygame.event.poll()
        return None
    
    def draw_game(self, player, bullets, enemies, particles, scroll, level=None, score_target=None, spawn_interval=None, endless_difficulty=None, powerups=None, dev_context=None):
        """按固定层级绘制当前帧。"""
        self.renderer.draw_background(scroll)
        
        for b in bullets:
            b.draw(self.screen)
        
        for e in enemies:
            e.draw(self.screen)

        if powerups:
            for powerup in powerups:
                powerup.draw(self.screen, self.font_s_bold)
        
        self.effects.draw_explosion(self.screen, particles)
        player.draw(self.screen)
        
        if level is not None and score_target is not None:
            self.renderer.draw_hud(player, level, score_target)
        else:
            if spawn_interval is None:
                spawn_interval = 55
            self.renderer.draw_endless_hud(player, spawn_interval, endless_difficulty)
        if self.runtime_tools:
            self.runtime_tools.draw_overlay(self.screen, dev_context)
    
    def game_screen(self, level):
        """游戏主界面"""
        self.current_level = level
        log(f"开始关卡 {level}")
        player = Player(self)
        if self.runtime_tools and hasattr(self.runtime_tools, "prepare_player"):
            self.runtime_tools.prepare_player(player)
        bullets = []
        enemies = []
        particles = []
        powerups = []
        scroll = 0
        spawn_timer = 0
        self.reset_bullet_group_timer()
        
        # 锁定上一屏残留的空格按下状态，避免进入关卡后立刻开火。
        ignore_space = pygame.key.get_pressed()[pygame.K_SPACE]
        
        # 关卡节奏和通关目标由规则模块统一计算。
        spawn_interval = calculate_level_spawn_interval(level)
        score_target = calculate_score_target(level)
        log(f"关卡 {level} 配置：生成间隔={spawn_interval}，目标分数={score_target}")
        
        running = True
        while running:
            self.clock.tick(self.FPS)
            scroll += 1
            self.update_bullet_group()
            dev_context = {
                "player": player,
                "bullets": bullets,
                "enemies": enemies,
                "particles": particles,
                "powerups": powerups,
                "difficulty": level,
            }
            
            # 事件处理
            result = self.handle_events(dev_context)
            if result == "main_menu":
                return "main_menu"
            if result == "resume_game":
                ignore_space = pygame.key.get_pressed()[pygame.K_SPACE]
            
            # 玩家输入
            keys = pygame.key.get_pressed()
            player.update(keys)
            if keys[pygame.K_SPACE]:
                if not ignore_space:
                    self.systems.player_shoot(player, bullets)
            else:
                ignore_space = False
            
            # 生成、更新、碰撞与道具逻辑交给规则系统。
            spawn_timer = self.systems.try_spawn_enemy(spawn_timer, spawn_interval, enemies)
            
            particles = self.systems.update_entities(bullets, enemies, particles, player)
            self.systems.update_powerups(powerups)
            
            particles = self.systems.handle_collisions(bullets, enemies, particles, player, difficulty=level, powerups=powerups)
            self.systems.handle_powerup_collisions(powerups, player)
            
            # 绘制入口保留在主流程，具体绘制实现交给渲染器、特效和实体。
            self.draw_game(player, bullets, enemies, particles, scroll, level, score_target, powerups=powerups, dev_context=dev_context)
            
            pygame.display.flip()
            
            # 检查是否达到目标分数
            if player.score >= score_target:
                log(f"关卡 {level} 完成！得分：{player.score}/{score_target}")
                if level >= MAX_LEVEL:
                    return player, "all_complete"
                return player, level + 1
            
            # 检查是否游戏结束
            if player.lives <= 0:
                log(f"关卡 {level} 失败！最终得分：{player.score}")
                return player, None
        
        return player, None
    
    def game_over_screen(self, player):
        """游戏结束界面"""
        return self.interfaces.game_over_screen(player)
    
    def level_complete_screen(self, player, score_target, prompt_text="按 回车 / 空格 进入下一关"):
        """关卡完成界面"""
        return self.interfaces.level_complete_screen(player, score_target, prompt_text)
    
    def confirm_exit_screen(self):
        """退出确认界面"""
        return self.interfaces.confirm_exit_screen()
    
    def endless_mode(self):
        """无尽模式"""
        log("开始无尽模式")
        self.current_level = 100
        player = Player(self)
        if self.runtime_tools and hasattr(self.runtime_tools, "prepare_player"):
            self.runtime_tools.prepare_player(player)
        player.is_new_high_score = False
        bullets = []
        enemies = []
        particles = []
        powerups = []
        
        scroll = 0
        spawn_timer = 0
        self.reset_bullet_group_timer()
        
        # 锁定上一屏残留的空格按下状态，避免进入无尽模式后立刻开火。
        ignore_space = pygame.key.get_pressed()[pygame.K_SPACE]
        
        # 无尽模式参数由规则模块提供，主循环只记录当前状态。
        endless_difficulty = ENDLESS_BASE_DIFFICULTY
        spawn_interval = calculate_level_spawn_interval(endless_difficulty)
        difficulty_timer = 0
        difficulty_increase_interval = ENDLESS_DIFFICULTY_INCREASE_INTERVAL
        previous_high_score = self.high_score
        next_high_score_checkpoint = calculate_next_high_score_checkpoint(previous_high_score)
        log(f"无尽模式初始配置：生成间隔={spawn_interval}")
        
        running = True
        while running:
            self.clock.tick(self.FPS)
            scroll += 1
            difficulty_timer += 1
            self.update_bullet_group()
            dev_context = {
                "player": player,
                "bullets": bullets,
                "enemies": enemies,
                "particles": particles,
                "powerups": powerups,
                "difficulty": endless_difficulty,
            }
            
            # 事件处理
            result = self.handle_events(dev_context)
            if result == "main_menu":
                return "main_menu"
            if result == "resume_game":
                ignore_space = pygame.key.get_pressed()[pygame.K_SPACE]
            
            # 玩家输入
            keys = pygame.key.get_pressed()
            player.update(keys)
            if keys[pygame.K_SPACE]:
                if not ignore_space:
                    self.systems.player_shoot(player, bullets)
            else:
                ignore_space = False
            
            # 随时间推进无尽难度，具体增长规则由规则模块决定。
            if difficulty_timer >= difficulty_increase_interval:
                difficulty_timer = 0
                endless_difficulty, spawn_interval = increase_endless_difficulty(endless_difficulty, spawn_interval)
                log(f"无尽模式难度增加：生成间隔={spawn_interval}")
            
            # 生成、更新、碰撞与道具逻辑交给规则系统。
            spawn_timer = self.systems.try_spawn_enemy(spawn_timer, spawn_interval, enemies)
            
            particles = self.systems.update_entities(bullets, enemies, particles, player)
            self.systems.update_powerups(powerups)
            
            particles = self.systems.handle_collisions(bullets, enemies, particles, player, difficulty=endless_difficulty, powerups=powerups)
            self.systems.handle_powerup_collisions(powerups, player)
            if should_update_high_score_checkpoint(player.score, previous_high_score, next_high_score_checkpoint):
                if self.update_high_score(player.score):
                    player.is_new_high_score = True
                next_high_score_checkpoint = calculate_next_high_score_checkpoint(player.score)
            
            # 绘制入口保留在主流程，具体绘制实现交给渲染器、特效和实体。
            self.draw_game(player, bullets, enemies, particles, scroll, spawn_interval=spawn_interval, endless_difficulty=endless_difficulty, powerups=powerups, dev_context=dev_context)
            
            pygame.display.flip()
            
            # 检查是否游戏结束
            if player.lives <= 0:
                log(f"无尽模式结束！最终得分：{player.score}")
                if self.update_high_score(player.score):
                    player.is_new_high_score = True
                player.show_high_score = True
                return player
        
        return player
    
    def run(self):
        """运行游戏"""
        while True:
            result = self.start_screen()
            
            if result == "endless":
                result = self.endless_mode()
                if result == "quit":
                    break
                if result == "main_menu":
                    continue
                action = self.game_over_screen(result)
                if action == "quit":
                    break
                if action == "main_menu":
                    continue
            else:
                level = result
                current_level = level
                
                while True:
                    game_result = self.game_screen(current_level)
                    if game_result == "quit":
                        break
                    if game_result == "main_menu":
                        break
                    
                    player, next_level = game_result
                    
                    if next_level == "all_complete":
                        self.level_complete_screen(
                            player,
                            calculate_score_target(current_level),
                            "按 回车 / 空格 回到主界面",
                        )
                        break
                    if next_level:
                        self.level_complete_screen(player, calculate_score_target(current_level))
                        current_level = next_level
                    else:
                        action = self.game_over_screen(player)
                        if action == "quit":
                            break
                        if action == "main_menu":
                            break
                        else:
                            current_level = level
                
                if game_result == "quit":
                    break
        pygame.quit()





if __name__ == "__main__":
    game = Game()
    game.run()
