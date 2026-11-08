"""e2_model.py -- copy of d4c/c2_model.py (exact scope-C model) with three additions for d4c2:
  * build(..., allowed=SET): level-3 variables only for helpers in SET (plus outputs in S); recipes whose
    operands are not both available are dropped.  Used only where a proof shows every circuit of the branch
    with |L2|+|H3| <= 30 has all its helpers in SET (see d4c2/REPORT.md); then min >= 31 closes the branch.
  * solve(..., stop_at=31): stop as soon as the proved bound reaches stop_at (pure minimisation protocol).
  * solve(..., sub="core4"): 4 core-based workers with different settings (one process, 4 threads).
  * any solution with objective <= 30 found during search is dumped at once (solve(..., dump=path)).
Original docstring follows.

c2_model.py -- exact scope-C model (first layer = P89, level-2 layer free) as a library.

Scope (REPORT.md of d4bound, section 5.1, strict normal form): a depth-<=4 circuit in normal form whose
set of weight-2 masks is EXACTLY P (the 89's 26 pairs).  Then (Lemmas 1-2 there):
  level 1 = P;  level 2 = L2 subset of U2(P) (triples x+p, quartets p+p');  V2 = inputs u P u L2;
  level 3 = masks in S = (U2 + V2) \\ (V2 u {0} u {weight 2}); a level-3 gate is u ^ v, u in L2, v in V2;
  level 4 = outputs only, o = s ^ t with s a present level-3 signal, t a present level-3 signal or V2 element.
  G = 32 + |P| + |L2| + |H3|  (H3 = level-3 non-outputs).   The question: |L2| + |H3| <= 30 ?
Weight-2 masks are excluded from S because in normal form a weight-2 mask is a level-1 pair (Lemma 1 (iii));
a circuit using one at level 3 has weight-2 set != P.  (Option strict=False keeps them: that is the
relaxation "P plus extra pairs that feed only level-4 outputs"; every statement proved with strict=False
covers the strict scope too.)
Lossless pruning: a level-3 helper must feed a level-4 output (normal form (ii)), so a mask with no level-4
recipe (fan-out 0) is never a helper; it is dropped from the helper universe.  (A partner t of an R2 recipe
o = s ^ t has the recipe itself, so partners are never pruned away.)

Model (CP-SAT):  x_u (u in U2) ... level-2 mask present, cost 1
                 a_s (s in H u Y3cand) ... level-3 signal present; cost 1 if s is not an output
                 a_s -> OR of constructions (u,v): x_u [and x_v if v in U2]
                 output o: a_o (if o in S) OR some recipe r(o,s): r -> a_s and partner present
                 optional: fixed levels for outputs, valid cuts, hard bound on the objective.
"""
import json, os, sys, time, itertools, collections
HERE = os.path.dirname(os.path.abspath(__file__))
D4B = os.path.join(os.path.dirname(HERE), "d4bound")
N = 32; INPUTS = [1 << j for j in range(N)]; FULL = (1 << N) - 1
pc = lambda v: bin(v).count("1")
REPO = os.path.expanduser("~/xor-circuit-research")
MAT = os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")


def load_targets():
    toks = " ".join(l.split("%")[0] for l in open(MAT).read().splitlines()).split()
    r, c = int(toks[1]), int(toks[2]); bits = list(map(int, toks[3:3 + r * c]))
    return [sum(bits[i * c + j] << j for j in range(c)) for i in range(r)]


T = load_targets(); TSET = set(T); W = [pc(t) for t in T]; TI = {t: i for i, t in enumerate(T)}
W5 = [i for i in range(32) if W[i] == 5]; W7 = [i for i in range(32) if W[i] == 7]
P89 = json.load(open(os.path.join(D4B, "d1_facts.json")))["P89"]


class Universe:
    def __init__(self, P, strict=True, U2cand=None):
        t0 = time.time()
        self.P = list(P); Pset = set(P)
        U2 = set()
        for pr in P:
            for x in INPUTS:
                if not (pr & x): U2.add(pr | x)
        for a, b in itertools.combinations(P, 2):
            if not (a & b): U2.add(a | b)
        self.U2all = sorted(U2)
        self.U2 = sorted(U2 if U2cand is None else set(U2cand)); self.U2set = set(self.U2)
        assert self.U2set <= U2
        self.base = set(INPUTS) | Pset
        self.V2 = self.base | self.U2set; V2l = sorted(self.V2)
        cons = collections.defaultdict(list)
        for u in self.U2:
            for v in V2l:
                if v == u: continue
                s = u ^ v
                if s == 0 or s in self.V2: continue
                if strict and pc(s) == 2: continue
                if v in self.base or u < v:          # each unordered U2+U2 construction once
                    cons[s].append((u, v))
        self.S = set(cons); self.cons = cons
        # fan-out and recipes
        fan = collections.defaultdict(set)
        for i, o in enumerate(T):
            for s in self.S:
                t = o ^ s
                if t in self.V2 or t in self.S:
                    fan[s].add(i)
        self.fan = fan
        self.H = set(s for s in self.S if s in fan or s in TSET)   # helper universe u outputs in S
        self.fan_inv = {i: set() for i in range(32)}
        for s, outs in fan.items():
            for i in outs: self.fan_inv[i].add(s)
        self.outS = [i for i, o in enumerate(T) if o in self.S]
        self.never = [i for i in range(32) if T[i] not in self.S]
        # level-3 constructions of outputs (for cuts / reporting)
        self.C3 = {i: cons.get(T[i], []) for i in range(32)}
        self.build_time = time.time() - t0

    def info(self):
        return (f"|U2|={len(self.U2)} |V2|={len(self.V2)} |S|={len(self.S)} helper-universe={len(self.H)} "
                f"level-3-realisable outputs={len(self.outS)} never={self.never} build {self.build_time:.1f}s")


def build(U, fix3=(), fix4=(), ub=None, cuts=True, forced_L2=(), banned_L2=(), extra=None, noR2=False,
          allowed=None):
    """Return (model, handles).  fix3/fix4: output indices forced to level 3 / 4.  ub: hard bound on
    |L2| + |H3|.  forced_L2 / banned_L2: level-2 masks forced present / absent.  extra(m, h): hook.
    noR2: sub-scope "no two-helper recipe" (every level-4 output = one helper + a level-<= 2 signal or a
    level-3 output); recipes with two non-output level-3 operands are dropped."""
    from ortools.sat.python import cp_model
    m = cp_model.CpModel()
    x = {u: m.NewBoolVar(f"x{u:x}") for u in U.U2}
    for u in forced_L2: m.Add(x[u] == 1)
    for u in banned_L2: m.Add(x[u] == 0)
    fix3 = set(fix3); fix4 = set(fix4)
    a = {}
    Hvars = [s for s in U.H if allowed is None or s in allowed or s in TSET]
    for s in Hvars:
        a[s] = m.NewBoolVar(f"a{s:x}")
    # outputs not in S: level 4 forced
    for i in U.never:
        assert i not in fix3, f"output {i} cannot be at level 3 over this first layer"
    # constructions
    ncv = 0
    for s in Hvars:
        lits = []
        for u, v in U.cons[s]:
            if v in U.base:
                lits.append(x[u])
            else:
                cv = m.NewBoolVar(""); ncv += 1
                m.AddImplication(cv, x[u]); m.AddImplication(cv, x[v]); lits.append(cv)
        m.AddBoolOr(lits + [a[s].Not()])
    # level fixings
    lvl3 = {}
    for i in range(32):
        o = T[i]
        if o in U.S:
            lvl3[i] = a[o]
            if i in fix3: m.Add(a[o] == 1)
            if i in fix4: m.Add(a[o] == 0)
        else:
            lvl3[i] = None
    # recipes
    rec = {}; nr = 0
    Hset = U.H
    for i, o in enumerate(T):
        terms = []
        if lvl3[i] is not None: terms.append(lvl3[i])
        rl = []
        if i in fix3:
            rec[i] = rl; continue
        for s in sorted(U.fan_inv[i]):
            if s not in a: continue          # helper outside the allowed set
            t = o ^ s
            if t in U.S and t not in a: continue
            if t in U.S:
                if s > t: continue          # unordered pair once
                if noR2 and s not in TSET and t not in TSET: continue
                r = m.NewBoolVar(""); nr += 1
                m.AddImplication(r, a[s]); m.AddImplication(r, a[t])
                rl.append((r, s, t))
            elif t in U.U2set:
                r = m.NewBoolVar(""); nr += 1
                m.AddImplication(r, a[s]); m.AddImplication(r, x[t])
                rl.append((r, s, t))
            else:                            # t input or pair: free
                rl.append((a[s], s, t))
        terms += [r for r, _, _ in rl]
        m.AddBoolOr(terms)
        rec[i] = rl
    helpers = [s for s in Hvars if s not in TSET]
    obj = sum(x.values()) + sum(a[s] for s in helpers)
    if ub is not None:
        m.Add(obj <= ub)
    if cuts:
        # K1: level-4 output needs a present helper operand unless (level 3) or (Lemma-5: level-3 output + V2)
        for i, o in enumerate(T):
            if i in fix3: continue
            terms = []
            if lvl3[i] is not None: terms.append(lvl3[i])
            seen = set()
            for r, s, t in rec[i]:
                for z in (s, t):
                    if z in U.S and z not in TSET and z not in seen:
                        seen.add(z); terms.append(a[z])
                if s in TSET and t not in U.S:      # Lemma-5 recipe: no helper
                    terms.append(r)
            m.Add(sum(terms) >= 1)
        # K2: a level-3 output needs a level-2 parent among its candidate parents
        for i in range(32):
            if lvl3[i] is None: continue
            par = sorted({u for u, v in U.C3[i]} | {v for u, v in U.C3[i] if v in U.U2set})
            m.Add(sum(x[u] for u in par) >= 1).OnlyEnforceIf(lvl3[i])
            if W[i] == 7:
                tri = [u for u in par if pc(u) == 3]; qua = [u for u in par if pc(u) == 4]
                m.Add(sum(x[u] for u in tri) >= 1).OnlyEnforceIf(lvl3[i])
                m.Add(sum(x[u] for u in qua) >= 1).OnlyEnforceIf(lvl3[i])
        # K3: a helper needs a level-2 parent
        for s in helpers:
            par = sorted({u for u, v in U.cons[s]} | {v for u, v in U.cons[s] if v in U.U2set})
            m.Add(sum(x[u] for u in par) >= 1).OnlyEnforceIf(a[s])
    if extra is not None:
        extra(m, dict(x=x, a=a, lvl3=lvl3, rec=rec, helpers=helpers, obj=obj))
    m.Minimize(obj)
    h = dict(x=x, a=a, lvl3=lvl3, rec=rec, helpers=helpers, obj=obj, ncv=ncv, nr=nr)
    return m, h


CORE4_MIX1 = [  # name, overrides (all core-based; diversity by seed / core extraction settings)
    ("core_a", dict(linearization_level=1)),
    ("core_b", dict(linearization_level=0, random_seed=7)),
    ("core_c", dict(linearization_level=1, find_multiple_cores=False, random_seed=13)),
    ("core_d", dict(linearization_level=0, max_sat_reverse_assumption_order=True, random_seed=29)),
]
# mix 2 (used from run BJ on, 2026-11-08 ~04:30 UTC): in B0 and FULLnoR2 every core-found bound improvement came
# from core_b (26 of 27) or core_d (1), both linearisation 0; core_a / core_c (linearisation 1) only reported the
# initial propagation bound.  So all four workers are linearisation-0 core workers, core_b and core_d kept as they
# were, two more seeds added.
CORE4 = [
    ("core_b", dict(linearization_level=0, random_seed=7)),
    ("core_e", dict(linearization_level=0, random_seed=101)),
    ("core_f", dict(linearization_level=0, random_seed=211)),
    ("core_d", dict(linearization_level=0, max_sat_reverse_assumption_order=True, random_seed=29)),
]


def solve(m, h, limit, workers=1, core=False, log=None, lin=1, hint=None, maxhs=False, sub=None,
          stop_at=None, dump=None, dump_at=30):
    from ortools.sat.python import cp_model
    sv = cp_model.CpSolver()
    sv.parameters.max_time_in_seconds = limit
    if sub is None:
        sv.parameters.num_search_workers = workers
    sv.parameters.linearization_level = lin
    sv.parameters.log_search_progress = log is not None
    sv.parameters.log_to_stdout = False
    if core:
        sv.parameters.optimize_with_core = True
    if maxhs:
        sv.parameters.optimize_with_core = True
        sv.parameters.optimize_with_max_hs = True
    if sub == "core4":
        # this ortools build's pybind parameter object only accepts repeated messages via text format
        V = CORE4[:workers]
        fmt = lambda v: ("true" if v else "false") if isinstance(v, bool) else str(v)
        txt = f"num_workers: {workers} num_full_subsolvers: {len(V)} "
        txt += " ".join(f'subsolvers: "{nm}"' for nm, _ in V) + " "
        txt += " ".join(f'subsolver_params {{ name: "{nm}" optimize_with_core: true '
                        + " ".join(f"{k}: {fmt(v)}" for k, v in ov.items()) + " }" for nm, ov in V)
        sv.parameters.merge_text_format(txt)
    if log is not None:
        f = open(log, "w")
        sv.log_callback = lambda s: (f.write(s + "\n"), f.flush())
    if stop_at is not None:
        def bcb(b):
            if b >= stop_at - 1e-6:
                sv.stop_search()
        sv.best_bound_callback = bcb

    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__(); self.n = 0
        def on_solution_callback(self):
            self.n += 1
            if dump is not None and self.ObjectiveValue() <= dump_at + 1e-6:
                w = {"objective": self.ObjectiveValue(),
                     "L2": sorted(u for u in h["x"] if self.Value(h["x"][u])),
                     "H3": sorted(s for s in h["helpers"] if self.Value(h["a"][s])),
                     "Y3": sorted(i for i in range(32) if h["lvl3"][i] is not None and self.Value(h["lvl3"][i])),
                     "recipes": {i: [(s, t) for r, s, t in h["rec"][i] if self.Value(r)] for i in range(32)}}
                w["total"] = len(w["L2"]) + len(w["H3"])      # |L2| + |H3| (= objective unless obj=x)
                if w["total"] <= 30:
                    json.dump(w, open(dump, "w"))
                    print(f"!!!!! solution with |L2|+|H3| = {w['total']} <= 30 dumped to {dump} !!!!!", flush=True)
    cb = CB()
    st = sv.Solve(m, cb)
    name = sv.StatusName(st)
    res = {"status": name, "wall": sv.WallTime(), "bound": sv.BestObjectiveBound(), "nsol": cb.n}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        res["objective"] = sv.ObjectiveValue()
        res["L2"] = sorted(u for u in h["x"] if sv.Value(h["x"][u]))
        res["H3"] = sorted(s for s in h["helpers"] if sv.Value(h["a"][s]))
        res["Y3"] = sorted(i for i in range(32) if h["lvl3"][i] is not None and sv.Value(h["lvl3"][i]))
        res["recipes"] = {i: [(s, t) for r, s, t in h["rec"][i] if sv.Value(r)] for i in range(32)}
    if log is not None:
        f.close()
    return res


def witness_to_circuit(U, L2, H3, Y3, recipes):
    """Build a gate list (mask, mask_a, mask_b, level) from a witness; outputs at level 3 use their
    construction, outputs at level 4 their recipe.  Returns gates and the levels; raises if inconsistent."""
    present = {}
    for xm in INPUTS: present[xm] = 0
    gates = []
    for p in U.P:
        bits = [1 << j for j in range(N) if p >> j & 1]
        gates.append((p, bits[0], bits[1], 1)); present[p] = 1
    L2set = set(L2)
    for u in L2:
        done = False
        for xm in INPUTS:
            if (u & xm) and (u ^ xm) in present and present[u ^ xm] == 1:
                gates.append((u, u ^ xm, xm, 2)); present[u] = 2; done = True; break
        if not done:
            for p in U.P:
                if (u & p) == p and (u ^ p) in present and present[u ^ p] <= 1:
                    gates.append((u, u ^ p, p, 2)); present[u] = 2; done = True; break
        assert done, f"level-2 mask {u:x} has no construction"
    def lvl3_gate(s):
        for u, v in U.cons[s]:
            if u in present and v in present and present[u] <= 2 and present[v] <= 2:
                gates.append((s, u, v, 3)); present[s] = 3; return True
        return False
    for s in H3:
        assert lvl3_gate(s), f"helper {s:x} unconstructible"
    for i in Y3:
        assert lvl3_gate(T[i]), f"output {i} not at level 3"
    for i in range(32):
        if i in Y3: continue
        ok = False
        for s, t in recipes[i]:
            if s in present and present[s] <= 3 and (t in present and present[t] <= 3):
                gates.append((T[i], s, t, 4)); present[T[i]] = 4; ok = True; break
        assert ok, f"output {i} has no valid recipe"
    return gates


def write_circ(gates, path, name):
    """Write an NCFF-style circuit file (same syntax as the repo's)."""
    names = {1 << j: f"x{j}" for j in range(N)}
    nt = 0; lines = []
    for mask, a, b, L in gates:
        if mask in TSET:
            nm = f"y{TI[mask]}"
        else:
            nt += 1; nm = f"t{nt}"
        names[mask] = nm
        lines.append(f"XOR {nm} {names[a]} {names[b]}")
    G = len(gates); D = max(L for _, _, _, L in gates)
    with open(path, "w") as f:
        f.write("%NCFF-0.1-2026 (NIST Circuit File Format)\n\n## Index of circuits (circuitName numOutputs numInputs)\n")
        f.write(f"  % {name} 32 32\n\n## Circuit\nbegin circuit {name}\n\n")
        f.write(f"  % Tally of gates ({G}): {G} XOR\n  % Gate depth {D}\n\nInputs: x0:x31\nOutputs: y0:y31\nInternal: t1:t{nt}\n")
        f.write("GateSyntax: GateName Output Inputs\n\nbegin SLP\n" + "\n".join(lines) + "\nend SLP\nend circuit\n")
    return G, D
