import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

Vec3 = Tuple[float, float, float]


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    return a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]


def norm(a: Vec3) -> float:
    return math.sqrt(dot(a, a))


def scale(a: Vec3, k: float) -> Vec3:
    return a[0] * k, a[1] * k, a[2] * k


def add(a: Vec3, b: Vec3) -> Vec3:
    return a[0] + b[0], a[1] + b[1], a[2] + b[2]


def sub(a: Vec3, b: Vec3) -> Vec3:
    return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def normalize(a: Vec3) -> Vec3:
    n = norm(a)
    if n == 0:
        return 0.0, 0.0, 0.0
    return scale(a, 1.0 / n)


def rotate(v: Vec3, axis: Vec3, angle: float) -> Vec3:
    # Rodrigues' rotation formula
    k = normalize(axis)
    cos = math.cos(angle)
    sin = math.sin(angle)
    term1 = scale(v, cos)
    term2 = scale(cross(k, v), sin)
    term3 = scale(k, dot(k, v) * (1 - cos))
    return add(add(term1, term2), term3)


def random_unit() -> Vec3:
    # uniform-ish via normal distribution
    x, y, z = random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1)
    return normalize((x, y, z))


@dataclass
class GameConfig:
    step_rad: float = 0.045  # speed
    turn_rad: float = 0.35  # rotation per tick
    eat_angle: float = 0.10  # apple
    self_hit_angle: float = 0.07  # crash
    init_len: int = 12


@dataclass
class GameState:
    snake: List[Vec3]
    t: Vec3
    apple: Vec3
    score: int = 0
    alive: bool = True


def angle_between(u: Vec3, v: Vec3) -> float:
    c = max(-1.0, min(1.0, dot(u, v)))
    return math.acos(c)


def new_game(cfg: GameConfig) -> GameState:
    head = (0.0, 0.0, 1.0)
    t = (1.0, 0.0, 0.0)
    snake = [head]
    # grow a tail
    axis = normalize(cross(head, t))
    p = head
    for _ in range(cfg.init_len - 1):
        p = rotate(p, axis, -cfg.step_rad)
        snake.append(p)
    apple = random_unit()
    return GameState(snake=snake, t=t, apple=apple)


def step(state: GameState, cfg: GameConfig, left: bool, right: bool) -> None:
    if not state.alive:
        return

    head = state.snake[0]
    t = state.t

    # Rotate tangent around radius
    if left and not right:
        t = rotate(t, head, +cfg.turn_rad)
    elif right and not left:
        t = rotate(t, head, -cfg.turn_rad)

    # guarantee tangence (numerical error accumulates)
    t = normalize(sub(t, scale(head, dot(head, t))))

    # Moving the head around the sphere: rotation around the axis a = head × t
    axis = normalize(cross(head, t))
    new_head = rotate(head, axis, cfg.step_rad)

    # Carry the whole body
    state.snake.insert(0, new_head)

    # eaten an apple?
    if angle_between(new_head, state.apple) < cfg.eat_angle:
        state.score += 1
        state.apple = random_unit()
    else:
        state.snake.pop()

    # Self-collision
    for seg in state.snake[10:]:  # Skip the first few times, otherwise false positives
        if angle_between(new_head, seg) < cfg.self_hit_angle:
            state.alive = False
            break

    state.t = t


def apple_guidance(state: GameState) -> Optional[Tuple[float, float]]:
    head = state.snake[0]
    apple = state.apple
    plane = cross(head, apple)
    if norm(plane) == 0.0:
        return None
    plane = normalize(plane)
    desired = normalize(cross(plane, head))
    offset = angle_between(state.t, desired)
    turn_dir = dot(cross(state.t, desired), head)
    return offset, turn_dir
