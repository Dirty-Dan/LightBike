"""Minimal socket server for the Light Bike game.

This server keeps track of every connected player and broadcasts the game
state to all clients on every update.  Each client only sends movement
commands; the authoritative position is maintained here.  The protocol is a
simple JSON message:

    {"action": "move", "direction": "left"}

The game state that is sent back looks like:

    {"players": {"player1": {"x": 10, "y": 20, "color": [255,0,0],
                             "trail": [{"x":10,"y":20}, ...]}, ...}}

Running this module launches the server on port 25565.
"""

from __future__ import annotations

import json
import select
import socket
from typing import Dict, List, Tuple

HOST = "0.0.0.0"
PORT = 25565
STEP = 5  # distance moved per command


class LightBikeServer:
    """TCP server handling multiple Light Bike clients."""

    def __init__(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow fast restart during development
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen()

        # Mapping of socket -> player id
        self._socket_to_pid: Dict[socket.socket, str] = {}

        # Game state sent to every client
        self.players: Dict[str, Dict[str, object]] = {}
        self.next_id = 1

        self.sockets: List[socket.socket] = [self.server_socket]

        # Predefined colours for up to four players
        self.colours: List[Tuple[int, int, int]] = [
            (255, 0, 0),    # red
            (0, 0, 255),    # blue
            (0, 255, 0),    # green
            (255, 255, 0),  # yellow
        ]

    # ------------------------------------------------------------------ utils
    def _broadcast(self) -> None:
        """Send the entire game state to every connected client."""
        data = (json.dumps({"players": self.players}) + "\n").encode("utf-8")
        for sock in list(self.sockets):
            if sock is self.server_socket:
                continue
            try:
                sock.sendall(data)
            except OSError:
                # If sending fails, drop the client
                self._remove_client(sock)

    def _remove_client(self, sock: socket.socket) -> None:
        pid = self._socket_to_pid.pop(sock, None)
        if pid and pid in self.players:
            del self.players[pid]
        if sock in self.sockets:
            self.sockets.remove(sock)
        try:
            sock.close()
        finally:
            self._broadcast()

    # ----------------------------------------------------------------- accept
    def _accept_new_client(self) -> None:
        client_socket, _ = self.server_socket.accept()
        self.sockets.append(client_socket)

        pid = f"player{self.next_id}"
        self._socket_to_pid[client_socket] = pid

        # Place players at slightly different starting positions
        start_x = 50 + 100 * ((self.next_id - 1) % 4)
        start_y = 50 + 100 * ((self.next_id - 1) // 4)
        colour = self.colours[(self.next_id - 1) % len(self.colours)]

        self.players[pid] = {
            "x": start_x,
            "y": start_y,
            "color": list(colour),
            "trail": [],
        }
        self.next_id += 1
        self._broadcast()

    # ------------------------------------------------------------- client data
    def _handle_client(self, sock: socket.socket) -> None:
        try:
            data = sock.recv(1024)
            if not data:
                # Client disconnected
                self._remove_client(sock)
                return
            message = json.loads(data.decode("utf-8"))
        except Exception:
            self._remove_client(sock)
            return

        pid = self._socket_to_pid.get(sock)
        if not pid:
            return
        player = self.players.get(pid)
        if not player:
            return

        if message.get("action") == "move":
            direction = message.get("direction")
            if direction == "left":
                player["x"] -= STEP
            elif direction == "right":
                player["x"] += STEP
            elif direction == "up":
                player["y"] -= STEP
            elif direction == "down":
                player["y"] += STEP

            player["trail"].append({"x": player["x"], "y": player["y"]})

        self._broadcast()

    # ------------------------------------------------------------------- main
    def serve_forever(self) -> None:
        print(f"Server started on {HOST}:{PORT}")
        while True:
            readable, _, _ = select.select(self.sockets, [], [])
            for sock in readable:
                if sock is self.server_socket:
                    self._accept_new_client()
                else:
                    self._handle_client(sock)


def main() -> None:
    LightBikeServer().serve_forever()


if __name__ == "__main__":
    main()

