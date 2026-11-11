#!/usr/bin/env python3
"""Hypothetical coverage scans at G = 75 (LP status, scipy HiGHS; a MEASUREMENT, never a premise).

Same driver as the published measurement (package lp_regen.run) and the same matrices as the independent checker
check_combined75.matrix (sprint case systems + push rows).  A key is feasible iff its flat system is LP-feasible and
some ALLOWED leaf (A = a, q_D = d) of its case tree is LP-feasible.  The allowed set is the variant's:
  full          all leaves                       (must reproduce 280 open claims / 229 load-bearing keys)
  A01           a <= 1                            (every leaf with A >= 2 assumed closed)
  A01_or_dark   a <= 1 or d >= 1                  (every leaf with A >= 2 and q_D = 0 assumed closed)
  A01_or_A5     a <= 1 or a >= 5                  (every leaf with A = 2..4 assumed closed)
  A0            a == 0                            (every leaf with A >= 1 assumed closed)
Writes hypo_<variant>.json: survivors with (k, l), every claim's (k, l, dead), LP-feasible keys, load-bearing keys
(the feasible even key at level k and odd key at level l of each survivor) with their open allowed leaves.
usage: python3 hypo_scan.py full A01 ...
"""
import sys, json, time, importlib.util
sys.dont_write_bytecode = True
from math import comb
from pathlib import Path
from collections import Counter
from functools import lru_cache
import numpy as np
from scipy.optimize import linprog

HERE = Path(__file__).resolve().parent
REPO = Path.home() / "xor-circuit-research"
CHK = REPO / "lower-bound-proofs/mixcolumns-lb75-open-cases/checkers"
PKG = REPO / "lower-bound-proofs/mixcolumns-lb75/source/lower_bounds/checks"
sys.path.insert(0, str(CHK))
import check_combined75 as CC  # noqa: E402
spec = importlib.util.spec_from_file_location("lp_regen_pkg", PKG / "lp_regen.py"); LR = importlib.util.module_from_spec(spec); spec.loader.exec_module(LR)
G = 75
ALLOW = {
    "full": lambda a, d: True,
    "A01": lambda a, d: a <= 1,
    "A01_or_dark": lambda a, d: a <= 1 or d >= 1,
    "A01_or_A5": lambda a, d: a <= 1 or a >= 5,
    "A0": lambda a, d: a == 0,
}
VARIANT = ["full"]
STATUS = Counter(); RECORD = {}; NLP = [0]; MATCACHE = {}


def lp_feasible(A, b):
    NLP[0] += 1
    res = linprog(np.zeros(A.shape[1]), A_ub=A, b_ub=b, bounds=(0, None), method="highs")
    STATUS[res.status] += 1
    if res.status not in (0, 2): print("LP status", res.status, flush=True)
    return res.status != 2


def case_system(key, hub, dark):
    k = (key, hub, dark)
    if k not in MATCACHE:
        if len(MATCACHE) > 20000: MATCACHE.clear()
        b, cols, n_sprint, pnames, _ = CC.matrix(key, hub, dark)
        MATCACHE[k] = (np.array([col for _, col in cols], float).T, np.array(b, float))
    return MATCACHE[k]


def feasible_cases(key, allow):
    q = key[4]
    A, b = case_system(key, None, None)
    if not lp_feasible(A, b): return False
    for a in range(q + 1):
        if not any(allow(a, d) for d in range(q + 1)): continue
        A, b = case_system(key, ("eq", a), None)
        if not lp_feasible(A, b): continue
        for d in range(q + 1):
            if not allow(a, d): continue
            A, b = case_system(key, ("eq", a), d)
            if lp_feasible(A, b): return True
    return False


def open_leaves(key, allow):
    q = key[4]; out = []
    A, b = case_system(key, None, None)
    if not lp_feasible(A, b): return out
    for a in range(q + 1):
        A, b = case_system(key, ("eq", a), None)
        if not lp_feasible(A, b): continue
        for d in range(q + 1):
            if not allow(a, d): continue
            A, b = case_system(key, ("eq", a), d)
            if lp_feasible(A, b): out.append([a, d])
    return out


@lru_cache(None)
def feasible(h, y, F, q, z, ori):
    key = (h, y, F, ori, q, z)
    if CC.direct_exclusion(key) or 2 * h + y + z + comb(q, 2) < 32:
        r = False
    elif not CC.package_types(key):
        r = False
    else:
        r = feasible_cases(key, ALLOW[VARIANT[0]])
    RECORD[key] = r
    return r


def load_bearing(surv, feas):
    lb = {}
    for st, ori, k, ell in surv:
        other = "Mt" if ori == "M" else "M"
        for q in range(0, k + 1):
            kk = (st[4], st[2], st[3], ori, q, k - q)
            if kk in feas: lb.setdefault(kk, []).append([list(st), ori, "even"])
        for q in range(0, ell + 1):
            kk = (st[5], st[3], st[2], other, q, ell - q)
            if kk in feas: lb.setdefault(kk, []).append([list(st), ori, "odd"])
    return lb


def run_variant(variant):
    t0 = time.time(); VARIANT[0] = variant; RECORD.clear(); STATUS.clear(); NLP[0] = 0; feasible.cache_clear()
    LR.feasible = feasible
    states, claims, surv = LR.run(G)
    feas = {k for k, v in RECORD.items() if v}
    lb = load_bearing(surv, feas)
    allow = ALLOW[variant]
    leaves = {str(k): open_leaves(k, allow) for k in sorted(lb)}
    out = {"variant": variant, "G": G, "scalar_states": len(states), "oriented_claims": len(claims), "survivors": len(surv),
           "survivors_M": sum(1 for st, o, k, l in surv if o == "M"), "survivors_Mt": sum(1 for st, o, k, l in surv if o == "Mt"),
           "shortfall": sorted(Counter(st[10] - k - l for st, o, k, l in surv).items()),
           "claims": [[list(st), o, k, l, dead] for (st, o), (k, l, dead) in sorted(claims.items())],
           "survivor_list": [[list(st), o, k, l] for st, o, k, l in sorted(surv)],
           "keys_touched": len(RECORD), "keys_lp_feasible": len(feas), "keys_load_bearing": len(lb),
           "lp_calls": NLP[0], "lp_status": dict(STATUS),
           "lp_feasible_keys": sorted(list(k) for k in feas),
           "load_bearing_keys": sorted(list(k) for k in lb),
           "load_bearing_claims": {str(k): v for k, v in sorted(lb.items())},
           "load_bearing_open_leaves": leaves,
           "lb_by_q": sorted(Counter(k[4] for k in lb).items()), "lb_by_ori": dict(Counter(k[3] for k in lb)),
           "seconds": round(time.time() - t0)}
    json.dump(out, open(HERE / f"hypo_{variant}.json", "w"))
    print(f"[{variant}] states {len(states)} claims {len(claims)} survivors {len(surv)} (M {out['survivors_M']}, Mt {out['survivors_Mt']}); "
          f"shortfall {out['shortfall']}; keys touched {len(RECORD)}, LP-feasible {len(feas)}, load-bearing {len(lb)} "
          f"(by q {out['lb_by_q']}); LP calls {NLP[0]} status {dict(STATUS)}; {time.time()-t0:.0f}s", flush=True)
    return out


if __name__ == "__main__":
    for v in sys.argv[1:]:
        run_variant(v)
