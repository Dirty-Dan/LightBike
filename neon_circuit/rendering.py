"""Rendering helpers for Neon Circuit UI and arena."""

from __future__ import annotations

from typing import Iterable, Tuple

import pygame

from .config import ARENA_MARGIN, GRID_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.title_font = pygame.font.SysFont("consolas", 72, bold=True)
        self.header_font = pygame.font.SysFont("consolas", 38, bold=True)
        self.text_font = pygame.font.SysFont("consolas", 28)
        self.small_font = pygame.font.SysFont("consolas", 22)

    def clear(self) -> None:
        self.screen.fill((5, 5, 12))

    def draw_grid(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for x in range(ARENA_MARGIN, SCREEN_WIDTH - ARENA_MARGIN, GRID_SIZE * 4):
            pygame.draw.line(overlay, (0, 120, 255, 35), (x, ARENA_MARGIN), (x, SCREEN_HEIGHT - ARENA_MARGIN), 1)
        for y in range(ARENA_MARGIN, SCREEN_HEIGHT - ARENA_MARGIN, GRID_SIZE * 4):
            pygame.draw.line(overlay, (255, 0, 160, 25), (ARENA_MARGIN, y), (SCREEN_WIDTH - ARENA_MARGIN, y), 1)
        pygame.draw.rect(
            overlay,
            (0, 220, 255, 180),
            (ARENA_MARGIN, ARENA_MARGIN, SCREEN_WIDTH - 2 * ARENA_MARGIN, SCREEN_HEIGHT - 2 * ARENA_MARGIN),
            2,
        )
        self.screen.blit(overlay, (0, 0))

    def draw_glow_line(self, color: Tuple[int, int, int], start: Tuple[int, int], end: Tuple[int, int]) -> None:
        glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(glow, (*color, 70), start, end, 8)
        pygame.draw.line(glow, (*color, 160), start, end, 4)
        self.screen.blit(glow, (0, 0))
        pygame.draw.line(self.screen, color, start, end, 2)

    def draw_glow_dot(self, color: Tuple[int, int, int], center: Tuple[int, int], radius: int) -> None:
        glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, 70), center, radius + 6)
        pygame.draw.circle(glow, (*color, 180), center, radius + 2)
        self.screen.blit(glow, (0, 0))
        pygame.draw.circle(self.screen, color, center, radius)

    def draw_title_screen(self) -> None:
        self.clear()
        self.draw_grid()
        title = self.title_font.render("NEON CIRCUIT", True, (0, 255, 255))
        subtitle = self.text_font.render("Retro local multiplayer light-bike combat", True, (255, 80, 200))
        hint = self.small_font.render("Press ENTER to start setup | ESC to quit", True, (220, 220, 220))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 180))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 280))
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 510))

    def draw_text(self, text: str, y: int, color: Tuple[int, int, int] = (220, 220, 230), centered: bool = True) -> None:
        surf = self.text_font.render(text, True, color)
        x = SCREEN_WIDTH // 2 - surf.get_width() // 2 if centered else 60
        self.screen.blit(surf, (x, y))

    def draw_setup_row(
        self,
        y: int,
        player_label: str,
        color_name: str,
        sound_name: str,
        controls_label: str,
        swatch_color: Tuple[int, int, int],
        selected: bool,
    ) -> None:
        border = (0, 255, 255) if selected else (80, 100, 120)
        rect = pygame.Rect(120, y, SCREEN_WIDTH - 240, 52)
        pygame.draw.rect(self.screen, (18, 20, 36), rect)
        pygame.draw.rect(self.screen, border, rect, 2)
        label = self.small_font.render(player_label, True, (220, 220, 255))
        details = self.small_font.render(f"Color: {color_name} | Sound: {sound_name} | Turn: {controls_label}", True, (200, 200, 210))
        self.screen.blit(label, (140, y + 5))
        self.screen.blit(details, (270, y + 16))
        pygame.draw.rect(self.screen, swatch_color, (220, y + 14, 28, 24))

    def draw_round_overlay(self, text: str) -> None:
        banner = pygame.Surface((SCREEN_WIDTH, 74), pygame.SRCALPHA)
        banner.fill((0, 0, 0, 160))
        self.screen.blit(banner, (0, 0))
        surf = self.text_font.render(text, True, (255, 255, 255))
        self.screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, 20))

    def draw_scores(self, rows: Iterable[str]) -> None:
        rows_list = list(rows)
        panel = pygame.Surface((260, 32 + len(rows_list) * 24), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 120))
        self.screen.blit(panel, (14, 14))
        y = 22
        for row in rows_list:
            text = self.small_font.render(row, True, (220, 220, 220))
            self.screen.blit(text, (26, y))
            y += 22
