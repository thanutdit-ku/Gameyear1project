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

        # Placeholder: green square
        size = 28
        rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
        pygame.draw.rect(screen, (34, 139, 34), rect)

        font = pygame.font.SysFont(None, 16)
        label = font.render(f"Lv{self.level}", True, (255, 255, 255))
        screen.blit(label, (x - label.get_width() // 2, y - label.get_height() // 2))
