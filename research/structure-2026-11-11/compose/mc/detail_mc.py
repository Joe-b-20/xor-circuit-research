"""CHECK: one corpus circuit in detail: primal block-cancelling gates and mirror exits (fwd order).

usage: python3 detail_mc.py FILE LINE     (LINE = cumulative non-empty line number as in corpus_mc.py)
Also checks the window graphs: primal (sheet supports) and mirror (row windows); lists triangles not
inside one window.
"""
import os
import sys
from itertools import combinations

from mirror_mc import WIN, desc as mdesc, groups, mirror, split, mc
from corpus_mc import KSTE, primal_split, serves

PN = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
      0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
      0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}


def pnib(v, j):
    return sum(((v >> (8 * c + j)) & 1) << c for c in range(4))


def pdesc(v):
    return " ".join("%d:%s" % (j, PN[pnib(v, j)]) for j in range(8) if pnib(v, j)) or "0"


def cross_triangles(wins):
    edges = set()
    for w in wins:
        for a, b in combinations(sorted(w), 2):
            edges.add((a, b))
    out = []
    for t in combinations(range(8), 3):
        if all(e in edges for e in combinations(t, 2)) and not any(set(t) <= w for w in wins):
            out.append(t)
    return out


def main():
    print("primal cross-window triangles:", cross_triangles(mc.SHEET_SUPPORT))
    print("mirror cross-window triangles:", cross_triangles(WIN))
    if len(sys.argv) < 3:
        return
    fn, want = sys.argv[1], int(sys.argv[2])
    nl = 0
    gates = None
    for f in ("circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"):
        for line in open(os.path.join(KSTE, f)):
            if not line.strip():
                continue
            nl += 1
            if nl == want:
                gates = mc.parse_pairs(line)
                assert f == fn
                break
        if gates:
            break
    for k in range(8):
        vals, st, labels, exits = primal_split(gates, k)
        anc = serves(gates, vals)
        for gi, a, b in exits:
            print("primal exit at block %d: g%d = [%s] + [%s] = [%s]; serves %s; a serves %s, b serves %s" % (
                k, 32 + gi, pdesc(vals[a]), pdesc(vals[b]), pdesc(vals[32 + gi]), sorted(anc.get(32 + gi, ())),
                sorted(anc.get(a, ())), sorted(anc.get(b, ()))))
    tot, red, _ = mirror(gates, "fwd")
    for S in ([1], [0, 1], [0, 1, 7], [7], [3], [4], [0]):
        st, labels, exits, _ = split(red, S)
        for idx, g in exits:
            print("mirror exit across %s: [%s] + [%s] = [%s], from primal node %s" % (
                S, mdesc(g["a"]), mdesc(g["b"]), mdesc(g["v"]), g["prim"]))


if __name__ == "__main__":
    main()
