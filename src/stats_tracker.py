import csv
import os
import pandas as pd
from datetime import datetime

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "game_stats.csv")
SUMMARY_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "game_summary.csv")
CSV_COLUMNS = ["session_id", "wave_number", "enemies_defeated",
               "damage_dealt", "gold_spent", "castle_hp", "survival_time"]
SUMMARY_CSV_COLUMNS = [
    "session_id",
    "waves_played",
    "total_damage_dealt",
    "castle_hp_lost",
    "enemies_encountered",
    "result",
]


class StatsTracker:
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Per-wave accumulators (reset after each save)
        self.enemies_defeated = 0
        self.damage_dealt = 0
        self.gold_spent = 0
        self.enemies_encountered = 0

        # Session-level history (one dict per wave, used for generate_report)
        self.history = []
        self.summary_saved = False

        self._ensure_csv_exists()

    # ------------------------------------------------------------------
    # Recording methods (called during gameplay)
    # ------------------------------------------------------------------

    def record_kill(self):
        """Call once each time an enemy is defeated."""
        self.enemies_defeated += 1

    def record_damage(self, amount):
        """Call each time a tower deals damage."""
        self.damage_dealt += amount

    def record_enemy_encountered(self):
        """Call once each time an enemy enters the battlefield."""
        self.enemies_encountered += 1

    def record_gold_spent(self, amount):
        """Call each time the player spends gold."""
        self.gold_spent += amount

    # ------------------------------------------------------------------
    # CSV persistence
    # ------------------------------------------------------------------

    def save_to_csv(self, wave_number, castle_hp, survival_time):
        """Append one row for the completed wave, then reset wave accumulators."""
        row = {
            "session_id": self.session_id,
            "wave_number": wave_number,
            "enemies_defeated": self.enemies_defeated,
            "damage_dealt": self.damage_dealt,
            "gold_spent": self.gold_spent,
            "castle_hp": castle_hp,
            "survival_time": round(survival_time, 2),
        }

        self.history.append(row)

        with open(CSV_PATH, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writerow(row)

        self._reset_wave()

    def save_session_summary(self, waves_played, castle_hp_lost, result):
        """Append one final summary row for the whole play session."""
        if self.summary_saved:
            return

        row = {
            "session_id": self.session_id,
            "waves_played": waves_played,
            "total_damage_dealt": sum(d["damage_dealt"] for d in self.history),
            "castle_hp_lost": castle_hp_lost,
            "enemies_encountered": self.enemies_encountered,
            "result": result,
        }

        with open(SUMMARY_CSV_PATH, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=SUMMARY_CSV_COLUMNS)
            writer.writerow(row)

        self.summary_saved = True

    def _reset_wave(self):
        """Reset per-wave accumulators for the next wave."""
        self.enemies_defeated = 0
        self.damage_dealt = 0
        self.gold_spent = 0

    def _ensure_csv_exists(self):
        """Create the CSV with headers if it does not exist yet."""
        os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
        if not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) == 0:
            with open(CSV_PATH, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()
        if not os.path.exists(SUMMARY_CSV_PATH) or os.path.getsize(SUMMARY_CSV_PATH) == 0:
            with open(SUMMARY_CSV_PATH, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=SUMMARY_CSV_COLUMNS)
                writer.writeheader()

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def generate_report(self):
        """Return a dict of summary statistics for this session using pandas."""
        if not self.history:
            return {}

        df = pd.DataFrame(self.history)
        numeric_cols = ["enemies_defeated", "damage_dealt",
                        "gold_spent", "castle_hp", "survival_time"]

        report = {}
        for col in numeric_cols:
            report[col] = {
                "mean": round(df[col].mean(), 2),
                "min": int(df[col].min()),
                "max": int(df[col].max()),
                "std": round(df[col].std(), 2),
                "sum": round(df[col].sum(), 2),
            }

        report["total_waves"] = len(self.history)
        report["session_id"] = self.session_id
        return report
