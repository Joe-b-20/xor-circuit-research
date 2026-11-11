"""Vertices of the dual of the two-point LP (classes N_11, N_10, N_01, N_00; constraints L1 L2 L3 D1 D2 D3).

Dual: maximise sum y_k b_k subject to, for each class, the sum of y_k over the constraints containing
that class <= 1, y >= 0. The LP optimum is the largest vertex value. Printed: each vertex.
"""
import itertools
from fractions import Fraction as F

# constraint -> classes it contains (sigma = (live at x1, live at x2))
C = {"L1": [(1, 1), (1, 0)], "L2": [(1, 1), (0, 1)], "L3": [(1, 0), (0, 1)],
     "D1": [(0, 1), (0, 0)], "D2": [(1, 0), (0, 0)], "D3": [(1, 1), (0, 0)]}
K = list(C)
classes = [(1, 1), (1, 0), (0, 1), (0, 0)]
# inequality rows a.y <= rhs : 4 class rows and 6 nonnegativity rows (-y <= 0)
rows = [([1 if s in C[k] else 0 for k in K], 1) for s in classes] + \
       [([-1 if i == j else 0 for j in range(6)], 0) for i in range(6)]


def solve(A, b):
    n = len(A)
    M = [[F(v) for v in A[i]] + [F(b[i])] for i in range(n)]
    for c in range(n):
        p = next((r for r in range(c, n) if M[r][c] != 0), None)
        if p is None:
            return None
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c and M[r][c] != 0:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * bb for a, bb in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


verts = set()
for sub in itertools.combinations(range(len(rows)), 6):
    y = solve([rows[i][0] for i in sub], [rows[i][1] for i in sub])
    if y is None:
        continue
    if all(sum(a * v for a, v in zip(r, y)) <= rhs for r, rhs in rows):
        verts.add(tuple(y))
for y in sorted(verts):
    print(" + ".join(f"{v}*{k}" for v, k in zip(y, K) if v) or "0")
