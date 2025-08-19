# LightBike

A very small experiment in building a multiplayer "light bike" game.  The
project contains a socket server that keeps track of the game state and a
simple Pygame client.  Two or more players can connect to the server and race
around the arena in real time.

## Getting the code

The game is written in pure Python and runs directly from source—no binaries
are required.  Download the code and install the only dependency, `pygame`:

```bash
git clone https://github.com/<user>/LightBike
cd LightBike
pip install -r requirements.txt
```

Alternatively, grab the latest source archive from the GitHub releases page
and extract it.

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

