import pygame
from src.enemies.enemy import Enemy


class DarkKnight(Enemy):
    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp = 300
        self.max_hp = 300
        self.speed = 1.5
        self.reward_gold = 50

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        radius = 18

        # Placeholder: dark grey circle
        pygame.draw.circle(screen, (60, 60, 60), (x, y), radius)

        # Health bar
        bar_width = 36
        bar_height = 4
        bar_x = x - bar_width // 2
        bar_y = y - radius - 8

        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
