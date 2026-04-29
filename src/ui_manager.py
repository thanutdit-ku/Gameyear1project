import io
import math
import pygame
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Layout constants (must match game area in game.py)
SCREEN_W, SCREEN_H = 800, 600
HUD_HEIGHT = 62
PANEL_WIDTH = 200
GAME_W = SCREEN_W - PANEL_WIDTH   # 600
GAME_H = SCREEN_H - HUD_HEIGHT    # 550

# Tower panel button config: key -> (label, cost, color)
TOWER_BUTTONS = {
    "archer": ("Archer",  100, (34, 139, 34)),
    "mage":   ("Mage",    150, (128, 0, 200)),
    "cannon": ("Cannon",  125, (180, 50, 0)),
}

HUD_BG_TOP = (18, 24, 38)
HUD_BG_BOTTOM = (12, 18, 30)
PANEL_BG = (15, 20, 33)
PANEL_EDGE = (62, 77, 103)
TEXT_PRIMARY = (241, 236, 225)
TEXT_MUTED = (126, 138, 162)
ACCENT_GOLD = (229, 183, 57)
FIELD_GOLD = (175, 139, 74)
FIELD_GOLD_LIGHT = (232, 202, 129)

TOWER_STATS = {
    "archer": {"ATK": 0.40, "SPD": 0.55, "RNG": 1.00},
    "mage":   {"ATK": 0.55, "SPD": 0.55, "RNG": 0.80},
    "cannon": {"ATK": 0.30, "SPD": 1.00, "RNG": 0.65},
}
TOWER_HOTKEYS = {"archer": "1", "mage": "2", "cannon": "3"}
BAR_COLORS = {
    "ATK": (230, 80,  80),
    "SPD": (80,  180, 230),
    "RNG": (80,  200, 120),
}


def _draw_vertical_gradient(surface, rect, top_color, bottom_color):
    height = max(rect.height, 1)
    for offset in range(height):
        t = offset / height
        color = tuple(
            int(top_color[i] + (bottom_color[i] - top_color[i]) * t)
            for i in range(3)
        )
        pygame.draw.line(
            surface,
            color,
            (rect.left, rect.top + offset),
            (rect.right, rect.top + offset),
        )


def _draw_card(surface, rect, top_color, bottom_color, border_color):
    _draw_vertical_gradient(surface, rect, top_color, bottom_color)
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=16)
    inner_glow = rect.inflate(-10, -10)
    pygame.draw.rect(surface, (120, 132, 156), inner_glow, 1, border_radius=12)


def _draw_stat_badge(surface, rect, label, value, accent, font_small, font_main, pulse=0.0):
    pygame.draw.rect(surface, (36, 45, 67), rect, border_radius=16)
    pygame.draw.rect(surface, (77, 92, 119), rect, 2, border_radius=16)
    if pulse > 0.0:
        glow_r = rect.inflate(int(6 * pulse), int(6 * pulse))
        glow_surf = pygame.Surface((glow_r.width, glow_r.height), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (220, 50, 50, int(140 * pulse)), glow_surf.get_rect(), 3, border_radius=18)
        surface.blit(glow_surf, glow_r.topleft)

    pygame.draw.circle(surface, accent, (rect.x + 18, rect.centery), 6)
    pygame.draw.circle(surface, (246, 236, 215), (rect.x + 18, rect.centery), 2)

    label_surf = font_small.render(label.upper(), True, TEXT_MUTED)
    value_surf = font_main.render(str(value), True, TEXT_PRIMARY)
    surface.blit(label_surf, (rect.x + 32, rect.y + 5))
    surface.blit(value_surf, (rect.right - value_surf.get_width() - 16, rect.y + 3))


class UIManager:
    def __init__(self, screen):
        self.screen = screen
        self.font_title = pygame.font.SysFont("georgia", 27, bold=True)
        self.font = pygame.font.SysFont("georgia", 18, bold=True)
        self.font_small = pygame.font.SysFont("georgia", 13, bold=True)
        self.font_large = pygame.font.SysFont("georgia", 36, bold=True)

        self.hud_elements = []        # reserved for future dynamic HUD elements
        self.tower_panel  = self._build_panel_rects()
        self.stats_screen = None      # cached pygame surface, built on demand
        self.sell_btn     = pygame.Rect(0, 0, 0, 0)  # set each frame in draw_tower_panel

    # ------------------------------------------------------------------
    # Panel rect setup
    # ------------------------------------------------------------------

    def _build_panel_rects(self):
        """Return a dict of tower_key -> pygame.Rect for each panel button."""
        panel_x = GAME_W + 12
        btn_w, btn_h = 176, 76
        rects = {}
        for i, key in enumerate(TOWER_BUTTONS):
            y = HUD_HEIGHT + 106 + i * (btn_h + 8)
            rects[key] = pygame.Rect(panel_x, y, btn_w, btn_h)
        return rects

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def draw_hud(self, gold, castle_hp, wave_number, player_name=""):
        """Draw the top HUD bar with gold, castle HP, and wave number."""
        bar_rect = pygame.Rect(0, 0, SCREEN_W, HUD_HEIGHT)
        _draw_vertical_gradient(self.screen, bar_rect, HUD_BG_TOP, HUD_BG_BOTTOM)
        pygame.draw.line(self.screen, (60, 75, 98), (0, HUD_HEIGHT), (SCREEN_W, HUD_HEIGHT), 2)

        title_font = pygame.font.SysFont("georgia", 30, bold=True)
        subtitle_font = pygame.font.SysFont(["thonburi", "arial", "georgia"], 13, bold=True)
        title = title_font.render("Kingdom's Last Stand", True, (245, 242, 235))
        self.screen.blit(title, (18, 9))

        if player_name:
            display_name = player_name
            while subtitle_font.size(f"Commander: {display_name}")[0] > 320 and len(display_name) > 1:
                display_name = display_name[:-1]
            if display_name != player_name:
                display_name = display_name[:-1] + "."
            subtitle_text = f"Commander: {display_name}"
            subtitle_color = (218, 201, 154)
        else:
            subtitle_text = "Hold the line. Spend wisely. Survive ten waves."
            subtitle_color = (104, 116, 140)
        subtitle = subtitle_font.render(subtitle_text, True, subtitle_color)
        self.screen.blit(subtitle, (20, 38))

        now = pygame.time.get_ticks()
        hp_pulse = 0.0
        if isinstance(castle_hp, (int, float)) and castle_hp <= 40:
            hp_pulse = 0.5 + 0.5 * math.sin(now / 250.0)

        badges = [
            (pygame.Rect(370, 15, 128, 28), "Gold",     gold,        ACCENT_GOLD,       0.0),
            (pygame.Rect(506, 15, 164, 28), "Castle HP", castle_hp,  (235, 116, 120),   hp_pulse),
            (pygame.Rect(678, 15, 108, 28), "Wave",     wave_number, (118, 190, 245),   0.0),
        ]

        for rect, label, value, accent, pulse in badges:
            _draw_stat_badge(self.screen, rect, label, value, accent, self.font_small, self.font, pulse)

    # ------------------------------------------------------------------
    # Tower panel
    # ------------------------------------------------------------------

    def draw_tower_panel(self, gold, selected_tower_type=None, sell_mode=False, mouse_pos=None):
        """Draw the right-side tower selection panel."""
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()

        panel_rect = pygame.Rect(GAME_W, HUD_HEIGHT, PANEL_WIDTH, SCREEN_H - HUD_HEIGHT)
        _draw_vertical_gradient(self.screen, panel_rect, PANEL_BG, (12, 15, 24))
        pygame.draw.line(self.screen, PANEL_EDGE, (GAME_W, HUD_HEIGHT), (GAME_W, SCREEN_H), 2)
        self._draw_armory_header()
        self._draw_treasury_box(gold)

        for key, rect in self.tower_panel.items():
            label, cost, color = TOWER_BUTTONS[key]
            can_afford = gold >= cost
            is_selected = key == selected_tower_type
            hover = rect.collidepoint(mouse_pos)
            self._draw_tower_card(key, rect, label, cost, color, can_afford, is_selected, hover)

        # --- [F] Sell Tower button (always visible, above ESC hint) ---
        self.sell_btn = pygame.Rect(GAME_W + 12, SCREEN_H - 74, PANEL_WIDTH - 24, 26)
        sell_hover = self.sell_btn.collidepoint(mouse_pos)
        if sell_mode:
            btn_bg     = (100, 14, 14) if not sell_hover else (130, 20, 20)
            btn_border = (230, 70, 70)
            btn_text   = "SELL MODE ON"
            btn_color  = (255, 100, 100)
        else:
            btn_bg     = (36, 46, 68) if not sell_hover else (50, 62, 90)
            btn_border = (80, 96, 128) if not sell_hover else (118, 190, 245)
            btn_text   = "[F] Sell Tower"
            btn_color  = (180, 190, 210)
        pygame.draw.rect(self.screen, (6, 9, 16), self.sell_btn.move(0, 4), border_radius=10)
        pygame.draw.rect(self.screen, btn_bg, self.sell_btn, border_radius=10)
        pygame.draw.rect(self.screen, btn_border, self.sell_btn, 2, border_radius=10)
        sell_font = pygame.font.SysFont("georgia", 13, bold=True)
        sell_surf = sell_font.render(btn_text, True, btn_color)
        self.screen.blit(sell_surf, (
            self.sell_btn.centerx - sell_surf.get_width() // 2,
            self.sell_btn.centery - sell_surf.get_height() // 2,
        ))

        # ESC hint at very bottom
        footer = pygame.Rect(GAME_W + 12, SCREEN_H - 42, PANEL_WIDTH - 24, 20)
        hint = self.font_small.render("ESC clears selection", True, (96, 108, 132))
        self.screen.blit(hint, (footer.centerx - hint.get_width() // 2, footer.y + 4))

    def _draw_armory_header(self):
        rect = pygame.Rect(GAME_W + 12, HUD_HEIGHT + 12, PANEL_WIDTH - 24, 44)
        shadow_rect = rect.move(0, 4)
        pygame.draw.rect(self.screen, (10, 14, 24), shadow_rect, border_radius=18)
        pygame.draw.rect(self.screen, (42, 51, 76), rect, border_radius=18)
        pygame.draw.rect(self.screen, (103, 118, 147), rect, 3, border_radius=18)
        # Inner highlight
        pygame.draw.rect(self.screen, (72, 86, 116), rect.inflate(-8, -8), 1, border_radius=14)
        # Diamond accents
        for dx in (rect.x + 14, rect.right - 14):
            pygame.draw.polygon(self.screen, (192, 158, 68), [
                (dx, rect.centery - 6), (dx + 5, rect.centery),
                (dx, rect.centery + 6), (dx - 5, rect.centery),
            ])
        title = pygame.font.SysFont("georgia", 20, bold=True).render("Armory", True, (248, 228, 160))
        # Title shadow
        sh = pygame.font.SysFont("georgia", 20, bold=True).render("Armory", True, (10, 8, 4))
        sh.set_alpha(130)
        self.screen.blit(sh, (rect.centerx - title.get_width() // 2 + 2, rect.y + 11))
        self.screen.blit(title, (rect.centerx - title.get_width() // 2, rect.y + 9))

    def _draw_treasury_box(self, gold):
        rect = pygame.Rect(GAME_W + 12, HUD_HEIGHT + 66, PANEL_WIDTH - 24, 26)
        pygame.draw.rect(self.screen, (34, 43, 64), rect, border_radius=15)
        pygame.draw.rect(self.screen, (74, 89, 116), rect, 2, border_radius=15)
        label = pygame.font.SysFont("georgia", 12, bold=True).render("Treasury", True, (160, 171, 189))
        amount = pygame.font.SysFont("georgia", 16, bold=True).render(f"{gold} gold", True, ACCENT_GOLD)
        self.screen.blit(label, (rect.x + 14, rect.y + 6))
        self.screen.blit(amount, (rect.right - amount.get_width() - 12, rect.y + 3))

    def _draw_tower_card(self, key, rect, label, cost, color, can_afford, is_selected, hover):
        base = (35, 42, 62) if can_afford else (47, 50, 58)
        border = FIELD_GOLD_LIGHT if is_selected else (74, 89, 116)
        pygame.draw.rect(self.screen, (8, 12, 20), rect.move(0, 5), border_radius=18)
        pygame.draw.rect(self.screen, base, rect, border_radius=18)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=18)
        if is_selected:
            glow = rect.inflate(4, 4)
            gs = pygame.Surface((glow.width, glow.height), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*FIELD_GOLD_LIGHT, 55), gs.get_rect(), 3, border_radius=20)
            self.screen.blit(gs, glow.topleft)
        elif hover:
            pygame.draw.rect(self.screen, (120, 133, 164), rect.inflate(2, 2), 1, border_radius=19)

        # Color stripe
        stripe_rect = pygame.Rect(rect.x + 12, rect.y + 10, 7, rect.height - 20)
        pygame.draw.rect(self.screen, color, stripe_rect, border_radius=5)

        # Icon circle (smaller, raised to top half)
        icon_center = (rect.x + 44, rect.y + 28)
        pygame.draw.circle(self.screen, color, icon_center, 14)
        lighter = tuple(min(255, c + 50) for c in color)
        pygame.draw.circle(self.screen, lighter, icon_center, 14, 2)
        self._draw_tower_letter(key, icon_center)

        text_x = rect.x + 68

        name_font  = pygame.font.SysFont("georgia", 14, bold=True)
        cost_font  = pygame.font.SysFont("georgia", 11, bold=True)
        trait_font = pygame.font.SysFont("verdana", 9,  bold=True)
        bar_font   = pygame.font.SysFont("verdana", 8,  bold=True)

        # Row 1: name
        name_surf = name_font.render(label, True, (247, 244, 236))
        self.screen.blit(name_surf, (text_x, rect.y + 6))

        # Hotkey badge (top-right corner)
        hotkey = TOWER_HOTKEYS.get(key, "")
        if hotkey:
            hk_rect = pygame.Rect(rect.right - 22, rect.y + 5, 18, 18)
            pygame.draw.rect(self.screen, (42, 52, 76), hk_rect, border_radius=9)
            pygame.draw.rect(self.screen, (90, 108, 142), hk_rect, 1, border_radius=9)
            hk_surf = pygame.font.SysFont("georgia", 11, bold=True).render(hotkey, True, (200, 215, 240))
            self.screen.blit(hk_surf, (hk_rect.centerx - hk_surf.get_width() // 2, hk_rect.y + 2))

        # Row 2: cost badge + trait tag
        price_rect = pygame.Rect(text_x, rect.y + 23, 44, 14)
        pygame.draw.rect(self.screen, (57, 68, 94), price_rect, border_radius=8)
        pygame.draw.rect(self.screen, (101, 116, 144), price_rect, 1, border_radius=8)
        cost_surf = cost_font.render(f"{cost}g", True, ACCENT_GOLD if can_afford else (160, 160, 160))
        self.screen.blit(cost_surf, (price_rect.centerx - cost_surf.get_width() // 2, price_rect.y + 1))

        trait_surf = trait_font.render(self._get_tower_trait(key), True, color)
        self.screen.blit(trait_surf, (text_x + 50, rect.y + 24))

        # Rows 3-5: stat bars (ATK / SPD / RNG)
        bar_total_w = rect.right - text_x - 8
        lbl_w = 24
        fill_w_max = bar_total_w - lbl_w - 2
        stats = TOWER_STATS.get(key, {})
        for i, (stat_name, bar_color) in enumerate(BAR_COLORS.items()):
            val = stats.get(stat_name, 0.0)
            by = rect.y + 43 + i * 11
            lbl = bar_font.render(stat_name, True, TEXT_MUTED)
            self.screen.blit(lbl, (text_x, by))
            bg_rect = pygame.Rect(text_x + lbl_w, by, fill_w_max, 7)
            pygame.draw.rect(self.screen, (28, 35, 52), bg_rect, border_radius=4)
            fw = max(2, int(fill_w_max * val))
            fill_rect = pygame.Rect(text_x + lbl_w, by, fw, 7)
            pygame.draw.rect(self.screen, bar_color, fill_rect, border_radius=4)
            shine = pygame.Surface((max(1, fw - 4), 2), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 55))
            self.screen.blit(shine, (fill_rect.x + 2, fill_rect.y + 1))

    def _draw_tower_letter(self, key, center):
        x, y = center
        letters = {"archer": "A", "mage": "M", "cannon": "C"}
        label = pygame.font.SysFont("georgia", 15, bold=True).render(letters[key], True, (248, 246, 238))
        self.screen.blit(label, (x - label.get_width() // 2, y - label.get_height() // 2 - 1))

    def _get_tower_trait(self, key):
        traits = {
            "archer": "Crit chance",
            "mage": "Control",
            "cannon": "AoE burst",
        }
        return traits[key]

    def _get_tower_flavor_text(self, key):
        descriptions = {
            "archer": "Precise rapid shots",
            "mage": "Arcane burst and slow",
            "cannon": "Heavy splash impact",
        }
        return descriptions[key]

    def get_tower_clicked(self, mouse_pos):
        """Return tower key if a panel button was clicked, else None."""
        for key, rect in self.tower_panel.items():
            if rect.collidepoint(mouse_pos):
                return key
        return None

    # ------------------------------------------------------------------
    # Stats screen
    # ------------------------------------------------------------------

    def draw_stats_screen(self, report, history):
        """Render the end-game stats overlay: summary table + 3 matplotlib graphs."""
        if not report or not history:
            return

        # Build (or use cached) graph surface
        if self.stats_screen is None:
            self.stats_screen = self._build_stats_surface(report, history)

        self.screen.blit(self.stats_screen, (0, 0))

    def _build_stats_surface(self, report, history):
        """Compose the full stats screen into a single pygame surface."""
        surf = pygame.Surface((SCREEN_W, SCREEN_H))
        surf.fill((15, 15, 25))

        # Title
        title = self.font_large.render("Game Over — Session Stats", True, (255, 215, 0))
        surf.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 12))

        # Summary table
        self._draw_summary_table(surf, report, y_start=55)

        # 3 graphs rendered via matplotlib
        graph_surf = self._render_graphs(history)
        surf.blit(graph_surf, (0, 270))

        # Prompt to quit
        prompt = self.font_small.render("Press Q or close the window to exit.", True, (180, 180, 180))
        surf.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, SCREEN_H - 22))

        return surf

    def _draw_summary_table(self, surf, report, y_start):
        """Draw a text-based summary statistics table onto surf."""
        features = [
            ("Enemies Defeated", "enemies_defeated"),
            ("Damage Dealt",     "damage_dealt"),
            ("Gold Spent",       "gold_spent"),
            ("Castle HP",        "castle_hp"),
            ("Survival Time",    "survival_time"),
        ]
        headers = ["Feature", "Mean", "Min", "Max", "Std Dev"]
        col_x   = [10, 240, 360, 450, 550]
        row_h   = 26

        # Header row
        for i, h in enumerate(headers):
            s = self.font_small.render(h, True, (255, 215, 0))
            surf.blit(s, (col_x[i], y_start))

        pygame.draw.line(surf, (100, 100, 100),
                         (10, y_start + row_h - 4), (700, y_start + row_h - 4), 1)

        for row_i, (display_name, key) in enumerate(features):
            y = y_start + row_h + row_i * row_h
            stats = report.get(key, {})

            cells = [
                display_name,
                str(stats.get("mean", "-")),
                str(stats.get("min",  "-")),
                str(stats.get("max",  "-")),
                str(stats.get("std",  "-")),
            ]
            color = (220, 220, 220) if row_i % 2 == 0 else (180, 180, 200)
            for i, cell in enumerate(cells):
                s = self.font_small.render(cell, True, color)
                surf.blit(s, (col_x[i], y))

    def _render_graphs(self, history):
        """Generate 3 matplotlib graphs and return them as a combined pygame surface."""
        waves   = [d["wave_number"]     for d in history]
        enemies = [d["enemies_defeated"] for d in history]
        gold    = [d["gold_spent"]       for d in history]
        hp      = [d["castle_hp"]        for d in history]

        fig, axes = plt.subplots(1, 3, figsize=(10, 3.2), facecolor="#0f0f19")
        fig.subplots_adjust(left=0.07, right=0.97, wspace=0.4)

        style = dict(color="#0f0f19", labelcolor="white", titlecolor="white")

        # Graph 1 — Histogram: enemies defeated distribution
        ax1 = axes[0]
        ax1.set_facecolor("#1a1a2e")
        ax1.hist(enemies, bins=max(len(set(enemies)), 1), color="#4a90d9", edgecolor="white")
        ax1.set_title("Enemies Defeated", **{k: v for k, v in style.items() if k != "color"})
        ax1.set_xlabel("Count", color="white")
        ax1.set_ylabel("Frequency", color="white")
        ax1.tick_params(colors="white")

        # Graph 2 — Line graph: castle HP per wave (time-series)
        ax2 = axes[1]
        ax2.set_facecolor("#1a1a2e")
        ax2.plot(waves, hp, color="#e05555", marker="o", linewidth=2)
        ax2.set_title("Castle HP per Wave", **{k: v for k, v in style.items() if k != "color"})
        ax2.set_xlabel("Wave", color="white")
        ax2.set_ylabel("Castle HP", color="white")
        ax2.tick_params(colors="white")

        # Graph 3 — Bar graph: gold spent per wave (proportion)
        ax3 = axes[2]
        ax3.set_facecolor("#1a1a2e")
        ax3.bar(waves, gold, color="#d4a017", edgecolor="white")
        ax3.set_title("Gold Spent per Wave", **{k: v for k, v in style.items() if k != "color"})
        ax3.set_xlabel("Wave", color="white")
        ax3.set_ylabel("Gold", color="white")
        ax3.tick_params(colors="white")

        # Convert figure to pygame surface via in-memory PNG
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=80, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close(fig)

        graph_surf = pygame.image.load(buf, "graph.png")
        return pygame.transform.scale(graph_surf, (SCREEN_W, SCREEN_H - 270 - 24))
