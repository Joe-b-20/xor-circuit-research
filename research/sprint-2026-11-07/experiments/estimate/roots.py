#!/usr/bin/env python3
"""Root kind of each catalogued chain (first epoch of the chain_index-th chain), to check whether
chains that share a plateau also share a (deterministic) root construction."""
import json, os
HUNT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt"
L = json.load(open("/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate/landings.json"))
out = {}
for cid in L["chains"]:
    arm, w, i = cid.split("/")
    p = os.path.join(HUNT, "runs", arm, "workers", w, "events.jsonl")
    chains, roots = [], {}
    for line in open(p):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("ev") == "epoch":
            c = e.get("engine_chain")
            if c not in roots:
                roots[c] = (e.get("root"), e.get("root_seed") or e.get("seed"))
                chains.append(c)
    i = int(i)
    out[cid] = (chains[i] if i < len(chains) else None, roots.get(chains[i]) if i < len(chains) else None)
for cid in sorted(out):
    print(cid, out[cid], len(L["chains"][cid]))
# one epoch example
for line in open(os.path.join(HUNT, "runs", "C", "workers", "free-00", "events.jsonl")):
    e = json.loads(line)
    if e.get("ev") == "epoch":
        print({k: v for k, v in e.items() if k not in ("env",)})
        break
