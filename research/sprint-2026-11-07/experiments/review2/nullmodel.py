#!/usr/bin/env python3
"""Null model for F11: chains wander independently; each chain visits n_c distinct nodes drawn
uniformly from N nodes.  Expected number of nodes entered by >=2 chains ~ sum_{c<c"} n_c n_c" / N
(exact: sum over nodes of P(>=2 chains) computed by Monte Carlo too).  Compare with the 8 observed.
Also compute the node-level D2 (visits) analogue of F12 directly from graph_data.json."""
import json, collections, math, random
G = json.load(open("/home/joebachir20/xs-campaigns/2026-11-07-sprint/graph/graph_data.json"))
hops = G["hops"]
nodes_of_chain = collections.defaultdict(set)
for h in hops:
    ck = tuple(h["chain"])
    nodes_of_chain[ck].add(h["u"]); nodes_of_chain[ck].add(h["v"])
# chains with a single node (no hops) are missing from hops: 7 isolated nodes per report; add from nodes list
seen = set().union(*nodes_of_chain.values())
iso = [n for n in G["nodes"] if n not in seen]
print("chains with hops:", len(nodes_of_chain), "; nodes in hops:", len(seen), "; isolated nodes (one-node chains):", len(iso))
n = [len(s) for s in nodes_of_chain.values()] + [1] * len(iso)
V = sum(n); S2 = sum(x * x for x in n)
pairs = (V * V - S2) / 2
chains_of_node = collections.defaultdict(set)
for ck, s in nodes_of_chain.items():
    for x in s: chains_of_node[x].add(ck)
shared = [x for x, cs in chains_of_node.items() if len(cs) > 1]
coin = sum(len(cs) * (len(cs) - 1) / 2 for cs in chains_of_node.values())
print(f"chains {len(n)}, total distinct-node incidences V={V}, sum n_c^2={S2}, cross-chain incidence pairs={pairs:,.0f}")
print(f"observed nodes entered by >=2 chains: {len(shared)}; coincident pairs: {coin:.0f}")
print(f"node-level D2 = pairs/coin = {pairs / coin:,.0f}  (effective number of equally likely nodes, visits incl. hops)")
print("\nExpected shared nodes if chains wander independently and uniformly over N nodes:")
for N in (1454, 2500, 7300, 2e4, 5e4, 1e5, 1.6e5, 2.5e5, 4e5):
    approx = pairs / N
    # exact-ish: E[#nodes with >=2 chains] = N * P(>=2 of the chains hit a given node); P(chain c hits node) = n_c/N
    p = [x / N for x in n]
    # P(no chain) and P(exactly one)
    lp0 = sum(math.log1p(-q) for q in p)
    p0 = math.exp(lp0)
    p1 = sum(q / (1 - q) for q in p) * p0
    exact = N * (1 - p0 - p1)
    # Poisson probability of observing <= 8 given mean exact
    mu = exact
    cdf = sum(math.exp(-mu) * mu ** i / math.factorial(i) for i in range(9))
    print(f"  N={N:>9,.0f}: E[shared nodes] = {exact:7.1f} (pairs/N = {approx:7.1f});  P(<= 8 observed | N) = {cdf:.3g}")
# Monte Carlo at N=1e5 to validate
random.seed(1)
N = 100000; reps = 200; tot = 0
for _ in range(reps):
    cnt = collections.Counter()
    for x in n:
        for v in random.sample(range(N), x): cnt[v] += 1
    tot += sum(1 for v in cnt.values() if v > 1)
print(f"Monte Carlo N=1e5: mean shared nodes {tot / reps:.1f}")
