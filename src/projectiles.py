import pygame


class Projectile:
    def __init__(self, origin, target, speed, damage):
        self.position   = pygame.Vector2(origin)
        self.target     = target
        self.target_pos = pygame.Vector2(target.position)
        self.speed      = speed
        self.damage     = damage
        self.done       = False
        self._direction = pygame.Vector2(1, 0)

    def update(self, dt, enemies):
        if self.target and not self.target.is_dead():
            self.target_pos = pygame.Vector2(self.target.position)

        diff = self.target_pos - self.position
        dist = diff.length()

        if dist < self.speed * dt + 6:
            self._hit(enemies)
            self.done = True
            return

        self._direction = diff.normalize()
        self.position  += self._direction * self.speed * dt

    def _hit(self, enemies):
        if self.target and not self.target.is_dead():
            self.target.take_damage(self.damage)

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255),
                           (int(self.position.x), int(self.position.y)), 3)


# ── Arrow ──────────────────────────────────────────────────────────────────

class Arrow(Projectile):
    _COLOR_HEAD  = (230, 200, 110)
    _COLOR_SHAFT = (185, 148,  72)

    def __init__(self, origin, target, damage):
        super().__init__(origin, target, speed=400, damage=damage)

    def draw(self, screen):
        head = self.position
        tail = head - self._direction * 11
        pygame.draw.line(screen, self._COLOR_SHAFT,
                         (int(tail.x), int(tail.y)),
                         (int(head.x), int(head.y)), 2)
        pygame.draw.circle(screen, self._COLOR_HEAD,
                           (int(head.x), int(head.y)), 2)


# ── Magic Orb ──────────────────────────────────────────────────────────────

class MagicOrb(Projectile):
    _COLOR_CORE  = (210, 100, 255)
    _COLOR_GLOW  = (130,  50, 210, 70)
    _SLOW_FACTOR   = 0.5
    _SLOW_DURATION = 2.0

    def __init__(self, origin, target, damage):
        super().__init__(origin, target, speed=250, damage=damage)

    def _hit(self, enemies):
        if self.target and not self.target.is_dead():
            self.target.take_damage(self.damage)
            self._apply_slow(self.target)

    @staticmethod
    def _apply_slow(enemy):
        if not hasattr(enemy, "base_speed"):
            enemy.base_speed = enemy.speed
        enemy.speed      = enemy.base_speed * MagicOrb._SLOW_FACTOR
        enemy.slow_timer = MagicOrb._SLOW_DURATION

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        glow = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(glow, self._COLOR_GLOW, (11, 11), 10)
        screen.blit(glow, (x - 11, y - 11))
        pygame.draw.circle(screen, self._COLOR_CORE, (x, y), 5)
        pygame.draw.circle(screen, (240, 190, 255), (x - 1, y - 1), 2)


# ── Cannonball ─────────────────────────────────────────────────────────────

class Cannonball(Projectile):
    SPLASH_RADIUS = 50
    _COLOR         = (42,  44,  55)
    _COLOR_OUTLINE = (82,  86, 102)

    def __init__(self, origin, target, damage):
        super().__init__(origin, target, speed=210, damage=damage)

    def _hit(self, enemies):
        for enemy in enemies:
            if self.target_pos.distance_to(enemy.position) <= self.SPLASH_RADIUS:
                enemy.take_damage(self.damage)

    def draw(self, screen):
        x, y = int(self.position.x), int(self.position.y)
        pygame.draw.circle(screen, self._COLOR,        (x, y), 5)
        pygame.draw.circle(screen, self._COLOR_OUTLINE,(x, y), 5, 1)
        pygame.draw.circle(screen, (105, 110, 128),    (x - 1, y - 1), 2)
