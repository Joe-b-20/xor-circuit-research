"""Reviewer's extra checks (machine review, phase 7). Read-only scan by stride; no search.
(1) single-block (pure) gates that are ancestors of a sheet whose window does not contain their block
    (sharing through an exit that the multi-block census of ACCOUNT section 3 does not see);
(2) the pair-local charge inequality |F_j u F_k| >= 20, i.e. (|F_j|-10)+(|F_k|-10) >= |F_j n F_k|, for every pair
    of sheets with a common charged gate; and P(1,2) for comparison.
usage: python3 rv_extra.py STRIDE
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvlib import BLK, WIN, ancestors_of_rows, check, pure_block, values  # noqa
from rv_checks import get, specs  # noqa


def main():
    stride = int(sys.argv[1])
    pure_out = Counter()
    pure_out_circ = Counter()
    pairloc = Counter()
    worst = None
    n = 0
    for sp in specs(stride):
        name, g = get(sp)
        if not all(check(g)):
            continue
        n += 1
        v = values(g)
        anc = ancestors_of_rows(g, v)
        mono = all((v[32 + k] & 0) == 0 and
                   {j for j in range(8) if v[32 + k] & BLK[j]} == {j for j in range(8) if (v[a] | v[c]) & BLK[j]}
                   for k, (a, c) in enumerate(g))
        pat = Counter()
        for x in range(32, len(v)):
            b = pure_block(v[x])
            if b is None:
                continue
            bad = tuple(j for j in range(8) if x in anc[j] and b not in WIN[j])
            if bad:
                pat[(b, bad)] += 1
        pure_out_circ[(mono, tuple(sorted(pat.items())))] += 1
        F = {j: {x for x in anc[j] if v[x] & BLK[j]} for j in range(8)}
        for j in range(8):
            for k in range(j + 1, 8):
                I = len(F[j] & F[k])
                if I:
                    s = len(F[j]) + len(F[k]) - 20 - I
                    pairloc[((j, k), s >= 0)] += 1
                    if worst is None or s < worst[0]:
                        worst = (s, name, (j, k), len(F[j]), len(F[k]), I)
    print("circuits:", n)
    print("(block-monotone, pure gates serving a sheet outside their window: ((block, such sheets), count)) -> #circuits")
    for k, c in pure_out_circ.most_common():
        print("    ", c, k)
    print("pair-local inequality |F_j|+|F_k|-20 >= |F_j n F_k| over pairs with a common charged gate: ((j,k), holds) -> #")
    for k, c in sorted(pairloc.items()):
        print("    ", k, c)
    print("least slack (slack, circuit, pair, |F_j|, |F_k|, |F_j n F_k|):", worst)


if __name__ == "__main__":
    main()
