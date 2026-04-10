import pygame
from src.enemies.enemy import Enemy


class Orc(Enemy):
    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp = 150
        self.max_hp = 150
        self.speed = 2.25
        self.reward_gold = 25

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        radius = 16

        # Placeholder: brown circle
        pygame.draw.circle(screen, (139, 69, 19), (x, y), radius)

        # Health bar
        bar_width = 32
        bar_height = 4
        bar_x = x - bar_width // 2
        bar_y = y - radius - 8

        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
