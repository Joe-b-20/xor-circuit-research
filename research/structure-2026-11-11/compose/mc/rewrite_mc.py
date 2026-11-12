"""CHECK (explicit constructions, verified): can a primal exit (block-cancelling gate) be re-wired at no cost?

usage: python3 rewrite_mc.py STRIDE
For each sampled kste circuit and each gate g that cancels a block (primal exit across a single-block
cut), look for two signals x, y (inputs or gates, not descendants of g) with val(x) + val(y) = val(g),
of two kinds:  Z: both zero on the cancelled block (the exit is replaced by an ordinary far gate);
               C: blocks(x) | blocks(y) inside blocks(g) (no cancellation at all at this gate).
If found, the gate is re-wired, the list re-sorted topologically, and the result verified to compute
MixColumns with the same gate count; block-monotonicity of the result is reported.
"""
import os
import sys
from collections import Counter

from corpus_mc import KSTE, mc


def descendants(gates, g):
    n = 32
    d = {g}
    for i, (a, b) in enumerate(gates):
        if a in d or b in d:
            d.add(n + i)
    return d


def rewire(gates, gi, x, y):
    """Replace gate gi's operands by (x, y) and topologically re-sort; returns new gate list."""
    n = 32
    ops = {n + i: (a, b) for i, (a, b) in enumerate(gates)}
    ops[n + gi] = (x, y)
    order, done = [], set(range(n))
    pending = list(ops)
    while pending:
        rest = []
        for g in pending:
            a, b = ops[g]
            if a in done and b in done:
                order.append(g)
                done.add(g)
            else:
                rest.append(g)
        if len(rest) == len(pending):
            return None
        pending = rest
    new = {g: n + i for i, g in enumerate(order)}
    new.update({i: i for i in range(n)})
    return [(new[ops[g][0]], new[ops[g][1]]) for g in order]


def main():
    stride = int(sys.argv[1])
    res = Counter()
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
            mono = "mono" if r["monotone"] else "nonmono"
            vals = [1 << i for i in range(32)]
            for a, b in gates:
                vals.append(vals[a] ^ vals[b])
            sup = [mc.blocks(v) for v in vals]
            for gi, (a, b) in enumerate(gates):
                g = 32 + gi
                cut = (sup[a] | sup[b]) - sup[g]
                if not cut:
                    continue
                d = descendants(gates, g)
                cand = [i for i in range(len(vals)) if i not in d]
                byval = {}
                for i in cand:
                    byval.setdefault(vals[i], i)
                v = vals[g]
                kinds = {}
                for i in cand:
                    j = byval.get(vals[i] ^ v)
                    if j is None or j == i:
                        continue
                    if not ((sup[i] | sup[j]) - sup[g]):
                        kinds.setdefault("C", (i, j))
                    if not (cut & (sup[i] | sup[j])):
                        kinds.setdefault("Z", (i, j))
                key = "%s cut%s %s->%s" % (mono, "".join(map(str, sorted(cut))),
                                            "".join(map(str, sorted(sup[a] | sup[b]))), "".join(map(str, sorted(sup[g]))))
                if not kinds:
                    res[key + " : no rewire"] += 1
                    continue
                kk = "C" if "C" in kinds else "Z"
                x, y = kinds[kk]
                ng = rewire(gates, gi, x, y)
                r2 = mc.analyse(ng) if ng else None
                ok = r2 is not None and len(ng) == len(gates)
                res[key + " : rewire %s ok=%s monotone-after=%s" % (kk, ok, r2["monotone"] if r2 else None)] += 1
    print("lines %d" % nl)
    for k, v in sorted(res.items()):
        print("  %5d %s" % (v, k))


if __name__ == "__main__":
    main()
