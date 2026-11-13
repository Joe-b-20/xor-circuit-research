"""CHECK (phase 9, main agent): the superposition construction applied to M^T, then transposed.

S = the global-parity construction of build_witness.py for the map M^T (rows of M^T in the same wire indexing:
row (k, b) has bit 8c + j set iff x_(k,b) occurs in output (c, j) of M). C' = S^T computes M. Reports the
charged families of S (as a circuit for M^T, sheets = blocks b, own block b) and of C' (as a circuit for M).
Explicit construction and direct evaluation only; no search.
usage: python3 dual_test.py
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_witness import build, mc_rows, stats  # noqa: E402


def transpose(gates, rows, n=32):
    vals = [1 << w for w in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    N = len(vals)
    keys = sorted(rows)
    out_node = {vals.index(rows[k], n): 8 * k[0] + k[1] for k in keys}
    readers = [[] for _ in range(N)]
    for gi, (a, b) in enumerate(gates):
        readers[a].append(n + gi)
        readers[b].append(n + gi)
    tg, tval = [], {}
    for v in range(N - 1, -1, -1):
        terms = ([out_node[v]] if v in out_node else []) + [tval[w] for w in readers[v]]
        assert terms
        acc = terms[0]
        for t in terms[1:]:
            tg.append((acc, t))
            acc = n + len(tg) - 1
        tval[v] = acc
    return tg


def main():
    M = mc_rows()
    MT = {}
    for w in range(32):
        MT[(w // 8, w % 8)] = sum(1 << (8 * c + j) for (c, j) in M if M[(c, j)] >> w & 1)
    bm = lambda j: sum(1 << (8 * c + j) for c in range(4))
    S = build(32, lambda w: w // 8, lambda w: w % 8, MT, 8, lambda w: w)
    print("S (for M^T):", stats(32, S, MT, bm, 8))
    C = transpose(S, MT)
    print("C' = S^T (for M):", stats(32, C, M, bm, 8))


if __name__ == "__main__":
    main()
