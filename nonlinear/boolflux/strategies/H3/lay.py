#!/usr/bin/env python3
"""Exact parallel re-layer of a window, with junk analysis.

Window U (closed under consumers), R = rest, W = span(1, inputs, R) (kept), operand space
V = span(inputs, R_op) with R_op a subset of R (default R).  Sigma = span(classes of the U ANDs
mod W) (dim q); Omega = classes of the 8 outputs (dim r, inside Sigma).

CASE covered [C]: m new ANDs, each a*b with a, b in V (no new AND reads another), each with
class mod W inside Sigma.  r1enum enumerates every such product exactly (all a in a hyperplane of
V, b by linear algebra), giving the achieved class set L in F2^q.  A choice l_1..l_m of L spans a
space containing Omega iff, with pi: F2^q -> F2^q / Omega and J = span(pi(l)), the l's span a
space of dimension r + dim J containing Omega; so the minimum m is min over subspaces J of
F2^q/Omega of (r + dim J) subject to rank{l in L : pi(l) in J} >= r + dim J.

Usage: lay.py CIRCUIT LOG --U "i,j,..." [--closure] [--ops all|nosinks] [--tag T]
"""
import argparse
import itertools
import json
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from wsat import Base, Span, info_set, ONES, NR, finish, save_circuit, mklog  # noqa: E402

BIN = HERE / "r1enum_v3"
FOUND = '/home/joebachir20/xs-campaigns/2026-11-15-study/H3/found'


def par(v): return v.bit_count() & 1


def checks_of(vecs):
    P, M, rk = info_set(vecs)
    Ps = set(P)
    return [(1 << x) | sum(1 << p for p in M[x]) for x in range(NR) if x not in Ps]


def setup(b: Base, U, ops=None):
    n = b.n
    R = [k for k in range(b.K) if k not in U]
    Rop = [k for k in R if ops is None or k in ops]
    Vb = b.tab[1:1 + n] + [b.andtab[k] for k in Rop]
    nv = len(Vb)
    W = [ONES] + b.tab[1:1 + n] + [b.andtab[k] for k in R]
    SW = Span(W); assert len(SW) == len(W)
    Srep = []; ST = Span(W)
    for k in sorted(U):
        if ST.add(b.andtab[k]): Srep.append(b.andtab[k])
    q = len(Srep)
    HT = checks_of(W + Srep)
    HW = checks_of(W)
    comp = []; sg = Span()
    for h in HW:
        s = sum(par(h & t) << i for i, t in enumerate(Srep))
        if s and sg.add(s):
            comp.append(h)
            if len(comp) == q: break
    assert len(comp) == q
    # make the signature map identity on Srep: sig(Srep_i) = e_i  (change of basis on comp)
    Mx = [sum(par(h & t) << i for i, t in enumerate(Srep)) for h in comp]   # row c: sig bits over Srep
    # invert: find combos of comp rows giving unit rows
    rows = [(Mx[c], 1 << c) for c in range(q)]
    piv = {}
    for v, f in rows:
        for h, (w, g) in piv.items():
            if (v >> h) & 1: v ^= w; f ^= g
        h = v.bit_length() - 1
        for k2 in list(piv):
            if (piv[k2][0] >> h) & 1: piv[k2] = (piv[k2][0] ^ v, piv[k2][1] ^ f)
        piv[h] = (v, f)
    comp2 = []
    for i in range(q):
        v, f = piv[i]; assert v == 1 << i
        hh = 0
        for c in range(q):
            if (f >> c) & 1: hh ^= comp[c]
        comp2.append(hh)
    comp = comp2
    sig = lambda v: sum(par(h & v) << c for c, h in enumerate(comp))  # noqa: E731
    Omega = Span([sig(y) for y in b.out])
    prods = [[Vb[i] & Vb[j] for j in range(nv)] for i in range(nv)]

    def G(h):
        return [sum(par(h & prods[i][j]) << j for j in range(nv)) for i in range(nv)]
    return dict(R=R, Rop=Rop, Vb=Vb, nv=nv, q=q, U=sorted(U), Srep=Srep, HT=HT, comp=comp,
                GH=[G(h) for h in HT], GC=[G(h) for h in comp], Omega=Omega, sig=sig)


def run_enum(S, maxhits, seed=1):
    nv = S['nv']; rnd = random.Random(seed)
    nf = min(len(S['GH']), nv + 10)
    GF = []
    for _ in range(nf):
        acc = [0] * nv
        for row in S['GH']:
            if rnd.random() < 0.5: acc = [x ^ y for x, y in zip(acc, row)]
        GF.append(acc)
    lines = ['%d %d %d %d' % (nv, len(S['GH']), len(S['GC']), nf)]
    for rows in (GF, S['GH'], S['GC']):
        for row in rows: lines.append(' '.join('%x' % w for w in row))
    t0 = time.time()
    p = subprocess.run([str(BIN), '1', '%x' % (1 << (nv - 1)), str(maxhits)], input='\n'.join(lines) + '\n',
                       capture_output=True, text=True, check=True)
    hits = []; summary = None
    for ln in p.stdout.splitlines():
        t = ln.split()
        if t[0] == 'H': hits.append(int(t[1], 16))
        elif t[0] == 'DONE': summary = ln
    return hits, summary, time.time() - t0


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


def achieved(S, hits):
    """dict signature -> witness (a, b) over the V basis, all nonzero achievable classes."""
    nv = S['nv']; L = {}
    for a in hits:
        kb = kernel([evalrow(G, a) for G in S['GH']], nv)
        gens = []
        for bv in kb:
            s = sum(par(evalrow(G, a) & bv) << c for c, G in enumerate(S['GC']))
            gens.append((s, bv))
        # all combinations (kernel dims are small)
        if len(gens) > 12: gens = gens[:12]
        for mask in range(1, 1 << len(gens)):
            s = 0; bv = 0
            for i, (gs, gb) in enumerate(gens):
                if (mask >> i) & 1: s ^= gs; bv ^= gb
            if s and s not in L: L[s] = (a, bv)
    return L


def min_cover(L, Omega, q, jmax, cap=2000000):
    """Smallest m = r + dim J (dim J <= jmax) with rank(L_J) >= m.  Returns (m, chosen sigs) or None.
    J ranges over spans of pi(L) elements (enough: shrinking J to span(pi(L_J)) keeps feasibility)."""
    r = len(Omega)
    red = {l: Omega.reduce(l) for l in L}
    junk = sorted(set(v for v in red.values() if v))
    best = None
    level = {(): Span()}
    seen = set()
    for j in range(0, jmax + 1):
        nxt = {}
        for key, J in level.items():
            members = [l for l in L if J.reduce(red[l]) == 0]
            sp = Span(members)
            if len(sp) >= r + j:
                # choose an independent subset of size r + j spanning >= Omega
                pick = []; s2 = Span()
                for l in members:
                    if s2.add(l): pick.append(l)
                return r + j, pick[:len(s2)]
            if j == jmax: continue
            for v in junk:
                if J.reduce(v) == 0: continue
                J2 = Span(list(J.b.values()) + [v])
                # canonical key: fully reduced basis
                kk = tuple(sorted(J2.reduce_basis()))
                if kk in seen: continue
                seen.add(kk); nxt[kk] = J2
                if len(seen) > cap: return ('CAP', j)
        level = nxt
        if not level: break
    return None


def _reduce_basis(self):
    """Reduced row echelon basis (canonical for the subspace)."""
    vs = dict(self.b)
    for h in sorted(vs):
        for k in vs:
            if k != h and (vs[k] >> h) & 1: vs[k] ^= vs[h]
    return list(vs.values())


Span.reduce_basis = _reduce_basis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('log')
    ap.add_argument('--U', required=True, help="window ANDs; 'sinks' = all ANDs without AND consumers")
    ap.add_argument('--closure', action='store_true')
    ap.add_argument('--ops', default='all', help="all | nosinks (operands only from R ANDs that have consumers in the original)")
    ap.add_argument('--tag', default='lay')
    ap.add_argument('--maxhits', type=int, default=2000000)
    ap.add_argument('--control', action='store_true', help='allow m = q (the original count) as a positive control')
    a = ap.parse_args()
    b = Base(a.circuit); log = mklog(a.log)
    if a.U == 'sinks': W = [k for k in range(b.K) if not b.cons[k]]
    else: W = [int(t) for t in a.U.split(',') if t.strip()]
    U = b.closure(W) if a.closure else set(W)
    assert b.closure(U) == U, 'window not closed'
    ops = None
    if a.ops == 'nosinks': ops = {k for k in range(b.K) if b.cons[k]}
    t0 = time.time()
    S = setup(b, U, ops)
    rec = {'method': 'lay-parallel', 'src': Path(a.circuit).name, 'W': a.U, 'U': sorted(U), 'k': len(U),
           'q': S['q'], 'r': len(S['Omega']), 'nv': S['nv'], 'ops': a.ops, 'setup': round(time.time() - t0, 1)}
    hits, summ, dt = run_enum(S, a.maxhits)
    L = achieved(S, hits)
    rec.update(enum_time=round(dt, 1), summary=summ, nhits=len(hits), L=len(L),
               L_span=len(Span(list(L))), L_in_Omega=sum(1 for l in L if S['Omega'].reduce(l) == 0))
    r = len(S['Omega'])
    jmax = (len(U) - r) if a.control else (len(U) - 1 - r)
    t1 = time.time()
    res = min_cover(L, S['Omega'], S['q'], jmax) if jmax >= 0 else None
    rec['cover_time'] = round(time.time() - t1, 1)
    if res is None:
        rec['result'] = 'UNSAT (no parallel cover with m <= %d)' % (r + jmax)
    elif res[0] == 'CAP':
        rec['result'] = 'CAP at j=%d' % res[1]
    else:
        m, pick = res
        rec['m'] = m
        newforms = []
        for s in pick:
            x, y = L[s]
            newforms.append((x << 1 if False else form_of(x, S, b.n), form_of(y, S, b.n)))
        try:
            sk, c2 = finish(b, S['R'], newforms)
            mt = c2.metrics()
            rec.update(result='SAT m=%d' % m, A=mt['A'])
            if mt['A'] < b.K or a.control:
                path, mt2 = save_circuit(c2, FOUND, '%s' % a.tag, dict(rec, how='H3 lay parallel re-layer of %s U=%s ops=%s' % (Path(a.circuit).name, sorted(U), a.ops)))
                rec.update(file=path, AD=mt2['AD'], G=mt2['G'])
        except ValueError as e:
            rec['result'] = 'BUILD-FAIL %s' % e
    log(rec)


def form_of(vec, S, n):
    """V-basis vector -> skeleton form over (const, inputs, R in order)."""
    pos = {k: j for j, k in enumerate(S['R'])}
    f = 0
    for i in range(S['nv']):
        if (vec >> i) & 1:
            if i < n: f |= 1 << (1 + i)
            else: f |= 1 << (1 + n + pos[S['Rop'][i - n]])
    return f


if __name__ == '__main__':
    main()
