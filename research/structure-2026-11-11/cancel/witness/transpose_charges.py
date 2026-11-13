"""CHECK (phase 9, main agent): charged families of a circuit and of its transpose.

Transposition (for a fully live circuit C of a 32 x 32 map M): each node v of C becomes a node of C^T whose value
is the XOR of the transposed values of v's readers, plus a fresh input if v is an output of C; a node with d
terms costs d - 1 two-input gates (chained in reader order). C^T computes M^T, and G(C^T) = G(C) when no output
of C is read by another gate (otherwise G(C^T) = G(C) - #(outputs of C that are read)).
M^T as a sheet system: its input blocks are the output bit positions of M; its row for the input x_(k,b) of M has
E on block b and s parts on block b+1 (and, for b = 7, on blocks 1, 3, 4); sheet b = the four rows x_(k,b).
Charges: F_b = ancestors (in C^T) of sheet-b rows nonzero on block b; reports |F_b|, the distinct union, E, R.
Inputs: the witness JSON from build_witness.py, recorded circuits, kste lines. Direct evaluation; no search.
usage: python3 transpose_charges.py SPEC [SPEC ...]
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_witness import mc_rows  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "..", "joint"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "compose", "compat"))

ROWS = mc_rows()
RK = sorted(ROWS)          # output (c, j): C^T input index 8c + j (unit c of block j)


def load(spec):
    if spec.endswith(".json"):
        return [tuple(x) for x in json.load(open(spec))]
    from jstats import get
    return get(spec)


def charges(n, gates, rows, bmask, nsheets):
    vals = [1 << w for w in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    idx = {}
    for i, v in enumerate(vals):
        idx.setdefault(v, i)
    F = {}
    for s in range(nsheets):
        st, A = [idx[rows[(k, s)]] for k in range(4)], set()
        while st:
            x = st.pop()
            if x < n or x in A:
                continue
            A.add(x)
            st.extend(gates[x - n])
        F[s] = {x for x in A if vals[x] & bmask(s)}
    mult = Counter(x for s in F for x in F[s])
    return len(mult), sum(len(F[s]) - 10 for s in F), sum(v - 1 for v in mult.values() if v > 1), [len(F[s]) for s in F]


def transpose(gates):
    n = 32
    N = n + len(gates)
    vals = [1 << w for w in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    out_node = {}
    for i, key in enumerate(RK):
        out_node[vals.index(ROWS[key], n)] = 8 * key[0] + key[1]
    readers = [[] for _ in range(N)]
    for gi, (a, b) in enumerate(gates):
        readers[a].append(n + gi)
        readers[b].append(n + gi)
    tg = []          # gates of C^T over 32 inputs
    tval = {}        # node of C -> signal index in C^T
    for v in range(N - 1, -1, -1):
        terms = ([out_node[v]] if v in out_node else []) + [tval[w] for w in readers[v]]
        assert terms, "node with no readers that is not an output: circuit not live"
        acc = terms[0]
        for t in terms[1:]:
            tg.append((acc, t))
            acc = 32 + len(tg) - 1
        tval[v] = acc
    # rows of M^T: transposed values of the inputs of C
    tv = [1 << w for w in range(32)]
    for a, b in tg:
        tv.append(tv[a] ^ tv[b])
    rowsT = {}
    for w in range(32):
        k, b = w // 8, w % 8
        rowsT[(k, b)] = tv[tval[w]]
    # check: row (k, b) of M^T has bit (8c + j) set iff x_(k,b) occurs in output (c, j)
    for w in range(32):
        expect = sum(1 << (8 * c + j) for (c, j) in RK if ROWS[(c, j)] >> w & 1)
        assert rowsT[(w // 8, w % 8)] == expect
    return tg, rowsT


def main():
    bm = lambda j: sum(1 << (8 * c + j) for c in range(4))
    for spec in sys.argv[1:]:
        g = load(spec)
        u, E, R, Fs = charges(32, g, ROWS, bm, 8)
        tg, rowsT = transpose(g)
        uT, ET, RT, FT = charges(32, tg, rowsT, bm, 8)
        print("%s: G=%d |union F|=%d (E %d, R %d)  |  G(C^T)=%d |union F^T|=%d (E %d, R %d) F^T sizes %s" % (
            os.path.basename(spec), len(g), u, E, R, len(tg), uT, ET, RT, FT))


if __name__ == "__main__":
    main()
