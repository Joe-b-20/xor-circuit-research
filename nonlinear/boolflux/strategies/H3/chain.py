#!/usr/bin/env python3
"""Exact decision for slack-1 windows in the general model (chains among the new ANDs allowed).

Window U (closed under consumers), R = rest, W = span(1, x, R), T = span(outputs mod W), r = dim T.
If r = |U| - 1 =: m, a replacement by m new ANDs f_1..f_m (topological order; f_l's operands in
V + span(f_<l), V = span(x, R_op)) must have every class f_l mod W inside T (the m classes span
the m-dim T), so:
  LEMMA 1. classes of f_1..f_m form a basis of T.
  LEMMA 2. the set of products available at step l, taken mod W_l = W + span(f_<l), depends only
           on the subspace S_l = span(classes of f_<l) of T, not on which witnesses were chosen
           (two witnesses with equal class differ by c + v, c constant, v in V; constants in
           operands change a product only by an element of the span, and v is already in V).
So the search is a BFS over subspaces S of T, starting at 0: from S, enumerate (r1enum, exact)
every product a*b with a, b in V + lift(S) whose class mod W + lift(S) lies in T and not in S;
each gives S' = S + class.  The window improves (K -> K-1) iff T is reachable.

CASE [C]: the kept ANDs R keep their functions; new operands range over span(x, R_op, f_<l)
(R_op = R unless --ops restricts it); any number of chain levels.

Usage: chain.py CIRCUIT LOG "W1;W2;..." [--closure] [--ops all|nosinks|lvlt:L] [--maxstates N]
"""
import argparse
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from wsat import Base, Span, info_set, ONES, NR, finish, save_circuit, mklog  # noqa: E402

BIN = HERE / "r1enum_v2"
FOUND = '/home/joebachir20/xs-campaigns/2026-11-15-study/H3/found'


def par(v): return v.bit_count() & 1


def checks_of(vecs):
    P, M, rk = info_set(vecs)
    Ps = set(P)
    return [(1 << x) | sum(1 << p for p in M[x]) for x in range(NR) if x not in Ps]


def comp_checks(Wv, Trep, HW=None):
    """Checks annihilating span(Wv) whose signatures on Trep (mod Wv) are independent."""
    HW = HW if HW is not None else checks_of(Wv)
    comp = []; sg = Span()
    for h in HW:
        s = sum(par(h & t) << i for i, t in enumerate(Trep))
        if s and sg.add(s): comp.append(h)
    return comp


def Gmat(h, Vb):
    nv = len(Vb)
    return [sum(par(h & Vb[i] & Vb[j]) << j for j in range(nv)) for i in range(nv)]


def enum(Vb, HT, comp, maxhits=500000, seed=1):
    nv = len(Vb)
    GH = [Gmat(h, Vb) for h in HT]
    GC = [Gmat(h, Vb) for h in comp]
    rnd = random.Random(seed)
    nf = min(len(GH), nv + 10)
    GF = []
    for _ in range(nf):
        acc = [0] * nv
        for row in GH:
            if rnd.random() < 0.5: acc = [x ^ y for x, y in zip(acc, row)]
        GF.append(acc)
    lines = ['%d %d %d %d' % (nv, len(GH), len(GC), nf)]
    for rows in (GF, GH, GC):
        for row in rows: lines.append(' '.join('%x' % w for w in row))
    t0 = time.time()
    p = subprocess.run([str(BIN), '1', '%x' % (1 << (nv - 1)), str(maxhits)], input='\n'.join(lines) + '\n',
                       capture_output=True, text=True, check=True)
    hits = [int(ln.split()[1], 16) for ln in p.stdout.splitlines() if ln.startswith('H ')]
    summ = [ln for ln in p.stdout.splitlines() if ln.startswith('DONE')][0]
    if int(summ.split()[-1]) != len(hits):
        raise RuntimeError('r1enum hit list truncated (%s); raise maxhits' % summ)
    return hits, GH, GC, time.time() - t0, summ


def kernel(rows, nv):
    piv = {}
    for v in rows:
        for h, w in piv.items():
            if (v >> h) & 1: v ^= w
        if v:
            h = v.bit_length() - 1
            for k in list(piv):
                if (piv[k] >> h) & 1: piv[k] ^= v
            piv[h] = v
    basis = []
    for f in [j for j in range(nv) if j not in piv]:
        bb = 1 << f
        for h, w in piv.items():
            if (w >> f) & 1: bb |= 1 << h
        basis.append(bb)
    return basis


def evalrow(G, a):
    r = 0; i = 0
    while a:
        if a & 1: r ^= G[i]
        a >>= 1; i += 1
    return r


def vtab(vec, Vb):
    t = 0; i = 0
    while vec:
        if vec & 1: t ^= Vb[i]
        vec >>= 1; i += 1
    return t


def key_of(sp):
    vs = dict(sp.b)
    for h in sorted(vs):
        for k in vs:
            if k != h and (vs[k] >> h) & 1: vs[k] ^= vs[h]
    return tuple(sorted(vs.values()))


def solve_window(b, U, ops, log, rec, maxstates=200, maxhits=500000, dm=1, target='outputs', maxenums=10**9):
    """BFS over operand spaces.  State = span(1, V + new ANDs so far) (canonical key); two states
    with the same operand space have the same future (exact also when R_op is a proper subset of R).
    target 'outputs': new classes must lie in T (exact for slack 1); target 'U': new classes must lie
    in Sigma_U = span(classes of the U ANDs mod W) (a restriction for slack > 1).
    Goal: the classes span a space containing T, with at most |U| - dm new ANDs."""
    n = b.n
    R = [k for k in range(b.K) if k not in U]
    Rop = [k for k in R if ops is None or k in ops]
    W = [ONES] + b.tab[1:1 + n] + [b.andtab[k] for k in R]
    Trep = []; ST = Span(W)
    for y in b.out:
        if ST.add(y): Trep.append(y)
    r = len(Trep)
    mmax = len(U) - dm
    rec.update(k=len(U), r=r, nv0=n + len(Rop), ops_n=len(Rop), target=target, mmax=mmax)
    if target == 'outputs' and r != mmax:
        rec['result'] = 'SKIP slack %d' % (len(U) - r); log(rec); return rec
    if r > mmax:
        rec['result'] = 'UNSAT-rank'; log(rec); return rec
    if target == 'outputs': Xrep = Trep
    else:
        Xrep = []; SX = Span(W)
        for k in sorted(U):
            if SX.add(b.andtab[k]): Xrep.append(b.andtab[k])
    q = len(Xrep); rec['q'] = q
    HT = checks_of(W + Xrep)
    compW = comp_checks(W, Xrep)
    sigW = lambda v: sum(par(h & v) << c for c, h in enumerate(compW))  # noqa: E731
    Omega = [sigW(y) for y in Trep]
    V0 = b.tab[1:1 + n] + [b.andtab[k] for k in Rop]
    start_key = key_of(Span([ONES] + V0))
    frontier = [[]]; seen = {start_key}
    t0 = time.time(); nenum = 0; tenum = 0.0
    while frontier:
        nxt = []
        for wits in frontier:
            Fs = [w[0] for w in wits]
            if len(Fs) >= mmax: continue
            Vb = V0 + Fs
            Ws = W + Fs
            comp = comp_checks(Ws, Xrep)
            if not comp: continue
            if nenum >= maxenums:
                rec.update(result='CAP enums %d (states %d)' % (nenum, len(seen)), enums=nenum,
                           enum_time=round(tenum, 1), time=round(time.time() - t0, 1))
                log(rec); return rec
            hits, GH, GC, dt, summ = enum(Vb, HT, comp, maxhits)
            nenum += 1; tenum += dt
            Sspan = Span([sigW(f) for f in Fs])
            for a in hits:
                kb = kernel([evalrow(G, a) for G in GH], len(Vb))
                atab = vtab(a, Vb)
                if len(kb) > 10: raise RuntimeError('kernel dim %d > 10: combos not enumerated' % len(kb))
                for mask in range(1, 1 << len(kb)):
                    bv = 0
                    for t, v in enumerate(kb):
                        if (mask >> t) & 1: bv ^= v
                    s2 = sum(par(evalrow(G, a) & bv) << c for c, G in enumerate(GC))
                    if not s2: continue
                    f = atab & vtab(bv, Vb)
                    cls = sigW(f)
                    if Sspan.reduce(cls) == 0: continue
                    S2 = Span(list(Sspan.b.values()) + [cls])
                    # prune: S2 + Omega must fit in mmax
                    if len(Span(list(S2.b.values()) + Omega)) > mmax: continue
                    k2 = key_of(Span([ONES] + Vb + [f]))
                    if k2 in seen: continue
                    seen.add(k2)
                    w2 = wits + [(f, a, bv, len(Vb))]
                    if all(S2.reduce(o) == 0 for o in Omega):
                        return build(b, R, Rop, w2, rec, log, nenum, tenum, len(seen))
                    nxt.append(w2)
                    if len(seen) > maxstates:
                        rec.update(result='CAP states %d' % len(seen), enums=nenum, enum_time=round(tenum, 1),
                                   time=round(time.time() - t0, 1))
                        log(rec); return rec
        frontier = nxt
    rec.update(result='UNSAT-chain (%d operand spaces reached, m<=%d)' % (len(seen), mmax), enums=nenum,
               enum_time=round(tenum, 1), states=len(seen), time=round(time.time() - t0, 1))
    log(rec); return rec


def build(b, R, Rop, wits, rec, log, nenum, tenum, nstates):
    n = b.n
    pos = {k: j for j, k in enumerate(R)}

    def form(vec, nvl):
        f = 0
        for i in range(nvl):
            if (vec >> i) & 1:
                if i < n: f |= 1 << (1 + i)
                elif i < n + len(Rop): f |= 1 << (1 + n + pos[Rop[i - n]])
                else: f |= 1 << (1 + n + len(R) + (i - n - len(Rop)))
        return f
    newforms = [(form(a, nvl), form(bv, nvl)) for (f, a, bv, nvl) in wits]
    sk, c2 = finish(b, R, newforms)
    path, mt = save_circuit(c2, FOUND, rec.get('tag', 'chain'),
                            dict(rec, how='H3 chain slack-1 re-solve of %s U=%s' % (rec['src'], rec['U'])))
    rec.update(result='SAT', A=mt['A'], AD=mt['AD'], G=mt['G'], file=path, enums=nenum,
               enum_time=round(tenum, 1), states=nstates)
    log(rec); return rec


def opset(b, spec):
    if spec == 'all': return None
    if spec == 'nosinks': return {k for k in range(b.K) if b.cons[k]}
    if spec.startswith('lvlt:'):
        L = int(spec[5:]); return {k for k in range(b.K) if b.level[k] < L}
    raise SystemExit('bad --ops')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('log'); ap.add_argument('windows')
    ap.add_argument('--closure', action='store_true')
    ap.add_argument('--ops', default='nosinks')
    ap.add_argument('--maxstates', type=int, default=300)
    ap.add_argument('--tag', default='chain')
    ap.add_argument('--dm', type=int, default=1, help='m = |U| - dm (dm=0: positive control)')
    ap.add_argument('--target', default='outputs')
    a = ap.parse_args()
    b = Base(a.circuit); log = mklog(a.log)
    ops = opset(b, a.ops)
    for wi, w in enumerate(a.windows.split(';')):
        Wl = [int(t) for t in w.split(',') if t.strip()]
        U = b.closure(Wl) if a.closure else set(Wl)
        assert b.closure(U) == U, 'not closed'
        rec = {'method': 'chain-slack1', 'src': Path(a.circuit).name, 'W': Wl, 'U': sorted(U), 'ops': a.ops,
               'tag': '%s-%d' % (a.tag, wi)}
        solve_window(b, U, ops, log, rec, a.maxstates, dm=a.dm, target=a.target)


if __name__ == '__main__':
    main()
