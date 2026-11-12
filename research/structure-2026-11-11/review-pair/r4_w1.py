"""Review item 3: Proposition 4.1's first sentence ('in a (W1) circuit a gate has mu = 2 only if ... it reaches
sheet j through a backward exit').  Builds ONE explicit (W1) circuit for Q_4 from q4_40.txt by splicing a
forward wrap-around route (no search) and checks it.  Definitions as in RECORD section 7 (output gate = any
gate whose mask is a row; ancestor = along the wires)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rlib as R  # noqa: E402

m = 4
Q = R.qm_model(m)
n, gates = R.read_qm(os.path.join(R.QDIR, "q4_40.txt"))
win = [frozenset({(j - 1) % m, j}) for j in range(m)]


def analyse(gates, label):
    vals = R.values(n, gates)
    assert R.computes(Q, n, gates)
    sup = [R.support(Q, v) for v in vals]
    w1 = [i for i, (a, b) in enumerate(gates) if not any((sup[a] | sup[b]) <= w for w in win)]
    rowsheet = {}
    for (c, j), v in Q["rows"].items():
        rowsheet.setdefault(v, set()).add(j)
    anc = [set() for _ in range(m)]
    for i in range(n, len(vals)):
        for j in rowsheet.get(vals[i], ()):
            st = [i]
            while st:
                s = st.pop()
                if s < n or s in anc[j]:
                    continue
                anc[j].add(s)
                st.extend(gates[s - n])
    mu = {i: [j for j in range(m) if j in sup[i] and i in anc[j]] for i in range(n, len(vals))}
    D = [sum(1 for i in mu if j in mu[i]) for j in range(m)]
    over = sum(d - 10 for d in D)
    unch = sum(1 for i in mu if not mu[i])
    exc = sum(max(0, len(mu[i]) - 1) for i in mu)
    # backward exits of Proposition 4.1
    bexits = []
    for i in range(n, len(vals)):
        a, b = gates[i - n]
        for j in range(m):
            k = (j + 1) % m
            if sup[i] == frozenset({j}) and sup[a] <= {j, k} and sup[b] <= {j, k} and R.nib(Q, vals[a], k) \
                    and R.nib(Q, vals[a], k) == R.nib(Q, vals[b], k) and i in anc[j]:
                bexits.append((i, j))
    print("%s: G = %d, (W1) violations %d, |D_j| = %s, over %d, unch %d, excess %d, G = 10m+over+unch-excess: %s"
          % (label, len(gates), len(w1), D, over, unch, exc, len(gates) == 10 * m + over + unch - exc))
    print("   gates with mu >= 2:", {i: mu[i] for i in mu if len(mu[i]) >= 2})
    print("   backward exits (h, j) serving sheet j:", bexits)
    return vals, sup, anc, mu, bexits


vals, sup, anc, mu, _ = analyse(gates, "q4_40")
B = [sum(1 << Q["idx"](c, j) for c in range(4)) for j in range(m)]
g = next(i for i in range(n, len(vals)) if sup[i] == frozenset({0, 1}) and i in anc[1])
readers = {}
for i, (a, b) in enumerate(gates):
    readers.setdefault(a, []).append(n + i)
    readers.setdefault(b, []).append(n + i)
rowmask0 = {Q["rows"][(c, 0)] for c in range(4)}
o = next(i for i in range(n, len(vals)) if vals[i] in rowmask0 and i not in readers)
x, y = gates[o - n]
assert sup[y] <= {3, 0} and sup[x] <= {3, 0}
print("chosen g = signal %d on blocks %s; chosen sheet-0 output o = signal %d = %d + %d" % (g, sorted(sup[g]), o, x, y))

# new gate list: drop o (it has no readers), shift later indices
newg = []
for i, (a, b) in enumerate(gates):
    if n + i == o:
        continue
    newg.append(tuple(s - 1 if s > o else s for s in (a, b)))
remap = lambda s: s - 1 if s > o else s  # noqa: E731
nv = R.values(n, newg)


def add(a, b):
    newg.append((a, b))
    nv.append(nv[a] ^ nv[b])
    return n + len(newg) - 1


def build(mask):
    units = [i for i in range(n) if (mask >> i) & 1]
    units.sort(key=lambda i: (i // 4, i % 4))
    acc = units[0]
    for u in units[1:]:
        acc = add(acc, u)
    return acc


G = remap(g)
p = build(nv[G] & B[0])
g1 = add(G, p)                                   # block 1 only (forward exit of block 0)
R2 = 1 << Q["idx"](0, 2)
p2 = build((nv[g1] & B[1]) | R2)
g2 = add(g1, p2)                                 # block 2 only
R3 = 1 << Q["idx"](0, 3)
p3 = build(R2 | R3)
g3 = add(g2, p3)                                 # block 3 only
y2 = add(remap(y), Q["idx"](0, 3))               # y + unit (0,3), on {3,0}
z = add(y2, g3)                                  # equals y
add(remap(x), z)                                 # equals o: new output gate of sheet 0
print("route values: g1 %s, g2 %s, g3 %s" % tuple(sorted(R.support(Q, nv[s])) for s in (g1, g2, g3)))
vals2, sup2, anc2, mu2, bex2 = analyse(newg, "modified")
print("   mu(g) in the modified circuit:", mu2[G])
desc = set()
st = [G]
rd2 = {}
for i, (a, b) in enumerate(newg):
    rd2.setdefault(a, []).append(n + i)
    rd2.setdefault(b, []).append(n + i)
while st:
    s = st.pop()
    for r in rd2.get(s, []):
        if r not in desc:
            desc.add(r)
            st.append(r)
print("   backward exits onto block 0 that are descendants of g:", [h for h, j in bex2 if j == 0 and h in desc])
