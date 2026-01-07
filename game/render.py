import math
from typing import List, Tuple
import pygame
from game.core import GameState, Vec3, angle_between, cross, rotate


def project(p: Vec3, size: int, r: int) -> Tuple[int, int]:
    cx = size // 2
    cy = size // 2
    x = int(cx + p[0] * r)
    y = int(cy - p[1] * r)
    return x, y


def visible(p: Vec3) -> bool:
    return p[2] >= 0.0


def _grid_points() -> List[Vec3]:
    pts: List[Vec3] = []
    for lat_deg in range(-60, 61, 30):
        lat = math.radians(lat_deg)
        cos_lat = math.cos(lat)
        sin_lat = math.sin(lat)
        for lon_deg in range(0, 360, 30):
            lon = math.radians(lon_deg)
            pts.append((cos_lat * math.cos(lon), cos_lat * math.sin(lon), sin_lat))
    return pts


GRID_POINTS = _grid_points()


def draw_frame(surface: pygame.Surface, state: GameState) -> None:
    surface.fill((10, 10, 12))
    size = surface.get_width()
    r = int(size * 0.38)

    head = state.snake[0]
    front = (0.0, 0.0, 1.0)
    axis = cross(head, front)
    axis_len_sq = axis[0] * axis[0] + axis[1] * axis[1] + axis[2] * axis[2]
    should_rotate = axis_len_sq > 1e-10
    if should_rotate:
        angle = angle_between(head, front)

    def orient(p: Vec3) -> Vec3:
        if not should_rotate:
            return p
        return rotate(p, axis, angle)

    pygame.draw.circle(surface, (200, 200, 210), (size // 2, size // 2), r, width=2)

    for dot_pt in GRID_POINTS:
        p = orient(dot_pt)
        if not visible(p):
            continue
        dx, dy = project(p, size, r)
        pygame.draw.circle(surface, (45, 55, 70), (dx, dy), 2)

    apple = orient(state.apple)
    if visible(apple):
        ax, ay = project(apple, size, r)
        pygame.draw.circle(surface, (255, 70, 70), (ax, ay), 6)

    for i, seg in enumerate(reversed(state.snake)):
        seg = orient(seg)
        if not visible(seg):
            continue
        x, y = project(seg, size, r)
        z = max(0.0, min(1.0, (seg[2] + 1.0) / 2.0))
        base = 60 + int(140 * z)
        pygame.draw.circle(surface, (40, base, 90), (x, y), 5)
