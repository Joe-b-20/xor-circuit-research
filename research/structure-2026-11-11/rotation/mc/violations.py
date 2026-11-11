"""What the non-block-monotone 88-gate MixColumns circuits of the kste corpus do.

usage: python3 violations.py [--limit N] [--example K]

For every valid 88-gate line (wiring as published) that is not block-monotone:
  - the block-cancelling gates g = a + b (a block of a or b absent from g), as support patterns "A+B->G";
  - the violating gates (nonzero on a block where an output they serve vanishes): support pattern and the
    sheets served; their charge mu.
Prints histograms and, for the first K non-monotone circuits (default 1), the violating part in the sheet
language (block j: s_c, d_c, t, e_c, E_c).  Read-only on the corpus.
"""
import os
import sys
from collections import Counter

import mc

KSTE = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
NAMES = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
         0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
         0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}


def nib(v, j):
    return sum(((v >> (8 * c + j)) & 1) << c for c in range(4))


def desc(v):
    return " ".join(f"{j}:{NAMES[nib(v, j)]}" for j in range(8) if nib(v, j))


def pat(s):
    return "".join(map(str, sorted(s)))


def study(gates):
    n = 32
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    first = {}
    for i in range(n, len(vals)):
        first.setdefault(vals[i], i)
    sup = [mc.blocks(v) for v in vals]
    anc = [set() for _ in range(8)]
    viol = set()
    for oi, t in enumerate(mc.TARGETS):
        o = first[t]
        seen, stack = set(), [o]
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        anc[oi % 8] |= seen
        for g in seen:
            if not sup[g] <= sup[o]:
                viol.add(g)
    cancel = []
    for gi, (a, b) in enumerate(gates):
        g = n + gi
        if (sup[a] | sup[b]) - sup[g]:
            cancel.append((g, a, b))
    return vals, sup, anc, viol, cancel


def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    nex = int(sys.argv[sys.argv.index("--example") + 1]) if "--example" in sys.argv else 1
    canc_types = Counter()
    canc_per_circuit = Counter()
    viol_types = Counter()
    canc_sets = Counter()
    nline = nnon = 0
    examples = []
    for fn in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"):
        for line in open(os.path.join(KSTE, fn)):
            if not line.strip():
                continue
            nline += 1
            if limit and nline > limit:
                break
            gates = mc.parse_pairs(line)
            if len(gates) != 88:
                continue
            r = mc.analyse(gates)
            if r is None or r["distinct"] != 88 or r["dead"] or r["monotone"]:
                continue
            nnon += 1
            vals, sup, anc, viol, cancel = study(gates)
            canc_per_circuit[len(cancel)] += 1
            key = []
            for g, a, b in cancel:
                p = "+".join(sorted([pat(sup[a]), pat(sup[b])])) + "->" + pat(sup[g])
                canc_types[p] += 1
                key.append(p)
            canc_sets[" ; ".join(sorted(key))] += 1
            for g in viol:
                serves = "".join(str(j) for j in range(8) if g in anc[j])
                viol_types[(pat(sup[g]), serves)] += 1
            if len(examples) < nex:
                examples.append((fn, nline, gates, vals, sup, anc, viol, cancel, r))
    print(f"non-monotone circuits studied: {nnon}")
    print("block-cancelling gates per circuit:", dict(sorted(canc_per_circuit.items())))
    print("block-cancelling gates by support pattern (operand supports -> result support), top 25:")
    for p, k in canc_types.most_common(25):
        print(f"   {p:<22} {k}")
    print("sets of cancellation patterns per circuit, top 12:")
    for p, k in canc_sets.most_common(12):
        print(f"   {k:>6}  {p}")
    print("violating gates by (support, sheets served), top 25:")
    for (p, s), k in viol_types.most_common(25):
        print(f"   support {p:<5} serves sheets {s:<6} {k}")
    for fn, nl, gates, vals, sup, anc, viol, cancel, r in examples:
        print(f"example: {fn} line {nl}: charges {r['charges']}, sum mu {r['sum_mu']}, excess {r['excess']}, "
              f"uncharged {r['uncharged']}, G01 {r['G01']}, G34 {r['G34']}")
        for g in sorted(viol):
            a, b = gates[g - 32]
            serves = [j for j in range(8) if g in anc[j]]
            print(f"   violating gate {g}: [{desc(vals[a])}] + [{desc(vals[b])}] = [{desc(vals[g])}]  serves sheets {serves}")
        for g, a, b in cancel:
            print(f"   cancelling gate {g}: [{desc(vals[a])}] + [{desc(vals[b])}] = [{desc(vals[g])}]")


if __name__ == "__main__":
    main()
