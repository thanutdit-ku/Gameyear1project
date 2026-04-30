import csv
import os
import tempfile
import unittest
from unittest.mock import patch


class TestStatsTracker(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.tmpdir, "game_stats.csv")
        self.patcher = patch("src.stats_tracker.CSV_PATH", self.csv_path)
        self.patcher.start()
        from src.stats_tracker import StatsTracker
        self.StatsTracker = StatsTracker

    def tearDown(self):
        self.patcher.stop()

    def _make_tracker(self, name="TestPlayer"):
        return self.StatsTracker(player_name=name)

    # --- initial state ---

    def test_initial_accumulators_are_zero(self):
        t = self._make_tracker()
        self.assertEqual(t.enemies_defeated, 0)
        self.assertEqual(t.damage_dealt, 0)
        self.assertEqual(t.gold_spent, 0)
        self.assertEqual(t.enemies_encountered, 0)

    def test_initial_history_is_empty(self):
        t = self._make_tracker()
        self.assertEqual(t.history, [])

    def test_player_name_is_set(self):
        t = self._make_tracker("Hero")
        self.assertEqual(t.player_name, "Hero")

    # --- recording ---

    def test_record_kill_increments(self):
        t = self._make_tracker()
        t.record_kill()
        t.record_kill()
        self.assertEqual(t.enemies_defeated, 2)

    def test_record_damage_accumulates(self):
        t = self._make_tracker()
        t.record_damage(50.5)
        t.record_damage(20.0)
        self.assertAlmostEqual(t.damage_dealt, 70.5)

    def test_record_gold_spent_accumulates(self):
        t = self._make_tracker()
        t.record_gold_spent(100)
        t.record_gold_spent(150)
        self.assertEqual(t.gold_spent, 250)

    def test_record_enemy_encountered_increments(self):
        t = self._make_tracker()
        t.record_enemy_encountered()
        t.record_enemy_encountered()
        self.assertEqual(t.enemies_encountered, 2)

    # --- save_to_csv ---

    def test_save_resets_accumulators(self):
        t = self._make_tracker()
        t.record_kill()
        t.record_damage(200)
        t.record_gold_spent(100)
        t.save_to_csv(wave_number=1, castle_hp=80, survival_time=60.0)
        self.assertEqual(t.enemies_defeated, 0)
        self.assertEqual(t.damage_dealt, 0)
        self.assertEqual(t.gold_spent, 0)

    def test_save_adds_to_history(self):
        t = self._make_tracker()
        t.save_to_csv(wave_number=1, castle_hp=90, survival_time=30.0)
        t.save_to_csv(wave_number=2, castle_hp=70, survival_time=40.0)
        self.assertEqual(len(t.history), 2)

    def test_save_writes_correct_data_to_csv(self):
        t = self._make_tracker("Alice")
        t.record_kill()
        t.record_kill()
        t.record_damage(300)
        t.record_gold_spent(150)
        t.save_to_csv(wave_number=3, castle_hp=55, survival_time=90.5)
        with open(self.csv_path, newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["player_name"], "Alice")
        self.assertEqual(int(rows[0]["wave_number"]), 3)
        self.assertEqual(int(rows[0]["enemies_defeated"]), 2)
        self.assertAlmostEqual(float(rows[0]["damage_dealt"]), 300.0)
        self.assertEqual(int(rows[0]["gold_spent"]), 150)
        self.assertAlmostEqual(float(rows[0]["castle_hp"]), 55.0)
        self.assertAlmostEqual(float(rows[0]["survival_time"]), 90.5)

    def test_multiple_saves_produce_multiple_csv_rows(self):
        t = self._make_tracker()
        t.save_to_csv(1, 100, 30)
        t.save_to_csv(2, 90, 35)
        t.save_to_csv(3, 80, 40)
        with open(self.csv_path, newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 3)

    def test_history_row_contains_all_fields(self):
        t = self._make_tracker("Charlie")
        t.save_to_csv(wave_number=2, castle_hp=75, survival_time=55.5)
        row = t.history[0]
        for key in ["player_name", "wave_number", "enemies_defeated",
                    "damage_dealt", "gold_spent", "castle_hp", "survival_time"]:
            self.assertIn(key, row)

    # --- CSV file ---

    def test_csv_has_correct_headers(self):
        self._make_tracker()
        with open(self.csv_path, newline="") as f:
            reader = csv.DictReader(f)
            self.assertEqual(
                reader.fieldnames,
                ["player_name", "wave_number", "enemies_defeated",
                 "damage_dealt", "gold_spent", "castle_hp", "survival_time"]
            )

    def test_csv_created_on_init(self):
        self._make_tracker()
        self.assertTrue(os.path.exists(self.csv_path))

    # --- set_player_name ---

    def test_set_player_name_updates_name(self):
        t = self._make_tracker("Old")
        t.set_player_name("New")
        self.assertEqual(t.player_name, "New")

    def test_set_player_name_strips_whitespace(self):
        t = self._make_tracker()
        t.set_player_name("  Hero  ")
        self.assertEqual(t.player_name, "Hero")

    def test_set_player_name_empty_string_ignored(self):
        t = self._make_tracker("Original")
        t.set_player_name("   ")
        self.assertEqual(t.player_name, "Original")

    def test_set_session_id_is_alias(self):
        t = self._make_tracker()
        t.set_session_id("Alias")
        self.assertEqual(t.player_name, "Alias")

    # --- generate_report ---

    def test_generate_report_empty_returns_empty_dict(self):
        t = self._make_tracker()
        self.assertEqual(t.generate_report(), {})

    def test_generate_report_single_wave(self):
        t = self._make_tracker("Bob")
        for _ in range(3):
            t.record_kill()
        t.record_damage(600)
        t.record_gold_spent(200)
        t.save_to_csv(wave_number=1, castle_hp=100, survival_time=30.0)
        report = t.generate_report()
        self.assertEqual(report["total_waves"], 1)
        self.assertEqual(report["player_name"], "Bob")
        self.assertAlmostEqual(report["enemies_defeated"]["sum"], 3)
        self.assertAlmostEqual(report["damage_dealt"]["mean"], 600.0)

    def test_generate_report_multiple_waves_totals(self):
        t = self._make_tracker()
        wave_data = [(5, 500, 100, 90, 30), (8, 800, 150, 70, 40), (3, 300, 80, 50, 25)]
        for w, (kills, dmg, gold, hp, time) in enumerate(wave_data, start=1):
            for _ in range(kills):
                t.record_kill()
            t.record_damage(dmg)
            t.record_gold_spent(gold)
            t.save_to_csv(wave_number=w, castle_hp=hp, survival_time=time)
        report = t.generate_report()
        self.assertEqual(report["total_waves"], 3)
        self.assertAlmostEqual(report["enemies_defeated"]["sum"], 16)
        self.assertAlmostEqual(report["gold_spent"]["sum"], 330)
        self.assertAlmostEqual(report["damage_dealt"]["max"], 800)

    def test_generate_report_has_stat_keys(self):
        t = self._make_tracker()
        t.save_to_csv(1, 100, 30)
        report = t.generate_report()
        for col in ["enemies_defeated", "damage_dealt", "gold_spent", "castle_hp", "survival_time"]:
            self.assertIn(col, report)
            for stat in ["mean", "min", "max", "std", "sum"]:
                self.assertIn(stat, report[col])
