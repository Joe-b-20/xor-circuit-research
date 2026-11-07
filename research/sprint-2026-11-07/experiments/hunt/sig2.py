#!/usr/bin/env python3
"""Cheap plateau identity, version 2: compare identities on the catalogued states and apply the
best to all sampled 88 states.
  v1 = (core, mobile) as in sig.py
  v2 = core only (S minus values moved by any neutral move at S)
  v3 = S plus every value added by a neutral move at S (the 1-step neutral closure's value set;
       for a product of 3-way triangles this is the plateau's whole value set)
  v4 = v3 applied twice (2-step closure's value set), validation set only
All modulo byte rotation.  Writes sigs2.json (hash -> [v3 sig, arm, worker, wall]).
Usage: sig2.py HUNT_DIR
"""
import glob, json, os, sys, time
HUNT = sys.argv[1]
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402
sp = pes_lib.make_space("mc", None)
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
seen = store["states"]
sizes = {k: v["size"] for k, v in store["plateaus"].items()}


def canon_set(vals):
    vals = tuple(sorted(vals))
    best = None
    for s in sp.shifts:
        k = tuple(sorted(sp.rot(vals, s))) if s else vals
        if best is None or k < best:
            best = k
    return pes_lib.h64(best)


fan_cache = {}


def fan(S):
    r = fan_cache.get(S)
    if r is None:
        g, d, neutral, downs, binds = pes_lib.fan(sp, S)
        r = (d, [(R, A) for R, A, k, dep in neutral], len(downs))
        fan_cache[S] = r
    return r


def sigs_of(values, two_step=False):
    helpers = [v for v in values if v not in sp.tset]
    st = sp.state(helpers)
    if st.count() != 88:
        return None
    S = frozenset(sp.hkey(st))
    d, neutral, nd = fan(S)
    mobile, added = set(), set()
    nbrs = []
    for R, A in neutral:
        mobile |= R | A
        added |= A
        nbrs.append((S - R) | A)
    core = S - mobile
    out = {"v1": pes_lib.h64((canon_set(core), canon_set(mobile))), "v2": canon_set(core),
           "v3": canon_set(S | added), "depth": d, "downs": nd, "nn": len(neutral)}
    if two_step:
        all2 = set(S | added)
        for N in nbrs:
            _, nb2, _ = fan(N)
            for R, A in nb2:
                all2 |= A
        out["v4"] = canon_set(all2)
    return out


states = {}
for sp_path in (os.path.join(HUNT, "samples.jsonl"), os.path.join(HUNT, "samplesC", "samples.jsonl")):
    if os.path.exists(sp_path):
        for line in open(sp_path):
            r = json.loads(line)
            if r["gates"] == 88 and r["hash"] not in states:
                states[r["hash"]] = (r["wall"], r["arm"], r["worker"], r["values"])
for rec in sorted(glob.glob(os.path.join(HUNT, "runs", "*", "workers", "*", "records", "g88-*.json"))):
    parts = rec.split(os.sep)
    arm, w = parts[-5], parts[-3]
    h = os.path.basename(rec)[:20]
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
print(f"88 states: {len(states)}", flush=True)

# validation on catalogued states (v1-v4)
t0 = time.time()
val = {}
for h, (wall, arm, w, values) in states.items():
    if seen.get(h):
        o = sigs_of(values, two_step=True)
        if o:
            val[h] = o
print(f"validation fans done in {time.time() - t0:.0f} s on {len(val)} states", flush=True)
for v in ("v1", "v2", "v3", "v4"):
    by_key, by_sig = {}, {}
    for h, o in val.items():
        by_key.setdefault(seen[h], set()).add(o[v])
        by_sig.setdefault(o[v], set()).add(seen[h])
    split = {k: s for k, s in by_key.items() if len(s) > 1}
    merged = {s: k for s, k in by_sig.items() if len(k) > 1}
    big = sum(1 for k in split if sizes.get(k, 0) > 100000)
    print(f"{v}: {len(by_key)} exact plateaus -> {len(by_sig)} signatures; split {len(split)} "
          f"(of which size>1e5: {big}); merged {len(merged)}")

# application with v3 to all states
t0 = time.time()
sig = {}
for h, (wall, arm, w, values) in states.items():
    o = sigs_of(values)
    if o:
        sig[h] = (o["v3"], arm, w, wall, o["depth"])
print(f"all fans done in {time.time() - t0:.0f} s", flush=True)
WH = {"A": 16.5, "B": 28.6, "C": 18.0}   # worker-hours actually delivered (review f1_load.py)
per_arm = {}
for h, (s, arm, w, wall, d) in sig.items():
    per_arm.setdefault(arm, {}).setdefault(s, []).append((wall, w))
allsigs = {}
for arm, d in per_arm.items():
    for s in d:
        allsigs.setdefault(s, set()).add(arm)
print("arm  88-states  distinct(v3)  per-worker-h  shared-with-other-arms  depth-dist")
for arm in sorted(per_arm):
    d = per_arm[arm]
    n_states = sum(len(v) for v in d.values())
    shared = sum(1 for s in d if len(allsigs[s]) > 1)
    dd = {}
    for h, (s, a, w, wall, dep) in sig.items():
        if a == arm:
            dd[dep] = dd.get(dep, 0) + 1
    print(f"{arm}    {n_states:5d}      {len(d):5d}        {len(d) / WH[arm]:6.2f}        {shared}   {dict(sorted(dd.items()))}")
for arm in sorted(per_arm):
    items = sorted(((wall, w, s) for h, (s, a, w, wall, dep) in sig.items() if a == arm))
    seen_s, curve = set(), []
    for i, (wall, w, s) in enumerate(items, 1):
        seen_s.add(s)
        if i in (100, 200, 300, 400, 500, 600, 700, len(items)):
            curve.append((i, len(seen_s)))
    print(f"  {arm} discovery (states, distinct v3): {curve}")
# repeats across chains: signatures seen by >1 (arm, worker) pair
multi = {s: sorted({(a, w) for a, w in [(x[1], x[2]) for x in [sig[h] for h in sig if sig[h][0] == s]]})
         for s in allsigs}
rep = {s: v for s, v in multi.items() if len(v) > 1}
print(f"signatures seen by more than one worker: {len(rep)} of {len(allsigs)}")
json.dump({h: [v[0], v[1], v[2], v[3]] for h, v in sig.items()}, open(os.path.join(HUNT, "sigs2.json"), "w"))
print("wrote sigs2.json")
