import pygame
from src.enemies.enemy import Enemy


class BossEnemy(Enemy):
    def __init__(self, waypoints):
        super().__init__(waypoints)
        self.hp = 750
        self.max_hp = 750
        self.speed = 1.125
        self.reward_gold = 250
        self.radius = 32  # 2x normal enemy size

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)

        # Placeholder: dark red circle at 2x size
        pygame.draw.circle(screen, (160, 0, 0), (x, y), self.radius)
        pygame.draw.circle(screen, (220, 50, 50), (x, y), self.radius, 3)  # outline

        # Larger health bar to match the bigger sprite
        bar_width = 64
        bar_height = 7
        bar_x = x - bar_width // 2
        bar_y = y - self.radius - 12

        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (220, 180, 0), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))

        # "BOSS" label above the health bar
        font = pygame.font.SysFont(None, 18)
        label = font.render("BOSS", True, (255, 220, 0))
        screen.blit(label, (x - label.get_width() // 2, bar_y - 16))
