"""Build script for Neon Circuit executables via PyInstaller."""

from __future__ import annotations

import platform
import subprocess
import sys


def main() -> int:
    os_name = platform.system()
    print(f"Building Neon Circuit for {os_name}...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        f"NeonCircuit-{os_name}",
        "LightBike.py",
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
