import pygame
import sys

from src.towers.archer_tower import ArcherTower
from src.towers.mage_tower import MageTower
from src.towers.cannon_tower import CannonTower
from src.wave import Wave
from src.stats_tracker import StatsTracker
from src.ui_manager import UIManager, GAME_W, HUD_HEIGHT, SCREEN_W, SCREEN_H

FPS = 60
TILE_SIZE = 40
MAX_WAVES = 10
CASTLE_DAMAGE_PER_ENEMY = 10

# Predefined enemy path: list of (x, y) screen-pixel waypoints
WAYPOINTS = [
    (0,   150),
    (200, 150),
    (200, 380),
    (440, 380),
    (440, 250),
    (600, 250),
]

TOWER_CLASSES = {
    "archer": ArcherTower,
    "mage":   MageTower,
    "cannon": CannonTower,
}

TOWER_COSTS = {
    "archer": 100,
    "mage":   150,
    "cannon": 125,
}


class Game:
    STATE_PREP      = "prep"
    STATE_WAVE      = "wave"
    STATE_GAME_OVER = "game_over"
    STATE_VICTORY   = "victory"

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Kingdom's Last Stand")
        self.clock = pygame.time.Clock()

        # Core game state
        self.gold       = 200
        self.castle_hp  = 100
        self.current_wave = 0
        self.towers   = []
        self.enemies  = []
        self.wave     = None
        self.state    = self.STATE_PREP

        # Systems
        self.stats_tracker = StatsTracker()
        self.ui_manager    = UIManager(self.screen)

        # Placement state
        self.selected_tower_type = None   # "archer" | "mage" | "cannon"
        self.tower_map = {}               # (col, row) -> Tower instance
        self.path_tiles = self._compute_path_tiles()

        # Timing
        self.wave_start_time = 0.0

        # UI elements owned by Game
        self.font = pygame.font.SysFont(None, 28)
        self.start_wave_btn = pygame.Rect(
            GAME_W // 2 - 110, SCREEN_H - 70, 220, 44
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self.update(dt)
            self.draw()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.selected_tower_type = None
                if event.key == pygame.K_q:
                    if self.state in (self.STATE_GAME_OVER, self.STATE_VICTORY):
                        pygame.quit()
                        sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_click(event.pos, event.button)

    def _handle_click(self, pos, button):
        if button != 1:
            return

        # Tower panel buttons
        tower_key = self.ui_manager.get_tower_clicked(pos)
        if tower_key:
            self.selected_tower_type = tower_key
            return

        # Start Wave button (prep phase only)
        if self.state == self.STATE_PREP:
            if self.start_wave_btn.collidepoint(pos):
                self.next_wave()
                return

        # Place tower on the game area
        if self.state in (self.STATE_PREP, self.STATE_WAVE):
            if pos[0] < GAME_W and pos[1] > HUD_HEIGHT:
                self._try_place_tower(pos)

    # ------------------------------------------------------------------
    # Tower placement
    # ------------------------------------------------------------------

    def _try_place_tower(self, pos):
        if not self.selected_tower_type:
            return

        col = pos[0] // TILE_SIZE
        row = (pos[1] - HUD_HEIGHT) // TILE_SIZE
        tile = (col, row)

        if tile in self.path_tiles:
            return
        if tile in self.tower_map:
            return

        cost = TOWER_COSTS[self.selected_tower_type]
        if self.gold < cost:
            return

        px = col * TILE_SIZE + TILE_SIZE // 2
        py = row * TILE_SIZE + HUD_HEIGHT + TILE_SIZE // 2
        tower = TOWER_CLASSES[self.selected_tower_type]((px, py))

        self.towers.append(tower)
        self.tower_map[tile] = tower
        self.gold -= cost
        self.stats_tracker.record_gold_spent(cost)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt):
        if self.state != self.STATE_WAVE:
            return

        # 1. Spawn next enemy from the wave queue
        new_enemy = self.wave.update(dt)
        if new_enemy:
            self.enemies.append(new_enemy)

        # 2. Move enemies; collect those that reached the castle
        reached_end = []
        for enemy in self.enemies:
            self._tick_slow(enemy, dt)
            enemy.move(dt)
            if enemy.has_reached_end():
                reached_end.append(enemy)

        for enemy in reached_end:
            self.castle_hp = max(0, self.castle_hp - CASTLE_DAMAGE_PER_ENEMY)
            self.enemies.remove(enemy)

        # 3. Towers attack; measure net HP lost across all enemies this frame
        hp_before = sum(e.hp for e in self.enemies)
        for tower in self.towers:
            tower.attack(self.enemies, dt)
        hp_after = sum(e.hp for e in self.enemies)
        dmg_dealt = hp_before - hp_after
        if dmg_dealt > 0:
            self.stats_tracker.record_damage(int(dmg_dealt))

        # 4. Remove dead enemies and reward gold
        dead = [e for e in self.enemies if e.is_dead()]
        for enemy in dead:
            self.gold += enemy.reward_gold
            self.stats_tracker.record_kill()
            self.enemies.remove(enemy)

        # 5. Check castle destroyed
        if self.check_game_over():
            self._end_wave()
            return

        # 6. Check wave fully cleared
        if self.wave.is_wave_complete() and not self.enemies:
            self._end_wave()

    def _tick_slow(self, enemy, dt):
        """Tick down MageTower slow and restore base speed when it expires."""
        if hasattr(enemy, "slow_timer"):
            enemy.slow_timer -= dt
            if enemy.slow_timer <= 0:
                enemy.speed = enemy.base_speed
                del enemy.slow_timer
                del enemy.base_speed

    # ------------------------------------------------------------------
    # Wave management
    # ------------------------------------------------------------------

    def next_wave(self):
        """Advance to the next wave (called by Start Wave button or externally)."""
        self.current_wave += 1
        self.wave = Wave(self.current_wave, WAYPOINTS)
        self.state = self.STATE_WAVE
        self.wave_start_time = pygame.time.get_ticks() / 1000.0

    def _end_wave(self):
        survival_time = pygame.time.get_ticks() / 1000.0 - self.wave_start_time
        self.stats_tracker.save_to_csv(
            self.current_wave, self.castle_hp, survival_time
        )

        if self.check_game_over():
            self.state = self.STATE_GAME_OVER
        elif self.current_wave >= MAX_WAVES:
            self.state = self.STATE_VICTORY
        else:
            self.state = self.STATE_PREP

    def check_game_over(self):
        return self.castle_hp <= 0

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self):
        self.screen.fill((34, 85, 34))   # grass background

        self._draw_path()
        self._draw_grid()
        self._draw_castle()

        for tower in self.towers:
            tower.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        self.ui_manager.draw_hud(self.gold, self.castle_hp, self.current_wave)
        self.ui_manager.draw_tower_panel(self.gold, self.selected_tower_type)

        if self.state == self.STATE_PREP:
            self._draw_start_wave_button()

        if self.state in (self.STATE_GAME_OVER, self.STATE_VICTORY):
            report = self.stats_tracker.generate_report()
            self.ui_manager.draw_stats_screen(report, self.stats_tracker.history)

        pygame.display.flip()

    def _draw_path(self):
        for i in range(len(WAYPOINTS) - 1):
            pygame.draw.line(
                self.screen, (180, 140, 80),
                WAYPOINTS[i], WAYPOINTS[i + 1], TILE_SIZE
            )

    def _draw_grid(self):
        color = (44, 95, 44)
        for col in range(GAME_W // TILE_SIZE + 1):
            x = col * TILE_SIZE
            pygame.draw.line(self.screen, color, (x, HUD_HEIGHT), (x, SCREEN_H), 1)
        for row in range((SCREEN_H - HUD_HEIGHT) // TILE_SIZE + 1):
            y = row * TILE_SIZE + HUD_HEIGHT
            pygame.draw.line(self.screen, color, (0, y), (GAME_W, y), 1)

    def _draw_castle(self):
        cx, cy = WAYPOINTS[-1]
        body = pygame.Rect(cx - 14, cy - 28, 36, 44)
        pygame.draw.rect(self.screen, (110, 90, 65), body, border_radius=3)
        pygame.draw.rect(self.screen, (160, 130, 90), body, 2, border_radius=3)
        label = self.font.render("Castle", True, (255, 240, 180))
        self.screen.blit(label, (cx - label.get_width() // 2, cy + 20))

    def _draw_start_wave_button(self):
        label_text = f"Start Wave {self.current_wave + 1}"
        pygame.draw.rect(self.screen, (200, 160, 0), self.start_wave_btn, border_radius=8)
        pygame.draw.rect(self.screen, (255, 220, 50), self.start_wave_btn, 2, border_radius=8)
        text = self.font.render(label_text, True, (20, 20, 20))
        self.screen.blit(
            text,
            (self.start_wave_btn.centerx - text.get_width() // 2,
             self.start_wave_btn.centery - text.get_height() // 2)
        )

    # ------------------------------------------------------------------
    # Path tile computation
    # ------------------------------------------------------------------

    def _compute_path_tiles(self):
        """Return a set of (col, row) tiles that overlap the enemy path.
        These tiles are blocked from tower placement."""
        path_tiles = set()
        for i in range(len(WAYPOINTS) - 1):
            x1, y1 = WAYPOINTS[i]
            x2, y2 = WAYPOINTS[i + 1]
            steps = max(abs(x2 - x1), abs(y2 - y1)) // 4 + 1
            for s in range(steps + 1):
                t = s / steps
                px = int(x1 + (x2 - x1) * t)
                py = int(y1 + (y2 - y1) * t)
                col = px // TILE_SIZE
                row = (py - HUD_HEIGHT) // TILE_SIZE
                # Buffer one tile on each side to match path visual width
                for dc in range(-1, 2):
                    for dr in range(-1, 2):
                        path_tiles.add((col + dc, row + dr))
        return path_tiles
