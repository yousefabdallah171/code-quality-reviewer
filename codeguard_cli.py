#!/usr/bin/env python3
"""Entry point for the codeguard skill CLI."""

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from codeguard_workflow import main  # noqa: E402

if __name__ == "__main__":
    main()
