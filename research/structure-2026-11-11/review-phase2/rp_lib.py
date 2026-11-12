"""Reviewer's own library (review of causal/REPORT.md and direct-sum/REPORT.md).  Written from scratch;
shares no code with the investigator's scripts.  Standard library only.  Vectors are Python ints (bit i =
coordinate i)."""
import re

ROOT = "/home/joebachir20/xor-circuit-research"


# ------------------------------------------------------------------ parsing
def load_txt(path):
    """rotation format: 'n k' then k lines 'a b' (signals 0..n-1 inputs, n+i gate i)."""
    lines = []
    for line in open(path):
        line = line.split("#")[0].strip()
        if line:
            lines.append(line)
    n, k = map(int, lines[0].split())
    gates = [tuple(map(int, l.split()[:2])) for l in lines[1:1 + k]]
    assert len(gates) == k
    return n, gates


def load_ncff(path):
    """NCFF: 'XOR out a b' lines; inputs x0..x(n-1)."""
    idx = {}
    gates = []
    n = None
    names_out = []
    for line in open(path):
        line = line.split("%")[0].strip()
        m = re.match(r"Inputs:\s*x(\d+):x(\d+)", line)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            n = hi - lo + 1
            for j in range(n):
                idx["x%d" % (lo + j)] = j
            continue
        m = re.match(r"XOR\s+(\S+)\s+(\S+)\s+(\S+)", line)
        if m:
            out, a, b = m.groups()
            gates.append((idx[a], idx[b]))
            idx[out] = n + len(gates) - 1
            names_out.append(out)
    return n, gates, idx


def values(n, gates):
    v = [1 << i for i in range(n)]
    for a, b in gates:
        v.append(v[a] ^ v[b])
    return v


def load_matrix(path):
    rows = []
    lines = [l.split() for l in open(path) if l.strip()]
    # first line: count, second: 'r c'
    r, c = map(int, lines[1])
    for l in lines[2:2 + r]:
        rows.append(sum(int(x) << j for j, x in enumerate(l)))
    return rows


# ------------------------------------------------------------------ Q_m rows (re-derived from qm.py doc)
def qm_rows(m):
    def bit(c, j):
        return 1 << (4 * (j % m) + (c % 4))

    out = []
    for j in range(m):
        for c in range(4):
            E = bit(c + 1, j) | bit(c + 2, j) | bit(c + 3, j)
            s = bit(c, j - 1) | bit(c + 1, j - 1)
            out.append(E ^ s)
    return out  # index 4j + c


# ------------------------------------------------------------------ F2 linear algebra
def rank(vecs):
    basis = {}
    for v in vecs:
        while v:
            h = v.bit_length() - 1
            if h in basis:
                v ^= basis[h]
            else:
                basis[h] = v
                break
    return len(basis)


def in_span(basis_list, v):
    basis = {}
    for b in basis_list:
        while b:
            h = b.bit_length() - 1
            if h in basis:
                b ^= basis[h]
            else:
                basis[h] = b
                break
    while v:
        h = v.bit_length() - 1
        if h not in basis:
            return False
        v ^= basis[h]
    return True


def all_triples(S):
    """collinear triples of a set S of distinct nonzero ints: list of sorted index triples."""
    pos = {v: i for i, v in enumerate(S)}
    out = []
    for i in range(len(S)):
        for j in range(i + 1, len(S)):
            k = pos.get(S[i] ^ S[j])
            if k is not None and k > j:
                out.append((i, j, k))
    return out


def derivations(S, n, T):
    """S list of distinct nonzero vectors with S[0..n-1] the units; T list of index triples forming a
    basis of R(S).  Returns dict v -> bitmask over T of the unique subset whose formal sum has non-input
    part [v], for every non-input index v.  Raises if T is not a basis."""
    G = len(S) - n
    assert len(T) == G
    rows = []
    for ti, t in enumerate(T):
        val = 0
        for x in t:
            if x >= n:
                val |= 1 << (x - n)
        rows.append([val, 1 << ti])
    piv = {}
    used = [False] * G
    for col in range(G):
        p = None
        for i in range(G):
            if not used[i] and (rows[i][0] >> col) & 1:
                p = i
                break
        if p is None:
            raise ValueError("not a basis")
        used[p] = True
        for i in range(G):
            if i != p and (rows[i][0] >> col) & 1:
                rows[i][0] ^= rows[p][0]
                rows[i][1] ^= rows[p][1]
        piv[col] = p
    return {n + col: rows[piv[col]][1] for col in range(G)}


def executable(S, n, T):
    """leaf-property peeling: True iff (S, T) is a circuit on its triples."""
    remaining = set(range(len(T)))
    while remaining:
        cnt = {}
        for ti in remaining:
            for x in T[ti]:
                if x >= n:
                    cnt.setdefault(x, []).append(ti)
        leaf = None
        for x, lst in cnt.items():
            if len(lst) == 1:
                leaf = lst[0]
                break
        if leaf is None:
            return False
        remaining.discard(leaf)
    return True


def popcount(v):
    return bin(v).count("1")
