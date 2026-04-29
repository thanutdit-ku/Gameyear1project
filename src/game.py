import pygame
import sys
import unicodedata
import random
from collections import Counter

from src.towers.archer_tower import ArcherTower
from src.towers.mage_tower import MageTower
from src.towers.cannon_tower import CannonTower
from src.projectiles import Projectile
from src.wave import Wave
from src.enemies.slime import MiniSlime
from src.stats_tracker import StatsTracker
from src.ui_manager import UIManager, GAME_W, GAME_H, HUD_HEIGHT, PANEL_WIDTH, SCREEN_W, SCREEN_H

FPS = 60
TILE_SIZE = 40
MAX_WAVES = 10
CASTLE_DAMAGE_PER_ENEMY = 10
START_FULLSCREEN = True

# Map definitions. Waypoints are screen-pixel coordinates that enemies follow.
MAPS = [
    {
        "name": "Royal Road",
        "tagline": "Balanced route",
        "waypoints": [
            (0,   150),
            (200, 150),
            (200, 380),
            (440, 380),
            (440, 250),
            (600, 250),
        ],
        "field": ((30, 95, 51), (36, 108, 59)),
        "grid": (128, 176, 117),
    },
    {
        "name": "Twin Bend",
        "tagline": "Longer turns",
        "waypoints": [
            (0,   240),
            (140, 240),
            (140, 450),
            (300, 450),
            (300, 320),
            (460, 320),
            (460, 500),
            (600, 500),
        ],
        "field": ((28, 76, 71), (34, 93, 82)),
        "grid": (107, 166, 151),
    },
    {
        "name": "Southern Pass",
        "tagline": "Late castle turn",
        "waypoints": [
            (0,   420),
            (160, 420),
            (160, 300),
            (320, 300),
            (320, 170),
            (520, 170),
            (520, 360),
            (600, 360),
        ],
        "field": ((70, 80, 42), (85, 96, 49)),
        "grid": (160, 168, 96),
    },
    {
        "name": "Stone Spiral",
        "tagline": "Tight defense",
        "waypoints": [
            (0,   180),
            (120, 180),
            (120, 460),
            (260, 460),
            (260, 260),
            (420, 260),
            (420, 420),
            (600, 420),
        ],
        "field": ((58, 72, 82), (70, 86, 98)),
        "grid": (139, 156, 166),
    },
    {
        "name": "Ember Valley",
        "tagline": "Short danger",
        "waypoints": [
            (0,   330),
            (180, 330),
            (180, 210),
            (360, 210),
            (360, 360),
            (500, 360),
            (500, 250),
            (600, 250),
        ],
        "field": ((94, 58, 38), (112, 70, 44)),
        "grid": (176, 122, 82),
    },
    {
        "name": "Frost Crossing",
        "tagline": "Wide zigzag",
        "waypoints": [
            (0,   470),
            (100, 470),
            (100, 150),
            (240, 150),
            (240, 390),
            (390, 390),
            (390, 190),
            (540, 190),
            (540, 330),
            (600, 330),
        ],
        "field": ((45, 80, 97), (53, 98, 118)),
        "grid": (125, 180, 196),
    },
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
        self.fullscreen = START_FULLSCREEN
        self.display = self._set_display_mode()
        self.screen = pygame.Surface((SCREEN_W, SCREEN_H)).convert()
        pygame.display.set_caption("Kingdom's Last Stand")
        pygame.key.start_text_input()
        self.clock = pygame.time.Clock()

        # Core game state
        self.gold       = 200
        self.castle_hp  = 100
        self.current_wave = 0
        self.towers   = []
        self.enemies  = []
        self.wave     = None
        self.state    = self.STATE_HOME
        self.paused = False
        self.player_name = ""
        self.selected_map_index = 0
        self.map_data = MAPS[self.selected_map_index]
        self.waypoints = self.map_data["waypoints"]

        # Systems
        self.stats_tracker = StatsTracker()
        self.ui_manager    = UIManager(self.screen)

        # Placement state
        self.selected_tower_type = None   # "archer" | "mage" | "cannon"
        self.sell_mode = False
        self.tower_map = {}               # (col, row) -> Tower instance
        self.path_tiles = self._compute_path_tiles()
        self._invalid_placement_flashes = []  # [{"col", "row", "timer"}]

        # Timing
        self.wave_start_time = 0.0

        # Projectiles in flight
        self.projectiles = []

        # Death particles
        self.particles = []

        # Floating damage numbers
        self.damage_numbers = []

        # Pre-generated next wave (so preview matches actual wave)
        self._queued_wave = None

        # UI elements owned by Game
        self.font = pygame.font.SysFont("georgia", 26, bold=True)
        self.font_small = pygame.font.SysFont("verdana", 16)
        self.start_wave_btn = pygame.Rect(
            GAME_W // 2 - 110, SCREEN_H - 70, 220, 44
        )
        self.home_name_input_rect = pygame.Rect(0, 0, 0, 0)
        self.home_name_input_active = True
        self.home_name_error_until = 0
        self.home_start_btn = pygame.Rect(0, 0, 0, 0)
        self.home_quit_btn = pygame.Rect(0, 0, 0, 0)
        self.home_map_buttons = []
        self.pause_btn     = pygame.Rect(GAME_W + 24, SCREEN_H - 162, PANEL_WIDTH - 48, 32)
        self.quit_game_btn = pygame.Rect(GAME_W + 24, SCREEN_H - 120, PANEL_WIDTH - 48, 32)
        self.static_battlefield = self._build_static_battlefield()
        self.home_backdrop = self._build_home_backdrop()

        # End-game screen buttons (set each frame when drawn)
        self.total_gold_earned = 0
        self.end_main_menu_btn = pygame.Rect(0, 0, 0, 0)
        self.end_quit_btn      = pygame.Rect(0, 0, 0, 0)

    def _set_display_mode(self):
        if self.fullscreen:
            try:
                return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            except pygame.error:
                self.fullscreen = False

        return pygame.display.set_mode((SCREEN_W, SCREEN_H))

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.display = self._set_display_mode()
        self.ui_manager.screen = self.screen

    def _display_to_game_pos(self, pos):
        target_rect = self._get_scaled_screen_rect()
        if target_rect.size == (SCREEN_W, SCREEN_H):
            return pos

        if not target_rect.collidepoint(pos):
            return (-1, -1)

        return (
            max(0, min(SCREEN_W - 1, int((pos[0] - target_rect.x) * SCREEN_W / target_rect.width))),
            max(0, min(SCREEN_H - 1, int((pos[1] - target_rect.y) * SCREEN_H / target_rect.height))),
        )

    def _get_mouse_pos(self):
        return self._display_to_game_pos(pygame.mouse.get_pos())

    def _get_scaled_screen_rect(self):
        display_w, display_h = self.display.get_size()
        scale = min(display_w / SCREEN_W, display_h / SCREEN_H)
        scaled_w = int(SCREEN_W * scale)
        scaled_h = int(SCREEN_H * scale)
        return pygame.Rect(
            (display_w - scaled_w) // 2,
            (display_h - scaled_h) // 2,
            scaled_w,
            scaled_h,
        )

    def _present_frame(self):
        target_rect = self._get_scaled_screen_rect()
        if target_rect.size == (SCREEN_W, SCREEN_H):
            self.display.blit(self.screen, (0, 0))
        else:
            self.display.fill((0, 0, 0))
            pygame.transform.scale(self.screen, target_rect.size, self.display.subsurface(target_rect))
        pygame.display.flip()

    # ------------------------------------------------------------------
    # Public state accessor
    # ------------------------------------------------------------------

    @property
    def game_state(self):
        if self.state == self.STATE_HOME:
            return "menu"
        if self.state in (self.STATE_PREP, self.STATE_WAVE):
            return "playing"
        if self.state == self.STATE_VICTORY:
            return "victory"
        return "game_over"

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
        events = pygame.event.get()
        has_text_input = any(event.type == pygame.TEXTINPUT for event in events)

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.TEXTINPUT:
                if self.state == self.STATE_HOME and self.home_name_input_active:
                    self._append_name_text(event.text)
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                    continue
                if self.state == self.STATE_HOME:
                    self._handle_home_keydown(event, allow_key_text=not has_text_input)
                    continue
                if event.key == pygame.K_ESCAPE:
                    self.selected_tower_type = None
                    self.sell_mode = False
                if event.key == pygame.K_f:
                    if self.state in (self.STATE_PREP, self.STATE_WAVE):
                        self.sell_mode = not self.sell_mode
                        if self.sell_mode:
                            self.selected_tower_type = None
                if event.key == pygame.K_p:
                    if self.state in (self.STATE_PREP, self.STATE_WAVE):
                        self._toggle_pause()
                if event.key == pygame.K_q:
                    if self.state in (self.STATE_GAME_OVER, self.STATE_VICTORY):
                        pygame.quit()
                        sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_click(self._display_to_game_pos(event.pos), event.button)

    def _handle_home_keydown(self, event, allow_key_text=False):
        if event.key == pygame.K_RETURN:
            self._try_start_campaign()
        elif event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
        elif event.key == pygame.K_BACKSPACE:
            self.player_name = self.player_name[:-1]
        elif event.key == pygame.K_TAB:
            self.home_name_input_active = not self.home_name_input_active
        elif allow_key_text and self.home_name_input_active and event.unicode and self._is_name_character(event.unicode):
            self._append_name_text(event.unicode)

    def _append_name_text(self, text):
        if not self._is_name_character(text):
            return
        available = 18 - len(self.player_name)
        if available > 0:
            self.player_name += text[:available]

    def _is_name_character(self, text):
        return all(
            char.isprintable() or unicodedata.category(char).startswith("M")
            for char in text
        )

    def _try_start_campaign(self):
        self.player_name = " ".join(self.player_name.strip().split())
        if self.player_name:
            self.state = self.STATE_PREP
            self.home_name_input_active = False
            self._queue_next_wave()
        else:
            self.home_name_input_active = True
            self.home_name_error_until = pygame.time.get_ticks() + 1400

    def _select_map(self, map_index):
        if map_index == self.selected_map_index:
            return

        self.selected_map_index = map_index
        self.map_data = MAPS[self.selected_map_index]
        self.waypoints = self.map_data["waypoints"]
        self.path_tiles = self._compute_path_tiles()
        self.static_battlefield = self._build_static_battlefield()

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
            if self.home_name_input_rect.collidepoint(pos):
                self.home_name_input_active = True
            elif self._handle_home_map_click(pos):
                self.home_name_input_active = False
            elif self.home_start_btn.collidepoint(pos):
                self._try_start_campaign()
            elif self.home_quit_btn.collidepoint(pos):
                pygame.quit()
                sys.exit()
            else:
                self.home_name_input_active = False
            return

        if self.state in (self.STATE_GAME_OVER, self.STATE_VICTORY):
            if self.end_main_menu_btn.collidepoint(pos):
                self._reset_for_main_menu()
            elif self.end_quit_btn.collidepoint(pos):
                pygame.quit()
                sys.exit()
            return

        # Sell mode: left-click on a tower in the map area sells it.
        # Clicks outside the map (sidebar, HUD) fall through to normal handlers.
        if self.sell_mode and self.state in (self.STATE_PREP, self.STATE_WAVE):
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
                return  # consumed: map area click (tower sold or empty tile)

        # Tower panel buttons
        tower_key = self.ui_manager.get_tower_clicked(pos)
        if tower_key:
            self.selected_tower_type = tower_key
            return

        if self.ui_manager.sell_btn.collidepoint(pos):
            if self.state in (self.STATE_PREP, self.STATE_WAVE):
                self.sell_mode = not self.sell_mode
                if self.sell_mode:
                    self.selected_tower_type = None
            return

        if self.quit_game_btn.collidepoint(pos):
            pygame.quit()
            sys.exit()

        if self.pause_btn.collidepoint(pos):
            self._toggle_pause()
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

    def _handle_home_map_click(self, pos):
        for map_index, rect in self.home_map_buttons:
            if rect.collidepoint(pos):
                self._select_map(map_index)
                return True
        return False

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.selected_tower_type = None
            self.sell_mode = False

    # ------------------------------------------------------------------
    # Tower placement
    # ------------------------------------------------------------------

    def _try_place_tower(self, pos):
        if not self.selected_tower_type:
            return

        col = pos[0] // TILE_SIZE
        row = (pos[1] - HUD_HEIGHT) // TILE_SIZE
        tile = (col, row)

        max_col = GAME_W // TILE_SIZE - 1
        max_row = (SCREEN_H - HUD_HEIGHT) // TILE_SIZE - 1
        if col < 0 or col > max_col or row < 0 or row > max_row:
            return

        if tile in self.path_tiles or tile in self.tower_map:
            self._flash_invalid(col, row)
            return

        cost = TOWER_COSTS[self.selected_tower_type]
        if self.gold < cost:
            self._flash_invalid(col, row)
            return

        px = col * TILE_SIZE + TILE_SIZE // 2
        py = row * TILE_SIZE + HUD_HEIGHT + TILE_SIZE // 2
        tower = TOWER_CLASSES[self.selected_tower_type]((px, py))

        self.towers.append(tower)
        self.tower_map[tile] = tower
        self.gold -= cost
        self.stats_tracker.record_gold_spent(cost)

    def _flash_invalid(self, col, row):
        for f in self._invalid_placement_flashes:
            if f["col"] == col and f["row"] == row:
                f["timer"] = 0.45
                return
        self._invalid_placement_flashes.append({"col": col, "row": row, "timer": 0.45})

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt):
        if self.state == self.STATE_HOME:
            return

        # Always tick flashes so they fade even in prep/paused state
        for f in self._invalid_placement_flashes:
            f["timer"] -= dt
        self._invalid_placement_flashes = [f for f in self._invalid_placement_flashes if f["timer"] > 0]

        if self.paused:
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

        # 3. Towers fire projectiles
        for tower in self.towers:
            proj = tower.attack(self.enemies, dt)
            if proj is not None:
                self.projectiles.append(proj)

        # 4. Update projectiles; track damage dealt this frame
        hp_snapshot = {id(e): e.hp for e in self.enemies}
        for proj in self.projectiles:
            proj.update(dt, self.enemies)
        self.projectiles = [p for p in self.projectiles if not p.done]

        total_dmg = 0
        for enemy in self.enemies:
            dmg = hp_snapshot.get(id(enemy), enemy.hp) - enemy.hp
            if dmg > 0:
                total_dmg += dmg
                self._spawn_damage_number(int(dmg), enemy.position)
        if total_dmg > 0:
            self.stats_tracker.record_damage(int(total_dmg))

        # Tick death particles
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 120 * dt  # gravity
            p["age"] += dt
        self.particles = [p for p in self.particles if p["age"] < p["max_age"]]

        # Tick floating damage numbers
        for dn in self.damage_numbers:
            dn["age"] += dt
            dn["y"] -= 38 * dt
        self.damage_numbers = [dn for dn in self.damage_numbers if dn["age"] < dn["max_age"]]

        # 4. Remove dead enemies and reward gold
        dead = [e for e in self.enemies if e.is_dead()]
        for enemy in dead:
            self.gold += enemy.reward_gold
            self.total_gold_earned += enemy.reward_gold
            self.stats_tracker.record_kill()
            self._spawn_death_particles(enemy.position)
            self.enemies.remove(enemy)
            if getattr(enemy, "splits_on_death", False):
                for offset in (-10, 10):
                    mini = MiniSlime(self.waypoints)
                    mini.position = pygame.Vector2(enemy.position.x + offset, enemy.position.y)
                    mini.path_index = enemy.path_index
                    self.enemies.append(mini)

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

    def _queue_next_wave(self):
        next_num = self.current_wave + 1
        if next_num <= MAX_WAVES:
            self._queued_wave = Wave(next_num, self.waypoints)

    def next_wave(self):
        """Advance to the next wave (called by Start Wave button or externally)."""
        self.paused = False
        self.sell_mode = False
        self.current_wave += 1
        self.wave = self._queued_wave or Wave(self.current_wave, self.waypoints)
        self._queued_wave = None
        self.projectiles = []
        self.state = self.STATE_WAVE
        self.wave_start_time = pygame.time.get_ticks() / 1000.0

    def _end_wave(self):
        self.paused = False
        self.damage_numbers.clear()
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
            self._queue_next_wave()

    def check_game_over(self):
        return self.castle_hp <= 0

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self):
        if self.state == self.STATE_HOME:
            self._draw_home_screen()
            self._present_frame()
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

        for proj in self.projectiles:
            proj.draw(self.screen)

        self._draw_castle_hp_bar()

        self.ui_manager.draw_hud(self.gold, self.castle_hp, self.current_wave, self.player_name)
        mouse_pos = self._get_mouse_pos()
        self.ui_manager.draw_tower_panel(self.gold, self.selected_tower_type, self.sell_mode, mouse_pos)
        self._draw_pause_button(mouse_pos)
        self._draw_quit_game_button(mouse_pos)
        self._draw_placement_preview()

        if self.state == self.STATE_PREP:
            self._draw_start_wave_button()
            self._draw_wave_preview()

        self._draw_particles()
        self._draw_damage_numbers()

        if self.state == self.STATE_VICTORY:
            self._draw_victory_screen()
        elif self.state == self.STATE_GAME_OVER:
            self._draw_game_over_screen()
        elif self.paused:
            self._draw_pause_overlay()

        self._present_frame()

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

        # Static background stars
        import random as _rng
        rng = _rng.Random(42)
        for _ in range(60):
            sx = rng.randint(380, 790)
            sy = rng.randint(10, 590)
            sr = rng.choice([1, 1, 1, 2])
            sa = rng.randint(40, 130)
            sc = rng.choice([(229,183,57),(160,200,255),(255,255,255)])
            gs = pygame.Surface((sr*2+2, sr*2+2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*sc, sa), (sr+1, sr+1), sr)
            surface.blit(gs, (sx-sr, sy-sr))

        return surface

    def _draw_home_sparkles(self):
        """Animated twinkling stars drifting slowly upward."""
        now = pygame.time.get_ticks()
        for i in range(28):
            seed   = i * 6271
            x      = (seed * 137 % 400) + 382
            period = 4500 + (seed % 2500)
            phase  = (now + seed * 53) % period
            t      = phase / period
            y      = ((seed * 251 % 480) + 50 - int(t * 90)) % 540 + 20
            fade   = 4.0 * t * (1.0 - t)
            a      = int(220 * fade)
            r      = 1 + (seed % 2)
            colors = [(229,183,57),(160,200,255),(255,255,255),(200,160,255)]
            c      = colors[seed % 4]
            s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*c, a), (r+1, r+1), r)
            self.screen.blit(s, (x-r, y-r))

    def _draw_home_screen(self):
        self.screen.blit(self.home_backdrop, (0, 0))
        self._draw_home_sparkles()

        pulse   = (pygame.time.get_ticks() % 2000) / 2000.0
        shimmer = 0.5 + 0.5 * abs(1 - pulse * 2)

        panel = pygame.Rect(42, 24, 320, 552)
        panel_shadow = panel.move(10, 14)
        pygame.draw.rect(self.screen, (4, 7, 14), panel_shadow, border_radius=32)
        pygame.draw.rect(self.screen, (15, 21, 36), panel, border_radius=32)
        # Animated border that pulses gold ↔ blue
        border_r = int(63  + 30 * shimmer)
        border_g = int(78  + 20 * shimmer)
        border_b = int(112 + 40 * shimmer)
        pygame.draw.rect(self.screen, (border_r, border_g, border_b), panel, 2, border_radius=32)
        # Inner highlight line
        pygame.draw.rect(self.screen, (40, 50, 75), panel.inflate(-8, -8), 1, border_radius=28)

        # ── Crest ────────────────────────────────────────────────────
        crest_outer = pygame.Rect(panel.x + 24, panel.y + 24, 78, 78)
        crest_inner = crest_outer.inflate(-10, -10)

        # Pulsing outer glow
        glow_r = int(52 + 10 * shimmer)
        glow_surf = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
        glow_a = int(80 * shimmer)
        pygame.draw.circle(glow_surf, (214, 160, 57, glow_a), (glow_r, glow_r), glow_r)
        self.screen.blit(glow_surf, (crest_outer.centerx - glow_r, crest_outer.centery - glow_r))

        pygame.draw.ellipse(self.screen, (181, 134, 57), crest_outer)
        pygame.draw.ellipse(self.screen, (247, 213, 126), crest_inner)
        pygame.draw.circle(self.screen, (52, 38, 17), crest_inner.center, 18)
        pygame.draw.polygon(self.screen, (88, 63, 25), [
            (crest_inner.centerx,      crest_inner.centery - 26),
            (crest_inner.centerx + 24, crest_inner.centery + 8),
            (crest_inner.centerx,      crest_inner.centery + 26),
            (crest_inner.centerx - 24, crest_inner.centery + 8),
        ])
        # Crest shine dot
        pygame.draw.circle(self.screen, (255, 240, 180), (crest_inner.centerx + 6, crest_inner.centery - 10), 3)

        # ── Eyebrow tag ───────────────────────────────────────────────
        eyebrow = pygame.Rect(panel.x + 24, panel.y + 120, 252, 30)
        pygame.draw.rect(self.screen, (28, 36, 58), eyebrow, border_radius=13)
        pygame.draw.rect(self.screen, (95, 111, 148), eyebrow, 1, border_radius=13)
        # Small diamond accents on sides
        for ex in (eyebrow.x + 10, eyebrow.right - 10):
            pygame.draw.polygon(self.screen, (180, 148, 70), [
                (ex, eyebrow.centery - 5), (ex+4, eyebrow.centery),
                (ex, eyebrow.centery + 5), (ex-4, eyebrow.centery),
            ])
        eyebrow_text = pygame.font.SysFont("georgia", 13, bold=True).render(
            "TACTICAL DEFENSE CAMPAIGN", True, (212, 196, 150))
        self.screen.blit(eyebrow_text,
            (eyebrow.centerx - eyebrow_text.get_width() // 2, eyebrow.y + 7))

        # ── Title (gold, multi-layer shadow) ──────────────────────────
        title_font = pygame.font.SysFont("georgia", 34, bold=True)
        title_color = (248, 228, 160)   # warm gold-white
        for line, y_off in (("Kingdom's", 160), ("Last Stand", 202)):
            # Deep shadow
            for dx, dy, a in ((3, 4, 160), (2, 3, 100), (1, 1, 60)):
                sh = title_font.render(line, True, (6, 9, 18))
                sh.set_alpha(a)
                self.screen.blit(sh, (panel.x + 24 + dx, panel.y + y_off + dy))
            surf = title_font.render(line, True, title_color)
            self.screen.blit(surf, (panel.x + 24, panel.y + y_off))

        # ── Decorative diamond separator ──────────────────────────────
        sep_y  = panel.y + 254
        sep_lx = panel.x + 26
        sep_rx = panel.x + 300
        sep_cx = (sep_lx + sep_rx) // 2
        line_clr = (160, 124, 52)
        pygame.draw.line(self.screen, line_clr, (sep_lx, sep_y), (sep_cx - 14, sep_y), 1)
        pygame.draw.line(self.screen, line_clr, (sep_cx + 14, sep_y), (sep_rx, sep_y), 1)
        # Center diamond
        pygame.draw.polygon(self.screen, (229, 183, 57), [
            (sep_cx,      sep_y - 6),
            (sep_cx + 6,  sep_y),
            (sep_cx,      sep_y + 6),
            (sep_cx - 6,  sep_y),
        ])
        # Side small diamonds
        for ox in (-22, 22):
            pygame.draw.polygon(self.screen, (180, 138, 58), [
                (sep_cx + ox,     sep_y - 4),
                (sep_cx + ox + 4, sep_y),
                (sep_cx + ox,     sep_y + 4),
                (sep_cx + ox - 4, sep_y),
            ])

        body_font = pygame.font.SysFont("georgia", 16, bold=False)
        body_lines = [
            "Marshal archers, mages, and cannons",
            "across a royal field. Hold the road.",
            "Protect the castle.",
        ]
        for index, line in enumerate(body_lines):
            surf = body_font.render(line, True, (160, 172, 196))
            self.screen.blit(surf, (panel.x + 24, panel.y + 268 + index * 22))

        self.home_name_input_rect = pygame.Rect(panel.x + 24, panel.y + 340, 270, 44)
        self._draw_name_input(self.home_name_input_rect)

        feature_specs = [
            ((panel.x + 24, panel.y + 396, 88, 50), (65, 173, 89),  "ARCHER", "Rapid shots"),
            ((panel.x + 116, panel.y + 396, 88, 50), (147, 93, 232), "MAGE",   "Slow control"),
            ((panel.x + 208, panel.y + 396, 88, 50), (218, 109, 32), "CANNON", "Splash burst"),
        ]
        feat_title_font = pygame.font.SysFont("georgia", 13, bold=True)
        feat_desc_font  = pygame.font.SysFont("georgia", 10, bold=False)
        for rect_args, color, title, desc in feature_specs:
            rect = pygame.Rect(*rect_args)
            pygame.draw.rect(self.screen, (22, 30, 49), rect, border_radius=18)
            pygame.draw.rect(self.screen, (68, 82, 112), rect, 1, border_radius=18)
            # Narrower gem (6px) leaves 66px of text space to the right
            gem_rect = pygame.Rect(rect.x + 8, rect.y + 7, 6, 36)
            pygame.draw.rect(self.screen, color, gem_rect, border_radius=4)
            title_surf = feat_title_font.render(title, True, (240, 233, 220))
            desc_surf  = feat_desc_font.render(desc,  True, (145, 157, 184))
            self.screen.blit(title_surf, (rect.x + 18, rect.y + 8))
            self.screen.blit(desc_surf,  (rect.x + 18, rect.y + 28))

        self.home_start_btn = pygame.Rect(panel.x + 24, panel.y + 458, 270, 46)
        self.home_quit_btn  = pygame.Rect(panel.x + 82, panel.y + 510, 128, 24)

        self._draw_home_button(
            self.home_start_btn,
            "Start Campaign",
            "Begin your first defense",
            (241, 188, 53),
            (184, 117, 19),
            hover=self.home_start_btn.collidepoint(self._get_mouse_pos()),
            glow_strength=shimmer,
        )
        self._draw_home_button(
            self.home_quit_btn,
            "Quit",
            "Exit the game",
            (54, 65, 94),
            (27, 34, 52),
            hover=self.home_quit_btn.collidepoint(self._get_mouse_pos()),
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
        ribbon_text = pygame.font.SysFont("georgia", 14, bold=True).render("ROYAL DEFENSE", True, (218, 201, 154))
        self.screen.blit(ribbon_text, (ribbon.centerx - ribbon_text.get_width() // 2, ribbon.y + 7))

        mini_field = pygame.Rect(preview_rect.x + 24, preview_rect.y + 70, preview_rect.width - 48, 274)
        self._draw_home_preview_field(mini_field)

        selector_title = pygame.font.SysFont("georgia", 14, bold=True).render("SELECT MAP", True, (218, 201, 154))
        self.screen.blit(selector_title, (preview_rect.x + 24, preview_rect.bottom - 168))

        self.home_map_buttons = []
        for map_index, map_data in enumerate(MAPS):
            col = map_index % 3
            row = map_index // 3
            rect = pygame.Rect(
                preview_rect.x + 24 + col * 108,
                preview_rect.bottom - 150 + row * 74,
                100,
                66,
            )
            self.home_map_buttons.append((map_index, rect))
            self._draw_home_map_card(rect, map_index, map_data)

    def _draw_home_map_card(self, rect, map_index, map_data):
        selected = map_index == self.selected_map_index
        hover = rect.collidepoint(self._get_mouse_pos())
        fill = (35, 43, 65) if selected else (22, 29, 47)
        border = (247, 222, 118) if selected else ((112, 128, 158) if hover else (71, 85, 116))

        pygame.draw.rect(self.screen, (7, 10, 18), rect.move(0, 5), border_radius=18)
        pygame.draw.rect(self.screen, fill, rect, border_radius=18)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=18)

        dark, light = map_data["field"]
        swatch = pygame.Rect(rect.x + 10, rect.y + 10, 18, 18)
        pygame.draw.rect(self.screen, dark, swatch, border_radius=6)
        pygame.draw.rect(self.screen, light, swatch.inflate(-6, -6), border_radius=4)

        index_surf = pygame.font.SysFont("georgia", 14, bold=True).render(str(map_index + 1), True, (244, 238, 228))
        self.screen.blit(index_surf, (swatch.centerx - index_surf.get_width() // 2, swatch.centery - index_surf.get_height() // 2 - 1))

        title_font = pygame.font.SysFont("georgia", 12, bold=True)
        tag_font   = pygame.font.SysFont("georgia", 11, bold=False)
        # Title-case avoids uppercase pixel-width blowup; all names fit at 12px
        name_surf = title_font.render(map_data["name"], True, (242, 236, 224))
        tag_surf  = tag_font.render(map_data["tagline"], True, (146, 158, 184))
        self.screen.blit(name_surf, (rect.x + 8, rect.y + 32))
        self.screen.blit(tag_surf,  (rect.x + 8, rect.y + 50))

    def _draw_name_input(self, rect):
        now = pygame.time.get_ticks()
        has_error = now < self.home_name_error_until and not self.player_name.strip()
        border = (235, 116, 120) if has_error else (
            (247, 222, 118) if self.home_name_input_active else (68, 82, 112)
        )

        pygame.draw.rect(self.screen, (9, 13, 23), rect.move(0, 5), border_radius=14)
        pygame.draw.rect(self.screen, (18, 25, 42), rect, border_radius=14)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=14)

        label_font = pygame.font.SysFont("georgia", 13, bold=True)
        input_font = pygame.font.SysFont(["thonburi", "arial", "georgia"], 18, bold=True)
        label_text = "COMMANDER NAME"
        if has_error:
            label_text = "ENTER A NAME FIRST"
        label = label_font.render(label_text, True, border)
        self.screen.blit(label, (rect.x + 14, rect.y + 6))

        text = self.player_name if self.player_name else "Type your name"
        text_color = (244, 238, 228) if self.player_name else (91, 103, 130)
        visible_text = text
        max_width = rect.width - 30
        while input_font.size(visible_text)[0] > max_width and len(visible_text) > 1:
            visible_text = visible_text[1:]
        value = input_font.render(visible_text, True, text_color)
        text_y = rect.y + 16
        self.screen.blit(value, (rect.x + 14, text_y))

        if self.home_name_input_active and (now // 420) % 2 == 0:
            cursor_x = rect.x + 14 + value.get_width() + 3
            pygame.draw.line(self.screen, (244, 238, 228), (cursor_x, text_y + 1), (cursor_x, text_y + 16), 2)

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
            title_surf = pygame.font.SysFont("georgia", 16, bold=True).render(title, True, title_color)
            self.screen.blit(title_surf, (rect.centerx - title_surf.get_width() // 2, rect.centery - title_surf.get_height() // 2 - 1))

    def _draw_home_preview_field(self, rect):
        dark, light = self.map_data["field"]
        grid_color = self.map_data["grid"]
        pygame.draw.rect(self.screen, dark, rect, border_radius=28)
        inset = rect.inflate(-12, -12)
        pygame.draw.rect(self.screen, light, inset, border_radius=24)

        cell = 28
        for row in range((inset.height // cell) + 1):
            for col in range((inset.width // cell) + 1):
                tile = pygame.Rect(inset.x + col * cell, inset.y + row * cell, cell, cell)
                pygame.draw.rect(self.screen, light if (row + col) % 2 == 0 else dark, tile)

        for x in range(inset.x, inset.right + 1, cell):
            pygame.draw.line(self.screen, grid_color, (x, inset.y), (x, inset.bottom), 1)
        for y in range(inset.y, inset.bottom + 1, cell):
            pygame.draw.line(self.screen, grid_color, (inset.x, y), (inset.right, y), 1)

        path_points = self._scale_waypoints_to_rect(self.waypoints, inset)
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

    def _scale_waypoints_to_rect(self, waypoints, rect):
        scaled = []
        for x, y in waypoints:
            scaled_x = rect.x + int((x / GAME_W) * rect.width)
            scaled_y = rect.y + int(((y - HUD_HEIGHT) / max(GAME_H, 1)) * rect.height)
            scaled.append((scaled_x, scaled_y))
        return scaled

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
        dark_tile, light_tile = self.map_data["field"]
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
        for i in range(len(self.waypoints) - 1):
            pygame.draw.line(
                target, (152, 102, 38),
                self.waypoints[i], self.waypoints[i + 1], TILE_SIZE + 8
            )
            pygame.draw.line(
                target, (231, 197, 120),
                self.waypoints[i], self.waypoints[i + 1], TILE_SIZE
            )
            pygame.draw.line(
                target, (240, 214, 150),
                self.waypoints[i], self.waypoints[i + 1], TILE_SIZE - 16
            )

        for i in range(len(self.waypoints) - 1):
            x1, y1 = self.waypoints[i]
            x2, y2 = self.waypoints[i + 1]
            steps = max(abs(x2 - x1), abs(y2 - y1)) // 34 + 1
            for step in range(steps):
                t = step / max(steps - 1, 1)
                x = int(x1 + (x2 - x1) * t)
                y = int(y1 + (y2 - y1) * t)
                pygame.draw.circle(target, (139, 92, 35), (x, y), 4)

    def _draw_grid(self, surface=None):
        target = surface or self.screen
        color = self.map_data["grid"]
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
        cx, cy = self.waypoints[-1]

        # Stone colors
        STONE      = (148, 152, 168)
        STONE_LT   = (188, 192, 205)
        STONE_DK   = (108, 112, 128)
        SHADOW_CLR = (28,  38,  28)
        WOOD       = (90,  64,  38)
        WOOD_DK    = (62,  42,  22)
        FLAG_RED   = (196, 52,  60)

        # Anchor: path endpoint is the gate mouth
        gx, gy = cx, cy

        # Ground shadow
        pygame.draw.ellipse(target, SHADOW_CLR, (gx - 42, gy + 8, 88, 16))

        # ── Wall / base ───────────────────────────────────────────────
        wall = pygame.Rect(gx - 36, gy - 28, 80, 42)
        pygame.draw.rect(target, STONE_DK, wall)
        pygame.draw.rect(target, STONE,    wall.inflate(-4, -4))
        pygame.draw.rect(target, STONE_LT, wall, 2)

        # Stone lines on wall
        for row_offset in (8, 18):
            pygame.draw.line(target, STONE_DK,
                             (wall.left + 4,  wall.top + row_offset),
                             (wall.right - 4, wall.top + row_offset), 1)
        for bx in range(wall.left + 10, wall.right - 4, 14):
            pygame.draw.line(target, STONE_DK,
                             (bx, wall.top + 4), (bx, wall.top + 8), 1)
            pygame.draw.line(target, STONE_DK,
                             (bx + 7, wall.top + 12), (bx + 7, wall.top + 16), 1)

        # Wall crenels
        for i in range(5):
            crenel = pygame.Rect(wall.left + 2 + i * 15, wall.top - 7, 9, 8)
            pygame.draw.rect(target, STONE_DK, crenel)
            pygame.draw.rect(target, STONE,    crenel.inflate(-2, -2))

        # ── Gate ──────────────────────────────────────────────────────
        gate = pygame.Rect(gx - 8, gy - 18, 18, 22)
        pygame.draw.rect(target, WOOD_DK, gate, border_radius=3)
        pygame.draw.rect(target, WOOD,    gate.inflate(-2, -2), border_radius=2)
        # portcullis bars
        for bar_x in range(gate.left + 2, gate.right - 1, 5):
            pygame.draw.line(target, WOOD_DK,
                             (bar_x, gate.top + 2), (bar_x, gate.bottom - 2), 1)
        pygame.draw.line(target, WOOD_DK,
                         (gate.left + 2, gate.top + 8), (gate.right - 2, gate.top + 8), 1)

        # ── Left tower ────────────────────────────────────────────────
        lt = pygame.Rect(gx - 50, gy - 44, 22, 52)
        pygame.draw.rect(target, STONE_DK, lt)
        pygame.draw.rect(target, STONE,    lt.inflate(-4, -4))
        pygame.draw.rect(target, STONE_LT, lt, 2)
        for i in range(3):
            c = pygame.Rect(lt.left + 2 + i * 7, lt.top - 6, 5, 7)
            pygame.draw.rect(target, STONE_DK, c)
            pygame.draw.rect(target, STONE,    c.inflate(-2, -2))
        # window
        pygame.draw.rect(target, (42, 52, 80),
                         (lt.centerx - 3, lt.top + 10, 6, 8), border_radius=2)

        # ── Right (main) tower — taller ───────────────────────────────
        rt = pygame.Rect(gx + 22, gy - 56, 26, 64)
        pygame.draw.rect(target, STONE_DK, rt)
        pygame.draw.rect(target, STONE,    rt.inflate(-4, -4))
        pygame.draw.rect(target, STONE_LT, rt, 2)
        for i in range(3):
            c = pygame.Rect(rt.left + 2 + i * 8, rt.top - 7, 6, 8)
            pygame.draw.rect(target, STONE_DK, c)
            pygame.draw.rect(target, STONE,    c.inflate(-2, -2))
        # windows
        pygame.draw.rect(target, (42, 52, 80),
                         (rt.centerx - 3, rt.top + 10, 6, 9), border_radius=2)
        pygame.draw.rect(target, (42, 52, 80),
                         (rt.centerx - 3, rt.top + 26, 6, 9), border_radius=2)

        # ── Flag on main tower ────────────────────────────────────────
        pole_x = rt.right - 3
        pole_top = rt.top - 18
        pygame.draw.line(target, WOOD, (pole_x, pole_top), (pole_x, rt.top), 2)
        pygame.draw.polygon(target, FLAG_RED, [
            (pole_x,      pole_top),
            (pole_x + 14, pole_top + 5),
            (pole_x,      pole_top + 10),
        ])
        pygame.draw.polygon(target, (220, 80, 90), [
            (pole_x + 2,  pole_top + 2),
            (pole_x + 11, pole_top + 5),
            (pole_x + 2,  pole_top + 8),
        ])

    def _draw_castle_hp_bar(self):
        cx, cy = self.waypoints[-1]
        ratio  = max(0.0, self.castle_hp / 100)

        bar_w = 64
        bar_h = 7
        bx    = cx - 32
        by    = cy + 26

        # background
        pygame.draw.rect(self.screen, (50, 20, 20),  (bx - 1, by - 1, bar_w + 2, bar_h + 2), border_radius=4)
        pygame.draw.rect(self.screen, (100, 30, 30), (bx, by, bar_w, bar_h), border_radius=3)

        # fill — green → yellow → red
        if ratio > 0.5:
            t   = (ratio - 0.5) * 2
            clr = (int(255 * (1 - t)), 210, 40)
        else:
            t   = ratio * 2
            clr = (220, int(180 * t), 20)

        fill_w = max(2, int(bar_w * ratio))
        pygame.draw.rect(self.screen, clr, (bx, by, fill_w, bar_h), border_radius=3)

        font  = pygame.font.SysFont("verdana", 10, bold=True)
        label = font.render(f"HP {self.castle_hp}", True, (240, 230, 200))
        self.screen.blit(label, (cx - label.get_width() // 2, by + bar_h + 3))

    def _draw_start_wave_button(self):
        label_text = f"Start Wave {self.current_wave + 1}"
        self.start_wave_btn = pygame.Rect(GAME_W // 2 - 128, SCREEN_H - 84, 256, 50)
        hover = self.start_wave_btn.collidepoint(self._get_mouse_pos())
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

        # Pulsing corner diamond accents
        import math as _m
        now = pygame.time.get_ticks()
        pulse = 0.55 + 0.45 * abs(_m.sin(now / 420.0))
        dia_a = int(200 * pulse)
        dia_surf = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.polygon(dia_surf, (255, 222, 80, dia_a), [(7, 0), (14, 7), (7, 14), (0, 7)])
        btn = self.start_wave_btn
        for dx, dy in ((-20, 0), (btn.width + 6, 0)):
            self.screen.blit(dia_surf, (btn.x + dx, btn.centery - 7))

        text = self.font.render(label_text, True, (38, 28, 10))
        sub = self.font_small.render("Release the next enemy march", True, (101, 69, 19))
        self.screen.blit(
            text,
            (self.start_wave_btn.centerx - text.get_width() // 2,
             self.start_wave_btn.y + 7)
        )
        self.screen.blit(sub, (self.start_wave_btn.centerx - sub.get_width() // 2, self.start_wave_btn.y + 31))

    # Enemy display config for wave preview
    _ENEMY_PREVIEW = {
        "Slime":       ("Slime",   (100, 220, 100)),
        "Goblin":      ("Goblin",  (80,  210,  80)),
        "SwordShield": ("Shield",  (90,  150, 230)),
        "Bat":         ("Bat",     (180, 140, 230)),
        "Orc":         ("Orc",     (210, 130,  60)),
        "Spider":      ("Spider",  (200,  80,  80)),
        "DarkKnight":  ("Knight",  (220,  70,  70)),
        "BossEnemy":   ("BOSS",    (255, 210,   0)),
    }

    def _draw_wave_preview(self):
        if not self._queued_wave:
            return

        counts = Counter(type(e).__name__ for e in self._queued_wave.enemy_queue)
        if not counts:
            return

        font = pygame.font.SysFont("verdana", 11, bold=True)
        btn = self.start_wave_btn
        total_w = self._preview_total_width(counts, font)
        pill_w = total_w + 32
        pill_h = 22
        pill_x = btn.centerx - pill_w // 2
        pill_y = btn.y - 32

        # Dark pill background
        pygame.draw.rect(self.screen, (6, 9, 18), (pill_x + 2, pill_y + 3, pill_w, pill_h), border_radius=11)
        pygame.draw.rect(self.screen, (20, 28, 48), (pill_x, pill_y, pill_w, pill_h), border_radius=11)
        pygame.draw.rect(self.screen, (78, 93, 128), (pill_x, pill_y, pill_w, pill_h), 1, border_radius=11)

        x = pill_x + 14
        label = font.render("NEXT:", True, (188, 176, 132))
        self.screen.blit(label, (x, pill_y + 5))
        x += label.get_width() + 8

        for enemy_name, count in counts.items():
            short, color = self._ENEMY_PREVIEW.get(enemy_name, (enemy_name[:3], (200, 200, 200)))
            surf   = font.render(f"{short}\u00d7{count}", True, color)
            shadow = font.render(f"{short}\u00d7{count}", True, (0, 0, 0))
            self.screen.blit(shadow, (x + 1, pill_y + 6))
            self.screen.blit(surf,   (x,     pill_y + 5))
            x += surf.get_width() + 10

    def _preview_total_width(self, counts, font):
        label_w = font.size("NEXT:")[0] + 8
        items_w = sum(
            font.size(f"{self._ENEMY_PREVIEW.get(n, (n[:3], None))[0]}\u00d7{c}")[0] + 10
            for n, c in counts.items()
        )
        return label_w + items_w

    def _spawn_damage_number(self, amount, position):
        self.damage_numbers.append({
            "text":    str(amount),
            "x":       float(position.x) + random.randint(-10, 10),
            "y":       float(position.y) - 18,
            "age":     0.0,
            "max_age": 0.85,
        })

    def _draw_damage_numbers(self):
        font = pygame.font.SysFont("verdana", 13, bold=True)
        for dn in self.damage_numbers:
            alpha = max(0.0, 1.0 - dn["age"] / dn["max_age"])
            a = int(255 * alpha)
            shadow = font.render(dn["text"], True, (0, 0, 0))
            surf   = font.render(dn["text"], True, (255, 230, 70))
            shadow.set_alpha(a)
            surf.set_alpha(a)
            bx = int(dn["x"]) - surf.get_width() // 2
            by = int(dn["y"])
            self.screen.blit(shadow, (bx + 1, by + 1))
            self.screen.blit(surf,   (bx,     by))

    # Death particle colors by enemy type (fallback = red/orange)
    _PARTICLE_COLORS = [
        (255, 80,  40),
        (255, 160,  30),
        (255, 220,  60),
        (200,  60,  20),
    ]

    def _spawn_death_particles(self, position):
        import math
        count = 10
        for i in range(count):
            angle  = (i / count) * math.tau + random.uniform(-0.3, 0.3)
            speed  = random.uniform(40, 110)
            color  = random.choice(self._PARTICLE_COLORS)
            self.particles.append({
                "x":       float(position.x),
                "y":       float(position.y),
                "vx":      math.cos(angle) * speed,
                "vy":      math.sin(angle) * speed - 30,
                "age":     0.0,
                "max_age": random.uniform(0.25, 0.45),
                "radius":  random.randint(2, 4),
                "color":   color,
            })

    def _draw_particles(self):
        for p in self.particles:
            alpha = max(0.0, 1.0 - p["age"] / p["max_age"])
            r = max(1, int(p["radius"] * alpha))
            a = int(255 * alpha)
            surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p["color"], a), (r + 1, r + 1), r)
            self.screen.blit(surf, (int(p["x"]) - r - 1, int(p["y"]) - r - 1))

    def _draw_pause_button(self, mouse_pos):
        self.pause_btn = pygame.Rect(GAME_W + 24, SCREEN_H - 162, PANEL_WIDTH - 48, 32)
        hover = self.pause_btn.collidepoint(mouse_pos)
        label_text = "Resume" if self.paused else "Pause"
        top = (64, 101, 128) if hover else (42, 58, 82)
        bottom = (24, 33, 52)

        pygame.draw.rect(self.screen, (6, 9, 16), self.pause_btn.move(0, 5), border_radius=12)
        for offset in range(self.pause_btn.height):
            t = offset / max(self.pause_btn.height, 1)
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(
                self.screen,
                color,
                (self.pause_btn.left, self.pause_btn.top + offset),
                (self.pause_btn.right, self.pause_btn.top + offset),
            )

        pygame.draw.rect(self.screen, (118, 190, 245) if hover else (76, 92, 122), self.pause_btn, 2, border_radius=12)
        label = pygame.font.SysFont("georgia", 14, bold=True).render(label_text, True, (246, 236, 225))
        self.screen.blit(
            label,
            (
                self.pause_btn.centerx - label.get_width() // 2,
                self.pause_btn.centery - label.get_height() // 2 - 1,
            ),
        )

    def _draw_quit_game_button(self, mouse_pos):
        self.quit_game_btn = pygame.Rect(GAME_W + 24, SCREEN_H - 120, PANEL_WIDTH - 48, 32)
        hover = self.quit_game_btn.collidepoint(mouse_pos)
        top = (119, 45, 48) if hover else (82, 32, 40)
        bottom = (54, 22, 31)

        pygame.draw.rect(self.screen, (6, 9, 16), self.quit_game_btn.move(0, 5), border_radius=12)
        for offset in range(self.quit_game_btn.height):
            t = offset / max(self.quit_game_btn.height, 1)
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(
                self.screen,
                color,
                (self.quit_game_btn.left, self.quit_game_btn.top + offset),
                (self.quit_game_btn.right, self.quit_game_btn.top + offset),
            )

        border = (232, 112, 104) if hover else (135, 72, 80)
        pygame.draw.rect(self.screen, border, self.quit_game_btn, 2, border_radius=12)

        label = pygame.font.SysFont("georgia", 14, bold=True).render("Quit Game", True, (246, 236, 225))
        self.screen.blit(
            label,
            (
                self.quit_game_btn.centerx - label.get_width() // 2,
                self.quit_game_btn.centery - label.get_height() // 2 - 1,
            ),
        )

    def _reset_for_main_menu(self):
        self.gold            = 200
        self.castle_hp       = 100
        self.current_wave    = 0
        self.towers          = []
        self.enemies         = []
        self.wave            = None
        self.tower_map       = {}
        self.damage_numbers.clear()
        self._invalid_placement_flashes.clear()
        self._queued_wave       = None
        self.selected_tower_type = None
        self.sell_mode          = False
        self.total_gold_earned  = 0
        self.paused             = False
        self.stats_tracker      = StatsTracker()
        self.ui_manager.stats_screen = None
        self.path_tiles         = self._compute_path_tiles()
        self.static_battlefield = self._build_static_battlefield()
        self.state              = self.STATE_HOME
        self.home_name_input_active = True
        self.player_name        = ""

    def _draw_end_button(self, rect, text, top_color, bottom_color, mouse_pos):
        if rect.collidepoint(mouse_pos):
            top_color = tuple(min(255, c + 22) for c in top_color)
        pygame.draw.rect(self.screen, (6, 9, 16), rect.move(0, 5), border_radius=14)
        for offset in range(rect.height):
            t = offset / max(rect.height, 1)
            color = tuple(int(top_color[i] + (bottom_color[i] - top_color[i]) * t) for i in range(3))
            pygame.draw.line(self.screen, color,
                             (rect.left, rect.top + offset), (rect.right, rect.top + offset))
        border = tuple(min(255, c + 60) for c in top_color)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=14)
        lbl = pygame.font.SysFont("georgia", 18, bold=True).render(text, True, (245, 240, 230))
        self.screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                               rect.centery - lbl.get_height() // 2))

    def _draw_victory_screen(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 500, 350
        panel = pygame.Rect((SCREEN_W - panel_w) // 2, (SCREEN_H - panel_h) // 2, panel_w, panel_h)
        pygame.draw.rect(self.screen, (14, 20, 36), panel.move(0, 8), border_radius=24)
        pygame.draw.rect(self.screen, (14, 20, 36), panel, border_radius=24)
        pygame.draw.rect(self.screen, (212, 175, 55), panel, 3, border_radius=24)

        title_font = pygame.font.SysFont("georgia", 60, bold=True)
        title = title_font.render("VICTORY!", True, (255, 215, 0))
        tx = panel.centerx - title.get_width() // 2
        for dx, dy, a in ((4, 5, 150), (2, 3, 80)):
            sh = title_font.render("VICTORY!", True, (90, 65, 0))
            sh.set_alpha(a)
            self.screen.blit(sh, (tx + dx, panel.y + 16 + dy))
        self.screen.blit(title, (tx, panel.y + 16))

        sub_font = pygame.font.SysFont("georgia", 16)
        subtitle = sub_font.render("You defended the kingdom!", True, (200, 190, 160))
        self.screen.blit(subtitle, (panel.centerx - subtitle.get_width() // 2, panel.y + 88))

        # Diamond separator
        sep_y  = panel.y + 116
        sep_lx = panel.x + 30
        sep_rx = panel.right - 30
        sep_cx = panel.centerx
        pygame.draw.line(self.screen, (160, 130, 40), (sep_lx, sep_y), (sep_cx - 14, sep_y), 1)
        pygame.draw.line(self.screen, (160, 130, 40), (sep_cx + 14, sep_y), (sep_rx, sep_y), 1)
        pygame.draw.polygon(self.screen, (212, 175, 55), [
            (sep_cx, sep_y - 6), (sep_cx + 6, sep_y), (sep_cx, sep_y + 6), (sep_cx - 6, sep_y)])
        for ox in (-22, 22):
            pygame.draw.polygon(self.screen, (160, 130, 45), [
                (sep_cx + ox, sep_y - 4), (sep_cx + ox + 4, sep_y),
                (sep_cx + ox, sep_y + 4), (sep_cx + ox - 4, sep_y)])

        total_kills = sum(d["enemies_defeated"] for d in self.stats_tracker.history)
        stat_font = pygame.font.SysFont("georgia", 18, bold=True)
        stats_rows = [
            ("Waves Survived",    str(self.current_wave)),
            ("Enemies Defeated",  str(total_kills)),
            ("Gold Earned",       str(self.total_gold_earned)),
        ]
        for i, (label, value) in enumerate(stats_rows):
            y = panel.y + 130 + i * 40
            row_bg = pygame.Rect(panel.x + 24, y - 3, panel_w - 48, 30)
            bg_color = (24, 32, 52) if i % 2 == 0 else (18, 24, 40)
            pygame.draw.rect(self.screen, bg_color, row_bg, border_radius=8)
            pygame.draw.rect(self.screen, (55, 68, 98), row_bg, 1, border_radius=8)
            lbl_s = stat_font.render(label, True, (172, 164, 140))
            val_s = stat_font.render(value, True, (248, 234, 190))
            self.screen.blit(lbl_s, (panel.x + 40, y))
            self.screen.blit(val_s, (panel.right - val_s.get_width() - 40, y))

        btn_w, btn_h = 200, 48
        btn_y = panel.bottom - 64
        self.end_main_menu_btn = pygame.Rect(panel.centerx - btn_w - 10, btn_y, btn_w, btn_h)
        self.end_quit_btn      = pygame.Rect(panel.centerx + 10,         btn_y, btn_w, btn_h)
        mouse_pos = self._get_mouse_pos()
        self._draw_end_button(self.end_main_menu_btn, "Main Menu",
                              (55, 80, 130), (38, 55, 92), mouse_pos)
        self._draw_end_button(self.end_quit_btn, "Quit Game",
                              (130, 45, 45), (92, 30, 35), mouse_pos)

    def _draw_game_over_screen(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 480, 310
        panel = pygame.Rect((SCREEN_W - panel_w) // 2, (SCREEN_H - panel_h) // 2, panel_w, panel_h)
        pygame.draw.rect(self.screen, (14, 20, 36), panel.move(0, 8), border_radius=24)
        pygame.draw.rect(self.screen, (14, 20, 36), panel, border_radius=24)
        pygame.draw.rect(self.screen, (192, 48, 48), panel, 3, border_radius=24)

        title_font = pygame.font.SysFont("georgia", 58, bold=True)
        title = title_font.render("GAME OVER", True, (220, 55, 55))
        tx = panel.centerx - title.get_width() // 2
        for dx, dy, a in ((4, 5, 150), (2, 3, 80)):
            sh = title_font.render("GAME OVER", True, (60, 10, 10))
            sh.set_alpha(a)
            self.screen.blit(sh, (tx + dx, panel.y + 18 + dy))
        self.screen.blit(title, (tx, panel.y + 18))

        sub_font = pygame.font.SysFont("georgia", 16)
        subtitle = sub_font.render("The castle has fallen.", True, (200, 170, 160))
        self.screen.blit(subtitle, (panel.centerx - subtitle.get_width() // 2, panel.y + 84))

        # Diamond separator (red tones)
        sep_y  = panel.y + 112
        sep_lx = panel.x + 30
        sep_rx = panel.right - 30
        sep_cx = panel.centerx
        pygame.draw.line(self.screen, (140, 48, 48), (sep_lx, sep_y), (sep_cx - 14, sep_y), 1)
        pygame.draw.line(self.screen, (140, 48, 48), (sep_cx + 14, sep_y), (sep_rx, sep_y), 1)
        pygame.draw.polygon(self.screen, (192, 60, 60), [
            (sep_cx, sep_y - 6), (sep_cx + 6, sep_y), (sep_cx, sep_y + 6), (sep_cx - 6, sep_y)])
        for ox in (-22, 22):
            pygame.draw.polygon(self.screen, (140, 44, 44), [
                (sep_cx + ox, sep_y - 4), (sep_cx + ox + 4, sep_y),
                (sep_cx + ox, sep_y + 4), (sep_cx + ox - 4, sep_y)])

        total_kills = sum(d["enemies_defeated"] for d in self.stats_tracker.history)
        stat_font = pygame.font.SysFont("georgia", 18, bold=True)
        stats_rows = [
            ("Wave Reached",     str(self.current_wave)),
            ("Enemies Defeated", str(total_kills)),
        ]
        for i, (label, value) in enumerate(stats_rows):
            y = panel.y + 126 + i * 40
            row_bg = pygame.Rect(panel.x + 24, y - 3, panel_w - 48, 30)
            bg_color = (28, 20, 20) if i % 2 == 0 else (22, 16, 16)
            pygame.draw.rect(self.screen, bg_color, row_bg, border_radius=8)
            pygame.draw.rect(self.screen, (80, 44, 44), row_bg, 1, border_radius=8)
            lbl_s = stat_font.render(label, True, (180, 158, 148))
            val_s = stat_font.render(value, True, (248, 220, 200))
            self.screen.blit(lbl_s, (panel.x + 40, y))
            self.screen.blit(val_s, (panel.right - val_s.get_width() - 40, y))

        btn_w, btn_h = 190, 48
        btn_y = panel.bottom - 62
        self.end_main_menu_btn = pygame.Rect(panel.centerx - btn_w - 10, btn_y, btn_w, btn_h)
        self.end_quit_btn      = pygame.Rect(panel.centerx + 10,         btn_y, btn_w, btn_h)
        mouse_pos = self._get_mouse_pos()
        self._draw_end_button(self.end_main_menu_btn, "Main Menu",
                              (55, 80, 130), (38, 55, 92), mouse_pos)
        self._draw_end_button(self.end_quit_btn, "Quit Game",
                              (130, 45, 45), (92, 30, 35), mouse_pos)

    def _draw_pause_overlay(self):
        overlay = pygame.Surface((GAME_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((4, 7, 14, 128))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(GAME_W // 2 - 120, SCREEN_H // 2 - 54, 240, 108)
        pygame.draw.rect(self.screen, (7, 10, 18), panel.move(0, 8), border_radius=18)
        pygame.draw.rect(self.screen, (23, 31, 50), panel, border_radius=18)
        pygame.draw.rect(self.screen, (118, 190, 245), panel, 2, border_radius=18)

        title = pygame.font.SysFont("georgia", 28, bold=True).render("Paused", True, (246, 236, 225))
        hint = pygame.font.SysFont("georgia", 12, bold=True).render("Press P or Resume to continue", True, (146, 158, 184))
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 22))
        self.screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.y + 66))

    def _draw_placement_preview(self):
        # Draw denied-placement flashes first (shown regardless of selected type)
        for f in self._invalid_placement_flashes:
            alpha = int(200 * (f["timer"] / 0.45))
            r = pygame.Rect(f["col"] * TILE_SIZE, f["row"] * TILE_SIZE + HUD_HEIGHT, TILE_SIZE, TILE_SIZE)
            flash = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            flash.fill((255, 60, 60, alpha))
            self.screen.blit(flash, r.topleft)
            pygame.draw.rect(self.screen, (255, 120, 120), r, 2, border_radius=4)

        if not self.selected_tower_type:
            return

        mouse_x, mouse_y = self._get_mouse_pos()
        if mouse_x >= GAME_W or mouse_y <= HUD_HEIGHT:
            return

        col = mouse_x // TILE_SIZE
        row = (mouse_y - HUD_HEIGHT) // TILE_SIZE
        max_col = GAME_W // TILE_SIZE - 1
        max_row = (SCREEN_H - HUD_HEIGHT) // TILE_SIZE - 1
        if col < 0 or col > max_col or row < 0 or row > max_row:
            return

        tile = (col, row)
        rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE + HUD_HEIGHT, TILE_SIZE, TILE_SIZE)
        valid = tile not in self.path_tiles and tile not in self.tower_map and self.gold >= TOWER_COSTS[self.selected_tower_type]

        # Semi-transparent tile tint
        overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        if valid:
            overlay.fill((80, 210, 100, 150))
            border_color = (180, 255, 190)
        else:
            overlay.fill((210, 60, 60, 150))
            border_color = (255, 170, 170)
        self.screen.blit(overlay, rect.topleft)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=4)

        # Range circle — only draw when placement would be valid
        if valid:
            center = rect.center
            range_radius = int(TOWER_CLASSES[self.selected_tower_type]((0, 0)).attack_range)
            range_surf = pygame.Surface((range_radius * 2 + 4, range_radius * 2 + 4), pygame.SRCALPHA)
            cx = cy = range_radius + 2
            pygame.draw.circle(range_surf, (80, 210, 100, 35), (cx, cy), range_radius)
            pygame.draw.circle(range_surf, (180, 255, 190, 100), (cx, cy), range_radius, 1)
            self.screen.blit(range_surf, (center[0] - cx, center[1] - cy))

    # ------------------------------------------------------------------
    # Path tile computation
    # ------------------------------------------------------------------

    def _compute_path_tiles(self):
        """Return a set of (col, row) tiles that overlap the enemy path.

        Uses precise rectangle-overlap math based on the actual drawn path
        width (TILE_SIZE + 8 outer border = 48px, half = 24px).  Each
        axis-aligned segment produces an axis-aligned rectangle; every grid
        tile that intersects that rectangle is marked as a path tile.
        Corner waypoints are also expanded by the half-width so that the
        full corner square is blocked.
        """
        half = (TILE_SIZE + 8) // 2  # 24 px — half the outer path width

        path_tiles = set()

        def _mark_rect(left, top, right, bottom):
            col_min = left // TILE_SIZE
            col_max = (right - 1) // TILE_SIZE
            row_min = (top - HUD_HEIGHT) // TILE_SIZE
            row_max = (bottom - 1 - HUD_HEIGHT) // TILE_SIZE
            for c in range(col_min, col_max + 1):
                for r in range(row_min, row_max + 1):
                    path_tiles.add((c, r))

        for i in range(len(self.waypoints) - 1):
            x1, y1 = self.waypoints[i]
            x2, y2 = self.waypoints[i + 1]

            if abs(x2 - x1) >= abs(y2 - y1):  # horizontal segment
                seg_left   = min(x1, x2)
                seg_right  = max(x1, x2) + 1
                seg_top    = y1 - half
                seg_bottom = y1 + half + 1
            else:                               # vertical segment
                seg_left   = x1 - half
                seg_right  = x1 + half + 1
                seg_top    = min(y1, y2)
                seg_bottom = max(y1, y2) + 1

            _mark_rect(seg_left, seg_top, seg_right, seg_bottom)

        # Also block the square around each waypoint corner so there are no
        # gaps where two segments meet at an angle.
        for x, y in self.waypoints:
            _mark_rect(x - half, y - half, x + half + 1, y + half + 1)

        return path_tiles
