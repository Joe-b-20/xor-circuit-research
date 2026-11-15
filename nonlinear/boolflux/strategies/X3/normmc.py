"""X3 normmc.py N E K [M]: exact general-model MC (CHM SAT) of x -> x^E on GF(2^N), keeping M independent output
coordinates (default: all independent ones).  Used for norms: (4,5): GF(16)->GF(4); (6,9): GF(64)->GF(8)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'H4'))
import chm
from gfinv import pow_table
n, e, k = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
tab = pow_table(n, e)
cols = []; bas = []
for o in range(n):
    c = sum(((tab[x] >> o) & 1) << x for x in range(1 << n)); r = c
    for b in bas: r = min(r, r ^ b)
    if r: bas.append(r); bas.sort(reverse=True); cols.append(o)
m = len(cols)
t2 = [sum(((tab[x] >> o) & 1) << i for i, o in enumerate(cols)) for x in range(1 << n)]
res, dt, f = chm.solve(t2, n, m, k)
print(json.dumps({'n': n, 'e': e, 'outputs': m, 'k': k, 'sat': res is not None, 'sec': round(dt, 1), 'circ': res}))
