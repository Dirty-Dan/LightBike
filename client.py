"""Online multiplayer client for Neon Circuit."""

from __future__ import annotations

import argparse
import json
import socket
from typing import Any, Optional

import pygame

from neon_circuit.config import GRID_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 25565


def send_json(sock: socket.socket, payload: dict[str, Any]) -> None:
    sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))


class SocketReader:
    def __init__(self) -> None:
        self.buffer = b""

    def recv_json(self, sock: socket.socket) -> Optional[dict[str, Any]]:
        try:
            chunk = sock.recv(4096)
        except BlockingIOError:
            return None
        if not chunk:
            raise ConnectionError("Server disconnected")
        self.buffer += chunk
        if b"\n" not in self.buffer:
            return None
        line, self.buffer = self.buffer.split(b"\n", 1)
        return json.loads(line.decode("utf-8"))


def draw_text(screen: pygame.Surface, font: pygame.font.Font, txt: str, x: int, y: int, color=(220, 220, 220)) -> None:
    surf = font.render(txt, True, color)
    screen.blit(surf, (x, y))


def cell_to_px(cell: list[int]) -> tuple[int, int]:
    return (cell[0] * GRID_SIZE + GRID_SIZE // 2, cell[1] * GRID_SIZE + GRID_SIZE // 2)


def run_client(host: str, port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.setblocking(False)

    reader = SocketReader()
    my_index: Optional[int] = None
    state: dict[str, Any] = {"mode": "lobby", "players": [], "scores": {}, "message": "Connecting..."}

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Neon Circuit Online")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("consolas", 34)
    text_font = pygame.font.SysFont("consolas", 22)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    send_json(sock, {"action": "turn", "dir": -1})
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    send_json(sock, {"action": "turn", "dir": 1})
                elif event.key == pygame.K_s:
                    send_json(sock, {"action": "start"})

        while True:
            try:
                msg = reader.recv_json(sock)
            except ConnectionError:
                state["message"] = "Disconnected from server"
                running = False
                break

            if msg is None:
                break
            if msg.get("type") == "welcome":
                my_index = int(msg["player_index"])
            elif msg.get("type") == "state":
                state = msg

        screen.fill((7, 7, 18))

        # Grid
        for x in range(0, SCREEN_WIDTH, GRID_SIZE * 2):
            pygame.draw.line(screen, (20, 20, 42), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE * 2):
            pygame.draw.line(screen, (20, 20, 42), (0, y), (SCREEN_WIDTH, y))

        draw_text(screen, title_font, "NEON CIRCUIT ONLINE", 24, 20, (0, 255, 255))
        draw_text(screen, text_font, f"Server: {host}:{port}", 24, 66)
        draw_text(screen, text_font, "Controls: A/D or Left/Right to turn, S to start", 24, 92)

        if my_index is not None:
            draw_text(screen, text_font, f"You are Player {my_index + 1}", 24, 118, (255, 220, 120))

        # Players and trails
        for p in state.get("players", []):
            bike = p.get("bike")
            if not bike:
                continue
            color = tuple(bike["color"])
            trail = bike["trail"]
            for i in range(1, len(trail)):
                pygame.draw.line(screen, color, cell_to_px(trail[i - 1]), cell_to_px(trail[i]), 3)
            head_pos = cell_to_px(bike["pos"])
            radius = 7 if bike.get("alive", False) else 5
            head_color = color if bike.get("alive", False) else (110, 110, 110)
            pygame.draw.circle(screen, head_color, head_pos, radius)

            label = f"P{p['index'] + 1}: {p['name']}"
            draw_text(screen, text_font, label, 24, 170 + p["index"] * 24, color)

        # Scoreboard
        scores = state.get("scores", {})
        score_parts = [f"P{i + 1}:{scores.get(str(i), 0)}" for i in range(4)]
        draw_text(screen, text_font, "Scores " + "  ".join(score_parts), 24, SCREEN_HEIGHT - 50)
        draw_text(screen, text_font, f"Mode: {state.get('mode', 'unknown')}", SCREEN_WIDTH - 260, 24, (180, 220, 255))
        draw_text(screen, text_font, state.get("message", ""), 24, SCREEN_HEIGHT - 80, (220, 200, 255))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sock.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Neon Circuit online client")
    parser.add_argument("--host", default=SERVER_HOST)
    parser.add_argument("--port", type=int, default=SERVER_PORT)
    args = parser.parse_args()
    run_client(args.host, args.port)


if __name__ == "__main__":
    main()
