"""Check the counting steps of the proof of Theorem 9.1 on enumerated local circuits (enum_three_G.json)."""
import json
import sys
from collections import Counter

AM, KM, BM = 0x00F, 0x0F0, 0xF00


def rank(vs):
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


for fn in sys.argv[1:]:
    data = json.load(open(fn))
    stats, bad = Counter(), 0
    for c in data:
        vals, ops = c["vals"], c["ops"]
        G = len(vals)
        opv = []
        for i, (o1, o2) in enumerate(ops):
            def known(o):
                if o[0] == "U":
                    return 1 << (8 + int(o[1:]))
                if o[0] == "G":
                    return vals[int(o[1:])]
                return None
            x, y = known(o1), known(o2)
            if x is None and y is None:      # FA + FK
                x, y = vals[i] & AM, vals[i] & KM
            elif x is None:
                x = vals[i] ^ y
            elif y is None:
                y = vals[i] ^ x
            assert x ^ y == vals[i]
            opv.append((x, y, o1, o2))
        B = [i for i in range(G) if vals[i] & BM]
        M = [i for i in range(G) if not vals[i] & BM and vals[i] & AM and vals[i] & KM]
        Ea, Ek, Ms, noncanon = [], [], set(), 0
        for i in B:
            x, y, o1, o2 = opv[i]
            z = [(v, o) for v, o in ((x, o1), (y, o2)) if not v & BM]
            if len(z) == 2:
                raise SystemExit("B-gate with both operands zero on b")
            if len(z) == 1:
                v, o = z[0]
                if v & AM and v & KM:
                    assert o[0] == "G"
                    Ms.add(int(o[1:]))
                elif v & AM or v == 0:
                    Ea.append(v)
                else:
                    Ek.append(v)
        dA = rank([v & AM for v in Ea])
        dK = rank([v >> 4 for v in Ek])
        s = len(Ms)
        ok = (len(B) >= 10 + len(Ek) and len(B) >= 10 + len(Ea) and dA + s >= 3 and dK + s >= 3
              and len(B) + len(M) >= 10 + max(len(Ea), len(Ek)) + s >= 13)
        bad += not ok
        stats[(len(B), len(M), len(Ea), len(Ek), s)] += 1
    print(fn, "circuits", len(data), "violations of the proof's inequalities:", bad)
    print("   (B, M, |Ea|, |Ek|, s):", stats.most_common(12))
