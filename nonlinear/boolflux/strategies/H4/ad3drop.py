"""For a zero-deficit ad3fix state: which level-1 products can be dropped (deficit recomputed with
E = span(1, x, N, L1 minus one product); N must stay in span(1, x, L1)).  Also reports the
junk dimension J = dim((T + M)/M) and dim of span(L1) mod V_N.
usage: ad3drop.py JSONL [INDEX...]"""
import json
import sys

import cover1
import ad3mem as A
from ad3sat import XT, NT, ADJ, N4T, basis_of, level_tables
from h4lib import ONES


def state_vecs(state, L1x):
    out = []
    for m in state:
        if m[0] == 'n': out.append(A.nprod(m[1], m[2]))
        elif m[0] == 'x': continue
        else: out.append(A.member(m[1], tuple(m[2])))
    return out


def deficit(E, vecs, T):
    Er = cover1.rowspace(E)
    v = [cover1.reduce(x, Er) for x in vecs]
    t = [cover1.reduce(x, Er) for x in T]
    return len(cover1.rowspace(v + t)) - len(cover1.rowspace(v))


def main():
    lines = open(sys.argv[1]).read().splitlines()
    idx = [int(i) for i in sys.argv[2:]] or range(len(lines))
    T = ADJ + [t for t in N4T if t]
    for i in idx:
        r = json.loads(lines[i])
        if r['deficit'] != 0: continue
        L1 = level_tables(r['l1file'], 1)
        L1 += [A.lin(m[1], XT) & A.lin(m[2], XT) for m in r['state'] if m[0] == 'x']
        vecs = state_vecs(r['state'], None)
        base = [ONES] + XT + A.Nb
        d0 = deficit(base + L1, vecs, T)
        drops = []
        for j in range(len(L1)):
            L = L1[:j] + L1[j + 1:]
            Nok = all(cover1.reduce(t, cover1.rowspace([ONES] + XT + L)) == 0 for t in NT)
            drops.append((j, Nok, deficit(base + L, vecs, T)))
        inf, J = A.junk([cover1.reduce(v, A.E0) for v in vecs])
        print(i, 'l1', len(L1), 'deficit', d0, 'J', J, 'drops', drops)


if __name__ == '__main__':
    main()
