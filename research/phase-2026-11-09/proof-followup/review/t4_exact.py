#!/usr/bin/env python3
"""Task 4 (grade): for the sampled 'step S (LP)' leaves, re-run the reviewer's count DFS (t4_stepS logic) collecting every
LP decision 'status 2' it relies on, and replace each by an EXACT Farkas certificate (lambda >= 0 integer,
lambda^T A' >= 0 on every column, lambda^T b' < 0, checked in integer arithmetic on the checker's matrix plus the count rows).
usage: t4_exact.py "(key)" a d"""
import sys, json, time
from fractions import Fraction
from math import lcm
from collections import Counter
import numpy as np
from scipy.optimize import linprog
import rcheck

key = eval(sys.argv[1]); a = int(sys.argv[2]); d = int(sys.argv[3])
R = rcheck.Rows(key, a, d)
b0, cols, *_ = rcheck.CC.matrix(tuple(key), ('eq', a), d)
Aint = [[int(c[i]) for c in [col for _, col in cols]] for i in range(len(b0))]   # rows x cols, exact integers
bint = [int(x) for x in b0]
ncol = len(cols)
CL = [(r, u) for r in range(4) for u in range(1, 4)]
present = [c for c in CL if c in R.cls]


def system(counts, exact):
    rows = [list(r) for r in Aint]; rhs = list(bint)
    for c in present:
        n = counts.get(c, 0)
        if not exact and c not in counts: continue
        ind = [0] * ncol
        for j in R.cls[c]: ind[j] = 1
        rows.append([-x for x in ind]); rhs.append(-n)
        if exact: rows.append(ind); rhs.append(n)
    return rows, rhs


def certify(counts, exact):
    rows, rhs = system(counts, exact)
    M = np.array(rows, float); bb = np.array(rhs, float); m = len(rows)
    # find lambda >= 0: M^T lambda >= 0, b^T lambda <= -1, min sum lambda
    res = linprog(np.ones(m), A_ub=np.vstack([-M.T, bb[None, :]]), b_ub=np.concatenate([np.zeros(ncol), [-1.0]]), bounds=[(0, None)] * m, method='highs')
    if res.status != 0: return False, f'dual status {res.status}'
    for den in (10**4, 10**6, 10**9):
        lam = [max(Fraction(0), Fraction(x).limit_denominator(den)) for x in res.x]
        L = 1
        for f in lam: L = lcm(L, f.denominator)
        li = [int(f * L) for f in lam]
        okc = all(sum(li[i] * rows[i][j] for i in range(m) if li[i]) >= 0 for j in range(ncol))
        val = sum(li[i] * rhs[i] for i in range(m) if li[i])
        if okc and val < 0: return True, dict(nnz=sum(1 for x in li if x), max=max(li), rhs=val)
    return False, 'rounding failed'


decisions = []


def struct_ok(c, final):
    n3 = sum(v for (r, u), v in c.items() if r == 3); A = sum(u * v for (r, u), v in c.items() if r == 3)
    if A > a or n3 > a: return False
    nu3 = sum(v for (r, u), v in c.items() if u == 3); nu2 = sum(v for (r, u), v in c.items() if u == 2)
    if nu3 > 1 or nu2 > 3 or (nu3 and nu2): return False
    if final and A != a: return False
    return True


feas = []


def dfs(j, c):
    if struct_ok(c, True):
        st = R.lp(dict(c), True)
        if st == 2: decisions.append((dict(c), True))
        else: feas.append(dict(c))
    for k in range(j, len(present)):
        c2 = Counter(c); c2[present[k]] += 1
        if not struct_ok(c2, False): continue
        st = R.lp(dict(c2), False)
        if st == 2: decisions.append((dict(c2), False)); continue
        dfs(k, c2)


t0 = time.time()
dfs(0, Counter())
ok = 0; bad = []
for c, ex in decisions:
    good, info = certify(c, ex)
    if good: ok += 1
    else: bad.append(({f'{r},{u}': v for (r, u), v in c.items()}, ex, info))
print(json.dumps(dict(key=list(key), a=a, d=d, lp_infeasible_decisions=len(decisions), exactly_certified=ok, uncertified=bad[:5],
                      n_uncertified=len(bad), exact_feasible_vectors=len(feas), seconds=round(time.time() - t0, 1))), flush=True)
