"""AD3 GF(4)-norm route, level 2 over a FIXED level 1 (taken from a circuit file whose level-1
products span N = x^17): simulated annealing over k members (lam, gamma) and p N-products,
score = deficit = dim(E + M + T) - dim(E + M), E = span(1, x, N, L1).  A zero-deficit state
gives an AD3 circuit with l1 + k + p + 12 ANDs (built by ad3build.py).

usage: ad3fix.py L1FILE --k K --p P --seconds S --seed S [--restarts R] [--out JSONL]
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time

import cover1
import ad3mem as A
from ad3sat import XT, NT, ADJ, N4T, basis_of, level_tables
from h4lib import ONES

GOOD = [(1, 8), (2, 7), (3, 15), (4, 10), (5, 2), (6, 13), (7, 5), (8, 9), (9, 1), (10, 14),
        (11, 6), (12, 3), (13, 11), (14, 4), (15, 12)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('l1file')
    ap.add_argument('--k', type=int, default=9); ap.add_argument('--p', type=int, default=3)
    ap.add_argument('--seconds', type=float, default=60); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--restarts', type=int, default=1)
    ap.add_argument('--single', action='store_true', help='one gamma for all members')
    ap.add_argument('--out', default=None)
    ap.add_argument('--T0', type=float, default=0.5)
    ap.add_argument('--all', action='store_true', help='keep restarting after a zero-deficit state')
    ap.add_argument('--extra', type=int, default=0, help='movable extra level-1 slots (x-form products)')
    a = ap.parse_args()
    L1 = level_tables(a.l1file, 1)
    Erows = cover1.rowspace([ONES] + XT + A.Nb + L1)
    assert all(cover1.reduce(t, Erows) == 0 for t in NT), 'N not in span(1, x, L1)'
    Tq = basis_of([cover1.reduce(t, Erows) for t in ADJ + [t for t in N4T if t]])
    rnd = random.Random(a.seed)
    cache = {}

    def mv(m):
        if m not in cache:
            if m[0] == 'n': cache[m] = cover1.reduce(A.nprod(m[1], m[2]), Erows)
            elif m[0] == 'x': cache[m] = cover1.reduce(A.lin(m[1], XT) & A.lin(m[2], XT), Erows)
            else: cache[m] = cover1.reduce(A.member(m[1], m[2]), Erows)
        return cache[m]

    def deficit(state):
        vec = [mv(m) for m in state]
        r = len(cover1.rowspace(vec))
        return len(cover1.rowspace(vec + Tq)) - r
    g_single = rnd.choice(GOOD)

    def rmem():
        return ('m', rnd.randrange(1, 256), g_single if a.single else rnd.choice(GOOD))

    def rn():
        x, y = rnd.sample(range(1, 16), 2); return ('n', x, y)
    k, p = a.k, a.p
    ex = a.extra

    def rx():
        while True:
            l, m = rnd.randrange(1, 256), rnd.randrange(1, 256)
            if l != m: return ('x', l, m)
    overall = None
    for rep in range(a.restarts):
        state = [rmem() for _ in range(k)] + [rn() for _ in range(p)] + [rx() for _ in range(ex)]
        cur = deficit(state); best = (cur, list(state))
        t0 = time.time(); secs = a.seconds / a.restarts; steps = 0
        while time.time() - t0 < secs and best[0] > 0:
            steps += 1
            ns = list(state); j = rnd.randrange(k + p + ex)
            if j >= k + p:
                m = ns[j]
                if rnd.random() < 0.5: ns[j] = rx()
                else:
                    l2, m2 = m[1] ^ (1 << rnd.randrange(8)), m[2]
                    if rnd.random() < 0.5: l2, m2 = m[1], m[2] ^ (1 << rnd.randrange(8))
                    ns[j] = ('x', l2, m2) if l2 and m2 and l2 != m2 else rx()
            elif j >= k: ns[j] = rn()
            else:
                m = ns[j]; u = rnd.random()
                if u < 0.4: ns[j] = ('m', (m[1] ^ (1 << rnd.randrange(8))) or 1, m[2])
                elif u < 0.6 and not a.single: ns[j] = ('m', m[1], rnd.choice(GOOD))
                else: ns[j] = rmem()
            s = deficit(ns)
            temp = a.T0 * (1 - (time.time() - t0) / secs) + 0.05
            if s <= cur or rnd.random() < math.exp((cur - s) / temp):
                state, cur = ns, s
                if s < best[0]: best = (s, list(ns))
        res = {'l1file': a.l1file, 'l1': len(L1) + ex, 'extra': ex, 'k': k, 'p': p, 'seed': a.seed, 'rep': rep,
               'steps': steps, 'deficit': best[0], 'state': best[1],
               'total_if_0': len(L1) + ex + k + p + 12}
        print(json.dumps(res), flush=True)
        if a.out:
            with open(a.out, 'a') as fh: fh.write(json.dumps(res) + chr(10))
        if overall is None or best[0] < overall: overall = best[0]
        if best[0] == 0 and not a.all: break


if __name__ == '__main__':
    main()
