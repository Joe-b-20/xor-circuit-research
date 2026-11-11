"""Parity profile of a recorded circuit: python3 profile.py FILE.circ.txt [...]

Prints, for the circuit and for its matrix: the counts (x, y, h) of odd+odd gates, even+even
gates and odd non-output gates, the number of labels (even signals), the label multiplicities on
the odd graph, and the reuse rank sum_l (m_l - 1)_+ . Standard library only; examines existing
circuits, searches nothing.
"""
import pathlib
import re
import sys
from collections import Counter

GATE = re.compile(r"^(XOR)\s+(\S+)\s+(\S+)\s+(\S+)")
RANGE = re.compile(r"^(Inputs|Outputs):\s*([a-z]+)(\d+):[a-z]+(\d+)")


def read(circ):
    vals, order = {}, []
    n_in = None
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
        if not m:
            continue
        _, out, a, b = m.groups()
        vals[out] = vals[a] ^ vals[b]
        order.append((out, a, b))
    return vals, order, n_in


def par(v):
    return bin(v).count("1") & 1


def profile(circ):
    vals, order, n_in = read(circ)
    outs = {k for k in vals if k.startswith("y")}
    x = y = h = 0
    label_edges = Counter()
    edges = []
    for out, a, b in order:
        pa, pb = par(vals[a]), par(vals[b])
        if pa and pb:
            x += 1
            edges.append((a, b, out))
            label_edges[out] += 1
        elif not pa and not pb:
            y += 1
            label_edges[out] += 0
        else:
            if out not in outs:
                h += 1
            odd, even = (a, b) if pa else (b, a)
            edges.append((odd, out, even))
            label_edges[even] += 1
    G = len(order)
    boundary = {k for k in vals if k.startswith("x")} | outs
    bb = Counter()
    hb = hh = 0
    for p, q, l in edges:
        inb = (p in boundary) + (q in boundary)
        if inb == 2:
            bb[l] += 1
        elif inb == 1:
            hb += 1
        else:
            hh += 1
    labels = [k for k in vals if not par(vals[k])]
    missing = [l for l in labels if bb[l] == 0]
    mult = Counter(label_edges[l] for l in labels)
    reuse = sum(max(0, label_edges[l] - 1) for l in labels)
    print(f"{pathlib.Path(circ).name}: G={G} x={x} y={y} h={h} (32+x+y+h={32 + x + y + h})")
    print(f"  labels={len(labels)} missing q={len(missing)} H-H edges z={hh} H-B edges={hb} B-B edges={sum(bb.values())}")
    print(f"  label multiplicity histogram (edges per label: count) = {dict(sorted(mult.items()))}")
    print(f"  reuse rank sum (m_l-1)+ = {reuse}; edges-labels = {len(edges) - len(labels)} = 32+h-y = {32 + h - y}")


if __name__ == "__main__":
    for f in sys.argv[1:]:
        profile(f)
