#!/usr/bin/env python3
"""Companion estimate on the cheap v3 signatures (hunt/sigs2.json, all 1,869 sampled 88 states).
Chains as sampling units (restart events, as landings.py); states that exist only as g88 records
(no sample t) are placed by wall time using the worker's wall - t offset from its samples.
Also: inverse-Simpson effective number D2 from cross-chain coincidences, for both the exact
catalogue and the signatures."""
import json, os, collections, math, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HUNT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt"
EST = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate"
sig = json.load(open(os.path.join(HUNT, "sigs2.json")))
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
h2p, PL = store["states"], store["plateaus"]

bounds = {}
for arm in sorted(os.listdir(os.path.join(HUNT, "runs"))):
    wdir = os.path.join(HUNT, "runs", arm, "workers")
    for w in sorted(os.listdir(wdir)):
        p = os.path.join(wdir, w, "events.jsonl")
        ts = []
        for line in open(p):
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("ev") == "restart":
                ts.append(e["t"])
        bounds[(arm, w)] = sorted(ts)


def chain_index(arm, w, t):
    ts = bounds.get((arm, w), [])
    return sum(1 for x in ts if x <= t)


tof, off = {}, collections.defaultdict(list)
for spth in ("samples.jsonl", "samplesC/samples.jsonl"):
    for line in open(os.path.join(HUNT, spth)):
        r = json.loads(line)
        if r.get("t") is not None:
            off[(r["arm"], r["worker"])].append(r["wall"] - r["t"])
            if r["gates"] == 88:
                tof.setdefault(r["hash"], r["t"])
offset = {k: sorted(v)[len(v) // 2] for k, v in off.items()}
inc = collections.defaultdict(set)
nrec = 0
for h, (s, arm, w, wall) in sig.items():
    t = tof.get(h)
    if t is None:
        t = wall - offset[(arm, w)]
        nrec += 1
    inc[s].add((arm, w, chain_index(arm, w, t)))
chains = {c for v in inc.values() for c in v}
T = len(chains)
ys = [len(v) for v in inc.values()]
Q = collections.Counter(ys)
S = len(inc)
U = sum(ys)
from estimate_lib import chao2, coverage, d2  # noqa: E402

out = []
P = lambda *a: out.append(" ".join(str(x) for x in a))
P("== 4. cheap v3 signatures (all sampled 88 states, arms A+B+C)")
P(f"states {len(sig)} (of which {nrec} placed by record wall time), signatures S={S}, chains T={T} "
  f"{dict(collections.Counter(a for a, _, _ in chains))}, incidences U={U}")
P("signature incidence counts Q_j:", dict(sorted(Q.items())))
for s, v in inc.items():
    if len(v) > 1:
        ks = {h2p.get(h) for h, x in sig.items() if x[0] == s}
        sz = sorted({PL[k]['size'] for k in ks if k}, reverse=True)
        P(f"  sig {s}: chains {sorted('/'.join(map(str, c)) for c in v)}; catalogued plateau sizes {sz}")
cc = chao2(S, Q[1], Q[2], T)
for k, v in cc.items():
    P(f"Chao2 {k}: N_sig = {v[0]:.0f}, 95% CI [{v[1]:.0f}, {v[2]:.0f}] (estimated, in signatures)")
P(f"coverage C_hat = {coverage(Q[1], Q[2], U, T):.4f}")
per_chain = collections.Counter(c for v in inc.values() for c in v)
D, lo, hi, pairs, coin = d2(inc, per_chain)
P(f"D2 (inverse Simpson, cross-chain coincidences {coin} of {pairs:,} pairs) = {D:.0f}, 95% CI [{lo:.0f}, {hi:.0f}]")
P("over-split factor (measured on 479 catalogued states, sig2.log): 230 exact -> 375 v3 signatures = 1.63x; "
  "a split also turns a would-be cross-chain repeat into two singletons, so N_sig is not simply N x 1.63")
P(f"naive deflation: Chao2 classic / 1.63 = {cc['classic'][0] / 1.63:.0f}")

# D2 for the exact catalogue
L = json.load(open(os.path.join(EST, "landings.json")))
inc2 = {r["key"]: {tuple(c.split("/")) for c in r["chain_ids"]} for r in L["rows"] if r["kind"] == "product"}
pc2 = collections.Counter(c for v in inc2.values() for c in v)
D, lo, hi, pairs, coin = d2(inc2, pc2)
P(f"\nexact catalogue D2 (product plateaus): cross-chain coincidences {coin} of {pairs:,} pairs -> D2 = {D:.0f}, "
  f"95% CI [{lo:.0f}, {hi:.0f}] (exact Poisson CI on the coincidence count)")
# clustered: count chain-pairs that coincide rather than plateau coincidences
cp = set()
for v in inc2.values():
    v = sorted(v)
    for i in range(len(v)):
        for j in range(i + 1, len(v)):
            cp.add((v[i], v[j]))
P(f"  coinciding chain pairs: {len(cp)} {sorted(('/'.join(a), '/'.join(b)) for a, b in cp)}")
print("\n".join(out))
open(os.path.join(EST, "sigs.out"), "w").write("\n".join(out) + "\n")
