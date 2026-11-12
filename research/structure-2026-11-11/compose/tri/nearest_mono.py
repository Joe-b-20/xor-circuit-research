"""CHECK: block-monotone kste circuits whose gate-value sets are closest to a given circuit's.

usage: python3 nearest_mono.py FILE LINE [TOP=5]   (own 1-based line numbers)
Prints, for the closest monotone circuits, the values only in the given circuit and only in the other.
"""
import os
import sys

from show_tri import KSTE, desc, load, mc

FILES = ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt")


def valset(gates):
    vals = [1 << i for i in range(32)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    return set(vals[32:])


def main():
    fn, ln = sys.argv[1], int(sys.argv[2])
    top = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    A = valset(load(fn, ln))
    best = []
    for f in FILES:
        for i, line in enumerate(open(os.path.join(KSTE, f)), 1):
            g = mc.parse_pairs(line)
            V = valset(g)
            d = len(A ^ V)
            if best and d > best[-1][0] and len(best) >= 50:
                continue
            r = mc.analyse(g)
            if r is None or not r["monotone"]:
                continue
            best.append((d, f, i, V))
            best.sort(key=lambda x: x[0])
            best = best[:50]
    for d, f, i, V in best[:top]:
        print("%s line %d: |sym diff| = %d" % (f, i, d))
        print("   only in given:", "; ".join(sorted(desc(v) for v in A - V)))
        print("   only in mono :", "; ".join(sorted(desc(v) for v in V - A)))


if __name__ == "__main__":
    main()
