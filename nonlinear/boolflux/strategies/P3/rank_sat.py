#!/usr/bin/env python3
"""Bilinear rank of the bottom tensor T (Y(4) x X(8) -> O(8)) of an AD4 BP-family AES circuit, by SAT.

T[o][i][j] = coefficient of y_i x_j in output o (bottom.py coordinates: monomials are independent,
so this is exact).  Question: is T = sum_{k<R} u_k (x) v_k (x) w_k over GF(2)?
A YES gives R last-level products (u_k . Y) * (v_k . X) whose GF(2)-combinations are the outputs.

    rank_sat.py FILE R [--budget CONFLICTS] [--seed S] [--out sol.json]
"""
import json, sys, time
from pathlib import Path
from itertools import product
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT  # noqa
from pysat.solvers import Solver  # noqa


def tensor(c):
    T, la, lg, last, Ysig, B = BT.analyse(c)
    Yt = [T[s] for s in Ysig]; Xt = [T[i] for i in range(c.n)]
    mons = BT.monomials(Yt, Xt)
    MB = BT.Basis()
    for nm, t in mons: assert MB.add(t, nm)
    ny, nx = len(Yt), len(Xt)
    Ten = [[[0] * nx for _ in range(ny)] for _ in range(c.m)]
    const = []
    rest = []
    for o, s in enumerate(c.outputs):
        cb = MB.coords(T[s]); assert cb is not None
        names = [MB.names[k] for k in range(len(MB.names)) if cb >> k & 1]
        const.append(1 if '1' in names else 0)
        for nm in names:
            if nm == '1': continue
            if len(nm) == 4 and nm[0] == 'y' and nm[2] == 'x':
                Ten[o][int(nm[1])][int(nm[3])] = 1
            else:
                rest.append((o, nm))
    return Ten, const, rest, Ysig


class CNF:
    def __init__(self):
        self.n = 0; self.cl = []
    def var(self):
        self.n += 1; return self.n
    def AND(self, a, b):
        z = self.var(); self.cl += [[-z, a], [-z, b], [z, -a, -b]]; return z
    def XOR(self, a, b):
        z = self.var(); self.cl += [[-z, a, b], [-z, -a, -b], [z, -a, b], [z, a, -b]]; return z


def solve(Ten, R, budget=None, seed=0, sym=True):
    m = len(Ten); ny = len(Ten[0]); nx = len(Ten[0][0])
    F = CNF()
    u = [[F.var() for _ in range(ny)] for _ in range(R)]
    v = [[F.var() for _ in range(nx)] for _ in range(R)]
    w = [[F.var() for _ in range(m)] for _ in range(R)]
    for k in range(R):
        F.cl += [u[k][:], v[k][:], w[k][:]]
    p = [[[F.AND(u[k][i], v[k][j]) for j in range(nx)] for i in range(ny)] for k in range(R)]
    for o, i, j in product(range(m), range(ny), range(nx)):
        terms = [F.AND(p[k][i][j], w[k][o]) for k in range(R)]
        acc = terms[0]
        for t in terms[1:]:
            acc = F.XOR(acc, t)
        F.cl.append([acc] if Ten[o][i][j] else [-acc])
    if sym:   # u_k as 4-bit numbers, non-decreasing in k (lex, msb first)
        for k in range(R - 1):
            a, b = u[k], u[k + 1]
            # a <= b lexicographic: eq-prefix chain
            eq = None
            for i in range(ny):
                # if prefix equal then not (a_i=1 and b_i=0)
                if eq is None:
                    F.cl.append([-a[i], b[i]])
                else:
                    F.cl.append([-eq, -a[i], b[i]])
                e = F.var()  # e <-> (prefix eq and a_i == b_i)
                x = F.XOR(a[i], b[i])
                if eq is None:
                    F.cl += [[-e, -x], [e, x]]
                else:
                    F.cl += [[-e, eq], [-e, -x], [e, -eq, x]]
                eq = e
    s = Solver(name='cadical153', bootstrap_with=F.cl)
    t0 = time.time()
    if budget:
        s.conf_budget(budget); r = s.solve_limited()
    else:
        r = s.solve()
    dt = time.time() - t0
    sol = None
    if r:
        M = set(l for l in s.get_model() if l > 0)
        sol = [{'u': [int(x in M) for x in u[k]], 'v': [int(x in M) for x in v[k]], 'w': [int(x in M) for x in w[k]]}
               for k in range(R)]
    return r, dt, sol, F.n, len(F.cl)


def check(Ten, sol):
    m = len(Ten); ny = len(Ten[0]); nx = len(Ten[0][0])
    for o, i, j in product(range(m), range(ny), range(nx)):
        s = 0
        for t in sol: s ^= t['u'][i] & t['v'][j] & t['w'][o]
        if s != Ten[o][i][j]: return False
    return True


def main():
    a = sys.argv[1:]
    f, R = a[0], int(a[1])
    budget = int(a[a.index('--budget') + 1]) if '--budget' in a else None
    out = a[a.index('--out') + 1] if '--out' in a else None
    c = BT.load(f)
    Ten, const, rest, Ysig = tensor(c)
    print('non-bilinear output terms:', rest, 'const', const)
    r, dt, sol, nv, nc = solve(Ten, R, budget)
    print('R=%d result=%s time=%.1fs vars=%d clauses=%d' % (R, r, dt, nv, nc))
    if sol:
        assert check(Ten, sol)
        for t in sol: print(t)
        if out:
            Path(out).write_text(json.dumps({'file': f, 'R': R, 'Ysig': Ysig, 'const': const, 'sol': sol}))


if __name__ == '__main__':
    main()
