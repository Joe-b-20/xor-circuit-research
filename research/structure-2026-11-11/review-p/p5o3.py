"""CHECK (reviewer; finite, abstract interface only): refute/REPORT.md P5, case o = 3.
Four independent labels l1..l4 (bits 0..3); E = {even number of l1..l3} + any l4 (so l4 in E, o = 3).
For every set S of three or four weight-3 exit values and EVERY staging (label order, exit slots after
their last label, order of exits), compute chi = min over replacements R of |R| - |S| + tau_R exactly
(R-gates placed before the exit they serve, reading labels already present and earlier R-values;
tau_R = 3 if labels u R-values contain 3 independent E-elements, else 4). Claim: chi <= 5 always.
"""
from itertools import combinations, permutations, product

LAB = [1, 2, 4, 8]


def inE(v):
    return v and bin(v & 7).count("1") % 2 == 0


def rank(vs):
    b = []
    for v in vs:
        for x in b:
            v = min(v, v ^ x)
        if v:
            b.append(v)
    return len(b)


def tau(vals):
    return 3 if rank([v for v in vals if inE(v)]) == 3 else 4


def best(events, nS):
    # events: list of ('L', v) or ('X', v); DFS over gates, limit |R| <= nS + 2 (chi <= 5 needs that or tau 3)
    res = [99]

    def go(i, have, nR):
        if nR - nS + 3 >= res[0]:
            return
        if i == len(events):
            res[0] = min(res[0], nR - nS + tau(have))
            return
        kind, v = events[i]
        if kind == 'L':
            go(i + 1, have | {v}, nR)
            return
        if v in have:
            go(i + 1, have, nR)
        # add one gate now (before this exit) and retry
        if nR < nS + 3:
            for a, b in combinations(sorted(have), 2):
                w = a ^ b
                if w and w not in have:
                    go(i, have | {w}, nR + 1)

    go(0, frozenset(), 0)
    return res[0]


def main():
    trip = [sum(LAB[j] for j in c) for c in combinations(range(4), 3)]
    worst = 0
    for k in (3, 4):
        for S in combinations(trip, k):
            for order in permutations(LAB):
                pos = {v: i for i, v in enumerate(order)}
                last = [max(pos[b] for b in LAB if b & x) for x in S]
                if any(l < 2 for l in last):
                    continue
                # exits: interleave by slot (after label index) then any order within a slot
                for perm in permutations(range(k)):
                    if any(last[perm[a]] > last[perm[a + 1]] for a in range(k - 1)):
                        continue
                    ev = []
                    xi = 0
                    for t, lv in enumerate(order):
                        ev.append(('L', lv))
                        while xi < k and last[perm[xi]] == t:
                            ev.append(('X', S[perm[xi]]))
                            xi += 1
                    c = best(ev, k)
                    if c > worst:
                        worst = c
                        print("new worst chi %d: S=%s order=%s" % (c, [format(x, '04b') for x in S], order))
    print("max chi over all sets/stagings: %d (claim <= 5)" % worst)


if __name__ == "__main__":
    main()
