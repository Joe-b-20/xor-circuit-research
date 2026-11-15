#!/usr/bin/env python3
"""Exact 'parallel slack-1' window test.

For a window U (closed under consumers) with r = rank(outputs mod W) = |U| - 1, W = span(1, V),
V = span(inputs, R), R = all \\ U: any replacement by m = r new ANDs has every new AND's class mod W
inside T = span(outputs mod W) (the r new classes must span T).  In the PARALLEL case (all new
operands in V; no new AND reads another new AND) this is decided exactly by enumerating every
product a*b, a, b in V, with class in T \\ {0} (r1enum.c), then checking whether the achieved
classes span T.  A positive answer gives a circuit with K - 1 ANDs.

Usage: r1.py CIRCUIT LOG "W1;W2;..." [--closure] [--tag T] [--maxhits N]
"""
import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from wsat import Base, Span, info_set, ONES, NR, finish, save_circuit, mklog  # noqa: E402

BIN = HERE / 'r1enum'
FOUND = '/home/joebachir20/xs-campaigns/2026-11-15-study/H3/found'


def checks_of(vecs):
    P, M, rk = info_set(vecs)
    Ps = set(P)
    return [(1 << x) | sum(1 << p for p in M[x]) for x in range(NR) if x not in Ps]


def par(v): return v.bit_count() & 1


def setup(b: Base, U, target='outputs'):
    n = b.n
    R = [k for k in range(b.K) if k not in U]
    Vb = b.tab[1:1 + n] + [b.andtab[k] for k in R]
    nv = len(Vb)
    W = [ONES] + Vb
    SW = Span(W)
    assert len(SW) == 1 + nv, 'V basis dependent'
    Trep = []
    ST = Span(W)
    for y in (b.out if target == 'outputs' else [b.andtab[k] for k in sorted(U)]):
        if ST.add(y): Trep.append(y)
    r = len(Trep)
    HT = checks_of(W + Trep)
    HW = checks_of(W)
    # r checks of W with independent T-signatures
    comp = []; sigs = Span()
    for h in HW:
        s = sum(par(h & t) << i for i, t in enumerate(Trep))
        if s and sigs.add(s):
            comp.append(h)
            if len(comp) == r: break
    assert len(comp) == r
    prods = [[Vb[i] & Vb[j] for j in range(nv)] for i in range(nv)]

    def G(h):
        return [sum(par(h & prods[i][j]) << j for j in range(nv)) for i in range(nv)]
    GH = [G(h) for h in HT]
    GC = [G(h) for h in comp]
    return dict(R=R, Vb=Vb, nv=nv, Trep=Trep, r=r, HT=HT, comp=comp, GH=GH, GC=GC)


def run_enum(S, maxhits, seed=1):
    nv = S['nv']; rnd = random.Random(seed)
    nf = min(len(S['GH']), nv + 12)
    GF = []
    for _ in range(nf):
        acc = [0] * nv
        for row in S['GH']:
            if rnd.random() < 0.5:
                acc = [x ^ y for x, y in zip(acc, row)]
        GF.append(acc)
    lines = ['%d %d %d %d' % (nv, len(S['GH']), len(S['GC']), nf)]
    for rows in (GF, S['GH'], S['GC']):
        for row in rows: lines.append(' '.join('%x' % w for w in row))
    t0 = time.time()
    p = subprocess.run([str(BIN), '1', '%x' % (1 << (nv - 1)), str(maxhits)], input='\n'.join(lines) + '\n',
                       capture_output=True, text=True, check=True)
    dt = time.time() - t0
    hits = []; summary = None
    for ln in p.stdout.splitlines():
        t = ln.split()
        if t[0] == 'H': hits.append(int(t[1], 16))
        elif t[0] == 'DONE': summary = ln
    return hits, summary, dt


def kernel(rows, nv):
    """Basis of {b : <row, b> = 0 for all rows} over F2^nv."""
    piv = {}
    for v in rows:
        for h, w in piv.items():
            if (v >> h) & 1: v ^= w
        if v:
            h = v.bit_length() - 1
            for k in list(piv):
                if (piv[k] >> h) & 1: piv[k] ^= v
            piv[h] = v
    free = [j for j in range(nv) if j not in piv]
    basis = []
    for f in free:
        b = 1 << f
        for h, w in piv.items():
            if (w >> f) & 1: b |= 1 << h
        basis.append(b)
    return basis


def evalrow(G, a):
    r = 0; i = 0
    while a:
        if a & 1: r ^= G[i]
        a >>= 1; i += 1
    return r


def analyse(S, hits):
    """Achieved classes (signature ints in F2^r) with one witness (a, b) each."""
    nv = S['nv']; ach = {}
    for a in hits:
        rows = [evalrow(G, a) for G in S['GH']]
        for bvec in kernel(rows, nv):
            sig = sum(par(evalrow(G, a) & bvec) << c for c, G in enumerate(S['GC']))
            if sig and sig not in ach: ach[sig] = (a, bvec)
        # the kernel is a subspace: also its sums (signature map is linear)
        sigs = list(ach)
    # close under the linear structure per hit is implicit: sums of witnesses with the same a
    return ach


def form_of(vec, S, n):
    f = 0
    for i in range(S['nv']):
        if (vec >> i) & 1:
            f |= 1 << (1 + i)          # inputs then R in order: positions 1..n, 1+n..
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('log'); ap.add_argument('windows')
    ap.add_argument('--closure', action='store_true')
    ap.add_argument('--tag', default='r1')
    ap.add_argument('--maxhits', type=int, default=200000)
    ap.add_argument('--target', default='outputs', help="outputs, or 'sinks' (positive control: T = classes of U)")
    a = ap.parse_args()
    b = Base(a.circuit); log = mklog(a.log)
    for wi, w in enumerate(a.windows.split(';')):
        W = [int(t) for t in w.split(',') if t.strip()]
        U = b.closure(W) if a.closure else set(W)
        assert b.closure(U) == U
        t0 = time.time()
        S = setup(b, U, a.target)
        rec = {'method': 'r1-parallel', 'src': Path(a.circuit).name, 'W': W, 'U': sorted(U), 'k': len(U),
               'rank': S['r'], 'nv': S['nv'], 'setup': round(time.time() - t0, 1)}
        if a.target == 'sinks':
            hits, summ, dt = run_enum(S, a.maxhits); ach = analyse(S, hits)
            rec.update(target='sinks', enum_time=round(dt, 1), summary=summ, nhits=len(hits),
                       achieved=len(ach), achieved_span=len(Span(list(ach))), result='CONTROL')
            log(rec); continue
        if S['r'] != len(U) - 1:
            rec['result'] = 'SKIP (slack %d, method needs slack 1)' % (len(U) - S['r']); log(rec); continue
        hits, summ, dt = run_enum(S, a.maxhits)
        ach = analyse(S, hits)
        span = Span(list(ach))
        rec.update(enum_time=round(dt, 1), summary=summ, nhits=len(hits), achieved=len(ach),
                   achieved_span=len(span))
        if len(span) < S['r']:
            rec['result'] = 'UNSAT-parallel'
        else:
            # pick r independent achieved classes
            pick = []; sp = Span()
            for sig, wit in ach.items():
                if sp.add(sig): pick.append(wit)
            n = b.n
            newforms = [(form_of(x, S, n), form_of(y, S, n)) for x, y in pick]
            try:
                sk, c2 = finish(b, S['R'], newforms)
                path, mt = save_circuit(c2, FOUND, '%s-%s' % (a.tag, '-'.join(map(str, W))),
                                        dict(rec, how='H3 r1 parallel slack-1 re-solve of %s window %s'
                                             % (Path(a.circuit).name, sorted(U))))
                rec.update(result='SAT', file=path, A=mt['A'], AD=mt['AD'], G=mt['G'])
            except ValueError as e:
                rec.update(result='BUILD-FAIL %s' % e)
        log(rec)


if __name__ == '__main__':
    main()
