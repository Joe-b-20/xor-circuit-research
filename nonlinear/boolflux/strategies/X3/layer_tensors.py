"""X3 layer_tensors.py CIRCUIT: positive control of the tensor view on a real circuit.  For every sink AND:
x(x)n tensor, rank, T_b-coset, coset size / type from semi_members.tsv; then dim of the tensor span and of J_t."""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'H3'))
from wsat import Base, ONES
from gfinv import gpow
D = os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/')
b = Base(sys.argv[1])
P = lambda e: [gpow(x, e, 8) if x else 0 for x in range(256)]
def tt(f): return sum((f(x) & 1) << x for x in range(256))
X = [tt(lambda x, i=i: x >> i) for i in range(8)]
nn = P(238); NN = P(17)
nB = [tt(lambda x, i=i: nn[x] >> i) for i in (0, 2, 4, 5)]
Nb = [tt(lambda x, i=i: NN[x] >> i) for i in range(8)]
V0 = [sum(1 << x for x in range(256) if NN[x] == v) for v in set(NN)]
other = [ONES] + X + [X[i] & X[j] for i in range(8) for j in range(i + 1, 8)] + V0 + [X[i] & Nb[j] for i in range(8) for j in range(8)]
Bf = [(nB[j] & X[i], 1 << (8 * j + i)) for j in range(4) for i in range(8)]
ech = {}
def add(v, tag):
    while v:
        h = v.bit_length() - 1
        if h not in ech: ech[h] = (v, tag); return True
        v ^= ech[h][0]; tag ^= ech[h][1]
    return False
for v in other: add(v, 0)
for v, t in Bf: assert add(v, t)
def tensor(f):
    tag = 0
    while f:
        h = f.bit_length() - 1
        if h not in ech: return None
        f ^= ech[h][0]; tag ^= ech[h][1]
    return tag
te = [tuple(int(z, 16) if i else int(z) for i, z in enumerate(t.split(':'))) for t in open(D + 'bil_tb.txt').read().split('TE')[1].split()]
def cls(t):
    for p, v in te:
        if (t >> p) & 1: t ^= v
    return t
info = {}
for ln in open(D + 'semi_members.tsv'):
    if ln[0] == '#': continue
    p = ln.rstrip('\n').split('\t'); info[int(p[0], 16)] = (p[2], p[7] + p[8])
def rank(vs):
    bs = []
    for v in vs:
        for q in bs: v = min(v, v ^ q)
        if v: bs.append(v)
    return len(bs)
ts = []
for k in range(b.K):
    if b.cons[k]: continue
    t = tensor(b.andtab[k])
    if t is None: print('AND', k, 'not in the operand model'); continue
    rows = [(t >> (8 * j)) & 255 for j in range(4)]
    print('AND %2d tensor %08x rank %d coset %08x %s' % (k, t, rank(rows), cls(t), info.get(t, ('1', 'not member/semi'))))
    ts.append(t)
print('sinks', len(ts), 'tensor span dim', rank(ts), 'J_t dim', rank([cls(t) for t in ts]),
      'T_b inside:', rank(ts + [v for p, v in te]) == rank(ts))
