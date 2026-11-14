import time, threading
from pysat.solvers import Solver
from pysat.examples.genhard import PHP
f = PHP(9)
for name in ['cadical195', 'glucose4', 'minisat22', 'glucose42']:
    s = Solver(name=name, bootstrap_with=f.clauses)
    t0 = time.time()
    tm = threading.Timer(1.0, lambda: s.interrupt())
    tm.start()
    try:
        r = s.solve_limited(expect_interrupt=True)
    except Exception as e:
        r = 'ERR %s' % e
    tm.cancel()
    print(name, r, round(time.time() - t0, 2))
    s.delete()
for name in ['cadical195', 'glucose4']:
    s = Solver(name=name, bootstrap_with=f.clauses)
    t0 = time.time()
    try:
        s.conf_budget(20000)
        r = s.solve_limited()
    except Exception as e:
        r = 'ERR %s' % e
    print('budget', name, r, round(time.time() - t0, 2))
