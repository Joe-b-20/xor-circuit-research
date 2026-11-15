"""X3b x3b_v0ops.py FILE: for each top-level AND with operands in aff(x) + V0, the V0 part of each operand
modulo span(1, N, n): is it zero, which middle products / which K-classes N^k it uses.
Also: middle products (role MID) as functions of N (exponent classes k of N^k with nonzero coefficient)."""
import sys
from pathlib import Path
S = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies'
for d in ('G', 'C', 'H1'):
    sys.path.insert(0, str(S / d))
import xag
from xag import ONES, AFFX, NC, nC, V0, coeff

def reducer(basis):
    b = {}
    for t, tag in basis:
        v = t
        while v:
            h = v.bit_length() - 1
            if h in b: v ^= b[h][0]; tag ^= b[h][1]
            else: b[h] = (v, tag); break
    def red(t):
        tag = 0
        while t:
            h = t.bit_length() - 1
            if h not in b: return t, tag
            t ^= b[h][0]; tag ^= b[h][1]
        return 0, tag
    return red

c, ands, outs, otabs = xag.parse(sys.argv[1])
roles = [xag.role(A) for A in ands]
top = max(A['level'] for A in ands)
# basis: AFFX (tag 0) + V0 indicator basis (tag bits)
red = reducer([(t, 0) for t in AFFX] + [(t, 1 << i) for i, t in enumerate(V0)])
def v0part(t):
    r, tag = red(t)
    assert r == 0, 'operand not in aff(x)+V0'
    g = 0
    for i in range(len(V0)):
        if tag >> i & 1: g ^= V0[i]
    return g
redNn = reducer([(t, 0) for t in [ONES] + list(NC) + list(nC)])
mids = [k for k in range(len(ands)) if roles[k] == 'MID']
redM = reducer([(t, 0) for t in [ONES] + list(NC) + list(nC)] + [(ands[k]['tab'], 1 << i) for i, k in enumerate(mids)])
def Nexp(g):
    # exponents k (cyclotomic leaders mod 15 of N^k) present in g, via univariate coefficients c_{17k}
    return sorted({min((17 * k * (2 ** j)) % 255 for j in range(8)) // 17 for k in range(1, 15) if coeff(g, 17 * k)})
print('MID products:', [(k, ands[k]['level'], Nexp(ands[k]['tab'])) for k in mids])
extras = []
for k, A in enumerate(ands):
    if A['level'] != top: continue
    row = []
    for side in ('Lt', 'Rt'):
        g = v0part(A[side]); e, _ = redNn(g)
        if e:
            _, tag = redM(e)
            row.append('V0extra classes %s mids %s' % (Nexp(e), [mids[i] for i in range(len(mids)) if tag >> i & 1]))
            extras.append(e)
        else: row.append('in span(1,N,n)')
    print('top AND %2d: %s' % (k, ' | '.join(row)))
b = {}
n = 0
for e in extras:
    v = e
    while v:
        h = v.bit_length() - 1
        if h in b: v ^= b[h]
        else: b[h] = v; n += 1; break
print('dim span of V0 extras mod (1,N,n):', n)
