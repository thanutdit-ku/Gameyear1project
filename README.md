# Kingdom's Last Stand

<p align="center">
  <img src="https://img.shields.io/badge/PYTHON-3.13-4B8BBE?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13" />
  <img src="https://img.shields.io/badge/PYGAME-2.6+-2E8B57?style=for-the-badge&logo=pygame&logoColor=white" alt="Pygame" />
</p>

<p align="center">
  <b>A fantasy tower defense game built with Python and Pygame.</b><br/>
  Defend the castle, place towers with limited gold, survive escalating waves, and review polished end-of-session battle stats.
</p>

## Overview

Kingdom's Last Stand is a wave-based defense game with a custom-rendered fantasy UI, multiple tower roles, mixed enemy types, and a cinematic home screen. The project focuses on gameplay clarity, strong visual presentation, and lightweight data tracking through CSV and chart summaries.

## Features

- Stylish home screen and in-game UI
- Three tower types with different roles
- Multiple enemy types with wave-based scaling
- Boss waves every 5th wave
- CSV stat tracking per wave
- End-of-session charts using Matplotlib

## Gameplay

You begin with gold and must place towers on the battlefield without blocking the enemy path. Each wave increases pressure through stronger enemies and mixed enemy compositions. If too many enemies reach the castle, the game ends.

### Towers

- `Archer`: fast attacks with a critical-hit chance
- `Mage`: high damage plus a slow effect
- `Cannon`: splash damage in an area

### Enemies

- `Goblin`: basic fast enemy
- `Bat`: very fast low-health flier that starts appearing in wave 2
- `SwordShield`: tougher goblin variant using a sprite sheet animation
- `Orc`: slower and tankier
- `DarkKnight`: late-wave elite enemy
- `BossEnemy`: appears every 5th wave

## Controls

- `Mouse Left Click`: select a tower or place it on the map
- `ESC`: clear selected tower
- `Enter` or `Space`: start from the home page
- `Q`: quit from the end screen or home page

## Requirements

- Python 3.10+
- `pygame`
- `matplotlib`
- `pandas`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python3 main.py
```

## Running Tests

The test suite covers `StatsTracker` and the game's statistics logic (`_player_stats`, `_to_number`). No display or Pygame window is required.

```bash
python -m unittest discover -s tests -v
```

Expected output:

```
Ran 45 tests in 0.010s

OK
```

### Test files

| File | What it tests |
|------|--------------|
| `tests/test_stats_tracker.py` | Recording kills/damage/gold, CSV writes, history, `generate_report` |
| `tests/test_game_stats.py` | Player stat aggregation, efficiency calculation, edge cases |

## Project Structure

```text
Game_project_year1/
├── assets/
│   └── images/
├── data/
│   └── game_stats.csv
├── src/
│   ├── enemies/
│   ├── towers/
│   ├── game.py
│   ├── stats_tracker.py
│   ├── ui_manager.py
│   └── wave.py
├── tests/
│   ├── test_stats_tracker.py
│   └── test_game_stats.py
├── main.py
├── requirements.txt
├── LICENSE
└── README.md
```

## Stats Output

Wave results are saved to:

`data/game_stats.csv`

Tracked values include:

- player name
- enemies defeated
- damage dealt
- gold spent
- castle HP
- survival time

## Notes

- Wave 1 alternates between `Goblin` and `SwordShield`
- `Bat` joins the enemy pool starting in wave 2
- Enemy stats scale up as waves increase
- The battlefield and UI are drawn with custom Pygame rendering

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE).
