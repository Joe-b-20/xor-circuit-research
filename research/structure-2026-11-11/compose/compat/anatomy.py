"""CHECK: label anatomy at primal block k and the row-coincidence count rho.

usage: python3 anatomy.py BLOCK SPEC [SPEC...]
S_near = far parts s(r) of the rows nonzero on block k. For the distinct labels: how many are far units,
equal to some s(r) ('row-part labels'), and the block supports of the others.
rho = number of near rows r whose far part s(r) is a far unit or the value of a P-gate (such a row gate
shares its pi_far value with a far signal, so it is wasted under pi_far).
Fibres: for each omega of a near row, number of L_k signals with that omega, rows, entries, h-gates.
"""
import sys
from collections import Counter

from clib import ROWS, blocks, bm, cut, load


def anat(spec, k):
    g = load(spec)
    vals, kind, labels = cut(g, k)
    low = bm(k)
    near = [r for r in ROWS.values() if r & low]
    S = {r & ~low for r in near}
    units = {1 << i for i in range(32) if not (1 << i) & low}
    Pv = {vals[x] for x in kind if kind[x] in "ox"}
    lam = {vals[a] for _, a in labels}
    sup = Counter("".join(map(str, sorted(blocks(v)))) for v in lam - units - S)
    rho = sum(1 for r in near if (r & ~low) in units | Pv)
    print("%s k=%d: labels %d = units %d + row-parts %d + other %d %s | rho %d of %d rows, |S_near| %d" % (
        spec, k, len(lam), len(lam & units), len(lam & S - units), len(lam - units - S), dict(sup), rho,
        len(near), len(S)))
    fib = Counter()
    for x in kind:
        if kind[x] in "fhe":
            fib[(vals[x] & low, kind[x])] += 1
    om = sorted({r & low for r in near})
    parts = []
    for w in om:
        nr = sum(1 for r in near if r & low == w)
        parts.append("%d:%d/%d(e%d,h%d)" % (bin(w).count("1"), nr, fib[(w, "f")] + fib[(w, "e")] + fib[(w, "h")],
                                            fib[(w, "e")], fib[(w, "h")]))
    other = sum(v for (w, t), v in fib.items() if w not in om)
    print("   fibres rows/signals: %s | helper-omega signals %d" % (" ".join(parts), other))


if __name__ == "__main__":
    k = int(sys.argv[1])
    for s in sys.argv[2:]:
        anat(s, k)
