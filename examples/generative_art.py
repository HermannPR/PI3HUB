#!/usr/bin/env python3
"""Fullscreen generative Perlin noise art using pygame."""
import pygame
import math
import random

try:
    from perlin_noise import PerlinNoise
    noise = PerlinNoise(octaves=4, seed=random.randint(0, 9999))
    USE_PERLIN = True
except ImportError:
    USE_PERLIN = False


def get_noise(x, y, scale=0.005):
    if USE_PERLIN:
        return noise([x * scale, y * scale])
    return math.sin(x * scale * 10) * math.cos(y * scale * 10) * 0.5


pygame.init()
info = pygame.display.Info()
W, H = info.current_w, info.current_h
screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
pygame.display.set_caption("Generative Art")
clock = pygame.time.Clock()

surface = pygame.Surface((W, H))
t = 0

print("Fullscreen generative art. Press Q or Esc to quit.")
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False

    surface.fill((0, 0, 0))
    for y in range(0, H, 4):
        for x in range(0, W, 4):
            n = get_noise(x + t * 50, y + t * 30)
            r = int((math.sin(n * math.pi * 2 + t) * 0.5 + 0.5) * 255)
            g = int((math.sin(n * math.pi * 2 + t + 2) * 0.5 + 0.5) * 200)
            b = int((math.cos(n * math.pi * 2 - t) * 0.5 + 0.5) * 255)
            pygame.draw.rect(surface, (r, g, b), (x, y, 4, 4))

    screen.blit(surface, (0, 0))
    pygame.display.flip()
    t += 0.005
    clock.tick(30)

pygame.quit()
