from pathlib import Path

import pygame
from src.enemies.enemy import Enemy

_ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "images" / "enemies" / "boss"

_FRAME_W    = 144
_FRAME_H    = 128
_COLS       = 3
_DISPLAY_W  = 90
_DISPLAY_H  = 80
_ANIM_SPEED = 150   # ms per frame — matches original preview delay
_BG_COLOR   = (71, 112, 76)

# Row layout: N=0, E=1, S=2, W=3
_DIR_ROWS = {"up": 0, "right": 1, "down": 2, "left": 3}


def _load_dragon_frames():
    # Sheet has no alpha — use colorkey then blit to SRCALPHA so scale preserves transparency
    sheet = pygame.image.load(_ASSET_DIR / "dragon.png").convert()
    sheet.set_colorkey(_BG_COLOR)
    frames = {direction: [] for direction in _DIR_ROWS}
    for direction, row in _DIR_ROWS.items():
        for col in range(_COLS):
            rect = pygame.Rect(col * _FRAME_W, row * _FRAME_H, _FRAME_W, _FRAME_H)
            frame = pygame.Surface((_FRAME_W, _FRAME_H), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), rect)
            frames[direction].append(
                pygame.transform.smoothscale(frame, (_DISPLAY_W, _DISPLAY_H))
            )
    return frames


class BossEnemy(Enemy):
    _frames = None

    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp          = 750
        self.max_hp      = 750
        self.speed       = 30
        self.reward_gold = 250
        self.radius      = 36
        self._load_all_frames()

    @classmethod
    def _load_all_frames(cls):
        if cls._frames is None:
            cls._frames = _load_dragon_frames()

    def _direction_key(self):
        if self.path_index < len(self.waypoints) - 1:
            target    = pygame.Vector2(self.waypoints[self.path_index + 1])
            direction = target - self.position
            if direction.length_squared() > 0:
                if abs(direction.x) >= abs(direction.y):
                    return "right" if direction.x > 0 else "left"
                return "down" if direction.y > 0 else "up"
        return "right"

    def _current_frame(self):
        key   = self._direction_key()
        frames = self._frames[key]
        idx   = (pygame.time.get_ticks() // _ANIM_SPEED) % len(frames)
        return frames[idx]

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        sprite = self._current_frame()
        rect   = sprite.get_rect(center=(x, y))

        # Shadow
        shadow = pygame.Rect(0, 0, 60, 16)
        shadow.center = (x, y + self.radius + 4)
        pygame.draw.ellipse(screen, (20, 14, 14), shadow)

        screen.blit(sprite, rect)

        # Health bar + BOSS label
        bar_y = rect.top + 4
        self._draw_health_bar(screen, x, bar_y, 70, 0, color=(220, 180, 0))

        font  = pygame.font.SysFont("georgia", 16, bold=True)
        label = font.render("BOSS", True, (255, 220, 0))
        screen.blit(label, (x - label.get_width() // 2, bar_y - 18))
