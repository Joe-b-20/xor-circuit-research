"""Reviewer's own library (machine review, phase 7). Independent of the authors' scripts.

MixColumns from the AES definition: out_i = 2 a_i + 3 a_{i+1} + a_{i+2} + a_{i+3}, GF(2^8) mod 0x11b.
Wire 8c + j = bit j of byte c; block j = wires {8c + j : c = 0..3}; sheet t = rows (i, t).
Circuit = list of (a, b) signal pairs; signal s < 32 is input s, signal 32 + k is gate k.
"""
import json
import os
import re

HOME = os.path.expanduser("~")
REPO = os.path.join(HOME, "xor-circuit-research")
REC = os.path.join(REPO, "circuits", "aes-mixcolumns")
KSTE = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
JOINT = os.path.join(REPO, "research/structure-2026-11-11/joint")
COMPAT = os.path.join(REPO, "research/structure-2026-11-11/review-compat")


def gmul(a, m):
    r = 0
    while m:
        if m & 1:
            r ^= a
        a <<= 1
        if a & 0x100:
            a ^= 0x11B
        m >>= 1
    return r


def build_rows():
    rows = {}
    for i in range(4):
        coef = {i: 2, (i + 1) % 4: 3, (i + 2) % 4: 1, (i + 3) % 4: 1}
        for t in range(8):
            mask = 0
            for k in range(4):
                for j in range(8):
                    if gmul(1 << j, coef[k]) >> t & 1:
                        mask |= 1 << (8 * k + j)
            rows[(i, t)] = mask
    return rows


ROWS = build_rows()
RKEYS = sorted(ROWS)  # row index = position in RKEYS
FULL = (1 << 32) - 1


def blk(j):
    return sum(1 << (8 * c + j) for c in range(4))


BLK = [blk(j) for j in range(8)]


def supp(v):
    return frozenset(j for j in range(8) if v & BLK[j])


def nib(v, j):
    return sum(((v >> (8 * c + j)) & 1) << c for c in range(4))


WIN = {}
for (i, t), m in ROWS.items():
    WIN.setdefault(t, set()).add(supp(m))
assert all(len(s) == 1 for s in WIN.values())
WIN = {t: next(iter(s)) for t, s in WIN.items()}


def values(g):
    v = [1 << i for i in range(32)]
    for a, b in g:
        v.append(v[a] ^ v[b])
    return v


def check(g):
    v = values(g)
    ok = all(r in set(v[32:]) for r in ROWS.values())
    red = len(set(v)) == len(v) and 0 not in v
    topo = all(a < 32 + k and b < 32 + k for k, (a, b) in enumerate(g))
    return ok, red and topo


def load_ncff(path):
    name = {}
    for i in range(32):
        name["x%d" % i] = i
    g, outs = [], {}
    for line in open(path):
        p = line.split()
        if len(p) == 4 and p[0] == "XOR":
            g.append((name[p[2]], name[p[3]]))
            name[p[1]] = 31 + len(g)
            if p[1][0] == "y":
                outs[int(p[1][1:])] = 31 + len(g)
    return g, outs


def load_kste(fn, line):
    ls = [l for l in open(os.path.join(KSTE, fn)) if l.strip()]
    return [(int(a), int(b)) for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", ls[line - 1])]


def kste_count(fn):
    return sum(1 for l in open(os.path.join(KSTE, fn)) if l.strip())


def load_json(path):
    return [tuple(x) for x in json.load(open(path))]


def keepmask(B):
    m = FULL
    for b in B:
        m &= ~BLK[b]
    return m


def restrict(g, v, B):
    """Sequential removal (first-producer convention). Returns (removed set, useful set)."""
    keep = keepmask(B)
    rep = {0: -1}
    for i in range(32):
        p = (1 << i) & keep
        if p not in rep:
            rep[p] = i
    first = {}
    removed = set()
    for k, (a, c) in enumerate(g):
        x = 32 + k
        p = v[x] & keep
        if p in rep:
            removed.add(x)
        else:
            rep[p] = x
            first[x] = (a, c)
    useful, st = set(), []
    for r in ROWS.values():
        s = rep[r & keep]
        if s >= 32:
            st.append(s)
    while st:
        s = st.pop()
        if s in useful:
            continue
        useful.add(s)
        for o in first[s]:
            q = rep[v[o] & keep]
            assert q != -1 or v[o] & keep == 0
            if q >= 32:
                st.append(q)
    return removed, useful


def D_formula(v, B):
    keep = keepmask(B)
    sig = set([0] + v)
    return len(sig) - len({x & keep for x in sig}) - 4 * len(B)


def pure_block(x):
    s = supp(x)
    return next(iter(s)) if len(s) == 1 else None


def readers_of(g):
    n = 32 + len(g)
    rd = [[] for _ in range(n)]
    for k, (a, c) in enumerate(g):
        rd[a].append(32 + k)
        rd[c].append(32 + k)
    return rd


def rho_all(g, v):
    """rho[s] = 32-bit mask over RKEYS: parity of #paths from s to each output node."""
    n = len(v)
    node = {}
    for idx, r in enumerate(RKEYS):
        node.setdefault(v.index(ROWS[r], 32), 0)
        node[v.index(ROWS[r], 32)] |= 1 << idx
    rd = readers_of(g)
    rho = [0] * n
    for s in range(n - 1, -1, -1):
        x = node.get(s, 0)
        for w in rd[s]:
            x ^= rho[w]
        rho[s] = x
    return rho


def ancestors_of_rows(g, v):
    """anc[j] = set of signals (gates only) with a path to (or equal to) a row node of sheet j."""
    anc = {}
    for j in range(8):
        st = [v.index(ROWS[(i, j)], 32) for i in range(4)]
        A = set()
        while st:
            s = st.pop()
            if s < 32 or s in A:
                continue
            A.add(s)
            st.extend(g[s - 32])
        anc[j] = A
    return anc


SHEETMASK = {j: sum(1 << idx for idx, r in enumerate(RKEYS) if r[1] == j) for j in range(8)}


def colmask(k, b):
    """column (k, b) of M as a mask over RKEYS."""
    return sum(1 << idx for idx, r in enumerate(RKEYS) if ROWS[r] >> (8 * k + b) & 1)


def gf2rank(vs):
    basis = []
    for x in vs:
        for y in basis:
            x = min(x, x ^ y)
        if x:
            basis.append(x)
    return len(basis)
