import pygame
import random
from src.towers.tower import Tower


class ArcherTower(Tower):
    CRIT_CHANCE = 0.2  # 20% chance to deal double damage

    def __init__(self, position):
        super().__init__(position, cost=100)
        self.damage = 25
        self.attack_range = 150
        self.attack_speed = 1.5

    def _on_attack(self, target, enemies):
        dmg = self.damage
        if random.random() < self.CRIT_CHANCE:
            dmg *= 2
        target.take_damage(dmg)

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        pygame.draw.ellipse(screen, (22, 38, 24), (x - 18, y + 10, 36, 12))
        pygame.draw.circle(screen, (92, 62, 40), (x, y + 2), 14)
        pygame.draw.circle(screen, (168, 123, 84), (x, y + 2), 14, 2)
        pygame.draw.line(screen, (73, 121, 68), (x, y - 14), (x, y + 14), 4)
        pygame.draw.arc(screen, (165, 228, 148), (x - 11, y - 14, 16, 28), 1.2, 5.1, 3)
        pygame.draw.line(screen, (234, 225, 201), (x - 3, y - 10), (x - 3, y + 10), 2)
        pygame.draw.line(screen, (234, 225, 201), (x + 2, y - 4), (x + 13, y - 10), 2)

        font = pygame.font.SysFont("verdana", 13, bold=True)
        label = font.render(f"Lv{self.level}", True, (255, 255, 255))
        screen.blit(label, (x - label.get_width() // 2, y + 18))
