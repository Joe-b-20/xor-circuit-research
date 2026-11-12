"""CHECK (Prop 2 sketch, block 7): random linear automorphisms A of the far space fixing W_7 pointwise;
count distinct non-unit values among A(far units) and R_far.  >= 31 would give phi(A units) > 30 >= L(R_far)."""
import random
from mycheck import rows
K = 7
bk = sum(1 << (8 * c + K) for c in range(4))
R = rows()
W = [r & ~bk for r in R if r & bk]
Rfar = [r for r in R if not r & bk]
far_units = [1 << i for i in range(32) if not (1 << i) & bk]

def basis(vs):
    b = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in b: v ^= b[h]
            else: b[h] = v; break
    return b

bw = basis(W)
print("dim W", len(bw))
# complement: far units not in span, greedy
comp, cur = [], dict(bw)
for u in far_units:
    v = u
    while v:
        h = v.bit_length() - 1
        if h in cur: v ^= cur[h]
        else: cur[h] = v; comp.append(u); break
print("complement size", len(comp))
Wb = list(bw.values())
def expr(u):  # write u in basis Wb + comp; return (w-part vector, comp coefficient list)
    # solve by brute elimination over basis of Wb+comp
    vecs = Wb + comp
    n = len(vecs)
    rowsv = [(vecs[i], 1 << i) for i in range(n)]
    piv = {}
    for v, tag in rowsv:
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h][0]; tag ^= piv[h][1]
            else: piv[h] = (v, tag); break
    v, tag = u, 0
    while v:
        h = v.bit_length() - 1
        v ^= piv[h][0]; tag ^= piv[h][1]
    return tag
best = 0
random.seed(1)
nW = len(Wb)
tags = {u: expr(u) for u in far_units}
for trial in range(2000):
    # A fixes Wb, sends comp[j] -> comp[j] + random element of span(Wb + comp) keeping invertibility
    img = []
    for j in range(len(comp)):
        x = comp[j]
        for i in range(nW):
            if random.random() < 0.5: x ^= Wb[i]
        img.append(x)
    if len(basis(Wb + img)) != 28: continue
    def A(u):
        t, x = tags[u], 0
        for i in range(nW):
            if t >> i & 1: x ^= Wb[i]
        for j in range(len(comp)):
            if t >> (nW + j) & 1: x ^= img[j]
        return x
    vals = {A(u) for u in far_units} | set(Rfar)
    nonunit = len([x for x in vals if bin(x).count("1") > 1])
    best = max(best, nonunit)
print("max distinct non-unit values in A(units) + R_far:", best)
