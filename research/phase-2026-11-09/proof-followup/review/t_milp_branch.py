#!/usr/bin/env python3
"""Exact branch-and-bound proof of integer infeasibility (R8-int) for the one MILP-load-bearing count vector found:
leaf (15,4,1,'Mt',3,1) A=1 qD=0, counts {(3,1):1, (1,2):2, (2,1):4}.  Every leaf of the branching tree carries an exact
Farkas certificate (integers, checked in exact arithmetic); branching on the most fractional variable of the LP solution.
Every variable is a nonnegative integer (helper counts, gate counts, sums of integers f_l), as R8-int asserts."""
import sys, json, math
from fractions import Fraction
from math import lcm
import numpy as np
from scipy.optimize import linprog
import rcheck

key = (15, 4, 1, 'Mt', 3, 1); a, d = 1, 0
counts = {(3, 1): 1, (1, 2): 2, (2, 1): 4}
if len(sys.argv) > 1:
    J = json.loads(sys.argv[1]); key = tuple(J['key']); a = J['a']; d = J['d']; counts = {tuple(map(int, k.split(','))): v for k, v in J['counts'].items()}
R = rcheck.Rows(key, a, d)
b0, cols, *_ = rcheck.CC.matrix(key, ('eq', a), d)
n = len(cols)
rows = [[int(col[i]) for _, col in cols] for i in range(len(b0))]; rhs = [int(x) for x in b0]
for c in [(r, u) for r in range(4) for u in range(1, 4)]:
    if c not in R.cls:
        assert counts.get(c, 0) == 0
        continue
    ind = [0] * n
    for j in R.cls[c]: ind[j] = 1
    rows.append(ind); rhs.append(counts.get(c, 0)); rows.append([-x for x in ind]); rhs.append(-counts.get(c, 0))
labels = [lab for lab, _ in cols]


def certify(rw, rh):
    M = np.array(rw, float); bb = np.array(rh, float); m = len(rw)
    du = linprog(np.ones(m), A_ub=np.vstack([-M.T, bb[None, :]]), b_ub=np.concatenate([np.zeros(n), [-1.0]]), bounds=[(0, None)] * m, method='highs')
    if du.status != 0: return False
    for den in (10**4, 10**6, 10**9):
        lam = [max(Fraction(0), Fraction(x).limit_denominator(den)) for x in du.x]
        L = 1
        for f in lam: L = lcm(L, f.denominator)
        li = [int(f * L) for f in lam]
        if all(sum(li[i] * rw[i][j] for i in range(m) if li[i]) >= 0 for j in range(n)) and sum(li[i] * rh[i] for i in range(m) if li[i]) < 0:
            return True
    return False


stats = dict(nodes=0, certified_leaves=0, uncertified=0, integral=0)
stack = [([], [])]
while stack and stats['nodes'] < 5000:
    extra_r, extra_b = stack.pop(); stats['nodes'] += 1
    rw = rows + extra_r; rh = rhs + extra_b
    res = linprog(np.zeros(n), A_ub=np.array(rw, float), b_ub=np.array(rh, float), bounds=[(0, None)] * n, method='highs')
    if res.status == 2:
        if certify(rw, rh): stats['certified_leaves'] += 1
        else: stats['uncertified'] += 1
        continue
    if res.status != 0: stats['uncertified'] += 1; continue
    x = res.x
    frac = [(abs(v - round(v)), j) for j, v in enumerate(x) if abs(v - round(v)) > 1e-7]
    if not frac:
        xi = [int(round(v)) for v in x]
        ok = all(sum(rw[i][j] * xi[j] for j in range(n)) <= rh[i] for i in range(len(rw)))
        if ok: stats['integral'] += 1; print('INTEGER SOLUTION', {str(labels[j]): xi[j] for j in range(n) if xi[j]}); break
        stats['uncertified'] += 1; continue
    _, j = max(frac); print("branch on", labels[j], "LP value", round(x[j], 6))
    t = math.floor(x[j])
    e = [0] * n; e[j] = 1
    stack.append((extra_r + [e], extra_b + [t]))                       # x_j <= floor
    stack.append((extra_r + [[-v for v in e]], extra_b + [-(t + 1)]))   # x_j >= floor + 1
stats['open_at_stop'] = len(stack)
print(json.dumps(dict(key=list(key), a=a, d=d, counts={f'{r},{u}': v for (r, u), v in counts.items()}, **stats,
                      proved_integer_infeasible=(not stack and stats['uncertified'] == 0 and stats['integral'] == 0))))
