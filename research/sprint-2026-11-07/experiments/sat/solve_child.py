"""Child: read request json, encode, solve, print one json line.  Killed by parent on timeout."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sat87  # noqa: E402
from pysat.solvers import Solver  # noqa: E402

req = json.load(open(sys.argv[1]))
t0 = time.time()
cl, nv, meta = sat87.encode(req["K"], req["m"], req["distinct"], req["symbreak"])
t1 = time.time()
s = Solver(name=req["solver"], bootstrap_with=cl)
r = s.solve()
t2 = time.time()
out = {"result": "SAT" if r else "UNSAT", "nvars": nv, "nclauses": len(cl),
       "enc_secs": round(t1 - t0, 2), "solve_secs": round(t2 - t1, 2)}
if r:
    order = sat87.decode(s.get_model(), meta)
    out["new_gates"] = order
print(json.dumps(out))
