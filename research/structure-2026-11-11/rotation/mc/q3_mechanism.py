"""Where block cancellation happens in a circuit for Q_m, and which gates serve two sheets.

usage: python3 q3_mechanism.py m FILE        (default: 3 ../circuits/q3_28.txt)

Prints for every gate: operands, mask in the sheet language, block support, the sheets whose outputs it is an
ancestor of ("serves"), its charge mu, and whether it is violating (nonzero on a block where an output it
serves vanishes).  Then lists the block-cancelling gates g = a + b (some block of a or b is absent from g)
with their type:
   exit      a and b have the same support and g lives on a proper subset of it
   triangle  supports {i,j} + {j,k} -> {i,k} with the three blocks pairwise adjacent on the cycle (only m = 3)
   other     anything else
and per-sheet charges.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import qm  # noqa: E402

NAMES = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
         0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
         0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}


def main():
    m = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "circuits", "q3_28.txt")
    n, gates = qm.read_circuit(path)
    targets = qm.rows(m)
    vals = qm.masks(n, gates)
    assert qm.computes(n, gates, targets)
    G = len(gates)
    sup = [frozenset(j for j in range(m) if (v >> (4 * j)) & 15) for v in vals]
    first = {}
    for i in range(n, n + G):
        first.setdefault(vals[i], i)
    tix = {t: i for i, t in enumerate(targets)}
    anc = [set() for _ in range(m)]
    viol = set()
    for oi, t in enumerate(targets):
        o = first[t]
        seen, stack = set(), [o]
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        anc[oi // 4] |= seen
        for g in seen:
            if not sup[g] <= sup[o]:
                viol.add(g)

    def name(s):
        if s < n:
            return f"in({s % 4},{s // 4})"
        if vals[s] in tix and first[vals[s]] == s:
            i = tix[vals[s]]
            return f"OUT({i % 4},{i // 4})"
        return f"g{s - n}"

    def desc(v):
        return " ".join(f"{j}:{NAMES[(v >> (4 * j)) & 15]}" for j in range(m) if (v >> (4 * j)) & 15)

    par = lambda v: bin(v).count("1") & 1
    print(f"{os.path.basename(path)}: m = {m}, {G} gates")
    for gi, (a, b) in enumerate(gates):
        g = n + gi
        serves = [j for j in range(m) if g in anc[j]]
        mu = sum(1 for j in serves if j in sup[g])
        kind = "PROD" if par(vals[a]) and par(vals[b]) else ("SUM " if not par(vals[a]) and not par(vals[b]) else
                                                             ("OUT " if vals[g] in tix else "HELP"))
        flag = "VIOLATING" if g in viol else ""
        print(f"  {name(g):>9} = {name(a):>9} + {name(b):<9} {kind} [{desc(vals[g]):<14}] blocks {sorted(sup[g])} "
              f"serves sheets {serves} mu={mu} {flag}")
    print("charges per sheet:", [sum(1 for g in anc[j] if j in sup[g]) for j in range(m)],
          " violating gates:", len(viol))
    print("block-cancelling gates:")
    types = {}
    for gi, (a, b) in enumerate(gates):
        g = n + gi
        lost = (sup[a] | sup[b]) - sup[g]
        if not lost:
            continue
        if sup[a] == sup[b]:
            typ = "exit"
        elif len(sup[a]) == 2 and len(sup[b]) == 2 and len(sup[a] & sup[b]) == 1 and sup[g] == (sup[a] ^ sup[b]):
            typ = "triangle" if m == 3 else "chain (support on two non-adjacent blocks)"
        else:
            typ = "other"
        types[typ] = types.get(typ, 0) + 1
        print(f"  {name(g):>9}: {sorted(sup[a])} + {sorted(sup[b])} -> {sorted(sup[g])}   cancelled {sorted(lost)}   {typ}"
              f"   [{desc(vals[a])}] + [{desc(vals[b])}] = [{desc(vals[g])}]")
    print("types:", types)


if __name__ == "__main__":
    main()
