"""CHECK: restriction to block k = 0 (pi_far) and its waste.

usage: python3 waste.py BLOCK SPEC [SPEC...]
pi_far(v) = v with block k zeroed. A gate is WASTED if pi_far(gate) is 0, a far unit, or equal to pi_far of an
earlier signal (inputs and gates). The non-wasted gates form a circuit for MC|_{k=0} (28 inputs, outputs
pi_far of all 32 rows), so R = n - waste is an upper bound on L(MC|_{k=0}) for this circuit.
Waste is split by class at the cut (f, h, e in L_k; o, x in P) and 'unit readers' (gates reading a block-k unit).
"""
import sys
from collections import Counter

from clib import ROWS, bm, cut, load


def waste(spec, k, verbose=True):
    g = load(spec)
    vals, kind, labels = cut(g, k)
    low = bm(k)
    seen = {0} | {(1 << i) & ~low for i in range(32)}
    W = Counter()
    U = 0
    for gi, (a, b) in enumerate(g):
        x = 32 + gi
        p = vals[x] & ~low
        ur = any(o < 32 and (1 << o) & low for o in (a, b))
        U += ur
        if p in seen:
            W[kind[x]] += 1
        seen.add(p)
    tgt = {r & ~low for r in ROWS.values()}
    assert tgt <= seen
    w = sum(W.values())
    if verbose:
        print("%s k=%d n=%d waste %d %s R=n-waste %d | unit readers %d" % (spec, k, len(g), w, dict(W), len(g) - w, U))
    return len(g), w, W


if __name__ == "__main__":
    k = int(sys.argv[1])
    for s in sys.argv[2:]:
        waste(s, k)
