#!/usr/bin/env python3
"""Relaxed parallel re-layer: new product classes allowed in Sigma' = Sigma_U + D, D = span of the
classes of X3's pool products (members + semi-members, semi_members.tsv) over the same prefix.

Window U = all last-level ANDs, prefix R kept, W = span(1, x, R), operands = all of span(x, R)
(n = x^238 lies in W for the A28 prefixes).  r1enum lists EVERY product a*b over V whose class mod W
lies in Sigma' (not only pool products).  Then statistics of the junk (class mod W + Omega) and the
exact question "m <= |U| - 1 products spanning a space containing Omega" by BFS over junk subspaces
(capped).  CASE [C]: parallel layer over the kept prefix, classes in Sigma_U + D.
Usage: lay_pool.py CIRCUIT TSV LOG [--maxpool N] [--cap N]
"""
import argparse
import collections
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lay  # noqa: E402
import pool  # noqa: E402
from chain import comp_checks, checks_of, par  # noqa: E402
from wsat import Base, Span, ONES, mklog, finish, save_circuit  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('tsv'); ap.add_argument('log')
    ap.add_argument('--cap', type=int, default=300000)
    ap.add_argument('--maxpool', type=int, default=10 ** 9)
    a = ap.parse_args()
    log = mklog(a.log)
    t0 = time.time()
    b = Base(a.circuit)
    sinks = [k for k in range(b.K) if not b.cons[k]]
    pre = [k for k in range(b.K) if b.cons[k]]
    W = [ONES] + b.tab[1:1 + b.n] + [b.andtab[k] for k in pre]
    SW = Span(W)
    # Sigma' reps: sinks then pool classes
    SX = Span(W); Xrep = []
    for k in sinks:
        if SX.add(b.andtab[k]): Xrep.append(b.andtab[k])
    q0 = len(Xrep)
    npool = 0
    for ln in open(a.tsv):
        if ln.startswith('#'): continue
        p = ln.split('\t'); npool += 1
        if npool > a.maxpool: break
        A1, A2, e1, e2 = (int(v, 16) for v in p[3:7])
        f = (pool.trx(A1) ^ pool.trn(e2)) & (pool.trx(A2) ^ pool.trn(e1))
        if SX.add(f): Xrep.append(f)
    q = len(Xrep)
    print('Sigma dim', q0, 'Sigma+D dim', q, 'time %.1f' % (time.time() - t0), flush=True)
    HT = checks_of(W + Xrep)
    compW = comp_checks(W, Xrep)
    sigW = lambda v: sum(par(h & v) << c for c, h in enumerate(compW))  # noqa: E731
    Omega = Span([sigW(y) for y in b.out])
    Vb = b.tab[1:1 + b.n] + [b.andtab[k] for k in pre]
    S = dict(R=pre, Rop=pre, Vb=Vb, nv=len(Vb), q=q, HT=HT, comp=compW,
             GH=[lay.chain_G(h, Vb) for h in HT] if hasattr(lay, 'chain_G') else None)
    from chain import Gmat
    S['GH'] = [Gmat(h, Vb) for h in HT]; S['GC'] = [Gmat(h, Vb) for h in compW]
    rec = {'method': 'lay-pool', 'src': Path(a.circuit).name, 'q_sigma': q0, 'q_total': q, 'nv': len(Vb),
           'pool_lines': npool, 'setup': round(time.time() - t0, 1)}
    print('setup done %.1f s, HT rows %d' % (time.time() - t0, len(HT)), flush=True)
    hits, summ, dt = lay.run_enum(S, 5000000)
    print('enum', summ, '%.1f s' % dt, flush=True)
    L = lay.achieved(S, hits)
    rec.update(enum_time=round(dt, 1), nhits=len(hits), L=len(L), summary=summ)
    # junk = class mod Omega (in signature coordinates)
    junk = collections.Counter(Omega.reduce(l) for l in L)
    rec.update(distinct_junk=len(junk), junk_span=len(Span([j for j in junk if j])),
               L_span=len(Span(list(L))), L_in_Omega=junk.get(0, 0))
    print(rec, flush=True)
    jmax = len(sinks) - 1 - len(Omega)
    res = lay.min_cover(L, Omega, q, jmax, cap=a.cap)
    if res is None: rec['result'] = 'UNSAT (no m <= %d)' % (len(sinks) - 1)
    elif res[0] == 'CAP': rec['result'] = 'CAP j=%d' % res[1]
    else:
        m, pick = res
        newforms = [(lay.form_of(L[s][0], S, b.n), lay.form_of(L[s][1], S, b.n)) for s in pick]
        sk, c2 = finish(b, pre, newforms)
        path, mt = save_circuit(c2, lay.FOUND, 'pool-%s' % Path(a.circuit).name[9:26], dict(rec, how='H3 lay_pool'))
        rec.update(result='SAT m=%d' % m, A=mt['A'], file=path)
    rec['time'] = round(time.time() - t0, 1)
    log(rec)


if __name__ == '__main__':
    main()
