import pygame
from src.enemies.enemy import Enemy


class BossEnemy(Enemy):
    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp = 750
        self.max_hp = 750
        self.speed = 30
        self.reward_gold = 250
        self.radius = 32  # 2x normal enemy size

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        pygame.draw.ellipse(screen, (31, 12, 12), (x - 36, y + 18, 72, 16))
        pygame.draw.circle(screen, (160, 0, 0), (x, y), self.radius)
        pygame.draw.circle(screen, (220, 50, 50), (x, y), self.radius, 3)  # outline
        pygame.draw.circle(screen, (255, 195, 130), (x - 10, y - 8), 6)
        pygame.draw.circle(screen, (255, 195, 130), (x + 10, y - 8), 6)
        pygame.draw.rect(screen, (255, 228, 128), (x - 14, y + 5, 10, 8), border_radius=2)
        pygame.draw.rect(screen, (255, 228, 128), (x + 4, y + 5, 10, 8), border_radius=2)

        # Larger health bar to match the bigger sprite
        bar_width = 64
        bar_y = y - self.radius - 12
        self._draw_health_bar(screen, x, bar_y, bar_width, 0, color=(220, 180, 0))

        # "BOSS" label above the health bar
        font = pygame.font.SysFont("georgia", 18, bold=True)
        label = font.render("BOSS", True, (255, 220, 0))
        screen.blit(label, (x - label.get_width() // 2, bar_y - 16))
