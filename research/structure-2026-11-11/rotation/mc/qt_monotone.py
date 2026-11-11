"""Block-monotonicity, charges and block-cancelling gates for a circuit of Q_T (shift plus extra entries).

usage: python3 qt_monotone.py m FILE [j:k,...]
Sheet j = outputs (c, j); its support = block j and the blocks k with T[j][k] = 1.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import qm  # noqa: E402


def main():
    m = int(sys.argv[1])
    n, gates = qm.read_circuit(sys.argv[2])
    T = qm.shift_T(m)
    if len(sys.argv) > 3:
        for item in sys.argv[3].split(","):
            j, k = map(int, item.split(":"))
            T[j] ^= 1 << k
    targets = qm.rows_T(T)
    vals = qm.masks(n, gates)
    assert qm.computes(n, gates, targets)
    G = len(gates)
    sup = [frozenset(j for j in range(m) if (v >> (4 * j)) & 15) for v in vals]
    first = {}
    for i in range(n, n + G):
        first.setdefault(vals[i], i)
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
    charges = [sum(1 for g in anc[j] if j in sup[g]) for j in range(m)]
    mu = [sum(1 for j in range(m) if j in sup[g] and g in anc[j]) for g in range(n, n + G)]
    canc = []
    for gi, (a, b) in enumerate(gates):
        g = n + gi
        if (sup[a] | sup[b]) - sup[g]:
            canc.append(f"{sorted(sup[a])}+{sorted(sup[b])}->{sorted(sup[g])}")
    print(f"{os.path.basename(sys.argv[2])}: G = {G}, block-monotone: {not viol}, violating gates {len(viol)}, "
          f"charges {charges}, sum mu {sum(mu)}, uncharged {mu.count(0)}, excess {sum(max(0, x - 1) for x in mu)}")
    print("   block-cancelling gates:", canc)


if __name__ == "__main__":
    main()
