#!/usr/bin/env python3
"""Cheap plateau identity: one remove1 fan per 88 state.  sig(S) = (core, mobile) where mobile =
values moved by any neutral move at S (R u A over the fan) and core = S - mobile, canonical
modulo byte rotation.  For an exact product of 3-way factors every member sees the whole factor,
so the signature is constant on the plateau.  Validated against the exact catalogue
(plateaus.json: state hash -> plateau key), then applied to every sampled 88 state of every arm.
Usage: sig.py HUNT_DIR
"""
import glob, json, os, sys, time
HUNT = sys.argv[1]
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402
sp = pes_lib.make_space("mc", None)
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
seen = store["states"]


def canon(core, mobile):
    best = None
    for s in sp.shifts:
        c = tuple(sorted(sp.rot(tuple(sorted(core)), s))) if s else tuple(sorted(core))
        m = tuple(sorted(sp.rot(tuple(sorted(mobile)), s))) if s else tuple(sorted(mobile))
        k = (c, m)
        if best is None or k < best:
            best = k
    return pes_lib.h64(best)


def sig_of(values):
    helpers = [v for v in values if v not in sp.tset]
    st = sp.state(helpers)
    if st.count() != 88:
        return None, st.count()
    hk = sp.hkey(st)
    S = frozenset(hk)
    g, d, neutral, downs, binds = pes_lib.fan(sp, S)
    mobile = set()
    for R, A, k, dep in neutral:
        mobile |= R | A
    core = S - mobile
    return canon(core, mobile), (d, len(neutral), len(downs))


# states: samples (both files) + g88 records; one record per hash
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

t0 = time.time()
sigs = {}
downs_found = []
for h, (wall, arm, w, values) in states.items():
    s, extra = sig_of(values)
    if s is None:
        continue
    sigs[h] = (s, arm, w, wall, extra)
    if extra[2]:
        downs_found.append((arm, w, h))
print(f"fans done in {time.time() - t0:.0f} s; states with a down exit: {len(downs_found)}", flush=True)
if downs_found:
    print("DOWN EXITS:", downs_found[:10])

# validation against the exact catalogue
by_key, by_sig = {}, {}
for h, (s, arm, w, wall, extra) in sigs.items():
    key = seen.get(h)
    if key is None:
        continue
    by_key.setdefault(key, set()).add(s)
    by_sig.setdefault(s, set()).add(key)
multi_sig = {k: v for k, v in by_key.items() if len(v) > 1}
multi_key = {s: v for s, v in by_sig.items() if len(v) > 1}
n_val = sum(1 for h in sigs if seen.get(h))
print(f"validation: {n_val} catalogued states, {len(by_key)} exact plateaus, {len(by_sig)} signatures")
print(f"  exact plateaus with >1 signature: {len(multi_sig)} (sizes: {sorted(len(v) for v in multi_sig.values())[:20]})")
print(f"  signatures spanning >1 exact plateau: {len(multi_key)}")
kinds = {}
for k, v in multi_sig.items():
    kinds[store['plateaus'][k]['kind']] = kinds.get(store['plateaus'][k]['kind'], 0) + 1
print(f"  kinds of the split plateaus: {kinds}")

# application: distinct signatures per arm, overlap, per worker-hour (3 h x 6 workers each arm)
WH = {"A": 18.0, "B": 18.0, "C": 18.0}
per_arm = {}
for h, (s, arm, w, wall, extra) in sigs.items():
    per_arm.setdefault(arm, {}).setdefault(s, []).append((wall, w))
allsigs = {}
for arm, d in per_arm.items():
    for s in d:
        allsigs.setdefault(s, set()).add(arm)
print("arm  88-states  distinct-sigs  sigs/worker-h  shared-with-other-arms")
for arm in sorted(per_arm):
    d = per_arm[arm]
    n_states = sum(len(v) for v in d.values())
    shared = sum(1 for s in d if len(allsigs[s]) > 1)
    print(f"{arm}    {n_states:5d}      {len(d):5d}        {len(d) / WH.get(arm, 18):6.2f}        {shared}")
for arm in sorted(per_arm):
    items = sorted(((wall, w, s) for h, (s, a, w, wall, extra) in sigs.items() if a == arm))
    seen_s, curve = set(), []
    for i, (wall, w, s) in enumerate(items, 1):
        seen_s.add(s)
        if i in (50, 100, 200, 300, 400, 500, 600, 700, len(items)):
            curve.append((i, len(seen_s)))
    print(f"  {arm} discovery (states, distinct sigs): {curve}")
json.dump({h: [v[0], v[1], v[2], v[3]] for h, v in sigs.items()}, open(os.path.join(HUNT, "sigs.json"), "w"))
print("wrote sigs.json")
