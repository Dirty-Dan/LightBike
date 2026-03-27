"""Gameplay simulation for the Neon Circuit arena."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .config import ARENA_MARGIN, DEFAULT_ROUND_SPEED, GRID_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH

Vec2 = Tuple[int, int]

DIR_UP: Vec2 = (0, -1)
DIR_DOWN: Vec2 = (0, 1)
DIR_LEFT: Vec2 = (-1, 0)
DIR_RIGHT: Vec2 = (1, 0)

TURN_LEFT = {
    DIR_UP: DIR_LEFT,
    DIR_LEFT: DIR_DOWN,
    DIR_DOWN: DIR_RIGHT,
    DIR_RIGHT: DIR_UP,
}

TURN_RIGHT = {
    DIR_UP: DIR_RIGHT,
    DIR_RIGHT: DIR_DOWN,
    DIR_DOWN: DIR_LEFT,
    DIR_LEFT: DIR_UP,
}


@dataclass
class PlayerConfig:
    index: int
    color: Tuple[int, int, int]
    sound_profile: str
    controls: Dict[str, int]


@dataclass
class BikeState:
    config: PlayerConfig
    pos: Vec2
    direction: Vec2
    alive: bool = True
    pending_turn: int = 0
    trail: List[Vec2] = field(default_factory=list)


@dataclass
class RoundResult:
    winner: Optional[int]
    message: str


class ArenaRound:
    """Grid-based Tron round simulation."""

    def __init__(self, player_configs: List[PlayerConfig], speed_cells: int = DEFAULT_ROUND_SPEED) -> None:
        self.player_configs = player_configs
        self.speed_cells = speed_cells
        self.time_acc = 0.0
        self.grid_left = ARENA_MARGIN // GRID_SIZE
        self.grid_top = ARENA_MARGIN // GRID_SIZE
        self.grid_right = (SCREEN_WIDTH - ARENA_MARGIN) // GRID_SIZE
        self.grid_bottom = (SCREEN_HEIGHT - ARENA_MARGIN) // GRID_SIZE
        self.occupied: Set[Vec2] = set()
        self.bikes = self._spawn_bikes()
        for bike in self.bikes:
            self.occupied.add(bike.pos)
            bike.trail.append(bike.pos)
        self.result: Optional[RoundResult] = None

    def _spawn_bikes(self) -> List[BikeState]:
        w = self.grid_right - self.grid_left
        h = self.grid_bottom - self.grid_top
        positions = [
            (self.grid_left + w // 4, self.grid_top + h // 2),
            (self.grid_left + (3 * w) // 4, self.grid_top + h // 2),
            (self.grid_left + w // 2, self.grid_top + h // 4),
            (self.grid_left + w // 2, self.grid_top + (3 * h) // 4),
        ]
        dirs = [DIR_RIGHT, DIR_LEFT, DIR_DOWN, DIR_UP]

        bikes: List[BikeState] = []
        for cfg in self.player_configs:
            bikes.append(BikeState(config=cfg, pos=positions[cfg.index], direction=dirs[cfg.index]))
        return bikes

    def queue_turn(self, player_index: int, direction: int) -> None:
        for bike in self.bikes:
            if bike.config.index == player_index and bike.alive:
                bike.pending_turn = direction
                break

    def update(self, dt: float) -> Optional[RoundResult]:
        if self.result:
            return self.result

        self.time_acc += dt
        step_time = 1.0 / self.speed_cells

        while self.time_acc >= step_time and not self.result:
            self.time_acc -= step_time
            self._step_once()

        return self.result

    def _step_once(self) -> None:
        alive = [b for b in self.bikes if b.alive]
        if len(alive) <= 1:
            self._finalize_result()
            return

        planned: Dict[int, Vec2] = {}
        for bike in alive:
            if bike.pending_turn == -1:
                bike.direction = TURN_LEFT[bike.direction]
            elif bike.pending_turn == 1:
                bike.direction = TURN_RIGHT[bike.direction]
            bike.pending_turn = 0
            planned[bike.config.index] = (bike.pos[0] + bike.direction[0], bike.pos[1] + bike.direction[1])

        collisions: Set[int] = set()
        cell_claims: Dict[Vec2, List[int]] = {}

        for player_idx, new_pos in planned.items():
            cell_claims.setdefault(new_pos, []).append(player_idx)

        for cell, claimers in cell_claims.items():
            if len(claimers) > 1:
                collisions.update(claimers)

        for bike in alive:
            new_pos = planned[bike.config.index]
            if self._out_of_bounds(new_pos) or new_pos in self.occupied:
                collisions.add(bike.config.index)

        for bike in alive:
            if bike.config.index in collisions:
                bike.alive = False
                continue
            bike.pos = planned[bike.config.index]
            bike.trail.append(bike.pos)
            self.occupied.add(bike.pos)

        self._finalize_result()

    def _out_of_bounds(self, pos: Vec2) -> bool:
        return pos[0] < self.grid_left or pos[0] > self.grid_right or pos[1] < self.grid_top or pos[1] > self.grid_bottom

    def _finalize_result(self) -> None:
        survivors = [bike for bike in self.bikes if bike.alive]
        if len(survivors) == 1:
            winner = survivors[0].config.index
            self.result = RoundResult(winner=winner, message=f"Player {winner + 1} wins the round!")
        elif len(survivors) == 0:
            self.result = RoundResult(winner=None, message="Crash chaos! Round is a draw.")
