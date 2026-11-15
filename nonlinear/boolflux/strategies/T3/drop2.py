#!/usr/bin/env python3
"""T3: can a level-2 AND be dropped? Needed at level <= 2: the 3 Q functions Tr(w x^170) and all 255
Tr(c x^84) (any level-3 coordinate choice needs the whole 8-dim V-space). For each level-2 AND P_i:
dim of (needed + S1 + other A2) vs (S1 + other A2); also the 'kernel' of the mixed products: the
intersection span(S1 + A2) with N-quadratic forms.
    python3 drop2.py CIRCUIT"""
import itertools
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import load, metrics, ONES, _gpow, _bit_tables    # noqa: E402
from pairs import and_levels, Basis                                       # noqa: E402
from gf4basis import RT, QT                                               # noqa: E402

c = load(sys.argv[1]); n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
S1 = [ONES] + [t[s] for s in range(NS) if al[s] <= 1]
A2 = [g for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 2]
need = [RT[1 << i] for i in range(8)] + sorted(set(QT[w] for w in range(1, 256)))[:0]
Qs = list({QT[w] for w in range(1, 256)})
need += Qs
print(metrics(c), 'S1 dim', Basis(S1).gens.__len__(), 'A2', len(A2), 'needed', len(need))
full = Basis(S1 + [t[g] for g in A2])
print('needed in S:', all(full.reduce(v) == 0 for v in need), 'dim S', len(full.gens))
for i, g in enumerate(A2):
    W = Basis(S1 + [t[h] for h in A2 if h != g])
    miss = sum(1 for v in need if W.reduce(v) != 0)
    a, b = c.gates[g - n][1:]
    print('drop s%d: needed functions outside span = %d' % (g, miss))
# N-quadratic forms inside S beyond S1
Nt = Basis([v for v in _bit_tables(lambda x: _gpow(x, 17)) if v not in (0, ONES)]).gens
NQ = [Nt[i] & Nt[j] for i, j in itertools.combinations(range(4), 2)]
B1 = Basis(S1)
nq_in_S1 = [B1.reduce(q) == 0 for q in NQ]
print('N-quadratic monomials in S1:', nq_in_S1)
# dimension of span(S1 + mixed A2 only) intersect span(S1 + NQ)
pureN = [g for g in A2 if Basis(S1 + NQ).reduce(t[g]) == 0]
mixed = [g for g in A2 if g not in pureN]
print('pure-N level-2 ANDs:', pureN, 'mixed:', len(mixed))
Bm = Basis(S1 + [t[g] for g in mixed])
k = sum(1 for q in NQ if Bm.reduce(q) == 0)
dimSm = len(Bm.gens); dimSmNQ = len(Basis(S1 + [t[g] for g in mixed] + NQ).gens); dimS1NQ = len(Basis(S1 + NQ).gens)
print('dim(S1+mixed) %d, dim(S1+NQ) %d, dim(S1+mixed+NQ) %d -> dim of N-quadratic part inside S1+mixed = %d' % (
    dimSm, dimS1NQ, dimSmNQ, dimSm + dimS1NQ - dimSmNQ - len(B1.gens)))
