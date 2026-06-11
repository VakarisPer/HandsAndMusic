import math
import random

import pygame


class Particle:
    def __init__(self, x, y, color, speed_min, speed_max,
                 size_min, size_max, lifetime):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(speed_min, speed_max)
        self.x = float(x)
        self.y = float(y)
        self.velocity_x = math.cos(angle) * speed
        self.velocity_y = math.sin(angle) * speed
        self.size = random.uniform(size_min, size_max)
        self.lifetime_remaining = random.uniform(lifetime * 0.5, lifetime)
        self.total_lifetime = self.lifetime_remaining
        self.color = color

    def update(self, delta_time):
        self.x += self.velocity_x * delta_time
        self.y += self.velocity_y * delta_time
        self.velocity_y += 180 * delta_time
        self.lifetime_remaining -= delta_time

    @property
    def is_alive(self):
        return self.lifetime_remaining > 0

    def draw(self, screen):
        progress = max(0.0, self.lifetime_remaining / self.total_lifetime)
        alpha = int(255 * progress)
        radius = int(self.size * progress)
        if radius <= 0:
            return
        r, g, b = self.color
        surface = pygame.Surface((radius * 2 + 2, radius * 2 + 2),
                                 pygame.SRCALPHA)
        pygame.draw.circle(
            surface, (r, g, b, alpha), (radius + 1, radius + 1), radius,
        )
        screen.blit(surface, (int(self.x - radius), int(self.y - radius)))


class ParticleSystem:
    def __init__(self):
        self._particles = []

    def emit(self, x, y, color, count=10, speed_min=40, speed_max=180,
             size_min=1.5, size_max=5, lifetime=0.8):
        for _ in range(count):
            self._particles.append(
                Particle(x, y, color, speed_min, speed_max,
                         size_min, size_max, lifetime),
            )

    def update_and_draw(self, screen, delta_time):
        alive = []
        for particle in self._particles:
            particle.update(delta_time)
            if particle.is_alive:
                particle.draw(screen)
                alive.append(particle)
        self._particles = alive

    def clear(self):
        self._particles.clear()
