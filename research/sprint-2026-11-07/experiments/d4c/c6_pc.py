"""c6_pc.py -- exact small bounds over P89 (strict), CP-SAT, seconds each:
  PC(Y)   = min |L2| such that every output in Y is at level 3 over P89 (constructions u^v, u in L2,
            v in inputs u P89 u L2); for Y = W5, W5 + one realisable weight-7, W5 + all six.
  H7free  = min number of level-3 helpers needed to put the 12 weight-7 outputs at level 4 when EVERY
            level-2 mask is free (all of U2 present, cost 0) and the 20 weight-5 outputs are present at
            level 3; and the same for the 6 never-level-3 outputs alone.  (Pure helper bound.)
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c2_model as M
from ortools.sat.python import cp_model
U = M.Universe(M.P89, strict=True); T = M.T; W = M.W; pc = M.pc
print(U.info(), flush=True)
real7 = [i for i in M.W7 if i not in U.never]
out = {}

def PC(Y, label, limit=120):
    m = cp_model.CpModel(); x = {u: m.NewBoolVar("") for u in U.U2}
    for i in Y:
        terms = []
        for u, v in U.C3[i]:
            if v in U.base: terms.append(x[u])
            else:
                d = m.NewBoolVar(""); m.AddImplication(d, x[u]); m.AddImplication(d, x[v]); terms.append(d)
        assert terms, f"output {i} not realisable"
        m.AddBoolOr(terms)
    m.Minimize(sum(x.values()))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = limit; sv.parameters.num_search_workers = 1
    st = sv.Solve(m)
    val = int(sv.ObjectiveValue()) if st == cp_model.OPTIMAL else None
    print(f"PC({label}) = {val} [{sv.StatusName(st)} {sv.WallTime():.1f}s] |Y|={len(Y)}", flush=True)
    return val

out["PC_W5"] = PC(M.W5, "W5")
for i in real7:
    out[f"PC_W5+y{i}"] = PC(M.W5 + [i], f"W5+y{i}")
out["PC_W5+all6"] = PC(M.W5 + real7, "W5+all six realisable weight-7")
out["PC_all6"] = PC(real7, "the six realisable weight-7 alone")

def Hfree(Y4, label, limit=300):
    """min helpers: all of U2 present free; W5 outputs present at level 3 (free); Y4 outputs at level 4."""
    m = cp_model.CpModel()
    Hs = set()
    for i in Y4: Hs |= U.fan_inv[i]
    a = {s: m.NewBoolVar("") for s in Hs if s not in M.TSET}
    y3 = set(M.W5)
    for i in Y4:
        o = T[i]; terms = []
        for s in U.fan_inv[i]:
            t = o ^ s
            if s in M.TSET:
                if M.TI[s] not in y3: continue
                if t in U.V2: terms.append(m.NewConstant(1))
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
    print(f"Hfree({label}) = {sv.ObjectiveValue() if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None} "
          f"bound {sv.BestObjectiveBound()} [{sv.StatusName(st)} {sv.WallTime():.1f}s] helpers={len(a)}", flush=True)
    return (sv.ObjectiveValue() if st == cp_model.OPTIMAL else None, sv.BestObjectiveBound())

out["Hfree_never6"] = Hfree(U.never, "six never-level-3 outputs")
out["Hfree_W7"] = Hfree(M.W7, "all 12 weight-7 outputs")
json.dump(out, open(os.path.join(M.HERE, "c6_pc.json"), "w"))
