"""Task 1b (revised): for each group, (i) forward SAT at m = claimed minimum -> explicit certificate
(upper bound), (ii) transposed SAT at m_T = |T| - 1 = 7 -> UNSAT (4 inputs, 8 targets; instant), which
with the transposition identity C(A) = C(A^T) + n - 4 gives the lower bound.  (iii) forward UNSAT at
m - 1 is attempted with a short limit and reported honestly.  Appends to minima.jsonl."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from run_sat import solve
from submaps import submatrix

HERE = os.path.dirname(os.path.abspath(__file__))
out = open(os.path.join(HERE, "minima.jsonl"), "a")
limit_fwd_unsat = int(sys.argv[1]) if len(sys.argv) > 1 else 120
for g in range(8):
    sup, fwd, cols = submatrix([g])
    n = len(sup)
    T = sorted(set(c for c in cols if bin(c).count("1") >= 2))
    claimed = lib.M_GROUP[g]
    r = solve(n, fwd, claimed, limit=600, tag=f"group{g} forward m={claimed}")
    r.update({"group": g, "mode": "forward", "support": sup})
    print(json.dumps({k: v for k, v in r.items() if k != "gates"}), flush=True)
    out.write(json.dumps(r) + "\n"); out.flush()
    rT = solve(4, T, len(T) - 1, limit=600, tag=f"group{g} transposed m_T={len(T)-1}")
    rT.update({"group": g, "mode": "transposed", "n_cols": n, "distinct_nonbasis_cols": len(T),
               "implied_forward_lb": len(T) + n - 4})
    print(json.dumps({k: v for k, v in rT.items() if k != "gates"}), flush=True)
    out.write(json.dumps(rT) + "\n"); out.flush()
    if limit_fwd_unsat > 0:
        r2 = solve(n, fwd, claimed - 1, limit=limit_fwd_unsat, tag=f"group{g} forward m={claimed-1}")
        r2.update({"group": g, "mode": "forward", "support": sup})
        print(json.dumps({k: v for k, v in r2.items() if k != "gates"}), flush=True)
        out.write(json.dumps(r2) + "\n"); out.flush()
