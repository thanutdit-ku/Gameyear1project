from pathlib import Path

import pygame
from src.enemies.enemy import Enemy


class Goblin(Enemy):
    _sprite = None
    _sprite_size = (40, 40)

    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp = 60
        self.max_hp = 60
        self.speed = 90
        self.reward_gold = 10
        self.sprite = self._load_sprite()

    @classmethod
    def _load_sprite(cls):
        if cls._sprite is not None:
            return cls._sprite

        sprite_path = (
            Path(__file__).resolve().parents[2]
            / "assets"
            / "images"
            / "enemies"
            / "goblin"
            / "howl.png"
        )
        image = pygame.image.load(sprite_path).convert_alpha()
        cls._sprite = pygame.transform.smoothscale(image, cls._sprite_size)
        return cls._sprite

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        sprite_rect = self.sprite.get_rect(midbottom=(x, y + 14))
        screen.blit(self.sprite, sprite_rect)
        self._draw_health_bar(screen, x, sprite_rect.top + 8, 24, -18)
