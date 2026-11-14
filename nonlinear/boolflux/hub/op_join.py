#!/usr/bin/env python3
"""hub operator join (see ops.py for the common CLI)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from boolflux.hub.ops import main  # noqa: E402
sys.exit(main("join"))
