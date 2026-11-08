"""z_nsol.py -- number of solutions met (solution callback count) and objective per run json."""
import json, glob, os
HERE = os.path.dirname(os.path.abspath(__file__))
for p in sorted(glob.glob(os.path.join(HERE, "e3_*.json"))):
    if p.endswith("_sol.json"): continue
    d = json.load(open(p))
    print(os.path.basename(p), d.get("status"), "nsol", d.get("nsol"), "objective", d.get("objective"),
          "bound", d.get("bound"), "wall", round(d.get("wall", 0)))
