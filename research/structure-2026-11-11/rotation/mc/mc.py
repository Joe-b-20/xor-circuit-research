"""MixColumns: sheets, charges, block-monotonicity and the local gate sets of the decomposition.

Library + command line:
  python3 mc.py FILE.circ.txt [...]           analyse recorded circuits (NCFF)
Masks use the repository convention: bit 8c + j = input (byte c, bit j); block j = the four inputs (., j).
Sheet j = the four outputs (c, j); its block support is {j-1, j}, plus block 7 for j = 1, 3, 4 ({7, 0} for j = 0).

Definitions (REPORT part II):
  anc(j)      gates that are ancestors-or-equal of an output gate of sheet j
  mu(g)       number of j with g nonzero on block j and g in anc(j)        (charge)
  monotone    for every output o and every g in anc(o): blocks(g) is a subset of blocks(o)
  G01         gates in anc(0) or anc(1) that are not supported on block 7 alone
  G34         gates in anc(3) or anc(4) that are not supported on block 2 alone or on block 7 alone
Standard library only.
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
MAT = os.path.join(HERE, "..", "..", "..", "..", "circuits", "aes-mixcolumns", "aes-mixcolumns.mat.txt")


def read_mat(path=MAT):
    toks = open(path).read().split()
    r, c = int(toks[1]), int(toks[2])
    bits = [int(t) for t in toks[3:3 + r * c]]
    return [sum(bits[i * c + j] << j for j in range(c)) for i in range(r)]


TARGETS = read_mat()                      # TARGETS[8c + j] = output (c, j)
BLOCKMASK = [sum(1 << (8 * c + j) for c in range(4)) for j in range(8)]


def blocks(v):
    return frozenset(j for j in range(8) if v & BLOCKMASK[j])


SHEET_SUPPORT = [blocks(TARGETS[j]) for j in range(8)]     # the four outputs of a sheet have equal support
for _j in range(8):
    assert all(blocks(TARGETS[8 * c + _j]) == SHEET_SUPPORT[_j] for c in range(4))


def parse_pairs(line):
    return [(int(a), int(b)) for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", line)]


def parse_ncff(path):
    """Returns the gate list (operand indices; inputs 0..31) of an NCFF .circ.txt file."""
    idx, gates = {}, []
    for line in open(path):
        line = line.split("%")[0].split("#")[0].strip()
        m = re.match(r"^Inputs:\s*([a-z]+)(\d+):[a-z]+(\d+)", line)
        if m:
            for i in range(int(m.group(2)), int(m.group(3)) + 1):
                idx[f"{m.group(1)}{i}"] = i - int(m.group(2))
            continue
        m = re.match(r"^XOR\s+(\S+)\s+(\S+)\s+(\S+)", line)
        if m:
            out, a, b = m.groups()
            gates.append((idx[a], idx[b]))
            idx[out] = 32 + len(gates) - 1
    return gates


def analyse(gates, targets=TARGETS):
    """Dictionary of statistics, or None if the gate list does not compute MixColumns."""
    n = 32
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        if not (a < len(vals) and b < len(vals)):
            return None
        vals.append(vals[a] ^ vals[b])
    first = {}
    for i in range(n, len(vals)):
        first.setdefault(vals[i], i)
    if any(t not in first for t in targets):
        return None
    G = len(gates)
    sup = [blocks(v) for v in vals]
    anc = [set() for _ in range(8)]
    viol = set()
    for oi, t in enumerate(targets):
        o = first[t]
        seen, stack = set(), [o]
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        j = oi % 8
        anc[j] |= seen
        so = sup[o]
        for g in seen:
            if not sup[g] <= so:
                viol.add(g)
    charges = [sum(1 for g in anc[j] if j in sup[g]) for j in range(8)]
    mu = [sum(1 for j in range(8) if j in sup[g] and g in anc[j]) for g in range(n, n + G)]
    dead = sum(1 for g in range(n, n + G) if not any(g in anc[j] for j in range(8)))
    pure7 = [g for g in range(n, n + G) if sup[g] == frozenset([7])]
    g01 = sum(1 for g in (anc[0] | anc[1]) if sup[g] != frozenset([7]))
    g34 = sum(1 for g in (anc[3] | anc[4]) if sup[g] not in (frozenset([2]), frozenset([7])))
    m27 = sum(1 for g in range(n, n + G) if sup[g] == frozenset([2, 7]))
    pats = Counter("".join(map(str, sorted(sup[g]))) for g in range(n, n + G))
    return dict(G=G, distinct=len(set(vals[n:])), monotone=not viol, violating=len(viol), charges=charges,
                sum_mu=sum(mu), excess=sum(max(0, x - 1) for x in mu), uncharged=mu.count(0), dead=dead,
                pure7=len(pure7), pure7_not_sheet7=sum(1 for g in pure7 if g not in anc[7]),
                G01=g01, G34=g34, M27=m27, patterns=dict(pats),
                uncharged_patterns=dict(Counter("".join(map(str, sorted(sup[n + i]))) for i, x in enumerate(mu) if x == 0)))


def support_closed_wiring(values):
    """Is there a wiring of the value set in which both operands of every gate are supported inside the
    block support of the gate (then the circuit is block-monotone)?  values: iterable of gate masks."""
    values = set(values)
    avail = {1 << i for i in range(32)}
    pending = set(values)
    progress = True
    while pending and progress:
        progress = False
        for v in list(pending):
            sv = blocks(v)
            bm = sum(BLOCKMASK[j] for j in sv)
            cands = [a for a in avail if not (a & ~bm)]
            cs = set(cands)
            if any((a ^ v) in cs for a in cands):
                avail.add(v)
                pending.discard(v)
                progress = True
    return not pending


def main():
    for f in sys.argv[1:]:
        res = analyse(parse_ncff(f))
        print(os.path.basename(f), {k: v for k, v in res.items() if k != "patterns"})
        print("   support patterns:", dict(sorted(res["patterns"].items())))


if __name__ == "__main__":
    main()
