"""CHECK: reconstruction quantities at primal single-block cuts carrying an exit (kste sample).

usage: python3 chi_mc.py STRIDE
At the cut (block k) of a primal exit: W = span of the off-block parts of the outputs meeting block k
(the forced label space); e = entries; e_min = fewest labels spanning a space containing W;
beta = L(S) - |S| from the fewest earlier labels summing to the exit value (single exit; minimal
combination), R ranges over the left-to-right chains and (for 4 labels) the balanced pairing of every
minimal combination; chi_up = min over these R (e_R by a greedy upper bound) of (|R| - |S| + e_R), e_R = fewest of labels + R-values
spanning W. chi_up >= chi, so far >= DL + e - chi_up is a valid (weaker) form of the ring analogue.
"""
import os
import sys
from collections import Counter
from itertools import combinations, permutations

from corpus_mc import KSTE, primal_split, mc


def rank(vs):
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def forced(k):
    low = mc.BLOCKMASK[k]
    return [t & ~low for t in mc.TARGETS if t & low and t & ~low]


def contains(vs, W):
    r = rank(vs)
    return all(rank(vs + [w]) == r for w in W)


def fewest_spanning(pool, W, lo):
    """Greedy UPPER bound on the fewest pool vectors whose span contains W (exact when it returns dim W)."""
    pool = sorted(set(pool))
    S = []
    def gain(S2):
        r = rank(S2)
        return sum(1 for w in W if rank(S2 + [w]) == r)
    while not contains(S, W):
        best = max(pool, key=lambda x: (gain(S + [x]), -rank(S + [x])))
        S.append(best)
        pool.remove(best)
    return len(S)


def main():
    stride = int(sys.argv[1])
    KS = [int(x) for x in sys.argv[2:]] or [2]
    out = Counter()
    nl = 0
    for fn in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"):
        p = os.path.join(KSTE, fn)
        if not os.path.exists(p):
            continue
        for line in open(p):
            if not line.strip():
                continue
            nl += 1
            if nl % stride:
                continue
            gates = mc.parse_pairs(line)
            r = mc.analyse(gates)
            if r is None or r["distinct"] != len(gates) or r["dead"]:
                continue
            for k in KS:
                vals, st, labels, exits = primal_split(gates, k)
                if len(exits) != 1:
                    continue
                W = forced(k)
                dimW = rank(W)
                labs = [x for _, x in labels]
                emin = fewest_spanning(labs, W, dimW)
                gi = exits[0][0]
                v = vals[32 + gi]
                early = sorted(set(x for i, x in labels if i < gi))
                combos = []
                for t in range(1, 7):
                    for c in combinations(early, t):
                        s = 0
                        for y in c:
                            s ^= y
                        if s == v:
                            combos.append(c)
                    if combos:
                        break
                if not combos:
                    out[("k%d" % k, "no combo <= 6")] += 1
                    continue
                t = len(combos[0])
                best = None
                for c in combos:
                    Rs = []
                    for perm in permutations(c):
                        acc, rv = perm[0], []
                        for y in perm[1:]:
                            acc ^= y
                            rv.append(acc)
                        Rs.append(rv)
                    if t == 4:
                        for (a, b), (cc, d) in [((c[0], c[1]), (c[2], c[3])), ((c[0], c[2]), (c[1], c[3])),
                                                ((c[0], c[3]), (c[1], c[2]))]:
                            Rs.append([a ^ b, cc ^ d, v])
                    for rv in Rs:
                        eR = fewest_spanning(labs + rv, W, dimW)
                        val = len(rv) - 1 + eR
                        best = val if best is None else min(best, val)
                beta = t - 2
                key = ("k%d" % k, "mono" if r["monotone"] else "nonmono", "e%d" % st["e"], "emin%d" % emin,
                       "beta%d" % beta, "chi_up%d" % best, "chi-e=%d" % (best - st["e"]),
                       "near%d" % (st["f"] + st["h"]))
                out[key] += 1
    print("lines %d" % nl)
    for k, v in out.most_common(30):
        print("  %4d %s" % (v, " ".join(k)))


if __name__ == "__main__":
    main()
