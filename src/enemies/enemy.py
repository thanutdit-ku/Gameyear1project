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

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)

        # Placeholder: magenta circle for the enemy body
        pygame.draw.circle(screen, (200, 0, 200), (x, y), 16)

        # Health bar
        bar_width = 32
        bar_height = 5
        bar_x = x - bar_width // 2
        bar_y = y - 26

        hp_ratio = self.hp / self.max_hp if self.max_hp > 0 else 0
        pygame.draw.rect(screen, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
