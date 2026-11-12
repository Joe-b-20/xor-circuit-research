"""CHECK (reviewer; finite, one fixed requirement set): fewest gates of a circuit on W0..W3, X containing
E_c(W) (c = 0..3) and W_c + X (c = 0..3), i.e. P3 with the four UNIT (odd) types that dependent clean
labels allow. Exhaustive over value sets with at most OMAX other gates."""
from itertools import combinations
E = {0b1110, 0b1101, 0b1011, 0b0111}
Z = {16 | (1 << c) for c in range(4)}
REQ = E | Z
for OMAX in range(0, 3):
    start = frozenset([1, 2, 4, 8, 16]); seen = {start}; stack = [(start, 0)]; found = None
    while stack and not found:
        s, o = stack.pop()
        if REQ <= s:
            found = sorted(s - start); break
        for a, b in combinations(list(s), 2):
            v = a ^ b
            if v in s: continue
            o2 = o + (v not in REQ)
            if o2 > OMAX: continue
            t = s | {v}
            if t not in seen: seen.add(t); stack.append((t, o2))
    print("others <= %d: %s" % (OMAX, ("found, gates %d: %s" % (len(found), [format(v, "05b") for v in found])) if found else "impossible"))
