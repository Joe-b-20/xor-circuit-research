#!/usr/bin/env python3
"""Batch of lay-parallel windows: for each circuit, U = sinks, U = sinks + closure(g) for every
non-sink g (and pairs if --pairs), largest operand space (all of R).  Logs one JSON line per window.

Usage: batch.py LOG CIRCUIT... [--pairs] [--maxnv N] [--jcap N]
"""
import argparse
import itertools
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lay  # noqa: E402
from wsat import Base, Span, finish, save_circuit, mklog  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('log'); ap.add_argument('circuits', nargs='+')
ap.add_argument('--pairs', action='store_true')
ap.add_argument('--maxnv', type=int, default=30)
ap.add_argument('--cap', type=int, default=300000)
ap.add_argument('--only', default='', help='comma list of window kinds: sinks,single,pair')
a = ap.parse_args()
log = mklog(a.log)
for path in a.circuits:
    b = Base(path)
    sinks = {k for k in range(b.K) if not b.cons[k]}
    wins = [('sinks', set(sinks))]
    inner = [k for k in range(b.K) if b.cons[k]]
    for g in inner:
        wins.append(('s+%d' % g, b.closure({g}) | sinks))
    if a.pairs:
        for g, h in itertools.combinations(inner, 2):
            wins.append(('s+%d+%d' % (g, h), b.closure({g, h}) | sinks))
    done = set()
    for name, U in wins:
        key = frozenset(U)
        if key in done: continue
        done.add(key)
        nv = 8 + b.K - len(U)
        rec = {'method': 'lay-parallel', 'src': Path(path).name, 'win': name, 'k': len(U), 'nv': nv}
        if nv > a.maxnv:
            rec['result'] = 'SKIP nv'; log(rec); continue
        t0 = time.time()
        S = lay.setup(b, U)
        hits, summ, dt = lay.run_enum(S, 2000000)
        L = lay.achieved(S, hits)
        r = len(S['Omega'])
        jmax = len(U) - 1 - r
        rec.update(U=sorted(U), q=S['q'], r=r, enum_time=round(dt, 1), nhits=len(hits), L=len(L),
                   L_span=len(Span(list(L))), L_in_Omega=sum(1 for l in L if S['Omega'].reduce(l) == 0))
        t1 = time.time()
        res = lay.min_cover(L, S['Omega'], S['q'], jmax, cap=a.cap) if jmax >= 0 else None
        rec['cover_time'] = round(time.time() - t1, 1)
        if res is None:
            rec['result'] = 'UNSAT-parallel (m <= %d impossible)' % (len(U) - 1)
        elif res[0] == 'CAP':
            rec['result'] = 'CAP j=%d' % res[1]
        else:
            m, pick = res
            newforms = [(lay.form_of(L[s][0], S, b.n), lay.form_of(L[s][1], S, b.n)) for s in pick]
            try:
                sk, c2 = finish(b, S['R'], newforms)
                path2, mt = save_circuit(c2, lay.FOUND, 'lay-%s-%s' % (Path(path).name[9:24], name.replace('+', '_')),
                                         dict(rec, how='H3 lay parallel re-layer, window %s of %s' % (name, Path(path).name)))
                rec.update(result='SAT m=%d' % m, A=mt['A'], AD=mt['AD'], G=mt['G'], file=path2)
            except ValueError as e:
                rec['result'] = 'BUILD-FAIL %s' % e
        rec['time'] = round(time.time() - t0, 1)
        log(rec)
