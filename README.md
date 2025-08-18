# LightBike

A very small experiment in building a multiplayer "light bike" game.  The
project contains a socket server that keeps track of the game state and a
simple Pygame client.  Two or more players can connect to the server and race
around the arena in real time.

## Running the game

1. Start the server on a machine reachable by all players:

   ```bash
   python server.py
   ```

2. For each player run the client, replacing `SERVER_HOST` in `client.py` if the
   server is on a different machine:

   ```bash
   python client.py
   ```

Use the arrow keys to move.  Each player leaves a trail behind them and the
game state is synchronised across all clients.

