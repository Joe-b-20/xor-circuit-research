"""Family counts of sharing/INDEPENDENT-SHEETS.md on recorded MixColumns circuits.

python3 families.py FILE.circ.txt [...]

For a set J of sheets, D_J = gates that are an output gate of a sheet of J or an ancestor of one, and
whose mask is nonzero on the own block (block j) of some sheet j of J. Theorem 2 claims |D_J| >= 10 |J|
for J = {0,2,4,6}, J = {1,3,5} and J = {7}. Also prints the gates lying in two of the three sets and in
none. Standard library only; examines existing circuits; a test, not a proof.
"""
import pathlib
import re
import sys

GATE = re.compile(r"^(XOR)\s+(\S+)\s+(\S+)\s+(\S+)")
RANGE = re.compile(r"^(Inputs|Outputs):\s*([a-z]+)(\d+):[a-z]+(\d+)")
FAMILIES = [(0, 2, 4, 6), (1, 3, 5), (7,)]


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
    anc = {j: set() for j in range(8)}
    for idx, k in outs:
        j = (idx - base) % 8
        stack = [k]
        while stack:
            s = stack.pop()
            if s in anc[j] or s not in ops:
                continue
            anc[j].add(s)
            stack.extend(ops[s])
    sets = []
    for J in FAMILIES:
        A = set().union(*(anc[j] for j in J))
        sets.append({g for g in A if sup[g] & set(J)})
    sizes = [len(s) for s in sets]
    union = set().union(*sets)
    multi = sum(1 for g in ops if sum(g in s for s in sets) >= 2)
    print(f"{pathlib.Path(circ).name}: G={len(order)}  |D_J| for J={FAMILIES}: {sizes} (claimed >= {[10 * len(J) for J in FAMILIES]})"
          f"  gates in two or more sets: {multi}  in none: {len(ops) - len(union)}")


if __name__ == "__main__":
    for f in sys.argv[1:]:
        main(f)
