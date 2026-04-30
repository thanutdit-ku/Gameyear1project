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

    # --- recording edge cases ---

    def test_record_kill_single(self):
        t = self._make_tracker()
        t.record_kill()
        self.assertEqual(t.enemies_defeated, 1)

    def test_record_damage_zero_no_change(self):
        t = self._make_tracker()
        t.record_damage(0)
        self.assertEqual(t.damage_dealt, 0)

    def test_record_gold_zero_no_change(self):
        t = self._make_tracker()
        t.record_gold_spent(0)
        self.assertEqual(t.gold_spent, 0)

    def test_record_kill_100_times(self):
        t = self._make_tracker()
        for _ in range(100):
            t.record_kill()
        self.assertEqual(t.enemies_defeated, 100)

    def test_record_damage_fractional_precision(self):
        t = self._make_tracker()
        t.record_damage(0.1)
        t.record_damage(0.2)
        self.assertAlmostEqual(t.damage_dealt, 0.3, places=5)

    def test_record_gold_multiple_small_amounts(self):
        t = self._make_tracker()
        for amount in [5, 10, 15, 20, 25]:
            t.record_gold_spent(amount)
        self.assertEqual(t.gold_spent, 75)

    def test_record_damage_large_value(self):
        t = self._make_tracker()
        t.record_damage(1_000_000)
        self.assertAlmostEqual(t.damage_dealt, 1_000_000)

    def test_record_gold_large_value(self):
        t = self._make_tracker()
        t.record_gold_spent(999_999)
        self.assertEqual(t.gold_spent, 999_999)

    def test_enemies_encountered_tracks_independently_from_kills(self):
        t = self._make_tracker()
        t.record_enemy_encountered()
        t.record_enemy_encountered()
        t.record_kill()
        self.assertEqual(t.enemies_encountered, 2)
        self.assertEqual(t.enemies_defeated, 1)

    # --- save_to_csv edge cases ---

    def test_save_with_zero_accumulators(self):
        t = self._make_tracker()
        t.save_to_csv(wave_number=1, castle_hp=100, survival_time=30.0)
        with open(self.csv_path, newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(int(rows[0]["enemies_defeated"]), 0)
        self.assertAlmostEqual(float(rows[0]["damage_dealt"]), 0.0)

    def test_save_survival_time_rounded_to_2_decimals(self):
        t = self._make_tracker()
        t.save_to_csv(wave_number=1, castle_hp=100, survival_time=30.557)
        self.assertAlmostEqual(t.history[0]["survival_time"], 30.56)

    def test_save_castle_hp_zero(self):
        t = self._make_tracker()
        t.save_to_csv(wave_number=1, castle_hp=0, survival_time=60.0)
        self.assertEqual(t.history[0]["castle_hp"], 0)

    def test_save_wave_number_ten(self):
        t = self._make_tracker()
        t.save_to_csv(wave_number=10, castle_hp=50, survival_time=120.0)
        self.assertEqual(t.history[0]["wave_number"], 10)

    def test_wave_accumulators_do_not_leak_between_waves(self):
        t = self._make_tracker()
        t.record_kill()
        t.record_damage(500)
        t.record_gold_spent(100)
        t.save_to_csv(wave_number=1, castle_hp=90, survival_time=30)
        t.save_to_csv(wave_number=2, castle_hp=80, survival_time=35)
        row2 = t.history[1]
        self.assertEqual(row2["enemies_defeated"], 0)
        self.assertAlmostEqual(row2["damage_dealt"], 0.0)
        self.assertAlmostEqual(row2["gold_spent"], 0.0)

    def test_enemies_encountered_not_reset_after_save(self):
        t = self._make_tracker()
        t.record_enemy_encountered()
        t.record_enemy_encountered()
        t.save_to_csv(wave_number=1, castle_hp=90, survival_time=30)
        self.assertEqual(t.enemies_encountered, 2)

    def test_csv_player_name_reflects_name_set_after_init(self):
        t = self._make_tracker("Temp")
        t.set_player_name("FinalName")
        t.save_to_csv(wave_number=1, castle_hp=100, survival_time=30)
        with open(self.csv_path, newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]["player_name"], "FinalName")

    def test_csv_appends_not_overwrites_on_second_save(self):
        t1 = self._make_tracker("P1")
        t1.save_to_csv(1, 100, 30)
        t2 = self._make_tracker("P2")
        t2.save_to_csv(1, 90, 25)
        with open(self.csv_path, newline="") as f:
            rows = list(csv.DictReader(f))
        names = [r["player_name"] for r in rows]
        self.assertIn("P1", names)
        self.assertIn("P2", names)

    def test_history_damage_matches_what_was_recorded(self):
        t = self._make_tracker()
        t.record_damage(123.45)
        t.save_to_csv(wave_number=1, castle_hp=100, survival_time=30)
        self.assertAlmostEqual(t.history[0]["damage_dealt"], 123.45)

    def test_history_gold_spent_zero_when_nothing_recorded(self):
        t = self._make_tracker()
        t.save_to_csv(wave_number=1, castle_hp=100, survival_time=30)
        self.assertAlmostEqual(t.history[0]["gold_spent"], 0.0)

    def test_history_preserves_insertion_order(self):
        t = self._make_tracker()
        for w in [1, 2, 3, 4, 5]:
            t.save_to_csv(wave_number=w, castle_hp=100 - w * 5, survival_time=w * 10)
        wave_nums = [row["wave_number"] for row in t.history]
        self.assertEqual(wave_nums, [1, 2, 3, 4, 5])

    def test_history_wave_number_matches_input(self):
        t = self._make_tracker()
        t.save_to_csv(wave_number=7, castle_hp=40, survival_time=200)
        self.assertEqual(t.history[0]["wave_number"], 7)

    # --- set_player_name edge cases ---

    def test_set_player_name_collapses_internal_spaces(self):
        t = self._make_tracker()
        t.set_player_name("King  Arthur")
        self.assertEqual(t.player_name, "King Arthur")

    def test_set_player_name_single_char(self):
        t = self._make_tracker()
        t.set_player_name("X")
        self.assertEqual(t.player_name, "X")

    def test_tracker_default_name_is_string(self):
        t = self.StatsTracker()
        self.assertIsInstance(t.player_name, str)

    # --- generate_report extended ---

    def test_generate_report_damage_min_correct(self):
        t = self._make_tracker()
        for dmg in [100, 300, 200]:
            t.record_damage(dmg)
            t.save_to_csv(wave_number=t.history.__len__() + 1, castle_hp=80, survival_time=30)
        self.assertAlmostEqual(t.generate_report()["damage_dealt"]["min"], 100)

    def test_generate_report_kills_max_correct(self):
        t = self._make_tracker()
        for kills in [3, 10, 6]:
            for _ in range(kills):
                t.record_kill()
            t.save_to_csv(wave_number=t.history.__len__() + 1, castle_hp=80, survival_time=30)
        self.assertEqual(t.generate_report()["enemies_defeated"]["max"], 10)

    def test_generate_report_hp_mean_correct(self):
        t = self._make_tracker()
        for hp in [100, 80, 60]:
            t.save_to_csv(wave_number=t.history.__len__() + 1, castle_hp=hp, survival_time=30)
        self.assertAlmostEqual(t.generate_report()["castle_hp"]["mean"], 80.0)

    def test_generate_report_survival_time_sum(self):
        t = self._make_tracker()
        for time in [30, 40, 50]:
            t.save_to_csv(wave_number=t.history.__len__() + 1, castle_hp=80, survival_time=time)
        self.assertAlmostEqual(t.generate_report()["survival_time"]["sum"], 120.0)

    def test_generate_report_total_waves_count(self):
        t = self._make_tracker()
        for i in range(7):
            t.save_to_csv(wave_number=i + 1, castle_hp=80, survival_time=30)
        self.assertEqual(t.generate_report()["total_waves"], 7)

    def test_generate_report_player_name_in_report(self):
        t = self._make_tracker("Knight")
        t.save_to_csv(1, 100, 30)
        self.assertEqual(t.generate_report()["player_name"], "Knight")
