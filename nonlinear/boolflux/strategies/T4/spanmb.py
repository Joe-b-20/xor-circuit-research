#!/usr/bin/env python3
"""T4: hypothetical multi-basis junk-sharing score: if the inversion provided Y-forms for ALPHAS
(> 4 of them, all at level 8), each output may pick any 4 independent ones as its basis.
Same scoring as spanscore.py (basis sets B of |B| <= MAXB, linear dependencies modulo S1), with
S1 = FRONT's stage-1 span and d-junk freeness tested in span(affine N, FRONT's A2/A3, EXTRA A3s).
    python3 spanmb.py FRONT ALPHAS(comma) [MAXB]"""
import sys, itertools, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import inv6 as I  # noqa
import invdesign as D  # noqa
import joint44 as J  # noqa
from rank2 import load, analyse  # noqa
from chain import wedge, qform, Red  # noqa

c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
alphas = [int(a) for a in sys.argv[2].split(',')]
maxb = int(sys.argv[3]) if len(sys.argv) > 3 else 2
S1 = [qform(T[s]) for s in fa if la[s] == 1]
Nx = [I.p256(x, 17) for x in range(256)]
def as16(t):
    f = {}
    for x in range(256):
        v = (t >> x) & 1; k = I.IDX[Nx[x]]
        if f.setdefault(k, v) != v: return None
    return sum(v << k for k, v in f.items())
span16 = list(I.AFF) + [as16(T[s]) for s in fa if la[s] >= 2]
piv = J.rank16(span16)
items = []          # (k, basis, design index)
cons = {}; q = {}; dfree = {}
for B in itertools.combinations(alphas, 4):
    if not D.indep(B): continue
    ws = J.wforms(list(B))
    Ys = [J.trY(a) for a in B]
    for di, d in enumerate(J.DES):
        s = 0
        for a, b in d[1]: s ^= Ys[a] & Ys[b]
        fr = J.in_span16(piv, s)
        pf = [J.in_span16(piv, Ys[a] & Ys[b]) for a, b in d[1]]
        for k in range(8):
            it = (k, B, di)
            cons[it] = [wedge(ws[k][a], ws[k][b]) for a, b in d[1]]
            qq = 0
            for x in cons[it]: qq ^= x
            q[it] = qq
            dfree[it] = (fr, [tuple(sorted((B[a], B[b]))) for (a, b), f in zip(d[1], pf) if not f])
            items.append(it)
print('items', len(items), flush=True)
SAVE = {'p3': 1, 'p2': 2}
best = (0, None)
for nb in range(1, maxb + 1):
    for Bs in itertools.combinations(items, nb):
        if len({it[0] for it in Bs}) < nb: continue
        red = Red(S1 + [x for it in Bs for x in cons[it]])
        cost = sum(len(cons[it]) for it in Bs)
        chosen = list(Bs); used = {it[0] for it in Bs}
        for k in range(8):
            if k in used: continue
            opts = [it for it in items if it[0] == k and red.red(q[it]) == 0]
            if opts: chosen.append(max(opts, key=lambda it: SAVE[J.DES[it[2]][0]]))
        sav = sum(SAVE[J.DES[it[2]][0]] for it in chosen)
        dp = set()
        for it in chosen:
            fr, nf = dfree[it]
            if not fr: dp |= set(nf)
        net = sav - cost - len(dp)
        if net > best[0]:
            best = (net, [(it[0], it[1], J.DES[it[2]]) for it in chosen])
            print(json.dumps({'net': best[0], 'choice': best[1], 'xjunk': cost, 'djunk': len(dp)}), flush=True)
print('best net', best[0])
