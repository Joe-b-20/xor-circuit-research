"""Explicit construction (phase 9, main agent; rebuilt from the user's description, the user's attachment was not
available in the session): a MixColumns circuit with few distinct charged gates. Direct verification only.

Construction ("global parity, then remainders"):
  z_c = XOR of the eight inputs x_(c,j) of byte c (7 gates per byte, 28);
  H_c = XOR of the other three z (6 gates: a = z0+z1, b = z2+z3, H0 = z1+b, H1 = z0+b, H2 = a+z3, H3 = a+z2);
  for each output y_(c,j): r_(c,j) = H_c + y_(c,j) has zero block-j part; build it as a chain of input sums in
  a fixed order (inputs sorted by wire), reusing a value already present; then y_(c,j) = H_c + r_(c,j).
Also the rotation model Q_m (rows E_c on block j plus s_c on block j-1; "byte" = unit index c, so z_c = XOR of
unit c over all m blocks), for m given.
Checks: computes the map; values distinct, nonzero, not inputs; every gate is an ancestor of an output; G,
F_j (ancestors of sheet j rows nonzero on block j), distinct charged, U, E, R; no intermediate equals a target.
usage: python3 build_witness.py mc [ORDER]  |  python3 build_witness.py q M      ORDER: wire (default) | block
"""
import json
import os
import sys
from collections import Counter


def mc_rows():
    def xt(b):
        b <<= 1
        return (b ^ 0x11b) if b & 0x100 else b
    mul = lambda a, m: {1: a, 2: xt(a), 3: xt(a) ^ a}[m]
    rows = {}
    for i in range(4):
        for t in range(8):
            mask = 0
            for c in range(4):
                m = [2, 3, 1, 1][(c - i) % 4]
                for j in range(8):
                    if (mul(1 << j, m) >> t) & 1:
                        mask |= 1 << (8 * c + j)
            rows[(i, t)] = mask
    return rows   # wire 8c + j = bit j of byte c; block j = wires {8c + j}


def build(n, unit_of, block_of, rows, nblocks, order_key):
    """unit_of(w), block_of(w): byte/unit index and block of input wire w."""
    idx = {1 << w: w for w in range(n)}
    gates = []
    targets = set(rows.values())

    def add(a, b, final=False):
        v = a ^ b
        if v in idx:
            return v
        assert final or v not in targets, "an intermediate equals a target"
        gates.append((idx[a], idx[b]))
        idx[v] = n + len(gates) - 1
        return v

    def chain(ws):
        acc = 1 << ws[0]
        for w in ws[1:]:
            acc = add(acc, 1 << w)
        return acc

    units = sorted(set(unit_of(w) for w in range(n)))
    z = {c: chain(sorted([w for w in range(n) if unit_of(w) == c], key=order_key)) for c in units}
    a = add(z[0], z[1]); b = add(z[2], z[3])
    H = {0: add(z[1], b), 1: add(z[0], b), 2: add(a, z[3]), 3: add(a, z[2])}
    for (c, j), y in sorted(rows.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        r = H[c] ^ y
        ws = sorted([w for w in range(n) if r >> w & 1], key=order_key)
        assert all(block_of(w) != j for w in ws)
        rr = chain(ws)
        add(H[c], rr, final=True)
    return gates


def stats(n, gates, rows, block_mask, nblocks):
    vals = [1 << w for w in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    G = len(gates)
    gv = vals[n:]
    ok = all(r in set(gv) for r in rows.values())
    reduced = len(set(vals)) == len(vals) and 0 not in vals
    idx = {v: i for i, v in enumerate(vals)}
    def anc(roots):
        A, st = set(), list(roots)
        while st:
            s = st.pop()
            if s < n or s in A:
                continue
            A.add(s)
            st.extend(gates[s - n])
        return A
    live = anc([idx[r] for r in rows.values()])
    A = {j: anc([idx[rows[(c, j)]] for c in range(4)]) for j in range(nblocks)}
    F = {j: {x for x in A[j] if vals[x] & block_mask(j)} for j in range(nblocks)}
    mult = Counter(x for j in F for x in F[j])
    out = set(idx[r] for r in rows.values())
    glob = {x for x in mult if x not in out}
    return dict(G=G, computes=ok, reduced=reduced, live=len(live) == G, distinct_charged=len(mult),
                charged_outputs=len(set(mult) & out), charged_other=len(glob), U=G - len(mult),
                E=sum(len(F[j]) - 10 for j in F), R=sum(v - 1 for v in mult.values() if v > 1),
                F_sizes=[len(F[j]) for j in range(nblocks)])


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if sys.argv[1] == "mc":
        rows = mc_rows()
        order = sys.argv[2] if len(sys.argv) > 2 else "wire"
        key = (lambda w: w) if order == "wire" else (lambda w: (w % 8, w // 8))
        g = build(32, lambda w: w // 8, lambda w: w % 8, rows, 8, key)
        s = stats(32, g, rows, lambda j: sum(1 << (8 * c + j) for c in range(4)), 8)
        print("MixColumns, order", order, s)
        json.dump(g, open(os.path.join(here, "witness_mc_%s.json" % order), "w"))
    else:
        m = int(sys.argv[2])
        E4 = lambda c: 15 ^ (1 << c)
        S4 = lambda c: (1 << c) | (1 << ((c + 1) % 4))
        rows = {(c, j): (E4(c) << (4 * j)) | (S4(c) << (4 * ((j - 1) % m))) for j in range(m) for c in range(4)}
        g = build(4 * m, lambda w: w % 4, lambda w: w // 4, rows, m, lambda w: w)
        s = stats(4 * m, g, rows, lambda j: 15 << (4 * j), m)
        print("Q_%d" % m, s, " 8m+2 =", 8 * m + 2)


if __name__ == "__main__":
    main()
