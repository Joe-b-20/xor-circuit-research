#!/usr/bin/env python3
"""T4: choose the stage-1 cover to create x-junk coincidences between outputs.

For a fixed front's Y-basis (the 4 Y-forms of FILE's inversion) the x-forms w_ik are fixed, and the
x-junk of a rank-2 design is the alternating form q_k(d) = sum over its pairs of w_ak ^ w_bk.
Two outputs can share their x-junk ANDs iff q_k(dk) + q_l(dl) lies in the stage-1 alternating span
S1 (9 dims, contains V_N).  This scans every image g(C) of the known cover classes and lists the
coincidences each one creates (V_N-structural ones hold for every cover).
    python3 coincov.py FILE OUT.jsonl COVER_SOURCE_DIR...
"""
import sys, itertools, json, glob, os
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import load, analyse, ONES  # noqa
from xjunk import decompose  # noqa
from chain import lin, wedge, qform, Red  # noqa
from covers import covers_of, canon, GROUP, act_key  # noqa
from absorb import N_tables  # noqa

DES = [('p3', (a, b)) for a, b in itertools.combinations(range(4), 2)] + \
      [('p2', ((0, 1), (2, 3))), ('p2', ((0, 2), (1, 3))), ('p2', ((0, 3), (1, 2)))]
def pairs_of(d): return [d[1]] if d[0] == 'p3' else list(d[1])

if __name__ == '__main__':
    f, outf = sys.argv[1], sys.argv[2]
    c = load(f); T, lg, la, fa, ba, V, X = analyse(c)
    outs = decompose(c, T, la, ba, 4)
    ys = sorted({y for d in outs for y in d})
    dfree = {}
    for di, d in enumerate(DES):
        s = 0
        for a, b in pairs_of(d): s ^= ys[a] & ys[b]
        dfree[di] = s in V
    Q = {}
    for k in range(8):
        w = [lin(outs[k].get(y, 0)) for y in ys]
        for di, d in enumerate(DES):
            q = 0
            for a, b in pairs_of(d): q ^= wedge(w[a], w[b])
            Q[(k, di)] = q
    VN = [qform(t) for t in N_tables()]
    keys = sorted(Q)
    files = []
    for dd in sys.argv[3:]:
        files += sorted(glob.glob(os.path.join(dd, '*.bfx'))) + sorted(glob.glob(os.path.join(dd, '*.circ.txt')))
    raw = set()
    for ff in files:
        try: cc = load(ff)
        except Exception: continue
        for cov in covers_of(cc): raw.add(cov)
    classes = {}
    for cov in raw: classes.setdefault(canon(cov), cov)
    print('classes', len(classes), 'dfree designs', [DES[i] for i in dfree if dfree[i]], flush=True)
    out = open(outf, 'w')
    from collections import Counter
    hist = Counter()
    for ci, cov in enumerate(classes.values()):
        for g in GROUP:
            ks = [act_key(x, g) for x in cov]
            red = Red(VN + [wedge(*sorted(k)[:2]) for k in ks])
            res = {}
            for key in keys:
                res.setdefault(red.red(Q[key]), []).append(key)
            hits = []
            for r, L in res.items():
                for (k, dk), (l, dl) in itertools.combinations(L, 2):
                    if k != l: hits.append((k, DES[dk][0], dk, l, dl, dfree[dk], dfree[dl]))
            # score: p2/p2 pairs and p3/p3 pairs on distinct outputs
            hist[len(hits)] += 1
            if hits:
                out.write(json.dumps({'class': ci, 'g': g, 'n': len(hits), 'hits': hits,
                                      'keys': [sorted(k) for k in ks]}) + '\n')
        out.flush()
        print('class', ci, 'hist', dict(hist), flush=True)
    print('done', flush=True)
