#!/usr/bin/env python3
"""recon-check: my own LP scan at G = 75 (scipy HiGHS; a MEASUREMENT, never a premise) over lp_regen.scalar_states(75),
with the package driver's walk (lp_regen.run), but with MY feasibility oracle built from the matrices of check_combined75:
  sprint    : check_cases4.matrix case systems (package + batch-1 + flat PK/FM + hub A = a with P1-P5, LIM + dark q_D = d);
              a key is LP-feasible iff the flat system is and some leaf (a, d) is          -> recon: 686 survivors
  push      : package rows (certify75.system) + my push5/push6 rows, flat, no case split   -> recon / archive: 509
  combined  : sprint case systems + my push rows in every case (restricted to kept columns) -> recon: 280
Writes scan_<variant>.json (every claim's (k, l, dead), survivors, LP-feasible keys) and compares with recon/scan_<variant>.json:
identical survivor sets with identical (k, l), and identical (k, l, dead) on all 7,416 claims.
usage: python3 scan.py sprint|push|combined ...
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
RECON = Path("/home/joebachir20/xs-campaigns/2026-11-09-phase/recon")
PKG = Path("/home/joebachir20/xor-circuit-research/lower-bound-proofs/mixcolumns-lb75/source/lower_bounds/checks")
sys.path.insert(0, str(HERE))
import check_combined75 as CC
spec = importlib.util.spec_from_file_location("lp_regen_pkg", PKG / "lp_regen.py"); LR = importlib.util.module_from_spec(spec); spec.loader.exec_module(LR)
spec = importlib.util.spec_from_file_location("certify75_pkg", PKG / "certify75.py"); C75 = importlib.util.module_from_spec(spec); spec.loader.exec_module(C75)
G = 75
VARIANT = ["combined"]
STATUS = Counter(); RECORD = {}; NLP = [0]


def lp_feasible(A, b):
    """A x <= b, x >= 0 has a solution?  HiGHS status 2 = infeasible; anything else counts as feasible (status logged)."""
    NLP[0] += 1
    res = linprog(np.zeros(A.shape[1]), A_ub=A, b_ub=b, bounds=(0, None), method="highs")
    STATUS[res.status] += 1
    if res.status not in (0, 2): print("LP status", res.status, flush=True)
    return res.status != 2


def case_system(key, hub, dark):
    """(A, b) as numpy arrays for the case system of the current variant."""
    if VARIANT[0] == "sprint":
        b, cols, n_pkg, n_b1, n_flat = CC.c4.matrix(key, hub, dark)
    else:
        b, cols, n_sprint, pnames, _ = CC.matrix(key, hub, dark)
    A = np.array([col for _, col in cols], float).T
    return A, np.array(b, float)


def feasible_cases(key):
    q = key[4]
    A, b = case_system(key, None, None)
    if not lp_feasible(A, b): return False
    for a in range(q + 1):
        A, b = case_system(key, ("eq", a), None)
        if not lp_feasible(A, b): continue
        for d in range(q + 1):
            A, b = case_system(key, ("eq", a), d)
            if lp_feasible(A, b): return True
    return False


def feasible_push(key):
    types, A0, B0, names = C75.system(key)
    assert types == CC.package_types(key)
    prow = CC.push_rows(key, types)
    A = np.array(A0 + [c for _, c, _ in prow], float); b = np.array(B0 + [bb for _, _, bb in prow], float)
    return lp_feasible(A, b)


@lru_cache(None)
def feasible(h, y, F, q, z, ori):
    key = (h, y, F, ori, q, z)
    if CC.direct_exclusion(key) or 2 * h + y + z + comb(q, 2) < 32:
        r = False
    elif not CC.package_types(key):
        r = False
    else:
        r = feasible_push(key) if VARIANT[0] == "push" else feasible_cases(key)
    RECORD[key] = r
    return r


def run_variant(variant):
    t0 = time.time(); VARIANT[0] = variant; RECORD.clear(); STATUS.clear(); NLP[0] = 0; CC.PUSHCACHE.clear(); feasible.cache_clear()
    LR.feasible = feasible                     # the driver's oracle
    states, claims, surv = LR.run(G)
    feas = {k for k, v in RECORD.items() if v}
    out = {"variant": variant, "G": G, "scalar_states": len(states), "oriented_claims": len(claims), "survivors": len(surv),
           "survivors_M": sum(1 for st, o, k, l in surv if o == "M"), "survivors_Mt": sum(1 for st, o, k, l in surv if o == "Mt"),
           "claims": [[list(st), o, k, l, dead] for (st, o), (k, l, dead) in sorted(claims.items())],
           "survivor_list": [[list(st), o, k, l] for st, o, k, l in sorted(surv)],
           "keys_touched": len(RECORD), "keys_lp_feasible": len(feas), "lp_calls": NLP[0], "lp_status": dict(STATUS),
           "lp_feasible_keys": sorted(list(k) for k in feas), "seconds": round(time.time() - t0)}
    json.dump(out, open(HERE / f"scan_{variant}.json", "w"))
    # ---- comparison with the recon scan
    R = json.load(open(RECON / f"scan_{variant}.json"))
    mine_s = {(tuple(st), o, k, l) for st, o, k, l in out["survivor_list"]}; rec_s = {(tuple(st), o, k, l) for st, o, k, l in R["survivor_list"]}
    mine_c = {(tuple(st), o): (k, l, dead) for st, o, k, l, dead in out["claims"]}; rec_c = {(tuple(st), o): (k, l, dead) for st, o, k, l, dead in R["claims"]}
    rec_feas = {tuple(k) for k in R["lp_feasible_keys"]}
    cmp = {"survivors_identical_with_kl": mine_s == rec_s, "survivors_mine_minus_recon": len(mine_s - rec_s), "survivors_recon_minus_mine": len(rec_s - mine_s),
           "claims_identical_kld": mine_c == rec_c, "claims_differing": sum(1 for c in mine_c if mine_c[c] != rec_c.get(c)),
           "lp_feasible_keys_identical": feas == rec_feas, "lp_feasible_mine_minus_recon": sorted(list(k) for k in feas - rec_feas)[:10],
           "lp_feasible_recon_minus_mine": sorted(list(k) for k in rec_feas - feas)[:10], "recon_survivors": R["survivors"], "recon_keys_lp_feasible": R["keys_lp_feasible"]}
    out["comparison"] = cmp
    json.dump(out, open(HERE / f"scan_{variant}.json", "w"))
    print(f"[{variant}] states {len(states)} claims {len(claims)} survivors {len(surv)} (M {out['survivors_M']}, Mt {out['survivors_Mt']}); "
          f"keys touched {len(RECORD)}, LP-feasible {len(feas)}, LP calls {NLP[0]} status {dict(STATUS)}; {time.time()-t0:.0f}s", flush=True)
    print(f"[{variant}] vs recon: {json.dumps(cmp)}", flush=True)
    return out


if __name__ == "__main__":
    for v in sys.argv[1:]:
        run_variant(v)
