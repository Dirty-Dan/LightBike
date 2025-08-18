"""Pygame client for the networked Light Bike game."""

import json
import socket
from typing import Dict

import pygame

SERVER_HOST = "127.0.0.1"  # Change to the server's IP when playing remotely
PORT = 25565


def send(sock: socket.socket, message: Dict[str, str]) -> None:
    sock.sendall(json.dumps(message).encode("utf-8"))


buffer = b""


def receive(sock: socket.socket) -> Dict[str, object] | None:
    """Receive a single JSON message terminated by a newline."""
    global buffer
    try:
        chunk = sock.recv(4096)
        if not chunk:
            return None
        buffer += chunk
    except BlockingIOError:
        return None
    if b"\n" not in buffer:
        return None
    line, buffer = buffer.split(b"\n", 1)
    return json.loads(line.decode("utf-8"))


def main() -> None:
    # ----------------------------------------------------------------- network
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_HOST, PORT))
    sock.setblocking(False)

    # ------------------------------------------------------------------ pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Light Bike")
    clock = pygame.time.Clock()

    running = True
    while running:
        # Handle input events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            send(sock, {"action": "move", "direction": "left"})
        elif keys[pygame.K_RIGHT]:
            send(sock, {"action": "move", "direction": "right"})
        elif keys[pygame.K_UP]:
            send(sock, {"action": "move", "direction": "up"})
        elif keys[pygame.K_DOWN]:
            send(sock, {"action": "move", "direction": "down"})

        # ---------------------------------------------------------------- draw
        state = receive(sock)
        if state:
            screen.fill((0, 0, 0))
            for player in state["players"].values():
                color = tuple(player["color"])
                for point in player.get("trail", []):
                    pygame.draw.rect(screen, color, (point["x"], point["y"], 10, 10))
                pygame.draw.rect(screen, color, (player["x"], player["y"], 10, 10))
            pygame.display.flip()

        clock.tick(60)

    pygame.quit()
    sock.close()


if __name__ == "__main__":
    main()

