import random
from src.enemies.goblin import Goblin
from src.enemies.swordshield import SwordShield
from src.enemies.orc import Orc
from src.enemies.dark_knight import DarkKnight
from src.enemies.boss_enemy import BossEnemy


class Wave:
    SPAWN_INTERVAL = 1.5  # seconds between each enemy spawn

    def __init__(self, wave_number, waypoints):
        self.wave_number = wave_number
        self.waypoints = waypoints
        self.spawn_interval = self.SPAWN_INTERVAL
        self.spawn_timer = 0
        self.is_complete = False

        self.enemy_queue = self._build_queue()

    # ------------------------------------------------------------------
    # Queue building
    # ------------------------------------------------------------------

    def _build_queue(self):
        """Build the ordered list of enemies to spawn this wave."""
        quantity = 5 + (self.wave_number - 1) * 2
        hp_mult = 1.20 ** (self.wave_number - 1)
        spd_mult = 1.10 ** (self.wave_number - 1)

        queue = []
        for index in range(quantity):
            enemy = self._pick_enemy_type(index)
            self._apply_scaling(enemy, hp_mult, spd_mult)
            enemy.set_spawn_offset(index * enemy.spawn_spacing)
            queue.append(enemy)

        # Every 5th wave: insert a boss at the end of the queue
        if self.wave_number % 5 == 0:
            boss = BossEnemy(self.waypoints)
            self._apply_scaling(boss, hp_mult, spd_mult)
            boss.set_spawn_offset(len(queue) * boss.spawn_spacing)
            queue.append(boss)

        return queue

    def _pick_enemy_type(self, index=0):
        """Return a new enemy instance based on wave progression."""
        if self.wave_number == 1:
            # First wave: alternate the two goblin variants for variety.
            choices = [Goblin, SwordShield]
            return choices[index % 2](self.waypoints)
        if self.wave_number <= 3:
            # Early waves: goblins and shield goblins
            choices = [Goblin, SwordShield]
            weights = [3, 2]
        elif self.wave_number <= 6:
            # Mid waves: goblins, shield goblins, and orcs
            choices = [Goblin, SwordShield, Orc]
            weights = [3, 2, 1]
        else:
            # Late waves: full enemy roster
            choices = [Goblin, SwordShield, Orc, DarkKnight]
            weights = [3, 2, 2, 1]

        enemy_class = random.choices(choices, weights=weights)[0]
        return enemy_class(self.waypoints)

    def _apply_scaling(self, enemy, hp_mult, spd_mult):
        """Scale an enemy's hp and speed in place."""
        enemy.hp = int(enemy.hp * hp_mult)
        enemy.max_hp = enemy.hp
        enemy.speed = round(enemy.speed * spd_mult, 3)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def spawn_next(self):
        """Pop and return the next enemy from the queue, or None if empty."""
        if self.enemy_queue:
            return self.enemy_queue.pop(0)
        return None

    def update(self, dt):
        """Tick the spawn timer. Returns a new enemy when it is time to spawn, else None."""
        if not self.enemy_queue:
            return None

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = self.spawn_interval
            return self.spawn_next()

        return None

    def is_wave_complete(self):
        """True when all enemies have been spawned from the queue."""
        return len(self.enemy_queue) == 0
