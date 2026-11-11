#!/usr/bin/env python3
"""farkas_q3.py -- exact Farkas certificates for every LP decision "infeasible" (status 2) that step S of enum_q3.py used.

Each leaf file records the pruned count vectors (counts {(r,u): n}, exact flag).  For each, the system is
    A n <= b  (the combined case system S(K,a,d), check_combined75.matrix)   plus   count rows
    -sum_v n_(r,u,v) <= -c_(r,u)  for every class in counts  [and  sum_v n_(r,u,v) <= c_(r,u) for all 12 classes if exact].
A certificate is lambda >= 0 with lambda^T A' >= 0 on every column and lambda^T b' < 0 (section 11 of PROOF.md).  We solve the
dual LP  min sum(lambda)  s.t.  lambda^T A' >= 0,  lambda^T b' <= -1,  lambda >= 0  (HiGHS), rationalise lambda with
Fraction.limit_denominator, scale to integers and CHECK the two conditions in exact integer arithmetic.  Only exact
successes are counted.  Output: farkas_q3.json (per leaf: vectors, certified, failed).  [certified] for the successes.
usage: python3 farkas_q3.py [results_dir]
"""
import sys, json, glob, time
from fractions import Fraction
from math import lcm
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import enum_q3 as E


def certify(lp, counts, exact):
    classes = lp.classes
    rows = [lp.A]; rhs = [lp.b]; names = ["sys"] * lp.A.shape[0]
    extra_rows = []; extra_rhs = []
    for c, n in counts.items():
        if c not in lp.ind:
            return dict(ok=n == 0, reason="deleted type with positive count" if n else "zero count on deleted type", cert=None)
        extra_rows.append(-lp.ind[c]); extra_rhs.append(-n)
        if exact: extra_rows.append(lp.ind[c]); extra_rhs.append(n)
    if exact:
        for c in classes:
            if c not in counts: extra_rows.append(lp.ind[c]); extra_rhs.append(0)
    A = np.vstack([lp.A] + extra_rows); b = np.concatenate([lp.b, np.array(extra_rhs, float)])
    m, ncol = A.shape
    # dual LP: lambda >= 0, -A^T lambda <= 0 (i.e. lambda^T A >= 0), b^T lambda <= -1, minimise sum lambda
    res = linprog(np.ones(m), A_ub=np.vstack([-A.T, b.reshape(1, -1)]), b_ub=np.concatenate([np.zeros(ncol), [-1.0]]), bounds=(0, None), method="highs")
    if res.status != 0: return dict(ok=False, reason=f"dual LP status {res.status}", cert=None)
    lam = res.x
    Aint = [[int(round(x)) for x in row] for row in A]; bint = [int(round(x)) for x in b]
    assert all(abs(x - round(x)) < 1e-9 for row in A for x in row) and all(abs(x - round(x)) < 1e-9 for x in b)
    for denom in (1, 2, 3, 4, 6, 8, 12, 24, 48, 96, 1000, 10 ** 4, 10 ** 6):
        fr = [Fraction(float(x)).limit_denominator(denom) if x > 1e-12 else Fraction(0) for x in lam]
        L = 1
        for f in fr: L = lcm(L, f.denominator)
        w = [int(f * L) for f in fr]
        if any(x < 0 for x in w): continue
        wb = sum(wi * bi for wi, bi in zip(w, bint))
        if wb >= 0: continue
        if all(sum(w[i] * Aint[i][j] for i in range(m)) >= 0 for j in range(ncol)):
            return dict(ok=True, reason="exact", cert=w, wrhs=wb, denominator=L)
    return dict(ok=False, reason="rationalisation failed", cert=None)


def main(results_dir):
    t0 = time.time(); out = {}; tot = 0; okc = 0; fails = []
    for fn in sorted(glob.glob(str(Path(results_dir) / "leaf_*.json"))):
        r = json.load(open(fn)); key = tuple(r["key"]); a = r["A"]; d = r["qD"]
        lp = E.LeafLP(key, a, d)
        vecs = r.get("lp_pruned_vectors", [])
        res = []
        for cv, ex in vecs:
            counts = {tuple(c): n for c, n in cv}
            c = certify(lp, counts, ex); tot += 1; okc += c["ok"]
            if not c["ok"]: fails.append((str(key), a, d, cv, ex, c["reason"]))
            res.append(dict(counts=[[list(c_), n] for c_, n in counts.items()], exact=ex, ok=c["ok"], reason=c["reason"], wrhs=c.get("wrhs"), nz=sum(1 for x in (c.get("cert") or []) if x)))
        out[f"{key} A={a} qD={d}"] = dict(vectors=len(vecs), certified=sum(1 for x in res if x["ok"]), detail=res)
        print(f"{key} A={a} qD={d}: {len(vecs)} pruned vectors, {sum(1 for x in res if x['ok'])} certified exactly  ({time.time()-t0:.0f}s)", flush=True)
    summ = dict(total_pruned_vectors=tot, certified=okc, failed=len(fails), failures=fails[:50], seconds=round(time.time() - t0))
    json.dump(dict(summary=summ, leaves=out), open(HERE / "farkas_q3.json", "w"))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(HERE / "results"))
