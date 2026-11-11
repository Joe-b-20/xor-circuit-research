"""Parity survey of every recorded circuit: python3 survey.py [circuits dir]

For each map folder, for its fewest-gate circuit: n inputs, m outputs, G, the number of odd-weight
outputs and inputs, x (odd+odd gates), y (even+even gates), h (odd non-output gates), the rank of the
even gate signals, whether all rows and all columns of the matrix are odd, and the minimum weight d
of a nonzero relation among the boundary signals when it is at most 6 (d = '>6' otherwise).
Standard library only; examines existing circuits, searches nothing.
"""
import itertools
import pathlib
import re
import sys

GATE = re.compile(r"^(XOR|XNOR)\s+(\S+)\s+(\S+)\s+(\S+)")
RANGE = re.compile(r"^(Inputs|Outputs):\s*([a-z]+)(\d+):[a-z]+(\d+)")
NAME = re.compile(r"-xor(\d+)-depth(\d+)\.circ\.txt$")


def read(circ):
    vals, order, n_in = {}, [], 0
    for line in pathlib.Path(circ).read_text().splitlines():
        line = line.split("%")[0].split("#")[0].strip()
        m = RANGE.match(line)
        if m and m.group(1) == "Inputs":
            base = int(m.group(3))
            n_in = int(m.group(4)) - base + 1
            for j in range(n_in):
                vals[f"x{j + base}"] = 1 << j
            continue
        m = GATE.match(line)
        if m:
            _, out, a, b = m.groups()
            vals[out] = vals[a] ^ vals[b]
            order.append((out, a, b))
    return vals, order, n_in


def rank(vs):
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def min_rel(points, limit=6):
    """Smallest size <= limit of a nonempty zero-sum subset of the (distinct) points, else None."""
    pts = sorted(set(points))
    s = set(pts)
    if 0 in s:
        return 1
    if len(pts) < len(points):
        return 2
    sums2 = {}
    for a, b in itertools.combinations(pts, 2):
        sums2.setdefault(a ^ b, []).append((a, b))
    if any(v in s for v in sums2):
        return 3
    if any(len(p) > 1 for p in sums2.values()):
        return 4
    # weight 5: pair sum equals a triple sum; weight 6: two disjoint triples
    trip = {}
    best = None
    for (v, prs) in sums2.items():
        a, b = prs[0]
        for c in pts:
            if c != a and c != b:
                t = v ^ c
                key = frozenset((a, b, c))
                if t in sums2:
                    d, e = sums2[t][0]
                    if d not in key and e not in key:
                        return 5
                trip.setdefault(t, set()).add(key)
    for t, keys in trip.items():
        keys = list(keys)
        for k1, k2 in itertools.combinations(keys, 2):
            if not (k1 & k2):
                return 6
    return best


def main(root):
    root = pathlib.Path(root)
    print("map | n m G | odd in/out | x y h | rank even | n+rank+m | G-(n.. ) = h+y-m | rows/cols odd | min rel")
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        circs = sorted(d.glob("*.circ.txt"), key=lambda p: int(NAME.search(p.name).group(1)))
        if not circs:
            continue
        vals, order, n = read(circs[0])
        outs = sorted(k for k in vals if k.startswith("y"))
        par = lambda v: bin(v).count("1") & 1
        x = y = h = 0
        for out, a, b in order:
            pa, pb = par(vals[a]), par(vals[b])
            if pa and pb:
                x += 1
            elif not pa and not pb:
                y += 1
            elif out not in outs:
                h += 1
        rows = [vals[k] for k in outs]
        m = len(rows)
        odd_out = sum(par(r) for r in rows)
        cols_odd = all(sum((r >> j) & 1 for r in rows) & 1 for j in range(n))
        even = [vals[g] for g, _, _ in order if not par(vals[g])]
        rk = rank(even)
        boundary = [1 << j for j in range(n)] + rows
        mr = min_rel(boundary) if n <= 32 else "skip"
        G = len(order)
        print(f"{d.name} | {n} {m} {G} | {n}/{odd_out} | {x} {y} {h} | {rk} | {n + rk + m if False else m + rk} | h+y={h + y} | {odd_out == m}/{cols_odd} | {mr if mr else '>6'}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "circuits")
