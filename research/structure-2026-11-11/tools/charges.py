"""Charges and block-monotonicity of a recorded MixColumns circuit: python3 charges.py FILE.circ.txt [...]

Block j = the four inputs "bit j of byte c". Sheet j = the four outputs (c, j).
For a gate g:  mu(g) = number of sheets j such that the mask of g is nonzero on block j and g is an
ancestor of (or equal to) an output gate of sheet j.
Charge theorem (RECORD section 7): the sum of mu over all gates is at least 80 for every circuit.
A circuit is block-monotone if, whenever g is an ancestor-or-equal of an output o, every block on which
g is nonzero is a block on which o is nonzero; then mu <= 1 for every gate.
Written independently of rotation/monotone.py. Standard library only; examines existing circuits.
"""
import pathlib
import re
import sys

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


def blocks_of(mu):
    return frozenset(j for j in range(8) if any((mu >> (8 * c + j)) & 1 for c in range(4)))


def main(circ):
    vals, order = read(circ)
    ops = {out: (a, b) for out, a, b in order}
    outs = sorted((int(k[1:]), k) for k in vals if k.startswith("y"))
    base = outs[0][0]
    sup = {k: blocks_of(v) for k, v in vals.items()}
    anc_of_sheet = {j: set() for j in range(8)}
    violating = set()
    for idx, k in outs:
        j = (idx - base) % 8
        seen, stack = set(), [k]
        while stack:
            s = stack.pop()
            if s in seen or s not in ops:
                continue
            seen.add(s)
            stack.extend(ops[s])
        anc_of_sheet[j] |= seen
        for g in seen:
            if not sup[g] <= sup[k]:
                violating.add(g)
    mu = {g: sum(1 for j in range(8) if j in sup[g] and g in anc_of_sheet[j]) for g in ops}
    per_sheet = [sum(1 for g in ops if j in sup[g] and g in anc_of_sheet[j]) for j in range(8)]
    total = sum(mu.values())
    excess = sum(max(0, v - 1) for v in mu.values())
    zero = sum(1 for v in mu.values() if v == 0)
    print(f"{pathlib.Path(circ).name}: G={len(order)} block-monotone={not violating} violating gates={len(violating)}")
    print(f"  charges per sheet 0..7 = {per_sheet} (each must be >= 10); sum mu = {total}; "
          f"gates with mu >= 2: {sum(1 for v in mu.values() if v >= 2)} (excess {excess}); gates with mu = 0: {zero}")


if __name__ == "__main__":
    for f in sys.argv[1:]:
        main(f)
