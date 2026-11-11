"""Read recorded MixColumns / InvMixColumns circuits "from the outputs".

Usage: python3 mc_reencode.py            (run from the repository root or from this directory)

A circuit for an invertible matrix A with G gates is, read with the outputs as inputs, a cyclic
system of size G for A^-1 (REPORT.md, Theorem C).  It is a circuit for A^-1 exactly when the closure
of the 32 output masks, under "two points of a collinear triple are in, so the third is in", is the
whole mask set.  For every recorded circuit of the two AES maps this script prints the size of that
closure, once using only the gate equations and once using every collinear triple of the mask set.
Nothing is searched; this only examines recorded circuits.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
GATE = re.compile(r"^(XOR)\s+(\S+)\s+(\S+)\s+(\S+)")


def read_matrix(path):
    tokens = " ".join(l.split("#")[0].split("%")[0] for l in path.read_text().splitlines()).split()
    rows_n, cols_n = int(tokens[1]), int(tokens[2])
    bits = list(map(int, tokens[3:3 + rows_n * cols_n]))
    return [sum(bits[i * cols_n + j] << j for j in range(cols_n)) for i in range(rows_n)], cols_n


def read_circuit(path, n):
    vals = {"x%d" % j: 1 << j for j in range(n)}
    gates = []
    for line in path.read_text().splitlines():
        line = line.split("%")[0].split("#")[0].strip()
        m = GATE.match(line)
        if m:
            _, g, a, b = m.groups()
            vals[g] = vals[a] ^ vals[b]
            gates.append((g, a, b))
    return vals, gates


def closure(start, triples_of):
    known = set(start)
    frontier = list(start)
    while frontier:
        a = frontier.pop()
        for b, c in triples_of.get(a, ()):
            if b in known and c not in known:
                known.add(c)
                frontier.append(c)
            elif c in known and b not in known:
                known.add(b)
                frontier.append(b)
    return known


def main():
    for folder in ("aes-mixcolumns", "aes-invmixcolumns"):
        d = ROOT / "circuits" / folder
        rows, n = read_matrix(d / (folder + ".mat.txt"))
        for circ in sorted(d.glob("*.circ.txt")):
            vals, gates = read_circuit(circ, n)
            outs = [vals["y%d" % j] for j in range(len(rows))]
            assert outs == rows, circ
            masks = set(vals.values())
            ins = [1 << j for j in range(n)]
            gate_tri, all_tri = {}, {}
            for g, a, b in gates:
                t = (vals[g], vals[a], vals[b])
                for i in range(3):
                    gate_tri.setdefault(t[i], []).append((t[(i + 1) % 3], t[(i + 2) % 3]))
            ms = sorted(masks)
            ntri = 0
            for i, a in enumerate(ms):
                for b in ms[i + 1:]:
                    c = a ^ b
                    if c > b and c in masks:
                        ntri += 1
                        for p, q, r in ((a, b, c), (b, c, a), (c, a, b)):
                            all_tri.setdefault(p, []).append((q, r))
            c_in = len(closure(ins, all_tri))
            c_gate = len(closure(outs, gate_tri))
            c_all = len(closure(outs, all_tri))
            print("%-44s gates %3d  masks %3d  collinear triples %3d | closure from the outputs: "
                  "%3d (gate equations only), %3d (all triples) of %d%s"
                  % (circ.name, len(gates), len(masks), ntri, c_gate, c_all, len(masks),
                     "   <- also a circuit for the inverse map" if c_all == len(masks) else ""))
            assert c_in == len(masks)


if __name__ == "__main__":
    main()
