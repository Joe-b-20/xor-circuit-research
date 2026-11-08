"""c3_run.py -- run one scope-C instance.
usage: python3 c3_run.py TAG [key=value ...]
  fix3=i,j,...   outputs forced to level 3        fix4=i,j,...  outputs forced to level 4
  fix3=W5 / fix4=W7 shorthands;  w7l3=bitmask over the 6 realisable weight-7 outputs (sorted index order)
  ub=30          hard bound |L2|+|H3| <= ub        time=600      wall limit (s)
  workers=1      core=0/1 (optimize_with_core)     maxhs=0/1     lin=1/2       strict=1/0   cuts=1/0
  u2=all|L89     level-2 candidate pool (all = scope C)
  sumx=k         exactly k level-2 masks           sumxmin=k / sumxmax=k   bounds on |L2|
  hmin=6         valid cut: at least hmin helpers among those that can serve the six never-level-3 outputs
                 (Hfree'(never6) = 6, c6b_hfree.py; valid for every level pattern)
  pc5=16         valid cut: |L2| + #(weight-5 outputs at level 4) >= 16  (PC(W5) = 16, c6_pc.py)
  m5=k           exactly k weight-5 outputs at level 4;  m5min / m5max bounds
Writes c3_TAG.json (status, bound, objective, witness) and c3_TAG.log (solver log).
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c2_model as M
HERE = M.HERE
tag = sys.argv[1]
kv = dict(a.split("=", 1) for a in sys.argv[2:])
def idx(spec):
    if not spec: return []
    if spec == "W5": return M.W5
    if spec == "W7": return M.W7
    return [int(z) for z in spec.split(",")]
fix3 = idx(kv.get("fix3", "")); fix4 = idx(kv.get("fix4", ""))
strict = kv.get("strict", "1") == "1"
U2cand = None
if kv.get("u2", "all") == "L89":
    U2cand = json.load(open(os.path.join(M.D4B, "d1_facts.json")))["L2_89"]
t0 = time.time()
U = M.Universe(M.P89, strict=strict, U2cand=U2cand)
real7 = [i for i in M.W7 if i not in U.never]
if "w7l3" in kv:
    bm = int(kv["w7l3"])
    fix3 += [real7[k] for k in range(len(real7)) if bm >> k & 1]
    fix4 += [real7[k] for k in range(len(real7)) if not bm >> k & 1]
fix4 = sorted(set(fix4) | set(U.never))
ub = int(kv["ub"]) if "ub" in kv else None
print(f"[{tag}] {U.info()}", flush=True)
print(f"[{tag}] fix3={sorted(fix3)} fix4={fix4} ub={ub} strict={strict} extra={ {k: v for k, v in kv.items() if k in ('sumx','sumxmin','sumxmax','hmin','pc5','m5','m5min','m5max','j','jmin','jmax')} }", flush=True)

def extra(m, h):
    x, a, lvl3 = h["x"], h["a"], h["lvl3"]
    sx = sum(x.values())
    if "sumx" in kv: m.Add(sx == int(kv["sumx"]))
    if "sumxmin" in kv: m.Add(sx >= int(kv["sumxmin"]))
    if "sumxmax" in kv: m.Add(sx <= int(kv["sumxmax"]))
    if "hmin" in kv:
        Hs = set()
        for i in U.never: Hs |= U.fan_inv[i]
        m.Add(sum(a[s] for s in Hs if s not in M.TSET) >= int(kv["hmin"]))
    if "pc5" in kv:
        m.Add(sx + sum(1 - lvl3[i] for i in M.W5) >= int(kv["pc5"]))
    m5 = sum(1 - lvl3[i] for i in M.W5)
    if "m5" in kv: m.Add(m5 == int(kv["m5"]))
    if "m5min" in kv: m.Add(m5 >= int(kv["m5min"]))
    if "m5max" in kv: m.Add(m5 <= int(kv["m5max"]))
    j7 = sum(lvl3[i] for i in real7)
    if "j" in kv: m.Add(j7 == int(kv["j"]))
    if "jmin" in kv: m.Add(j7 >= int(kv["jmin"]))
    if "jmax" in kv: m.Add(j7 <= int(kv["jmax"]))

m, h = M.build(U, fix3=fix3, fix4=fix4, ub=ub, cuts=kv.get("cuts", "1") == "1", extra=extra, noR2=kv.get("noR2", "0") == "1")
if kv.get("hint") == "89":        # the recorded 89 as a solution hint (primal search around it)
    D1 = json.load(open(os.path.join(M.D4B, "d1_facts.json")))
    L2_89 = set(D1["L2_89"]); H89 = set(D1["L3h_89"])
    for u, v in h["x"].items(): m.AddHint(v, int(u in L2_89))
    for s, v in h["a"].items(): m.AddHint(v, int(s in H89 or (s in M.TSET and M.TI[s] in M.W5)))
print(f"[{tag}] model: x={len(h['x'])} a={len(h['a'])} cons-vars={h['ncv']} recipe-vars={h['nr']} build {time.time()-t0:.1f}s", flush=True)
res = M.solve(m, h, float(kv.get("time", 600)), workers=int(kv.get("workers", 1)), core=kv.get("core", "0") == "1",
              log=os.path.join(HERE, f"c3_{tag}.log"), lin=int(kv.get("lin", 1)), maxhs=kv.get("maxhs", "0") == "1")
res.update(tag=tag, fix3=sorted(fix3), fix4=fix4, ub=ub, strict=strict, args=kv, total_wall=time.time() - t0)
print(f"[{tag}] status {res['status']} objective {res.get('objective')} bound {res['bound']} wall {res['wall']:.1f}s", flush=True)
if "objective" in res:
    print(f"[{tag}] witness: |L2|={len(res['L2'])} |H3|={len(res['H3'])} Y3={res['Y3']}", flush=True)
    if res["objective"] <= 30:
        print(f"[{tag}] !!!!! OBJECTIVE <= 30: candidate 88-gate circuit, verify with c5_verify.py !!!!!", flush=True)
json.dump(res, open(os.path.join(HERE, f"c3_{tag}.json"), "w"))
