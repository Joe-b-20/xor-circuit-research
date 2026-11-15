#!/usr/bin/env python3
"""P2: simulated annealing in the bsat3 model (one product per alpha class per output).

State: for every output k and x-coordinate q a vector v_{k,q} in GF(2)^15 (classes = nonzero alpha
coordinate vectors) with sum_alpha v_{k,q}[alpha] alpha = column q of M_k.  m_{alpha,k} = bits
(v_{k,q}[alpha])_q.  Moves: add a weight-3 kernel vector {a, b, a^b} at one (k, q) (these span the
kernel).  Cost: BIG * sum_k max(0, K_k - 1) + #distinct (alpha, m != 0) [+ eps * incidence].
K_k = sum_{alpha: m_{alpha,k} != 0} 2^(1 + lev(alpha) - D).

    python3 sa3.py FRONT D OUT.jsonl [--seconds T] [--seed S] [--T0 t] [--target P]
Writes every state with Kraft OK and #products <= target (and new best) as a decomposition.
"""
import argparse
import json
import math
import random
import sys
import time
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bil    # noqa: E402
import ylev   # noqa: E402
import orbit as O   # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('front'); ap.add_argument('D', type=int); ap.add_argument('out')
    ap.add_argument('--seconds', type=float, default=600); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--T0', type=float, default=1.0); ap.add_argument('--target', type=int, default=18)
    ap.add_argument('--big', type=float, default=8.0); ap.add_argument('--period', type=int, default=200000)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    F = ylev.front(ylev.load(a.front))
    lev = {v: F['levels'][v][0] for v in range(1, 16)}
    Wt = {v: 2.0 ** (1 + lev[v] - a.D) for v in lev}
    triples = [(x, y, x ^ y) for x in range(1, 16) for y in range(x + 1, 16) if (x ^ y) > y]
    # initial: each output in the cheapest basis representation: choose 4 lightest independent classes
    order = sorted(range(1, 16), key=lambda v: lev[v])
    basis = []; span = {0}
    for v in order:
        if v not in span:
            basis.append(v); span = span | {s ^ v for s in span}
        if len(basis) == 4: break
    # solve column q: coordinates of column vector (4 bits, p = alpha coordinate) in basis
    def solve(col):
        # find s subset of basis with XOR = col
        for msk in range(16):
            x = 0
            for i in range(4):
                if (msk >> i) & 1: x ^= basis[i]
            if x == col: return [basis[i] for i in range(4) if (msk >> i) & 1]
        raise ValueError
    m = [[0] * 16 for _ in range(8)]       # m[k][v] = 8-bit functional (bit q = GMASK index q)
    for k in range(8):
        for q in range(8):
            col = sum(bil.M[k][p][q] << p for p in range(4))
            for v in solve(col): m[k][v] ^= 1 << q
    cnt = [Counter() for _ in range(16)]
    for k in range(8):
        for v in range(1, 16):
            if m[k][v]: cnt[v][m[k][v]] += 1
    def kraft(k): return sum(Wt[v] for v in range(1, 16) if m[k][v])
    K = [kraft(k) for k in range(8)]
    nprod = sum(len(cnt[v]) for v in range(1, 16))
    exc = sum(max(0.0, x - 1.0) for x in K)
    cost = a.big * exc + nprod
    out = open(a.out, 'a')
    T0 = time.time(); it = 0; best = None; seen = set()

    def snapshot():
        prods = {}
        for k in range(8):
            for v in range(1, 16):
                if m[k][v]:
                    g = sum(bil.GMASK[q] for q in range(8) if (m[k][v] >> q) & 1)
                    key = (bil.ALPHA[v], g); prods[key] = prods.get(key, 0) | (1 << (7 - k))
        return [(al, g, O.w_of(cv)) for (al, g), cv in prods.items()]

    while time.time() - T0 < a.seconds:
        it += 1
        T = a.T0 * (1.0 - ((it % a.period) / a.period)) + 0.02
        k = rng.randrange(8); q = rng.randrange(8); tri = rng.choice(triples)
        # apply
        old = [m[k][v] for v in tri]
        for v in tri:
            if m[k][v]: cnt[v][m[k][v]] -= 1; (cnt[v][m[k][v]] == 0) and cnt[v].pop(m[k][v])
            m[k][v] ^= 1 << q
            if m[k][v]: cnt[v][m[k][v]] += 1
        nK = kraft(k)
        nn = sum(len(cnt[v]) for v in range(1, 16))
        nexc = exc - max(0.0, K[k] - 1.0) + max(0.0, nK - 1.0)
        ncost = a.big * nexc + nn
        d = ncost - cost
        if d <= 0 or rng.random() < math.exp(-d / T):
            K[k] = nK; exc = nexc; cost = ncost; nprod = nn
            if best is None or (exc, nprod) < best:
                best = (exc, nprod)
                print('%.1fs it %d exc %.3f nprod %d K %s' % (time.time() - T0, it, exc, nprod, [round(x, 3) for x in K]), flush=True)
            if exc <= 1e-9 and nprod <= a.target:
                dec = snapshot(); key = tuple(sorted(dec))
                if key not in seen:
                    seen.add(key)
                    ok = O.check(dec)
                    print('FOUND D=%d nprod %d check %s' % (a.D, len(dec), ok), flush=True)
                    out.write(json.dumps({'D': a.D, 'P': len(dec), 'check': ok, 'dec': dec, 'K': K,
                                          'front': a.front, 'seed': a.seed}) + '\n'); out.flush()
        else:
            for v, o in zip(tri, old):
                if m[k][v]: cnt[v][m[k][v]] -= 1; (cnt[v][m[k][v]] == 0) and cnt[v].pop(m[k][v])
                m[k][v] = o
                if o: cnt[v][o] += 1
    print('end best', best, 'found', len(seen), flush=True)


if __name__ == '__main__':
    main()
