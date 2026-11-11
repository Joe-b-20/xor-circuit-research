"""Shared helpers for the restriction study (imported by the other scripts; not run directly).

Masks are Python ints: bit j of a row mask = coefficient of input x_j.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
MC_DIR = ROOT / "circuits" / "aes-mixcolumns"
MAT = MC_DIR / "aes-mixcolumns.mat.txt"
GATE = re.compile(r"^(XOR|XNOR)\s+(\S+)\s+(\S+)\s+(\S+)")
N = 32


def read_matrix(path=MAT):
    tokens = " ".join(l.split("#")[0].split("%")[0] for l in path.read_text().splitlines()).split()
    rows_n, cols_n = int(tokens[1]), int(tokens[2])
    bits = list(map(int, tokens[3:3 + rows_n * cols_n]))
    return [sum(bits[i * cols_n + j] << j for j in range(cols_n)) for i in range(rows_n)]


def transpose(rows, n=N):
    return [sum(((rows[i] >> j) & 1) << i for i in range(len(rows))) for j in range(n)]


def wt(v):
    return bin(v).count("1")


def rank(vecs):
    """Rank over F2 of a list of int bit-vectors."""
    basis = {}
    r = 0
    for v in vecs:
        while v:
            h = v.bit_length() - 1
            if h in basis:
                v ^= basis[h]
            else:
                basis[h] = v
                r += 1
                break
    return r


def apply(rows, u):
    """M u for M given by its rows (u an int over inputs)."""
    out = 0
    for i, r in enumerate(rows):
        if wt(r & u) & 1:
            out |= 1 << i
    return out


def inverse(rows, n=N):
    """Rows of M^{-1} (Gauss-Jordan over F2)."""
    a = [(rows[i], 1 << i) for i in range(n)]
    for col in range(n):
        piv = next(i for i in range(col, n) if (a[i][0] >> col) & 1)
        a[col], a[piv] = a[piv], a[col]
        for i in range(n):
            if i != col and (a[i][0] >> col) & 1:
                a[i] = (a[i][0] ^ a[col][0], a[i][1] ^ a[col][1])
    return [a[i][1] for i in range(n)]


def read_circuit(path):
    """Return (gates, outputs): gates = list of (name, a, b); masks via circuit_masks."""
    gates, names = [], []
    for line in path.read_text().splitlines():
        line = line.split("%")[0].split("#")[0].strip()
        m = GATE.match(line)
        if m:
            gates.append((m.group(2), m.group(3), m.group(4)))
    return gates


def circuit_masks(gates, n=N):
    """Signals in order: inputs x0..x{n-1} then gates. Returns (names, masks, ops)."""
    names = [f"x{j}" for j in range(n)]
    idx = {nm: j for j, nm in enumerate(names)}
    masks = [1 << j for j in range(n)]
    ops = [None] * n
    for out, a, b in gates:
        ia, ib = idx[a], idx[b]
        idx[out] = len(names)
        names.append(out)
        masks.append(masks[ia] ^ masks[ib])
        ops.append((ia, ib))
    return names, masks, ops, idx


def mc_circuits():
    return sorted(MC_DIR.glob("*.circ.txt"))
