import pygame
import sys

from src.towers.archer_tower import ArcherTower
from src.towers.mage_tower import MageTower
from src.towers.cannon_tower import CannonTower
from src.wave import Wave
from src.stats_tracker import StatsTracker
from src.ui_manager import UIManager, GAME_W, GAME_H, HUD_HEIGHT, SCREEN_W, SCREEN_H

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
    STATE_HOME      = "home"
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
        self.state    = self.STATE_HOME

        # Systems
        self.stats_tracker = StatsTracker()
        self.ui_manager    = UIManager(self.screen)

        # Placement state
        self.selected_tower_type = None   # "archer" | "mage" | "cannon"
        self.sell_mode = False
        self.tower_map = {}               # (col, row) -> Tower instance
        self.path_tiles = self._compute_path_tiles()

        # Timing
        self.wave_start_time = 0.0

        # UI elements owned by Game
        self.font = pygame.font.SysFont("georgia", 26, bold=True)
        self.font_small = pygame.font.SysFont("verdana", 16)
        self.start_wave_btn = pygame.Rect(
            GAME_W // 2 - 110, SCREEN_H - 70, 220, 44
        )
        self.home_start_btn = pygame.Rect(0, 0, 0, 0)
        self.home_quit_btn = pygame.Rect(0, 0, 0, 0)
        self.static_battlefield = self._build_static_battlefield()
        self.home_backdrop = self._build_home_backdrop()

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
                if self.state == self.STATE_HOME:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = self.STATE_PREP
                    elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                        pygame.quit()
                        sys.exit()
                    continue
                if event.key == pygame.K_ESCAPE:
                    self.selected_tower_type = None
                    self.sell_mode = False
                if event.key == pygame.K_f:
                    if self.state == self.STATE_PREP:
                        self.sell_mode = not self.sell_mode
                        if self.sell_mode:
                            self.selected_tower_type = None
                if event.key == pygame.K_q:
                    if self.state in (self.STATE_GAME_OVER, self.STATE_VICTORY):
                        pygame.quit()
                        sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_click(event.pos, event.button)

    def _get_tower_at(self, pos):
        """Return the Tower at the given screen position, or None."""
        col = pos[0] // TILE_SIZE
        row = (pos[1] - HUD_HEIGHT) // TILE_SIZE
        return self.tower_map.get((col, row))

    def _handle_click(self, pos, button):
        # Right-click: cycle targeting mode on tower under cursor
        if button == 3:
            if self.state in (self.STATE_PREP, self.STATE_WAVE):
                if pos[0] < GAME_W and pos[1] > HUD_HEIGHT:
                    tower = self._get_tower_at(pos)
                    if tower:
                        tower.cycle_targeting_mode()
            return

        if button != 1:
            return

        if self.state == self.STATE_HOME:
            if self.home_start_btn.collidepoint(pos):
                self.state = self.STATE_PREP
            elif self.home_quit_btn.collidepoint(pos):
                pygame.quit()
                sys.exit()
            return

        # Sell mode: left-click on a tower during PREP to sell it
        if self.sell_mode and self.state == self.STATE_PREP:
            if pos[0] < GAME_W and pos[1] > HUD_HEIGHT:
                col = pos[0] // TILE_SIZE
                row = (pos[1] - HUD_HEIGHT) // TILE_SIZE
                tile = (col, row)
                tower = self.tower_map.get(tile)
                if tower:
                    refund = tower.cost // 2
                    self.gold += refund
                    self.towers.remove(tower)
                    del self.tower_map[tile]
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
        if self.state == self.STATE_HOME:
            return

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
        self.sell_mode = False
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
        if self.state == self.STATE_HOME:
            self._draw_home_screen()
            pygame.display.flip()
            return

        self.screen.blit(self.static_battlefield, (0, 0))

        for tower in self.towers:
            tower.draw(self.screen)
            if self.sell_mode:
                tx, ty = int(tower.position.x), int(tower.position.y)
                tint = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                tint.fill((200, 30, 30, 110))
                pygame.draw.rect(tint, (220, 50, 50, 200), tint.get_rect(), 2)
                self.screen.blit(tint, (tx - TILE_SIZE // 2, ty - TILE_SIZE // 2))

        for enemy in self.enemies:
            enemy.draw(self.screen)

        self.ui_manager.draw_hud(self.gold, self.castle_hp, self.current_wave)
        self.ui_manager.draw_tower_panel(self.gold, self.selected_tower_type, self.sell_mode)
        self._draw_placement_preview()

        if self.state == self.STATE_PREP:
            self._draw_start_wave_button()

        if self.state in (self.STATE_GAME_OVER, self.STATE_VICTORY):
            report = self.stats_tracker.generate_report()
            self.ui_manager.draw_stats_screen(report, self.stats_tracker.history)

        pygame.display.flip()

    def _build_home_backdrop(self):
        surface = pygame.Surface((SCREEN_W, SCREEN_H))
        surface.fill((7, 10, 18))

        for offset in range(SCREEN_H):
            t = offset / max(SCREEN_H - 1, 1)
            color = (
                int(9 + (22 - 9) * t),
                int(14 + (31 - 14) * t),
                int(25 + (46 - 25) * t),
            )
            pygame.draw.line(surface, color, (0, offset), (SCREEN_W, offset))

        glow_specs = [
            ((120, 112), 180, (214, 150, 55, 52)),
            ((656, 140), 220, (75, 122, 211, 42)),
            ((580, 490), 250, (42, 125, 91, 40)),
        ]
        for center, radius, color in glow_specs:
            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, color, (radius, radius), radius)
            surface.blit(glow, (center[0] - radius, center[1] - radius))

        return surface

    def _draw_home_screen(self):
        self.screen.blit(self.home_backdrop, (0, 0))

        pulse = (pygame.time.get_ticks() % 2000) / 2000.0
        shimmer = 0.5 + 0.5 * abs(1 - pulse * 2)

        panel = pygame.Rect(42, 52, 320, 496)
        panel_shadow = panel.move(10, 14)
        pygame.draw.rect(self.screen, (4, 7, 14), panel_shadow, border_radius=32)
        pygame.draw.rect(self.screen, (15, 21, 36), panel, border_radius=32)
        pygame.draw.rect(self.screen, (63, 78, 112), panel, 2, border_radius=32)

        crest_outer = pygame.Rect(panel.x + 24, panel.y + 24, 78, 78)
        crest_inner = crest_outer.inflate(-10, -10)
        pygame.draw.ellipse(self.screen, (181, 134, 57), crest_outer)
        pygame.draw.ellipse(self.screen, (247, 213, 126), crest_inner)
        pygame.draw.circle(self.screen, (52, 38, 17), crest_inner.center, 18)
        pygame.draw.polygon(
            self.screen,
            (88, 63, 25),
            [
                (crest_inner.centerx, crest_inner.centery - 26),
                (crest_inner.centerx + 24, crest_inner.centery + 8),
                (crest_inner.centerx, crest_inner.centery + 26),
                (crest_inner.centerx - 24, crest_inner.centery + 8),
            ],
        )

        eyebrow = pygame.Rect(panel.x + 24, panel.y + 120, 252, 26)
        pygame.draw.rect(self.screen, (32, 40, 63), eyebrow, border_radius=13)
        pygame.draw.rect(self.screen, (95, 111, 148), eyebrow, 1, border_radius=13)
        eyebrow_text = pygame.font.SysFont("georgia", 12, bold=True).render(
            "TACTICAL DEFENSE CAMPAIGN",
            True,
            (212, 196, 150),
        )
        self.screen.blit(
            eyebrow_text,
            (eyebrow.centerx - eyebrow_text.get_width() // 2, eyebrow.y + 6),
        )

        title_font = pygame.font.SysFont("georgia", 31, bold=True)
        title_main = title_font.render("Kingdom's", True, (245, 238, 224))
        title_sub = title_font.render("Last Stand", True, (245, 238, 224))
        self.screen.blit(title_main, (panel.x + 24, panel.y + 182))
        self.screen.blit(title_sub, (panel.x + 24, panel.y + 220))

        accent_line = pygame.Rect(panel.x + 26, panel.y + 286, 118, 4)
        pygame.draw.rect(self.screen, (212, 165, 74), accent_line, border_radius=2)

        body_font = pygame.font.SysFont("georgia", 12, bold=True)
        body_lines = [
            "Marshal archers, mages, and cannons",
            "across a royal field. Hold the road.",
            "Protect the castle.",
        ]
        for index, line in enumerate(body_lines):
            surf = body_font.render(line, True, (149, 161, 188))
            self.screen.blit(surf, (panel.x + 24, panel.y + 314 + index * 22))

        feature_specs = [
            ((panel.x + 24, panel.y + 386, 82, 54), (65, 173, 89), "ARCHER", "Rapid shots"),
            ((panel.x + 119, panel.y + 386, 82, 54), (147, 93, 232), "MAGE", "Slow control"),
            ((panel.x + 214, panel.y + 386, 82, 54), (218, 109, 32), "CANNON", "Splash burst"),
        ]
        for rect_args, color, title, desc in feature_specs:
            rect = pygame.Rect(*rect_args)
            pygame.draw.rect(self.screen, (22, 30, 49), rect, border_radius=18)
            pygame.draw.rect(self.screen, (68, 82, 112), rect, 1, border_radius=18)
            gem_rect = pygame.Rect(rect.x + 10, rect.y + 8, 16, 38)
            pygame.draw.rect(self.screen, color, gem_rect, border_radius=8)
            title_surf = pygame.font.SysFont("georgia", 10, bold=True).render(title, True, (240, 233, 220))
            desc_surf = pygame.font.SysFont("georgia", 8, bold=True).render(desc, True, (145, 157, 184))
            self.screen.blit(title_surf, (rect.x + 34, rect.y + 10))
            self.screen.blit(desc_surf, (rect.x + 34, rect.y + 28))

        self.home_start_btn = pygame.Rect(panel.x + 24, panel.y + 450, 270, 48)
        self.home_quit_btn = pygame.Rect(panel.x + 82, panel.y + 510, 128, 24)

        self._draw_home_button(
            self.home_start_btn,
            "Start Campaign",
            "Begin your first defense",
            (241, 188, 53),
            (184, 117, 19),
            hover=self.home_start_btn.collidepoint(pygame.mouse.get_pos()),
            glow_strength=shimmer,
        )
        self._draw_home_button(
            self.home_quit_btn,
            "Quit",
            "Exit the game",
            (54, 65, 94),
            (27, 34, 52),
            hover=self.home_quit_btn.collidepoint(pygame.mouse.get_pos()),
            glow_strength=0.0,
        )

        preview_rect = pygame.Rect(392, 52, 364, 496)
        preview_shadow = preview_rect.move(12, 16)
        pygame.draw.rect(self.screen, (4, 6, 12), preview_shadow, border_radius=34)
        pygame.draw.rect(self.screen, (15, 20, 32), preview_rect, border_radius=34)
        pygame.draw.rect(self.screen, (61, 76, 109), preview_rect, 2, border_radius=34)

        ribbon = pygame.Rect(preview_rect.x + 26, preview_rect.y + 24, 136, 28)
        pygame.draw.rect(self.screen, (35, 45, 68), ribbon, border_radius=14)
        pygame.draw.rect(self.screen, (96, 112, 146), ribbon, 1, border_radius=14)
        ribbon_text = pygame.font.SysFont("georgia", 12, bold=True).render("ROYAL DEFENSE", True, (218, 201, 154))
        self.screen.blit(ribbon_text, (ribbon.centerx - ribbon_text.get_width() // 2, ribbon.y + 6))

        mini_field = pygame.Rect(preview_rect.x + 24, preview_rect.y + 70, preview_rect.width - 48, 274)
        self._draw_home_preview_field(mini_field)

        stat_cards = [
            (pygame.Rect(preview_rect.x + 24, preview_rect.bottom - 112, 96, 74), "10", "WAVES", (217, 177, 79)),
            (pygame.Rect(preview_rect.x + 132, preview_rect.bottom - 112, 96, 74), "3", "TOWERS", (112, 182, 255)),
            (pygame.Rect(preview_rect.x + 240, preview_rect.bottom - 112, 96, 74), "1", "CASTLE", (232, 112, 104)),
        ]
        for rect, value, label, color in stat_cards:
            pygame.draw.rect(self.screen, (22, 29, 47), rect, border_radius=20)
            pygame.draw.rect(self.screen, (71, 85, 116), rect, 1, border_radius=20)
            orb = pygame.Rect(rect.x + 12, rect.y + 12, 18, 18)
            pygame.draw.ellipse(self.screen, color, orb)
            value_surf = pygame.font.SysFont("georgia", 26, bold=True).render(value, True, (244, 238, 228))
            label_surf = pygame.font.SysFont("georgia", 10, bold=True).render(label, True, (138, 151, 179))
            self.screen.blit(value_surf, (rect.x + 14, rect.y + 28))
            self.screen.blit(label_surf, (rect.x + 42, rect.y + 16))

    def _draw_home_button(self, rect, title, subtitle, top, bottom, hover=False, glow_strength=0.0):
        shadow = rect.move(0, 8)
        pygame.draw.rect(self.screen, (10, 13, 22), shadow, border_radius=22)

        height = max(rect.height, 1)
        for offset in range(height):
            t = offset / height
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(self.screen, color, (rect.left, rect.top + offset), (rect.right, rect.top + offset))

        border = (255, 233, 168) if hover else (242, 214, 128)
        pygame.draw.rect(self.screen, border, rect, 3, border_radius=22)
        inner = rect.inflate(-8, -8)
        inner_glow = pygame.Surface((inner.width, inner.height), pygame.SRCALPHA)
        pygame.draw.rect(inner_glow, (255, 245, 205, 48), inner_glow.get_rect(), 1, border_radius=18)
        self.screen.blit(inner_glow, inner.topleft)

        title_color = (37, 26, 10) if top[0] > 120 else (236, 239, 246)
        subtitle_color = (104, 68, 18) if top[0] > 120 else (143, 154, 182)
        if rect.height >= 46:
            title_surf = pygame.font.SysFont("georgia", 21, bold=True).render(title, True, title_color)
            subtitle_surf = pygame.font.SysFont("georgia", 10, bold=True).render(subtitle, True, subtitle_color)
            self.screen.blit(title_surf, (rect.centerx - title_surf.get_width() // 2, rect.y + 9))
            self.screen.blit(subtitle_surf, (rect.centerx - subtitle_surf.get_width() // 2, rect.y + 34))
        else:
            title_surf = pygame.font.SysFont("georgia", 14, bold=True).render(title, True, title_color)
            self.screen.blit(title_surf, (rect.centerx - title_surf.get_width() // 2, rect.centery - title_surf.get_height() // 2 - 1))

    def _draw_home_preview_field(self, rect):
        pygame.draw.rect(self.screen, (20, 70, 43), rect, border_radius=28)
        inset = rect.inflate(-12, -12)
        pygame.draw.rect(self.screen, (31, 98, 55), inset, border_radius=24)

        cell = 28
        light = (42, 116, 67)
        dark = (28, 88, 52)
        for row in range((inset.height // cell) + 1):
            for col in range((inset.width // cell) + 1):
                tile = pygame.Rect(inset.x + col * cell, inset.y + row * cell, cell, cell)
                pygame.draw.rect(self.screen, light if (row + col) % 2 == 0 else dark, tile)

        for x in range(inset.x, inset.right + 1, cell):
            pygame.draw.line(self.screen, (118, 171, 103), (x, inset.y), (x, inset.bottom), 1)
        for y in range(inset.y, inset.bottom + 1, cell):
            pygame.draw.line(self.screen, (118, 171, 103), (inset.x, y), (inset.right, y), 1)

        path_points = [
            (inset.x - 8, inset.y + 56),
            (inset.x + 120, inset.y + 56),
            (inset.x + 120, inset.y + 192),
            (inset.x + 236, inset.y + 192),
            (inset.x + 236, inset.y + 100),
            (inset.right + 8, inset.y + 100),
        ]
        for width, color in ((34, (144, 94, 36)), (26, (231, 199, 123)), (16, (244, 221, 159))):
            pygame.draw.lines(self.screen, color, False, path_points, width)

        for i in range(len(path_points) - 1):
            x1, y1 = path_points[i]
            x2, y2 = path_points[i + 1]
            steps = max(abs(x2 - x1), abs(y2 - y1)) // 26 + 1
            for step in range(steps):
                t = step / max(steps - 1, 1)
                x = int(x1 + (x2 - x1) * t)
                y = int(y1 + (y2 - y1) * t)
                pygame.draw.circle(self.screen, (147, 101, 46), (x, y), 3)

        for corner in (
            (rect.left + 14, rect.top + 14, 24, 24, 180, 270),
            (rect.right - 38, rect.top + 14, 24, 24, 270, 360),
            (rect.left + 14, rect.bottom - 38, 24, 24, 90, 180),
            (rect.right - 38, rect.bottom - 38, 24, 24, 0, 90),
        ):
            arc_rect = pygame.Rect(*corner[:4])
            pygame.draw.arc(
                self.screen,
                (215, 177, 91),
                arc_rect,
                corner[4] * 3.14159 / 180,
                corner[5] * 3.14159 / 180,
                4,
            )

    def _build_static_battlefield(self):
        surface = pygame.Surface((SCREEN_W, SCREEN_H))
        self._draw_battlefield_background(surface)
        self._draw_path(surface)
        self._draw_grid(surface)
        self._draw_field_frame(surface)
        self._draw_castle(surface)
        return surface

    def _draw_battlefield_background(self, surface=None):
        target = surface or self.screen
        target.fill((13, 18, 30))
        field_rect = pygame.Rect(0, HUD_HEIGHT, GAME_W, SCREEN_H - HUD_HEIGHT)
        dark_tile = (30, 95, 51)
        light_tile = (36, 108, 59)
        cols = GAME_W // TILE_SIZE + 1
        rows = (SCREEN_H - HUD_HEIGHT) // TILE_SIZE + 1

        for row in range(rows):
            for col in range(cols):
                tile_rect = pygame.Rect(
                    col * TILE_SIZE,
                    HUD_HEIGHT + row * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                color = light_tile if (row + col) % 2 == 0 else dark_tile
                pygame.draw.rect(target, color, tile_rect)

        field_glow = pygame.Surface((field_rect.width, field_rect.height), pygame.SRCALPHA)
        field_glow.fill((247, 230, 168, 12))
        target.blit(field_glow, field_rect.topleft)

    def _draw_path(self, surface=None):
        target = surface or self.screen
        for i in range(len(WAYPOINTS) - 1):
            pygame.draw.line(
                target, (152, 102, 38),
                WAYPOINTS[i], WAYPOINTS[i + 1], TILE_SIZE + 8
            )
            pygame.draw.line(
                target, (231, 197, 120),
                WAYPOINTS[i], WAYPOINTS[i + 1], TILE_SIZE
            )
            pygame.draw.line(
                target, (240, 214, 150),
                WAYPOINTS[i], WAYPOINTS[i + 1], TILE_SIZE - 16
            )

        for i in range(len(WAYPOINTS) - 1):
            x1, y1 = WAYPOINTS[i]
            x2, y2 = WAYPOINTS[i + 1]
            steps = max(abs(x2 - x1), abs(y2 - y1)) // 34 + 1
            for step in range(steps):
                t = step / max(steps - 1, 1)
                x = int(x1 + (x2 - x1) * t)
                y = int(y1 + (y2 - y1) * t)
                pygame.draw.circle(target, (139, 92, 35), (x, y), 4)

    def _draw_grid(self, surface=None):
        target = surface or self.screen
        color = (128, 176, 117)
        for col in range(GAME_W // TILE_SIZE + 1):
            x = col * TILE_SIZE
            pygame.draw.line(target, color, (x, HUD_HEIGHT), (x, SCREEN_H), 1)
        for row in range((SCREEN_H - HUD_HEIGHT) // TILE_SIZE + 1):
            y = row * TILE_SIZE + HUD_HEIGHT
            pygame.draw.line(target, color, (0, y), (GAME_W, y), 1)

    def _draw_field_frame(self, surface=None):
        target = surface or self.screen
        outer = pygame.Rect(8, HUD_HEIGHT + 8, GAME_W - 16, SCREEN_H - HUD_HEIGHT - 16)
        inner = outer.inflate(-8, -8)
        pygame.draw.rect(target, (149, 114, 58), outer, 3, border_radius=16)
        pygame.draw.rect(target, (225, 194, 116), inner, 2, border_radius=14)

        corner = 16
        lines = [
            ((inner.left + 10, inner.top + 8), (inner.left + 10 + corner, inner.top + 8)),
            ((inner.left + 8, inner.top + 10), (inner.left + 8, inner.top + 10 + corner)),
            ((inner.right - 10 - corner, inner.top + 8), (inner.right - 10, inner.top + 8)),
            ((inner.right - 8, inner.top + 10), (inner.right - 8, inner.top + 10 + corner)),
            ((inner.left + 10, inner.bottom - 8), (inner.left + 10 + corner, inner.bottom - 8)),
            ((inner.left + 8, inner.bottom - 10 - corner), (inner.left + 8, inner.bottom - 10)),
            ((inner.right - 10 - corner, inner.bottom - 8), (inner.right - 10, inner.bottom - 8)),
            ((inner.right - 8, inner.bottom - 10 - corner), (inner.right - 8, inner.bottom - 10)),
        ]
        for start, end in lines:
            pygame.draw.line(target, (225, 194, 116), start, end, 3)

    def _draw_castle(self, surface=None):
        target = surface or self.screen
        cx, cy = WAYPOINTS[-1]
        shadow = pygame.Rect(cx - 18, cy + 12, 74, 18)
        base = pygame.Rect(cx - 10, cy - 18, 46, 34)
        left_tower = pygame.Rect(cx - 18, cy - 28, 14, 30)
        right_tower = pygame.Rect(cx + 30, cy - 28, 14, 30)
        gate = pygame.Rect(cx + 8, cy - 2, 10, 18)

        pygame.draw.ellipse(target, (33, 46, 31), shadow)
        pygame.draw.rect(target, (146, 149, 164), base, border_radius=5)
        pygame.draw.rect(target, (205, 208, 219), base, 2, border_radius=5)
        pygame.draw.rect(target, (132, 136, 151), left_tower, border_radius=4)
        pygame.draw.rect(target, (132, 136, 151), right_tower, border_radius=4)
        pygame.draw.rect(target, (89, 66, 44), gate, border_radius=3)

        for tower in (left_tower, right_tower):
            for i in range(2):
                crenel = pygame.Rect(tower.x + 2 + i * 5, tower.y - 4, 3, 5)
                pygame.draw.rect(target, (205, 208, 219), crenel, border_radius=1)

        flag_pole_top = (right_tower.right - 1, right_tower.y - 10)
        pygame.draw.line(target, (94, 70, 45), flag_pole_top, (right_tower.right - 1, right_tower.y + 6), 2)
        pygame.draw.polygon(
            target,
            (191, 58, 67),
            [
                (flag_pole_top[0], flag_pole_top[1]),
                (flag_pole_top[0] + 13, flag_pole_top[1] + 4),
                (flag_pole_top[0], flag_pole_top[1] + 8),
            ],
        )

        label = self.font.render("Castle", True, (248, 239, 208))
        target.blit(label, (cx - label.get_width() // 2 + 28, cy + 10))

    def _draw_start_wave_button(self):
        label_text = f"Start Wave {self.current_wave + 1}"
        self.start_wave_btn = pygame.Rect(GAME_W // 2 - 128, SCREEN_H - 84, 256, 50)
        hover = self.start_wave_btn.collidepoint(pygame.mouse.get_pos())
        top = (244, 195, 50) if hover else (229, 181, 43)
        bottom = (188, 125, 18)
        shadow_rect = self.start_wave_btn.move(12, 10)
        pygame.draw.rect(self.screen, (64, 75, 45), shadow_rect, border_radius=16)
        for offset in range(self.start_wave_btn.height):
            t = offset / max(self.start_wave_btn.height, 1)
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(
                self.screen,
                color,
                (self.start_wave_btn.left, self.start_wave_btn.top + offset),
                (self.start_wave_btn.right, self.start_wave_btn.top + offset),
            )
        inner = self.start_wave_btn.inflate(-6, -6)
        accent = self.start_wave_btn.inflate(6, 6)
        pygame.draw.rect(self.screen, (247, 222, 118), accent, 2, border_radius=18)
        pygame.draw.rect(self.screen, (246, 214, 97), self.start_wave_btn, 3, border_radius=16)
        pygame.draw.rect(self.screen, (249, 229, 145), inner, 1, border_radius=14)
        text = self.font.render(label_text, True, (38, 28, 10))
        sub = self.font_small.render("Release the next enemy march", True, (101, 69, 19))
        self.screen.blit(
            text,
            (self.start_wave_btn.centerx - text.get_width() // 2,
             self.start_wave_btn.y + 7)
        )
        self.screen.blit(sub, (self.start_wave_btn.centerx - sub.get_width() // 2, self.start_wave_btn.y + 31))

    def _draw_placement_preview(self):
        if not self.selected_tower_type:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        if mouse_x >= GAME_W or mouse_y <= HUD_HEIGHT:
            return

        col = mouse_x // TILE_SIZE
        row = (mouse_y - HUD_HEIGHT) // TILE_SIZE
        tile = (col, row)
        rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE + HUD_HEIGHT, TILE_SIZE, TILE_SIZE)
        valid = tile not in self.path_tiles and tile not in self.tower_map and self.gold >= TOWER_COSTS[self.selected_tower_type]
        fill = (111, 196, 118) if valid else (196, 92, 92)
        outline = (227, 248, 210) if valid else (249, 214, 214)

        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, outline, rect, 2, border_radius=8)

        center = rect.center
        range_radius = int(TOWER_CLASSES[self.selected_tower_type]((0, 0)).attack_range)
        pygame.draw.circle(self.screen, (*fill, 40), center, range_radius, 1)

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
