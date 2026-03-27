# Neon Circuit

**Neon Circuit** is a polished, local-multiplayer light-bike arena game inspired by classic Tron gameplay.
It is built with **Python + Pygame** for fast development and easy cross-platform packaging for **Windows** and **Linux**.

## Features

- 2 to 4 local players on one machine
- Continuous forward bike movement with 90° left/right turns
- Solid light trails with instant elimination on collision
- Round-based gameplay with persistent scoreboard
- Retro neon visual style (dark arena + glowing trails/grid)
- Title screen, setup menu, gameplay, and round results flow
- Per-player customization before each round:
  - bike color
  - bike sound profile (Classic Synth / Deep Engine / Arcade Buzz)
- Procedural retro audio for bike hums, menu SFX, collision, and win sounds
- Build script for executable packaging with PyInstaller

## Controls

### Gameplay turns

- **Player 1:** `A` / `D`
- **Player 2:** `Left Arrow` / `Right Arrow`
- **Player 3:** `J` / `L`
- **Player 4:** `Numpad 4` / `Numpad 6`

### Global

- `ESC` = Quit (or pause from gameplay into result overlay)

### Setup screen

- `UP` / `DOWN` = select player row
- `LEFT` / `RIGHT` = change selected player color
- `Q` / `E` = change selected player sound profile
- `[` / `]` = change player count (2-4)
- `ENTER` = start round

### Round result screen

- `R` = replay
- `M` = return to title
- `ESC` = quit

## Quick Start (Run from Source)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux
# .venv\Scripts\activate  # Windows PowerShell

pip install -r requirements.txt
python LightBike.py
```

You can also launch with:

```bash
python -m neon_circuit
```

## Build Executables (Windows and Linux)

> Build on each target OS to produce native executables.

### One-command build

```bash
python build.py
```

This creates a one-file executable in `dist/` named:

- Linux: `NeonCircuit-Linux`
- Windows: `NeonCircuit-Windows.exe`

### Manual PyInstaller command

```bash
python -m PyInstaller --noconfirm --clean --onefile --windowed --name NeonCircuit LightBike.py
```

## Downloadable Builds

To distribute downloadable files:

1. Build on Linux and Windows separately using `python build.py`.
2. Zip the generated files from `dist/`.
3. Upload both archives as release assets (e.g., GitHub Releases):
   - `NeonCircuit-Linux.zip`
   - `NeonCircuit-Windows.zip`

## Project Structure

```text
LightBike/
├── LightBike.py              # Main launcher
├── build.py                  # PyInstaller build helper
├── requirements.txt
├── README.md
├── neon_circuit/
│   ├── __init__.py
│   ├── __main__.py           # python -m neon_circuit entrypoint
│   ├── app.py                # State machine + menus + flow
│   ├── audio.py              # Procedural retro synth/sfx
│   ├── config.py             # Tunables, controls, palettes
│   ├── gameplay.py           # Bike movement, trails, collisions
│   └── rendering.py          # Neon UI + arena drawing helpers
├── server.py                 # Legacy network prototype (unused)
└── client.py                 # Legacy network prototype (unused)
```

## Extensibility Notes

The codebase is intentionally modular so you can add:

- AI bots (`gameplay.py` and `app.py` player injection)
- Online multiplayer (replace local input layer)
- Multiple arena types (spawn and bounds presets)
- Power-ups and game modes (state + collision hooks)

## Technical Choice

**Why Pygame?**

- Very fast to prototype arcade mechanics
- Excellent keyboard latency for responsive turning gameplay
- Easy packaging into standalone executables with PyInstaller
- Runs reliably on both Windows and Linux with minimal setup

