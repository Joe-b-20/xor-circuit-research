"""Sanity: bloat a circuit (XOR -> NOT(XNOR), AND -> NOT(NOT a XOR ... )) and check the tool repairs it."""
import random
import sys

import wresyn as R
from boolflux import core

c = core.read_ncff(sys.argv[1])
rng = random.Random(5)
gates = list(c.gates)
n = c.n
# bloat: pick 5 XOR gates, replace s = XOR(a,b) by t = XNOR(a,b); s = NOT t (append-at-end not
# allowed for topological order, so rebuild through apply-like remap)
new = []
idx = {i: i for i in range(n)}
chosen = set(rng.sample([j for j, g in enumerate(gates) if g[0] == R.XOR], 5))
for j, (op, a, b) in enumerate(gates):
    if j in chosen:
        new.append((R.XNOR, idx[a], idx[b]))
        t = n + len(new) - 1
        new.append((R.NOT, t, t))
    else:
        new.append((op, idx[a], idx[b]))
    idx[n + j] = n + len(new) - 1
bc = core.Circuit(n, c.m, new, [idx[s] for s in c.outputs], c.name, c.in_names, c.out_names)
assert R.correct(bc)
print('bloated', bc.metrics()['G'], 'from', c.metrics()['G'])
st = R.State(bc)
cur = bc
found = 0
for it in range(400):
    st = R.State(cur)
    W = R.grow_window(st, rng.choice(range(n, st.S)), rng.randint(3, 6), rng, 12)
    if W is None:
        continue
    w = R.analyse(st, W, rng=rng)
    if w is None:
        continue
    res, sol = R.solve(w, w.k - 1, w.a, budget=20000)
    if res:
        nc = R.apply(st, w, *sol).live()
        assert R.correct(nc)
        cur = nc
        found += 1
        print('it', it, 'G', nc.metrics()['G'])
print('final', cur.metrics())
