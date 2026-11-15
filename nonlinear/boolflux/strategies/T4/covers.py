#!/usr/bin/env python3
"""T4: stage-1 9-covers of N = x^17 (from archive circuits), their images under the group
G = {x -> a x^(2^i)} (order 2040, preserves span of N's coordinates), and which bottom x-junk
targets (rank-2 forms = 2-dim spaces of x-linear forms) a cover can contain.
    python3 covers.py FRONT_FILE ARCHIVE_DIR [ARCHIVE_DIR ...]
"""
import sys, glob, itertools, json, os
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import Span, load, analyse, ONES  # noqa
from xjunk import decompose  # noqa
from chain import lin, wedge, qform, Red  # noqa
from absorb import gmul, gpow, N_tables  # noqa
from boolflux import core  # noqa

def tr(z):
    t = 0; s = z
    for _ in range(8): t ^= s; s = gmul(s, s)
    return t & 1
# linear form vector (bit i <-> input i, input i = bit 7-i of the byte) <-> alpha
L_OF = {}
for al in range(256):
    l = 0
    for i in range(8):
        if tr(gmul(al, 1 << (7 - i))): l |= 1 << i
    L_OF[al] = l
A_OF = {l: al for al, l in L_OF.items()}
assert len(A_OF) == 256
INV8 = {}
GROUP = [(a, i) for a in range(1, 256) for i in range(8)]
def act(al, g):
    a, i = g
    return gpow(gmul(al, a), 1 << ((8 - i) % 8))
def skey(l, m):
    return frozenset((l, m, l ^ m))
def act_key(k, g):
    return frozenset(L_OF[act(A_OF[l], g)] for l in k)

VN = Red([qform(t) for t in N_tables()])
assert len(VN.p) == 4

def covers_of(c):
    T, lg, la, fa, ba, V, X = analyse(c)
    a1 = [s for s in fa if la[s] == 1]
    prods = []
    for s in a1:
        op, a, b = c.gates[s - c.n]
        l, m = lin(T[a]), lin(T[b])
        if l and m and l != m: prods.append(skey(l, m))
    out = []
    def spans(sub):
        r = Red([wedge(*sorted(k)[:2]) for k in sub])
        return all(r.red(v) == 0 for v in VN.p.values())
    if len(prods) < 9: return out
    for sub in itertools.combinations(prods, 9):
        if len(set(sub)) == 9 and spans(sub): out.append(frozenset(sub))
        if len(out) > 20: break
    return out

def canon(cov):
    best = None
    for g in GROUP:
        k = tuple(sorted(tuple(sorted(act_key(x, g))) for x in cov))
        if best is None or k < best: best = k
    return best

if __name__ == '__main__':
    front = sys.argv[1]
    c = load(front); T, lg, la, fa, ba, V, X = analyse(c)
    AD = max(la[o] for o in c.outputs)
    outs = decompose(c, T, la, ba, AD)
    ys = sorted({y for d in outs for y in d})
    free = [(i, j) for i, j in itertools.combinations(range(len(ys)), 2) if (ys[i] & ys[j]) in V]
    targets = {}
    for k, d in enumerate(outs):
        w = [lin(d.get(y, 0)) for y in ys]
        for i, j in itertools.combinations(range(len(ys)), 2):
            targets.setdefault(skey(w[i], w[j]), []).append((k, (i, j), (i, j) in free))
    print('targets', len(targets), 'free pairs', free, flush=True)
    files = []
    for d in sys.argv[2:]:
        files += sorted(glob.glob(os.path.join(d, '*.bfx'))) + sorted(glob.glob(os.path.join(d, '*.circ.txt')))
    classes = {}
    for f in files:
        try:
            cc = load(f)
        except Exception:
            continue
        for cov in covers_of(cc):
            if cov in classes.values(): continue
            classes.setdefault(len(classes), cov)
        if len(classes) > 400: break
    print('raw covers', len(classes), flush=True)
    canon_seen = {}
    for idx, cov in classes.items():
        ck = canon(cov)
        canon_seen.setdefault(ck, cov)
    print('cover classes up to G', len(canon_seen), flush=True)
    # orbit membership of targets: for each class and g, targets contained
    best = []
    for ck, cov in canon_seen.items():
        for g in GROUP:
            img = {act_key(x, g) for x in cov}
            hit = [t for t in img if t in targets]
            if hit:
                info = [targets[t] for t in hit]
                nfree = len({k for L in info for (k, p, fr) in L if fr})
                nany = len({k for L in info for (k, p, fr) in L})
                best.append((nfree, nany, ck, g, info))
    best.sort(key=lambda z: (-z[0], -z[1]))
    print('cover images hitting targets:', len(best))
    for b in best[:15]:
        print(json.dumps({'outputs_free': b[0], 'outputs_any': b[1], 'g': b[3], 'hits': b[4]}))
