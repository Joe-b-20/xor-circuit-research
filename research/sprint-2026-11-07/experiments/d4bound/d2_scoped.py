"""d2_scoped.py -- exact scoped minimisation of h2 + h3 for depth-4 circuits whose FIRST LAYER is a
given pair set P (here the 26 pairs of the repo 89@4), with the level-2 layer drawn from a candidate
list U2cand.  Model (layered value-set form, proved lossless in REPORT.md section 1):

  V2   = inputs u P u L2,  L2 subset of U2cand (triples x+p / quartets p+p' over P), cost 1 each
  S    = {u ^ v : u in U2cand, v in V2} \\ (V2 u {0})  = every mask a level-3 gate can carry
  level-3 helper s in S \\ TARGETS : cost 1, needs a construction (u, v) with u, v available
  level-3 output o in S            : cost 0, needs a construction
  level-4 output o                 : o = s ^ t with s in S (helper or level-3 output), t in S u V2,
                                     both available; cost 0
  minimise |L2| + |helpers|.      G >= 32 + |P| + optimum   for every circuit in the scope.

Scopes (argument):
  A  U2cand = the 89's 22 level-2 values, all forced          (is h3 = 9 minimal over the 89's bank?)
  B  U2cand = the 30 level-2 values of the 81-state family L0  (choice free)
  C  U2cand = all 1060 triples/quartets over P                 (the full first-layer scope)
Solver: OR-tools CP-SAT (exact; optimality proof printed) with a wall limit; for C also the LP
relaxation via scipy/HiGHS as a cheap valid lower bound.  Single process; run under nice.
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
P = F["P89"]
scope = sys.argv[1]
limit = float(sys.argv[2]) if len(sys.argv) > 2 else 600.0
mode = sys.argv[3] if len(sys.argv) > 3 else "cpsat"

def all_u2(P):
    U = set()
    for pr in P:
        for x in INPUTS:
            if not (pr & x):
                U.add(pr | x)
    for a, b in itertools.combinations(P, 2):
        if not (a & b):
            U.add(a | b)
    return sorted(U)

if scope == "A":
    U2cand = sorted(F["L2_89"]); forced = set(U2cand)
elif scope == "B":
    s7 = json.load(open(os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/q89/s7_structure.json")))
    core = [v for v in s7["const"] if pc(v) in (3, 4) and v not in set(P)]
    slots = [v for sl in s7["slots"] for v in sl]
    U2cand = sorted(set(core) | set(slots)); forced = set()
    assert set(F["L2_89"]) <= set(U2cand), "89's level-2 values must be in the L0 union"
elif scope == "C":
    U2cand = all_u2(P); forced = set()
else:
    raise SystemExit("scope A|B|C")
U2 = all_u2(P)
assert set(U2cand) <= set(U2)

t0 = time.time()
base = set(INPUTS) | set(P)
U2set = set(U2cand)
V2 = base | U2set
V2l = sorted(V2)
cons = collections.defaultdict(set)      # s -> set of constructions; construction = (u,) if v in base else (min,max)
for u in U2cand:
    for v in V2l:
        if v == u:
            continue
        s = u ^ v
        if s == 0 or s in V2:
            continue
        cons[s].add((u,) if v in base else (min(u, v), max(u, v)))
S = set(cons)
helpers = [s for s in S if s not in TSET]
outs3 = [o for o in T if o in S]
ncons = sum(len(c) for c in cons.values())
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
nrec = sum(len(v) for v in rec.values())
print(f"scope {scope}: |U2cand|={len(U2cand)} forced={len(forced)} |V2|={len(V2)} |S|={len(S)} helpers={len(helpers)} "
      f"level-3-realizable outputs={len(outs3)} constructions={ncons} level-4 recipes={nrec}  build {time.time()-t0:.1f}s", flush=True)

if mode == "lp":
    import numpy as np, scipy.sparse as sp
    from scipy.optimize import linprog
    # variables: x_u (U2cand), a_s (S), c_k (two-U2 constructions), r_k (recipes)
    xi = {u: i for i, u in enumerate(U2cand)}; nx = len(xi)
    si = {s: nx + i for i, s in enumerate(sorted(S))}; ns = len(si)
    cidx = {}; rows = []; cols = []; vals = []; rhs = []; nrow = 0
    nextvar = nx + ns
    def addrow(entries, b):      # sum entries <= b
        global nrow
        for j, v in entries:
            rows.append(nrow); cols.append(j); vals.append(v)
        rhs.append(b); nrow += 1
    # a_s <= sum lits
    for s in sorted(S):
        ent = [(si[s], 1.0)]
        for c in cons[s]:
            if len(c) == 1:
                ent.append((xi[c[0]], -1.0))
            else:
                if c not in cidx:
                    cidx[c] = nextvar; nextvar += 1
                    # c <= x_u, c <= x_v
                    addrow([(cidx[c], 1.0), (xi[c[0]], -1.0)], 0.0)
                    addrow([(cidx[c], 1.0), (xi[c[1]], -1.0)], 0.0)
                ent.append((cidx[c], -1.0))
        addrow(ent, 0.0)
    # outputs
    for o in T:
        ent = []
        if o in S:
            ent.append((si[o], -1.0))
        for s, t in rec[o]:
            j = nextvar; nextvar += 1
            addrow([(j, 1.0), (si[s], -1.0)], 0.0)
            if t in S:
                addrow([(j, 1.0), (si[t], -1.0)], 0.0)
            elif t in U2set:
                addrow([(j, 1.0), (xi[t], -1.0)], 0.0)
            ent.append((j, -1.0))
        addrow(ent, -1.0)          # -(sum) <= -1
    nv = nextvar
    cvec = np.zeros(nv); cvec[:nx] = 1.0
    for s in helpers:
        cvec[si[s]] = 1.0
    A = sp.csr_matrix((vals, (rows, cols)), shape=(nrow, nv))
    bounds = [(0, 1)] * nv
    for u in forced:
        bounds[xi[u]] = (1, 1)
    print(f"LP: {nv} vars, {nrow} rows, build {time.time()-t0:.1f}s", flush=True)
    res = linprog(cvec, A_ub=A, b_ub=np.array(rhs), bounds=bounds, method="highs", options={"time_limit": limit, "disp": False})
    print("LP status:", res.status, res.message, " value:", res.fun, f" ({time.time()-t0:.1f}s)")
    if res.status == 0:
        print(f"RESULT scope {scope} LP relaxation: h2 + h3 >= {res.fun:.4f}  =>  G >= 32 + {len(P)} + ceil = {32 + len(P) + int(-(-res.fun // 1))}")
    sys.exit(0)

from ortools.sat.python import cp_model
m = cp_model.CpModel()
x = {u: m.NewBoolVar(f"x{u:x}") for u in U2cand}
for u in forced:
    m.Add(x[u] == 1)
avail = {s: m.NewBoolVar(f"a{s:x}") for s in S}
ncvar = 0
for s in S:
    lits = []
    for c in cons[s]:
        if len(c) == 1:
            lits.append(x[c[0]])
        else:
            cv = m.NewBoolVar(""); ncvar += 1
            m.AddImplication(cv, x[c[0]]); m.AddImplication(cv, x[c[1]])
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
        if t in S:
            m.AddImplication(r, avail[t])
        elif t in U2set:
            m.AddImplication(r, x[t])
        terms.append(r)
    m.AddBoolOr(terms)
obj = sum(x.values()) + sum(avail[s] for s in helpers)
m.Minimize(obj)
print(f"CP-SAT model: x={len(x)} avail={len(avail)} cons-vars={ncvar} recipe-vars={nr}  build {time.time()-t0:.1f}s", flush=True)
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = limit
solver.parameters.num_search_workers = 1; solver.parameters.linearization_level = 2
solver.parameters.log_search_progress = False
st = solver.Solve(m)
name = solver.StatusName(st)
print(f"CP-SAT status {name} objective {solver.ObjectiveValue() if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None} "
      f"best bound {solver.BestObjectiveBound()}  wall {solver.WallTime():.1f}s")
if st == cp_model.OPTIMAL:
    L2 = sorted(u for u in U2cand if solver.Value(x[u]))
    H3 = sorted(s for s in helpers if solver.Value(avail[s]))
    Y3 = [o for o in outs3 if solver.Value(avail[o])]
    print(f"RESULT scope {scope}: min h2 + h3 = {int(round(solver.ObjectiveValue()))}  (h2={len(L2)}, h3={len(H3)}, level-3 outputs={len(Y3)}) "
          f"=> every depth-4 circuit in the scope has G >= 32 + {len(P)} + {int(round(solver.ObjectiveValue()))} = {32 + len(P) + int(round(solver.ObjectiveValue()))}")
    json.dump({"scope": scope, "L2": L2, "H3": H3, "Y3": Y3, "opt": solver.ObjectiveValue()}, open(os.path.join(HERE, f"d2_scope{scope}.json"), "w"))
else:
    print(f"RESULT scope {scope}: NOT PROVED (status {name}); valid lower bound from solver: h2 + h3 >= {solver.BestObjectiveBound()}")
