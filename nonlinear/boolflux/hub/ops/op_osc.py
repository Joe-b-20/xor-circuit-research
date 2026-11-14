#!/usr/bin/env python3
"""Track-F hub operator osc (see f_ops.py for what it does and measured effect)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_ops  # noqa: E402
f_ops.run("osc")
