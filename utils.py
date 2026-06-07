import pygame


def clamp(value, minimum, maximum):
    """把数值限制在最小值和最大值之间。"""
    return max(minimum, min(maximum, value))


def point_in_polygon(x, y, polygon):
    """使用射线法判断点是否在多边形内部。"""
    inside = False
    n = len(polygon)
    for i in range(n):
        j = (i + 1) % n
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
    return inside


def create_button_surface(size, fill_color, border_color, border_radius=0):
    """创建带填充色和边框的按钮表面。"""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surface, fill_color, (0, 0, size[0], size[1]), border_radius=border_radius)
    pygame.draw.rect(surface, border_color, (0, 0, size[0], size[1]), 2, border_radius=border_radius)
    return surface
