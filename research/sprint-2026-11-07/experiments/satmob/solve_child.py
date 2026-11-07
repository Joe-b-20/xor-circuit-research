"""Child: read request json, encode with sat/sat87.encode, optionally restrict the operand pool
(unit clauses forbidding selectors of constants outside `allowed`), solve, print one json line.
Killed by the parent on timeout."""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "sat"))
import sat87  # noqa: E402
from pysat.solvers import Solver  # noqa: E402

req = json.load(open(sys.argv[1]))
t0 = time.time()
cl, nv, meta = sat87.encode(req["K"], req["m"], req["distinct"], req["symbreak"])
nforbid = 0
if req.get("allowed") is not None:
    allowed = set(req["allowed"])
    const = meta["const"]
    for j in range(req["m"]):
        for u in range(len(const)):
            if const[u] not in allowed:
                cl.append([-meta["A"][j][u]]); cl.append([-meta["B"][j][u]]); nforbid += 2
t1 = time.time()
s = Solver(name=req["solver"], bootstrap_with=cl)
r = s.solve()
t2 = time.time()
out = {"result": "SAT" if r else "UNSAT", "nvars": nv, "nclauses": len(cl), "nforbid": nforbid,
       "enc_secs": round(t1 - t0, 2), "solve_secs": round(t2 - t1, 2)}
if r:
    out["new_gates"] = sat87.decode(s.get_model(), meta)
print(json.dumps(out))
