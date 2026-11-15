#!/usr/bin/env python3
"""P2: orbit search for depth-feasible rank-1 bottoms (see orbit.py for the model and symmetries).

    python3 orbsearch.py D OUT.json --fronts F1 F2 ... --bottoms B1 B2 ...

For every front (its Y-form level table), every base bottom decomposition (extracted from a
circuit with a rank-1 AND-level-4 bottom) and every image under (a, b, Frobenius) (15*255*8):
per-output Kraft sums  sum_{j in output} 2^(1 + lev(alpha_j) - D).  Feasible = all <= 1.
Exact within the model (rank-1 products of pure Y-forms and linear x-forms; products at
1 + lev(alpha); output = XOR of its products).
"""
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bil    # noqa: E402
import ylev   # noqa: E402
import orbit as O   # noqa: E402

I = O.I
MUL = [[O.m256(a, b) for b in range(256)] for a in range(256)]
INV = [O.inv(z) for z in range(256)]
SQ = [MUL[x][x] for x in range(256)]
P8 = [O.p256(z, 8) for z in range(256)]
P128 = [O.p256(z, 128) for z in range(256)]
LV = [O.lvec(w) for w in range(256)]


def gmap_fast(g, mtab):
    m = 0
    for q in range(8):
        e = 1 << (7 - q)
        if bin(g & mtab[e]).count('1') & 1: m |= e
    return m


def orbit_iter(dec):
    G16 = [z for z in I.SUB if z]
    for b in range(1, 256):
        b17i = INV[O.p256(b, 17)]
        mb = MUL[b]
        base = [(MUL[al][b17i], gmap_fast(g, mb), MUL[w][b]) for al, g, w in dec]
        for f in range(8):
            if f:
                base = [(P8[al], gmap_fast(g, SQ), P128[w]) for al, g, w in base]
            for a in G16:
                ai = INV[a]
                yield (a, b, f), [(MUL[al][a], g, MUL[w][ai]) for al, g, w in base]


def kraft(d2, lev, D):
    ks = [0.0] * 8
    for al, g, w in d2:
        lv = LV[w]; wt = 2.0 ** (1 + lev[al] - D)
        for k in range(8):
            if (lv >> (7 - k)) & 1: ks[k] += wt
    return ks


def main():
    D = int(sys.argv[1]); out = sys.argv[2]
    i = sys.argv.index('--fronts'); j = sys.argv.index('--bottoms')
    fronts = sys.argv[i + 1:j]; bottoms = sys.argv[j + 1:]
    decs = []
    for b in bottoms:
        d = O.extract(ylev.load(b))
        if d is None or not O.check(d):
            print('no rank-1 bottom:', b, flush=True); continue
        decs.append((b, d))
    res = []
    for fname in fronts:
        F = ylev.front(ylev.load(fname))
        lev = {bil.ALPHA[v]: F['levels'][v][0] for v in range(1, 16)}
        for bname, dec in decs:
            best = None; feas = []
            for tr, d2 in orbit_iter(dec):
                ks = kraft(d2, lev, D)
                nover = sum(1 for x in ks if x > 1 + 1e-9)
                key = (nover, round(sum(max(0.0, x - 1.0) for x in ks), 4), round(sum(ks), 4))
                if best is None or key < best[0]: best = (key, tr, ks)
                if nover == 0: feas.append({'tr': tr, 'dec': d2, 'ks': ks})
            print('front %s (%d) bottom %s (%d): best %s feasible %d' % (
                Path(fname).name, F['nfront'], Path(bname).name, len(dec), best, len(feas)), flush=True)
            res.append({'front': fname, 'nfront': F['nfront'], 'bottom': bname, 'nprod': len(dec),
                        'best': best, 'nfeas': len(feas), 'feasible': feas[:200]})
    json.dump(res, open(out, 'w'))


if __name__ == '__main__':
    main()
