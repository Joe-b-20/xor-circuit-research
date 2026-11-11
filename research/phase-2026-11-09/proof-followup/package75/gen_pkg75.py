#!/usr/bin/env python3
"""Exact certificates at G = 75 for the claims that the PACKAGE rows (L1)-(L23) alone exclude.

The package (lower-bound-proofs/mixcolumns-lb75) ships exact Farkas certificates for G = 74 only; at G = 75 its own LP
model leaves 1,508 of the 7,416 oriented claims open and excludes 5,908 by LP status.  This script repeats the package's
generator (certify75.generate) with the scalar domain of G = 75 (lp_regen.scalar_states(75), the same formulas with G = 75):
for every key the walk needs, an LP-infeasible local system (certify75.system(key), which does not depend on G) gets a
nonnegative integer Farkas vector, checked exactly by certify75.check_certificate.  A claim is recorded as EXCLUDED when
its bounds satisfy k > Se or l > So or k + l > budget, otherwise as OPEN.  Nothing here says that the framework applies
at G = 75; that is a mathematical obligation listed in OBLIGATIONS-76.md.  Output: CERTIFICATES_PKG75_G75.json.
"""
import json, sys, importlib.util, time
from fractions import Fraction
from math import comb, lcm, gcd
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
HERE = Path(__file__).resolve().parent
PKG = Path.home() / "xor-circuit-research/lower-bound-proofs/mixcolumns-lb75/source/lower_bounds/checks"


def load(name):
    spec = importlib.util.spec_from_file_location(name + "_pkg", PKG / (name + ".py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


C75 = load("certify75"); LR = load("lp_regen")
G = 75
certificates = {}; feasible = set(); failed = {}


def solve(key):
    """True if the key may be feasible (no certificate), False if it has an exact certificate or is directly excluded."""
    if C75.direct_exclusion(key): return False
    if key in certificates: return False
    if key in feasible: return True
    types, A, B, names = C75.system(key)
    if not types:
        feasible.add(key); return True            # no column: the walk treats it as feasible unless the package excludes it directly
    AA = np.array(A, float)
    res = linprog(np.zeros(len(A)), A_ub=-AA.T, b_ub=np.zeros(len(types)), A_eq=np.array([B], float), b_eq=[-1], bounds=(0, None), method="highs")
    if res.status == 2:
        feasible.add(key); return True
    if not res.success:
        failed[key] = "dual LP status %d" % res.status; feasible.add(key); return True
    for den in (10 ** 7, 10 ** 9, 10 ** 11):
        ws = [Fraction(float(w)).limit_denominator(den) for w in res.x]
        scale = lcm(*(w.denominator for w in ws)); ints = [int(w * scale) for w in ws]
        common = gcd(*ints) or 1; ints = [w // common for w in ints]
        try:
            C75.check_certificate(key, ints)
        except AssertionError:
            continue
        certificates[key] = ints
        return False
    failed[key] = "rationalisation failed"; feasible.add(key); return True


def first_possible(h, y, F, ori, least, greatest):
    for s in range(least, greatest + 1):
        for q in range(s + 1):
            z = s - q
            if 2 * h + y + z + comb(q, 2) < 32: continue
            if solve((h, y, F, ori, q, z)): return s
    return greatest + 1


def main():
    t0 = time.time()
    states = list(LR.scalar_states(G)); claims = []; n_open = 0
    for state in states:
        a, b, Y, V, he, ho, le, lo, Se, So, budget = state
        for ori, other in (("M", "Mt"), ("Mt", "M")):
            k = first_possible(he, Y, V, ori, le, min(Se, budget - lo))
            ell = lo
            if k <= Se and k + ell <= budget:
                ell = first_possible(ho, V, Y, other, lo, min(So, budget - k))
            dead = k > Se or ell > So or k + ell > budget
            n_open += not dead
            claims.append({"state": list(state), "orientation": ori, "lower_even": k, "lower_odd": ell, "excluded": bool(dead)})
    out = {"gates": G, "rows": "package rows (L1)-(L23) only, certify75.system", "scalar_states": len(states), "claims": claims,
           "excluded": sum(c["excluded"] for c in claims), "open": n_open,
           "certificates": [{"key": list(k), "weights": w} for k, w in sorted(certificates.items())],
           "uncertified_keys": [[list(k), v] for k, v in sorted(failed.items())], "seconds": round(time.time() - t0)}
    json.dump(out, open(HERE / "CERTIFICATES_PKG75_G75.json", "w"), separators=(",", ":"))
    print(f"G = {G}: states {len(states)}, claims {len(claims)}, excluded {out['excluded']}, open {n_open}, certificates {len(certificates)}, "
          f"LP-feasible keys {len(feasible)}, uncertified {len(failed)}, {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
