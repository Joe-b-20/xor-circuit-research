"""d4_post.py -- small exact facts used in REPORT.md sections 3-5.
  (a) Z4 byte rotation maps the target set to itself (transport of scoped facts to rotated layers).
  (b) which outputs are never level-3-realizable over the 89's first layer P89 (not u ^ v with u a
      triple/quartet over P89 and v an input/pair/triple/quartet over P89).
  (c) exact minimum number of level-2 masks (triples/quartets, any pairs) that can serve as last-gate
      parents for a set Y3 of outputs placed at level 3, ignoring pair cost ("parent cover"), for
      Y3 = all 32, Y3 = the 20 weight-5 outputs, Y3 = the 12 weight-7 outputs. CP-SAT, exact.
  (d) the 20 output pairs with |o+o'| = 4: their structure (bit position, byte offsets).
"""
import json, os, itertools, collections, time
HERE = os.path.dirname(os.path.abspath(__file__))
N = 32; INPUTS = [1 << j for j in range(N)]; FULL = (1 << N) - 1
pc = lambda v: bin(v).count("1")
F = json.load(open(os.path.join(HERE, "d1_facts.json")))
REPO = os.path.expanduser("~/xor-circuit-research")
MAT = os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")
toks = " ".join(l.split("%")[0] for l in open(MAT).read().splitlines()).split()
r, c = int(toks[1]), int(toks[2]); bits = list(map(int, toks[3:3 + r * c]))
T = [sum(bits[i * c + j] << j for j in range(c)) for i in range(r)]; TSET = set(T); W = [pc(t) for t in T]

def rot(v, s):
    s = (s * 8) % 32
    return ((v << s) | (v >> (32 - s))) & FULL
# (a)
for s in range(4):
    assert set(rot(t, s) for t in T) == TSET, "target set not rotation invariant"
print("(a) Z4 byte rotation maps the 32 target masks onto themselves: checked for all 4 rotations")
# (b)
P = F["P89"]; Pset = set(P)
U2 = set()
for pr in P:
    for x in INPUTS:
        if not (pr & x): U2.add(pr | x)
for a, b in itertools.combinations(P, 2):
    if not (a & b): U2.add(a | b)
V2 = set(INPUTS) | Pset | U2
real = set()
for u in U2:
    for v in V2:
        if u != v: real.add(u ^ v)
never = [i for i, t in enumerate(T) if t not in real]
print("(b) outputs never level-3-realizable over P89 (index, weight):", [(i, W[i]) for i in never])
# (d)
le4 = F["pairs_le4"]
print("(d) |o_i+o_j| = 4 pairs by bit position:", sorted(collections.Counter(i % 8 for i, j, w in le4).items()),
      " byte offsets:", sorted(collections.Counter(((j - i) // 8) % 4 for i, j, w in le4).items()))
# (c) parent cover
def submasks(mask, k):
    bb = [i for i in range(N) if mask >> i & 1]
    for comb in itertools.combinations(bb, k):
        yield sum(1 << i for i in comb)
decomp = {}
for i, o in enumerate(T):
    L = set()
    for u in range(0, 5):
        for v in range(0, 5):
            if u + v > 4 or (W[i] - u) + v > 4 or u > W[i]: continue
            for ain in submasks(o, u):
                for aout in submasks(FULL ^ o, v):
                    a = ain | aout; bm = a ^ o
                    if a and bm and a < bm: L.add((a, bm))
    decomp[i] = sorted(L)
from ortools.sat.python import cp_model
def parent_cover(Y3, label):
    t0 = time.time()
    m = cp_model.CpModel()
    masks = sorted({par for i in Y3 for a, bm in decomp[i] for par in (a, bm) if pc(par) >= 3})
    z = {q: m.NewBoolVar("") for q in masks}
    for i in Y3:
        terms = []
        for a, bm in decomp[i]:
            need = [q for q in (a, bm) if pc(q) >= 3]
            assert need, "a level-3 output needs a level-2 parent"
            if len(need) == 1:
                terms.append(z[need[0]])
            else:
                d = m.NewBoolVar(""); m.AddImplication(d, z[need[0]]); m.AddImplication(d, z[need[1]]); terms.append(d)
        m.AddBoolOr(terms)
    m.Minimize(sum(z.values()))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = 120; sv.parameters.num_search_workers = 1; sv.parameters.linearization_level = 2
    st = sv.Solve(m)
    print(f"(c) parent cover {label}: |Y3|={len(Y3)} universe={len(masks)} status={sv.StatusName(st)} min level-2 parents = {sv.ObjectiveValue():.0f} (bound {sv.BestObjectiveBound():.0f}) {time.time()-t0:.1f}s")
    return sv.ObjectiveValue() if st == cp_model.OPTIMAL else None
res = {}
res["all32"] = parent_cover(list(range(32)), "all 32 outputs at level 3")
res["w5"] = parent_cover([i for i in range(32) if W[i] == 5], "the 20 weight-5 outputs at level 3")
res["w7"] = parent_cover([i for i in range(32) if W[i] == 7], "the 12 weight-7 outputs at level 3")
json.dump({"never_l3_over_P89": never, "parent_cover": res}, open(os.path.join(HERE, "d4_post.json"), "w"))
