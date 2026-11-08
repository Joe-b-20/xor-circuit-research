"""e3_run.py -- run one scope-C instance (d4c2 version of d4c/c3_run.py, same keys plus the new ones).
usage: python3 e3_run.py TAG [key=value ...]
  fix3=i,j,...   outputs forced to level 3        fix4=i,j,...  outputs forced to level 4
  fix3=W5 / fix4=W7 shorthands;  w7l3=bitmask over the 6 realisable weight-7 outputs (sorted index order)
  ub=30          hard bound |L2|+|H3| <= ub (NOT used in d4c2: pure minimisation)   time=600 wall limit (s)
  workers=1      core=0/1 (optimize_with_core)     maxhs=0/1     lin=1/2       strict=1/0   cuts=1/0
  sumx=k         exactly k level-2 masks           sumxmin=k / sumxmax=k   bounds on |L2|
  hmin=6         valid cut: >= hmin helpers among those that can serve the six never-level-3 outputs (N6)
  pc5=16         valid cut: |L2| + #(weight-5 outputs at level 4) >= 16
  m5=k / m5min / m5max     number of weight-5 outputs at level 4
  j / jmin / jmax          number of the six realisable weight-7 outputs at level 3
  noR2=1         sub-scope: no level-4 recipe with two non-output level-3 operands
 new in d4c2:
  helpers=N6     level-3 helper universe restricted to N6 (sound only when the branch forces all helpers into
                 N6 for every circuit with |L2|+|H3| <= 30, e.g. sumx=24 with hmin=6; see REPORT.md)
  outN6max=k     at most k helpers outside N6 (sound when sumx=s fixes |H3| <= 30-s and hmin=6: k = 24-s)
  sub=core4      `workers` core-based subsolvers with different settings (e2_model.CORE4)
  stop=31        stop when the proved bound reaches 31 (branch closed: no circuit with |L2|+|H3| <= 30)
  hsum=h         branch |H3| = h exactly         obj=x  minimise |L2| only (then closed iff bound >= 31-h;
                 use stop=31-h)
Writes e3_TAG.json (status, bound, objective, witness), e3_TAG.log (solver log); a solution with objective
<= 30 met during search goes to e3_TAG_sol.json at once and is verified at the end (e5_verify.py).
"""
import json, os, sys, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2_model as M
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
t0 = time.time()
U = M.Universe(M.P89, strict=strict)
real7 = [i for i in M.W7 if i not in U.never]
if "w7l3" in kv:
    bm = int(kv["w7l3"])
    fix3 += [real7[k] for k in range(len(real7)) if bm >> k & 1]
    fix4 += [real7[k] for k in range(len(real7)) if not bm >> k & 1]
fix4 = sorted(set(fix4) | set(U.never))
ub = int(kv["ub"]) if "ub" in kv else None
N6 = set()
for i in U.never: N6 |= U.fan_inv[i]
N6 = set(s for s in N6 if s not in M.TSET)
allowed = N6 if kv.get("helpers") == "N6" else None
print(f"[{tag}] {U.info()} |N6|={len(N6)}", flush=True)
print(f"[{tag}] fix3={sorted(fix3)} fix4={fix4} ub={ub} strict={strict} helpers={kv.get('helpers','all')} "
      f"extra={ {k: v for k, v in kv.items() if k in ('sumx','sumxmin','sumxmax','hmin','pc5','m5','m5min','m5max','j','jmin','jmax','outN6max','noR2')} }", flush=True)

def extra(m, h):
    x, a, lvl3 = h["x"], h["a"], h["lvl3"]
    sx = sum(x.values())
    if "sumx" in kv: m.Add(sx == int(kv["sumx"]))
    if "sumxmin" in kv: m.Add(sx >= int(kv["sumxmin"]))
    if "sumxmax" in kv: m.Add(sx <= int(kv["sumxmax"]))
    if "hmin" in kv:
        m.Add(sum(a[s] for s in N6 if s in a) >= int(kv["hmin"]))
    if "outN6max" in kv:
        m.Add(sum(a[s] for s in h["helpers"] if s not in N6) <= int(kv["outN6max"]))
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

m, h = M.build(U, fix3=fix3, fix4=fix4, ub=ub, cuts=kv.get("cuts", "1") == "1", extra=extra,
               noR2=kv.get("noR2", "0") == "1", allowed=allowed)
dump_at = 30
if "hsum" in kv:                      # branch |H3| = hsum exactly
    m.Add(sum(h["a"][s] for s in h["helpers"]) == int(kv["hsum"]))
if kv.get("obj") == "x":              # objective |L2| only (with hsum fixed: closed iff bound >= 31 - hsum)
    m.Minimize(sum(h["x"].values()))
    dump_at = 30 - int(kv.get("hsum", 0))
print(f"[{tag}] model: x={len(h['x'])} a={len(h['a'])} helpers={len(h['helpers'])} cons-vars={h['ncv']} "
      f"recipe-vars={h['nr']} build {time.time()-t0:.1f}s", flush=True)
dump = os.path.join(HERE, f"e3_{tag}_sol.json")
res = M.solve(m, h, float(kv.get("time", 600)), workers=int(kv.get("workers", 1)), core=kv.get("core", "0") == "1",
              log=os.path.join(HERE, f"e3_{tag}.log"), lin=int(kv.get("lin", 1)), maxhs=kv.get("maxhs", "0") == "1",
              sub=kv.get("sub"), stop_at=float(kv["stop"]) if "stop" in kv else None, dump=dump, dump_at=dump_at)
res.update(tag=tag, fix3=sorted(fix3), fix4=fix4, ub=ub, strict=strict, args=kv, total_wall=time.time() - t0,
           core4=M.CORE4 if kv.get("sub") == "core4" else None)
target = 31 - int(kv["hsum"]) if kv.get("obj") == "x" else 31     # bound that closes the branch
closed = res["bound"] >= target - 1e-6 or res["status"] == "INFEASIBLE"
res["closed"] = closed; res["target"] = target
if "L2" in res: res["total"] = len(res["L2"]) + len(res["H3"])
print(f"[{tag}] status {res['status']} objective {res.get('objective')} bound {res['bound']} target {target} "
      f"wall {res['wall']:.1f}s closed={closed}", flush=True)
json.dump(res, open(os.path.join(HERE, f"e3_{tag}.json"), "w"))
cand = None
if "total" in res and res["total"] <= 30:
    cand = os.path.join(HERE, f"e3_{tag}.json")
elif os.path.exists(dump):
    cand = dump
if cand is not None:
    w = json.load(open(cand)); w["strict"] = strict
    json.dump(w, open(dump, "w"))
    print(f"[{tag}] !!!!! |L2|+|H3| = {len(w['L2']) + len(w['H3'])} <= 30: candidate <= 88-gate circuit, "
          f"verifying !!!!!", flush=True)
    out = subprocess.run([sys.executable, os.path.join(HERE, "e5_verify.py"), dump], capture_output=True, text=True)
    print(out.stdout, out.stderr, flush=True)
    with open(os.path.join(HERE, "FOUND_88AT4"), "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} tag {tag} "
                f"|L2|+|H3| {len(w['L2']) + len(w['H3'])}\n"
                f"{out.stdout}\n{out.stderr}\n")
