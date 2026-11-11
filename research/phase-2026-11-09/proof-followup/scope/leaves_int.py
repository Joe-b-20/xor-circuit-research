#!/usr/bin/env python3
"""Integer status of the 572 open leaves of the 229 load-bearing keys (combined system, G = 75) WITH RECORDED SOLVER STATUS.

For every (key, leaf (A = a, q_D = d)) in the published scan_leaves.json: the case matrix of check_combined75.matrix
(the independent checker's rows), all columns integer, bounds [0, h] (every column is a count of helpers or of gates;
the aux columns are bounded by 2G), three objectives: zero, minimise the number of hubs (types with r <= 2 and u >= 1),
maximise it.  scipy.optimize.milp (HiGHS), time limit TL seconds per solve.  Status codes recorded verbatim:
0 optimal, 1 iteration/time limit, 2 infeasible, 3 unbounded, 4 other.  "integer-infeasible" is asserted only on status 2.
Writes leaves_int.json.  A MEASUREMENT: nothing here is a certificate.
"""
import sys, json, time
sys.dont_write_bytecode = True
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

HERE = Path(__file__).resolve().parent
REPO = Path.home() / "xor-circuit-research"
CHK = REPO / "lower-bound-proofs/mixcolumns-lb75-open-cases/checkers"
MEAS = REPO / "lower-bound-proofs/mixcolumns-lb75-open-cases/combined/measurement"
sys.path.insert(0, str(CHK))
import check_combined75 as CC  # noqa: E402
G = 75
TL = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0


def solve(key, a, d):
    h = key[0]
    b, cols, n_sprint, pnames, _ = CC.matrix(key, ("eq", a), d)
    A = np.array([col for _, col in cols], float).T
    labels = [lab for lab, _ in cols]
    ub = np.array([h if isinstance(lab, tuple) else 2 * G for lab in labels], float)
    hubs = np.array([1.0 if (isinstance(lab, tuple) and lab[0] <= 2 and lab[1] >= 1) else 0.0 for lab in labels])
    res = {}
    sols = []
    for name, c in (("zero", np.zeros(len(labels))), ("min_hubs", hubs), ("max_hubs", -hubs)):
        t0 = time.time()
        r = milp(c, constraints=[LinearConstraint(A, -np.inf, np.array(b, float))], integrality=np.ones(len(labels)),
                 bounds=Bounds(np.zeros(len(labels)), ub), options=dict(time_limit=TL))
        st = int(r.status)
        entry = {"status": st, "message": r.message, "seconds": round(time.time() - t0, 2)}
        if r.x is not None:
            x = np.round(r.x).astype(int)
            # exact re-check of the integer solution against every row
            lhs = A @ x
            entry["violations"] = int(np.sum(lhs > np.array(b) + 1e-9))
            sol = {str(lab): int(v) for lab, v in zip(labels, x) if v != 0}
            entry["solution"] = sol
            if entry["violations"] == 0 and sol not in sols: sols.append(sol)
        res[name] = entry
        if st == 2: break          # infeasible: the other objectives cannot change that
    return res, sols


def main():
    L = json.load(open(MEAS / "scan_leaves.json"))["leaves"]
    out = {"time_limit": TL, "leaves": []}
    t0 = time.time(); n = 0; hist = Counter()
    for ks, leaves in L.items():
        key = eval(ks)
        for a, d in leaves:
            n += 1
            res, sols = solve(key, a, d)
            statuses = [v["status"] for v in res.values()]
            cls = "infeasible" if 2 in statuses else ("feasible" if any(v.get("violations") == 0 for v in res.values()) else "unresolved")
            hist[cls] += 1
            out["leaves"].append({"key": list(key), "A": a, "qD": d, "class": cls, "solves": res, "distinct_solutions": sols})
            if n % 50 == 0:
                print(f"{n}/572 {dict(hist)} {time.time()-t0:.0f}s", flush=True)
                json.dump(out, open(HERE / "leaves_int.json", "w"))
    out["summary"] = dict(hist); out["seconds"] = round(time.time() - t0)
    json.dump(out, open(HERE / "leaves_int.json", "w"))
    print("done", dict(hist), f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
