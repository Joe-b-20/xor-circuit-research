#!/usr/bin/env python3
import json, os, hashlib
S = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint")
for rel in ["predtest/runs/pt1", "x1/runs/x1a", "sweep/runs/sw1"]:
    r = os.path.join(S, rel)
    plan = json.load(open(os.path.join(r, "plan.json")))
    print("==", rel, "plan.seeds:", json.dumps(plan["seeds"])[:1200])
    for w in plan["workers"][:4]:
        print(w["id"], w["seed"])
        ev = os.path.join(r, "workers", w["id"], "events.jsonl")
        with open(ev) as f:
            e = json.loads(f.readline())
        print("  start:", {k: e.get(k) for k in ("source", "root", "seed_sha256", "seed")})
    sd = os.path.join(r, "seeds")
    if os.path.isdir(sd):
        for f in os.listdir(sd):
            p = os.path.join(sd, f)
            if os.path.isfile(p):
                print("  seedfile", f, hashlib.sha256(open(p, "rb").read()).hexdigest()[:16])
            else:
                for g in os.listdir(p):
                    print("  seedfile", f + "/" + g, hashlib.sha256(open(os.path.join(p, g), "rb").read()).hexdigest()[:16])
