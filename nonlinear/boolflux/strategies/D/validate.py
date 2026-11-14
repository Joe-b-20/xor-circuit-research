"""Encoding check: the original window program must satisfy the encoding at r = k (A = a).
Also checks that the decoded solution re-simulates correctly when the solver returns one."""
import random
import sys
import time

import wresyn as R
from boolflux import core

path, nwin = sys.argv[1], int(sys.argv[2])
kk = int(sys.argv[3]) if len(sys.argv) > 3 else 6
c = core.read_ncff(path)
st = R.State(c)
rng = random.Random(3)
cnt = {'SAT': 0, 'UNSAT': 0, 'UNK': 0}
done = 0
while done < nwin:
    W = R.grow_window(st, rng.choice(range(c.n, st.S)), rng.randint(3, kk), rng, 12)
    if W is None:
        continue
    w = R.analyse(st, W, ndiv=rng.randint(0, 2), rng=rng)
    if w is None:
        continue
    done += 1
    t0 = time.time()
    res, sol = R.solve(w, w.k, w.a, budget=200000)
    key = 'SAT' if res else ('UNSAT' if res is False else 'UNK')
    cnt[key] += 1
    if res:
        nc = R.apply(st, w, *sol).live()
        m = nc.metrics()
        ok = R.correct(nc) and m['GD'] <= st.GD and m['AD'] <= st.AD and m['A'] <= st.A
        if not ok:
            print('BAD replacement', m)
    else:
        print('k=%d a=%d c=%d m=%d %s  req_g %s arr_g %s req_a %s arr_a %s' % (
            w.k, w.a, len(w.ins), len(w.outs), key, w.req_g, w.arr_g, w.req_a, w.arr_a))
print(cnt)
