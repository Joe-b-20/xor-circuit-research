"""CHECK (phase 7, main agent): what the gates removed at 0, 1 or 2 blocks are, and the third removal category.

For a given circuit: for each gate its block support B(g), Z(g) (blocks where it is removed, first-producer
convention), whether it reads a pure-block operand (and which block), and whether its removal at b is LOCAL
(one of its operands or itself lies in block b alone) or NONLOCAL (a coincidence with an unrelated signal).
Then for each block b the restricted circuit built from first producers: U_b = gates useful for the restricted
outputs, dead_b = S_b - U_b (new value, not needed after simplification).
usage: python3 jclass.py SPEC [-v]
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jstats import get, zero_mask  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "compose", "compat"))
from clib import ROWS, bm, blocks, desc, values  # noqa: E402


def restrict(g, vals, b):
    keep = zero_mask([b])
    rep = {}
    for i in range(32):
        rep.setdefault((1 << i) & keep, i)
    rep.setdefault(0, -1)
    first = {}
    removed = set()
    for gi, (a, c) in enumerate(g):
        x = 32 + gi
        p = vals[x] & keep
        if p in rep:
            removed.add(x)
        else:
            rep[p] = x
            first[x] = (a, c)
    cls = lambda s: rep[vals[s] & keep] if s >= 0 else -1
    roots = {cls(rep[r & keep]) for r in ROWS.values() if (r & keep) in rep}
    useful, st = set(), [r for r in roots if r >= 32]
    while st:
        s = st.pop()
        if s in useful:
            continue
        useful.add(s)
        for o in first[s]:
            co = cls(o)
            if co >= 32:
                st.append(co)
    return removed, useful


def main(spec, verbose):
    g = get(spec)
    vals = values(g)
    n = len(vals)
    Z = {x: set() for x in range(32, n)}
    U, dead = [], []
    for b in range(8):
        rem, use = restrict(g, vals, b)
        for x in rem:
            Z[x].add(b)
        U.append(len(use))
        dead.append(len(g) - len(rem) - len(use))
    print("== %s G=%d" % (spec, len(g)))
    print("  useful U_b:", U, " dead (new but unneeded):", dead)
    pure = lambda s: len(blocks(vals[s])) == 1
    tally = Counter()
    for x in range(32, n):
        a, c = g[x - 32]
        loc = set()
        for b in Z[x]:
            if any(vals[s] & ~bm(b) == 0 for s in (a, c, x)):
                loc.add(b)
        kind = "%d-blk|Z|=%d" % (len(blocks(vals[x])), len(Z[x]))
        kind += "" if Z[x] == loc else " nonlocal%d" % len(Z[x] - loc)
        kind += " pureops%d" % sum(pure(s) for s in (a, c))
        tally[kind] += 1
        if verbose:
            print("  g%-3d %-34s Z=%s ops %s | %s" % (x, desc(vals[x]), sorted(Z[x]), desc(vals[a]), desc(vals[c])))
    for k, v in sorted(tally.items()):
        print("  %-40s %d" % (k, v))


if __name__ == "__main__":
    main(sys.argv[1], "-v" in sys.argv)
