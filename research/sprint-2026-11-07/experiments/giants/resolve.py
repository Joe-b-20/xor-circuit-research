#!/usr/bin/env python3
"""Step 2: exact identity/size of the 18 non-product keys with pes_lib.compress (raised limits).
Order: one seed per chain first, then the rest; before compressing, each seed is tested for
membership (any byte rotation) in every product plateau of plateaus.json and every plateau
resolved here.  A process-wide fan memo (pes_lib.fan wrapped) is shared across seeds.
Writes resolve.jsonl (one line per entry) incrementally."""
import json, os, sys, time
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib
G = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants"
HUNT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt"
VL, CL, TL = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3])
BUDGET = float(sys.argv[4])  # seconds: no new compress starts after this
sp = pes_lib.make_space("mc", None)
_fan = pes_lib.fan
MEMO = {}
def fan_memo(sp_, S, c=None):
    r = MEMO.get(S)
    if r is None:
        if len(MEMO) > 400000:
            MEMO.clear()
        r = _fan(sp_, S)
        MEMO[S] = r
    return r
pes_lib.fan = fan_memo

def key_of(pl):
    allv = sorted(pl.allv) if pl.kind == "product" else sorted(set().union(*pl.states))
    k = min(sp.rot(tuple(allv), s) if s else tuple(allv) for s in sp.shifts)
    return "p" + pes_lib.h64(k).to_bytes(8, "big").hex()

store = json.load(open(os.path.join(HUNT, "plateaus.json")))
P = store["plateaus"]
known = {k: pes_lib.Plateau.from_json(v["plateau"]) for k, v in P.items() if v["kind"] == "product"}
print("product plateaus loaded:", len(known), flush=True)
E = json.load(open(os.path.join(G, "entries.json")))
first, rest, seenc = [], [], set()
for e in E:
    c = e["chains"][0]
    (rest if c in seenc else first).append(e)
    seenc.add(c)
order = first + rest
resolved = {}   # key -> Plateau (resolved here)
done = set()
import glob
for f in glob.glob(os.path.join(G, "pl_*.json")):
    resolved[os.path.basename(f)[3:-5]] = pes_lib.Plateau.from_json(json.load(open(f)))
outp = os.path.join(G, "resolve.jsonl")
if os.path.exists(outp):
    for line in open(outp):
        done.add(json.loads(line)["entry"])
T0 = time.time()

def member(S0):
    for s in sp.shifts:
        S = frozenset(sp.rot(tuple(sorted(S0)), s) if s else S0)
        for k, pl in list(resolved.items()) + list(known.items()):
            if pl.contains(S):
                return k, s
    return None, None

for e in order:
    if e["key"] in done:
        continue
    S0 = frozenset(e["seed"])
    rec = {"entry": e["key"], "chain": e["chains"][0], "t_sample": e["samples"][0][2]}
    k, s = member(S0)
    if k:
        pl = resolved.get(k) or known[k]
        rec.update(resolved=True, how="membership", canon=k, shift=s, size=pl.size(), radices=pl.radices(),
                   in_catalogue=k in known)
    elif time.time() - T0 > BUDGET:
        rec.update(resolved=False, how="skipped: wall budget exhausted")
    else:
        t = time.time()
        pl, info = pes_lib.compress(sp, tuple(sorted(S0)), verify_limit=VL, closure_limit=CL, time_limit=TL)
        info.pop("downs", None)
        rec["info"] = {k2: v for k2, v in info.items() if k2 != "depth_hist"}
        rec["seconds"] = round(time.time() - t, 1)
        if pl.kind == "product":
            key = key_of(pl)
            rec.update(resolved=True, how="compress-" + str(info.get("verified")), canon=key, size=pl.size(),
                       radices=pl.radices(), in_catalogue=key in known)
            resolved.setdefault(key, pl)
            json.dump(pl.to_json(), open(os.path.join(G, "pl_" + key + ".json"), "w"))
        elif info.get("verified") == "closure-complete":
            key = key_of(pl)
            rec.update(resolved=True, how="closure-complete", canon=key, size=pl.size(), radices=[], in_catalogue=key in P)
            resolved.setdefault(key, pl)
        else:
            rec.update(resolved=False, how=str(info.get("verified")) + "; " + str(info.get("note")),
                       closure_states=pl.size())
    rec["wall"] = round(time.time() - T0, 1)
    print(json.dumps(rec), flush=True)
    with open(outp, "a") as f:
        f.write(json.dumps(rec) + "\n")
print("DONE", round(time.time() - T0), "s; memo", len(MEMO), flush=True)
