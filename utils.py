import pygame


def clamp(value, minimum, maximum):
    """Clamp value between minimum and maximum."""
    return max(minimum, min(maximum, value))


def point_in_polygon(x, y, polygon):
    """Return True if point is inside a polygon using the ray casting method."""
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
    """Return a button surface with fill and border."""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surface, fill_color, (0, 0, size[0], size[1]), border_radius=border_radius)
    pygame.draw.rect(surface, border_color, (0, 0, size[0], size[1]), 2, border_radius=border_radius)
    return surface
