"""Compare encodings (colex symmetry breaking on/off) on the same windows: status and time."""
import random
import sys
import time

import wresyn as R
from boolflux import core

path, k, nwin, budget = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
c = core.read_ncff(path)
st = R.State(c)
rng = random.Random(7)
tot = {True: [0, 0, 0, 0.0], False: [0, 0, 0, 0.0]}
done = 0
while done < nwin:
    W = R.grow_window(st, rng.choice(range(c.n, st.S)), k, rng, 12)
    if W is None:
        continue
    w = R.analyse(st, W, rng=random.Random(done))
    if w is None or w.k != k:
        continue
    done += 1
    row = []
    for cx in (False, True):  # cegis off / on
        t0 = time.time()
        res, sol = R.solve(w, w.k - 1, w.a, budget=budget, cegis=cx)
        dt = time.time() - t0
        i = 0 if res else (1 if res is False else 2)
        tot[cx][i] += 1
        tot[cx][3] += dt
        row.append('%s %.2fs' % ({0: 'SAT', 1: 'UNSAT', 2: 'UNK'}[i], dt))
    print('c=%d m=%d P=%d  nocolex %s | colex %s' % (len(w.ins), len(w.outs), len(w.pats), row[0], row[1]), flush=True)
print('nocolex sat/unsat/unk/time', tot[False])
print('colex   sat/unsat/unk/time', tot[True])
