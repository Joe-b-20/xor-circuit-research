#!/usr/bin/env python3
"""Pool-based last layer over a fixed prefix (X3's members + semi-members as candidate products).

Prefix = the non-last-level ANDs of CIRCUIT (kept), W = span(1, x, prefix).  Pool = products
(Tr(A1 x) + Tr_K(e2 n)) * (Tr(A2 x) + Tr_K(e1 n)), n = x^238, one per line of X3's
semi_members.tsv (1275 members in 5-cosets, 107k semi-members in 2-/3-cosets).
CASE [C]: last layer = m products from the pool (any classes, junk unrestricted); question: the
smallest m with outputs in span(W, layer).  Statistics first (junk dimension, groups); the exact
cover is a BFS over junk subspaces J spanned by pool junk vectors: m = 8 + dim J is feasible iff
rank{p : junk(p) in J} >= 8 + dim J.
Usage: pool.py CIRCUIT TSV [--jmax 4] [--cap N]
"""
import argparse
import collections
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wsat import Base, Span, ONES  # noqa: E402

MOD = 0x11B


def gmul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1
        if a & 0x100: a ^= MOD
        b >>= 1
    return r


def gpow(a, e):
    r = 1
    while e:
        if e & 1: r = gmul(r, a)
        a = gmul(a, a); e >>= 1
    return r


def tr(z, k=8):
    s = 0
    for _ in range(k): s ^= z; z = gmul(z, z)
    return s & 1


NN = [gpow(x, 238) for x in range(256)]
TRX = {}


def trx(A):
    if A not in TRX: TRX[A] = sum(tr(gmul(A, x)) << x for x in range(256))
    return TRX[A]


TRN = {}


def trn(e):
    if e not in TRN: TRN[e] = sum(tr(gmul(e, NN[x]), 4) << x for x in range(256))
    return TRN[e]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('tsv')
    ap.add_argument('--jmax', type=int, default=4)
    ap.add_argument('--cap', type=int, default=200000)
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    t0 = time.time()
    b = Base(a.circuit)
    sinks = [k for k in range(b.K) if not b.cons[k]]
    pre = [k for k in range(b.K) if b.cons[k]]
    W = [ONES] + b.tab[1:1 + b.n] + [b.andtab[k] for k in pre]
    SW = Span(W)
    nin = [e for e in range(256) if gpow(e, 16) == e]       # GF(16) elements
    n_in_W = all(SW.reduce(trn(e)) == 0 for e in nin)
    Om = Span()
    for y in b.out: Om.add(SW.reduce(y))
    SWO = Span(W + [SW.reduce(y) for y in b.out])
    # original last layer: classes and junk
    orig = [SW.reduce(b.andtab[k]) for k in sinks]
    orig_j = Span([SWO.reduce(c) for c in orig])
    print('circuit', Path(a.circuit).name, 'prefix', len(pre), 'last layer', len(sinks),
          'dim W', len(SW), 'n in W:', n_in_W, 'dim Omega', len(Om), 'orig junk dim', len(orig_j), flush=True)
    groups = collections.defaultdict(list)    # junk -> list of (class, line)
    npool = 0; zero = 0
    for ln in open(a.tsv):
        if ln.startswith('#'): continue
        p = ln.split('\t')
        A1, A2, e1, e2 = (int(v, 16) for v in p[3:7])
        f = (trx(A1) ^ trn(e2)) & (trx(A2) ^ trn(e1))
        c = SW.reduce(f)
        npool += 1
        if not c: zero += 1; continue
        j = SWO.reduce(c)
        groups[j].append((c, p[2], ln.strip()))
    alljunk = Span(list(groups))
    print('pool', npool, 'in W', zero, 'distinct junk', len(groups), 'junk span dim', len(alljunk),
          'junk-0 products', len(groups.get(0, [])), 'time %.1f' % (time.time() - t0), flush=True)
    # does the pool contain the original classes?
    poolcls = set(c for g in groups.values() for c, _, _ in g)
    print('original classes in pool:', sum(1 for c in orig if c in poolcls), '/', len(orig), flush=True)
    # group sizes
    hist = collections.Counter(len(g) for j, g in groups.items() if j)
    print('junk group sizes:', dict(sorted(hist.items())[:20]), flush=True)
    # BFS over junk subspaces
    r = len(Om)
    junks = [j for j in groups if j]
    # rank of groups' classes inside each J: maintain per J
    level = {(): Span()}
    seen = set()
    best = None
    for d in range(0, a.jmax + 1):
        nxt = {}
        for key, J in level.items():
            mem = [c for j, g in groups.items() if J.reduce(j) == 0 for c, _, _ in g]
            rk = len(Span(mem))
            if rk >= r + d:
                best = (r + d, key)
                print('FEASIBLE m = %d with junk subspace of dim %d' % (r + d, d), flush=True)
                break
            if d == a.jmax: continue
            for v in junks:
                if J.reduce(v) == 0: continue
                J2 = Span(list(J.b.values()) + [v])
                vs = dict(J2.b)
                for h in sorted(vs):
                    for k in vs:
                        if k != h and (vs[k] >> h) & 1: vs[k] ^= vs[h]
                kk = tuple(sorted(vs.values()))
                if kk in seen: continue
                seen.add(kk); nxt[kk] = J2
                if len(seen) > a.cap:
                    print('CAP at depth', d + 1, 'subspaces', len(seen), flush=True); return
        if best: break
        level = nxt
        print('depth %d done, %d subspaces next, %.1f s' % (d, len(level), time.time() - t0), flush=True)
    print('RESULT', 'min m =', best[0] if best else '> %d' % (r + a.jmax), 'time %.1f' % (time.time() - t0))


if __name__ == '__main__':
    main()
