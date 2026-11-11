"""Filtration levels of the signals of a recorded MixColumns circuit.

python3 levels.py FILE.circ.txt [...]

The 32 inputs are bit r of byte c (index 8c + r). Block r = the four inputs with the same r.
For a mask mu, look at its four bits on each block, (mu_0, mu_1, mu_2, mu_3):
  level 4: some block has odd weight            (mask not in W3)
  level 3: all blocks even, some block has mu_0 != mu_2   (in W3, not in W2)
  level 2: every block is 0000, 1111, 1010 or 0101, some block is 1010 or 0101 (in W2, not W1)
  level 1: every block constant, mask nonzero   (in W1)
W_k is the annihilator of (1+y)^(4-k) R, R = F_256[y]/(y^4+1); MixColumns acts on W_k/W_(k-1)
as the identity. Prints the partition of the circuit, the level histogram and the gate types.
Standard library only; examines existing circuits, searches nothing.
"""
import pathlib
import re
import sys
from collections import Counter

GATE = re.compile(r"^(XOR)\s+(\S+)\s+(\S+)\s+(\S+)")
RANGE = re.compile(r"^(Inputs|Outputs):\s*([a-z]+)(\d+):[a-z]+(\d+)")


def read(circ):
    vals, order = {}, []
    for line in pathlib.Path(circ).read_text().splitlines():
        line = line.split("%")[0].split("#")[0].strip()
        m = RANGE.match(line)
        if m and m.group(1) == "Inputs":
            base = int(m.group(3))
            for j in range(int(m.group(4)) - base + 1):
                vals[f"x{j + base}"] = 1 << j
            continue
        m = GATE.match(line)
        if m:
            _, out, a, b = m.groups()
            vals[out] = vals[a] ^ vals[b]
            order.append((out, a, b))
    return vals, order


def blocks(mu):
    return [tuple((mu >> (8 * c + r)) & 1 for c in range(4)) for r in range(8)]


def level(mu):
    bl = blocks(mu)
    if any(sum(b) & 1 for b in bl):
        return 4
    if any(b[0] != b[2] for b in bl):
        return 3
    if any(b[0] != b[1] for b in bl):
        return 2
    return 1 if mu else 0


def odd_blocks(mu):
    return [r for r, b in enumerate(blocks(mu)) if sum(b) & 1]


def rank(vs):
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def main(circ):
    vals, order = read(circ)
    outs = {k for k in vals if k.startswith("y")}
    gate_names = [o for o, _, _ in order]
    par = lambda v: bin(v).count("1") & 1
    even = [vals[g] for g in gate_names if not par(vals[g])]
    print(f"{pathlib.Path(circ).name}: G={len(order)}")
    print(f"  rank of even signals = {rank(even)}; even signals inside W3: {sum(level(v) <= 3 for v in even)} of {len(even)}")
    multi = [g for g in gate_names if par(vals[g]) and len(odd_blocks(vals[g])) != 1]
    print(f"  odd gates that are odd on more than one canonical block: {len(multi)}")
    lv = Counter()
    for g in gate_names:
        lv[(level(vals[g]), "out" if g in outs else "gate")] += 1
    print(f"  signals by level: {dict(sorted(lv.items()))}")
    ranks = {k: rank([vals[g] for g in gate_names if level(vals[g]) <= k]) for k in (1, 2, 3)}
    print(f"  rank of gate signals of level <= 1, 2, 3: {ranks[1]}, {ranks[2]}, {ranks[3]} (W1, W2, W3 have dimension 8, 16, 24)")
    types = Counter()
    for g, a, b in order:
        la, lb = sorted((level(vals[a]), level(vals[b])), reverse=True)
        types[(la, lb, level(vals[g]))] += 1
    print("  gate types (level a, level b -> level result): count")
    for t, n in sorted(types.items(), reverse=True):
        print(f"    {t[0]} + {t[1]} -> {t[2]}: {n}")


if __name__ == "__main__":
    for f in sys.argv[1:]:
        main(f)
