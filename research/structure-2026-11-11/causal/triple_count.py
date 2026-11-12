"""How many collinear triples does the value set of a recorded circuit have?  (inspection of existing circuits)

usage: python3 triple_count.py FILE [...]      FILE = rotation text circuit (.txt, "n k" header) or NCFF (.circ.txt)

For a circuit set S with G non-input elements, a wiring is the same thing as an executable basis of G triples
(report Lemma 1.1).  If S has exactly G collinear triples, the basis is unique and so is the wiring: the value
set determines the circuit, its ancestor relation, its charges and whether it is block-monotone.
Prints G, the number of triples of S, and (when there are extra triples) how many elements lie in an extra one.
"""
import os
import pathlib
import re
import sys
from itertools import combinations

GATE = re.compile(r"^(XOR)\s+(\S+)\s+(\S+)\s+(\S+)")
RANGE = re.compile(r"^(Inputs|Outputs):\s*([a-z]+)(\d+):[a-z]+(\d+)")


def load(path):
    text = pathlib.Path(path).read_text()
    if path.endswith(".circ.txt"):
        names, gates, n = {}, [], 0
        for line in text.splitlines():
            line = line.split("%")[0].split("#")[0].strip()
            mm = RANGE.match(line)
            if mm and mm.group(1) == "Inputs":
                base = int(mm.group(3))
                n = int(mm.group(4)) - base + 1
                for j in range(n):
                    names[f"x{j + base}"] = j
                continue
            mm = GATE.match(line)
            if mm:
                _, out, a, b = mm.groups()
                names[out] = n + len(gates)
                gates.append((names[a], names[b]))
        return n, gates
    lines = [l.split("#")[0].strip() for l in text.splitlines()]
    lines = [l for l in lines if l]
    n, k = map(int, lines[0].split())
    return n, [tuple(map(int, l.split()[:2])) for l in lines[1:1 + k]]


def main():
    for path in sys.argv[1:]:
        n, gates = load(path)
        vals = [1 << i for i in range(n)]
        for a, b in gates:
            vals.append(vals[a] ^ vals[b])
        G = len(gates)
        if len(set(vals)) != len(vals) or 0 in vals:
            print(f"{os.path.basename(path)}: G = {G}; values not distinct, skipped")
            continue
        idx = {v: i for i, v in enumerate(vals)}
        gate_tr = {tuple(sorted((n + gi, a, b))) for gi, (a, b) in enumerate(gates)}
        extra = []
        cnt = 0
        for i, j in combinations(range(n + G), 2):
            k = idx.get(vals[i] ^ vals[j])
            if k is not None and k > j:
                cnt += 1
                if (i, j, k) not in gate_tr:
                    extra.append((i, j, k))
        touched = {i for t in extra for i in t}
        print(f"{os.path.basename(path)}: G = {G}; collinear triples of the value set = {cnt}; "
              f"extra (non-gate) triples = {len(extra)}" + (f", touching {len(touched)} elements" if extra else
                                                         "  -> unique basis, unique wiring"))


if __name__ == "__main__":
    main()
