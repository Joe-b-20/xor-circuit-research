"""llay.c problem with BOTH levels movable: K1 stage-1 slots (x-form products, N required in
their span) and K2 layer slots (products over O = span(x, N)), targets x^84 and N4.
Init: stage-1 = the level-1 products of a record's L1 file minus the indices in DROP (plus its
extra 'x' slots), layer = the record's level-2 state.
usage: ad3_llay2.py JSONL INDEX OUTPREFIX DROP(comma list or -)"""
import json
import sys

import ad3mem as A
from ad3sat import XT, NT, ADJ, N4T, basis_of
from ad3_prob import hexw
from ad3_llay import xcoef
from ad3build import level1_operands
from h4lib import ONES


def strip(t):
    return t ^ ONES if t & 1 else t


def main():
    rec = json.loads(open(sys.argv[1]).read().splitlines()[int(sys.argv[2])])
    out = sys.argv[3]
    drop = set() if sys.argv[4] == '-' else {int(i) for i in sys.argv[4].split(',')}
    ops = [(xcoef(strip(a)), xcoef(strip(b))) for i, (a, b) in enumerate(level1_operands(rec['l1file']))
           if i not in drop]
    ops += [(m[1], m[2]) for m in rec['state'] if m[0] == 'x']
    layer = [m for m in rec['state'] if m[0] != 'x']
    E = [ONES] + XT
    O = XT + A.Nb
    T = basis_of(ADJ + [t for t in N4T if t])
    lines = ['4 256', str(len(E))] + [hexw(t) for t in E]
    lines += [str(len(O))] + [hexw(t) for t in O]
    lines += [str(len(T))] + [hexw(t) for t in T]
    lines += [str(len(layer)), str(len(ops)), '8'] + [hexw(t) for t in XT] + [str(len(A.Nb))] + [hexw(t) for t in A.Nb]
    open(out + '.prob', 'w').write('\n'.join(lines) + '\n')
    init = ['init']
    for m in layer:
        if m[0] == 'n':
            init.append('%x %x' % (m[1] << 8, m[2] << 8))
        else:
            lam, (g0, g1) = m[1], m[2]
            a0, a1 = A.COMP[lam]
            init.append('%x %x' % (xcoef(a0) | (g0 << 8), xcoef(a1) | (g1 << 8)))
    open(out + '.init', 'w').write('\n'.join(init) + '\n')
    open(out + '.inits1', 'w').write('\n'.join(['inits1'] + ['%x %x' % o for o in ops]) + '\n')
    print(out, 'K1', len(ops), 'K2', len(layer))


if __name__ == '__main__':
    main()
