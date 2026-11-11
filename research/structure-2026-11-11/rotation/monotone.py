"""Block-monotonicity and the charge count of Theorem 3.5 for circuits of Q_m.

usage: python3 monotone.py m FILE [m FILE ...]

A circuit is block-monotone if, whenever a gate g is an ancestor of (or equal to) an output o, every
block on which the mask of g is nonzero is a block on which o is nonzero.  For every circuit the script
prints: whether it is block-monotone; the number of violating (gate, output) pairs and violating gates;
the charges mu(g) = #{ j : g is nonzero on block j and g is an ancestor-or-equal of an output of sheet j };
sum of mu (Theorem 3.5: at least 10m for m >= 3), the excess = sum of (mu - 1)+ and G + excess.
"""
import sys

import qm


def analyse(m, path):
    n, gates = qm.read_circuit(path)
    targets = qm.rows(m)
    vals = qm.masks(n, gates)
    assert qm.computes(n, gates, targets), path
    G = len(gates)
    sup = [frozenset(j for j in range(m) if (v >> (4 * j)) & 15) for v in vals]
    first = {}
    for i in range(n, n + G):
        first.setdefault(vals[i], i)
    out_sig = [first[t] for t in targets]
    # ancestors-or-equal of every output (as bit sets over gate indices)
    anc_sheet = [0] * m           # union over the outputs of sheet j
    viol_pairs = 0
    viol_gates = set()
    for oi, o in enumerate(out_sig):
        seen = set()
        stack = [o]
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            a, b = gates[s - n]
            stack.append(a)
            stack.append(b)
        j = oi // 4
        for s in seen:
            anc_sheet[j] |= 1 << (s - n)
            if not sup[s] <= sup[o]:
                viol_pairs += 1
                viol_gates.add(s)
    mu = []
    for gi in range(G):
        mu.append(sum(1 for j in range(m) if (anc_sheet[j] >> gi) & 1 and j in sup[n + gi]))
    excess = sum(max(0, x - 1) for x in mu)
    print(f"{path}: m = {m}, G = {G}, block-monotone: {not viol_gates}, violating gates {len(viol_gates)} "
          f"(pairs {viol_pairs}), sum mu = {sum(mu)} (>= {10 * m}), excess = {excess}, G + excess = {G + excess}, "
          f"gates with mu = 0: {mu.count(0)}")


def main():
    args = sys.argv[1:]
    for i in range(0, len(args), 2):
        analyse(int(args[i]), args[i + 1])


if __name__ == "__main__":
    main()
