from pathlib import Path

import pygame

from src.enemies.enemy import Enemy

_ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "images" / "enemies" / "slime"


def _load_move_frames(size):
    frames = []
    for i in range(4):
        img = pygame.image.load(_ASSET_DIR / f"slime-move-{i}.png").convert_alpha()
        frames.append(pygame.transform.smoothscale(img, size))
    return frames


class Slime(Enemy):
    _frames = None
    _sprite_size = (34, 28)
    _animation_speed = 130
    splits_on_death = True

    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp = 40
        self.max_hp = 40
        self.speed = 75
        self.reward_gold = 8
        self.spawn_spacing = 36
        self.frames = self._load_frames()

    @classmethod
    def _load_frames(cls):
        if cls._frames is not None:
            return cls._frames
        cls._frames = _load_move_frames(cls._sprite_size)
        return cls._frames

    def _get_current_frame(self):
        idx = (pygame.time.get_ticks() // self._animation_speed) % len(self.frames)
        return self.frames[idx]

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        sprite = self._get_current_frame()
        sprite_rect = sprite.get_rect(center=(x, y))
        screen.blit(sprite, sprite_rect)
        self._draw_health_bar(screen, x, sprite_rect.top + 2, 22, -12, color=(100, 220, 100))


class MiniSlime(Enemy):
    _frames = None
    _sprite_size = (20, 16)
    _animation_speed = 100
    splits_on_death = False

    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp = 20
        self.max_hp = 20
        self.speed = 88
        self.reward_gold = 0
        self.spawn_spacing = 24
        self.frames = self._load_frames()

    @classmethod
    def _load_frames(cls):
        if cls._frames is not None:
            return cls._frames
        cls._frames = _load_move_frames(cls._sprite_size)
        return cls._frames

    def _get_current_frame(self):
        idx = (pygame.time.get_ticks() // self._animation_speed) % len(self.frames)
        return self.frames[idx]

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        sprite = self._get_current_frame()
        sprite_rect = sprite.get_rect(center=(x, y))
        screen.blit(sprite, sprite_rect)
        self._draw_health_bar(screen, x, sprite_rect.top + 2, 14, -10, color=(80, 200, 80))
