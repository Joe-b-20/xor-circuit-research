#!/usr/bin/env python3
"""Follow-up on graph_data.json: (a) hops whose both endpoints are exactly catalogued, split by
sampled-89 count (are 0-sample hops genuine plateau changes?); (b) the multi-chain components.
Usage: followup.py OUT_DIR"""
import collections, json, sys
OUT = sys.argv[1]
G = json.load(open(OUT + "/graph_data.json"))
hops = G["hops"]
both = [h for h in hops if h["u"].startswith("key:") and h["v"].startswith("key:")]
print(f"hops with both endpoints exactly catalogued (distinct exact plateaus by construction): {len(both)} of {len(hops)}")
print("  sampled-89 count among them:", sorted(collections.Counter(h["exc_samples"] for h in both).items()))
print("  Jaccard (helpers) 0-sample:", sorted(round(h["jac_h"], 2) for h in both if h["exc_samples"] == 0)[:40])
one = [h for h in hops if h["u"].startswith("key:") != h["v"].startswith("key:")]
none = [h for h in hops if not h["u"].startswith("key:") and not h["v"].startswith("key:")]
for name, hs in (("one end catalogued", one), ("neither end catalogued", none)):
    c = collections.Counter(h["exc_samples"] > 0 for h in hs)
    print(f"  {name}: {len(hs)} hops, with sampled 89: {c[True]}, without: {c[False]}")
# steps/ wall of 0-sample hops: is the gap one sampling interval?
z = [h for h in hops if h["exc_samples"] == 0]
w = sorted(h["exc_wall"] for h in z)
print("0-sample hops: wall gap quartiles", [round(w[int(q * (len(w) - 1))]) for q in (0, .25, .5, .75, 1)])
# excursion length in samples, by arm, as time-at-89 fraction check
# components
parent = {}
def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
for u, v, c in G["edges"]:
    ru, rv = find(u), find(v)
    if ru != rv: parent[ru] = rv
for n in G["nodes"]: find(n)
comp = collections.defaultdict(set)
for n in G["nodes"]: comp[find(n)].add(n)
chains_of_comp = collections.defaultdict(set)
for h in hops:
    chains_of_comp[find(h["u"])].add(tuple(h["chain"]))
multi = [(len(comp[c]), sorted(chs)) for c, chs in chains_of_comp.items() if len(chs) > 1]
print("multi-chain components (size, chains):")
for m in sorted(multi, reverse=True): print("  ", m)
# cycle lengths: for in-chain revisits, how far back was the node?
# (recompute from hops order per chain)
by_chain = collections.defaultdict(list)
for h in hops: by_chain[tuple(h["chain"])].append(h)
back = []
for ck, hs in by_chain.items():
    seq = [hs[0]["u"]] + [h["v"] for h in hs]
    for i, n in enumerate(seq):
        if n in seq[:i]:
            j = max(k for k in range(i) if seq[k] == n)
            back.append(i - j)
print("in-chain revisit: hops since last visit of that node:", sorted(collections.Counter(back).items()))
