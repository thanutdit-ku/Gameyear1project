from pathlib import Path

import pygame

from src.enemies.enemy import Enemy


class SwordShield(Enemy):
    _frames = None
    _frame_size = 64
    _sprite_size = (52, 52)
    _animation_speed = 140

    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp = 95
        self.max_hp = 95
        self.speed = 72
        self.reward_gold = 16
        self.spawn_spacing = 56
        self.frames = self._load_frames()

    @classmethod
    def _load_frames(cls):
        if cls._frames is not None:
            return cls._frames

        sprite_path = (
            Path(__file__).resolve().parents[2]
            / "assets"
            / "images"
            / "enemies"
            / "goblin"
            / "swordshield.png"
        )
        sheet = pygame.image.load(sprite_path).convert_alpha()

        rows = []
        for row in range(4):
            row_frames = []
            for col in range(4):
                frame_rect = pygame.Rect(
                    col * cls._frame_size,
                    row * cls._frame_size,
                    cls._frame_size,
                    cls._frame_size,
                )
                frame = pygame.Surface(frame_rect.size, pygame.SRCALPHA)
                frame.blit(sheet, (0, 0), frame_rect)
                row_frames.append(pygame.transform.smoothscale(frame, cls._sprite_size))
            rows.append(row_frames)

        cls._frames = {
            "down": rows[0],
            "up": rows[1],
            "right": rows[2],
            "left": rows[3],
        }
        return cls._frames

    def _get_direction_key(self):
        if self.path_index < len(self.waypoints) - 1:
            target = pygame.Vector2(self.waypoints[self.path_index + 1])
            direction = target - self.position
            if direction.length_squared() > 0:
                if abs(direction.y) > abs(direction.x):
                    return "down" if direction.y > 0 else "up"
                return "right" if direction.x > 0 else "left"
        return "right"

    def _get_current_frame(self):
        direction_key = self._get_direction_key()
        frames = self.frames[direction_key]
        frame_index = (pygame.time.get_ticks() // self._animation_speed) % len(frames)
        return frames[frame_index]

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        sprite = self._get_current_frame()
        sprite_rect = sprite.get_rect(midbottom=(x, y + 18))
        shadow_rect = pygame.Rect(0, 0, 26, 10)
        shadow_rect.center = (x, y + 12)

        pygame.draw.ellipse(screen, (28, 19, 20), shadow_rect)
        screen.blit(sprite, sprite_rect)
        self._draw_health_bar(screen, x, sprite_rect.top + 8, 30, -18, color=(126, 214, 150))
