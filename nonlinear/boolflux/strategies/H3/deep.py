#!/usr/bin/env python3
"""Deep windows (consumer-closed U, any slack) with new-AND classes restricted to Sigma_U.

CASE [C] (with --ops all): kept ANDs R keep their functions; new ANDs f_1..f_m in any chain order,
operands in span(x, R, f_<l); every class f_l mod W lies in Sigma_U = span(classes of the deleted
ANDs mod W) (W = span(1, x, R)); outputs in span(W, f).  By Lemma 2 (chain.py) the products
available after choosing classes S depend only on S, so
  1. SATURATION: S_0 = 0, S_{t+1} = S_t + {classes in Sigma_U of products over V + lift(S_t)};
     the limit S* contains every class that any such chain can create.  If T (outputs mod W) is
     not inside S*, no m works.  If it is, then
  2. MIN COVER: BFS over subspaces (one enumeration per state) for the smallest m with T inside S,
     bounded by m <= |U| - 1 (improvement only).
Usage: deep.py LOG CIRCUIT... [--kinds deep] [--ops all] [--maxstates N] [--maxnv N]
"""
import argparse
import itertools
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import chain  # noqa: E402
from chain import enum, kernel, evalrow, vtab, par, comp_checks, checks_of  # noqa: E402
from wsat import Base, Span, ONES, mklog  # noqa: E402


def products(Vb, HT, Ws, Xrep, sigW, maxcombo=10):
    """All classes (sigW) of products over Vb landing in W+Sigma and not in Ws, with witnesses."""
    comp = comp_checks(Ws, Xrep)
    if not comp: return {}, 0.0
    hits, GH, GC, dt, summ = enum(Vb, HT, comp)
    out = {}
    for a in hits:
        kb = kernel([evalrow(G, a) for G in GH], len(Vb))
        if len(kb) > maxcombo: raise RuntimeError('kernel dim %d > %d' % (len(kb), maxcombo))
        atab = vtab(a, Vb)
        for mask in range(1, 1 << len(kb)):
            bv = 0
            for t, v in enumerate(kb):
                if (mask >> t) & 1: bv ^= v
            if not sum(par(evalrow(G, a) & bv) << c for c, G in enumerate(GC)): continue
            f = atab & vtab(bv, Vb)
            cls = sigW(f)
            if cls not in out: out[cls] = (f, a, bv, len(Vb))
    return out, dt


def run(b, U, ops, rec, maxstates, log):
    n = b.n
    R = [k for k in range(b.K) if k not in U]
    Rop = [k for k in R if ops is None or k in ops]
    W = [ONES] + b.tab[1:1 + n] + [b.andtab[k] for k in R]
    Trep = []; ST = Span(W)
    for y in b.out:
        if ST.add(y): Trep.append(y)
    Xrep = []; SX = Span(W)
    for k in sorted(U):
        if SX.add(b.andtab[k]): Xrep.append(b.andtab[k])
    HT = checks_of(W + Xrep)
    compW = comp_checks(W, Xrep)
    sigW = lambda v: sum(par(h & v) << c for c, h in enumerate(compW))  # noqa: E731
    Omega = [sigW(y) for y in Trep]
    V0 = b.tab[1:1 + n] + [b.andtab[k] for k in Rop]
    mmax = len(U) - 1
    rec.update(k=len(U), q=len(Xrep), r=len(Trep), nv0=len(V0), mmax=mmax)
    # 1. saturation
    S = Span(); wits = []; rounds = 0; tt = 0.0
    while True:
        Fs = [w[0] for w in wits]
        P, dt = products(V0 + Fs, HT, W + Fs, Xrep, sigW); tt += dt; rounds += 1
        added = 0
        for cls, w in P.items():
            if S.add(cls): wits.append(w); added += 1
        if not added: break
    rec.update(sat_rounds=rounds, sat_dim=len(S), sat_time=round(tt, 1),
               T_in_sat=all(S.reduce(o) == 0 for o in Omega))
    if not rec['T_in_sat']:
        rec['result'] = 'UNSAT-deep (T not in saturation, any m)'; log(rec); return rec
    # 2. BFS for the smallest m <= mmax
    frontier = [(Span(), [])]; seen = {()}
    nenum = 0
    for depth in range(mmax):
        nxt = []
        for Sp, wl in frontier:
            Fs = [w[0] for w in wl]
            P, dt = products(V0 + Fs, HT, W + Fs, Xrep, sigW); nenum += 1; tt += dt
            for cls, w in P.items():
                if Sp.reduce(cls) == 0: continue
                S2 = Span(list(Sp.b.values()) + [cls])
                if len(Span(list(S2.b.values()) + Omega)) > mmax: continue
                key = chain.key_of(S2)
                if key in seen: continue
                seen.add(key)
                w2 = wl + [w]
                if all(S2.reduce(o) == 0 for o in Omega):
                    rec['bfs_enums'] = nenum
                    return chain.build(b, R, Rop, w2, rec, log, nenum, tt, len(seen))
                nxt.append((S2, w2))
                if len(seen) > maxstates:
                    rec.update(result='CAP states %d depth %d' % (len(seen), depth), bfs_enums=nenum)
                    log(rec); return rec
        frontier = nxt
        if not frontier: break
    rec.update(result='UNSAT-deep (no m<=%d)' % mmax, bfs_enums=nenum, states=len(seen))
    log(rec); return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('log'); ap.add_argument('circuits', nargs='+')
    ap.add_argument('--ops', default='all')
    ap.add_argument('--maxstates', type=int, default=3000)
    ap.add_argument('--maxnv', type=int, default=27)
    ap.add_argument('--pairs', action='store_true')
    ap.add_argument('--windows', default='', help='explicit "i,j;k" closures (with sinks added) instead of the sweep')
    a = ap.parse_args()
    log = mklog(a.log)
    for path in a.circuits:
        b = Base(path)
        ops = chain.opset(b, a.ops)
        sinks = {k for k in range(b.K) if not b.cons[k]}
        inner = [k for k in range(b.K) if b.cons[k]]
        wins = [('allsinks', set(sinks))]
        Xs = [tuple(int(t) for t in w.split(',')) for w in a.windows.split(';') if w] if a.windows else \
            (list(itertools.combinations(inner, 1)) + (list(itertools.combinations(inner, 2)) if a.pairs else []))
        seenU = {frozenset(sinks)}
        for X in Xs:
            U = frozenset(b.closure(set(X)) | sinks)
            if U in seenU: continue
            seenU.add(U); wins.append(('d' + '_'.join(map(str, X)), set(U)))
        for name, U in wins:
            nv = 8 + len([k for k in range(b.K) if k not in U and (ops is None or k in ops)])
            rec = {'method': 'deep-sigmaU', 'src': Path(path).name, 'win': name, 'U': sorted(U), 'ops': a.ops,
                   'tag': 'dp-%s-%s' % (Path(path).name[9:26], name), 'nv': nv}
            if nv > a.maxnv:
                rec['result'] = 'SKIP nv'; log(rec); continue
            t0 = time.time()
            try:
                run(b, U, ops, rec, a.maxstates, lambda r: None)
            except Exception as e:
                rec['result'] = 'ERROR %r' % (e,)
            rec['time'] = round(time.time() - t0, 1)
            log(rec)


if __name__ == '__main__':
    main()
