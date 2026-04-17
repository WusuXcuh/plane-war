import pygame
import random
import sys
import math
import os
import datetime
from constants import WIDTH, HEIGHT, FPS, COLORS, RETURN_BUTTON_RECT, PLAYER_IMAGE
from entities import Player, Enemy, Bullet
from interfaces import Interfaces
from utils import create_button_surface, point_in_polygon

# 日志记录函数
def log(message):
    """记录日志到debug文件夹中的log.txt文件"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}\n"
    os.makedirs("debug", exist_ok=True)
    log_file_path = "debug/log.txt"
    
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(log_message)
    print(log_message.strip())
    
    # 检查日志行数并进行清理
    _cleanup_log_file(log_file_path)


def _cleanup_log_file(log_file_path):
    """清理日志文件：超过500行则删除第一行直至<=500行"""
    try:
        if not os.path.exists(log_file_path):
            return
        
        with open(log_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # 如果行数 > 500，保留最后500行（删除第一行直至<=500）
        if len(lines) > 500:
            lines = lines[-(500):]
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
    
    except Exception as e:
        # 日志清理异常不应中断主程序
        pass

class Game:
    def __init__(self):
        # 初始化 pygame
        pygame.init()
        
        # 游戏常量
        self.WIDTH, self.HEIGHT = WIDTH, HEIGHT
        self.FPS = FPS
        
        # 颜色定义
        self.COLORS = COLORS
        
        # 陨石大小配置（0=最小 … 4=最大）
        self.SIZE_SCALE = [0.135, 0.24, 0.36, 0.525, 0.75]      # 相对基础形状的缩放（缩小到30%）
        self.SIZE_HP = [1, 1, 2, 3, 5]                       # 血量
        self.SIZE_SCORE = [60, 50, 80, 120, 240]              # 得分翻倍（最小陨石60分，第二小陨石50分，中等大小陨石80分）
        self.SIZE_SPEEDS = [(3.2,5.5),(2.4,4.0),(1.7,3.2),(1.0,2.0),(0.6,1.2)]  # 速度范围
        
        # 屏幕和时钟
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("飞机大战")
        self.clock = pygame.time.Clock()
        
        # 字体
        self.font_s = self._load_font(24)
        self.font_m = self._load_font(40)
        self.font_l = self._load_font(60)
        
        # 加载玩家飞机图片
        self.PLAYER_IMG = self._load_player_image()
        self.PLAYER_MASK = pygame.mask.from_surface(self.PLAYER_IMG, 127)  # 降低阈值，确保更多像素被认为是实心的
        self.RETURN_BUTTON_RECT = pygame.Rect(*RETURN_BUTTON_RECT)
        
        # 加载陨石图片缓存
        self.METEORITE_IMG_CACHE = {}
        self._load_meteorite_images()
        
        # 星空背景
        self.stars = [(random.randint(0, self.WIDTH), random.randint(0, self.HEIGHT), random.random()) for _ in range(120)]
        
        # 数量限制，避免关卡末期陨石数量失控导致卡顿
        self.MAX_ENEMIES = 40
        self.MAX_PARTICLES = 120
        
        # 为子弹创建共享碰撞掩码
        bullet_surface = pygame.Surface((Bullet.W, Bullet.H), pygame.SRCALPHA)
        pygame.draw.rect(bullet_surface, (255, 255, 255, 255), (0, 0, Bullet.W, Bullet.H))
        self.BULLET_MASK = pygame.mask.from_surface(bullet_surface)
        
        # 界面管理
        self.interfaces = Interfaces(self)
        
        # 记录游戏初始化
        log("游戏初始化完成")
    
    def toggle_debug_collision(self):
        """切换碰撞调试模式"""
        self.DEBUG_COLLISION = not self.DEBUG_COLLISION
        log(f"碰撞调试模式: {'启用' if self.DEBUG_COLLISION else '禁用'}")
        
    def _load_font(self, size):
        """加载字体"""
        # 尝试加载系统中常用的中文字体
        font_paths = [
            "C:/Windows/Fonts/simhei.ttf",  # 黑体
            "C:/Windows/Fonts/simsun.ttc",  # 宋体
            "C:/Windows/Fonts/microsoftyahei.ttf",  # 微软雅黑
            "C:/Windows/Fonts/msyh.ttf",  # 微软雅黑
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font = pygame.font.Font(font_path, size)
                    # 测试字体是否能渲染中文
                    test_surface = font.render("测试", True, (255, 255, 255))
                    if test_surface.get_width() > 0:
                        log(f"成功加载中文字体: {font_path}")
                        return font
            except Exception as e:
                log(f"尝试加载字体 {font_path} 失败: {e}")
                pass
        
        # 如果没有找到中文字体，尝试使用系统默认字体
        try:
            font = pygame.font.SysFont(None, size)
            log(f"使用系统默认字体，大小: {size}")
            return font
        except Exception as e:
            log(f"加载系统默认字体失败: {e}")
            
        # 如果所有尝试都失败，返回一个基本的字体对象
        class DummyFont:
            def render(self, text, antialias, color):
                surface = pygame.Surface((len(text) * 10, size))
                surface.fill((0, 0, 0))
                return surface
        log("使用虚拟字体")
        return DummyFont()
    
    def _load_player_image(self):
        """加载玩家飞机图片，保持原始长宽比例"""
        path = os.path.join(os.path.dirname(__file__), PLAYER_IMAGE)
        raw = pygame.image.load(path).convert_alpha()
        
        # 计算原始图片的宽高比
        original_width, original_height = raw.get_size()
        aspect_ratio = original_width / original_height
        
        # 设定目标宽度，保持比例计算高度
        target_width = 60
        target_height = int(target_width / aspect_ratio)
        
        log(f"飞机图片原始尺寸: {original_width}x{original_height}, 缩放后: {target_width}x{target_height}")
        
        return pygame.transform.smoothscale(raw, (target_width, target_height))
    
    def _load_meteorite_images(self):
        """加载所有陨石图片"""
        meteorite_dir = os.path.join(os.path.dirname(__file__), "pictures/meteorite")
        if not os.path.exists(meteorite_dir):
            log(f"陨石图片目录不存在: {meteorite_dir}")
            return
        
        # 获取目录中所有 PNG 文件
        image_files = [f for f in os.listdir(meteorite_dir) if f.endswith('.png')]
        if not image_files:
            log("陨石目录中没有找到任何图片")
            return
        
        # 加载所有图片
        for img_file in image_files:
            try:
                path = os.path.join(meteorite_dir, img_file)
                img = pygame.image.load(path).convert_alpha()
                self.METEORITE_IMG_CACHE[img_file] = img
                log(f"成功加载陨石图片: {img_file}")
            except Exception as e:
                log(f"加载陨石图片 {img_file} 失败: {e}")
    
    def _get_random_meteorite_image(self):
        """获取随机陨石图片"""
        if not self.METEORITE_IMG_CACHE:
            return None
        return random.choice(list(self.METEORITE_IMG_CACHE.values()))
    
    def draw_player(self, surf, cx, cy):
        """绘制玩家飞机"""
        w, h = self.PLAYER_IMG.get_size()
        surf.blit(self.PLAYER_IMG, (cx - w // 2, cy - h // 2))
    
    def draw_enemy(self, surf, cx, cy, size=1, rotation=0, img=None):
        """绘制敌人（陨石）"""
        if img:
            # 使用图片绘制陨石
            sc = self.SIZE_SCALE[size]
            img_width, img_height = img.get_size()
            
            # 计算缩放后的尺寸
            scaled_width = int(img_width * sc)
            scaled_height = int(img_height * sc)
            
            # 缩放图片
            scaled_img = pygame.transform.smoothscale(img, (scaled_width, scaled_height))
            
            # 旋转图片（转换为度数）
            rotation_deg = int(rotation * 180 / math.pi)
            rotated_img = pygame.transform.rotate(scaled_img, rotation_deg)
            
            # 获取旋转后的矩形
            rect = rotated_img.get_rect(center=(cx, cy))
            
            # 绘制到表面
            surf.blit(rotated_img, rect.topleft)
        else:
            # 如果没有图片，使用多边形作为备选方案
            self._draw_enemy_polygon(surf, cx, cy, size, rotation)
    
    def _draw_enemy_polygon(self, surf, cx, cy, size=1, rotation=0):
        """绘制敌人多边形（备选方案）"""
        sc = self.SIZE_SCALE[size]
        
        # 颜色随大小变深
        colors = [
            ((140,110, 75),( 80, 58, 32),(195,165,120)),  # 0 最小
            ((120, 90, 60),( 70, 50, 30),(180,150,110)),  # 1
            ((108, 76, 44),( 60, 40, 18),(168,132, 90)),  # 2
            (( 95, 62, 30),( 50, 30, 10),(155,115, 68)),  # 3
            (( 80, 48, 20),( 38, 20,  5),(135, 95, 50)),  # 4 最大
        ]
        ROCK, ROCK_DARK, ROCK_LIT = colors[size]
        
        def sp(x, y):
            # 应用旋转
            angle = rotation
            rx = x * math.cos(angle) - y * math.sin(angle)
            ry = x * math.sin(angle) + y * math.cos(angle)
            return (cx + int(rx * sc), cy + int(ry * sc))
        
        pts = [sp(-13,-24), sp(8,-26), sp(24,-10), sp(26, 8),
               sp(13, 26), sp(-8,29), sp(-24, 13), sp(-29,-5)]
        pygame.draw.polygon(surf, ROCK, pts)
        lw = max(1, int(2 * sc))
        pygame.draw.polygon(surf, ROCK_DARK, pts, lw)
        
        # 坑洞
        pygame.draw.circle(surf, ROCK_DARK, sp(5, -5), max(1, int(6 * sc)))
        pygame.draw.circle(surf, ROCK_DARK, sp(-10, 10), max(1, int(4 * sc)))
        if size >= 2:
            pygame.draw.circle(surf, ROCK_DARK, sp(3, 18), max(1, int(3 * sc)))
        if size >= 3:
            pygame.draw.circle(surf, ROCK_DARK, sp(-5, -16), max(1, int(3 * sc)))
        
        # 高光
        pygame.draw.polygon(surf, ROCK_LIT, [sp(-10,-18), sp(3,-21), sp(10,-8), sp(-3,-5)])
    
    def draw_bullet(self, surf, x, y, friendly=True):
        """绘制子弹"""
        if friendly:
            pygame.draw.rect(surf, self.COLORS['YELLOW'], (x - 2, y - 8, 4, 16), border_radius=2)
            glow = pygame.Surface((10, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 255, 0, 60), (0, 0, 10, 20))
            surf.blit(glow, (x - 5, y - 10))
        else:
            # 碎石外观（小而清晰）
            ROCK = (150, 115, 75)
            ROCK_DARK = (80, 55, 30)
            ROCK_LIT = (210, 175, 120)
            pts = [
                (x - 2, y - 4),
                (x + 2, y - 5),
                (x + 5, y - 1),
                (x + 4, y + 3),
                (x + 1, y + 5),
                (x - 3, y + 3),
                (x - 5, y - 0),
            ]
            pygame.draw.polygon(surf, ROCK, pts)
            pygame.draw.polygon(surf, ROCK_DARK, pts, 1)
            pygame.draw.line(surf, ROCK_LIT, (x - 1, y - 3), (x + 2, y - 4), 1)
    
    def draw_explosion(self, surf, particles):
        """绘制爆炸效果"""
        for p in particles:
            alpha = max(0, int(255 * p["life"] / p["max_life"]))
            r = max(1, int(p["r"] * p["life"] / p["max_life"]))
            c = (*p["color"], alpha)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, c, (r, r), r)
            surf.blit(s, (int(p["x"]) - r, int(p["y"]) - r))
    
    def draw_background(self, scroll):
        """绘制背景"""
        self.screen.fill(self.COLORS['BLACK'])
        for sx, sy, sp in self.stars:
            ny = (sy + scroll * sp * 0.5) % self.HEIGHT
            b = int(100 + 155 * sp)
            r = 1 if sp < 0.5 else 2
            pygame.draw.circle(self.screen, (b, b, b), (sx, int(ny)), r)
    
    def make_explosion(self, cx, cy, n=24, colors=None, r_range=(4, 12), speed_range=(1.5, 5)):
        """创建爆炸粒子"""
        if colors is None:
            colors = [self.COLORS['RED'], self.COLORS['ORANGE'], self.COLORS['YELLOW'], self.COLORS['WHITE']]
        particles = []
        for _ in range(n):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(*speed_range)
            life = random.randint(20, 45)
            particles.append({
                "x": cx, "y": cy,
                "vx": speed * math.cos(angle),
                "vy": speed * math.sin(angle),
                "r": random.randint(*r_range),
                "color": random.choice(colors),
                "life": life, "max_life": life,
            })
        return particles
    
    def update_particles(self, particles):
        """更新粒子状态"""
        alive = []
        for p in particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.15   # 重力
            p["life"] -= 1
            if p["life"] > 0:
                alive.append(p)
        return alive
    
    def draw_hud(self, player, level, score_target):
        """绘制游戏界面信息"""
        # 分数
        txt = self.font_s.render(f"得分: {player.score}", True, self.COLORS['WHITE'])
        self.screen.blit(txt, (15, 15))
        # 关卡
        txt = self.font_s.render(f"关卡: {level}", True, self.COLORS['YELLOW'])
        self.screen.blit(txt, (self.WIDTH // 2 - txt.get_width() // 2, 15))
        # 生命
        txt = self.font_s.render(f"命: {player.lives}", True, self.COLORS['CYAN'])
        self.screen.blit(txt, (self.WIDTH - txt.get_width() - 15, 15))
        # 目标分数
        progress = min(100, int(player.score / score_target * 100))
        txt = self.font_s.render(f"目标: {player.score}/{score_target} ({progress}%)", True, self.COLORS['GREEN'])
        self.screen.blit(txt, (15, 50))
        self._draw_return_button()
    
    def draw_endless_hud(self, player, spawn_interval):
        """绘制无尽模式界面信息"""
        # 难度（放在左上角）
        difficulty = 100 - ((spawn_interval - 15) / 40 * 100)
        difficulty = min(100, max(0, int(difficulty)))
        txt = self.font_s.render(f"难度: {difficulty}", True, self.COLORS['ORANGE'])
        self.screen.blit(txt, (15, 15))
        # 分数
        txt = self.font_s.render(f"得分: {player.score}", True, self.COLORS['WHITE'])
        self.screen.blit(txt, (15, 50))
        # 模式
        txt = self.font_s.render("模式: 无尽", True, self.COLORS['MAGENTA'])
        self.screen.blit(txt, (self.WIDTH // 2 - txt.get_width() // 2, 15))
        # 生命
        txt = self.font_s.render(f"命: {player.lives}", True, self.COLORS['CYAN'])
        self.screen.blit(txt, (self.WIDTH - txt.get_width() - 15, 15))
        self._draw_return_button()
    
    def _draw_return_button(self):
        """绘制统一的返回按钮"""
        btn_surface = create_button_surface((self.RETURN_BUTTON_RECT.width, self.RETURN_BUTTON_RECT.height),
                                           (255, 100, 100, 120),
                                           (255, 150, 150, 200),
                                           border_radius=8)
        self.screen.blit(btn_surface, self.RETURN_BUTTON_RECT.topleft)
        return_txt = self.font_s.render("返回", True, self.COLORS['WHITE'])
        self.screen.blit(return_txt, (
            self.RETURN_BUTTON_RECT.centerx - return_txt.get_width() // 2,
            self.RETURN_BUTTON_RECT.centery - return_txt.get_height() // 2
        ))

    def _player_shoot(self, player, bullets):
        """处理玩家射击逻辑"""
        if player.try_shoot():
            bullet_x = player.x + player.W // 2
            bullet_y = player.y - 10
            bullets.append(Bullet(bullet_x, bullet_y, self))

    def _calculate_level_spawn_interval(self, level):
        return max(10, 55 - (level - 1) // 10 * 5)

    def _calculate_score_target(self, level):
        return 1000 + (level - 1) * 1000

    def _calculate_endless_difficulty(self, spawn_interval):
        base_spawn_interval = 55
        min_spawn_interval = 15
        difficulty = int(1 + (base_spawn_interval - spawn_interval) / (base_spawn_interval - min_spawn_interval) * 9)
        return max(1, min(10, difficulty))

    def _try_spawn_enemy(self, spawn_timer, spawn_interval, enemies):
        """Generate a new enemy when the timer reaches the spawn interval."""
        spawn_timer += 1
        if spawn_timer >= spawn_interval:
            spawn_timer = 0
            if len(enemies) < self.MAX_ENEMIES:
                enemies.append(Enemy(self))
        return spawn_timer

    def show_text_center(self, text, font, color, y):
        """在屏幕中央显示文字"""
        s = font.render(text, True, color)
        self.screen.blit(s, (self.WIDTH // 2 - s.get_width() // 2, y))
    
    def level_select_screen(self):
        """关卡选择界面"""
        return self.interfaces.level_select_screen()
    
    def start_screen(self):
        """开始界面"""
        return self.interfaces.start_screen()
    
    def handle_events(self):
        """处理游戏事件"""
        # 处理事件，但不清空事件队列
        event = pygame.event.poll()
        while event:
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.confirm_exit_screen():
                        pygame.quit(); sys.exit()
            # 鼠标点击检测
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.RETURN_BUTTON_RECT.collidepoint(pygame.mouse.get_pos()):
                    return "main_menu"
            event = pygame.event.poll()
        return None
    
    def update_entities(self, bullets, enemies, particles, player):
        """更新游戏实体"""
        # 更新子弹
        for b in bullets[:]:
            if b.update():
                bullets.remove(b)
        
        # 更新陨石
        for e in enemies[:]:
            if e.update():
                enemies.remove(e)
        
        # 更新粒子
        particles = self.update_particles(particles)
        if len(particles) > self.MAX_PARTICLES:
            particles = particles[-self.MAX_PARTICLES:]
        
        # 玩家无敌状态由Player类自己更新
        
        return particles
    
    def handle_collisions(self, bullets, enemies, particles, player, difficulty=1):
        """处理碰撞检测"""
        # 限制碎裂体和概率扩展，避免高级关卡数量爆炸式增长
        clamped_difficulty = min(max(difficulty, 1), 12)
        base_probability = 0.5
        max_probability = 0.9
        spawn_probability = min(max_probability, base_probability + (clamped_difficulty - 1) * 0.1)
        piece_multiplier = 1 + min(1.5, (clamped_difficulty - 1) * 0.1)
        # 碰撞检测：玩家子弹 vs 敌机
        for b in bullets[:]:
            for e in enemies[:]:
                # 首先进行矩形碰撞检测（快速筛选），稍微扩大检测范围以防止子弹穿过
                expanded_e_x = e.x - 5
                expanded_e_y = e.y - 5
                expanded_e_w = e.W + 10
                expanded_e_h = e.H + 10
                
                if b.x + b.W > expanded_e_x and b.x < expanded_e_x + expanded_e_w and b.y + b.H > expanded_e_y and b.y < expanded_e_y + expanded_e_h:
                    # 子弹与陨石的碰撞检测（使用mask）
                    if e.meteorite_img:
                        try:
                            bullet_cx = b.x + b.W // 2
                            bullet_cy = b.y + b.H // 2
                            center_x = e.x + e.W // 2
                            center_y = e.y + e.H // 2
                            
                            if hasattr(e, 'rotated_mask') and e.rotated_mask is not None and e.rotated_rect is not None:
                                rotated_mask = e.rotated_mask
                                rotated_rect = e.rotated_rect
                            else:
                                sc = self.SIZE_SCALE[e.kind]
                                img_width, img_height = e.meteorite_img.get_size()
                                scaled_width = int(img_width * sc)
                                scaled_height = int(img_height * sc)
                                scaled_img = pygame.transform.smoothscale(e.meteorite_img, (scaled_width, scaled_height))
                                rotation_deg = int(e.rotation * 180 / math.pi)
                                rotated_img = pygame.transform.rotate(scaled_img, rotation_deg)
                                rotated_mask = pygame.mask.from_surface(rotated_img)
                                rotated_rect = rotated_img.get_rect(center=(center_x, center_y))
                            
                            offset_x = int(b.x) - rotated_rect.left
                            offset_y = int(b.y) - rotated_rect.top
                            
                            if rotated_mask.overlap(self.BULLET_MASK, (offset_x, offset_y)):
                                if b in bullets:
                                    bullets.remove(b)
                                e.hp -= 1
                                collision_x = bullet_cx
                                collision_y = bullet_cy
                                particles += self.make_explosion(collision_x, collision_y, n=8, r_range=(2, 6))
                        except (pygame.error, ValueError, MemoryError) as ex:
                            log(f"子弹-陨石 mask 碰撞失败 (种类{e.kind}): {ex}")
                            bullet_cx = b.x + b.W // 2
                            bullet_cy = b.y + b.H // 2
                            center_x = e.x + e.W // 2
                            center_y = e.y + e.H // 2
                            dist = math.sqrt((bullet_cx - center_x)**2 + (bullet_cy - center_y)**2)
                            if dist < max(e.W, e.H) // 2:
                                if b in bullets:
                                    bullets.remove(b)
                                e.hp -= 1
                                particles += self.make_explosion(bullet_cx, bullet_cy, n=8, r_range=(2, 6))
                    # 检查陨石是否被击碎
                        if e.hp <= 0:
                            # 爆炸效果（在碰撞点）
                            particles += self.make_explosion(collision_x, collision_y, n=30, r_range=(5, 15))
                            # 根据陨石大小给予不同分数
                            player.score += self.SIZE_SCORE[e.kind]
                            
                            # 生成小陨石：根据难度调整概率和数量
                            if e.kind > 1:  # 只有大于第二小的陨石才会碎裂
                                # 生成小陨石的概率：根据难度调整
                                if random.random() < spawn_probability:
                                    # 计算生成小陨石的数量，根据难度调整
                                    base_max_pieces = int(min(4, e.kind * 1.5))
                                    base_min_pieces = max(1, e.kind - 1)
                                    max_pieces = max(1, min(4, int(base_max_pieces * piece_multiplier)))
                                    min_pieces = max(1, min(max_pieces, int(base_min_pieces * piece_multiplier * 0.6)))
                                    if min_pieces > max_pieces:
                                        min_pieces = max_pieces
                                    piece_count = random.randint(min_pieces, max_pieces)
                                    
                                    # 生成小陨石
                                    for _ in range(piece_count):
                                        # 新陨石必须比原陨石小（小于原陨石等级）
                                        new_kind = random.randint(0, e.kind - 1)
                                        # 计算新陨石的位置（在原陨石附近）
                                        new_x = e.x + random.randint(-e.W//4, e.W//4)
                                        new_y = e.y + random.randint(-e.H//4, e.H//4)
                                        # 创建新陨石并继承父陨石图片，确保碎裂后真正更小
                                        new_enemy = Enemy(self, kind=new_kind, meteorite_img=e.meteorite_img)
                                        new_enemy.x = new_x
                                        new_enemy.y = new_y
                                        # 调整新陨石的速度：向下方-90~90度内的随机角度，速度为原速度的2.5倍
                                        # 计算向下方的随机角度（-90~90度，即-pi/2到pi/2弧度）
                                        angle = random.uniform(-math.pi/2, math.pi/2)
                                        # 计算原速度的大小
                                        original_speed = math.sqrt(e.vx**2 + e.vy**2)
                                        # 新速度为原速度的1.75倍
                                        new_speed = original_speed * 1.75
                                        # 根据角度计算新的速度分量
                                        new_enemy.vx = new_speed * math.sin(angle)  # 水平方向
                                        new_enemy.vy = new_speed * math.cos(angle)  # 垂直方向（向下）
                                        # 确保y方向速度为正（向下）
                                        if new_enemy.vy < 0:
                                            new_enemy.vy = -new_enemy.vy
                                        enemies.append(new_enemy)
                            
                            enemies.remove(e)
                    break
        
        # 碰撞检测：陨石 vs 玩家
        if player.invincible == 0:  # 只有当玩家不在无敌状态时才检测碰撞
            for e in enemies[:]:
                # 首先进行矩形碰撞检测（快速筛选）
                if player.x + player.W > e.x and player.x < e.x + e.W and player.y + player.H > e.y and player.y < e.y + e.H:
                    # 玩家与陨石的碰撞检测（使用mask）
                    if e.meteorite_img:
                        try:
                            if hasattr(e, 'rotated_mask') and e.rotated_mask is not None and e.rotated_rect is not None:
                                rotated_mask = e.rotated_mask
                                rotated_rect = e.rotated_rect
                            else:
                                sc = self.SIZE_SCALE[e.kind]
                                img_width, img_height = e.meteorite_img.get_size()
                                scaled_width = int(img_width * sc)
                                scaled_height = int(img_height * sc)
                                scaled_img = pygame.transform.smoothscale(e.meteorite_img, (scaled_width, scaled_height))
                                rotation_deg = int(e.rotation * 180 / math.pi)
                                rotated_img = pygame.transform.rotate(scaled_img, rotation_deg)
                                rotated_mask = pygame.mask.from_surface(rotated_img)
                                rotated_rect = rotated_img.get_rect(center=(e.x + e.W // 2, e.y + e.H // 2))
                            
                            offset_x = int(player.x) - int(rotated_rect.left)
                            offset_y = int(player.y) - int(rotated_rect.top)
                            collision_detected = self.PLAYER_MASK.overlap(rotated_mask, (offset_x, offset_y))
                            
                            if collision_detected:
                                explosion_x = e.x + e.W // 2
                                explosion_y = e.y + e.H // 2
                                particles += self.make_explosion(explosion_x, explosion_y, n=40, r_range=(8, 20))
                                log(f"飞机被陨石砸到（Mask碰撞）！当前分数：{player.score}")
                                player.invincible = 120
                                player.can_shoot = False
                                player.lives -= 1
                                enemies.remove(e)
                                break
                            else:
                                center_x = e.x + e.W // 2
                                center_y = e.y + e.H // 2
                                player_cx = player.x + player.W // 2
                                player_cy = player.y + player.H // 2
                                dist = math.sqrt((player_cx - center_x)**2 + (player_cy - center_y)**2)
                                collision_radius = max(e.W, e.H) * 0.75
                                if dist < collision_radius:
                                    explosion_x = e.x + e.W // 2
                                    explosion_y = e.y + e.H // 2
                                    particles += self.make_explosion(explosion_x, explosion_y, n=40, r_range=(8, 20))
                                    log(f"飞机被陨石砸到（距离碰撞）！当前分数：{player.score}")
                                    player.invincible = 120
                                    player.can_shoot = False
                                    player.lives -= 1
                                    enemies.remove(e)
                                    break
                        except (pygame.error, ValueError, MemoryError, IndexError) as ex:
                            log(f"玩家-陨石碰撞异常 (种类{e.kind}): {ex}, 使用距离检测")
                            center_x = e.x + e.W // 2
                            center_y = e.y + e.H // 2
                            player_cx = player.x + player.W // 2
                            player_cy = player.y + player.H // 2
                            dist = math.sqrt((player_cx - center_x)**2 + (player_cy - center_y)**2)
                            collision_radius = max(e.W, e.H) * 0.75
                            if dist < collision_radius:
                                explosion_x = e.x + e.W // 2
                                explosion_y = e.y + e.H // 2
                                particles += self.make_explosion(explosion_x, explosion_y, n=40, r_range=(8, 20))
                                log(f"飞机被陨石砸到（异常恢复）！当前分数：{player.score}")
                                player.invincible = 120
                                player.can_shoot = False
                                player.lives -= 1
                                enemies.remove(e)
                                break
        else:
            # 无敌状态：陨石直接穿过玩家
            pass
        
        return particles
    
    def draw_game(self, player, bullets, enemies, particles, scroll, level=None, score_target=None, spawn_interval=None):
        """绘制游戏界面"""
        # 绘制背景
        self.draw_background(scroll)
        
        # 绘制子弹
        for b in bullets:
            b.draw(self.screen)
        
        # 绘制陨石
        for e in enemies:
            e.draw(self.screen)
        
        # 绘制爆炸效果
        self.draw_explosion(self.screen, particles)
        
        # 绘制玩家
        player.draw(self.screen)
        
        # 绘制HUD
        if level is not None and score_target is not None:
            self.draw_hud(player, level, score_target)
        else:
            # 无尽模式HUD
            if spawn_interval is None:
                spawn_interval = 55
            self.draw_endless_hud(player, spawn_interval)
    
    def game_screen(self, level):
        """游戏主界面"""
        log(f"开始关卡 {level}")
        player = Player(self)
        bullets = []
        enemies = []
        particles = []
        
        scroll = 0
        spawn_timer = 0
        
        # 进入新关时先锁定空格，避免上一屏空格按下状态导致直接发射
        ignore_space = pygame.key.get_pressed()[pygame.K_SPACE]
        
        # 根据关卡号动态计算难度
        spawn_interval = self._calculate_level_spawn_interval(level)
        score_target = self._calculate_score_target(level)
        log(f"关卡 {level} 配置：生成间隔={spawn_interval}，目标分数={score_target}")
        
        running = True
        while running:
            self.clock.tick(self.FPS)
            scroll += 1
            
            # 事件处理
            result = self.handle_events()
            if result == "main_menu":
                return "main_menu"
            
            # 玩家输入
            keys = pygame.key.get_pressed()
            player.update(keys)
            if keys[pygame.K_SPACE]:
                if not ignore_space:
                    self._player_shoot(player, bullets)
            else:
                ignore_space = False
            
            # 生成敌机
            spawn_timer = self._try_spawn_enemy(spawn_timer, spawn_interval, enemies)
            
            # 更新游戏实体
            particles = self.update_entities(bullets, enemies, particles, player)
            
            # 碰撞检测，传入难度参数
            particles = self.handle_collisions(bullets, enemies, particles, player, difficulty=level)
            
            # 绘制
            self.draw_game(player, bullets, enemies, particles, scroll, level, score_target)
            
            pygame.display.flip()
            
            # 检查是否达到目标分数
            if player.score >= score_target:
                log(f"关卡 {level} 完成！得分：{player.score}/{score_target}")
                return player, level + 1
            
            # 检查是否游戏结束
            if player.lives <= 0:
                log(f"关卡 {level} 失败！最终得分：{player.score}")
                return player, None
        
        return player, None
    
    def game_over_screen(self, player):
        """游戏结束界面"""
        return self.interfaces.game_over_screen(player)
    
    def level_complete_screen(self, player, score_target):
        """关卡完成界面"""
        return self.interfaces.level_complete_screen(player, score_target)
    
    def confirm_exit_screen(self):
        """退出确认界面"""
        return self.interfaces.confirm_exit_screen()
    
    def endless_mode(self):
        """无尽模式"""
        log("开始无尽模式")
        player = Player(self)
        bullets = []
        enemies = []
        particles = []
        
        scroll = 0
        spawn_timer = 0
        
        # 进入无尽模式时先锁定空格，避免上一屏空格按下状态导致直接发射
        ignore_space = pygame.key.get_pressed()[pygame.K_SPACE]
        
        # 初始生成间隔
        spawn_interval = 55
        # 难度增加计数器
        difficulty_timer = 0
        # 每1000帧增加一次难度
        difficulty_increase_interval = 1000
        log(f"无尽模式初始配置：生成间隔={spawn_interval}")
        
        running = True
        while running:
            self.clock.tick(self.FPS)
            scroll += 1
            difficulty_timer += 1
            
            # 事件处理
            result = self.handle_events()
            if result == "main_menu":
                return "main_menu"
            
            # 玩家输入
            keys = pygame.key.get_pressed()
            player.update(keys)
            if keys[pygame.K_SPACE]:
                if not ignore_space:
                    self._player_shoot(player, bullets)
            else:
                ignore_space = False
            
            # 增加难度
            if difficulty_timer >= difficulty_increase_interval:
                difficulty_timer = 0
                spawn_interval = max(15, spawn_interval - 2)  # 最小间隔为15帧
                log(f"无尽模式难度增加：生成间隔={spawn_interval}")
            
            # 生成敌机
            spawn_timer = self._try_spawn_enemy(spawn_timer, spawn_interval, enemies)
            
            # 更新游戏实体
            particles = self.update_entities(bullets, enemies, particles, player)
            
            # 计算无尽模式难度
            difficulty = self._calculate_endless_difficulty(spawn_interval)
            # 碰撞检测，传入难度参数
            particles = self.handle_collisions(bullets, enemies, particles, player, difficulty=difficulty)
            
            # 绘制
            self.draw_game(player, bullets, enemies, particles, scroll, spawn_interval=spawn_interval)
            
            pygame.display.flip()
            
            # 检查是否游戏结束
            if player.lives <= 0:
                log(f"无尽模式结束！最终得分：{player.score}")
                return player
        
        return player
    
    def run(self):
        """运行游戏"""
        while True:
            result = self.start_screen()
            
            if result == "endless":
                # 无尽模式
                result = self.endless_mode()
                if result == "quit":
                    break
                if result == "main_menu":
                    continue
                # 显示游戏结束界面
                action = self.game_over_screen(result)
                if action == "quit":
                    break
                if action == "main_menu":
                    # 回到主界面
                    continue
            else:
                # 关卡模式
                level = result
                current_level = level
                
                while True:
                    game_result = self.game_screen(current_level)
                    if game_result == "quit":
                        break
                    if game_result == "main_menu":
                        break
                    
                    player, next_level = game_result
                    
                    # 检查是否达到下一关
                    if next_level:
                        # 显示关卡完成界面
                        self.level_complete_screen(player, 1000 + (current_level - 1) * 1000)
                        current_level = next_level
                    else:
                        # 显示游戏结束界面
                        action = self.game_over_screen(player)
                        if action == "quit":
                            break
                        if action == "main_menu":
                            # 回到主界面
                            break
                        else:
                            # 重新开始当前关卡
                            current_level = level
                
                if game_result == "quit":
                    break
        pygame.quit()





if __name__ == "__main__":
    game = Game()
    game.run()