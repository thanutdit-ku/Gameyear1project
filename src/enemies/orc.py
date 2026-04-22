from pathlib import Path

import pygame
from src.enemies.enemy import Enemy

_ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "images" / "enemies" / "orc"
_SPRITE_SHEET_PATH = _ASSET_DIR / "orc_walk.png"

_FRAME_W  = 32
_FRAME_H  = 32
_COLS     = 10
_WALK_ROW = 0
_BG_COLOR = (103, 82, 56)
_DISPLAY_SIZE = (40, 40)
_ANIM_SPEED   = 110   # ms per frame


def _load_walk_frames():
    # Image already has per-pixel alpha — no colorkey needed
    sheet = pygame.image.load(_SPRITE_SHEET_PATH).convert_alpha()
    frames = []
    for col in range(_COLS):
        rect = pygame.Rect(col * _FRAME_W, _WALK_ROW * _FRAME_H, _FRAME_W, _FRAME_H)
        frame = pygame.Surface((_FRAME_W, _FRAME_H), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), rect)
        frames.append(pygame.transform.smoothscale(frame, _DISPLAY_SIZE))
    return frames


class Orc(Enemy):
    _frames = None

    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp       = 150
        self.max_hp   = 150
        self.speed    = 60
        self.reward_gold = 25
        self.frames = self._load_frames()

    @classmethod
    def _load_frames(cls):
        if cls._frames is None:
            cls._frames = _load_walk_frames()
        return cls._frames

    def _current_frame(self):
        idx = (pygame.time.get_ticks() // _ANIM_SPEED) % len(self.frames)
        return self.frames[idx]

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        sprite = self._current_frame()
        rect = sprite.get_rect(center=(x, y))
        screen.blit(sprite, rect)
        self._draw_health_bar(screen, x, rect.top + 4, 32, -14)
