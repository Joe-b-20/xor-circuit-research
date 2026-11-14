import cProfile
import pstats
import random
import sys
import time

import wresyn as R
from boolflux import core

c = core.read_ncff(sys.argv[1])
st = R.State(c)
rng = random.Random(11)


def work():
    done = 0
    te = ts = ta = 0
    while done < 15:
        W = R.grow_window(st, rng.choice(range(c.n, st.S)), 8, rng, 12)
        if W is None:
            continue
        t0 = time.time()
        w = R.analyse(st, W, ndiv=2, rng=rng)
        if w is None:
            continue
        t1 = time.time()
        enc = R.encode(w, w.k - 1, w.a)
        t2 = time.time()
        res, sol = R.solve(w, w.k - 1, w.a, budget=30000)
        t3 = time.time()
        ta += t1 - t0
        te += t2 - t1
        ts += (t3 - t2) - (t2 - t1)
        done += 1
        print('k %d c %d P %d clauses %d ana %.2f enc %.2f solve %.2f %s' % (w.k, len(w.ins), len(w.pats), len(enc[1]), t1 - t0, t2 - t1, (t3 - t2) - (t2 - t1), res))
    print('totals ana %.1f enc %.1f solve %.1f' % (ta, te, ts))


cProfile.run('work()', '/tmp/d_prof.out')
pstats.Stats('/tmp/d_prof.out').sort_stats('cumtime').print_stats(12)
