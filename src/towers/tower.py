import pygame
import math


TARGETING_MODES = ["first", "last", "strongest", "closest"]
TARGETING_LABELS = {"first": "F", "last": "L", "strongest": "S", "closest": "C"}


class Tower:
    def __init__(self, position, cost):
        self.position = pygame.Vector2(position)
        self.cost = cost
        self.level = 1
        self.targeting_mode = "first"

        # Subclasses define these directly
        self.damage = 0
        self.attack_range = 0
        self.attack_speed = 0  # attacks per second

        self._attack_cooldown = 0  # seconds remaining until next attack

    def cycle_targeting_mode(self):
        """Advance to the next targeting mode in the cycle."""
        idx = TARGETING_MODES.index(self.targeting_mode)
        self.targeting_mode = TARGETING_MODES[(idx + 1) % len(TARGETING_MODES)]

    def find_target(self, enemies):
        """Return the best enemy within attack range based on targeting_mode."""
        in_range = [e for e in enemies if self.position.distance_to(e.position) <= self.attack_range]
        if not in_range:
            return None

        if self.targeting_mode == "first":
            return max(in_range, key=lambda e: e.path_index)
        if self.targeting_mode == "last":
            return min(in_range, key=lambda e: e.path_index)
        if self.targeting_mode == "strongest":
            return max(in_range, key=lambda e: e.hp)
        # "closest"
        return min(in_range, key=lambda e: self.position.distance_to(e.position))

    def attack(self, enemies, dt):
        """Reduce cooldown each frame; fire at the best target when ready.
        Returns a Projectile when one is spawned, else None."""
        self._attack_cooldown -= dt
        if self._attack_cooldown > 0:
            return None

        target = self.find_target(enemies)
        if target is None:
            return None

        projectile = self._on_attack(target, enemies)
        self._attack_cooldown = 1.0 / self.attack_speed
        return projectile

    def _on_attack(self, target, enemies):
        """Spawn a projectile or deal instant damage. Return Projectile or None."""
        target.take_damage(self.damage)
        return None

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

        # Targeting mode label above tower
        mode_label = TARGETING_LABELS[self.targeting_mode]
        mode_surf = font.render(mode_label, True, (255, 220, 80))
        screen.blit(mode_surf, (x - mode_surf.get_width() // 2, y - size // 2 - mode_surf.get_height() - 1))

    def draw_range(self, screen):
        """Draw attack range circle (shown when tower is selected)."""
        x, y = int(self.position.x), int(self.position.y)
        surf = pygame.Surface((self.attack_range * 2, self.attack_range * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 255, 255, 40), (self.attack_range, self.attack_range), self.attack_range)
        pygame.draw.circle(surf, (255, 255, 255, 120), (self.attack_range, self.attack_range), self.attack_range, 1)
        screen.blit(surf, (x - self.attack_range, y - self.attack_range))
