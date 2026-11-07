#!/usr/bin/env python3
"""Identify the 88-gate plateaus reached by the hunt: every distinct 88 state in samples.jsonl
(and the g88 records) is compressed with the PES plateau compression (remove1-neutral closure
as core + independent factors), and plateaus are keyed modulo byte rotation.  Writes
plateaus.json (key -> first arm/worker/time, size, factor radices, members seen) and prints the
discovery curve per arm: new plateaus against 88-arrivals, in order of discovery.
Usage: plateaus.py HUNT_DIR [max_states]
"""
import glob, json, os, sys, time

HUNT = sys.argv[1]
MAXN = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402

sp = pes_lib.make_space("mc", None)
out_path = os.path.join(HUNT, "plateaus.json")
store = json.load(open(out_path)) if os.path.exists(out_path) else {"plateaus": {}, "states": {}}
P = store["plateaus"]
seen_states = store["states"]

# collect 88 states: samples first (time ordered), then records
cands = []
sp_path = os.path.join(HUNT, "samples.jsonl")
if os.path.exists(sp_path):
    for line in open(sp_path):
        r = json.loads(line)
        if r["gates"] == 88:
            cands.append((r["wall"], r["arm"], r["worker"], r["hash"], r["values"]))
for rec in sorted(glob.glob(os.path.join(HUNT, "runs", "*", "workers", "*", "records", "g88-*.json"))):
    parts = rec.split(os.sep)
    arm, w = parts[-5], parts[-3]
    d = json.load(open(rec))
    cands.append((os.path.getmtime(rec), arm, w, os.path.basename(rec)[:20], d["values"]))
cands.sort()

n_new = 0
t0 = time.time()
for wall, arm, w, h, values in cands:
    if h in seen_states:
        continue
    if n_new >= MAXN:
        break
    helpers = [v for v in values if v not in sp.tset]
    st = sp.state(helpers)
    if st.count() != 88:
        seen_states[h] = None
        continue
    hk = sp.hkey(st)
    # quick membership test against known plateaus (any rotation)
    found = None
    for s in sp.shifts:
        rk = sp.rot(hk, s) if s else hk
        S = frozenset(rk)
        for key, info in P.items():
            pl = pes_lib.Plateau.from_json(info["plateau"])
            if pl.contains(S):
                found = key
                break
        if found:
            break
    if found is None:
        pl, info = pes_lib.compress(sp, hk, verify_limit=20000, closure_limit=20000, time_limit=600)
        if info.get("downs"):
            print("DOWN EXIT FOUND", arm, w, h, info["downs"][:3], flush=True)
            with open(os.path.join(HUNT, "DOWN_EXITS.txt"), "a") as f:
                f.write(json.dumps({"arm": arm, "worker": w, "hash": h, "downs": [str(x) for x in info["downs"]]}) + "\n")
        allv = sorted(pl.allv) if pl.kind == "product" else sorted(set().union(*pl.states))
        key = min(sp.rot(tuple(allv), s) if s else tuple(allv) for s in sp.shifts)
        key = "p" + pes_lib.h64(key).to_bytes(8, "big").hex()
        if key not in P:
            P[key] = {"plateau": pl.to_json(), "size": pl.size(), "radices": pl.radices(),
                      "kind": pl.kind, "depth": st.depth(), "first": {"arm": arm, "worker": w, "wall": wall},
                      "members_seen": 0, "arms": {}}
            n_new += 1
        found = key
    P[found]["members_seen"] += 1
    P[found]["arms"][arm] = P[found]["arms"].get(arm, 0) + 1
    seen_states[h] = found
    if time.time() - t0 > 3000:
        break

json.dump(store, open(out_path + ".tmp", "w"))
os.replace(out_path + ".tmp", out_path)

print(f"states seen {len(seen_states)}, plateaus {len(P)}")
by_arm = {}
for key, info in P.items():
    by_arm.setdefault(info["first"]["arm"], []).append((info["first"]["wall"], key))
for arm, lst in sorted(by_arm.items()):
    lst.sort()
    print(f"  {arm}: {len(lst)} plateaus first seen here")
sizes = {}
for info in P.values():
    sizes[(info["kind"], info["size"])] = sizes.get((info["kind"], info["size"]), 0) + 1
print("  plateau sizes:", dict(sorted(sizes.items(), key=lambda kv: -kv[1])))
print("  radices:", sorted({tuple(info["radices"]) for info in P.values()}))
