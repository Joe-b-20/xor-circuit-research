"""CHECK: labels at single-group cuts of the MixColumns mirror, by group support; required span.

usage: python3 labels_mc.py CIRCUIT [order] [groups...]
For group k prints: the minimal label span forced by the rows (span of the s-parts of the rows meeting
w^k), its dimension, the rank of the observed labels, whether the labels lie in a sum of pure group
spaces, and every label with its group support and description.
"""
import os
import sys
from collections import Counter

from mirror_mc import ROWS, desc, groups, mirror, rank, split, mc


def forced_span(k):
    low = 15 << (4 * k)
    return [r & ~low for r in ROWS.values() if r & low and r & ~low]


def main():
    path = sys.argv[1]
    order = sys.argv[2] if len(sys.argv) > 2 else "fwd"
    ks = [int(x) for x in sys.argv[3:]] or list(range(8))
    gates = mc.parse_ncff(path) if path.endswith(".txt") and "circ" in path else None
    tot, red, _ = mirror(gates, order)
    for k in ks:
        st, labels, exits, _ = split(red, [k])
        fs = forced_span(k)
        labs = [x for _, x in labels]
        both = rank(fs + labs)
        sup = Counter("".join(map(str, sorted(groups(x)))) for x in labs)
        mixed = [x for x in labs if len(groups(x)) >= 2]
        print("group %d: f %d h %d e %d | forced dim %d, label rank %d, rank(forced+labels) %d; "
              "label supports %s" % (k, st["f"], st["h"], st["e"], rank(fs), st["rank"], both, dict(sup)))
        for x in mixed:
            print("    mixed label [%s]" % desc(x))


if __name__ == "__main__":
    main()
