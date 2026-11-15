"""X3 zprep_pref.py CIRCUIT [CIRCUIT2 for the middle]: zcos input with J = span(1, x, prefix ANDs), prefix = the
non-sink ANDs of CIRCUIT (or: level-1 ANDs of CIRCUIT + ANDs of levels 2.. of CIRCUIT2 that are functions of N)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'H3'))
from wsat import Base, ONES
from gfinv import gpow
b = Base(sys.argv[1])
P = lambda e: [gpow(x, e, 8) if x else 0 for x in range(256)]
def tt(tab, i): return sum(((tab[x] >> i) & 1) << x for x in range(256))
def indep(vs):
    out = []; bas = []
    for v in vs:
        r = v
        for q in bas: r = min(r, r ^ q)
        if r: bas.append(r); bas.sort(reverse=True); out.append(v)
    return out
X = b.tab[1:1 + b.n]
N_ = P(17)
def isN(t):   # function of N?
    seen = {}
    for x in range(256):
        v = (t >> x) & 1
        if seen.setdefault(N_[x], v) != v: return False
    return True
if len(sys.argv) > 2:
    b2 = Base(sys.argv[2])
    E = [b.andtab[k] for k in range(b.K) if b.level[k] == 1] + [b2.andtab[k] for k in range(b2.K) if b2.level[k] > 1 and isN(b2.andtab[k])]
else:
    E = [b.andtab[k] for k in range(b.K) if b.cons[k]]
J = indep([ONES] + X + E)
T = b.out
# x bits in the order of gfinv (bit i of the integer x): rebuild from scratch so that families match zcos
Xs = [tt(list(range(256)), i) for i in range(8)]
assert len(indep([ONES] + X + Xs)) == 9
n_ = P(238); z_ = P(33)
nB = indep([tt(n_, i) for i in range(8)]); NB = indep([tt(N_, i) for i in range(8)]); Z = [tt(z_, i) for i in range(8)]
out = []
for name, vs in (('J', J), ('T', T), ('X', Xs), ('Z', Z), ('n', nB), ('N', NB)):
    out.append('%s %d' % (name, len(vs)))
    for v in vs: out.append(' '.join('%016x' % ((v >> (64 * w)) & (2**64 - 1)) for w in range(4)))
sys.stdout.write('\n'.join(out) + '\n')
print('prefix ANDs', len(E), 'dim J', len(J), file=sys.stderr)
