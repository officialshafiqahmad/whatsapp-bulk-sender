#!/usr/bin/env python3
"""Double-click friendly launcher for the web UI."""

from __future__ import annotations

import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    venv_python = ROOT / "venv" / "bin" / "python"
    python = str(venv_python if venv_python.exists() else sys.executable)

    if not venv_python.exists():
        subprocess.check_call([python, "-m", "venv", str(ROOT / "venv")])
        python = str(ROOT / "venv" / "bin" / "python")
        subprocess.check_call([python, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])
        subprocess.check_call([python, "-m", "playwright", "install", "chromium"])

    webbrowser.open("http://127.0.0.1:8765")
    subprocess.call([python, str(ROOT / "app.py")])


if __name__ == "__main__":
    main()
