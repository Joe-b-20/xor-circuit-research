#!/usr/bin/env python3
"""T3: exact XOR count of the bottom layer (outputs from the last-level AND products) by SAT.

Targets: the 8 outputs as GF(2) vectors over the level-3 products (constants dropped: XNOR is free on
the last gate). Question: is there an XOR straight-line program with k gates (2-input XOR, operands =
products or earlier gates) computing all targets? Optional gate-depth limit: product arrival levels are
taken from the circuit, outputs must have level <= cap.  [C] for: this target matrix, XOR/XNOR gates only,
no use of other signals.
    python3 bottomsat.py CIRCUIT --k 14 [--cap 26] [--timeout 300]
"""
import argparse
import itertools
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import load, metrics, ONES       # noqa: E402
from pairs import and_levels                              # noqa: E402
from prodswap import RBasis                               # noqa: E402
from pysat.solvers import Solver                          # noqa: E402
from pysat.card import CardEnc, EncType                   # noqa: E402


def matrix(c):
    n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
    L = max(al[s] for s in c.outputs)
    prods = [g for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == L]
    lv = [0] * n
    for op, a, b in c.gates: lv.append(1 + max(lv[a], lv[b]))
    R = RBasis([ONES] + [t[p] for p in prods])
    rows = []
    for o in c.outputs:
        r, m = R.reduce(t[o]); assert r == 0
        rows.append(m >> 1)
    return prods, [lv[p] for p in prods], rows


def solve(rows, nin, k, arr=None, cap=None, timeout=300, solver='cd19'):
    top = [0]
    def nv():
        top[0] += 1; return top[0]
    cl = []
    nb = nin
    val = {}          # (signal, bit) -> var ; inputs are constants
    for j in range(nin, nin + k):
        for r in range(nb): val[(j, r)] = nv()
    sel = {}
    for j in range(nin, nin + k):
        prs = list(itertools.combinations(range(j), 2))
        vs = []
        for (s, u) in prs:
            x = nv(); sel[(j, s, u)] = x; vs.append(x)
        enc = CardEnc.equals(lits=vs, bound=1, top_id=top[0], encoding=EncType.seqcounter)
        top[0] = max(top[0], enc.nv); cl += enc.clauses
        for (s, u) in prs:
            x = sel[(j, s, u)]
            for r in range(nb):
                def lit(sig):
                    if sig < nin: return None if sig != r else True
                    return val[(sig, r)]
                a = lit(s); b = lit(u); y = val[(j, r)]
                # y = a xor b, with constants folded
                av = [] if a is None else ([True] if a is True else [a])
                bv = [] if b is None else ([True] if b is True else [b])
                const = 0; vars_ = []
                for z in av + bv:
                    if z is True: const ^= 1
                    else: vars_.append(z)
                # y xor vars xor const = 0 under x
                if not vars_:
                    cl.append([-x, y] if const else [-x, -y])
                elif len(vars_) == 1:
                    v = vars_[0]
                    if const: cl += [[-x, y, v], [-x, -y, -v]]
                    else: cl += [[-x, -y, v], [-x, y, -v]]
                else:
                    v, w = vars_
                    for sy in (0, 1):
                        for sv in (0, 1):
                            for sw in (0, 1):
                                if (sy ^ sv ^ sw) != 0:   # forbidden assignment y=sy,v=sv,w=sw (y = v xor w)
                                    cl.append([-x, (-y if sy else y), (-v if sv else v), (-w if sw else w)])
    # outputs
    osel = []
    for m, row in enumerate(rows):
        ors = []
        for j in range(nin, nin + k):
            o = nv(); ors.append(o); osel.append((o, j))
            for r in range(nb):
                cl.append([-o, val[(j, r)] if (row >> r) & 1 else -val[(j, r)]])
        cl.append(ors)
    # depth
    if cap is not None and arr is not None:
        D = cap
        lvv = {}
        for j in range(nin, nin + k):
            for d in range(1, D + 2): lvv[(j, d)] = nv()     # level(j) >= d
            for d in range(2, D + 2): cl.append([-lvv[(j, d)], lvv[(j, d - 1)]])
            cl.append([lvv[(j, 1)]])
            for (s, u) in itertools.combinations(range(j), 2):
                x = sel[(j, s, u)]
                for z in (s, u):
                    if z < nin:
                        if arr[z] + 1 > D: cl.append([-x])
                        else: cl.append([-x, lvv[(j, arr[z] + 1)]])
                    else:
                        for d in range(1, D + 1): cl.append([-x, -lvv[(z, d)], lvv[(j, d + 1)]])
        for o, j in osel: cl.append([-o, -lvv[(j, D + 1)]])
    with Solver(name=solver, bootstrap_with=cl) as S:
        if cap is not None and arr is not None:
            pass
        t0 = time.time()
        res = S.solve_limited() if False else S.solve()
        return res, time.time() - t0, top[0], len(cl)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('--k', type=int, required=True)
    ap.add_argument('--cap', type=int)
    a = ap.parse_args()
    c = load(a.circuit)
    prods, arr, rows = matrix(c)
    print(metrics(c), 'bottom rows', [bin(r).count('1') for r in rows], 'arrivals', arr)
    res, dt, nvars, ncl = solve(rows, 12, a.k, arr, a.cap)
    print('k=%d cap=%s: %s (%.1fs, %d vars, %d clauses)' % (a.k, a.cap, 'SAT' if res else 'UNSAT', dt, nvars, ncl))


if __name__ == '__main__':
    main()
