"""Authoritative online multiplayer server for Neon Circuit.

Protocol (newline-delimited JSON):
- Client -> server:
    {"action": "join", "name": "Alice"}
    {"action": "turn", "dir": -1|1}
    {"action": "start"}
- Server -> client:
    {
      "type": "welcome",
      "player_index": 0,
      "name": "Alice"
    }
    {
      "type": "state",
      "mode": "lobby"|"playing"|"round_over",
      "players": [...],
      "scores": {"0": 1, ...},
      "message": "..."
    }
"""

from __future__ import annotations

import argparse
import json
import socket
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

from neon_circuit.config import COLOR_PRESETS, SOUND_PRESETS
from neon_circuit.gameplay import ArenaRound, PlayerConfig

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 25565
MAX_PLAYERS = 4


@dataclass
class ClientInfo:
    sock: socket.socket
    addr: tuple[str, int]
    name: str
    player_index: int


class NeonCircuitServer:
    def __init__(self, host: str, port: int, tick_rate: int = 30) -> None:
        self.host = host
        self.port = port
        self.tick_rate = tick_rate

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        self.clients: Dict[socket.socket, ClientInfo] = {}
        self.scores: Dict[int, int] = {i: 0 for i in range(MAX_PLAYERS)}
        self.lock = threading.Lock()

        self.round: Optional[ArenaRound] = None
        self.mode = "lobby"
        self.round_over_time: float = 0.0

    def _make_player_config(self, idx: int) -> PlayerConfig:
        return PlayerConfig(
            index=idx,
            color=COLOR_PRESETS[idx % len(COLOR_PRESETS)],
            sound_profile=SOUND_PRESETS[idx % len(SOUND_PRESETS)],
            controls={},
        )

    def _active_player_configs(self) -> list[PlayerConfig]:
        indices = sorted(info.player_index for info in self.clients.values())
        return [self._make_player_config(idx) for idx in indices]

    def _start_round(self) -> None:
        configs = self._active_player_configs()
        if len(configs) < 2:
            return
        self.round = ArenaRound(configs)
        self.mode = "playing"

    def _serialize_state(self, message: str = "") -> dict[str, object]:
        players = []
        by_index = {c.player_index: c for c in self.clients.values()}

        for idx, info in sorted(by_index.items()):
            bike_payload = None
            if self.round:
                for bike in self.round.bikes:
                    if bike.config.index == idx:
                        bike_payload = {
                            "pos": [bike.pos[0], bike.pos[1]],
                            "trail": [[t[0], t[1]] for t in bike.trail],
                            "alive": bike.alive,
                            "color": list(bike.config.color),
                        }
                        break

            players.append(
                {
                    "index": idx,
                    "name": info.name,
                    "bike": bike_payload,
                }
            )

        return {
            "type": "state",
            "mode": self.mode,
            "players": players,
            "scores": {str(k): v for k, v in self.scores.items()},
            "message": message,
        }

    def _send_json(self, sock: socket.socket, payload: dict[str, object]) -> bool:
        try:
            sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            return True
        except OSError:
            return False

    def _broadcast_state(self, message: str = "") -> None:
        payload = self._serialize_state(message)
        dead = []
        for sock in self.clients:
            if not self._send_json(sock, payload):
                dead.append(sock)
        for sock in dead:
            self._drop_client(sock)

    def _drop_client(self, sock: socket.socket) -> None:
        info = self.clients.pop(sock, None)
        try:
            sock.close()
        except OSError:
            pass
        if info:
            print(f"[-] Player disconnected: {info.name} ({info.addr[0]}:{info.addr[1]})")
            if self.mode == "playing" and self.round:
                for bike in self.round.bikes:
                    if bike.config.index == info.player_index:
                        bike.alive = False
                        self.round._finalize_result()  # keep server deterministic
                        break

    def _handle_line(self, sock: socket.socket, line: bytes) -> None:
        try:
            msg = json.loads(line.decode("utf-8"))
        except json.JSONDecodeError:
            return

        action = msg.get("action")
        info = self.clients.get(sock)
        if not info:
            return

        if action == "turn" and self.mode == "playing" and self.round:
            dir_value = int(msg.get("dir", 0))
            if dir_value in (-1, 1):
                self.round.queue_turn(info.player_index, dir_value)

        elif action == "start" and self.mode == "lobby":
            if len(self.clients) >= 2:
                self._start_round()
                self._broadcast_state("Round started")

    def _client_thread(self, sock: socket.socket) -> None:
        buff = b""
        try:
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buff += chunk
                while b"\n" in buff:
                    line, buff = buff.split(b"\n", 1)
                    if line.strip():
                        with self.lock:
                            self._handle_line(sock, line)
        except OSError:
            pass
        finally:
            with self.lock:
                self._drop_client(sock)
                self._broadcast_state()

    def _accept_clients_forever(self) -> None:
        while True:
            sock, addr = self.server_socket.accept()
            with self.lock:
                if len(self.clients) >= MAX_PLAYERS:
                    self._send_json(sock, {"type": "error", "message": "Lobby is full (max 4 players)."})
                    sock.close()
                    continue

                player_index = 0
                used = {client.player_index for client in self.clients.values()}
                while player_index in used:
                    player_index += 1

                self._send_json(sock, {"type": "welcome", "player_index": player_index})

                sock.settimeout(None)
                info = ClientInfo(
                    sock=sock,
                    addr=addr,
                    name=f"Player {player_index + 1}",
                    player_index=player_index,
                )
                self.clients[sock] = info
                print(f"[+] Player connected: {info.name} ({addr[0]}:{addr[1]})")
                self._broadcast_state("Player joined")

            thread = threading.Thread(target=self._client_thread, args=(sock,), daemon=True)
            thread.start()

    def _game_loop(self) -> None:
        last = time.perf_counter()
        while True:
            now = time.perf_counter()
            dt = now - last
            last = now

            with self.lock:
                if self.mode == "playing" and self.round:
                    result = self.round.update(dt)
                    if result:
                        self.mode = "round_over"
                        if result.winner is not None:
                            self.scores[result.winner] += 1
                        self.round_over_time = time.perf_counter()
                        self._broadcast_state(result.message)
                    else:
                        self._broadcast_state()
                elif self.mode == "round_over":
                    self._broadcast_state("Round over - restarting in 3 seconds")
                    if time.perf_counter() - self.round_over_time >= 3.0:
                        if len(self.clients) >= 2:
                            self._start_round()
                            self._broadcast_state("New round")
                        else:
                            self.mode = "lobby"
                            self.round = None
                else:
                    self._broadcast_state("Waiting for 2+ players. Host presses S to start.")

            time.sleep(1.0 / self.tick_rate)

    def serve_forever(self) -> None:
        print(f"Neon Circuit server listening on {self.host}:{self.port}")
        accept_thread = threading.Thread(target=self._accept_clients_forever, daemon=True)
        accept_thread.start()
        self._game_loop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Neon Circuit online multiplayer server")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    server = NeonCircuitServer(args.host, args.port)
    server.serve_forever()


if __name__ == "__main__":
    main()
