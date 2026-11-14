"""Probe: sample windows of a circuit, report sizes and SAT outcomes for r = k-1."""
import random
import sys
import time

import wresyn as R
from boolflux import core

path = sys.argv[1]
k = int(sys.argv[2])
nwin = int(sys.argv[3])
ndiv = int(sys.argv[4]) if len(sys.argv) > 4 else 0
budget = int(sys.argv[5]) if len(sys.argv) > 5 else 20000
c = core.read_ncff(path)
st = R.State(c)
print('G A GD AD', st.G, st.A, st.GD, st.AD)
rng = random.Random(1)
gs = list(range(c.n, st.S))
stats = {'sat': 0, 'unsat': 0, 'unk': 0, 'skip': 0}
t00 = time.time()
for it in range(nwin):
    W = R.grow_window(st, rng.choice(gs), k, rng, 12)
    if W is None:
        stats['skip'] += 1
        continue
    t0 = time.time()
    w = R.analyse(st, W, ndiv=ndiv, rng=rng)
    if w is None:
        stats['skip'] += 1
        continue
    t1 = time.time()
    res, sol = R.solve(w, w.k - 1, w.a, budget=budget)
    t2 = time.time()
    key = 'sat' if res else ('unsat' if res is False else 'unk')
    stats[key] += 1
    print('k=%d a=%d c=%d m=%d P=%d free=%d  %s  ana %.2fs sat %.2fs' % (
        w.k, w.a, len(w.ins), len(w.outs), len(w.pats), w.nfree, key, t1 - t0, t2 - t1), flush=True)
    if res:
        nc = R.apply(st, w, *sol)
        ok = R.correct(nc)
        m = nc.metrics()
        print('   -> G %d A %d GD %d AD %d correct %s' % (m['G'], m['A'], m['GD'], m['AD'], ok))
print(stats, 'total %.1fs' % (time.time() - t00))
