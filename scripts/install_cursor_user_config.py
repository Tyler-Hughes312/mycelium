#!/usr/bin/env python3
"""Backward-compatible entry → install_mcp_clients.py """

from __future__ import annotations

import runpy
from pathlib import Path

if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "install_mcp_clients.py"
    runpy.run_path(str(target), run_name="__main__")
