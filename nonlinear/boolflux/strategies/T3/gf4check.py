#!/usr/bin/env python3
"""T3: test the GF(4) reading of the AD3 circuits:
   x^-1 = x^170 * x^84,  x^170 = Delta^-1 in GF(4), level-3 products = Karatsuba GF(4) x GF(256).
Checks: are the level-3 Q operands the functionals Tr(w x^170), w in GF(4)*?  are the R operands
Tr(c x^84) exactly (c in GF(256)), or only on supp(Q)?  are all Tr(c x^84) in S (span of signals of
AND level <= 2)?
    python3 gf4check.py CIRCUIT"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import load, metrics, _gpow, _gmul, ONES   # noqa: E402
from pairs import and_levels, Basis                                 # noqa: E402


def tr(c):
    """function table of x -> Tr(c * f(x)) for f given later"""


def trace(z):
    t = 0; y = z
    for _ in range(8):
        t ^= y; y = _gmul(y, y)
    return t  # 0 or 1


def table(f):
    v = 0
    for x in range(256):
        if f(x) & 1: v |= 1 << x
    return v


def main():
    c = load(sys.argv[1]); n = c.n; t = c.tables(); al = and_levels(c)
    # input bit convention: check that the S-box input x maps as integer -> core input tables
    # core.input_tables: bit i of x is input i?  we test both conventions via the N span
    P170 = [_gpow(x, 170) for x in range(256)]
    P84 = [_gpow(x, 84) for x in range(256)]
    TQ = {table(lambda x, w=w: trace(_gmul(w, P170[x]))): w for w in range(1, 256)}
    TR = {table(lambda x, cc=cc: trace(_gmul(cc, P84[x]))): cc for cc in range(1, 256)}
    S = Basis([ONES] + [t[s] for s in range(n + len(c.gates)) if al[s] <= 2])
    print(metrics(c), 'dim S', len(S.gens))
    print('all Tr(c x^84) in S:', all(S.reduce(v) == 0 for v in TR))
    print('all Tr(w x^170) in S:', sum(S.reduce(v) == 0 for v in TQ), 'of', len(TQ))
    for g in range(n, n + len(c.gates)):
        op, a, b = c.gates[g - n]
        if op != 8 or al[g] != 3: continue
        out = []
        for s in (a, b):
            v = t[s]
            lab = None
            for u in (v, v ^ ONES):
                if u in TQ: lab = 'Q(w=%d)' % TQ[u]
                elif u in TR: lab = 'R(c=%d)' % TR[u]
            out.append(lab or 'other')
        # R only on supp(Q)?
        ext = ''
        if 'other' in out:
            ia = 0 if out[0] == 'other' else 1
            q = t[(a, b)[1 - ia]]; r = t[(a, b)[ia]]
            m = [cc for v, cc in TR.items() if (v ^ r) & q == 0 or (v ^ r ^ ONES) & q == 0]
            ext = ' R agrees with Tr(c x^84) on supp(Q) for c in %s' % m[:6]
        print('s%d: %s x %s%s' % (g, out[0], out[1], ext))


if __name__ == '__main__':
    main()
