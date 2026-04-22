from pathlib import Path

import pygame
from src.enemies.enemy import Enemy

_ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "images" / "enemies" / "spider"

_FRAME_W    = 64
_FRAME_H    = 64
_COLS       = 10
_DISPLAY_SIZE = (44, 44)
_ANIM_SPEED   = 100   # ms per frame

# LPC standard: up=0, left=1, down=2, right=3
_DIR_ROWS = {"up": 0, "left": 1, "down": 2, "right": 3}


def _load_spider_frames():
    sheet = pygame.image.load(_ASSET_DIR / "walk.png").convert_alpha()
    frames = {}
    for direction, row in _DIR_ROWS.items():
        row_frames = []
        for col in range(_COLS):
            rect = pygame.Rect(col * _FRAME_W, row * _FRAME_H, _FRAME_W, _FRAME_H)
            frame = pygame.Surface((_FRAME_W, _FRAME_H), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), rect)
            row_frames.append(pygame.transform.smoothscale(frame, _DISPLAY_SIZE))
        frames[direction] = row_frames
    return frames


class Spider(Enemy):
    _frames = None

    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp          = 80
        self.max_hp      = 80
        self.speed       = 82
        self.reward_gold = 14
        self.spawn_spacing = 48
        self._load_all_frames()

    @classmethod
    def _load_all_frames(cls):
        if cls._frames is None:
            cls._frames = _load_spider_frames()

    def _direction_key(self):
        if self.path_index < len(self.waypoints) - 1:
            target    = pygame.Vector2(self.waypoints[self.path_index + 1])
            direction = target - self.position
            if direction.length_squared() > 0:
                if abs(direction.x) >= abs(direction.y):
                    return "right" if direction.x > 0 else "left"
                return "down" if direction.y > 0 else "up"
        return "right"

    def _current_frame(self):
        key = self._direction_key()
        idx = (pygame.time.get_ticks() // _ANIM_SPEED) % _COLS
        return self._frames[key][idx]

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        sprite = self._current_frame()
        rect   = sprite.get_rect(center=(x, y))

        shadow = pygame.Rect(0, 0, 28, 8)
        shadow.center = (x, y + 18)
        pygame.draw.ellipse(screen, (20, 14, 10), shadow)

        screen.blit(sprite, rect)
        self._draw_health_bar(screen, x, rect.top + 4, 28, -12, color=(200, 80, 80))
