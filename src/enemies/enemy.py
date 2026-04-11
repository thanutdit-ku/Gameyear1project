import pygame
import math


class Enemy:
    def __init__(self, waypoints):
        self.waypoints = waypoints
        self.path_index = 0
        self.position = pygame.Vector2(waypoints[0])
        self.spawn_spacing = 48

        # Subclasses define these directly
        self.hp = 0
        self.max_hp = 0
        self.speed = 0
        self.reward_gold = 0

    def set_spawn_offset(self, distance):
        if len(self.waypoints) < 2 or distance <= 0:
            return

        start = pygame.Vector2(self.waypoints[0])
        next_point = pygame.Vector2(self.waypoints[1])
        direction = next_point - start
        if direction.length_squared() == 0:
            return

        self.position = start - direction.normalize() * distance

    def move(self, dt):
        if self.path_index >= len(self.waypoints) - 1:
            return

        target = pygame.Vector2(self.waypoints[self.path_index + 1])
        direction = target - self.position
        distance = direction.length()

        if distance == 0:
            self.path_index += 1
            return

        step = self.speed * dt

        if step >= distance:
            self.position = target
            self.path_index += 1
        else:
            self.position += direction.normalize() * step

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp < 0:
            self.hp = 0

    def is_dead(self):
        return self.hp <= 0

    def has_reached_end(self):
        return self.path_index >= len(self.waypoints) - 1

    def _draw_health_bar(self, screen, x, y, width, y_offset, color=(110, 228, 122)):
        bar_height = 5
        bar_x = x - width // 2
        bar_y = y + y_offset

        hp_ratio = self.hp / self.max_hp if self.max_hp > 0 else 0
        pygame.draw.rect(screen, (35, 17, 17), (bar_x - 1, bar_y - 1, width + 2, bar_height + 2), border_radius=4)
        pygame.draw.rect(screen, (93, 29, 29), (bar_x, bar_y, width, bar_height), border_radius=4)
        pygame.draw.rect(screen, color, (bar_x, bar_y, int(width * hp_ratio), bar_height), border_radius=4)

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        pygame.draw.ellipse(screen, (28, 19, 25), (x - 18, y + 8, 36, 12))
        pygame.draw.circle(screen, (162, 36, 132), (x, y), 14)
        pygame.draw.circle(screen, (255, 173, 243), (x - 4, y - 5), 4)
        pygame.draw.circle(screen, (255, 173, 243), (x + 4, y - 5), 4)
        pygame.draw.arc(screen, (67, 10, 43), (x - 8, y - 1, 16, 10), 3.3, 6.0, 2)
        self._draw_health_bar(screen, x, y, 32, -25)
