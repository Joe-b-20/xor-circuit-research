"""d1_facts.py -- finite facts about the MixColumns map and the recorded 89@4 circuit, for the
depth-4 lower-bound report.  Read-only on the repo.  Output: d1_facts.out (stdout) + d1_facts.json.

Facts computed:
  F1  output weights; pairwise |o1+o2| distribution (which output pairs differ by a mask of weight <=4,
      i.e. could be "level-3 output + level-<=2 value" at level 4 without any level-3 helper).
  F2  census of the repo 89@4: level of every gate, parity type (OO/OE/EE), weight, helper/output;
      the identity G = 32 + p + h2 + h3 and the split h3 = b + e3 + o3.
  F3  depth-3 final-parent decompositions of each output (parents of weight <=4): 285 / 35 as in the
      depth-3 proof; the parent "capacity": how many distinct outputs a given triple / quartet mask can
      be a last-gate parent of at level 3.
  F4  depth-4 last-gate splits per output if the two parents may be ANY masks of weight <= 8
      (support bound of a level-3 signal): the size of the unrestricted depth-4 recipe space.
  F5  with the 89's first layer P (26 pairs) fixed: sizes of U2 (triples/quartets over P), of the
      level-3 universe S = (U2 + V2) \\ V2, and of the per-output level-4 recipe lists (the instance
      sizes of the scoped exact problems in d2).
"""
import json, os, re, sys, itertools, collections, time
REPO = os.path.expanduser("~/xor-circuit-research")
MAT = os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")
C89 = os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns-xor89-depth4.circ.txt")
HERE = os.path.dirname(os.path.abspath(__file__))
N = 32
INPUTS = [1 << j for j in range(N)]
pc = lambda v: bin(v).count("1")
OUT = {}

def load_targets():
    toks = " ".join(l.split("%")[0] for l in open(MAT).read().splitlines()).split()
    r, c = int(toks[1]), int(toks[2])
    bits = list(map(int, toks[3:3 + r * c]))
    return [sum(bits[i * c + j] << j for j in range(c)) for i in range(r)]

T = load_targets()
TSET = set(T)
assert len(TSET) == 32
W = [pc(t) for t in T]
print("F1 output weights:", collections.Counter(W))
OUT["weights"] = W

# F1 pairwise sums
pair_w = collections.Counter()
le4 = []
for i in range(32):
    for j in range(i + 1, 32):
        w = pc(T[i] ^ T[j])
        pair_w[w] += 1
        if w <= 4:
            le4.append((i, j, w))
print("F1 pairwise |o_i + o_j| histogram:", sorted(pair_w.items()))
print("F1 output pairs with |o_i+o_j| <= 4:", le4)
OUT["pair_sum_hist"] = sorted(pair_w.items()); OUT["pairs_le4"] = le4
# triple sums (two outputs + V2 element = output?): o_i + o_j + o_k weight
tri_le4 = 0
for i, j, k in itertools.combinations(range(32), 3):
    if pc(T[i] ^ T[j] ^ T[k]) <= 4:
        tri_le4 += 1
print("F1 output triples with |o_i+o_j+o_k| <= 4:", tri_le4)

# F2 census of the 89
vals = {f"x{j}": 1 << j for j in range(N)}
lev = {f"x{j}": 0 for j in range(N)}
gates = []
for line in open(C89):
    m = re.match(r"^XOR\s+(\S+)\s+(\S+)\s+(\S+)", line.strip())
    if not m:
        continue
    o, a, b = m.groups()
    vals[o] = vals[a] ^ vals[b]
    lev[o] = 1 + max(lev[a], lev[b])
    gates.append((o, a, b))
assert len(gates) == 89
depth_of_mask = {}
for o, a, b in gates:
    depth_of_mask[vals[o]] = lev[o]
assert all(t in depth_of_mask for t in T)
assert all(len(set(vals.values())) == len(vals) for _ in [0])
cen = collections.Counter()
rows = []
for o, a, b in gates:
    v = vals[o]; L = lev[o]; w = pc(v)
    pa, pb = pc(vals[a]) & 1, pc(vals[b]) & 1
    typ = {2: "OO", 1: "OE", 0: "EE"}[pa + pb]
    kind = "out" if v in TSET else "helper"
    cen[(L, kind, typ, w)] += 1
    rows.append((o, L, kind, typ, w, a, b))
print("F2 census of repo 89@4 (level, kind, parity-type, weight): count")
for k in sorted(cen):
    print("   ", k, cen[k])
p = sum(c for (L, k, t, w), c in cen.items() if L == 1)
h2 = sum(c for (L, k, t, w), c in cen.items() if L == 2 and k == "helper")
h3 = sum(c for (L, k, t, w), c in cen.items() if L == 3 and k == "helper")
b = sum(c for (L, k, t, w), c in cen.items() if L == 3 and k == "helper" and t == "OO")
e3 = sum(c for (L, k, t, w), c in cen.items() if L == 3 and k == "helper" and t == "EE")
o3 = sum(c for (L, k, t, w), c in cen.items() if L == 3 and k == "helper" and t == "OE")
y3 = sum(c for (L, k, t, w), c in cen.items() if L == 3 and k == "out")
y4 = sum(c for (L, k, t, w), c in cen.items() if L == 4 and k == "out")
x_oo = sum(c for (L, k, t, w), c in cen.items() if t == "OO")
y_ee = sum(c for (L, k, t, w), c in cen.items() if t == "EE")
h_odd = sum(c for (L, k, t, w), c in cen.items() if t == "OE" and k == "helper")
print(f"F2 p={p} h2={h2} h3={h3} (b={b} e3={e3} o3={o3}) y3={y3} y4={y4}; 32+p+h2+h3={32+p+h2+h3}")
print(f"F2 lb75 accounting: x(OO)={x_oo} y(EE)={y_ee} h(odd helpers)={h_odd}; 32+x+y+h={32+x_oo+y_ee+h_odd}")
# level-4 outputs: parents
reuse = 0; two_l3 = 0; one_l3 = 0
l3helper_users = collections.Counter()
for o, a, b_ in gates:
    if lev[o] == 4:
        la, lb = lev[a], lev[b_]
        pa_out = vals[a] in TSET; pb_out = vals[b_] in TSET
        if pa_out or pb_out:
            reuse += 1
        if la == 3 and lb == 3:
            two_l3 += 1
        else:
            one_l3 += 1
        for z in (a, b_):
            if lev[z] == 3 and vals[z] not in TSET:
                l3helper_users[z] += 1
print(f"F2 level-4 outputs: {y4}; with two level-3 parents {two_l3}, with one {one_l3}; using a level-3 OUTPUT as parent (reuse): {reuse}")
print("F2 level-3 helper fan-out into level-4 outputs:", sorted(l3helper_users.values()))
P89 = sorted(vals[o] for o, a, b_ in gates if lev[o] == 1)
L2_89 = sorted(vals[o] for o, a, b_ in gates if lev[o] == 2)
L3h_89 = sorted(vals[o] for o, a, b_ in gates if lev[o] == 3 and vals[o] not in TSET)
OUT["P89"] = P89; OUT["L2_89"] = L2_89; OUT["L3h_89"] = L3h_89
OUT["census89"] = {str(k): v for k, v in cen.items()}

# F3 depth-3 final-parent decompositions and capacities
def submasks(mask, k):
    bits = [i for i in range(N) if mask >> i & 1]
    for comb in itertools.combinations(bits, k):
        yield sum(1 << i for i in comb)
FULL = (1 << N) - 1
decomp = {}          # output index -> list of (a,b) with a<b, |a|,|b|<=4, a^b=o
parent_outputs = collections.defaultdict(set)
for i, o in enumerate(T):
    L = set()
    # enumerate a with |a|<=4 and |a^o|<=4: a = (a∩o) ∪ (a\o), |a∩o|=u, |a\o|=v, u+v<=4, (|o|-u)+v<=4
    for u in range(0, 5):
        for v in range(0, 5):
            if u + v > 4 or (W[i] - u) + v > 4 or u > W[i]:
                continue
            for ain in submasks(o, u):
                for aout in submasks(FULL ^ o, v):
                    a = ain | aout
                    bm = a ^ o
                    if a == 0 or bm == 0:
                        continue
                    if a < bm:
                        L.add((a, bm))
    decomp[i] = sorted(L)
    for a, bm in L:
        for par in (a, bm):
            if pc(par) >= 2:
                parent_outputs[par].add(i)
cnt5 = [len(decomp[i]) for i in range(32) if W[i] == 5]
cnt7 = [len(decomp[i]) for i in range(32) if W[i] == 7]
print("F3 depth-3 decompositions per output: weight5", set(cnt5), "weight7", set(cnt7), "total", sum(len(v) for v in decomp.values()))
cap = collections.Counter()
cap_by_w = collections.defaultdict(collections.Counter)
for par, outs in parent_outputs.items():
    cap[len(outs)] += 1
    cap_by_w[pc(par)][len(outs)] += 1
print("F3 parent-mask capacity (number of distinct outputs a weight>=2 mask can be a level-3 last-gate parent of): hist", sorted(cap.items()))
for w in sorted(cap_by_w):
    print(f"    weight-{w} parents:", sorted(cap_by_w[w].items()))
OUT["cap_hist"] = sorted(cap.items())
# capacity restricted to the two output weight classes
cap5 = collections.Counter(); cap7 = collections.Counter()
for par, outs in parent_outputs.items():
    n5 = sum(1 for i in outs if W[i] == 5); n7 = sum(1 for i in outs if W[i] == 7)
    cap5[n5] += 1; cap7[n7] += 1
print("F3 capacity towards weight-5 outputs:", sorted(cap5.items()), " towards weight-7 outputs:", sorted(cap7.items()))

# F4 depth-4 unrestricted last-gate splits (both parents weight <= 8)
def count_splits(o, cap_w):
    w = pc(o); tot = 0
    from math import comb
    for u in range(0, w + 1):
        for v in range(0, 33):
            if u + v <= cap_w and (w - u) + v <= cap_w:
                tot += comb(w, u) * comb(32 - w, v)
    return tot // 2     # unordered {a, o+a}; a=0 or a=o included (parent weight 0 impossible in a normalized circuit; negligible)
print("F4 depth-4 last-gate splits per output with parents of weight <=8 (unordered): weight5 =", count_splits(T[W.index(5)], 8), " weight7 =", count_splits(T[W.index(7)], 8))
print("F4 same count with parents of weight <=4 (depth 3):", count_splits(T[W.index(5)], 4), count_splits(T[W.index(7)], 4))

# F5 sizes with the 89's first layer fixed
t0 = time.time()
Pset = set(P89)
U2 = set()
for pr in P89:
    for x in INPUTS:
        if not (pr & x):
            U2.add(pr | x)
for a_, b_ in itertools.combinations(P89, 2):
    if not (a_ & b_):
        U2.add(a_ | b_)
V2 = set(INPUTS) | Pset | U2
print(f"F5 with P89 fixed: |U2| = {len(U2)} (triples {sum(1 for u in U2 if pc(u)==3)}, quartets {sum(1 for u in U2 if pc(u)==4)}), |V2| = {len(V2)}")
U2l = sorted(U2); V2l = sorted(V2)
S = set()
for u in U2l:
    for v in V2l:
        s = u ^ v
        if s and s not in V2:
            S.add(s)
print(f"F5 level-3 universe |S| = (U2 + V2) \\ V2 = {len(S)}  ({time.time()-t0:.1f}s); outputs in S (level-3-realizable over P89 with ANY level-2 choice): {sum(1 for t in T if t in S)}")
Sx = S | V2
rec = []
for i, o in enumerate(T):
    n = 0
    for s in S:
        t_ = o ^ s
        if t_ in Sx and s < t_:
            n += 1
    rec.append(n)
print("F5 per-output level-4 recipe count {s,t}, s in S, t in S u V2:", rec, " total", sum(rec))
# how many level-2 values of the 89 are in U2 (sanity: all)
assert all(u in U2 for u in L2_89), "a level-2 value of the 89 is not a triple/quartet over its pairs?"
# number of known-89 level-3 helpers in S
assert all(s in S for s in L3h_89)
OUT["U2_size"] = len(U2); OUT["S_size"] = len(S); OUT["recipes_l4"] = rec
json.dump(OUT, open(os.path.join(HERE, "d1_facts.json"), "w"))
print("done", f"{time.time()-t0:.1f}s")
