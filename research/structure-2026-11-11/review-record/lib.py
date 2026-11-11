"""Shared helpers for the independent review of RECORD.md sections 1-4 (standard library only).

Circuits are read from scratch (NCFF: 'Inputs: x0:x31', 'Outputs: y0:y31', lines 'XOR out a b').
Masks are ints, bit j = input j. Rows of the matrix are taken from the *.mat.txt of the map and
checked against the circuit outputs.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
CIRC = ROOT / "circuits"
GATE = re.compile(r"^(XOR|XNOR)\s+(\S+)\s+(\S+)\s+(\S+)")
RANGE = re.compile(r"^(Inputs|Outputs):\s*([a-z]+)(\d+):([a-z]+)(\d+)")
NAME = re.compile(r"-xor(\d+)-depth(\d+)\.circ\.txt$")


def read_matrix(path):
    tokens = " ".join(l.split("#")[0].split("%")[0] for l in pathlib.Path(path).read_text().splitlines()).split()
    rn, cn = int(tokens[1]), int(tokens[2])
    bits = list(map(int, tokens[3:3 + rn * cn]))
    return [sum(bits[i * cn + j] << j for j in range(cn)) for i in range(rn)], cn


def read_circuit(path):
    """Return (n_inputs, gates, out_names) with gates = list of (name, a, b) and a dict of masks.

    Inputs are named x<base+j> with mask 1<<j. The output names are the declared Outputs range."""
    vals, gates, n_in, outs = {}, [], None, []
    for line in pathlib.Path(path).read_text().splitlines():
        line = line.split("%")[0].split("#")[0].strip()
        m = RANGE.match(line)
        if m:
            lo, hi = int(m.group(3)), int(m.group(5))
            if m.group(1) == "Inputs":
                n_in = hi - lo + 1
                for j in range(n_in):
                    vals[f"{m.group(2)}{lo + j}"] = 1 << j
            else:
                outs = [f"{m.group(2)}{lo + j}" for j in range(hi - lo + 1)]
            continue
        m = GATE.match(line)
        if m:
            _, o, a, b = m.groups()
            assert a in vals and b in vals and o not in vals, (path, line)
            vals[o] = vals[a] ^ vals[b]
            gates.append((o, a, b))
    return n_in, gates, outs, vals


def wt(v):
    return bin(v).count("1")


def par(v):
    return wt(v) & 1


class Span:
    """Incremental F_2 span with reduction."""

    def __init__(self):
        self.basis = {}  # pivot bit -> vector

    def reduce(self, v):
        while v:
            p = v.bit_length() - 1
            b = self.basis.get(p)
            if b is None:
                return v
            v ^= b
        return 0

    def add(self, v):
        v = self.reduce(v)
        if v:
            self.basis[v.bit_length() - 1] = v
            return True
        return False

    def __contains__(self, v):
        return self.reduce(v) == 0

    def dim(self):
        return len(self.basis)


def rank(vs):
    s = Span()
    for v in vs:
        s.add(v)
    return s.dim()


def all_circuits():
    for d in sorted(p for p in CIRC.iterdir() if p.is_dir()):
        mats = list(d.glob("*.mat.txt"))
        circs = sorted(d.glob("*.circ.txt"), key=lambda p: int(NAME.search(p.name).group(1)))
        if len(mats) != 1 or not circs:
            continue
        yield d.name, mats[0], circs


def load(circ, mat):
    """Load circuit and matrix and check that output i of the circuit equals row i."""
    rows, cn = read_matrix(mat)
    n, gates, outs, vals = read_circuit(circ)
    assert n == cn, (circ, n, cn)
    assert len(outs) == len(rows)
    for i, o in enumerate(outs):
        assert vals[o] == rows[i], (circ, o)
    return n, gates, outs, vals, rows
