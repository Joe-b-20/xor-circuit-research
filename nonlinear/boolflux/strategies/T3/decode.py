#!/usr/bin/env python3
"""T3: decode an AD3 circuit in intrinsic coordinates.
N bits: x^17 (in GF(2^8) poly basis 0x11B, 4 nonzero coordinate functions spanning the subfield image).
For each AND at level 2 and 3: operands written in span{1, x_i, n_j, n_j n_k, n_j x_i} when possible.
    python3 decode.py CIRCUIT"""
import itertools
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                               # noqa: E402
from boolflux.hub.common import load, metrics, _gpow, _bit_tables, ONES   # noqa: E402
from pairs import and_levels, Basis                     # noqa: E402
from prodswap import RBasis                             # noqa: E402

X = core.input_tables(8)
Nt = [v for v in _bit_tables(lambda x: _gpow(x, 17)) if v not in (0, ONES)]
nb = Basis(Nt); Nb = nb.gens          # 4 independent N coordinate functions
assert len(Nb) == 4, len(Nb)
names = ['1'] + ['x%d' % i for i in range(8)] + ['n%d' % j for j in range(4)]
vecs = [ONES] + X + Nb
for j, k in itertools.combinations(range(4), 2):
    names.append('n%dn%d' % (j, k)); vecs.append(Nb[j] & Nb[k])
for j in range(4):
    for i in range(8):
        names.append('n%dx%d' % (j, i)); vecs.append(Nb[j] & X[i])
for j, k, l in itertools.combinations(range(4), 3):
    names.append('n%dn%dn%d' % (j, k, l)); vecs.append(Nb[j] & Nb[k] & Nb[l])
R = RBasis(vecs)


def show(v):
    r, m = R.reduce(v)
    # m is mask over R.gens indices (gens includes dependent vectors too, but reduce uses only pivots)
    terms = [names[i] for i in range(len(names)) if (m >> i) & 1]
    return ' + '.join(terms) + (' + RES' if r else '')


def main():
    c = load(sys.argv[1]); n = c.n; t = c.tables(); al = and_levels(c)
    print(metrics(c))
    for L in (1, 2, 3):
        print('--- level', L)
        for g in range(n, n + len(c.gates)):
            op, a, b = c.gates[g - n]
            if op != 8 or al[g] != L: continue
            print('s%d = AND(s%d, s%d):  [%s]  x  [%s]' % (g, a, b, show(t[a]), show(t[b])))
    print('--- outputs')
    for k, s in enumerate(c.outputs):
        print('y%d' % k, show(t[s])[:200])


if __name__ == '__main__':
    main()
