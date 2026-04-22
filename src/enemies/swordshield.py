from pathlib import Path

import pygame

from src.enemies.enemy import Enemy

_ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "images" / "enemies" / "swordshield"

_FRAME_W      = 42
_FRAME_H      = 42
_WALK_FRAMES  = 8
_IDLE_FRAMES  = 4
_DISPLAY_SIZE = (48, 48)
_WALK_SPEED   = 120   # ms per frame
_IDLE_SPEED   = 180


def _slice_frames(path, count):
    sheet = pygame.image.load(path).convert_alpha()
    frames = []
    for i in range(count):
        rect = pygame.Rect(i * _FRAME_W, 0, _FRAME_W, _FRAME_H)
        frame = pygame.Surface((_FRAME_W, _FRAME_H), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), rect)
        frames.append(pygame.transform.smoothscale(frame, _DISPLAY_SIZE))
    return frames


class SwordShield(Enemy):
    _walk_frames = None
    _idle_frames = None

    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp          = 95
        self.max_hp      = 95
        self.speed       = 72
        self.reward_gold = 16
        self.spawn_spacing = 56
        self._load_all_frames()

    @classmethod
    def _load_all_frames(cls):
        if cls._walk_frames is not None:
            return
        cls._walk_frames = _slice_frames(_ASSET_DIR / "walk.png", _WALK_FRAMES)
        cls._idle_frames = _slice_frames(_ASSET_DIR / "idle.png", _IDLE_FRAMES)

    def _facing_left(self):
        if self.path_index < len(self.waypoints) - 1:
            target = pygame.Vector2(self.waypoints[self.path_index + 1])
            return (target - self.position).x < 0
        return False

    def _current_frame(self):
        moving = self.path_index < len(self.waypoints) - 1
        if moving:
            idx = (pygame.time.get_ticks() // _WALK_SPEED) % _WALK_FRAMES
            frame = self._walk_frames[idx]
        else:
            idx = (pygame.time.get_ticks() // _IDLE_SPEED) % _IDLE_FRAMES
            frame = self._idle_frames[idx]

        if self._facing_left():
            frame = pygame.transform.flip(frame, True, False)
        return frame

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        sprite = self._current_frame()
        sprite_rect = sprite.get_rect(midbottom=(x, y + 18))

        shadow = pygame.Rect(0, 0, 26, 10)
        shadow.center = (x, y + 12)
        pygame.draw.ellipse(screen, (28, 19, 20), shadow)

        screen.blit(sprite, sprite_rect)
        self._draw_health_bar(screen, x, sprite_rect.top + 8, 30, -18, color=(126, 214, 150))
