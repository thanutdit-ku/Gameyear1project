from pathlib import Path

import pygame

from src.enemies.enemy import Enemy


class Bat(Enemy):
    _frames_by_direction = None
    _frame_size = 32
    _sprite_size = (44, 44)
    _animation_speed = 110

    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp = 45
        self.max_hp = 45
        self.speed = 118
        self.reward_gold = 12
        self.spawn_spacing = 42
        self.frames_by_direction = self._load_frames()

    @classmethod
    def _load_frames(cls):
        if cls._frames_by_direction is not None:
            return cls._frames_by_direction

        sprite_path = (
            Path(__file__).resolve().parents[2]
            / "assets"
            / "images"
            / "enemies"
            / "goblin"
            / "bat.png"
        )
        sheet = pygame.image.load(sprite_path).convert_alpha()

        rows = []
        for row in range(sheet.get_height() // cls._frame_size):
            row_frames = []
            for col in range(sheet.get_width() // cls._frame_size):
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

        cls._frames_by_direction = {
            "down": rows[0],
            "right": rows[1],
            "up": rows[2],
            "left": rows[3],
        }
        return cls._frames_by_direction

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
        frames = self.frames_by_direction[direction_key]
        frame_index = (pygame.time.get_ticks() // self._animation_speed) % len(frames)
        return frames[frame_index]

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        sprite = self._get_current_frame()
        sprite_rect = sprite.get_rect(center=(x, y - 6))
        shadow_rect = pygame.Rect(0, 0, 24, 8)
        shadow_rect.center = (x, y + 10)

        pygame.draw.ellipse(screen, (24, 17, 24), shadow_rect)
        screen.blit(sprite, sprite_rect)
        self._draw_health_bar(screen, x, sprite_rect.top + 4, 24, -14, color=(186, 119, 214))
