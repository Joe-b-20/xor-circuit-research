"""CHECK: canonical split |T| = |L_k| + |P| at primal block k, labels and their classes.

usage: python3 cutstats.py BLOCK SPEC [SPEC...]   (SPEC: r88 r89 r97 or circuits_3.txt:13114)
Label classes (distinct values): U far input unit, R far required row, A P-gate ancestor of a far row
(other than R), X P-gate not an ancestor of any far row ("label-only"), E exit value.
"""
import sys
from collections import Counter

from clib import ROWS, W, ancestors, bm, check, cut, far_rows, load, rank


def stats(spec, k):
    g = load(spec)
    ok, red = check(g)
    vals, kind, labels = cut(g, k)
    c = Counter(kind.values())
    frs = set(far_rows(k))
    frg = [x for x in kind if vals[x] in frs]
    anc = ancestors(g, frg)
    P = [x for x in kind if kind[x] in "ox"]
    labelonly = [x for x in P if x not in anc]
    lv = sorted({vals[a] for _, a in labels})
    first = {}
    for _, a in labels:
        first.setdefault(vals[a], a)
    cls = Counter()
    for v in lv:
        a = first[v]
        if a < 32:
            cls["U"] += 1
        elif v in frs:
            cls["R"] += 1
        elif kind[a] == "x":
            cls["E"] += 1
        elif a in anc:
            cls["A"] += 1
        else:
            cls["X"] += 1
    w = W(k)
    rl, rw, rlw = rank(lv), rank(w), rank(lv + w)
    print("%s k=%d ok=%s red=%s n=%d | f %d h %d e %d |L| %d | ord %d exit %d |P| %d | labels distinct %d "
          "rank %d dimW %d dim(L&W) %d | classes %s | label-only P gates %d" % (
              spec, k, ok, red, len(g), c["f"], c["h"], c["e"], c["f"] + c["h"] + c["e"], c["o"], c["x"],
              c["o"] + c["x"], len(lv), rl, rw, rl + rw - rlw, dict(cls), len(labelonly)))
    return g, vals, kind, labels


if __name__ == "__main__":
    k = int(sys.argv[1])
    for s in sys.argv[2:]:
        stats(s, k)
