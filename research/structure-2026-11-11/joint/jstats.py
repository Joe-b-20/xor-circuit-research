"""CHECK (phase 7, main agent): joint behaviour of the eight single-block restrictions of given circuits.

Not a search. For each given circuit (recorded, kste corpus line, or a review-compat JSON gate list):
- D_b = gates removed when block b is zeroed (value 0, an input, or equal to the image of an earlier signal);
  checks the value-set formula D_b = |Sigma| - |pi_b(Sigma)| - 4 (Sigma = {0} + inputs + gate values);
- Z(g) = blocks at which gate g is removed (first-producer convention), distribution of |Z(g)|;
- sum_b D_b against G;
- two-block overlap O(b,b') = D_b + D_b' - D_{b,b'} and its fibre formula sum_F (n - r - s + 1);
- charged sets F_j (ancestors of sheet j rows nonzero on block j) and how many of them are removed at j.
usage: python3 jstats.py SPEC [SPEC ...]   SPEC = r88 | r89 | r97 | FILE:LINE | path/to/x.json
"""
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "compose", "compat"))
from clib import ROWS, ancestors, bm, check, load, values  # noqa: E402


def get(spec):
    if spec.endswith(".json"):
        g = json.load(open(spec))
        if isinstance(g, dict):
            g = g.get("gates", g)
        return [tuple(x) for x in g]
    return load(spec)


def zero_mask(blocks):
    m = 0
    for b in blocks:
        m |= bm(b)
    return ((1 << 32) - 1) ^ m


def removal(vals, keep):
    """Return set of gate indices removed under v -> v & keep (first-producer convention)."""
    seen = {0}
    for i in range(32):
        seen.add((1 << i) & keep)
    rem = set()
    for x in range(32, len(vals)):
        p = vals[x] & keep
        if p in seen:
            rem.add(x)
        seen.add(p)
    return rem


def D(vals, blocks):
    return len(removal(vals, zero_mask(blocks)))


def fibre_overlap(vals, b, c):
    keep = zero_mask([b, c])
    fib = defaultdict(set)
    sig = [0] + vals
    for v in set(sig):
        fib[v & keep].add(v)
    tot = 0
    for F in fib.values():
        n = len(F)
        r = len({v & bm(b) for v in F})
        s = len({v & bm(c) for v in F})
        tot += n - r - s + 1
    return tot


def main(specs):
    for spec in specs:
        g = get(spec)
        ok, red = check(g)
        vals = values(g)
        G = len(g)
        Sig = set([0] + vals)
        Db, Z = {}, defaultdict(set)
        for b in range(8):
            rem = removal(vals, zero_mask([b]))
            Db[b] = len(rem)
            for x in rem:
                Z[x].add(b)
            img = {v & zero_mask([b]) for v in Sig}
            assert Db[b] == len(Sig) - len(img) - 4, (spec, b)
        zdist = Counter(len(Z[x]) for x in range(32, len(vals)))
        print("== %s G=%d valid=%s reduced=%s" % (spec, G, ok, red))
        print("  D_b:", [Db[b] for b in range(8)], "sum", sum(Db.values()), " |Z(g)| distribution:", dict(sorted(zdist.items())))
        ov = []
        for b in range(8):
            c = (b + 1) % 8
            o = Db[b] + Db[c] - D(vals, [b, c])
            assert o == fibre_overlap(vals, b, c)
            ov.append(o)
        ov7 = [Db[b] + Db[7] - D(vals, [b, 7]) for b in range(7)]
        print("  overlap O(b,b+1) b=0..7:", ov, " O(b,7) b=0..6:", ov7)
        # charged sets
        idx = {v: i for i, v in enumerate(vals)}
        line = []
        for j in range(8):
            roots = [idx[ROWS[(i, j)]] for i in range(4)]
            anc = ancestors(g, roots)
            Fj = {x for x in anc if vals[x] & bm(j)}
            wasted = sum(1 for x in Fj if j in Z[x])
            line.append("%d:%d/%d" % (j, wasted, len(Fj)))
        print("  charged F_j removed at j / |F_j|:", " ".join(line))


if __name__ == "__main__":
    main(sys.argv[1:])
