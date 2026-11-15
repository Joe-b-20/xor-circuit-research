"""P7: show linear gates between AND levels 1 and 2 as forms over (1, x, AND-1 products), with consumers."""
import sys
sys.path.insert(0, '.')
import s1lib as L
from boolflux import skeleton
c = L.load(sys.argv[1]); n = c.n
T, lg, la = L.sim(c)
form = [1 << (1 + i) for i in range(n)]
ands = []
for op, a, b in c.gates:
    fa, fb = form[a], form[b]
    if op == 6: f = fa ^ fb
    elif op == 9: f = fa ^ fb ^ 1
    elif op == 3: f = fa ^ 1
    else:
        ands.append(n + len(form) - n); f = 1 << (1 + n + len(ands) - 1)
    form.append(f)
names = ['1'] + ['x%d' % i for i in range(n)] + ['a%d' % k for k in range(len(ands))]
fmt = lambda F: '+'.join(names[p] for p in range(len(names)) if (F >> p) & 1)
fo = {}
for j, (op, a, b) in enumerate(c.gates):
    for o in {a, b}: fo.setdefault(o, []).append(n + j)
for j, (op, a, b) in enumerate(c.gates):
    s = n + j
    if op in L.core.NONLINEAR_OPS: continue
    if la[s] == 1:
        print('%3d GL%d op%d (%d,%d) %-40s -> %s' % (s, lg[s], op, a, b, fmt(form[s]), fo.get(s)))
