"""P4: complemented AND operands in the 103's skeleton (XNOR freedom at no top cost).

Complementing a top form g (made by an XOR gate, so XNOR costs the same) changes
  level-1 AND (g+1) g' = g g' + g'   -> pre-inversion x-parts shift by g' on the targets with a_i,
  output AND  f (g+1) = f g + f      -> the bottom gets the inverse-side signal f as an extra input
                                       with column col(f g) (an extra bottom input costs >= 1 gate:
                                       XOR(M) = XOR(M^T) + n - 8 and n grows by one).
Inputs x0, x2, x7 cannot be complemented for free (NOT costs a gate).  For every pattern of
complements (choice A for all pairs) this prints the rank of the shifted x-parts X' (pre >= 10 +
rank X') and the number of extra bottom inputs; a pattern can only gain if (4 - rank) > extra.

    python3 compscan.py CIRC
"""
import itertools
import json
import sys

import bottomvar
import pairscan
import preinj


def main():
    path = sys.argv[1]
    gates, s, lvl1, pairs, X, P = pairscan.setup(path)
    _, col = bottomvar.bottom_columns(path)
    best = []
    hist = {}
    for comp in itertools.product(range(4), repeat=9):
        ok = True
        Xp = list(X)
        extra = 0
        fcols = []
        for i, (g, gp) in enumerate(pairs):
            cg, cgp = comp[i] & 1, comp[i] >> 1
            if (cg and bin(g).count('1') == 1) or (cgp and bin(gp).count('1') == 1):
                ok = False
                break
            sh = (gp if cg else 0) ^ (g if cgp else 0)
            for j in range(4):
                if i in P[j]:
                    Xp[j] ^= sh
            fc = (col[(i, 0)] if cg else 0) ^ (col[(i, 1)] if cgp else 0)
            if fc:
                extra += 1
                fcols.append(fc)
        if not ok:
            continue
        rk = preinj.rank(Xp)
        gain = (4 - rk) - extra
        hist[(rk, extra)] = hist.get((rk, extra), 0) + 1
        if gain > 0:
            best.append(dict(comp=comp, rank=rk, extra=extra, X=Xp, fcols=fcols))
    print(json.dumps(dict(hist={str(k): v for k, v in sorted(hist.items())}, gainers=len(best))))
    for b in best[:50]:
        print(json.dumps(b))


if __name__ == '__main__':
    main()
