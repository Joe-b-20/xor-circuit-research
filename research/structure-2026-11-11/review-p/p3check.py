"""CHECK (reviewer; finite, exhaustive over value sets of one small fixed problem; not a proof of anything
beyond this lemma): refute/REPORT.md P3 (mirror lemma).

Inputs W0..W3 = bits 0..3, X = bit 4. Required: E_c(W) (weight-3 vectors on W). ZX = {Z + X : Z even,
nonzero on W} (7 vectors). A circuit is determined (for these questions) by its set of computed values,
built one XOR at a time from two earlier values; zero and repeated values are never useful and are skipped.
'other' = a gate value outside E u ZX. We enumerate every reachable value set with at most OMAX others and
record, over sets containing all four E_c, the best m = |set n ZX| and whether the Z's span Even(F_2^4).
P3 claims: with <= 2 others, never (m >= 4) and never (m = 3 with the Z's spanning).
"""
import sys
from itertools import combinations

OMAX = int(sys.argv[1]) if len(sys.argv) > 1 else 2
INP = [1, 2, 4, 8, 16]
E = {0b1110, 0b1101, 0b1011, 0b0111}
EVEN = [z for z in range(1, 16) if bin(z).count("1") % 2 == 0]
ZX = {z | 16 for z in EVEN}


def rank(vs):
    rows, r = list(vs), 0
    basis = []
    for v in rows:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def main():
    start = frozenset(INP)
    seen = {start}
    stack = [(start, 0)]
    best = {}   # (m, spanning) -> min others
    while stack:
        s, oth = stack.pop()
        if E <= s:
            zs = [v ^ 16 for v in s & ZX]
            key = (len(zs), rank(zs) == 3)
            if oth < best.get(key, 99):
                best[key] = oth
        vals = list(s)
        for a, b in combinations(vals, 2):
            v = a ^ b
            if v in s:
                continue
            o2 = oth + (0 if (v in E or v in ZX) else 1)
            if o2 > OMAX:
                continue
            t = s | {v}
            if t not in seen:
                seen.add(t)
                stack.append((t, o2))
    print("OMAX %d: %d value sets explored" % (OMAX, len(seen)))
    for key in sorted(best):
        print("  m=%d spanning=%s: fewest others %d" % (key[0], key[1], best[key]))
    bad = [k for k in best if best[k] <= 2 and (k[0] >= 4 or (k[0] == 3 and k[1]))]
    print("P3 violated:" if bad else "P3 holds (no violating set with <= 2 others)", bad)


if __name__ == "__main__":
    main()
