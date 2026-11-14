#!/usr/bin/env python3
"""Stage transplant (Track E, mechanism M3): the front of circuit X (all signals of AND level <= L)
combined with the back of circuit Y.  Every Y signal whose complete truth table equals a front
signal of X (or, optionally, the XOR of two front signals of X) is replaced by it; the remaining Y
gates are copied with remapped operands; dead gates are removed.  The result is exact (checked on
all 256 inputs) and its (A, AD, G, GD) is compared with the pinned NIST set.

    python3 splice.py OUT.json FILE...      (all ordered pairs, all cut levels)
"""
import json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import core, load, metrics, correct, levels, ONES, published_files   # noqa: E402

XOR, XNOR, NOT = 6, 9, 3


def splice(X, tx, lx, L, Y, ty, pairs=False):
    n = X.n
    gates = list(X.gates)
    front = {}
    for s in range(n + len(X.gates)):
        if lx[s] <= L and tx[s] not in front: front[tx[s]] = s
    ymap = list(range(n))
    pair_cache = {}
    fl = list(front.items()) if pairs else []
    for j, (op, a, b) in enumerate(Y.gates):
        t = ty[n + j]
        s = front.get(t)
        if s is None and t ^ ONES in front and op != NOT:
            # complement of a front signal: one NOT (counts as a gate) unless Y's own gate is as cheap
            pass
        if s is None and pairs and op in (XOR, XNOR):
            # t = a ^ b (^1) with a, b front signals: one new gate
            for ta, sa in fl:
                sb = front.get(t ^ ta)
                if sb is not None and sb != sa:
                    gates.append((XOR, sa, sb)); s = n + len(gates) - 1; break
                sb = front.get(t ^ ta ^ ONES)
                if sb is not None and sb != sa:
                    gates.append((XNOR, sa, sb)); s = n + len(gates) - 1; break
        if s is None:
            gates.append((op, ymap[a], ymap[b])); s = n + len(gates) - 1
        ymap.append(s)
    c = core.Circuit(n, Y.m, gates, [ymap[o] for o in Y.outputs]).live()
    return c


def main():
    out = Path(sys.argv[1])
    files = [Path(a) for a in sys.argv[2:]] or published_files()
    circs = []
    for f in files:
        c = load(f)
        if not correct(c): continue
        circs.append((f.name, c, c.tables(), levels(c), metrics(c)))
    sys.path.insert(0, str(HERE.parents[1] / 'campaigns'))
    import aes_check
    pub = aes_check.published()
    res = []; t0 = time.time()
    seen = set()
    for xn, X, tx, lx, mx in circs:
        for yn, Y, ty, ly, my in circs:
            if xn == yn: continue
            for L in range(1, mx[1]):
                for pairs in (False, True):
                    c = splice(X, tx, lx, L, Y, ty, pairs)
                    m = metrics(c)
                    if m in ((mx), (my)): continue
                    key = core.to_kernel(c)
                    if key in seen: continue
                    seen.add(key)
                    if not correct(c): raise SystemExit('BUG: splice wrong %s %s %d' % (xn, yn, L))
                    dom = [nm for (u, nm) in pub if all(a <= b for a, b in zip(u, m))]
                    # margin: smallest G reduction needed to become non-dominated at the same A, AD, GD
                    gs = [u[2] for (u, nm) in pub if u[0] <= m[0] and u[1] <= m[1] and u[3] <= m[3]]
                    need = max(0, m[2] - min(gs) + 1) if gs else 0
                    res.append({'X': xn, 'Y': yn, 'L': L, 'pairs': pairs, 'metrics': m, 'new': not dom, 'need': need,
                                'kernel': key})
    res.sort(key=lambda r: (r['need'], r['metrics'][2]))
    out.write_text(json.dumps(res, indent=0))
    print('%d splices (%d distinct) in %.0f s' % (len(res), len(seen), time.time() - t0))
    for r in res[:40]:
        print(r['need'], r['metrics'], r['X'][:34], '<-', r['Y'][:34], 'L', r['L'], 'pairs', r['pairs'], 'NEW' if r['new'] else '')


if __name__ == '__main__':
    main()
