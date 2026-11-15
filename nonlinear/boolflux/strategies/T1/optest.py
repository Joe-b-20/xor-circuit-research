#!/usr/bin/env python3
"""smoke test: one call of each T1 operator with short budgets"""
import sys, time, types
sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/T1')
import t1run as T
a = types.SimpleNamespace(goal=sys.argv[1], seed=7, hours=0.01, vary=1, data=sys.argv[2], name='smoke', ops='polish,osc,trb,join,skel,pullA')
w = T.Worker(a)
print('pool', len(w.pool), 'a29', len(w.a29), 'front', sorted(w.front()))
for op in sys.argv[3].split(','):
    src = w.a29 if op == 'pullA' else w.pool
    i, (c, m, o) = w.pick(src)
    t0 = time.time()
    cs = getattr(w, 'op_' + op)(c)
    print(op, i, m, '->', [T.metrics(x) for x in cs if x], round(time.time() - t0, 1), 's', flush=True)
