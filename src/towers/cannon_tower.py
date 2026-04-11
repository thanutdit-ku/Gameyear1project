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
        pygame.draw.ellipse(screen, (24, 26, 30), (x - 20, y + 10, 40, 12))
        pygame.draw.rect(screen, (98, 72, 53), (x - 10, y + 2, 20, 12), border_radius=4)
        pygame.draw.circle(screen, (56, 63, 75), (x, y - 4), 11)
        pygame.draw.circle(screen, (139, 149, 164), (x, y - 4), 11, 2)
        pygame.draw.line(screen, (68, 74, 82), (x + 4, y - 8), (x + 18, y - 16), 6)
        pygame.draw.circle(screen, (152, 99, 70), (x + 19, y - 17), 3)

        font = pygame.font.SysFont("verdana", 13, bold=True)
        label = font.render(f"Lv{self.level}", True, (255, 255, 255))
        screen.blit(label, (x - label.get_width() // 2, y + 18))
