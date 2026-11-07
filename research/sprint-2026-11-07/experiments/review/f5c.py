#!/usr/bin/env python3
"""Review check for F5's migration reading and F2 over the hunt catalogue.
(a) Along each worker's sampled 88 states (time order, chain boundaries from restart events),
    the Jaccard similarity (mod rotation) between consecutive DISTINCT plateaus: is a 'hop'
    a new core or a 2-value re-pairing?  (b) For every product plateau in plateaus.json: do all
    3-choice single-value factors XOR to zero?  Usage: f5c.py HUNT_DIR"""
import json, os, sys, collections

HUNT = sys.argv[1]
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402

sp = pes_lib.make_space("mc", None)
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
P, h2p = store["plateaus"], store["states"]


def allvals(pj):
    vals = set(pj.get("core") or [])
    for fac in pj.get("factors") or []:
        for ch in fac["choices"]:
            vals |= set(ch)
    for s in pj.get("states") or []:
        vals |= set(s)
    return vals


V = {k: allvals(P[k]["plateau"]) for k in P}
rotV = {k: [set(sp.rot(tuple(V[k]), s)) if s else V[k] for s in sp.shifts] for k in P}


def jac(a, b):
    A = V[a]
    return max(len(A & B) / len(A | B) for B in rotV[b])


# restart times per (arm, worker)
bounds = {}
for arm in os.listdir(os.path.join(HUNT, "runs")):
    wdir = os.path.join(HUNT, "runs", arm, "workers")
    if not os.path.isdir(wdir):
        continue
    for w in os.listdir(wdir):
        ts = []
        p = os.path.join(wdir, w, "events.jsonl")
        if os.path.exists(p):
            for line in open(p):
                if '"ev":"restart"' in line:
                    try:
                        ts.append(json.loads(line)["t"])
                    except Exception:
                        pass
        bounds[(arm, w)] = sorted(ts)


def chain_idx(arm, w, t):
    return sum(1 for x in bounds.get((arm, w), []) if x <= t)


seq = collections.defaultdict(list)
for sp_path in (os.path.join(HUNT, "samples.jsonl"), os.path.join(HUNT, "samplesC", "samples.jsonl")):
    if os.path.exists(sp_path):
        for line in open(sp_path):
            r = json.loads(line)
            if r["gates"] != 88:
                continue
            k = h2p.get(r["hash"])
            if not k:
                continue
            seq[(r["arm"], r["worker"], chain_idx(r["arm"], r["worker"], r["t"]))].append((r["t"], k))

trans = collections.defaultdict(list)
per_chain = []
for (arm, w, c), lst in seq.items():
    lst.sort()
    keys = [k for _, k in lst]
    distinct = []
    for k in keys:
        if not distinct or distinct[-1] != k:
            distinct.append(k)
    nd = len(set(keys))
    per_chain.append((arm, w, c, len(keys), nd, len(distinct) - 1))
    for a, b in zip(distinct, distinct[1:]):
        trans[arm].append(jac(a, b))
for arm in sorted(trans):
    xs = sorted(trans[arm])
    n = len(xs)
    hist = collections.Counter(round(x, 1) for x in xs)
    print(f"arm {arm}: {n} transitions between consecutive distinct plateaus; Jaccard histogram {dict(sorted(hist.items()))}; "
          f"median {xs[n//2]:.2f}; share >= 0.9: {sum(1 for x in xs if x >= 0.9)/n:.2f}; share < 0.7: {sum(1 for x in xs if x < 0.7)/n:.2f}")
big = sorted(per_chain, key=lambda x: -x[4])[:6]
print("chains with most distinct plateaus (arm, worker, chain, samples, distinct, transitions):", big)

# (b) F2 over all product plateaus
n3 = bad = coupled = 0
for k, v in P.items():
    if v["kind"] != "product":
        continue
    for fac in v["plateau"]["factors"]:
        ch = fac["choices"]
        if len(ch) == 3 and all(len(c) == 1 for c in ch):
            n3 += 1
            if ch[0][0] ^ ch[1][0] ^ ch[2][0] != 0:
                bad += 1
        else:
            coupled += 1
print(f"F2 check over {sum(1 for v in P.values() if v['kind']=='product')} product plateaus: 3-way single-value factors {n3}, "
      f"XOR != 0: {bad}; other (coupled) factors {coupled}")
