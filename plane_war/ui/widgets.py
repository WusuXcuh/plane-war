"""界面控件的绘制工具。"""

import pygame


def create_button_surface(size, fill_color, border_color, border_radius=0):
    """创建带填充色和边框的按钮表面。

    界面层复用这个函数生成按钮底图，保证按钮的圆角、边框宽度和透明度处理一致。
    """
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surface, fill_color, (0, 0, size[0], size[1]), border_radius=border_radius)
    pygame.draw.rect(surface, border_color, (0, 0, size[0], size[1]), 2, border_radius=border_radius)
    return surface
