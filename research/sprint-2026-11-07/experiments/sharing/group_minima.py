"""Task 1b: exact unrestricted minima of the eight 4-output groups, restricted to their support
(WLOG: substituting 0 for a non-support input never increases gate count).  For each group: SAT at
m = claimed and UNSAT at m = claimed - 1.  Appends to minima.jsonl."""
import json
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from run_sat import solve

HERE = os.path.dirname(os.path.abspath(__file__))
out = open(os.path.join(HERE, "minima.jsonl"), "a")
for g in range(8):
    sup = lib.group_support(g)
    n = len(sup)
    targets = [lib.relabel(t, sup) for t in lib.GROUP_TARGETS[g]]
    claimed = lib.M_GROUP[g]
    for m in (claimed - 1, claimed):
        r = solve(n, targets, m, limit=900, tag=f"group{g}")
        r["group"] = g
        r["support"] = sup
        print(json.dumps({k: v for k, v in r.items() if k != "gates"}), flush=True)
        out.write(json.dumps(r) + "\n"); out.flush()
