#!/usr/bin/env python3
"""P7: which Y-forms Tr(alpha N^-1) (either polarity) can a GD10 tower circuit's inversion deliver at
gate level <= 7 as an XOR of its existing N-function signals (Kraft at level 7), and at what XOR cost?
Also: for the proportional pair (y5, y6), the cheapest pair of bases sharing 2 products whose Y-forms
are all reachable.

    yreach.py CIRCUIT
"""
import itertools, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s1lib as L  # noqa: E402
import bopt, bsel  # noqa: E402
core = L.core


def main():
    c = L.load(sys.argv[1]); n = c.n
    T, lg, la, base = bopt.base_front(c)
    Ys = [b[1] for b in base]
    # N-function signals of the inversion: AND level 1..3 cone, degree > 1 or N-affine, gate level 4..7
    co = []
    for j, (op, a, b) in enumerate(c.gates):
        if op in core.NONLINEAR_OPS and la[n + j] == 2:
            for o in (a, b):
                if L.deg(T[o]) == 2: co.append(T[o])
    key = [tuple((t >> x) & 1 for t in co) for x in range(256)]
    fib = {}
    for x in range(256): fib.setdefault(key[x], []).append(x)
    fibers = list(fib.values())
    isN = lambda t: all(len({(t >> x) & 1 for x in f}) == 1 for f in fibers)
    sig = {}
    for s in range(n, n + len(c.gates)):
        if 4 <= lg[s] <= 7 and la[s] <= 3 and isN(T[s]):
            t = T[s]
            if t not in sig or lg[s] < lg[sig[t]]: sig[t] = s
    sigs = sorted(sig.items(), key=lambda kv: lg[kv[1]])
    print('N-function signals at GL4-7:', len(sigs), 'by level', {l: sum(1 for t, s in sigs if lg[s] == l) for l in range(4, 8)})
    # target Y-forms: span of base (normalised f(0)=0), both polarities
    targets = {}
    for al in range(1, 16):
        t = 0
        for i in range(4):
            if (al >> i) & 1: t ^= Ys[i]
        targets[t] = al; targets[t ^ L.ONES] = al
    # enumerate Kraft-feasible XORs at level 7
    by = {l: [(t, s) for t, s in sigs if lg[s] == l] for l in range(4, 8)}
    reach = {}
    for t, s in sigs:
        if t in targets: reach.setdefault(targets[t], (0, [s]))
    for n7 in range(0, 2):
        for n6 in range(0, 3 - 2 * n7 if n7 == 0 else 1):
            pass
    cand = [(t, s, 2.0 ** (lg[s] - 7)) for t, s in sigs if lg[s] <= 6]
    # depth-first over subsets with Kraft <= 1 and size <= 5
    def dfs(i, acc, kr, used):
        if used and acc in targets:
            al = targets[acc]; cost = len(used) - 1
            if al not in reach or cost < reach[al][0]: reach[al] = (cost, list(used))
        if len(used) >= 5: return
        for k in range(i, len(cand)):
            t, s, w = cand[k]
            if kr + w <= 1 + 1e-9:
                used.append(s); dfs(k + 1, acc ^ t, kr + w, used); used.pop()
    dfs(0, 0, 0.0, [])
    for al in range(1, 16):
        r = reach.get(al)
        print('alpha %2d (weight %d): %s' % (al, bin(al).count('1'), 'cost %d XOR via %s' % (r[0], r[1]) if r else 'not reachable at GL7'))


if __name__ == '__main__':
    main()
