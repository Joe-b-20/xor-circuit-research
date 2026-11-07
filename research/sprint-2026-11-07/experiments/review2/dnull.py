#!/usr/bin/env python3
"""(1) Same-root chain-0 trajectories across arms A/B/C (are they identical?).
(2) Hunt D snapshot: chains, v3 nodes (samplesD/sigs.json if usable), cross-chain shared nodes
observed vs the null model (independent uniform wandering over N_eff nodes)."""
import json, os, collections, math
HUNT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt"

print("== (1) chain 0 of free-00 in arms A, B, C: first improve events (t, gates) and restarts")
for arm in "ABC":
    ev = [json.loads(l) for l in open(f"{HUNT}/runs/{arm}/workers/free-00/events.jsonl") if l.strip()]
    imp = [(round(e["t"], 1), e.get("gates", e.get("level"))) for e in ev if e["ev"] == "improve"][:10]
    rs = [round(e["t"], 1) for e in ev if e["ev"] == "restart"][:3]
    print(f"  {arm}: improves {imp}; restarts {rs}")

print("\n== (2) hunt D snapshot")
sig_path = f"{HUNT}/samplesD/sigs.json"
sigs = json.load(open(sig_path)) if os.path.exists(sig_path) else {}
k0 = next(iter(sigs)) if sigs else None
print("sigs.json entries:", len(sigs), "example:", k0, sigs.get(k0) if k0 else None)
restarts = {}
for arm in sorted(os.listdir(f"{HUNT}/runsD")):
    wdir = f"{HUNT}/runsD/{arm}/workers"
    if not os.path.isdir(wdir):
        continue
    for w in sorted(os.listdir(wdir)):
        p = f"{wdir}/{w}/events.jsonl"
        if not os.path.exists(p):
            continue
        ts = []
        for line in open(p):
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("ev") == "restart":
                ts.append(e["t"])
        restarts[(arm, w)] = sorted(ts)


def chain_index(arm, w, t):
    ts = restarts.get((arm, w), [])
    i = 0
    while i < len(ts) and ts[i] <= t:
        i += 1
    return i


def node_of(r):
    s = sigs.get(r["hash"])
    if s is None:
        return None
    return s[0] if isinstance(s, list) else s


nodes_of_chain = collections.defaultdict(set)
n88 = 0
nosig = 0
for line in open(f"{HUNT}/samplesD/samples.jsonl"):
    r = json.loads(line)
    if r["gates"] != 88:
        continue
    n88 += 1
    nd = node_of(r)
    if nd is None:
        nosig += 1
        continue
    nodes_of_chain[(r["arm"], r["worker"], chain_index(r["arm"], r["worker"], r["t"] or 0))].add(nd)
print(f"88 samples {n88}, without signature {nosig}, chains with 88 nodes {len(nodes_of_chain)}")
n = [len(s) for s in nodes_of_chain.values()]
V = sum(n)
pairs = (V * V - sum(x * x for x in n)) / 2
chains_of_node = collections.defaultdict(set)
for ck, s in nodes_of_chain.items():
    for x in s:
        chains_of_node[x].add(ck)
shared = {x: cs for x, cs in chains_of_node.items() if len(cs) > 1}
across_arm = sum(1 for cs in shared.values() if len({c[0] for c in cs}) > 1)
print(f"distinct nodes {len(chains_of_node)}, incidences {V}, cross-chain pairs {pairs:,.0f}, shared nodes {len(shared)} (across arms {across_arm})")
for N in (2500, 7300, 5e4, 1.3e5, 2.5e5):
    print(f"  null model N={N:>9,.0f}: expected shared nodes {pairs / N:6.1f}")
if shared:
    print("  observed shared nodes imply N_eff ~", f"{pairs / len(shared):,.0f}")
