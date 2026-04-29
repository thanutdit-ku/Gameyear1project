import os
import pygame
from src.towers.tower import Tower, TARGETING_LABELS
from src.projectiles import Cannonball

ANIM_FPS = 8
FRAME_SIZE = 64
NUM_FRAMES = 8


class CannonTower(Tower):
    SPLASH_RADIUS = 50
    _frames = None

    @classmethod
    def _load_frames(cls):
        if cls._frames is not None:
            return
        sheet_path = os.path.join("assets", "images", "enemies", "dark_knight", "Cannon", "cannon-sheet.png")
        sheet = pygame.image.load(sheet_path).convert_alpha()
        cls._frames = []
        for i in range(NUM_FRAMES):
            frame = sheet.subsurface(pygame.Rect(i * FRAME_SIZE, 0, FRAME_SIZE, FRAME_SIZE))
            cls._frames.append(pygame.transform.flip(
                pygame.transform.scale(frame, (FRAME_SIZE, FRAME_SIZE)),
                True, False,
            ))

    def __init__(self, position):
        super().__init__(position, cost=125)
        self.damage = 10
        self.attack_range = 100
        self.attack_speed = 2.5
        self._load_frames()

    def _on_attack(self, target, enemies):
        return Cannonball(self.position, target, self.damage)

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)

        frame_idx = (pygame.time.get_ticks() // (1000 // ANIM_FPS)) % NUM_FRAMES
        frame = self._frames[frame_idx]
        screen.blit(frame, (x - FRAME_SIZE // 2, y - FRAME_SIZE // 2))

        font = pygame.font.SysFont("verdana", 12, bold=True)
        label = font.render(f"Lv{self.level}", True, (255, 255, 255))
        screen.blit(label, (x - label.get_width() // 2, y + FRAME_SIZE // 2 + 2))

        mode_surf = font.render(TARGETING_LABELS[self.targeting_mode], True, (255, 220, 80))
        screen.blit(mode_surf, (x - mode_surf.get_width() // 2, y - FRAME_SIZE // 2 - mode_surf.get_height() - 1))
