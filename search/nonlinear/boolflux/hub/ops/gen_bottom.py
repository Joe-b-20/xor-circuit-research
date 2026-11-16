#!/usr/bin/env python3
"""Hub operator gen_bottom (see depth_ops.py for what it does and its measured effect)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import depth_ops  # noqa: E402
depth_ops.run("gen_bottom")
