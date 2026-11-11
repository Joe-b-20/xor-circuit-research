"""Statistics of rank M[T,S] for MixColumns: how close is the requirement to a superconcentrator?

Usage: python3 research/structure-2026-11-11/restriction/rankstats.py
Prints, for |S| = |T| = k, the fraction of random pairs with full rank k, and the exact minimum
rank over byte-aligned and "one input byte x any outputs" families.
"""
import random
from itertools import combinations

from common import N, rank, read_matrix

M = read_matrix()
BYTE = [sum(1 << (8 * b + k) for k in range(8)) for b in range(4)]


def sub_rank(S, T):
    return rank([M[o] & S for o in range(N) if T >> o & 1])


def main():
    rng = random.Random(7)
    for k in (1, 2, 4, 8, 12, 16, 20, 24, 28, 32):
        trials = 4000
        full = 0
        deficit = 0
        for _ in range(trials):
            S = sum(1 << i for i in rng.sample(range(N), k))
            T = sum(1 << i for i in rng.sample(range(N), k))
            r = sub_rank(S, T)
            full += r == k
            deficit += k - r
        print(f"k={k:2d}: P(full rank) ~ {full / trials:.3f}, mean deficit {deficit / trials:.2f}")
    # S inside one input byte, T = one output byte: always |S| (blocks are invertible)
    ok = all(sub_rank(sum(1 << (8 * b + j) for j in range(8) if s >> j & 1), BYTE[c]) == bin(s).count("1")
             for b in range(4) for c in range(4) for s in range(256))
    print("S within one input byte, T = one output byte: rank = |S| always:", ok)
    # minimum over all 8-subsets S of inputs of rank M[all outputs-in-two-bytes, S]? sample
    worst = min(sub_rank(sum(1 << i for i in rng.sample(range(N), 16)),
                         BYTE[0] | BYTE[1]) for _ in range(3000))
    print("min sampled rank M[two output bytes, random 16 inputs] =", worst, "(16 would be superconcentrator-like)")


if __name__ == "__main__":
    main()
