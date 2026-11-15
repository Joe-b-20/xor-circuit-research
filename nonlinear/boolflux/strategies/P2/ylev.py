#!/usr/bin/env python3
"""P2: Y-form levels of a circuit's front (ANDs of AND level < 4), per polarity, plus the
front's skeleton forms.  Model M (see bil.py).  Adapted from strategies/T4/ylevels.py.

front(c) -> dict(levels={v: (level, form_mask)} for v = 1..15 (alpha coordinate vector in
bil.ALPHA_B), nfront, sk (skeleton.extract), arr (skeleton-bound arrivals per basis position),
front_ands (list of AND indices in skeleton order with AL < 4)).
A form mask is over positions [const, x0..x7, a0, a1, ...] (skeleton convention).
"""
import heapq
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bil   # noqa: E402
from boolflux import core, skeleton   # noqa: E402


def huff(levels, const=False):
    if not levels: return 0
    if len(levels) == 1: return levels[0] + (1 if const else 0)
    h = list(levels); heapq.heapify(h)
    while len(h) > 1:
        a = heapq.heappop(h); b = heapq.heappop(h); heapq.heappush(h, max(a, b) + 1)
    return h[0]


def load(f):
    return core.read_ncff(f) if not f.endswith('.bfx') else core.from_kernel(open(f).read())


def front(c):
    n = c.n
    sk = skeleton.extract(c)
    ands, outs = sk['ands'], sk['outputs']
    T = c.tables()
    lg = [0] * n; la = [0] * n
    for op, a, b in c.gates:
        lg.append(1 + max(lg[a], lg[b])); la.append((1 if op in core.NONLINEAR_OPS else 0) + max(la[a], la[b]))
    sig = [n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
    nb = 1 + n + len(ands)
    arr = [0] * nb
    for k, (L, R) in enumerate(ands):
        tl = [p for p in range(1, nb) if (L >> p) & 1]; tr = [p for p in range(1, nb) if (R >> p) & 1]
        arr[1 + n + k] = 1 + max(huff([arr[p] for p in tl], bool(L & 1)), huff([arr[p] for p in tr], bool(R & 1)))
    fr = [k for k, s in enumerate(sig) if la[s] < 4]
    # elimination over basis tables: const, inputs, front ANDs
    vecs = [bil.ONES] + [T[i] for i in range(n)] + [T[sig[k]] for k in fr]
    pos = list(range(1 + n)) + [1 + n + k for k in fr]
    rows = []
    for i, v in enumerate(vecs):
        t = 1 << pos[i]
        for pb, rv, rt in rows:
            if (v >> pb) & 1: v ^= rv; t ^= rt
        if v:
            rows.append((v.bit_length() - 1, v, t))
    def express(v):
        t = 0
        for pb, rv, rt in rows:
            if (v >> pb) & 1: v ^= rv; t ^= rt
        return None if v else t
    levels = {}
    for v in range(1, 16):
        tt = bil.tab_Y(bil.ALPHA[v])
        best = None
        for pol in (0, 1):
            m = express(tt ^ (bil.ONES if pol else 0))
            if m is None: continue
            terms = [arr[p] for p in range(1, nb) if (m >> p) & 1]
            lv = huff(terms, bool(m & 1))
            if best is None or lv < best[0]: best = (lv, m, pol)
        levels[v] = best
    return dict(levels=levels, nfront=len(fr), front_idx=fr, sk=sk, arr=arr, n=n)


if __name__ == '__main__':
    for f in sys.argv[1:]:
        F = front(load(f))
        print(Path(f).name, 'front ANDs', F['nfront'])
        print('  ', sorted((F['levels'][v][0] if F['levels'][v] else None, bil.ALPHA[v]) for v in range(1, 16)))
