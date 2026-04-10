# Kingdom's Last Stand — Project Reference

## Game Type & Theme
Fantasy Medieval Tower Defense built with **Python + Pygame**.
The player defends a castle from waves of medieval enemies (goblins, orcs, dark knights)
by placing and upgrading towers along a predefined path.

## Tech Stack
- **Python** (core language)
- **Pygame** (game engine / rendering / event loop)
- **matplotlib** (end-of-session graphs)
- **pandas** (CSV data analysis)
- **csv** (built-in, data recording)

No external game engines. No SQLite or other databases.

---

## Class Hierarchy

```
Game
Tower  (base)
├── ArcherTower(Tower)   — fast, low dmg, long range  | dmg=25, range=150, spd=1.5
├── MageTower(Tower)     — slow, high dmg, med range  | dmg=60, range=120, spd=0.8
└── CannonTower(Tower)   — splash dmg, short range    | dmg=40, range=100, spd=0.5, splash=50
Enemy  (base)
├── Goblin(Enemy)        — fast, low HP
├── Orc(Enemy)           — medium HP/speed
└── DarkKnight(Enemy)    — slow, high HP
Wave
StatsTracker
UIManager
```

### Class Details

**Game**
- Attributes: `screen`, `clock`, `current_wave`, `gold`, `castle_hp`, `towers[]`, `enemies[]`
- Methods: `run()`, `update()`, `draw()`, `next_wave()`, `check_game_over()`

**Tower** (abstract base)
- Attributes: `level`, `damage`, `attack_range`, `attack_speed`, `position`, `cost`
- Methods: `find_target()`, `attack()`, `upgrade()`, `draw()`

**Enemy** (base — use inheritance for all enemy types)
- Attributes: `hp`, `max_hp`, `speed`, `reward_gold`, `path_index`, `position`
- Methods: `move()`, `take_damage()`, `is_dead()`, `draw()`
- No `enemy_type` attribute. No `if-else` branching on type inside base class.
- Each subclass defines its own `hp`, `speed`, `reward_gold`, and sprite directly.

**Goblin(Enemy)** — defines: `hp`, `speed`, `reward_gold`, sprite
**Orc(Enemy)** — defines: `hp`, `speed`, `reward_gold`, sprite
**DarkKnight(Enemy)** — defines: `hp`, `speed`, `reward_gold`, sprite

**Wave**
- Attributes: `wave_number`, `enemy_list[]`, `spawn_interval`, `spawn_timer`, `is_complete`
- Methods: `spawn_next()`, `update()`, `is_wave_complete()`

**StatsTracker**
- Attributes: `enemies_defeated`, `damage_dealt[]`, `gold_spent[]`, `towers_placed[]`, `survival_time`
- Methods: `record_kill()`, `record_damage()`, `record_gold_spent()`, `save_to_csv()`, `generate_report()`

**UIManager**
- Attributes: `font`, `hud_elements[]`, `tower_panel`, `stats_screen`
- Methods: `draw_hud()`, `draw_tower_panel()`, `draw_stats_screen()`

---

## Algorithms

1. **Pathfinding** — Waypoint-based path following (predefined (x,y) waypoints list per enemy)
2. **Collision Detection** — Euclidean distance radius check (tower range circle vs enemy position)
3. **Target Selection** — Priority = enemy with highest `path_index` (closest to castle)
4. **Wave Scaling** — Rule-based: HP, speed, quantity scale proportionally with wave number
5. **Event Loop** — Pygame event system for tower placement, selection, wave initiation

---

## Statistics Tracking (5 Features)

All data written to a single **`data/game_stats.csv`** — appended each session, never overwritten.

| Feature | Variable | Unit | Recorded When |
|---|---|---|---|
| Enemies Defeated per Wave | `enemies_defeated` | count (int) | End of each wave |
| Damage Dealt per Wave | `damage_dealt` | damage pts (int) | End of each wave |
| Gold Spent per Wave | `gold_spent` | gold (int) | End of each wave |
| Castle HP Remaining per Wave | `castle_hp` | HP (int) | End of each wave |
| Wave Survival Time | `survival_time` | seconds (float) | Wave start → end |

### CSV Schema

```
session_id, wave_number, enemies_defeated, damage_dealt, gold_spent, castle_hp, survival_time
```

Each row = one wave in one session. `session_id` identifies the playthrough.

### Visualizations (end-of-session screen)

- **Graph 1** — Enemies Defeated per Wave → Histogram (distribution)
- **Graph 2** — Castle HP Remaining per Wave → Line graph (time-series)
- **Graph 3** — Gold Spent per Wave → Bar graph (proportion)
- Summary stats table: Mean, Min, Max, Std Dev for all 5 features

---

## Key Design Rules (from instructor feedback)

- Use **inheritance** for both Tower types AND Enemy types — reduces repeated hp/speed/sprite setup
- Do **NOT** separate data analysis into a different file — keep it integrated (StatsTracker + UIManager)
- Study **inheritance vs composition** for special tower behaviors and choose the appropriate pattern
- Make the project **stand out** from other tower defense submissions

## Standout Features

**Boss Wave System**
Every 5th wave (wave 5, 10, 15, …) spawns a `BossEnemy(Enemy)` subclass alongside the normal wave.

`BossEnemy` defines directly (no `enemy_type` branching):
- `hp` = base enemy hp × 5
- `speed` = base enemy speed × 0.5
- `reward_gold` = base reward × 10
- `size` = 2× normal enemy size
- Renders its own health bar above the sprite

---

## Project Structure

```
kingdom_last_stand game/
├── main.py                  # Entry point
├── requirements.txt
├── CLAUDE.md
├── data/
│   └── game_stats.csv       # Cumulative stats across all sessions
├── assets/
│   ├── images/
│   │   ├── towers/
│   │   │   ├── archer/
│   │   │   ├── mage/
│   │   │   └── cannon/
│   │   ├── enemies/
│   │   │   ├── goblin/
│   │   │   ├── orc/
│   │   │   └── dark_knight/
│   │   ├── map/
│   │   └── ui/
│   └── sounds/
└── src/
    ├── game.py
    ├── wave.py
    ├── stats_tracker.py
    ├── ui_manager.py
    ├── towers/
    │   ├── tower.py         # Base Tower class
    │   ├── archer_tower.py
    │   ├── mage_tower.py
    │   └── cannon_tower.py
    └── enemies/
        ├── enemy.py         # Base Enemy class
        ├── goblin.py
        ├── orc.py
        └── dark_knight.py
```

---

## Timeline

| Week | Task |
|---|---|
| 9 | Game architecture + OOP class setup |
| 10 | Core mechanics (tower placement, enemy pathing, wave system) |
| 11 | Tower types, enemy types, upgrade system + UI/HUD |
| 12 | StatsTracker + CSV recording |
| 13 | Data visualization + bug fixing + polish |
| 14 | Submission (draft) |
