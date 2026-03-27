"""Configuration constants and static data for Neon Circuit."""

from __future__ import annotations

import pygame

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
ARENA_MARGIN = 48
GRID_SIZE = 8
DEFAULT_ROUND_SPEED = 22  # cells per second
TITLE = "Neon Circuit"
MAX_PLAYERS = 4
MIN_PLAYERS = 2

# Tron-like neon palette.
COLOR_PRESETS = [
    (0, 255, 255),   # Cyan
    (255, 64, 255),  # Magenta
    (255, 180, 0),   # Amber
    (0, 255, 120),   # Neon green
    (120, 190, 255), # Electric blue
    (255, 80, 120),  # Neon rose
]

SOUND_PRESETS = ["Classic Synth", "Deep Engine", "Arcade Buzz"]

PLAYER_CONTROL_PRESETS = [
    {"left": pygame.K_a, "right": pygame.K_d, "label": "A / D"},
    {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "label": "Left / Right"},
    {"left": pygame.K_j, "right": pygame.K_l, "label": "J / L"},
    {"left": pygame.K_KP4, "right": pygame.K_KP6, "label": "Numpad 4 / Numpad 6"},
]
