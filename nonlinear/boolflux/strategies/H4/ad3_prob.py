"""Problem files for track G's llay.c (exact coordinate descent): AND levels 1 + 2 of the
GF(4)-norm (AD3) route.  E = span(1, x); stage-1 slots: k1 products of x-forms with N = x^17
required in span(1, x, S1); layer: k2 products with operands in O = span(x, N); targets:
x^84 (8 coords) and N4 = x^85 (2 coords).  [Level 3 = x^84 * N4^2 is 12 more ANDs.]

usage: ad3_prob.py K1 K2 OUT [--o-extra none|n4]
"""
import sys

import cover1
from ad3sat import XT, NT, ADJ, N4T, basis_of
from h4lib import ONES


def hexw(t):
    return ' '.join('%x' % ((t >> (64 * w)) & ((1 << 64) - 1)) for w in range(4))


def main():
    k1, k2, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    Nb = basis_of([t for t in NT if t])
    E = [ONES] + XT
    O = XT + Nb
    T = basis_of(ADJ + [t for t in N4T if t])
    lines = ['4 256', str(len(E))] + [hexw(t) for t in E]
    lines += [str(len(O))] + [hexw(t) for t in O]
    lines += [str(len(T))] + [hexw(t) for t in T]
    lines += [str(k2), str(k1), '8'] + [hexw(t) for t in XT] + [str(len(Nb))] + [hexw(t) for t in Nb]
    open(out, 'w').write('\n'.join(lines) + '\n')
    print(out, 'nT', len(T))


if __name__ == '__main__':
    main()
