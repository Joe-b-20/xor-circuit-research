"""Own library for review-O: MixColumns matrix, parsers, reduction check, transpose, cut split.

Convention (FIPS 197 / NCFF files): x_(8b+r) = bit r (LSB=0) of byte b; y likewise.
Primal block j = input bits {8c+j : c}. Mirror (transposed) input 4*j+c <-> primal output 8c+j,
mirror group j = mirror bits {4j+c : c}.
"""
import os
import re

N = 32


def xt(a):
    a <<= 1
    return (a ^ 0x11B) if a & 0x100 else a


def gmul(a, k):
    r = 0
    while k:
        if k & 1:
            r ^= a
        a = xt(a)
        k >>= 1
    return r


M = [[2, 3, 1, 1], [1, 2, 3, 1], [1, 1, 2, 3], [3, 1, 1, 2]]


def mc_rows():
    """ROW[8i+r] = input mask of output bit r of byte i."""
    rows = [0] * 32
    for j in range(4):
        for s in range(8):
            # input bit (j, s): x_j = 1<<s; output byte i = sum M[i][j]*x_j
            for i in range(4):
                v = gmul(1 << s, M[i][j])
                for r in range(8):
                    if (v >> r) & 1:
                        rows[8 * i + r] |= 1 << (8 * j + s)
    return rows


ROWS = mc_rows()
PBLOCK = [sum(1 << (8 * c + j) for c in range(4)) for j in range(8)]
MBLOCK = [15 << (4 * j) for j in range(8)]


def transpose_rows(rows, n=32):
    """mirror rows indexed by mirror output (= primal input) in mirror bit coordinates."""
    out = []
    for i in range(n):          # primal input i -> mirror output i
        v = 0
        for o in range(len(rows)):
            if (rows[o] >> i) & 1:
                c, j = divmod(o, 8)
                v |= 1 << (4 * j + c)
        out.append(v)
    return out


MROWS = transpose_rows(ROWS)    # MROWS[8c+k] = mirror row of primal input (c,k)


def parse_pairs(line):
    return [(int(a), int(b)) for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", line)]


def parse_ncff(path):
    """gates as (a,b) operand indices; inputs x0..x31 = 0..31; names in definition order."""
    idx, gates = {}, []
    for i in range(32):
        idx["x%d" % i] = i
    for line in open(path):
        line = line.split("%")[0].strip()
        m = re.match(r"^XOR\s+(\S+)\s+(\S+)\s+(\S+)$", line)
        if not m:
            continue
        o, a, b = m.groups()
        gates.append((idx[a], idx[b]))
        idx[o] = 32 + len(gates) - 1
    return gates


def values(gates, n=32):
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        if a >= len(vals) or b >= len(vals):
            return None
        vals.append(vals[a] ^ vals[b])
    return vals


def check(gates, rows, n=32):
    """(computes, reduced, info). reduced = values distinct, nonzero, not inputs, no dead gate."""
    vals = values(gates, n)
    if vals is None:
        return False, False, "bad index"
    pos = {}
    for i, v in enumerate(vals):
        pos.setdefault(v, i)
    comp = all(r in pos for r in rows)
    distinct = len(set(vals)) == len(vals) and 0 not in vals
    live = set()
    stack = [pos[r] for r in rows if r in pos]
    while stack:
        x = stack.pop()
        if x in live or x < n:
            continue
        live.add(x)
        a, b = gates[x - n]
        stack += [a, b]
    dead = len(gates) - len(live)
    return comp, distinct and dead == 0, "distinct %s dead %d" % (distinct, dead)


def split(vals, ops, n, low):
    """vals: all values (inputs first); ops: list of (va, vb) operand VALUES per gate (gate i = vals[n+i]).
    Returns dict f,h,e,N,x and labels list."""
    first = set(v & low for v in vals[:n] if v & low)
    st = dict(f=0, h=0, e=0, N=0, x=0)
    labels = []
    for i in range(n, len(vals)):
        v = vals[i]
        va, vb = ops[i - n]
        om, oa, ob = v & low, va & low, vb & low
        if om == 0:
            if oa or ob:
                assert oa and ob and oa == ob
                st["x"] += 1
            else:
                st["N"] += 1
        elif om not in first:
            first.add(om)
            st["f"] += 1
        elif (oa == 0) != (ob == 0):
            st["e"] += 1
            labels.append(va if oa == 0 else vb)
        else:
            st["h"] += 1
    st["near"] = st["f"] + st["h"]
    st["far"] = st["N"] + st["x"] + st["e"]
    st["labels"] = labels
    return st


def rank(vs):
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def in_span(vs, w):
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    for b in basis:
        w = min(w, w ^ b)
    return w == 0


def W_info(rows, low):
    meet = [r for r in rows if r & low]
    s = [r & ~low for r in meet]
    oms = set(r & low for r in meet)
    return dict(rows=len(meet), dimW=rank(s), oms=len(oms),
                nonunit_oms=sum(1 for o in oms if bin(o).count("1") > 1), spart=s)


def transpose(gates, rows, n=32, order="fwd"):
    """Transposed circuit as (mirror values list, operand-value pairs), unreduced, plus reduced version.
    Primal outputs: first node computing rows[o]; mirror input o' = mirror bit index of output o."""
    vals = values(gates, n)
    pos = {}
    for i in range(n, len(vals)):
        pos.setdefault(vals[i], i)
    term = {}
    for o, r in enumerate(rows):
        c, j = divmod(o, 8)
        term.setdefault(pos[r], []).append(4 * j + c)
    readers = {}
    for gi, (a, b) in enumerate(gates):
        for x in (a, b):
            readers.setdefault(x, []).append(n + gi)
    Tm = [1 << i for i in range(n)]
    Tops = []
    adj = {}
    for v in reversed(range(len(vals))):
        idxs = list(term.get(v, [])) + [adj[r] for r in readers.get(v, []) if adj[r] is not None]
        if not idxs:
            adj[v] = None
            continue
        if order == "rev":
            idxs = idxs[::-1]
        acc = idxs[0]
        for x in idxs[1:]:
            Tm.append(Tm[acc] ^ Tm[x])
            Tops.append((acc, x))
            acc = len(Tm) - 1
        adj[v] = acc
    outs = [adj[i] for i in range(n)]       # mirror output for primal input i
    return Tm, Tops, outs


def reduce_mirror(Tm, Tops, n=32):
    """drop zero and repeated values; return vals list and operand-VALUE pairs (gates as index pairs too)."""
    seen = {}
    for i in range(n):
        seen[Tm[i]] = i
    rv = list(Tm[:n])
    rops = []
    rgates = []
    for i in range(n, len(Tm)):
        v = Tm[i]
        if v == 0 or v in seen:
            continue
        a, b = Tm[Tops[i - n][0]], Tm[Tops[i - n][1]]
        seen[v] = len(rv)
        rv.append(v)
        rops.append((a, b))
        rgates.append((seen[a], seen[b]))
    return rv, rops, rgates
