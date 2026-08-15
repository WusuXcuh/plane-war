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
    """游戏总控。

    这里只负责搭建子系统、维护全局状态、调度界面流程和两个游戏模式。
    具体的资源加载、绘制、碰撞、道具、粒子效果等逻辑放在对应模块里，避免主文件继续膨胀。
    """

    def __init__(self, runtime_tools_factory=None):
        pygame.init()
        # 可选运行时工具由开发者入口注入；普通入口不导入也不依赖开发者代码。
        self.runtime_tools = None

        # 基础窗口配置从常量模块读取，并挂到游戏对象上供各子系统统一访问。
        self.WIDTH, self.HEIGHT = WIDTH, HEIGHT
        self.FPS = FPS
        self.COLORS = COLORS
        self.SHIELD_ALPHA = SHIELD_ALPHA

        # 陨石等级配置：索引 0 最小，索引 4 最大；实体和规则系统都通过这些数组取数值。
        self.SIZE_SCALE = METEORITE_SIZE_SCALE
        self.SIZE_HP = METEORITE_SIZE_HP
        self.SIZE_SCORE = METEORITE_SIZE_SCORE
        self.SIZE_SPEEDS = METEORITE_SIZE_SPEEDS

        # 屏幕和时钟只在游戏初始化时创建一次；开发者面板会临时调整窗口大小。
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("飞机大战")
        self.clock = pygame.time.Clock()

        # 资源管理器集中处理路径、字体、图片、子弹组和星空数据，游戏对象只保留结果引用。
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

        # 玩家飞机图片和像素级遮罩在这里创建一次，碰撞系统每帧复用，避免重复生成。
        self.PLAYER_IMG = self.assets.load_player_image()
        self.PLAYER_MASK = pygame.mask.from_surface(self.PLAYER_IMG, 127)
        self.RETURN_BUTTON_RECT = pygame.Rect(*RETURN_BUTTON_RECT)

        # 陨石原图缓存由资源管理器加载；缩放后的图片由渲染器按尺寸等级懒加载缓存。
        self.METEORITE_IMG_CACHE = self.assets.load_meteorite_images()
        self.SCALED_METEORITE_CACHE = {}

        # 子弹图片仍挂在游戏对象上，兼容子弹实体构造时读取当前子弹贴图的方式。
        self.assets.load_bullet_images()
        self.BULLET_IMAGES = self.assets.bullet_images
        self.BULLET_IMAGE_GROUPS = self.assets.bullet_image_groups
        self.BULLET_GROUP_INDEXES = self.assets.bullet_group_indexes
        self.POWERUP_IMAGES = self.assets.load_powerup_images()
        # 加载关卡按钮模板底图
        self.LEVEL_BUTTON_TEMPLATE = self.assets.load_level_button_template()
        self.LEVEL_BUTTON_IMAGES = {}

        # 星空背景
        self.stars = self.assets.create_stars(self.WIDTH, self.HEIGHT)

        # 系统运行参数由多个模块共享：数量上限防止实体过多导致卡顿，调试开关仅影响碰撞可视化。
        self.MAX_ENEMIES = MAX_ENEMIES
        self.MAX_PARTICLES = MAX_PARTICLES
        self.DEBUG_COLLISION = False
        self.METEORITE_DAMAGE_RANGES = METEORITE_DAMAGE_RANGES
        self.high_score_store = HighScoreStore(base_dir, log)
        self.high_score = self.load_high_score()

        # 默认子弹遮罩用于无贴图兜底；有贴图的子弹会在实体里使用自己的遮罩。
        self.BULLET_MASK = self.assets.create_default_bullet_mask()

        # 子系统按职责拆分：特效、渲染、规则系统、界面；主循环只调用它们的公开方法。
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
        """在普通无尽模式刷新纪录时保存最高分。

        开发者模式会禁用最高分写入，避免调试时加分、无敌或调速污染正式记录。
        """
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
        """回到主界面前，让可选运行时工具恢复普通窗口大小和显示状态。"""
        if self.runtime_tools and hasattr(self.runtime_tools, "restore_game_window"):
            self.runtime_tools.restore_game_window()

    def handle_events(self, dev_context=None):
        """处理游戏内通用事件，并优先交给运行时工具拦截。

        开发者面板的按钮和快捷键由 runtime_tools 先处理；未被拦截的事件才进入普通游戏逻辑。
        """
        # 用逐个轮询的方式处理事件，避免把界面层正在等待的事件一次性清空。
        event = pygame.event.poll()
        while event:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if self.runtime_tools and self.runtime_tools.handle_event(event, dev_context):
                event = pygame.event.poll()
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.confirm_exit_screen():
                        pygame.quit()
                        sys.exit()
                    return "resume_game"
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                # 运行时工具可能改变游戏画面在窗口里的位置，点击游戏内按钮前要换回游戏坐标。
                if self.runtime_tools and hasattr(self.runtime_tools, "translate_game_mouse_pos"):
                    mouse_pos = self.runtime_tools.translate_game_mouse_pos(mouse_pos)
                if self.RETURN_BUTTON_RECT.collidepoint(mouse_pos):
                    return "main_menu"
            event = pygame.event.poll()
        return None

    def draw_game(self, player, bullets, enemies, particles, scroll, level=None, score_target=None, spawn_interval=None, endless_difficulty=None, powerups=None, dev_context=None):
        """按固定层级绘制当前帧。

        绘制顺序会影响遮挡关系：背景先画，随后是子弹、陨石、道具、爆炸、玩家和界面信息。
        开发者面板最后绘制，保证它始终浮在游戏画面之上。
        """
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
        """运行一个关卡，并返回下一步流程。

        返回值含义：
        - "main_menu"：玩家点返回，回主界面。
        - (player, 下一关编号)：当前关卡完成，进入下一关。
        - (player, "all_complete")：第 100 关完成，显示最终通关提示。
        - (player, None)：玩家生命耗尽，进入游戏结束界面。
        """
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

        # 锁定上一屏残留的空格按下状态，避免按空格开始游戏后进入关卡立刻开火。
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

            # 事件处理可能会暂停、返回主界面，或被开发者面板完全拦截。
            result = self.handle_events(dev_context)
            if result == "main_menu":
                return "main_menu"
            if result == "resume_game":
                ignore_space = pygame.key.get_pressed()[pygame.K_SPACE]

            # 玩家移动由玩家实体处理；射击保留在系统层，方便统一生成多弹道子弹。
            keys = pygame.key.get_pressed()
            player.update(keys)
            if keys[pygame.K_SPACE]:
                if not ignore_space:
                    self.systems.player_shoot(player, bullets)
            else:
                ignore_space = False

            # 生成、更新、碰撞与道具逻辑交给规则系统，主循环只负责按顺序调度。
            spawn_timer = self.systems.try_spawn_enemy(spawn_timer, spawn_interval, enemies)

            particles = self.systems.update_entities(bullets, enemies, particles, player)
            self.systems.update_powerups(powerups)

            particles = self.systems.handle_collisions(bullets, enemies, particles, player, difficulty=level, powerups=powerups)
            self.systems.handle_powerup_collisions(powerups, player)

            # 绘制入口保留在主流程，具体绘制实现交给渲染器、特效和实体。
            self.draw_game(player, bullets, enemies, particles, scroll, level, score_target, powerups=powerups, dev_context=dev_context)

            pygame.display.flip()

            # 达到目标分数即通关；最高关卡完成后不再生成 101 关。
            if player.score >= score_target:
                log(f"关卡 {level} 完成！得分：{player.score}/{score_target}")
                if level >= MAX_LEVEL:
                    return player, "all_complete"
                return player, level + 1

            # 生命耗尽才算失败；开发者模式默认无敌时通常不会走到这里。
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
        """运行无尽模式，并在普通模式下维护最高记录。"""
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

        # 无尽模式参数由规则模块提供，主循环只记录当前难度、生成间隔和最高分检查点。
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

            # 事件处理可能会暂停、返回主界面，或被开发者面板完全拦截。
            result = self.handle_events(dev_context)
            if result == "main_menu":
                return "main_menu"
            if result == "resume_game":
                ignore_space = pygame.key.get_pressed()[pygame.K_SPACE]

            # 玩家移动由实体处理；射击继续交给系统层，保持关卡模式和无尽模式一致。
            keys = pygame.key.get_pressed()
            player.update(keys)
            if keys[pygame.K_SPACE]:
                if not ignore_space:
                    self.systems.player_shoot(player, bullets)
            else:
                ignore_space = False

            # 随时间推进无尽难度：规则模块决定增长间隔、生成间隔下降幅度和最低间隔。
            if difficulty_timer >= difficulty_increase_interval:
                difficulty_timer = 0
                endless_difficulty, spawn_interval = increase_endless_difficulty(endless_difficulty, spawn_interval)
                log(f"无尽模式难度增加：生成间隔={spawn_interval}")

            # 生成、更新、碰撞与道具逻辑交给规则系统；开发者工具可通过接口暂停或调速陨石。
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
            self.draw_game(
                player, bullets, enemies, particles, scroll, spawn_interval=spawn_interval, endless_difficulty=endless_difficulty, powerups=powerups, dev_context=dev_context
            )

            pygame.display.flip()

            # 无尽模式只有生命耗尽才结算；开发者模式不会写入最高记录。
            if player.lives <= 0:
                log(f"无尽模式结束！最终得分：{player.score}")
                if self.update_high_score(player.score):
                    player.is_new_high_score = True
                player.show_high_score = True
                return player

        return player

    def run(self):
        """游戏主流程。

        每轮都先显示主界面，再根据玩家选择进入关卡模式或无尽模式。
        关卡模式会在内部循环推进关卡；无尽模式结束后直接进入游戏结束界面。
        """
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
