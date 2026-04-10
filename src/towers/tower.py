import pygame
import math


class Tower:
    def __init__(self, position, cost):
        self.position = pygame.Vector2(position)
        self.cost = cost
        self.level = 1

        # Subclasses define these directly
        self.damage = 0
        self.attack_range = 0
        self.attack_speed = 0  # attacks per second

        self._attack_cooldown = 0  # seconds remaining until next attack

    def find_target(self, enemies):
        """Return the enemy with the highest path_index within attack range, or None."""
        best = None
        for enemy in enemies:
            dist = self.position.distance_to(enemy.position)
            if dist <= self.attack_range:
                if best is None or enemy.path_index > best.path_index:
                    best = enemy
        return best

    def attack(self, enemies, dt):
        """Reduce cooldown each frame; fire at the best target when ready."""
        self._attack_cooldown -= dt
        if self._attack_cooldown > 0:
            return

        target = self.find_target(enemies)
        if target is None:
            return

        self._on_attack(target, enemies)
        self._attack_cooldown = 1.0 / self.attack_speed

    def _on_attack(self, target, enemies):
        """Apply damage to the target. Subclasses can override for special behaviour."""
        target.take_damage(self.damage)

    def upgrade(self):
        """Increase level and boost stats. Subclasses may override for custom scaling."""
        if self.level >= 2:
            return False
        self.level += 1
        self.damage = int(self.damage * 1.5)
        self.attack_range = int(self.attack_range * 1.2)
        return True

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)

        # Placeholder: grey square
        size = 28
        rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
        pygame.draw.rect(screen, (150, 150, 150), rect)

        # Level indicator
        font = pygame.font.SysFont(None, 16)
        label = font.render(f"Lv{self.level}", True, (255, 255, 255))
        screen.blit(label, (x - label.get_width() // 2, y - label.get_height() // 2))

    def draw_range(self, screen):
        """Draw attack range circle (shown when tower is selected)."""
        x, y = int(self.position.x), int(self.position.y)
        surf = pygame.Surface((self.attack_range * 2, self.attack_range * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 255, 255, 40), (self.attack_range, self.attack_range), self.attack_range)
        pygame.draw.circle(surf, (255, 255, 255, 120), (self.attack_range, self.attack_range), self.attack_range, 1)
        screen.blit(surf, (x - self.attack_range, y - self.attack_range))
