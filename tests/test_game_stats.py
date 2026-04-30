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
