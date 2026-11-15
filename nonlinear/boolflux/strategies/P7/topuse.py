"""P7: list the top linear layer (gates with no AND in their fan-in) of a circuit: each gate's form,
level, and its consumers (AND levels of AND consumers / 'lin' for linear consumers outside the top)."""
import sys
sys.path.insert(0, '.')
import s1lib as L
c = L.load(sys.argv[1]); n = c.n
T, lg, la = L.sim(c)
fo = {}
for j, (op, a, b) in enumerate(c.gates):
    for o in {a, b}: fo.setdefault(o, []).append(n + j)
top = [n + j for j, (op, a, b) in enumerate(c.gates) if op not in L.core.NONLINEAR_OPS and la[n + j] == 0]
print('top gates', len(top))
def mask(t):
    t = t ^ (L.ONES if t & 1 else 0)
    return sum(1 << i for i in range(8) if (t >> (1 << i)) & 1)
kinds = {}
for s in top:
    us = []
    for u in fo.get(s, []):
        op = c.gates[u - n][0]
        if op in L.core.NONLINEAR_OPS: us.append('A%d' % la[u])
        elif la[u] == 0: us.append('top')
        else: us.append('lin%d' % la[u])
    k = ','.join(sorted(set(us)))
    kinds[k] = kinds.get(k, 0) + 1
    print('%3d GL%d %-10s %s' % (s, lg[s], format(mask(T[s]), '08b'), ' '.join(us)))
print(kinds)
