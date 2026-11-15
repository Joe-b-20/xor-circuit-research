#!/usr/bin/env python3
"""All slack-1 windows of a circuit through chain.solve_window:
  - minimal dependent sets S of sinks (rank(outputs mod span(rest)) = |S| - 1), sizes 2..maxsize;
  - consumer closures of single interior ANDs (and pairs) with slack 1.
Usage: chainbatch.py LOG CIRCUIT... [--ops nosinks|all] [--maxsize 9] [--maxnv 30]
"""
import argparse
import itertools
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import chain  # noqa: E402
from wsat import Base, mklog  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('log'); ap.add_argument('circuits', nargs='+')
ap.add_argument('--ops', default='nosinks')
ap.add_argument('--maxsize', type=int, default=9)
ap.add_argument('--maxnv', type=int, default=30)
ap.add_argument('--maxstates', type=int, default=400)
ap.add_argument('--kinds', default='closure,sinks')
ap.add_argument('--target', default='outputs')
ap.add_argument('--dm', type=int, default=1)
ap.add_argument('--maxenums', type=int, default=10**9)
ap.add_argument('--minsize', type=int, default=2)
a = ap.parse_args()
log = mklog(a.log)
for path in a.circuits:
    b = Base(path)
    ops = chain.opset(b, a.ops)
    sinks = [k for k in range(b.K) if not b.cons[k]]
    wins = []
    if 'closure' in a.kinds:
        inner = [k for k in range(b.K) if b.cons[k]]
        seenU = set()
        for X in list(itertools.combinations(inner, 1)) + list(itertools.combinations(inner, 2)):
            U = frozenset(b.closure(set(X)))
            if U in seenU: continue
            seenU.add(U)
            if b.rank_mod(set(U)) == len(U) - 1: wins.append(('cl' + '_'.join(map(str, X)), set(U)))
    if 'deep' in a.kinds:   # sinks + closure of one or two interior ANDs (any slack), for target U
        inner = [k for k in range(b.K) if b.cons[k]]
        seenU = set()
        for X in list(itertools.combinations(inner, 1)) + list(itertools.combinations(inner, 2)):
            U = frozenset(b.closure(set(X)) | set(sinks))
            if U in seenU: continue
            seenU.add(U); wins.append(('d' + '_'.join(map(str, X)), set(U)))
        wins.insert(0, ('allsinks', set(sinks)))
    if 'sinks' in a.kinds:
        found = []
        for s in range(2, a.maxsize + 1):
            keep = s >= a.minsize
            for S in itertools.combinations(sinks, s):
                if any(f <= set(S) for f in found): continue
                if b.rank_mod(set(S)) < s:
                    found.append(set(S))
                    if keep: wins.append(('s' + '_'.join(map(str, S)), set(S)))
    print('windows', len(wins), file=sys.stderr, flush=True)
    for name, U in wins:
        nv = 8 + len([k for k in range(b.K) if k not in U and (ops is None or k in ops)])
        rec = {'method': 'chain-slack1', 'src': Path(path).name, 'win': name, 'U': sorted(U), 'ops': a.ops,
               'tag': 'ch-%s-%s' % (Path(path).name[9:26], name)}
        if nv > a.maxnv:
            rec.update(result='SKIP nv %d' % nv); log(rec); continue
        t0 = time.time()
        try:
            chain.solve_window(b, U, ops, lambda r: None, rec, a.maxstates, dm=a.dm, target=a.target, maxenums=a.maxenums)
        except Exception as e:  # keep going, record the failure
            rec['result'] = 'ERROR %r' % (e,)
        rec['time'] = round(time.time() - t0, 1)
        log(rec)
