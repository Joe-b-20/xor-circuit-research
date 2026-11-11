"""Verify a circuit for Q_m / Q_T and print it in the sheet language.

usage: python3 show.py m FILE [--T j:k,...] [--quiet] [--save OUT.txt]
  FILE is either this directory's text format (see qm.read_circuit) or a record .json of search/xorflux
  (key "gates": list of operand pairs).  Prints VERIFIED / FAILED, the parity profile
  (x, y, h, number of blocks c of the final partition, p, rho; G = 2n + x + 2h + p - rho is checked)
  and one line per gate.  Block components: s0..s3 adjacent pairs, d0 d1 opposite pairs, t all four,
  e_c one input, E_c three inputs.
"""
import json
import sys

import qm

NAMES = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
         0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
         0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}


def describe(v, m):
    parts = []
    for j in range(m):
        b = (v >> (4 * j)) & 15
        if b:
            parts.append(f"{j}:{NAMES[b]}")
    return " ".join(parts)


def load(path):
    if path.endswith(".json"):
        d = json.load(open(path))
        gates = [tuple(g) for g in d["gates"]]
        n = min(min(a, b) for a, b in gates if True) * 0  # placeholder, n inferred by caller
        return None, gates
    return qm.read_circuit(path)


def main():
    args = sys.argv[1:]
    m = int(args[0])
    T = qm.shift_T(m)
    if "--T" in args:
        for item in args[args.index("--T") + 1].split(","):
            j, k = map(int, item.split(":"))
            T[j] ^= 1 << k
    targets = qm.rows_T(T)
    n = 4 * m
    n2, gates = load(args[1])
    assert n2 is None or n2 == n
    ok = qm.computes(n, gates, targets)
    print("VERIFIED" if ok else "FAILED", f": {len(gates)} gates, n = {n}")
    if not ok:
        sys.exit(1)
    pr = qm.profile(n, gates, targets)
    blocks = pr.pop("blocks")
    print("profile:", pr, " ledger 2n + x + 2h + p - rho =", 2 * n + pr["x"] + 2 * pr["h"] + pr["p"] - pr["rho"])
    print("final partition:", " | ".join(",".join(f"({i % 4},{i // 4})" for i in b) for b in blocks))
    if "--save" in args:
        qm.write_circuit(args[args.index("--save") + 1], n, gates,
                         f"circuit for Q_T, m = {m}, T = shift" + (f" + {args[args.index('--T') + 1]}" if "--T" in args else "")
                         + f"; {len(gates)} gates; verified by show.py")
    if "--quiet" in args:
        return
    vals = qm.masks(n, gates)
    tidx = {t: i for i, t in enumerate(targets)}
    fan = [0] * len(vals)
    for a, b in gates:
        fan[a] += 1
        fan[b] += 1

    def name(sidx):
        if sidx < n:
            return f"in({sidx % 4},{sidx // 4})"
        v = vals[sidx]
        if v in tidx:
            return f"OUT({tidx[v] % 4},{tidx[v] // 4})"
        return f"g{sidx - n}"

    for gi, (a, b) in enumerate(gates):
        g = n + gi
        pa, pb = qm.popcount(vals[a]) & 1, qm.popcount(vals[b]) & 1
        if pa and pb:
            kind = "PRODUCER"
        elif not pa and not pb:
            kind = "SUM"
        else:
            kind = "OUTPUT" if vals[g] in tidx else "HELPER"
        print(f"{name(g):>10} = {name(a):>10} + {name(b):<10} {kind:<8} fan-out {fan[g]}  [{describe(vals[g], m)}]")


if __name__ == "__main__":
    main()
