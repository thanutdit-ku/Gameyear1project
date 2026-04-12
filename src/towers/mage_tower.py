from pathlib import Path

import pygame

from src.towers.tower import Tower

SLOW_FACTOR = 0.5   # reduce speed to 50%
SLOW_DURATION = 2.0  # seconds


class MageTower(Tower):
    _frames = None
    _animation_speed = 95
    _label_font = None

    def __init__(self, position):
        super().__init__(position, cost=150)
        self.damage = 60
        self.attack_range = 120
        self.attack_speed = 0.8
        self.frames = self._load_frames()

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

    @classmethod
    def _load_frames(cls):
        if cls._frames is not None:
            return cls._frames

        base_path = (
            Path(__file__).resolve().parents[2]
            / "assets"
            / "images"
            / "enemies"
            / "dark_knight"
            / "mage"
        )
        cls._frames = []
        for index in range(1, 7):
            image = pygame.image.load(base_path / f"AttackMighty{index}.png").convert_alpha()
            image = pygame.transform.flip(image, True, False)
            bounds = image.get_bounding_rect(min_alpha=80)
            if bounds.width and bounds.height:
                image = image.subsurface(bounds).copy()
            w, h = image.get_size()
            frame = pygame.transform.scale(image, (w * 2, h * 2))
            cls._frames.append(frame)
        return cls._frames

    @classmethod
    def _get_label_font(cls):
        if cls._label_font is None:
            cls._label_font = pygame.font.SysFont("verdana", 13, bold=True)
        return cls._label_font

    def _get_current_frame(self):
        frame_index = (pygame.time.get_ticks() // self._animation_speed) % len(self.frames)
        return self.frames[frame_index]

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        sprite = self._get_current_frame()
        sprite_rect = sprite.get_rect(midbottom=(x, y + 20))
        shadow_rect = pygame.Rect(0, 0, 32, 10)
        shadow_rect.center = (x, y + 13)

        pygame.draw.ellipse(screen, (19, 21, 35), shadow_rect)
        screen.blit(sprite, sprite_rect)

        label = self._get_label_font().render(f"Lv{self.level}", True, (255, 255, 255))
        screen.blit(label, (x - label.get_width() // 2, y + 20))
