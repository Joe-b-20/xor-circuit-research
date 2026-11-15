#!/usr/bin/env python3
"""T3: two-product exchanges at AND level 2 that keep every needed level-<=2 function.

For a pair (i, j) of level-2 ANDs let W = S1 + span{other 10 level-2 ANDs}. The needed functions
(3 Q's and the 8-dim V-space) span <P_i, P_j> mod W (drop2.py: each P is needed), so replacements
(P_i', P_j') work iff they represent two different nonzero classes of {P_i, P_j, P_i + P_j} mod W.
Operands are restricted to the structured forms c + l(N) + s(x) (l in the N-span, s x-linear) for both
a' and b' (exhaustive over a', b' solved by linear algebra). Reports, per pair and class, the number of
new products (not equal to P_i or P_j), and lists pairs where two different classes are both reachable
by a new product ('genuine 2-exchanges'). [C] for this operand form.
    python3 l2pair.py CIRCUIT OUT.json"""
import json
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                              # noqa: E402
from boolflux.hub.common import load, metrics, ONES, _gpow, _bit_tables  # noqa: E402
from pairs import and_levels, Basis                                    # noqa: E402
from prodswap import RBasis, gauss_solve, comb                         # noqa: E402

c = load(sys.argv[1]); n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
X = core.input_tables(8)
Nb = Basis([v for v in _bit_tables(lambda x: _gpow(x, 17)) if v not in (0, ONES)]).gens
S1 = Basis([ONES] + [t[s] for s in range(NS) if al[s] <= 1]); sg = S1.gens
A2 = [g for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 2]
F = []
for k in range(16):
    l = 0
    for j in range(4):
        if (k >> j) & 1: l ^= Nb[j]
    for m in range(256):
        s = 0
        for i in range(8):
            if (m >> i) & 1: s ^= X[i]
        if l ^ s: F.append(l ^ s)
Fset = set(F) | {f ^ ONES for f in F}
res = []; t0 = time.time()
for ii in range(len(A2)):
    for jj in range(ii + 1, len(A2)):
        gi, gj = A2[ii], A2[jj]
        W = RBasis(sg + [t[h] for h in A2 if h not in (gi, gj)])
        classes = {'Pi': W.reduce(t[gi])[0], 'Pj': W.reduce(t[gj])[0], 'Pi+Pj': W.reduce(t[gi] ^ t[gj])[0]}
        found = {k: [] for k in classes}
        for av in F:
            prods = [W.reduce(av & s)[0] for s in sg]
            for key, target in classes.items():
                r = gauss_solve(prods, target)
                if r is None: continue
                part, null = r
                if len(null) > 12: continue
                for k in range(1 << len(null)):
                    mm = part
                    for q, v in enumerate(null):
                        if (k >> q) & 1: mm ^= v
                    bv = comb(sg, mm)
                    if bv not in Fset: continue
                    P = av & bv
                    if S1.reduce(P ^ t[gi]) == 0 or S1.reduce(P ^ t[gj]) == 0: continue   # trivial (operand complement / S1 shift)
                    found[key].append((av, bv))
        nk = {k: len(v) for k, v in found.items()}
        genuine = sum(1 for v in nk.values() if v > 0) >= 2
        res.append({'i': gi, 'j': gj, 'new_products_per_class': nk, 'genuine': genuine,
                    'examples': {k: [(hex(a)[:10], hex(b)[:10]) for a, b in v[:3]] for k, v in found.items()}})
        print('s%d,s%d: %s%s (%.0fs)' % (gi, gj, nk, '  GENUINE' if genuine else '', time.time() - t0), flush=True)
Path(sys.argv[2]).write_text(json.dumps(res, indent=1))
print('genuine pairs:', sum(r['genuine'] for r in res), 'of', len(res))
