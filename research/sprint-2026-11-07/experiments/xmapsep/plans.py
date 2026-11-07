#!/usr/bin/env python3
import json, os, sys
XS = os.path.expanduser("~/xs-campaigns")
for r in ["2026-10-28/runs/fox_mu8", "2026-10-29/runs/fox_mu8", "2026-10-30-gap/run", "2026-10-31-long/runs/gaps16",
          "2026-10-31-long/runs/wide64", "2026-10-30-nist/runs/nist-batch-64", "2026-10-30-nist/runs/nist-grostl"]:
    print("==", r)
    p = json.load(open(os.path.join(XS, r, "plan.json")))
    print(p.get("name"), p.get("created_utc"), p.get("duration"), "workers", len(p.get("workers", [])), "groups", len(p.get("groups", [])))
    for w in (p.get("workers") or [])[:3]:
        print({k: w.get(k) for k in ("id", "target", "depth_cap", "group")})
    for g in p.get("groups", [])[:6]:
        print({k: g.get(k) for k in ("name", "target", "depth_cap", "count", "seeds")})
    # sessions: wall time
    sd = os.path.join(XS, r, "sessions")
    if os.path.isdir(sd):
        for f in os.listdir(sd):
            try:
                s = json.load(open(os.path.join(sd, f)))
                print("session", {k: s.get(k) for k in ("started_utc", "stopped_utc", "wall_s", "elapsed_s", "duration") if k in s})
            except Exception as e:
                print("session?", f, e)
