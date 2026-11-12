"""W1 check: a double-charged g in F_j 'collapses' in the window projection of sheet j if its projected value
is a unit of block j or equals the projection of another gate of F_j. Count double charges collapsing in
neither of their two projections."""
import os
from collections import Counter
from rev import *
import sys
SYM = len(sys.argv) < 2 or sys.argv[1] != 'earlier'   # 'earlier': collapse only onto an EARLIER gate (the authors' convention)

KSTE = os.path.expanduser('~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor')
ROOT = os.path.expanduser('~/xor-circuit-research')

def neither(M, r):
    n = M.n
    units = set(1 << i for i in range(n))
    cnt = 0
    for g in range(n, len(r['val'])):
        if r['mult'][g] < 2:
            continue
        coll = False
        for j in r['F']:
            if g not in r['F'][j]:
                continue
            pm = sum(M.bmask[b] for b in M.proj[j])
            pv = r['val'][g] & pm
            if pv in units or any(r['val'][h] & pm == pv for h in r['F'][j] if (h != g if SYM else h < g)):
                coll = True
        cnt += not coll
    return cnt

if __name__ == '__main__':
    Mq = Q(3)
    n, gates = read_rot(os.path.join(ROOT, 'research/structure-2026-11-11/rotation/circuits/q3_28.txt'))
    print('Q_3: double charges collapsing in neither projection:', neither(Mq, analyse(Mq, gates)))
    M = MC(); h = Counter()
    for fn in ('circuits_1.txt', 'circuits_2.txt', 'circuits_3.txt', 'circuits_depth5.txt'):
        lines = open(os.path.join(KSTE, fn)).read().splitlines()
        for i in range(0, len(lines), 50):
            r = analyse(M, read_kste_line(lines[i]))
            if r['ok'] and r['R']:
                h[(r['R'], neither(M, r))] += 1
    print('MixColumns (R, #neither): circuits', dict(h))
