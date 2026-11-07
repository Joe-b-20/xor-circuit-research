#!/usr/bin/env python3
"""Hunt D/E analysis: per arm, 88 states sampled, distinct cheap-identity (v3) signatures per
worker-hour, per-worker pairing across arms (same campaign seed -> same first roots), depth
distribution of 88 states, and any state below 88.
Usage: sigD.py RUNS_DIR SAMPLES_JSONL [HOURS_PER_ARM]   (e.g. runsD samplesD/samples.jsonl 13)
"""
import glob, json, os, sys, time
RUNS, SAMPLES = sys.argv[1], sys.argv[2]
HOURS = float(sys.argv[3]) if len(sys.argv) > 3 else 13.0
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402
sp = pes_lib.make_space("mc", None)
TGT = 88


def canon_set(vals):
    vals = tuple(sorted(vals))
    best = None
    for s in sp.shifts:
        k = tuple(sorted(sp.rot(vals, s))) if s else vals
        if best is None or k < best:
            best = k
    return pes_lib.h64(best)


def sig_of(values):
    helpers = [v for v in values if v not in sp.tset]
    st = sp.state(helpers)
    if st.count() != TGT:
        return None
    S = frozenset(sp.hkey(st))
    g, d, neutral, downs, binds = pes_lib.fan(sp, S)
    added = set()
    for R, A, k, dep in neutral:
        added |= A
    return canon_set(S | added), d, len(downs)


states, below = {}, []
if os.path.exists(SAMPLES):
    for line in open(SAMPLES):
        r = json.loads(line)
        if r["gates"] < TGT:
            below.append((r["arm"], r["worker"], r["gates"], r["hash"]))
        if r["gates"] == TGT and r["hash"] not in states:
            states[r["hash"]] = (r["wall"], r["arm"], r["worker"], r["values"])
for rec in sorted(glob.glob(os.path.join(RUNS, "*", "workers", "*", "records", "g*.json"))):
    parts = rec.split(os.sep)
    arm, w = parts[-5], parts[-3]
    base = os.path.basename(rec)
    g = int(base.split("-")[0][1:])
    if g < TGT:
        below.append((arm, w, g, base))
    if g != TGT:
        continue
    h = base[:20]
    if h in states:
        continue
    d = json.load(open(rec))
    if d.get("values"):
        values = d["values"]
    elif d.get("circuit"):
        c = d["circuit"]
        masks = [1 << i for i in range(c["inputCount"])]
        for a, b in c["gates"]:
            masks.append(masks[a] ^ masks[b])
        values = masks[c["inputCount"]:]
    else:
        continue
    states[h] = (os.path.getmtime(rec), arm, w, values)
print(f"{time.strftime('%H:%M:%SZ', time.gmtime())}  {TGT} states: {len(states)}; states below {TGT}: {len(below)}", flush=True)
for b in below[:20]:
    print("  BELOW:", b)

t0 = time.time()
sig = {}
for h, (wall, arm, w, values) in states.items():
    o = sig_of(values)
    if o:
        sig[h] = (o[0], arm, w, wall, o[1], o[2])
print(f"fans done in {time.time() - t0:.0f} s", flush=True)

arms = sorted({a for _, a, _, _, _, _ in sig.values()} | {os.path.basename(p) for p in glob.glob(os.path.join(RUNS, "*")) if os.path.isdir(p)})
WH = {}
for arm in arms:
    plan = os.path.join(RUNS, arm, "plan.json")
    start = os.path.getmtime(plan) if os.path.exists(plan) else time.time()
    nw = len(glob.glob(os.path.join(RUNS, arm, "workers", "*")))
    WH[arm] = nw * (min(time.time(), start + HOURS * 3600) - start) / 3600
per_arm = {a: {} for a in arms}
for h, (s, arm, w, wall, d, nd) in sig.items():
    per_arm[arm].setdefault(s, []).append((wall, w, d))
allsigs = {}
for arm in arms:
    for s in per_arm[arm]:
        allsigs.setdefault(s, set()).add(arm)
print("arm  worker-h  88-states  distinct(v3)  distinct/worker-h  shared-with-other-arms  depth-dist")
for arm in arms:
    d = per_arm[arm]
    n_states = sum(len(v) for v in d.values())
    shared = sum(1 for s in d if len(allsigs[s]) > 1)
    dd = {}
    for v in d.values():
        for wall, w, dep in v:
            dd[dep] = dd.get(dep, 0) + 1
    wh = WH[arm] or 1e-9
    print(f"{arm}  {WH[arm]:6.2f}  {n_states:6d}  {len(d):6d}  {len(d) / wh:8.2f}  {shared:4d}  {dict(sorted(dd.items()))}")
print("per worker (distinct v3 signatures), paired across arms by worker name:")
workers = sorted({w for v in sig.values() for w in [v[2]]})
print("worker  " + "  ".join(f"{a:>6s}" for a in arms))
for w in workers:
    row = []
    for arm in arms:
        row.append(len({s for s, v in per_arm[arm].items() if any(x[1] == w for x in v)}))
    print(f"{w:7s} " + "  ".join(f"{n:6d}" for n in row))
for arm in arms:
    items = sorted(((wall, w, s) for h, (s, a, w, wall, d, nd) in sig.items() if a == arm))
    seen_s, curve = set(), []
    for i, (wall, w, s) in enumerate(items, 1):
        seen_s.add(s)
        if i % 100 == 0 or i == len(items):
            curve.append((i, len(seen_s)))
    print(f"  {arm} discovery (states, distinct v3): {curve}")
multi = {}
for h, (s, a, w, wall, d, nd) in sig.items():
    multi.setdefault(s, set()).add((a, w))
rep = {s: v for s, v in multi.items() if len(v) > 1}
print(f"signatures seen by more than one (arm, worker): {len(rep)} of {len(multi)}")
for s, v in list(rep.items())[:10]:
    print("  ", s, sorted(v))
out = os.path.join(os.path.dirname(SAMPLES) or ".", "sigs.json")
json.dump({h: [v[0], v[1], v[2], v[3], v[4]] for h, v in sig.items()}, open(out, "w"))
print("wrote", out)
