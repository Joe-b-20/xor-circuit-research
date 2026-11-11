"""Shared helpers for the reviewer's checks (MixColumns from field arithmetic, NCFF parsing,
charges).  Input index i = 8*byte + bit (as in the .mat file and the NCFF interface).
Block j = {8c + j : c = 0..3}."""
import os

ROOT = os.path.expanduser("~/xor-circuit-research")


def xtime(b):
    b <<= 1
    if b & 0x100:
        b ^= 0x11B
    return b


def gmul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a = xtime(a)
        b >>= 1
    return r


def mixcolumns_rows():
    """Row masks (32-bit ints over inputs) of one column of MixColumns, from field arithmetic."""
    coef = [2, 3, 1, 1]
    rows = []
    for c in range(4):          # output byte
        for j in range(8):      # output bit
            m = 0
            for d in range(4):  # input byte
                k = coef[(d - c) % 4]
                for i in range(8):  # input bit
                    if (gmul(k, 1 << i) >> j) & 1:
                        m |= 1 << (8 * d + i)
            rows.append(m)
    return rows


def read_mat():
    p = os.path.join(ROOT, "circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")
    with open(p) as f:
        toks = f.read().split()
    assert toks[0] == "1" and toks[1] == "32" and toks[2] == "32"
    vals = list(map(int, toks[3:]))
    rows = []
    for r in range(32):
        m = 0
        for col in range(32):
            if vals[32 * r + col]:
                m |= 1 << col
        rows.append(m)
    return rows


def blockmask(j):
    return sum(1 << (8 * c + j) for c in range(4))


BM = [blockmask(j) for j in range(8)]


def blocks_of(m):
    return frozenset(j for j in range(8) if m & BM[j])


def read_ncff(path):
    """Returns (gates, outname) where gates = list of (a, b) signal indices; signals 0..31 inputs,
    32+k gate k; outname maps gate signal -> output index for y-named gates."""
    idx = {"x%d" % i: i for i in range(32)}
    gates, outname = [], {}
    in_slp = False
    with open(path) as f:
        for line in f:
            line = line.split("%")[0].strip()
            if line.startswith("begin SLP"):
                in_slp = True
                continue
            if line.startswith("end SLP"):
                break
            if not in_slp or not line:
                continue
            tok = line.split()
            assert tok[0] == "XOR", line
            o, a, b = tok[1], tok[2], tok[3]
            s = 32 + len(gates)
            gates.append((idx[a], idx[b]))
            assert o not in idx
            idx[o] = s
            if o.startswith("y"):
                outname[s] = int(o[1:])
    return gates, outname


def masks(gates, n=32):
    v = [1 << i for i in range(n)]
    for a, b in gates:
        assert a < len(v) and b < len(v)
        v.append(v[a] ^ v[b])
    return v


def ancestors_sets(gates, n=32):
    """anc[s] = set of gate signals that are ancestors-or-equal of signal s (via wires)."""
    anc = [frozenset() for _ in range(n)]
    for k, (a, b) in enumerate(gates):
        s = n + k
        anc.append(anc[a] | anc[b] | {s})
    return anc


def charges(gates, rows, carriers="all", outname=None, n=32):
    """Per-sheet D_j sizes, mu per gate, block-monotone flag.  carriers='all': every gate whose
    mask equals a row of sheet j is an output gate of sheet j; 'named': only the y-named gate."""
    v = masks(gates, n)
    anc = ancestors_sets(gates, n)
    G = len(gates)
    rowset = {r: i for i, r in enumerate(rows)}
    out_gates = {j: [] for j in range(8)}  # sheet j = outputs (c, j) = row 8c + j
    for k in range(G):
        s = n + k
        if carriers == "all":
            if v[s] in rowset:
                out_gates[rowset[v[s]] % 8].append(s)
        else:
            if s in outname:
                out_gates[outname[s] % 8].append(s)
    for j in range(8):
        got = {v[s] for s in out_gates[j]}
        assert got == {rows[8 * c + j] for c in range(4)}, ("sheet not computed", j)
    A = {}
    D = {}
    for j in range(8):
        Aj = set()
        for s in out_gates[j]:
            Aj |= anc[s]
        A[j] = Aj
        D[j] = {s for s in Aj if v[s] & BM[j]}
    mu = {n + k: sum(1 for j in range(8) if (n + k) in D[j]) for k in range(G)}
    # block-monotone: g ancestor (strict or equal) of an output o => blocks(g) subset blocks(o)
    allout = [s for j in range(8) for s in out_gates[j]]
    bm_viol = set()
    for o in allout:
        bo = blocks_of(v[o])
        for g in anc[o]:
            if not blocks_of(v[g]) <= bo:
                bm_viol.add(g)
    return dict(D=[len(D[j]) for j in range(8)], mu=mu, bm_viol=bm_viol, G=G, v=v, A=A)
