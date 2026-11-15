"""P4: for a per-pair choice c and given top helper sets, search pre-inversion injection patterns
with amin + e + k <= TARGET over all 840 inversion-input bases (prereach logic; reach vectors from
units + columns of P'^T + up to (helpers of the transposed optimum + e) wild vectors).

    python3 choicepre.py CIRC C9 TARGET h1,h2,h3 [h1,h2,h3 ...]
"""
import itertools
import json
import sys

import pairscan
import preinj
import prereach


def main():
    path, cs, target = sys.argv[1], sys.argv[2], int(sys.argv[3])
    hsets = [tuple(int(t) for t in a.split(',')) for a in sys.argv[4:]]
    c = [int(ch) for ch in cs]
    gates, s, lvl1, pairs, X, P = pairscan.setup(path)
    forms, Xp0 = pairscan.choice(pairs, X, P, c)
    F = {f for f in forms if bin(f).count('1') > 1}
    # P as bitmasks over the 9 level-1 products, in pairscan's P index lists
    Pm = [sum(1 << i for i in idx) for idx in P]
    bases = []
    seen = set()
    for M in itertools.permutations(range(1, 16), 4):
        if preinj.rank(list(M)) < 4 or frozenset(M) in seen:
            continue
        seen.add(frozenset(M))
        bases.append(M)
    for hs in hsets:
        avail = F | set(hs) | {1 << i for i in range(8)}
        best = None
        for M in bases:
            Pp, Xp = prereach.matmul(M, Pm), prereach.matmul(M, Xp0)
            cols = [sum(1 << j for j in range(4) if (Pp[j] >> i) & 1) for i in range(9)]
            aT, hh = prereach.amin_T(cols)
            if aT is None:
                continue
            amin = aT + 5
            rk = preinj.rank(Xp)
            fixed = set(cols) | {1, 2, 4, 8}
            for e in range(0, max(0, target - amin - rk) + 1):
                done = False
                for k in range(rk, target - amin - e + 1):
                    B = prereach.patterns(Xp, avail, fixed, k, wild=len(hh) + e)
                    if B:
                        rec = dict(c=cs, helpers=list(hs), M=list(M), amin=amin, e=e, k=k, pre=amin + e + k, reach=list(B))
                        print(json.dumps(rec), flush=True)
                        best = min(best or 99, amin + e + k)
                        done = True
                        break
                if done:
                    break
        print(json.dumps(dict(c=cs, helpers=list(hs), best_pre=best)), flush=True)


if __name__ == '__main__':
    main()
