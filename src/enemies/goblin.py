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

        # Health bar
        bar_width = 24
        bar_height = 4
        bar_x = x - bar_width // 2
        bar_y = sprite_rect.top - 10

        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
