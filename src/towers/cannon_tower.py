import pygame
from src.towers.tower import Tower


class CannonTower(Tower):
    SPLASH_RADIUS = 50

    def __init__(self, position):
        super().__init__(position, cost=125)
        self.damage = 40
        self.attack_range = 100
        self.attack_speed = 0.5

    def _on_attack(self, target, enemies):
        """Deal full damage to all enemies within splash_radius of the target."""
        for enemy in enemies:
            if target.position.distance_to(enemy.position) <= self.SPLASH_RADIUS:
                enemy.take_damage(self.damage)

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)

        # Placeholder: dark red square
        size = 28
        rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
        pygame.draw.rect(screen, (180, 50, 0), rect)

        font = pygame.font.SysFont(None, 16)
        label = font.render(f"Lv{self.level}", True, (255, 255, 255))
        screen.blit(label, (x - label.get_width() // 2, y - label.get_height() // 2))
