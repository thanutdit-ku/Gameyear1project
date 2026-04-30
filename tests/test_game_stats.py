import sys
import unittest
from unittest.mock import MagicMock

# Mock pygame and all submodules before importing game
for _mod in [
    "pygame", "pygame.font", "pygame.mixer", "pygame.image", "pygame.transform",
    "pygame.draw", "pygame.display", "pygame.time", "pygame.event",
    "pygame.key", "pygame.mouse", "pygame.locals", "pygame.Surface",
]:
    sys.modules[_mod] = MagicMock()

from src.game import Game  # noqa: E402


def _new_game():
    """Return a Game instance without running __init__ (no pygame needed)."""
    return Game.__new__(Game)


class TestToNumber(unittest.TestCase):
    def setUp(self):
        self.game = _new_game()

    def test_valid_integer_string(self):
        self.assertEqual(self.game._to_number("42"), 42.0)

    def test_valid_float_string(self):
        self.assertAlmostEqual(self.game._to_number("3.14"), 3.14)

    def test_invalid_string_returns_zero(self):
        self.assertEqual(self.game._to_number("abc"), 0.0)

    def test_none_returns_zero(self):
        self.assertEqual(self.game._to_number(None), 0.0)

    def test_empty_string_returns_zero(self):
        self.assertEqual(self.game._to_number(""), 0.0)

    def test_numeric_value_passthrough(self):
        self.assertAlmostEqual(self.game._to_number(99.9), 99.9)

    def test_zero_string(self):
        self.assertEqual(self.game._to_number("0"), 0.0)

    def test_negative_string(self):
        self.assertAlmostEqual(self.game._to_number("-5.5"), -5.5)


class TestPlayerStats(unittest.TestCase):
    def setUp(self):
        self.game = _new_game()

    def _row(self, name, wave, kills, damage, gold, hp, time):
        return {
            "player_name": name,
            "wave_number": str(wave),
            "enemies_defeated": str(kills),
            "damage_dealt": str(damage),
            "gold_spent": str(gold),
            "castle_hp": str(hp),
            "survival_time": str(time),
        }

    # --- basic cases ---

    def test_empty_rows_returns_empty_list(self):
        self.assertEqual(self.game._player_stats([]), [])

    def test_single_player_single_wave_fields(self):
        rows = [self._row("Alice", 1, 10, 500, 100, 80, 30)]
        result = self.game._player_stats(rows)
        self.assertEqual(len(result), 1)
        p = result[0]
        self.assertEqual(p["name"], "Alice")
        self.assertEqual(p["wave"], 1)
        self.assertAlmostEqual(p["kills"], 10)
        self.assertAlmostEqual(p["damage"], 500)
        self.assertAlmostEqual(p["gold"], 100)
        self.assertAlmostEqual(p["hp"], 80)
        self.assertAlmostEqual(p["time"], 30)

    # --- aggregation across waves ---

    def test_kills_damage_gold_time_are_summed(self):
        rows = [
            self._row("Bob", 1, 5, 300, 100, 90, 30),
            self._row("Bob", 2, 8, 400, 150, 70, 40),
            self._row("Bob", 3, 3, 200, 80, 50, 25),
        ]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["kills"], 16)
        self.assertAlmostEqual(p["damage"], 900)
        self.assertAlmostEqual(p["gold"], 330)
        self.assertAlmostEqual(p["time"], 95)

    def test_wave_is_max_not_sum(self):
        rows = [
            self._row("Carol", 1, 0, 0, 0, 90, 10),
            self._row("Carol", 5, 0, 0, 0, 60, 10),
            self._row("Carol", 3, 0, 0, 0, 75, 10),
        ]
        p = self.game._player_stats(rows)[0]
        self.assertEqual(p["wave"], 5)

    def test_hp_is_average_not_last(self):
        rows = [
            self._row("Dave", 1, 0, 0, 0, 100, 10),
            self._row("Dave", 2, 0, 0, 0, 60, 10),
            self._row("Dave", 3, 0, 0, 0, 80, 10),
        ]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["hp"], 80.0)

    # --- efficiency ---

    def test_efficiency_equals_damage_over_gold(self):
        rows = [self._row("Eve", 1, 5, 1000, 200, 80, 30)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["efficiency"], 5.0)

    def test_efficiency_zero_gold_uses_fallback_of_one(self):
        rows = [self._row("Frank", 1, 5, 500, 0, 80, 30)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["efficiency"], 500.0)

    def test_efficiency_zero_damage_is_zero(self):
        rows = [self._row("Ghost", 1, 0, 0, 200, 80, 30)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["efficiency"], 0.0)

    # --- multiple players ---

    def test_multiple_players_are_separated(self):
        rows = [
            self._row("Alice", 1, 10, 500, 100, 80, 30),
            self._row("Bob",   1,  5, 200, 150, 90, 25),
            self._row("Alice", 2,  8, 400, 120, 60, 40),
        ]
        result = self.game._player_stats(rows)
        names = {p["name"] for p in result}
        self.assertEqual(names, {"Alice", "Bob"})

    def test_alice_stats_are_isolated_from_bob(self):
        rows = [
            self._row("Alice", 1, 10, 500, 100, 80, 30),
            self._row("Bob",   1,  5, 200, 150, 90, 25),
            self._row("Alice", 2,  8, 400, 120, 60, 40),
        ]
        result = self.game._player_stats(rows)
        alice = next(p for p in result if p["name"] == "Alice")
        self.assertAlmostEqual(alice["kills"], 18)
        self.assertAlmostEqual(alice["damage"], 900)

    def test_bob_stats_are_isolated_from_alice(self):
        rows = [
            self._row("Alice", 1, 10, 500, 100, 80, 30),
            self._row("Bob",   1,  5, 200, 150, 90, 25),
        ]
        result = self.game._player_stats(rows)
        bob = next(p for p in result if p["name"] == "Bob")
        self.assertAlmostEqual(bob["kills"], 5)
        self.assertAlmostEqual(bob["gold"], 150)

    # --- edge / error cases ---

    def test_missing_player_name_defaults_to_dash(self):
        rows = [{
            "wave_number": "1", "enemies_defeated": "0", "damage_dealt": "0",
            "gold_spent": "0", "castle_hp": "100", "survival_time": "30"
        }]
        p = self.game._player_stats(rows)[0]
        self.assertEqual(p["name"], "-")

    def test_non_numeric_fields_treated_as_zero(self):
        rows = [self._row("Grace", "bad", "bad", "bad", "bad", "bad", "bad")]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["kills"], 0)
        self.assertAlmostEqual(p["damage"], 0)
        self.assertAlmostEqual(p["gold"], 0)

    def test_result_has_required_keys(self):
        rows = [self._row("Hank", 2, 7, 350, 120, 70, 45)]
        p = self.game._player_stats(rows)[0]
        for key in ["name", "wave", "kills", "damage", "gold", "hp", "time", "efficiency"]:
            self.assertIn(key, p)

    def test_single_wave_hp_equals_that_wave_hp(self):
        rows = [self._row("Ivy", 1, 0, 0, 0, 77, 20)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["hp"], 77.0)

    # --- _to_number extra cases ---

    def test_whitespace_only_string_returns_zero(self):
        self.assertEqual(self.game._to_number("   "), 0.0)

    def test_scientific_notation_string(self):
        self.assertAlmostEqual(self.game._to_number("1e3"), 1000.0)

    def test_large_number_string(self):
        self.assertAlmostEqual(self.game._to_number("999999"), 999999.0)

    def test_integer_passthrough(self):
        self.assertAlmostEqual(self.game._to_number(42), 42.0)

    def test_string_with_two_dots_returns_zero(self):
        self.assertEqual(self.game._to_number("1.2.3"), 0.0)

    # --- _player_stats: waves list ---

    def test_waves_list_contains_all_wave_numbers(self):
        rows = [
            self._row("Jack", 1, 5, 200, 100, 90, 30),
            self._row("Jack", 3, 8, 300, 120, 70, 40),
            self._row("Jack", 5, 3, 150, 80, 55, 25),
        ]
        p = self.game._player_stats(rows)[0]
        self.assertIn(1.0, p["waves"])
        self.assertIn(3.0, p["waves"])
        self.assertIn(5.0, p["waves"])

    def test_waves_list_length_matches_row_count(self):
        rows = [self._row("Kate", i, 0, 0, 0, 80, 10) for i in range(1, 6)]
        p = self.game._player_stats(rows)[0]
        self.assertEqual(len(p["waves"]), 5)

    # --- _player_stats: HP edge cases ---

    def test_hp_average_includes_zero_hp(self):
        rows = [
            self._row("Leo", 1, 0, 0, 0, 100, 10),
            self._row("Leo", 2, 0, 0, 0, 0, 10),
        ]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["hp"], 50.0)

    def test_hp_all_zero_averages_to_zero(self):
        rows = [self._row("Mia", i, 0, 0, 0, 0, 10) for i in range(1, 4)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["hp"], 0.0)

    def test_hp_all_100_averages_to_100(self):
        rows = [self._row("Ned", i, 0, 0, 0, 100, 10) for i in range(1, 6)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["hp"], 100.0)

    # --- _player_stats: zero stats ---

    def test_kills_zero_across_all_waves(self):
        rows = [self._row("Olivia", i, 0, 500, 100, 80, 30) for i in range(1, 4)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["kills"], 0.0)

    def test_damage_zero_across_all_waves(self):
        rows = [self._row("Pete", i, 5, 0, 100, 80, 30) for i in range(1, 4)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["damage"], 0.0)

    def test_gold_zero_across_all_waves(self):
        rows = [self._row("Quinn", i, 5, 300, 0, 80, 30) for i in range(1, 4)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["gold"], 0.0)

    # --- _player_stats: 10-wave run ---

    def test_player_with_ten_waves_kills_sum(self):
        rows = [self._row("Rose", i, 10, 500, 100, 100 - i * 5, i * 10) for i in range(1, 11)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["kills"], 100)

    def test_player_with_ten_waves_max_wave(self):
        rows = [self._row("Sam", i, 5, 300, 100, 80, 30) for i in range(1, 11)]
        p = self.game._player_stats(rows)[0]
        self.assertEqual(p["wave"], 10)

    def test_player_with_ten_waves_damage_sum(self):
        rows = [self._row("Tina", i, 5, 200, 100, 80, 30) for i in range(1, 11)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["damage"], 2000)

    # --- _player_stats: efficiency edge cases ---

    def test_efficiency_equal_damage_and_gold(self):
        rows = [self._row("Uma", 1, 5, 200, 200, 80, 30)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["efficiency"], 1.0)

    def test_efficiency_precise_decimal(self):
        rows = [self._row("Victor", 1, 5, 333, 100, 80, 30)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["efficiency"], 3.33, places=2)

    def test_efficiency_large_damage_small_gold(self):
        rows = [self._row("Wendy", 1, 5, 1_000_000, 100, 80, 30)]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["efficiency"], 10000.0)

    # --- _player_stats: name edge cases ---

    def test_none_player_name_defaults_to_dash(self):
        rows = [{
            "player_name": None,
            "wave_number": "1", "enemies_defeated": "5",
            "damage_dealt": "300", "gold_spent": "100",
            "castle_hp": "80", "survival_time": "30",
        }]
        p = self.game._player_stats(rows)[0]
        self.assertEqual(p["name"], "-")

    def test_empty_string_player_name_defaults_to_dash(self):
        rows = [{
            "player_name": "",
            "wave_number": "1", "enemies_defeated": "0",
            "damage_dealt": "0", "gold_spent": "0",
            "castle_hp": "100", "survival_time": "30",
        }]
        p = self.game._player_stats(rows)[0]
        self.assertEqual(p["name"], "-")

    # --- _player_stats: multiple players extended ---

    def test_three_players_all_counted(self):
        rows = [
            self._row("A", 1, 5, 200, 100, 80, 30),
            self._row("B", 1, 8, 400, 150, 70, 25),
            self._row("C", 1, 3, 100, 80, 90, 20),
        ]
        result = self.game._player_stats(rows)
        self.assertEqual(len(result), 3)

    def test_five_players_all_counted(self):
        rows = [self._row(name, 1, 5, 200, 100, 80, 30) for name in ["A", "B", "C", "D", "E"]]
        result = self.game._player_stats(rows)
        self.assertEqual(len(result), 5)

    def test_result_count_matches_unique_player_names(self):
        rows = (
            [self._row("X", i, 5, 200, 100, 80, 30) for i in range(1, 4)] +
            [self._row("Y", i, 3, 150, 80, 75, 20) for i in range(1, 3)]
        )
        result = self.game._player_stats(rows)
        self.assertEqual(len(result), 2)

    # --- _player_stats: time ---

    def test_survival_time_is_summed(self):
        rows = [
            self._row("Zoe", 1, 0, 0, 0, 80, 30),
            self._row("Zoe", 2, 0, 0, 0, 60, 45),
            self._row("Zoe", 3, 0, 0, 0, 40, 55),
        ]
        p = self.game._player_stats(rows)[0]
        self.assertAlmostEqual(p["time"], 130)

    # --- _player_stats: wave 0 ---

    def test_wave_zero_is_valid(self):
        rows = [self._row("Aaron", 0, 0, 0, 0, 100, 10)]
        p = self.game._player_stats(rows)[0]
        self.assertEqual(p["wave"], 0)
