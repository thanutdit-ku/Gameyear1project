import pygame
from src.enemies.enemy import Enemy


class Orc(Enemy):
    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp = 150
        self.max_hp = 150
        self.speed = 60
        self.reward_gold = 25

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        pygame.draw.ellipse(screen, (26, 18, 12), (x - 20, y + 10, 40, 12))
        pygame.draw.circle(screen, (120, 87, 46), (x, y), 16)
        pygame.draw.circle(screen, (168, 130, 75), (x - 5, y - 5), 4)
        pygame.draw.circle(screen, (168, 130, 75), (x + 5, y - 5), 4)
        pygame.draw.rect(screen, (210, 222, 206), (x - 9, y + 3, 5, 6), border_radius=2)
        pygame.draw.rect(screen, (210, 222, 206), (x + 4, y + 3, 5, 6), border_radius=2)
        self._draw_health_bar(screen, x, y, 32, -25)
