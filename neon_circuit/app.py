"""Main application state machine for Neon Circuit."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List

import pygame

from .audio import AudioManager
from .config import (
    COLOR_PRESETS,
    FPS,
    MAX_PLAYERS,
    MIN_PLAYERS,
    PLAYER_CONTROL_PRESETS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SOUND_PRESETS,
    TITLE,
    GRID_SIZE,
)
from .gameplay import ArenaRound, PlayerConfig
from .rendering import Renderer


class GameState(Enum):
    TITLE = auto()
    SETUP = auto()
    PLAYING = auto()
    ROUND_OVER = auto()


COLOR_NAMES = {
    (0, 255, 255): "Cyan",
    (255, 64, 255): "Magenta",
    (255, 180, 0): "Amber",
    (0, 255, 120): "Green",
    (120, 190, 255): "Blue",
    (255, 80, 120): "Rose",
}


@dataclass
class PlayerSetup:
    color_idx: int
    sound_idx: int


class NeonCircuitApp:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
        self.audio = AudioManager()

        self.state = GameState.TITLE
        self.running = True
        self.player_count = 2
        self.selected_setup_row = 0
        self.players_setup = [PlayerSetup(i % len(COLOR_PRESETS), i % len(SOUND_PRESETS)) for i in range(MAX_PLAYERS)]

        self.scores: Dict[int, int] = {i: 0 for i in range(MAX_PLAYERS)}
        self.round: ArenaRound | None = None
        self.round_result_text = ""

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._render()
            pygame.display.flip()

        self.audio.stop_all_hums()
        pygame.quit()

    def _active_configs(self) -> List[PlayerConfig]:
        configs: List[PlayerConfig] = []
        for i in range(self.player_count):
            setup = self.players_setup[i]
            configs.append(
                PlayerConfig(
                    index=i,
                    color=COLOR_PRESETS[setup.color_idx],
                    sound_profile=SOUND_PRESETS[setup.sound_idx],
                    controls=PLAYER_CONTROL_PRESETS[i],
                )
            )
        return configs

    def _start_round(self) -> None:
        self.round = ArenaRound(self._active_configs())
        self.round_result_text = ""
        self.audio.stop_all_hums()
        for bike in self.round.bikes:
            self.audio.start_bike_hum(bike.config.index, bike.config.sound_profile)
        self.state = GameState.PLAYING

    def _return_to_menu(self) -> None:
        self.audio.stop_all_hums()
        self.state = GameState.TITLE

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._on_keydown(event.key)

    def _on_keydown(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            if self.state == GameState.PLAYING:
                self.state = GameState.ROUND_OVER
                self.round_result_text = "Paused"
                self.audio.stop_all_hums()
            else:
                self.running = False
            return

        if self.state == GameState.TITLE:
            if key == pygame.K_RETURN:
                self.audio.menu_select()
                self.state = GameState.SETUP
            return

        if self.state == GameState.SETUP:
            self._handle_setup_input(key)
            return

        if self.state == GameState.PLAYING:
            self._handle_turn_input(key)
            return

        if self.state == GameState.ROUND_OVER:
            if key == pygame.K_r:
                self.audio.menu_select()
                self._start_round()
            elif key == pygame.K_m:
                self.audio.menu_select()
                self._return_to_menu()

    def _handle_setup_input(self, key: int) -> None:
        row_max = self.player_count - 1
        if key == pygame.K_UP:
            self.selected_setup_row = max(0, self.selected_setup_row - 1)
            self.audio.menu_move()
        elif key == pygame.K_DOWN:
            self.selected_setup_row = min(row_max, self.selected_setup_row + 1)
            self.audio.menu_move()
        elif key == pygame.K_LEFT:
            row = self.players_setup[self.selected_setup_row]
            row.color_idx = (row.color_idx - 1) % len(COLOR_PRESETS)
            self.audio.menu_move()
        elif key == pygame.K_RIGHT:
            row = self.players_setup[self.selected_setup_row]
            row.color_idx = (row.color_idx + 1) % len(COLOR_PRESETS)
            self.audio.menu_move()
        elif key == pygame.K_q:
            row = self.players_setup[self.selected_setup_row]
            row.sound_idx = (row.sound_idx - 1) % len(SOUND_PRESETS)
            self.audio.menu_move()
        elif key == pygame.K_e:
            row = self.players_setup[self.selected_setup_row]
            row.sound_idx = (row.sound_idx + 1) % len(SOUND_PRESETS)
            self.audio.menu_move()
        elif key == pygame.K_LEFTBRACKET:
            self.player_count = max(MIN_PLAYERS, self.player_count - 1)
            self.selected_setup_row = min(self.selected_setup_row, self.player_count - 1)
            self.audio.menu_move()
        elif key == pygame.K_RIGHTBRACKET:
            self.player_count = min(MAX_PLAYERS, self.player_count + 1)
            self.audio.menu_move()
        elif key == pygame.K_RETURN:
            self.audio.menu_select()
            self._start_round()

    def _handle_turn_input(self, key: int) -> None:
        if not self.round:
            return

        for cfg in self.round.player_configs:
            if key == cfg.controls["left"]:
                self.round.queue_turn(cfg.index, -1)
                return
            if key == cfg.controls["right"]:
                self.round.queue_turn(cfg.index, 1)
                return

    def _update(self, dt: float) -> None:
        if self.state != GameState.PLAYING or not self.round:
            return

        result = self.round.update(dt)
        alive_indices = {bike.config.index for bike in self.round.bikes if bike.alive}
        for bike in self.round.bikes:
            if bike.config.index not in alive_indices:
                self.audio.stop_bike_hum(bike.config.index)

        if result:
            self.round_result_text = result.message
            self.state = GameState.ROUND_OVER
            self.audio.stop_all_hums()
            self.audio.play_sfx("crash")
            if result.winner is not None:
                self.scores[result.winner] += 1
                self.audio.play_sfx("win")

    def _render(self) -> None:
        if self.state == GameState.TITLE:
            self.renderer.draw_title_screen()
            return

        if self.state == GameState.SETUP:
            self._render_setup()
            return

        if self.state in (GameState.PLAYING, GameState.ROUND_OVER):
            self._render_arena()
            if self.state == GameState.ROUND_OVER:
                self._render_round_over()

    def _render_setup(self) -> None:
        self.renderer.clear()
        self.renderer.draw_grid()
        header = self.renderer.header_font.render("LOCAL MULTIPLAYER SETUP", True, (0, 255, 255))
        self.screen.blit(header, (SCREEN_WIDTH // 2 - header.get_width() // 2, 50))
        self.renderer.draw_text("UP/DOWN select player | LEFT/RIGHT color | Q/E sound", y=110)
        self.renderer.draw_text("[ and ] change player count (2-4) | ENTER start", y=145)

        y = 220
        for i in range(self.player_count):
            setup = self.players_setup[i]
            color = COLOR_PRESETS[setup.color_idx]
            sound_name = SOUND_PRESETS[setup.sound_idx]
            color_name = COLOR_NAMES.get(color, "Custom")
            controls_label = PLAYER_CONTROL_PRESETS[i]["label"]
            self.renderer.draw_setup_row(
                y=y,
                player_label=f"Player {i + 1}",
                color_name=color_name,
                sound_name=sound_name,
                controls_label=controls_label,
                swatch_color=color,
                selected=(self.selected_setup_row == i),
            )
            y += 66

    def _render_arena(self) -> None:
        if not self.round:
            return
        self.renderer.clear()
        self.renderer.draw_grid()

        for bike in self.round.bikes:
            trail_pixels = [
                (cell[0] * GRID_SIZE + GRID_SIZE // 2, cell[1] * GRID_SIZE + GRID_SIZE // 2)
                for cell in bike.trail
            ]
            if len(trail_pixels) > 1:
                for i in range(1, len(trail_pixels)):
                    self.renderer.draw_glow_line(bike.config.color, trail_pixels[i - 1], trail_pixels[i])
            head_color = bike.config.color if bike.alive else (120, 120, 120)
            head_pos = (bike.pos[0] * GRID_SIZE + GRID_SIZE // 2, bike.pos[1] * GRID_SIZE + GRID_SIZE // 2)
            self.renderer.draw_glow_dot(head_color, head_pos, 5)

        status = "Controls: P1 A/D | P2 ←/→ | P3 J/L | P4 Num4/Num6"
        self.renderer.draw_round_overlay(status)
        score_rows = [f"P{i + 1}: {self.scores[i]}" for i in range(self.player_count)]
        self.renderer.draw_scores(score_rows)

    def _render_round_over(self) -> None:
        panel = pygame.Surface((760, 200), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        self.screen.blit(panel, (SCREEN_WIDTH // 2 - 380, SCREEN_HEIGHT // 2 - 100))
        title = self.renderer.header_font.render(self.round_result_text, True, (255, 255, 255))
        prompt = self.renderer.text_font.render("Press R to replay | M for menu | ESC to quit", True, (220, 220, 220))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 42))
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, SCREEN_HEIGHT // 2 + 26))


def main() -> None:
    NeonCircuitApp().run()


if __name__ == "__main__":
    main()
