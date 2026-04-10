import pygame
from src.enemies.enemy import Enemy


class Goblin(Enemy):
    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp = 60
        self.max_hp = 60
        self.speed = 4.5
        self.reward_gold = 10

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        radius = 12

        # Placeholder: green circle
        pygame.draw.circle(screen, (0, 180, 0), (x, y), radius)

        # Health bar
        bar_width = 24
        bar_height = 4
        bar_x = x - bar_width // 2
        bar_y = y - radius - 8

        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
