#!/usr/bin/env python3
"""LP bounds of the aggregates of the leaf case systems of the M^T q = 3 keys (scipy HiGHS; a MEASUREMENT used only to
size the enumeration; the enumeration itself re-solves the LP at every node).  For every LP-feasible key of the block and
every LP-feasible leaf (A = a, q_D = d): min/max of U = sum u n, W = sum r u n, #helpers with u >= 1, by (r,u) the max of
sum_v n_(r,u,v), #r=0 helpers with u>=1, n3 (all full helpers), and the status of every solve."""
import sys, json, time
sys.dont_write_bytecode = True
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scope"))
import hypo_scan as HS
CC = HS.CC

def bounds(key, a, d):
    A, b = HS.case_system(key, ("eq", a), d)
    _, cols, _, _, _ = CC.matrix(key, ("eq", a), d)
    labels = [lab for lab, _ in cols]
    n = len(labels)
    def opt(c, sense):
        res = linprog(np.array(c, float) * (1 if sense == "min" else -1), A_ub=A, b_ub=b, bounds=(0, None), method="highs")
        if res.status != 0: return ("status", res.status)
        return round((res.fun if sense == "min" else -res.fun), 6)
    def vec(fn): return [fn(*lab) if isinstance(lab, tuple) else 0 for lab in labels]
    out = {}
    for name, fn in [("U", lambda r, u, v: u), ("W", lambda r, u, v: r * u), ("nU", lambda r, u, v: int(u >= 1)),
                     ("n0U", lambda r, u, v: int(r == 0 and u >= 1)), ("n3", lambda r, u, v: int(r == 3)),
                     ("n_u1", lambda r, u, v: int(u == 1)), ("n_u2", lambda r, u, v: int(u == 2)), ("n_u3", lambda r, u, v: int(u == 3)),
                     ("U0", lambda r, u, v: u if r == 0 else 0), ("Uanch", lambda r, u, v: u if r >= 1 else 0)]:
        out[name] = [opt(vec(fn), "min"), opt(vec(fn), "max")]
    ru = {}
    for r in range(4):
        for u in range(1, 4):
            v = vec(lambda rr, uu, vv: int(rr == r and uu == u))
            if any(v): ru[f"({r},{u})"] = opt(v, "max")
    out["max_by_ru"] = ru
    return out

if __name__ == "__main__":
    keys = [tuple(k) for k in json.load(open(HERE.parent / "scope/hypo_kill_Mt3.json"))["killed_keys_list"]]
    t0 = time.time(); res = {}
    for key in keys:
        leaves = HS.open_leaves(key, HS.ALLOW["full"])
        res[str(key)] = {"open_leaves": leaves, "leaves": {}}
        for a, d in leaves:
            res[str(key)]["leaves"][f"{a},{d}"] = bounds(key, a, d)
    json.dump(res, open(HERE / "lp_bounds.json", "w"), indent=1)
    nl = sum(len(v["open_leaves"]) for v in res.values())
    print(len(keys), "keys,", nl, "open leaves,", f"{time.time()-t0:.0f}s")
    for k, v in res.items():
        for lf, bd in v["leaves"].items():
            print(k, lf, "U", bd["U"], "W", bd["W"], "nU", bd["nU"], "n0U", bd["n0U"], "n3", bd["n3"], "u1/u2/u3", bd["n_u1"], bd["n_u2"], bd["n_u3"], "maxru", bd["max_by_ru"])
