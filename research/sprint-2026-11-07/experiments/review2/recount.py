#!/usr/bin/env python3
"""Recompute F12 numbers from landing_table.txt / landings.json; sensitivity to giants and to clustering."""
import json, math, collections, sys
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate")
from estimate_lib import chao2, d2, pois_ci
rows = []
for l in open("/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate/landing_table.txt"):
    if l.startswith("#") or l.startswith("key"):
        continue
    p = l.split()
    rows.append({"key": p[0], "kind": p[1], "size": None if p[2] == "None" else int(p[2]), "chains": int(p[3]), "first": int(p[4])})
L = json.load(open("/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate/landings.json"))
T = L["T_chains"]
prod = [r for r in rows if r["kind"] == "product"]
Q = collections.Counter(r["chains"] for r in prod)
S = len(prod)
print(f"rows {len(rows)}, product {S}, T={T}, Q1={Q[1]}, Q2={Q[2]}, Q3+={sum(v for k, v in Q.items() if k > 2)}")
c = chao2(S, Q[1], Q[2], T)
print("Chao2 product only:", {k: tuple(round(x) for x in v) for k, v in c.items()})
Qa = collections.Counter(r["chains"] for r in rows)
c = chao2(len(rows), Qa[1], Qa[2], T)
print(f"Chao2 all 230 keys (giants as singletons): Q1={Qa[1]} Q2={Qa[2]}", {k: tuple(round(x) for x in v) for k, v in c.items()})
for extra in (1, 2, 3):
    c = chao2(len(rows) - extra, Qa[1] - 2 * extra, Qa[2] + extra, T)
    print(f"  if {extra} hidden giant repeat(s): Chao2 classic {c['classic'][0]:.0f} [{c['classic'][1]:.0f}, {c['classic'][2]:.0f}]")
inc = {r["key"]: set(r["chain_ids"]) for r in L["rows"] if r["kind"] == "product"}
pc = collections.Counter(cc for v in inc.values() for cc in v)
D, lo, hi, pairs, coin = d2(inc, pc)
print(f"D2 product: pairs {pairs:,.0f} coin {coin} D2 {D:,.0f} [{lo:,.0f}, {hi:,.0f}]")
met = collections.Counter()
for k, cs in inc.items():
    cs = sorted(cs)
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            met[(cs[i], cs[j])] += 1
print("chain pairs that met:", dict(met))
npairs_chain = T * (T - 1) // 2
k = len(met)
lo2, hi2 = pois_ci(k)
print(f"chain-pair meetings: {k} of {npairs_chain}; N_eff = pairs/meetings = {pairs / k:,.0f}, 95% [{pairs / hi2:,.0f}, {pairs / lo2:,.0f}]")
arms = collections.Counter(cc.split("/")[0] for cc in pc)
print("arm composition of catalogued chains:", dict(arms), "; incidences per chain sorted:", sorted(pc.values()))
g = [r for r in L["rows"] if r["kind"] != "product"]
print("giant/closure keys:", len(g), "from chains", dict(collections.Counter(cc for r in g for cc in r["chain_ids"])))
c0 = [cc for cc in pc if cc.endswith("/0")]
print("chain 0 (shared first roots across arms) among catalogued chains:", sorted(c0))
# how much of the alpha signal comes from the top-9 plateaus: incidences by size rank
prod_sorted = sorted(prod, key=lambda r: -r["size"])
print("top 12 by size (size, chains):", [(r["size"], r["chains"]) for r in prod_sorted[:12]])
# the alpha fit with the 18 giants added as singletons with hypothetical sizes
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate")
from sens import profile  # noqa: E402
base = [(r["chains"], math.log(r["size"])) for r in prod]
for gs in (3000, 3.0e4, 3.0e5, 3.0e6, 1.0e7):
    d = base + [(1, math.log(gs))] * len(g)
    a, lo_, hi_, lr0 = profile(d)
    print(f"alpha with 18 giants as singletons of size {gs:g}: alpha_hat {a:.2f} 95% [{lo_:.2f}, {hi_:.2f}], LR vs 0: {lr0:.2f}")
