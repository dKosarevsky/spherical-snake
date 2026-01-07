import math
from typing import List, Tuple
import pygame
from game.core import GameState, Vec3, cross, dot, normalize, scale, sub


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


def _build_basis(state: GameState):
    head = normalize(state.snake[0])
    z_axis = head
    tangent = sub(state.t, scale(z_axis, dot(z_axis, state.t)))
    x_axis = normalize(tangent) if tangent != (0.0, 0.0, 0.0) else (1.0, 0.0, 0.0)
    y_axis = cross(z_axis, x_axis)

    def orient(p: Vec3) -> Vec3:
        return dot(p, x_axis), dot(p, y_axis), dot(p, z_axis)

    return orient, x_axis, y_axis


def draw_frame(surface: pygame.Surface, state: GameState) -> None:
    surface.fill((10, 10, 12))
    size = surface.get_width()
    r = int(size * 0.38)

    orient, x_axis, y_axis = _build_basis(state)
    tangent2d = (
        dot(state.t, x_axis),
        dot(state.t, y_axis),
    )

    pygame.draw.circle(surface, (200, 200, 210), (size // 2, size // 2), r, width=2)

    for dot_pt in GRID_POINTS:
        p = orient(dot_pt)
        if not visible(p):
            continue
        dx, dy = project(p, size, r)
        pygame.draw.circle(surface, (45, 55, 70), (dx, dy), 2)

    apple = orient(state.apple)
    ax, ay = project(apple, size, r)
    if visible(apple):
        pygame.draw.circle(surface, (255, 70, 70), (ax, ay), 10)
    else:
        pygame.draw.circle(surface, (100, 80, 80), (ax, ay), 10, width=2)

    for i, seg in enumerate(reversed(state.snake)):
        seg = orient(seg)
        if not visible(seg):
            continue
        x, y = project(seg, size, r)
        z = max(0.0, min(1.0, (seg[2] + 1.0) / 2.0))
        base = 60 + int(140 * z)
        pygame.draw.circle(surface, (40, base, 90), (x, y), 7)

    head_3d = orient(state.snake[0])
    if visible(head_3d):
        hx, hy = project(head_3d, size, r)
        dir_len = math.hypot(*tangent2d)
        if dir_len < 1e-5:
            dir_vec = (1.0, 0.0)
        else:
            dir_vec = (tangent2d[0] / dir_len, tangent2d[1] / dir_len)
        perp_vec = (-dir_vec[1], dir_vec[0])
        nose = (hx + dir_vec[0] * 18, hy - dir_vec[1] * 18)
        base_left = (
            hx - dir_vec[0] * 6 + perp_vec[0] * 10,
            hy + dir_vec[1] * 6 - perp_vec[1] * 10,
        )
        base_right = (
            hx - dir_vec[0] * 6 - perp_vec[0] * 10,
            hy + dir_vec[1] * 6 + perp_vec[1] * 10,
        )
        pygame.draw.polygon(surface, (60, 200, 110), [nose, base_left, base_right])
        pygame.draw.circle(surface, (30, 120, 70), (hx, hy), 11)
        eye_offset = 6
        eye_forward = 2
        eye1 = (
            int(hx - dir_vec[0] * eye_forward + perp_vec[0] * eye_offset),
            int(hy + dir_vec[1] * eye_forward - perp_vec[1] * eye_offset),
        )
        eye2 = (
            int(hx - dir_vec[0] * eye_forward - perp_vec[0] * eye_offset),
            int(hy + dir_vec[1] * eye_forward + perp_vec[1] * eye_offset),
        )
        pygame.draw.circle(surface, (0, 0, 0), eye1, 2)
        pygame.draw.circle(surface, (0, 0, 0), eye2, 2)
