"""CHECK: (|L_k|, |P|), near1 = f+h, entries, distinct labels, waste over a kste corpus sample.

usage: python3 corpus.py BLOCK STRIDE
"""
import os
import re
import sys
from collections import Counter

from clib import KSTE, bm, check, cut
from waste import waste  # noqa: F401  (uses load; we inline below)


def wst(g, vals, k):
    low = bm(k)
    seen = {0} | {(1 << i) & ~low for i in range(32)}
    w = 0
    for gi in range(len(g)):
        p = vals[32 + gi] & ~low
        w += p in seen
        seen.add(p)
    return w


def main():
    k, stride = int(sys.argv[1]), int(sys.argv[2])
    rows = []
    for fn in ["circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"]:
        ls = [l for l in open(os.path.join(KSTE, fn)) if l.strip()]
        for n in range(0, len(ls), stride):
            g = [(int(a), int(b)) for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", ls[n])]
            ok, red = check(g)
            if not (ok and red):
                continue
            vals, kind, labels = cut(g, k)
            c = Counter(kind.values())
            L = c["f"] + c["h"] + c["e"]
            rows.append((fn, n + 1, len(g), L, c["o"] + c["x"], c["x"], c["f"] + c["h"], c["e"],
                         len({vals[a] for _, a in labels}), wst(g, vals, k)))
    print("block %d: %d circuits; sizes %s" % (k, len(rows), dict(Counter(r[2] for r in rows))))
    for name, i in [("|L|", 3), ("|P|", 4), ("exits", 5), ("near1", 6), ("e", 7), ("distinct labels", 8), ("waste", 9)]:
        print("  %-16s min %d max %d  dist %s" % (name, min(r[i] for r in rows), max(r[i] for r in rows),
                                                 sorted(Counter(r[i] for r in rows).items())))
    fr = Counter((r[3], r[4]) for r in rows)
    print("  (|L|,|P|) pairs:", sorted(fr.items()))
    fr2 = Counter((r[6], r[4] + r[7]) for r in rows)
    print("  (near1, far1) pairs:", sorted(fr2.items()))
    best = min(rows, key=lambda r: r[3]); print("  min |L| at", best[:2], best[3:])
    best = min(rows, key=lambda r: r[4]); print("  min |P| at", best[:2], best[3:])


if __name__ == "__main__":
    main()
