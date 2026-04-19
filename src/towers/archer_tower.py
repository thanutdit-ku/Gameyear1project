import os
import pygame
import random
from src.towers.tower import Tower, TARGETING_LABELS

ANIM_FPS = 12
FRAME_SIZE = 64


class ArcherTower(Tower):
    CRIT_CHANCE = 0.2
    _frames = None

    @classmethod
    def _load_frames(cls):
        if cls._frames is not None:
            return
        folder = os.path.join("assets", "images", "enemies", "dark_knight", "Archer")
        files = sorted(f for f in os.listdir(folder) if f.endswith(".png"))
        cls._frames = [
            pygame.transform.flip(
                pygame.transform.scale(
                    pygame.image.load(os.path.join(folder, f)).convert_alpha(),
                    (FRAME_SIZE, FRAME_SIZE),
                ),
                True, False,
            )
            for f in files
        ]

    def __init__(self, position):
        super().__init__(position, cost=100)
        self.damage = 25
        self.attack_range = 150
        self.attack_speed = 1.5
        self._load_frames()

    def _on_attack(self, target, enemies):
        dmg = self.damage
        if random.random() < self.CRIT_CHANCE:
            dmg *= 2
        target.take_damage(dmg)

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)

        frame_idx = (pygame.time.get_ticks() // (1000 // ANIM_FPS)) % len(self._frames)
        frame = self._frames[frame_idx]
        screen.blit(frame, (x - FRAME_SIZE // 2, y - FRAME_SIZE // 2))

        font = pygame.font.SysFont("verdana", 12, bold=True)
        label = font.render(f"Lv{self.level}", True, (255, 255, 255))
        screen.blit(label, (x - label.get_width() // 2, y + FRAME_SIZE // 2 + 2))

        mode_surf = font.render(TARGETING_LABELS[self.targeting_mode], True, (255, 220, 80))
        screen.blit(mode_surf, (x - mode_surf.get_width() // 2, y - FRAME_SIZE // 2 - mode_surf.get_height() - 1))
