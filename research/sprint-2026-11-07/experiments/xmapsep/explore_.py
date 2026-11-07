#!/usr/bin/env python3
"""Explore run structure: plan.json workers, status.json, event kinds, restart events."""
import json, os, collections, sys
S = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint")
RUNS = {"x1a": "x1/runs/x1a", "x1b": "x1/runs/x1b", "pt1": "predtest/runs/pt1", "pt2": "predtest/runs/pt2",
        "sw1": "sweep/runs/sw1", "sw2": "sweep/runs/sw2"}
r = os.path.join(S, RUNS["sw2"])
plan = json.load(open(os.path.join(r, "plan.json")))
print("plan keys", list(plan.keys()))
w0 = plan["workers"][0]
print("worker plan entry", json.dumps(w0)[:1500])
print("campaign", json.dumps({k: v for k, v in plan.items() if k != "workers"})[:1500])
wd = os.path.join(r, "workers", "klsw17-m-8x8-gf256-00")
print("status", open(os.path.join(wd, "status.json")).read()[:1500])
print("recorder", open(os.path.join(wd, "recorder.json")).read()[:800])
c = collections.Counter()
restarts = []
imps = []
for line in open(os.path.join(wd, "events.jsonl")):
    e = json.loads(line)
    c[e["ev"]] += 1
    if e["ev"] in ("restart", "chain", "root", "seed"):
        restarts.append(e)
    if e["ev"] == "improve":
        imps.append((round(e["t"]), e["before"], e["after"], e["kind"], e["move"], e.get("root_source"), e["chain"]))
print(c)
for e in restarts[:6]:
    print(json.dumps(e)[:600])
print("n improves", len(imps))
for i in imps:
    print(i)
# last events
lines = open(os.path.join(wd, "events.jsonl")).read().splitlines()
for l in lines[-3:]:
    print(l[:500])
print("sessions", os.listdir(os.path.join(r, "sessions")))
print("campaign.jsonl tail")
for l in open(os.path.join(r, "campaign.jsonl")).read().splitlines()[-5:]:
    print(l[:400])
