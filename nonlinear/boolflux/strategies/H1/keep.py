"""Keep-set table (as G's subsets.py, re-implemented): over the prefix E of circuit P (span of 1, x,
stage-1 and middle ANDs of P) and a pool M of last-layer products (from circuits Q1, Q2, ...),
d(X) = dim(T + E + X) - dim(E + X) for every subset X of M.  A k-member last layer over E that
keeps X needs |X| + d(X) <= k.  Prints min d(X) by |X| and the subsets reaching k = 9 + ... budget.
usage: python3 keep.py PREFIXFILE MEMBERFILE [MEMBERFILE2] [--k K]"""
import itertools
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
from xag import gf, AFFX, span


def prefix_and_last(f):
    c, ands, outs, ot = xag.parse(f)
    roles = [xag.role(A) for A in ands]
    pre = [A['tab'] for A, r in zip(ands, roles) if r in ('S1', 'MID')]
    last = [A['tab'] for A, r in zip(ands, roles) if r not in ('S1', 'MID')]
    return pre, last, ot


def main():
    argv = list(sys.argv[1:])
    k = 13
    if '--k' in argv:
        i = argv.index('--k'); k = int(argv[i + 1]); del argv[i:i + 2]
    args = argv
    pre, _, T = prefix_and_last(args[0])
    pool = []
    for f in args[1:]:
        _, last, _ = prefix_and_last(f); pool += last
    # de-duplicate members modulo E
    E = span(AFFX, pre)
    piv = sorted(E.piv.items(), reverse=True)

    def fullred(v):                       # linear projection: clear every pivot bit
        for h, (pv, _) in piv:
            if (v >> h) & 1: v ^= pv
        return v
    # pivots of gf.Span are leading bits of vectors whose higher bits may hit other pivots;
    # make the basis fully reduced first
    rb = []
    for h, (pv, _) in piv:
        for h2, pv2 in rb:
            if (pv >> h2) & 1: pv ^= pv2
        rb.append((h, pv))
    for i in range(len(rb)):
        h, pv = rb[i]
        for j in range(len(rb)):
            if j != i and (rb[j][1] >> h) & 1: rb[j] = (rb[j][0], rb[j][1] ^ pv)
    piv = [(h, (pv, 0)) for h, pv in rb]
    red = []
    for t in pool:
        r = fullred(t)
        if r and r not in red: red.append(r)
    Tr = [fullred(t) for t in T]
    m = len(red)
    print('prefix', Path(args[0]).name, 'dim E', E.dim(), 'pool', m, 'members (distinct mod E)')
    best = {}
    hits = []
    for mask in range(1 << m):
        X = [red[i] for i in range(m) if mask >> i & 1]
        S = gf.Span(X)
        dEX = S.dim()
        for t in Tr: S.add(t)
        d = S.dim() - dEX
        s = len(X)
        if s not in best or d < best[s][0]: best[s] = (d, mask)
        if s + d <= k and d >= 0 and s <= k:
            hits.append((s, d, mask))
    for s in sorted(best):
        print('  |X|=%2d  min d=%d  e.g. %s' % (s, best[s][0],
                                               [i + 1 for i in range(m) if best[s][1] >> i & 1]))
    full = [h for h in hits if h[1] == 0]
    print('subsets with |X| + d <= %d: %d ; with d = 0 (complete layers of size <= %d): %d' % (
        k, len(hits), k, len(full)))
    for h in sorted(full)[:10]:
        print('   complete:', h[0], [i + 1 for i in range(m) if h[2] >> i & 1])


if __name__ == '__main__':
    main()
