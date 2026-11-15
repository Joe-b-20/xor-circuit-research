"""X3 zprep.py: tables for zcos.c.  Writes hex 256-bit tables:
 line 'J k' then k tables: basis of the free junk space Aff + Quad(x) + V0 (functions of N)
 line 'T 8' the 8 output tables (inversion x^254; the AES affine map is free)
 line 'X 8', 'Z 8' (coordinates of x^33 = x^16 N: the class-9 quadratics), 'n 4' (independent coordinates of N^-1),
 'N 4' (independent coordinates of N)."""
import sys
from gfinv import gpow
P = lambda e: [gpow(x, e, 8) if x else 0 for x in range(256)]
def tt(tab, i): return sum(((tab[x] >> i) & 1) << x for x in range(256))
ONE = (1 << 256) - 1
X = [tt(list(range(256)), i) for i in range(8)]
inv = P(254); n_ = P(238); N_ = P(17); z_ = P(33)
def indep(vs):
    out = []; bas = []
    for v in vs:
        r = v
        for b in bas: r = min(r, r ^ b)
        if r: bas.append(r); bas.sort(reverse=True); out.append(v)
    return out
T = [tt(inv, i) for i in range(8)]
nB = indep([tt(n_, i) for i in range(8)]); NB = indep([tt(N_, i) for i in range(8)]); Z = [tt(z_, i) for i in range(8)]
assert len(nB) == 4 and len(NB) == 4 and len(indep(Z)) == 8
quad = [X[i] & X[j] for i in range(8) for j in range(i + 1, 8)]
# V0: all functions of N: indicator of each value of N
vals = sorted(set(N_))
V0 = [sum(1 << x for x in range(256) if N_[x] == v) for v in vals]
J = indep([ONE] + X + quad + V0)
out = []
for name, vs in (('J', J), ('T', T), ('X', X), ('Z', Z), ('n', nB), ('N', NB)):
    out.append('%s %d' % (name, len(vs)))
    for v in vs: out.append(' '.join('%016x' % ((v >> (64 * w)) & (2**64 - 1)) for w in range(4)))
sys.stdout.write('\n'.join(out) + '\n')
print('dims J', len(J), file=sys.stderr)
