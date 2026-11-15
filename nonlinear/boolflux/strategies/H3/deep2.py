#!/usr/bin/env python3
"""Two-level re-solve of a deep window with classes in Sigma_U.

Window U (consumer-closed), R = rest, W = span(1, x, R), V = span(x, R) (all of R as operands),
Sigma_U = span(classes of the U ANDs mod W), T = outputs mod W.
CASE [C]: new ANDs = A (a <= amax ANDs, operands in V) then B (any number, operands in V + A, no B
reads another B), every class mod W inside Sigma_U, total |A| + |B| <= |U| - 1.
Method: level-1 classes P1 (r1enum over V); for every independent choice A of <= amax classes in
P1 (one witness per class suffices by Lemma 2), all classes L of products over V + A (r1enum), then
the exact min-cover over L modulo span(A) (lay.min_cover).  amax = 0 is the parallel re-layer.
Usage: deep2.py LOG CIRCUIT... [--amax 2] [--pairs] [--windows "X1;X2"] [--maxnv 26]
"""
import argparse
import itertools
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import chain  # noqa: E402
import lay  # noqa: E402
from deep import products  # noqa: E402
from chain import par, comp_checks, checks_of  # noqa: E402
from wsat import Base, Span, ONES, mklog  # noqa: E402


def run(b, U, rec, amax, cap, control=False):
    n = b.n
    R = [k for k in range(b.K) if k not in U]
    W = [ONES] + b.tab[1:1 + n] + [b.andtab[k] for k in R]
    Trep = []; ST = Span(W)
    for y in b.out:
        if ST.add(y): Trep.append(y)
    Xrep = []; SX = Span(W)
    for k in sorted(U):
        if SX.add(b.andtab[k]): Xrep.append(b.andtab[k])
    q = len(Xrep)
    HT = checks_of(W + Xrep)
    compW = comp_checks(W, Xrep)
    sigW = lambda v: sum(par(h & v) << c for c, h in enumerate(compW))  # noqa: E731
    Omega = [sigW(y) for y in Trep]
    V0 = b.tab[1:1 + n] + [b.andtab[k] for k in R]
    mmax = len(U) - (0 if control else 1)
    rec.update(k=len(U), q=q, r=len(Trep), nv0=len(V0), mmax=mmax, amax=amax)
    t0 = time.time()
    P1, dt = products(V0, HT, W, Xrep, sigW)
    nen = 1; tt = dt
    # independent class choices
    cls1 = list(P1)
    choices = [()]
    for a in range(1, amax + 1):
        for C in itertools.combinations(cls1, a):
            if len(Span(list(C))) == a: choices.append(C)
    rec.update(P1=len(P1), choices=len(choices))
    best = None
    for C in choices:
        wA = [P1[c] for c in C]
        FA = [w[0] for w in wA]
        if C:
            L, dt = products(V0 + FA, HT, W + FA, Xrep, sigW); nen += 1; tt += dt
        else:
            L = P1
        SA = Span(list(C))
        Om = Span()
        for o in Omega:
            Om.add(SA.reduce(o))
        red = {}
        for c, w in L.items():
            rc = SA.reduce(c)
            if rc and rc not in red: red[rc] = w
        jmax = mmax - len(C) - len(Om)
        if jmax < 0: continue
        res = lay.min_cover(red, Om, q, jmax, cap=cap)
        if res is None: continue
        if res[0] == 'CAP':
            rec.setdefault('caps', []).append([list(C), res[1]]); continue
        m, pick = res
        tot = len(C) + m
        if best is None or tot < best[0]:
            best = (tot, wA, [red[s] for s in pick])
    rec.update(enums=nen, enum_time=round(tt, 1))
    if best is None:
        rec['result'] = 'UNSAT-deep2 (no |A|+|B| <= %d)%s' % (mmax, ' with CAPs' if rec.get('caps') else '')
        return rec
    tot, wA, wB = best
    return chain.build(b, R, R, wA + wB, rec, lambda r: None, nen, tt, len(choices))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('log'); ap.add_argument('circuits', nargs='+')
    ap.add_argument('--amax', type=int, default=2)
    ap.add_argument('--pairs', action='store_true')
    ap.add_argument('--windows', default='')
    ap.add_argument('--maxnv', type=int, default=26)
    ap.add_argument('--cap', type=int, default=200000)
    ap.add_argument('--control', action='store_true', help='allow |U| new ANDs (positive control)')
    ap.add_argument('--nosinks-added', action='store_true', help='windows = closure(X) only (no sinks added)')
    a = ap.parse_args()
    log = mklog(a.log)
    for path in a.circuits:
        b = Base(path)
        sinks = {k for k in range(b.K) if not b.cons[k]}
        inner = [k for k in range(b.K) if b.cons[k]]
        Xs = [tuple(int(t) for t in w.split(',')) for w in a.windows.split(';') if w] if a.windows else \
            ([()] + list(itertools.combinations(inner, 1)) + (list(itertools.combinations(inner, 2)) if a.pairs else []))
        seenU = set()
        for X in Xs:
            U = b.closure(set(X)) if a.nosinks_added else (b.closure(set(X)) | sinks)
            if frozenset(U) in seenU: continue
            seenU.add(frozenset(U))
            nv = 8 + b.K - len(U)
            rec = {'method': 'deep2', 'src': Path(path).name, 'win': 'd' + '_'.join(map(str, X)), 'U': sorted(U),
                   'ops': 'all', 'tag': 'd2-%s-%s' % (Path(path).name[9:26], '_'.join(map(str, X)) or 'sinks'), 'nv': nv}
            if nv > a.maxnv:
                rec['result'] = 'SKIP nv'; log(rec); continue
            t0 = time.time()
            try:
                run(b, U, rec, a.amax, a.cap, a.control)
            except Exception as e:
                import traceback; traceback.print_exc()
                rec['result'] = 'ERROR %r' % (e,)
            rec['time'] = round(time.time() - t0, 1)
            log(rec)


if __name__ == '__main__':
    main()
