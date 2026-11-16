#!/usr/bin/env python3
"""P6: per-AND / per-output depth anatomy of an AD3 circuit's skeleton (Huffman arrivals).

    python3 skelan.py FILE [--cap D]

For every AND: AND level, Huffman-earliest level, operand term counts by (kind, arrival).
For every output: terms by kind and arrival, Huffman level, Kraft sum at cap D.
"""
import sys, heapq, argparse
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[4]))
from boolflux import core, skeleton   # noqa: E402


def huff(levels, const=False):
    if not levels:
        return 0
    if len(levels) == 1:
        return levels[0] + (1 if const else 0)
    h = list(levels); heapq.heapify(h)
    while len(h) > 1:
        a = heapq.heappop(h); b = heapq.heappop(h); heapq.heappush(h, max(a, b) + 1)
    return h[0]


def bits(f):
    p = 0
    while f:
        if f & 1: yield p
        f >>= 1; p += 1


VARIANTS = False   # if True: every AND takes the fastest of its trivial operand variants
                   # (L,R), (L,L+R+1), (L+R+1,R) (same product exactly)


def anatomy(c):
    sk = skeleton.extract(c)
    n = c.n; ands = sk['ands']; nb = 1 + n + len(ands)
    arr = [0] * nb; alv = [0] * nb
    for k, (L, R) in enumerate(ands):
        if VARIANTS:
            def a_(F): return huff([arr[p] for p in bits(F) if p], F & 1)
            best = None
            for X, Y in ((L, R), (L, L ^ R ^ 1), (L ^ R ^ 1, R)):
                v = max(a_(X), a_(Y))
                if best is None or v < best[0]: best = (v, X, Y)
            L, R = best[1], best[2]; ands[k] = (L, R)
        tl = [p for p in bits(L) if p]; tr = [p for p in bits(R) if p]
        dl = huff([arr[p] for p in tl], L & 1); dr = huff([arr[p] for p in tr], R & 1)
        arr[1 + n + k] = 1 + max(dl, dr)
        alv[1 + n + k] = 1 + max([alv[p] for p in tl + tr] + [0])
    return sk, arr, alv


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--cap', type=int, default=12)
    a = ap.parse_args()
    c = core.read_ncff(a.file) if a.file.endswith('.txt') else core.from_kernel(open(a.file).read())
    m = c.metrics(); print(a.file, m['A'], m['AD'], m['G'], m['GD'])
    sk, arr, alv = anatomy(c); n = c.n
    def desc(f):
        cnt = Counter()
        for p in bits(f):
            if p == 0: continue
            kind = 'x' if p <= n else 'A%d' % alv[p]
            cnt[(kind, arr[p])] += 1
        return ' '.join('%s@%d:%d' % (k, l, v) for (k, l), v in sorted(cnt.items()))
    for k, (L, R) in enumerate(sk['ands']):
        p = 1 + n + k
        print('AND%2d lvl%d arr%2d | L %s | R %s' % (k, alv[p], arr[p], desc(L), desc(R)))
    for j, f in enumerate(sk['outputs']):
        t = [arr[p] for p in bits(f) if p]
        kr = sum(2.0 ** (x - a.cap) for x in t)
        print('OUT%d huff %d kraft@%d %.3f | %s' % (j, huff(t, f & 1), a.cap, kr, desc(f)))


if __name__ == '__main__':
    main()
