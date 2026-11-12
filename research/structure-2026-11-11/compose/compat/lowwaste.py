"""CHECK (explicit construction): a MixColumns circuit with low waste at block K (5 or 6 in the runs made; the docstring formerly said "exactly 4", which is false).
P: far rows and y_r = s(r) + sum of lambda_c over c in omega(r), each built from far units by a chain
(values already present are reused). L: g_c = u_c + lambda_c (lambda_c = far unit of byte c, bit LAM),
omega signals from the g_c (8 gates), rows = omega signal + y_r (entries)."""
import sys
from clib import ROWS, bm, check, cut
from corpus import wst
K = int(sys.argv[1]); LAM = (K + 3) % 8
low = bm(K)
idx = {1 << i: i for i in range(32)}
gates = []
def add(a, b):
    v = a ^ b
    if v in idx: return v
    gates.append((idx[a], idx[b])); idx[v] = 31 + len(gates); return v
def chain(v):
    if v in idx: return v
    bits = [1 << i for i in range(32) if v >> i & 1]
    acc = bits[0]
    for x in bits[1:]: acc = add(acc, x)
    return acc
lam = [1 << (8 * c + LAM) for c in range(4)]
u = [1 << (8 * c + K) for c in range(4)]
near = [r for r in ROWS.values() if r & low]
far = [r for r in ROWS.values() if not r & low]
def om(r): return [c for c in range(4) if r >> (8 * c + K) & 1]
for r in far: chain(r)
Y = {}
for r in near:
    y = (r & ~low)
    for c in om(r): y ^= lam[c]
    Y[r] = chain(y)
g = [add(u[c], lam[c]) for c in range(4)]
sig = {}
for c in range(4): sig[(c, (c + 1) % 4)] = add(g[c], g[(c + 1) % 4])
for c in range(4):
    a = sig[((c + 1) % 4, (c + 2) % 4)]; add(a, g[(c + 3) % 4])
for r in near:
    w = r & low; base = w
    ws = [x for x in idx if x & low == w and x & ~low == sum(lam[c] for c in om(r))]
    add(ws[0], Y[r])
vals = [1 << i for i in range(32)]
for a, b in gates: vals.append(vals[a] ^ vals[b])
print("K=%d n=%d computes,reduced=%s waste=%d" % (K, len(gates), check(gates), wst(gates, vals, K)))
