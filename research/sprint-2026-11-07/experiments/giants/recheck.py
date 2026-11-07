#!/usr/bin/env python3
"""Membership re-check of every unresolved entry (any byte rotation) against all plateaus resolved
by resolve.py (pl_*.json) and all product plateaus of plateaus.json.  Updates resolve.jsonl
in place (hit -> resolved by membership), keeps the original record under 'first_attempt'."""
import glob, json, os, sys
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib
G = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants"
HUNT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt"
sp = pes_lib.make_space("mc", None)
P = json.load(open(os.path.join(HUNT, "plateaus.json")))["plateaus"]
cand = {k: pes_lib.Plateau.from_json(v["plateau"]) for k, v in P.items() if v["kind"] == "product"}
for f in glob.glob(os.path.join(G, "pl_*.json")):
    cand[os.path.basename(f)[3:-5]] = pes_lib.Plateau.from_json(json.load(open(f)))
E = {e["key"]: e for e in json.load(open(os.path.join(G, "entries.json")))}
recs = [json.loads(l) for l in open(os.path.join(G, "resolve.jsonl"))]
for r in recs:
    if r["resolved"]:
        continue
    S0 = frozenset(E[r["entry"]]["seed"])
    hit = None
    for s in sp.shifts:
        S = frozenset(sp.rot(tuple(sorted(S0)), s)) if s else S0
        for k, pl in cand.items():
            if pl.contains(S):
                hit = (k, s, pl)
                break
        if hit:
            break
    print(r["entry"], "->", hit[0] if hit else None, flush=True)
    if hit:
        k, s, pl = hit
        old = dict(r)
        r.clear()
        r.update(entry=old["entry"], chain=old["chain"], t_sample=old["t_sample"], resolved=True,
                 how="membership (recheck)", canon=k, shift=s, size=pl.size(), radices=pl.radices(),
                 in_catalogue=k in P, first_attempt=old)
with open(os.path.join(G, "resolve.jsonl.tmp"), "w") as f:
    for r in recs:
        f.write(json.dumps(r) + "\n")
os.replace(os.path.join(G, "resolve.jsonl.tmp"), os.path.join(G, "resolve.jsonl"))
