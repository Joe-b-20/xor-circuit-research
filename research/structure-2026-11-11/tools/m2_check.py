"""The half-size quotient map M2 of MixColumns and a 26-gate circuit for it.

M2 is MixColumns restricted to the inputs (u, v, u, v) (bytes), i.e. to (1+y)^2 R: the outputs are
out0 = out2 = u + 2(u+v), out1 = out3 = v + 2(u+v). As a 16 x 16 bit matrix: inputs u_0..u_7 (bits
0..7), v_0..v_7 (bits 8..15); outputs out0 bits then out1 bits.

Checks (a) that M2 built from the repository matrix equals the formula, (b) the explicit 26-gate
circuit below. Also prints the partition of each circuit given on the command line (blocks of
inputs i ~ j iff e_i + e_j lies in the span of the even gate signals).
Standard library only.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]


def read_matrix(path):
    tokens = " ".join(l.split("#")[0].split("%")[0] for l in path.read_text().splitlines()).split()
    rows_n, cols_n = int(tokens[1]), int(tokens[2])
    bits = list(map(int, tokens[3:3 + rows_n * cols_n]))
    return [sum(bits[i * cols_n + j] << j for j in range(cols_n)) for i in range(rows_n)]


def m2_rows():
    rows = read_matrix(ROOT / "circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")
    out = []
    for r in rows[:16]:  # out0 and out1
        m = 0
        for j in range(8):
            u = ((r >> j) & 1) ^ ((r >> (16 + j)) & 1)
            v = ((r >> (8 + j)) & 1) ^ ((r >> (24 + j)) & 1)
            m |= (u << j) | (v << (8 + j))
        out.append(m)
    return out


def formula_rows():
    U = [1 << j for j in range(8)]
    V = [1 << (8 + j) for j in range(8)]
    W = [U[j] ^ V[j] for j in range(8)]
    two = [W[7], W[0] ^ W[7], W[1], W[2] ^ W[7], W[3] ^ W[7], W[4], W[5], W[6]]
    return [U[j] ^ two[j] for j in range(8)] + [V[j] ^ two[j] for j in range(8)]


def circuit26():
    U = [1 << j for j in range(8)]
    V = [1 << (8 + j) for j in range(8)]
    gates = []

    def g(a, b):
        gates.append(a ^ b)
        return a ^ b

    w = {k: g(U[k], V[k]) for k in (7, 1, 4, 5, 6)}          # 5 producers
    o = {}
    o["u0"], o["v0"] = g(U[0], w[7]), g(V[0], w[7])
    alpha = g(V[0], o["u0"])                                  # w0 + w7, odd + odd
    o["u1"], o["v1"] = g(U[1], alpha), g(V[1], alpha)
    o["u2"], o["v2"] = g(U[2], w[1]), g(V[2], w[1])
    p2 = g(U[2], w[7])                                        # helper
    beta = g(p2, V[2])                                        # w2 + w7
    o["u3"], o["v3"] = g(U[3], beta), g(V[3], beta)
    p3 = g(U[3], w[7])                                        # helper
    gamma = g(p3, V[3])                                       # w3 + w7
    o["u4"], o["v4"] = g(U[4], gamma), g(V[4], gamma)
    for j, k in ((5, 4), (6, 5), (7, 6)):
        o[f"u{j}"], o[f"v{j}"] = g(U[j], w[k]), g(V[j], w[k])
    outs = [o[f"u{j}"] for j in range(8)] + [o[f"v{j}"] for j in range(8)]
    return gates, outs


GATE = re.compile(r"^(XOR)\s+(\S+)\s+(\S+)\s+(\S+)")
RANGE = re.compile(r"^(Inputs|Outputs):\s*([a-z]+)(\d+):[a-z]+(\d+)")


def partition(circ):
    vals, n = {}, 0
    evens = []
    for line in pathlib.Path(circ).read_text().splitlines():
        line = line.split("%")[0].split("#")[0].strip()
        m = RANGE.match(line)
        if m and m.group(1) == "Inputs":
            base = int(m.group(3))
            n = int(m.group(4)) - base + 1
            for j in range(n):
                vals[f"x{j + base}"] = 1 << j
            continue
        m = GATE.match(line)
        if m:
            _, out, a, b = m.groups()
            vals[out] = vals[a] ^ vals[b]
            if bin(vals[out]).count("1") % 2 == 0:
                evens.append(vals[out])
    basis = []
    for v in evens:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)

    def inspan(v):
        for b in basis:
            v = min(v, v ^ b)
        return v == 0

    blocks, seen = [], set()
    for i in range(n):
        if i in seen:
            continue
        blk = [j for j in range(n) if j == i or inspan((1 << i) ^ (1 << j))]
        seen.update(blk)
        blocks.append(blk)
    return blocks


if __name__ == "__main__":
    a, b = m2_rows(), formula_rows()
    print("M2 from repository matrix equals formula:", a == b)
    gates, outs = circuit26()
    print("26-gate circuit: gates =", len(gates), "distinct nonzero =", len(set(gates)) == len(gates) and 0 not in gates,
          "outputs correct =", outs == b)
    print("M2 rows (hex):", " ".join(f"{r:04x}" for r in b))
    for f in sys.argv[1:]:
        bl = partition(f)
        print(pathlib.Path(f).name, "blocks:", len(bl), bl)
