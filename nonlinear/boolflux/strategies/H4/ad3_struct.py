"""Structure of AND-depth-3 circuits: in which spans do the operands of each AND level lie?
usage: ad3_struct.py FILE"""
import sys

from h4lib import pw, inv, ONES
import cover1
sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear')
from boolflux import core


def tt_of(func, k):
    t = 0
    for p in range(256):
        if (func(p) >> k) & 1: t |= 1 << p
    return t


def coords(func):
    return [tt_of(func, k) for k in range(8)]


X = coords(lambda p: p)
NN = [t for t in coords(lambda p: pw(p, 17) if p else 0) if t]
ADJ = coords(lambda p: pw(p, 84) if p else 0)
N4 = [t for t in coords(lambda p: pw(p, 85) if p else 0) if t]
INV = coords(inv)


def rank(vs):
    return len(cover1.rowspace(vs))


def inspan(v, vs):
    return rank(vs + [v]) == rank(vs)


def main(f):
    c = core.read_ncff(f)
    tabs = c.tables()
    la = [0] * 8
    ands = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    opnds = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for j, (op, a, b) in enumerate(c.gates):
        l = (1 if op in core.NONLINEAR_OPS else 0) + max(la[a], la[b]); la.append(l)
        if op in core.NONLINEAR_OPS:
            ands[l].append(tabs[8 + j]); opnds[l].append((tabs[a], tabs[b]))
    one = [ONES]
    base = one + X
    print('levels', {l: len(v) for l, v in ands.items() if v})
    L1 = ands[1]
    print('N in span(1,x,L1):', all(inspan(t, base + L1) for t in NN), ' dim span(1,x,L1) =', rank(base + L1))
    S2 = base + NN
    ok2 = [inspan(a, S2) and inspan(b, S2) for a, b in opnds[2]]
    print('L2 operands in span(1,x,N):', sum(ok2), '/', len(ok2))
    S2b = base + NN + L1
    print('L2 operands in span(1,x,L1):', sum(inspan(a, S2b) and inspan(b, S2b) for a, b in opnds[2]))
    E2 = base + L1 + ands[2]
    print('x^84 in span(1,x,L1,L2):', [inspan(t, E2) for t in ADJ])
    print('N4 in span(1,x,L1,L2):', [inspan(t, E2) for t in N4])
    S3 = base + NN + ADJ + N4
    print('L3 operands in span(1,x,N,x^84,N4):', sum(inspan(a, S3) and inspan(b, S3) for a, b in opnds[3]), '/', len(opnds[3]))
    S3b = base + L1 + ands[2]
    print('L3 operands in span(1,x,L1,L2):', sum(inspan(a, S3b) and inspan(b, S3b) for a, b in opnds[3]))
    # level-3 operand pair types
    for a, b in opnds[3]:
        ta = 'P' if inspan(a, base + ADJ) else ('m' if inspan(a, one + N4) else '?')
        tb = 'P' if inspan(b, base + ADJ) else ('m' if inspan(b, one + N4) else '?')
        print(' L3 pair', ta, tb, 'a in span(1,x,N,P,N4)', inspan(a, S3), 'b', inspan(b, S3))


if __name__ == '__main__':
    main(sys.argv[1])
