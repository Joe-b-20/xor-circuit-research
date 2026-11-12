"""Follow-ups: (1) classify BOTH operands vs only the off-path operand at needed cancellations;
(2) list exits on g->j paths with confined non-escaping off-path operand that do not cancel a needed block;
(3) circuits with smallest |union F_j|; (4) (E, R, U) triples among double-charge circuits."""
import os
from collections import Counter
from rev import *

KSTE = os.path.expanduser('~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor')
ROOT = os.path.expanduser('~/xor-circuit-research')

def kclass(r, off, e):
    sp, W = r['sp'], r['W']
    L = [l for l in blocks(sp[off]) if sp[off] & ~W[l] == 0]
    if not L:
        return 'notconf'
    return 'conf-nonesc' if any(sp[e] >> l & 1 for l in L) else 'escape'

def both_ops(r, gates, n):
    """per (g, j, e) at needed cancellations: class of each operand, and of off-path ones."""
    both, offc, other = Counter(), Counter(), []
    for g in range(n, n + len(gates)):
        if r['mult'][g] < 2:
            continue
        for j in r['F']:
            if g not in r['F'][j]:
                continue
            need = r['sp'][g] & ~r['W'][j]
            if not need:
                continue
            for e, lost in r['isexit'].items():
                if e == g or not (r['A'][j] >> e & 1):
                    continue
                a, b = gates[e - n]
                ona = [o for o in (a, b) if r['anc'][o] >> g & 1]
                if not ona:
                    continue
                if lost & need:
                    for o in (a, b):
                        both[kclass(r, o, e)] += 1
                    for o in (a, b):
                        if r['anc'][o] >> g & 1:
                            off = b if o == a else a
                            offc[kclass(r, off, e)] += 1
                else:
                    for o in ona:
                        off = b if o == a else a
                        if kclass(r, off, e) == 'conf-nonesc':
                            other.append((g, j, e, off, blocks(r['sp'][g]), blocks(lost),
                                          blocks(r['sp'][off]), [k for k in r['F'] if off in r['F'][k]]))
    return both, offc, other

if __name__ == '__main__':
    Mq = Q(3)
    n, gates = read_rot(os.path.join(ROOT, 'research/structure-2026-11-11/rotation/circuits/q3_28.txt'))
    r = analyse(Mq, gates)
    b, o, oth = both_ops(r, gates, n)
    print('Q_3 both operands', dict(b), 'off-path', dict(o), 'other conf-nonesc', oth)
    M = MC()
    tb, to, toth = Counter(), Counter(), []
    unions, triples = [], Counter()
    for fn in ('circuits_1.txt', 'circuits_2.txt', 'circuits_3.txt', 'circuits_depth5.txt'):
        lines = open(os.path.join(KSTE, fn)).read().splitlines()
        for i in range(0, len(lines), 50):
            g = read_kste_line(lines[i])
            r = analyse(M, g)
            if not r['ok']:
                continue
            b, o, oth = both_ops(r, g, 32)
            tb.update(b); to.update(o); toth += [(fn, i + 1) + x for x in oth]
            unions.append((r['union'], fn, i + 1, r['E'], r['R'], r['U'], r['c']))
            if r['R']:
                triples[(r['E'], r['R'], r['U'])] += 1
    print('MC both operands', dict(tb), 'off-path only', dict(to))
    print('MC exits on g->j paths, not cancelling a needed block, with confined non-escaping off-path operand:')
    for x in toth:
        print('  ', x)
    unions.sort()
    print('smallest unions (union, file, line, E, R, U, c):', unions[:5])
    print('(E,R,U) among double-charge circuits:', sorted(triples.items()))
