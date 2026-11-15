#!/usr/bin/env python3
"""T4: one extra x-junk AND t (a rank-2 form) that upgrades two outputs at once.
Given the span G of built x-junk ANDs (constituents of basis outputs, PAIRING), for outputs k, l and
2-product designs dk, dl (p2, any pairing): t must satisfy r_k(dk), r_l(dl) in span(S1, G, t), i.e.
r_k + r_l in span(S1, G) and t in r_k + span(S1, G) with rank(t) = 2 (exhaustive over the coset).
    python3 onemore.py FRONT BASIS(comma) [PAIRING]"""
import sys, itertools, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import load, analyse  # noqa
from xjunk import decompose  # noqa
from chain import lin, wedge, qform, Red, PAIRS  # noqa

DES2 = [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]


def altrank(w):
    """rank of the alternating 8x8 matrix of a 28-bit wedge vector"""
    M = [0] * 8
    for r, (a, b) in enumerate(PAIRS):
        if (w >> r) & 1: M[a] |= 1 << b; M[b] |= 1 << a
    rk = 0; rows = M[:]
    for col in range(8):
        piv = next((i for i in range(rk, 8) if (rows[i] >> col) & 1), None)
        if piv is None: continue
        rows[rk], rows[piv] = rows[piv], rows[rk]
        for i in range(8):
            if i != rk and (rows[i] >> col) & 1: rows[i] ^= rows[rk]
        rk += 1
    return rk


c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
basis = [int(x) for x in sys.argv[2].split(',')]
pair = sys.argv[3] if len(sys.argv) > 3 else '02-13'
PAIR = tuple(tuple(int(ch) for ch in p) for p in pair.split('-'))
outs = decompose(c, T, la, ba, 4)
ys = sorted({y for d in outs for y in d})
W = [[lin(outs[k].get(y, 0)) for y in ys] for k in range(8)]
S1forms = [qform(T[s]) for s in fa if la[s] == 1]
G = [wedge(W[k][a], W[k][b]) for k in basis for a, b in PAIR]
SG = Red(S1forms + G)
print('dim S1+G', len(SG.p), flush=True)
# span basis vectors of S1+G (as list) for coset enumeration
gens = list(SG.p.values())
def q(k, d):
    r = 0
    for a, b in d: r ^= wedge(W[k][a], W[k][b])
    return r
found = []
others = [k for k in range(8) if k not in basis]
for k, l in itertools.combinations(others, 2):
    for dk in DES2:
        for dl in DES2:
            rk, rl = q(k, dk), q(l, dl)
            if SG.red(rk ^ rl) != 0: continue
            # search t in rk + span(S1 + G) with rank 2 (2^dim elements)
            n = len(gens)
            if n > 20: print('span too big', n); continue
            hit = None
            for mask in range(1 << n):
                t = rk
                for i in range(n):
                    if (mask >> i) & 1: t ^= gens[i]
                if t and altrank(t) == 2: hit = t; break
            rec = {'k': k, 'l': l, 'dk': dk, 'dl': dl, 'rank2_t': hit is not None}
            print(json.dumps(rec), flush=True)
            if hit is not None: found.append(rec)
print('found', len(found))
