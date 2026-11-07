"""d3_subset.py -- as d2_scoped.py scope C, but the pairs are SELECTABLE too (cost 1 each):
scope = normal-form depth-<=4 circuits whose set of weight-2 masks is a SUBSET of the given pair
set P (default: the 26 pairs of the repo 89@4).  Level-2 candidates: all triples/quartets over P;
each needs its constructing pair(s) present.  Minimise |L1| + |L2| + |H3|;  G >= 32 + optimum.
This is the robust form of the scoped statement: it is closed under dead-gate deletion.
Usage: python3 d3_subset.py <wall-limit-s> [pairs-json-list]
"""
import json, os, sys, time, itertools, collections
HERE = os.path.dirname(os.path.abspath(__file__))
N = 32
INPUTS = [1 << j for j in range(N)]
pc = lambda v: bin(v).count("1")
F = json.load(open(os.path.join(HERE, "d1_facts.json")))
REPO = os.path.expanduser("~/xor-circuit-research")
MAT = os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")

def load_targets():
    toks = " ".join(l.split("%")[0] for l in open(MAT).read().splitlines()).split()
    r, c = int(toks[1]), int(toks[2])
    bits = list(map(int, toks[3:3 + r * c]))
    return [sum(bits[i * c + j] << j for j in range(c)) for i in range(r)]

T = load_targets(); TSET = set(T)
limit = float(sys.argv[1]) if len(sys.argv) > 1 else 600.0
P = sorted(json.loads(sys.argv[2])) if len(sys.argv) > 2 else sorted(F["P89"])
tag = sys.argv[3] if len(sys.argv) > 3 else "P89"
assert all(pc(p) == 2 for p in P)
t0 = time.time()
Pset = set(P)
# level-2 candidates with their constructions over P
U2cons = collections.defaultdict(set)
for pr in P:
    for x in INPUTS:
        if not (pr & x):
            U2cons[pr | x].add((pr,))
for a, b in itertools.combinations(P, 2):
    if not (a & b):
        U2cons[a | b].add((a, b))
pool = sys.argv[4] if len(sys.argv) > 4 else "all"
if pool == "L0":      # restrict level-2 candidates to the 30 level-2 masks of the 81-state family (scope B pool)
    s7 = json.load(open(os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/q89/s7_structure.json")))
    keep = set(v for v in s7["const"] if pc(v) in (3, 4)) | set(v for sl in s7["slots"] for v in sl)
    U2cons = collections.defaultdict(set, {u: c for u, c in U2cons.items() if u in keep})
    assert len(U2cons) == 30, len(U2cons)
    tag = tag + "-L0pool"
U2cand = sorted(U2cons); U2set = set(U2cand)
base = set(INPUTS)
V2 = base | Pset | U2set
V2l = sorted(V2)
cons = collections.defaultdict(set)      # level-3 mask -> constructions (u, v) u in U2, v in V2
for u in U2cand:
    for v in V2l:
        if v == u:
            continue
        s = u ^ v
        if s == 0 or s in V2:
            continue
        if v in base:
            cons[s].add((u,))
        elif v in Pset:
            cons[s].add((u, v))
        else:
            cons[s].add((min(u, v), max(u, v)))
S = set(cons)
helpers = [s for s in S if s not in TSET]
rec = {}
for o in T:
    L = []
    for s in S:
        t = o ^ s
        if t in S:
            if s < t:
                L.append((s, t))
        elif t in V2:
            L.append((s, t))
    rec[o] = L
print(f"subset scope {tag}: |P|={len(P)} |U2|={len(U2cand)} |S|={len(S)} helpers={len(helpers)} "
      f"constructions={sum(len(c) for c in cons.values())} recipes={sum(len(v) for v in rec.values())} build {time.time()-t0:.1f}s", flush=True)

from ortools.sat.python import cp_model
m = cp_model.CpModel()
y = {p: m.NewBoolVar(f"y{p:x}") for p in P}
x = {u: m.NewBoolVar(f"x{u:x}") for u in U2cand}
for u in U2cand:
    lits = []
    for c in U2cons[u]:
        if len(c) == 1:
            lits.append(y[c[0]])
        else:
            cv = m.NewBoolVar(""); m.AddImplication(cv, y[c[0]]); m.AddImplication(cv, y[c[1]]); lits.append(cv)
    m.AddBoolOr(lits + [x[u].Not()])
avail = {s: m.NewBoolVar(f"a{s:x}") for s in S}
def lit_of(v):
    if v in base: return None
    if v in Pset: return y[v]
    if v in U2set: return x[v]
    return avail[v]
ncv = 0
for s in S:
    lits = []
    for c in cons[s]:
        if len(c) == 1:
            lits.append(x[c[0]])
        else:
            cv = m.NewBoolVar(""); ncv += 1
            m.AddImplication(cv, x[c[0]] if c[0] in U2set else y[c[0]])
            m.AddImplication(cv, lit_of(c[1]))
            lits.append(cv)
    m.AddBoolOr(lits + [avail[s].Not()])
nr = 0
for o in T:
    terms = []
    if o in S:
        terms.append(avail[o])
    for s, t in rec[o]:
        r = m.NewBoolVar(""); nr += 1
        m.AddImplication(r, avail[s])
        lt = lit_of(t)
        if lt is not None:
            m.AddImplication(r, lt)
        terms.append(r)
    m.AddBoolOr(terms)
m.Minimize(sum(y.values()) + sum(x.values()) + sum(avail[s] for s in helpers))
print(f"CP-SAT model: y={len(y)} x={len(x)} avail={len(avail)} cons-vars={ncv} recipe-vars={nr} build {time.time()-t0:.1f}s", flush=True)
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = limit
solver.parameters.num_search_workers = 1
st = solver.Solve(m)
name = solver.StatusName(st)
ok = st in (cp_model.OPTIMAL, cp_model.FEASIBLE)
print(f"CP-SAT status {name} objective {solver.ObjectiveValue() if ok else None} best bound {solver.BestObjectiveBound()} wall {solver.WallTime():.1f}s")
if st == cp_model.OPTIMAL:
    L1 = [p for p in P if solver.Value(y[p])]; L2 = [u for u in U2cand if solver.Value(x[u])]
    H3 = [s for s in helpers if solver.Value(avail[s])]; Y3 = [o for o in T if o in S and solver.Value(avail[o])]
    v = int(round(solver.ObjectiveValue()))
    print(f"RESULT subset scope {tag}: min |L1|+|L2|+|H3| = {v} (|L1|={len(L1)}, |L2|={len(L2)}, |H3|={len(H3)}, level-3 outputs={len(Y3)}) => G >= 32 + {v} = {32+v} for every normal-form depth-<=4 circuit whose weight-2 masks lie in {tag}")
    json.dump({"tag": tag, "P": P, "L1": L1, "L2": L2, "H3": H3, "Y3": Y3, "opt": v}, open(os.path.join(HERE, f"d3_{tag}.json"), "w"))
else:
    print(f"RESULT subset scope {tag}: NOT PROVED (status {name}); valid lower bound: |L1|+|L2|+|H3| >= {solver.BestObjectiveBound()}")
