"""z_b0nor2.py -- read d4c's B0noR2b result (read-only) to cite it exactly."""
import json, os
p = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/d4c/c3_B0noR2b.json")
d = json.load(open(p))
print({k: d[k] for k in ("status", "bound", "wall", "fix3", "fix4", "ub", "strict", "args")})
