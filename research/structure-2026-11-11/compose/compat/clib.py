"""CHECK library (compat study): MixColumns cut statistics at a primal single-block cut.

Own MixColumns matrix (AES poly 0x11b, wire 8c+j = bit j of byte c). Block j = wires {8c+j}.
Circuits: recorded NCFF files (via review-pair/rlib.read_ncff) or kste corpus lines.
Standard library only.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "review-pair"))
import rlib  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
REC = os.path.join(ROOT, "circuits", "aes-mixcolumns")
KSTE = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")


def xt(b):
    b <<= 1
    return (b ^ 0x11b) if b & 0x100 else b


def mul(a, m):
    return {1: a, 2: xt(a), 3: xt(a) ^ a}[m]


def mc_rows():
    """dict (c, j) -> mask of output bit j of byte c."""
    rows = {}
    for i in range(4):
        for t in range(8):
            mask = 0
            for c in range(4):
                m = [2, 3, 1, 1][(c - i) % 4]
                for j in range(8):
                    if (mul(1 << j, m) >> t) & 1:
                        mask |= 1 << (8 * c + j)
            rows[(i, t)] = mask
    return rows


ROWS = mc_rows()


def bm(k):
    return sum(1 << (8 * c + k) for c in range(4))


def blocks(v):
    return frozenset(j for j in range(8) if v & bm(j))


def nib(v, j):
    return sum(((v >> (8 * c + j)) & 1) << c for c in range(4))


def desc(v):
    return " ".join("%d:%s" % (j, format(nib(v, j), "04b")[::-1]) for j in range(8) if nib(v, j))


def rank(vs):
    return len(rlib.reduce_basis(list(vs)))


def load(spec):
    """spec: 'r88', 'r89', 'r97' or 'FILE:LINE' (kste, 1-based among non-empty lines)."""
    if spec[0] == "r":
        fn = {"r88": "aes-mixcolumns-xor88-depth5.circ.txt", "r89": "aes-mixcolumns-xor89-depth4.circ.txt",
              "r97": "aes-mixcolumns-xor97-depth3.circ.txt"}[spec]
        _, g = rlib.read_ncff(os.path.join(REC, fn))
        return g
    fn, n = spec.split(":")
    ls = [l for l in open(os.path.join(KSTE, fn)) if l.strip()]
    return [(int(a), int(b)) for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", ls[int(n) - 1])]


def values(gates):
    v = [1 << i for i in range(32)]
    for a, b in gates:
        v.append(v[a] ^ v[b])
    return v


def check(gates):
    vals = values(gates)
    ok = all(t in set(vals[32:]) for t in ROWS.values())
    reduced = len(set(vals)) == len(vals) and 0 not in vals
    return ok, reduced


def ancestors(gates, roots):
    anc, st = set(), list(roots)
    while st:
        s = st.pop()
        if s < 32 or s in anc:
            continue
        anc.add(s)
        st.extend(gates[s - 32])
    return anc


def cut(gates, k):
    """Classify every gate at primal block k. Returns dict with lists and the label data."""
    vals = values(gates)
    low = bm(k)
    om = lambda x: vals[x] & low
    seen = {1 << i for i in range(32) if (1 << i) & low}
    kind = {}
    labels = []  # (gate index, far operand index)
    for gi, (a, b) in enumerate(gates):
        g = 32 + gi
        if om(g) == 0:
            kind[g] = "x" if (om(a) or om(b)) else "o"
        elif (om(a) == 0) != (om(b) == 0):
            kind[g] = "e"
            labels.append((g, a if om(a) == 0 else b))
        elif om(g) in seen:
            kind[g] = "h"
        else:
            seen.add(om(g))
            kind[g] = "f"
    return vals, kind, labels


def W(k):
    low = bm(k)
    return [r & ~low for r in ROWS.values() if r & low]


def far_rows(k):
    low = bm(k)
    return [r for r in ROWS.values() if not r & low]
