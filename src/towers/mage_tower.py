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

        # Placeholder: purple square
        size = 28
        rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
        pygame.draw.rect(screen, (128, 0, 200), rect)

        font = pygame.font.SysFont(None, 16)
        label = font.render(f"Lv{self.level}", True, (255, 255, 255))
        screen.blit(label, (x - label.get_width() // 2, y - label.get_height() // 2))
