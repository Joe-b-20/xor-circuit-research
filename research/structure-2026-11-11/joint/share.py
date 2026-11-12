"""CHECK (phase 7, main agent): sharing census -- which multi-block gates are ancestors of rows of two or more
sheets, by (block support, sheet set), and whether the support lies in the intersection of those sheets'
windows (window(j) = block support of sheet j's rows: {j, j-1} plus 7 for j in {1, 3, 4}).
Block-monotone circuits (no gate cancels a whole block) admit only supports inside the window intersection
(READERS.md, Theorem 3); the census shows what the other circuits use. Read-only, no search.
usage: python3 share.py --scan STRIDE   |   python3 share.py SPEC [SPEC ...]
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jstats import get  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "compose", "compat"))
from clib import KSTE, ROWS, ancestors, blocks, check, desc, values  # noqa: E402

WIN = {j: blocks(ROWS[(0, j)]) for j in range(8)}


def census(g):
    vals = values(g)
    idx = {v: i for i, v in enumerate(vals)}
    anc = {j: ancestors(g, [idx[ROWS[(i, j)]] for i in range(4)]) for j in range(8)}
    mono = all(blocks(vals[32 + gi]) == blocks(vals[a]) | blocks(vals[b]) for gi, (a, b) in enumerate(g))
    out = Counter()
    ex = {}
    for x in range(32, len(vals)):
        B = blocks(vals[x])
        if len(B) < 2:
            continue
        S = tuple(j for j in range(8) if x in anc[j])
        if len(S) < 2:
            continue
        inter = set.intersection(*[set(WIN[j]) for j in S])
        key = (tuple(sorted(B)), S, B <= inter)
        out[key] += 1
        ex.setdefault(key, x)
    return mono, out, ex, vals


def main():
    if sys.argv[1] == "--scan":
        stride = int(sys.argv[2])
        specs = ["r88", "r89", "r97"]
        for fn in sorted(os.listdir(KSTE)):
            if fn.startswith("circuits_"):
                m = sum(1 for l in open(os.path.join(KSTE, fn)) if l.strip())
                specs += ["%s:%d" % (fn, i) for i in range(1, m + 1, stride)]
        tot = {True: Counter(), False: Counter()}
        ncirc = Counter()
        outside_per = Counter()
        for s in specs:
            g = get(s)
            ok, red = check(g)
            if not (ok and red):
                continue
            mono, out, ex, vals = census(g)
            ncirc[mono] += 1
            for k in out:
                tot[mono][k] += 1
            outside_per[(mono, sum(v for k, v in out.items() if not k[2]))] += 1
        for mono in (True, False):
            print("block-monotone=%s: %d circuits; (support, sheets, inside window intersection): #circuits containing" % (mono, ncirc[mono]))
            for k, v in sorted(tot[mono].items(), key=lambda kv: (not kv[0][2], -kv[1])):
                print("    ", k, v)
        print("  gates shared outside the window intersection, per circuit (mono, count): n", dict(sorted(outside_per.items())))
        return
    for s in sys.argv[1:]:
        g = get(s)
        mono, out, ex, vals = census(g)
        print("== %s block-monotone=%s" % (s, mono))
        for k, v in sorted(out.items(), key=lambda kv: (not kv[0][2], kv[0])):
            print("   support %s sheets %s inside=%s: %d (e.g. g%d %s)" % (k[0], k[1], k[2], v, ex[k], desc(vals[ex[k]])))


if __name__ == "__main__":
    main()
