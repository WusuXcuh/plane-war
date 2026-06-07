"""资源加载与轻量资源状态管理。

这里集中处理字体、图片、子弹图片组、星空和默认碰撞遮罩，避免主流程文件
承担路径查找、缩放、随机选图等细节。
"""

import os
import random

import pygame

from constants import BULLET_TARGET_HEIGHT, BULLET_TARGET_WIDTH, PLAYER_IMAGE, POWERUP_TARGET_SIZE
from entities import Bullet


# 道具类型到道具图片目录中具体文件名的映射。
# 文件名可以是中文；游戏逻辑内部仍使用固定字符串标识。
POWERUP_IMAGE_FILES = {
    "score": "加分道具.png",
    "shield": "护盾道具.png",
    "repair": "治疗道具.png",
    "rapid_fire": "加快射速.png",
    "bullet_stream": "增加弹道.png",
}


class DummyFont:
    """字体系统不可用时的兜底对象，保证界面流程不会崩溃。"""

    def __init__(self, size):
        self.size = size
        self.bold = False

    def set_bold(self, value):
        self.bold = bool(value)

    def render(self, text, antialias, color):
        surface = pygame.Surface((len(text) * 10, self.size), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        return surface


class AssetManager:
    """集中加载和管理图片/字体等资源。

    资源加载后会挂回游戏对象，供实体、渲染器、规则系统等模块访问。
    """

    def __init__(self, game, base_dir):
        self.game = game
        self.base_dir = base_dir
        self.bullet_images = []
        self.bullet_image_groups = {}
        self.bullet_group_indexes = {}
        self.current_bullet_group = None
        self.bullet_switch_timer = 0

    def load_font(self, size):
        """优先使用系统中文字体，失败时回退到默认字体。"""
        font_paths = [
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/microsoftyahei.ttf",
            "C:/Windows/Fonts/msyh.ttf",
        ]

        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    font = pygame.font.Font(font_path, size)
                    test_surface = font.render("测试", True, (255, 255, 255))
                    if test_surface.get_width() > 0:
                        return font
            except Exception:
                pass

        try:
            return pygame.font.SysFont(None, size)
        except Exception:
            return DummyFont(size)

    def load_player_image(self):
        """加载玩家飞机，并按目标宽度等比缩放。"""
        path = os.path.join(self.base_dir, PLAYER_IMAGE)
        raw = pygame.image.load(path).convert_alpha()
        original_width, original_height = raw.get_size()
        target_width = 60
        target_height = int(target_width / (original_width / original_height))
        return pygame.transform.smoothscale(raw, (target_width, target_height))

    def load_meteorite_images(self):
        """加载陨石原图；具体缩放和旋转由陨石实体和渲染器按尺寸等级处理。"""
        meteorite_dir = os.path.join(self.base_dir, "pictures/meteorite")
        images = {}
        if not os.path.exists(meteorite_dir):
            return images

        for img_file in sorted(os.listdir(meteorite_dir)):
            if not img_file.lower().endswith(".png"):
                continue
            try:
                path = os.path.join(meteorite_dir, img_file)
                images[img_file] = pygame.image.load(path).convert_alpha()
            except Exception:
                pass
        return images

    def load_bullet_images(self):
        """加载玩家子弹图片，支持按子文件夹分组。"""
        bullet_dir = os.path.join(self.base_dir, "pictures/bullets")
        self.bullet_images = []
        self.bullet_image_groups = {}
        self.bullet_group_indexes = {}
        self.current_bullet_group = None
        self.bullet_switch_timer = 0

        if not os.path.exists(bullet_dir):
            return

        image_groups = self._collect_bullet_image_groups(bullet_dir)
        for group_name, image_files in image_groups.items():
            group_images = []
            for img_file in image_files:
                image = self._load_bullet_image(bullet_dir, img_file)
                if image:
                    group_images.append(image)
                    self.bullet_images.append(image)
            if group_images:
                self.bullet_image_groups[group_name] = group_images
                self.bullet_group_indexes[group_name] = 0

        self.reset_bullet_group_timer()

    def load_powerup_images(self):
        """加载道具图片，并统一缩放到目标尺寸。"""
        powerup_dir = os.path.join(self.base_dir, "pictures/powerup")
        images = {}
        if not os.path.exists(powerup_dir):
            return images

        for kind, filename in POWERUP_IMAGE_FILES.items():
            path = os.path.join(powerup_dir, filename)
            if not os.path.exists(path):
                continue
            try:
                raw = pygame.image.load(path).convert_alpha()
                images[kind] = pygame.transform.smoothscale(
                    raw,
                    (POWERUP_TARGET_SIZE, POWERUP_TARGET_SIZE),
                )
            except Exception:
                pass
        return images

    def _collect_bullet_image_groups(self, bullet_dir):
        group_dirs = [
            name for name in sorted(os.listdir(bullet_dir))
            if os.path.isdir(os.path.join(bullet_dir, name))
        ]
        if group_dirs:
            return {
                group_name: [
                    os.path.join(group_name, f)
                    for f in sorted(os.listdir(os.path.join(bullet_dir, group_name)))
                    if f.lower().endswith(".png")
                ]
                for group_name in group_dirs
            }

        return {
            "default": [
                f for f in sorted(os.listdir(bullet_dir))
                if f.lower().endswith(".png")
            ]
        }

    def _load_bullet_image(self, bullet_dir, img_file):
        try:
            path = os.path.join(bullet_dir, img_file)
            raw = pygame.image.load(path).convert_alpha()
            original_width, original_height = raw.get_size()
            scale = min(BULLET_TARGET_WIDTH / original_width, BULLET_TARGET_HEIGHT / original_height)
            target_width = max(1, int(original_width * scale))
            target_height = max(1, int(original_height * scale))
            image = pygame.transform.smoothscale(raw, (target_width, target_height))
            return pygame.transform.rotate(image, 90)
        except Exception:
            return None

    def reset_bullet_group_timer(self):
        """重置子弹组轮换，并随机选择一个可用子弹组。"""
        self.bullet_switch_timer = 0
        if self.bullet_image_groups:
            self.current_bullet_group = random.choice(list(self.bullet_image_groups.keys()))
            self.bullet_group_indexes[self.current_bullet_group] = 0

    def update_bullet_group(self, fps):
        """每 10 秒切换到另一个子弹图片组。"""
        if len(self.bullet_image_groups) <= 1:
            return

        self.bullet_switch_timer += 1
        if self.bullet_switch_timer < fps * 10:
            return

        self.bullet_switch_timer = 0
        groups = [group for group in self.bullet_image_groups if group != self.current_bullet_group]
        self.current_bullet_group = random.choice(groups)
        self.bullet_group_indexes[self.current_bullet_group] = 0

    def get_bullet_image(self):
        """按当前子弹组顺序取图；没有分组时随机取一张。"""
        if self.current_bullet_group in self.bullet_image_groups:
            group_images = self.bullet_image_groups[self.current_bullet_group]
            index = self.bullet_group_indexes.get(self.current_bullet_group, 0)
            image = group_images[index % len(group_images)]
            self.bullet_group_indexes[self.current_bullet_group] = (index + 1) % len(group_images)
            return image

        if not self.bullet_images:
            return None
        return random.choice(self.bullet_images)

    def get_random_meteorite_image(self, meteorite_images):
        if not meteorite_images:
            return None
        return random.choice(list(meteorite_images.values()))

    def create_stars(self, width, height, count=120):
        return [(random.randint(0, width), random.randint(0, height), random.random()) for _ in range(count)]

    def create_default_bullet_mask(self):
        bullet_surface = pygame.Surface((Bullet.W, Bullet.H), pygame.SRCALPHA)
        pygame.draw.rect(bullet_surface, (255, 255, 255, 255), (0, 0, Bullet.W, Bullet.H))
        return pygame.mask.from_surface(bullet_surface)
