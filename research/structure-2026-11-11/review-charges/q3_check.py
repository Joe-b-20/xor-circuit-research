"""Verify rotation/circuits/q3_28.txt computes Q_3 and count block-monotonicity violations and
charges, from the definitions (own code; only qm.rows / qm.read_circuit used for the target and
file format).  Also prints the structure of the violating gates."""
import os
import sys
sys.path.insert(0, os.path.expanduser("~/xor-circuit-research/research/structure-2026-11-11/rotation"))
import qm

m = int(sys.argv[2]) if len(sys.argv) > 2 else 3
path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/xor-circuit-research/research/structure-2026-11-11/rotation/circuits/q3_28.txt")
n, gates = qm.read_circuit(path)
assert n == 4 * m
rows = qm.rows(m)
# own target construction for cross-check
own = []
for j in range(m):
    for c in range(4):
        E = sum(1 << (4 * j + (c + k) % 4) for k in (1, 2, 3))
        s = (1 << (4 * ((j - 1) % m) + c % 4)) | (1 << (4 * ((j - 1) % m) + (c + 1) % 4))
        own.append(E | s)
assert own == rows
v = [1 << i for i in range(n)]
for a, b in gates:
    v.append(v[a] ^ v[b])
G = len(gates)
print("G =", G, "computes Q_%d:" % m, set(rows) <= set(v), " distinct masks:", len(set(v)) == len(v))
BM = [0xF << (4 * j) for j in range(m)]


def blocks(x):
    return frozenset(j for j in range(m) if x & BM[j])


anc = [frozenset() for _ in range(n)]
for k, (a, b) in enumerate(gates):
    anc.append(anc[a] | anc[b] | {n + k})
rowidx = {r: i for i, r in enumerate(rows)}
outg = {j: [s for s in range(n, n + G) if v[s] in rowidx and rowidx[v[s]] // 4 == j] for j in range(m)}
D = {}
for j in range(m):
    A = set()
    for s in outg[j]:
        A |= anc[s]
    D[j] = {s for s in A if v[s] & BM[j]}
mu = {s: sum(s in D[j] for j in range(m)) for s in range(n, n + G)}
viol = set()
for j in range(m):
    for o in outg[j]:
        for g in anc[o]:
            if not blocks(v[g]) <= blocks(v[o]):
                viol.add(g)
print("D_j sizes", [len(D[j]) for j in range(m)], "sum mu", sum(mu.values()),
      "excess", sum(max(0, x - 1) for x in mu.values()), "mu=0:", sum(1 for x in mu.values() if x == 0))
print("block-monotone violators:", len(viol))
for k in range(G):
    s = n + k
    print("g%-2d = %2d + %2d  blocks %s  mu %d %s" % (k, gates[k][0], gates[k][1], sorted(blocks(v[s])), mu[s],
          "VIOL" if s in viol else ""))
