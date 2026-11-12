"""CHECK (phase 8, main agent): what the triangle sheets cost inside existing circuits, by restriction.

For each given MixColumns circuit (recorded or kste corpus line; read-only), zero the blocks of Z (default
4, 5, 6) and keep the ancestors of the rows of the sheets in S (default 1, 2, 3). Count the gates that, after
the restriction, give a NEW value that is not supported on the free blocks Fr (default {0}) alone: this is the
size of the restricted circuit for those sheets when the free blocks' parts are given for nothing (the
convention of the pair theorem, RECORD 15). Also the charged families after restriction and their union.
These are measurements of given circuits (each restricted circuit is a valid circuit for the restricted rows);
they are upper bounds on the restricted problem, not its value. No search.
usage: python3 tri3.py STRIDE [Z] [S] [Fr]   e.g.  python3 tri3.py 25 456 123 0
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "joint"))
from jstats import get  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "compose", "compat"))
from clib import KSTE, ROWS, bm, check, values  # noqa: E402


def measure(g, Z, S, Fr):
    vals = values(g)
    keep = ((1 << 32) - 1) ^ sum(bm(b) for b in Z)
    free = sum(bm(b) for b in Fr)
    rep = {}
    for i in range(32):
        rep.setdefault(vals[i] & keep, i)
    rep.setdefault(0, -1)
    first = {}
    for gi, (a, c) in enumerate(g):
        x = 32 + gi
        p = vals[x] & keep
        if p not in rep:
            rep[p] = x
            first[x] = (a, c)
    cls = lambda s: rep[vals[s] & keep] if s >= 0 else -1
    roots = {j: [cls(rep[ROWS[(i, j)] & keep]) for i in range(4)] for j in S}
    anc = {}
    for j in S:
        A, st = set(), [r for r in roots[j] if r >= 32]
        while st:
            s = st.pop()
            if s in A:
                continue
            A.add(s)
            for o in first[s]:
                co = cls(o)
                if co >= 32:
                    st.append(co)
        anc[j] = A
    allA = set().union(*anc.values())
    counted = {x for x in allA if (vals[x] & keep) & ~free}
    F = {j: {x for x in anc[j] if vals[x] & keep & bm(j)} for j in S}
    union = set().union(*F.values())
    return len(counted), [len(F[j]) for j in S], len(union)


def main():
    stride = int(sys.argv[1])
    Z = [int(c) for c in (sys.argv[2] if len(sys.argv) > 2 else "456")]
    S = [int(c) for c in (sys.argv[3] if len(sys.argv) > 3 else "123")]
    Fr = [int(c) for c in (sys.argv[4] if len(sys.argv) > 4 else "0")] if (len(sys.argv) <= 4 or sys.argv[4] != "-") else []
    specs = ["r88", "r89", "r97"]
    for fn in sorted(os.listdir(KSTE)):
        if fn.startswith("circuits_"):
            m = sum(1 for l in open(os.path.join(KSTE, fn)) if l.strip())
            specs += ["%s:%d" % (fn, i) for i in range(1, m + 1, stride)]
    cnt, best = Counter(), None
    for s in specs:
        g = get(s)
        if not all(check(g)):
            continue
        c, Fs, u = measure(g, Z, S, Fr)
        cnt[(c, u)] += 1
        if best is None or c < best[0]:
            best = (c, s, Fs, u)
    print("zero %s, sheets %s, free %s: (restricted count, charged union): circuits" % (Z, S, Fr))
    for k, v in sorted(cnt.items()):
        print("   ", k, v)
    print("  least restricted count:", best)


if __name__ == "__main__":
    main()
