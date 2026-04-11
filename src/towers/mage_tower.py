import pygame
from src.towers.tower import Tower

SLOW_FACTOR = 0.5   # reduce speed to 50%
SLOW_DURATION = 2.0  # seconds


class MageTower(Tower):
    def __init__(self, position):
        super().__init__(position, cost=150)
        self.damage = 60
        self.attack_range = 120
        self.attack_speed = 0.8

    def _on_attack(self, target, enemies):
        target.take_damage(self.damage)
        self._apply_slow(target)

    def _apply_slow(self, enemy):
        """Slow the enemy to 50% speed for 2 seconds.
        Requires the Enemy base class to support slow_timer and base_speed."""
        if not hasattr(enemy, "base_speed"):
            enemy.base_speed = enemy.speed
        enemy.speed = enemy.base_speed * SLOW_FACTOR
        enemy.slow_timer = SLOW_DURATION

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        pygame.draw.ellipse(screen, (19, 21, 35), (x - 18, y + 10, 36, 12))
        pygame.draw.polygon(
            screen,
            (67, 56, 126),
            [(x, y - 18), (x + 14, y - 4), (x + 10, y + 14), (x - 10, y + 14), (x - 14, y - 4)],
        )
        pygame.draw.polygon(
            screen,
            (205, 145, 255),
            [(x, y - 14), (x + 9, y - 2), (x, y + 10), (x - 9, y - 2)],
        )
        pygame.draw.circle(screen, (244, 230, 255), (x, y - 2), 4)
        pygame.draw.circle(screen, (180, 228, 255), (x - 10, y - 8), 3)
        pygame.draw.circle(screen, (180, 228, 255), (x + 10, y - 8), 3)

        font = pygame.font.SysFont("verdana", 13, bold=True)
        label = font.render(f"Lv{self.level}", True, (255, 255, 255))
        screen.blit(label, (x - label.get_width() // 2, y + 18))
