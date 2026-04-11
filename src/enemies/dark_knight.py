import pygame
from src.enemies.enemy import Enemy


class DarkKnight(Enemy):
    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp = 300
        self.max_hp = 300
        self.speed = 42
        self.reward_gold = 50

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        pygame.draw.ellipse(screen, (17, 18, 24), (x - 22, y + 12, 44, 12))
        pygame.draw.circle(screen, (66, 70, 82), (x, y), 18)
        pygame.draw.circle(screen, (145, 152, 173), (x, y), 18, 2)
        pygame.draw.polygon(screen, (34, 36, 44), [(x, y - 22), (x + 18, y - 3), (x, y + 8), (x - 18, y - 3)])
        pygame.draw.rect(screen, (215, 57, 57), (x - 9, y - 3, 6, 3), border_radius=1)
        pygame.draw.rect(screen, (215, 57, 57), (x + 3, y - 3, 6, 3), border_radius=1)
        self._draw_health_bar(screen, x, y, 36, -28, color=(225, 130, 130))
