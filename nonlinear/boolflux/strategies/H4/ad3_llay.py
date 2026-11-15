"""Hand an ad3fix.py state to track G's llay.c (exact coordinate descent over ALL products of
O x O, O = span(x, N)) with E = span(1, x, L1 of the state's file), targets x^84 and N4.
usage: ad3_llay.py JSONL INDEX OUTPREFIX   (writes OUTPREFIX.prob and OUTPREFIX.init)
"""
import json
import sys

import ad3mem as A
from ad3sat import XT, NT, ADJ, N4T, basis_of, level_tables
from ad3_prob import hexw
from h4lib import ONES


def xcoef(t):
    """coefficients of a linear (no constant) x-function over XT"""
    c = 0
    for i in range(8):
        # value at the unit vector e_i
        if (t >> (1 << i)) & 1: c |= 1 << i
    assert sum(1 << p for p in range(256) if bin(p & c).count('1') & 1) == t
    return c


def main():
    rec = json.loads(open(sys.argv[1]).read().splitlines()[int(sys.argv[2])])
    out = sys.argv[3]
    ol1 = len(sys.argv) > 4 and sys.argv[4] == 'ol1'
    L1 = level_tables(rec['l1file'], 1)
    L1 += [A.lin(m[1], XT) & A.lin(m[2], XT) for m in rec['state'] if m[0] == 'x']
    rec['state'] = [m for m in rec['state'] if m[0] != 'x']
    E = [ONES] + XT + L1
    O = XT + A.Nb + (L1 if ol1 else [])
    T = basis_of(ADJ + [t for t in N4T if t])
    K = len(rec['state'])
    lines = ['4 256', str(len(E))] + [hexw(t) for t in E]
    lines += [str(len(O))] + [hexw(t) for t in O]
    lines += [str(len(T))] + [hexw(t) for t in T]
    lines += [str(K), '0']
    open(out + '.prob', 'w').write('\n'.join(lines) + '\n')
    init = ['init']
    for m in rec['state']:
        if m[0] == 'n':
            init.append('%x %x' % (m[1] << 8, m[2] << 8))
        else:
            lam, (g0, g1) = m[1], m[2]
            a0, a1 = A.COMP[lam]
            init.append('%x %x' % (xcoef(a0) | (g0 << 8), xcoef(a1) | (g1 << 8)))
    open(out + '.init', 'w').write('\n'.join(init) + '\n')
    print(out, 'K', K)


if __name__ == '__main__':
    main()
