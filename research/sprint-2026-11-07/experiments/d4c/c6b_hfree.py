"""c6b_hfree.py -- pure helper bounds valid for EVERY level pattern: Hfree'(Y4) = min number of level-3
helpers to put the outputs Y4 at level 4 when all of U2 is free and ALL level-3-realisable outputs not in
Y4 (weight-5 and the six realisable weight-7) are free partners.  Also: the number of minimum (size-16)
parent covers of the 20 weight-5 outputs over P89 (enumeration, capped)."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c2_model as M
from ortools.sat.python import cp_model
U = M.Universe(M.P89, strict=True); T = M.T; W = M.W
real7 = [i for i in M.W7 if i not in U.never]
REAL = set(M.W5) | set(real7)
out = {}

def Hfree(Y4, label, limit=240):
    Y4 = set(Y4); y3 = REAL - Y4
    m = cp_model.CpModel(); Hs = set()
    for i in Y4: Hs |= U.fan_inv[i]
    a = {s: m.NewBoolVar("") for s in Hs if s not in M.TSET}
    for i in Y4:
        o = T[i]; terms = []
        for s in U.fan_inv[i]:
            t = o ^ s
            if s in M.TSET:
                if M.TI[s] not in y3: continue
                if t in U.V2: terms.append(m.NewBoolVar(""))   # Lemma-5 style: free (bool unconstrained)
                elif t in a: terms.append(a[t])
                continue
            if t in U.V2: terms.append(a[s])
            elif t in M.TSET:
                if M.TI[t] in y3: terms.append(a[s])
            elif s < t:
                r = m.NewBoolVar(""); m.AddImplication(r, a[s]); m.AddImplication(r, a[t]); terms.append(r)
        m.AddBoolOr(terms)
    m.Minimize(sum(a.values()))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = limit; sv.parameters.num_search_workers = 1
    sv.parameters.optimize_with_core = True
    st = sv.Solve(m)
    val = sv.ObjectiveValue() if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None
    print(f"Hfree'({label}) = {val} bound {sv.BestObjectiveBound()} [{sv.StatusName(st)} {sv.WallTime():.1f}s] |Y4|={len(Y4)} helpers={len(a)}", flush=True)
    wit = []
    if val is not None:
        H = [s for s in a if sv.Value(a[s])]
        for s in H:
            served = []
            for i in Y4:
                t = T[i] ^ s
                if t in U.V2: served.append((i, "V2:" + ("base" if t in U.base else "U2")))
                elif t in M.TSET and M.TI[t] in y3: served.append((i, f"y{M.TI[t]}"))
                elif t in H: served.append((i, "helper"))
            par = sorted({u for u, v in U.cons[s]} | {v for u, v in U.cons[s] if v in U.U2set})
            wit.append((s, M.pc(s), served, len(par)))
            print(f"      helper {s:#x} w{M.pc(s)} serves {served}  (#candidate level-2 parents {len(par)})")
    return {"value": val, "bound": sv.BestObjectiveBound(), "status": sv.StatusName(st), "witness": wit}

out["never6"] = Hfree(U.never, "six never-level-3 outputs")
for i in real7:
    out[f"never6+y{i}"] = Hfree(U.never + [i], f"never6 + y{i}", limit=90)
out["W7"] = Hfree(M.W7, "all 12 weight-7 outputs", limit=300)
out["never6+y0"] = Hfree(U.never + [0], "never6 + y0 (weight 5)", limit=90)
out["never6+y7"] = Hfree(U.never + [7], "never6 + y7 (weight 5, Lemma-5-capable)", limit=90)
# count minimum parent covers of W5
m = cp_model.CpModel(); x = {u: m.NewBoolVar("") for u in U.U2}
for i in M.W5:
    terms = []
    for u, v in U.C3[i]:
        if v in U.base: terms.append(x[u])
        else:
            d = m.NewBoolVar(""); m.AddImplication(d, x[u]); m.AddImplication(d, x[v]); m.AddBoolOr([d, x[u].Not(), x[v].Not()]); terms.append(d)
    m.AddBoolOr(terms)
m.Add(sum(x.values()) == 16)
class CB(cp_model.CpSolverSolutionCallback):
    def __init__(s): super().__init__(); s.n = 0; s.sols = set()
    def on_solution_callback(s):
        s.sols.add(tuple(u for u in U.U2 if s.Value(x[u]))); s.n += 1
        if len(s.sols) >= 20000: s.StopSearch()
sv = cp_model.CpSolver(); sv.parameters.enumerate_all_solutions = True; sv.parameters.num_search_workers = 1
sv.parameters.max_time_in_seconds = 120
cb = CB(); st = sv.Solve(m, cb)
print(f"minimum (16-mask) parent covers of W5 over P89: {len(cb.sols)} distinct [{sv.StatusName(st)} {sv.WallTime():.1f}s]", flush=True)
out["n_min_covers_W5"] = len(cb.sols); out["min_covers_status"] = sv.StatusName(st)
json.dump(out, open(os.path.join(M.HERE, "c6b_hfree.json"), "w"))
