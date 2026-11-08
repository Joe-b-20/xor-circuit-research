"""Generate the instance lists (JSON) for the near-miss campaign.  usage: python3 gen.py
Writes inst_a0.json (D, r alone), inst_b.json (18-pair), inst_a1.json (D singletons), inst_a2.json (D cones),
inst_c.json (A75/A76), inst_a3.json (D pairs), inst_a4.json (D large windows, any-pair, 600 s)."""
import json, os, sys, itertools
from common import *
import sat87

tidx = {t: i for i, t in enumerate(TARGETS)}
def nm(v): return ("y%d" % tidx[v]) if v in tidx else ("x%d" % (v.bit_length()-1) if v in INPUTS else "h%08x" % v)


def window(order, seeds, anypair):
    vals = sat87.values_of(order)
    W = set(seeds) if anypair else sat87.closure_remove(order, seeds)
    W = sat87.private_cone(order, W)
    K = [v for v in vals if v not in W]
    while True:
        if sat87.wiring_from_values(K) is not None:
            break
        comp = set(sat87.values_of(sat87.wiring_from_values_partial(K)))
        K = [v for v in K if v in comp]
    return frozenset(set(vals) - set(K))


def inst(family, name, vals, W, m, limit, note=""):
    K = sorted(v for v in vals if v not in W)
    assert sat87.split_closed(K)
    need = [t for t in TARGETS if t not in K]
    return {"family": family, "name": name, "K": K, "m": m, "k": len(W), "W": sorted(W),
            "targets_needed": [tidx[t] for t in need], "limit": limit, "note": note}


def dump(fn, L):
    json.dump(L, open(fn, "w"))
    print(fn, len(L), "instances; k/m:", [(x["k"], x["m"]) for x in L][:60])


# ---------------- (a) candidate D
order, missing, prof = load_deep("b87_most_exact", 87)
vals = sat87.values_of(order)
par = parents(order); users = sat87.dependents(order); dep = depth_of(order)
r = [x["actual"] for x in prof["rows"] if x["residual"]][0]
helpers = [v for v in vals if v not in TSET and v != r]
anc = []; st = [r]; seen = set()
while st:
    v = st.pop()
    for o in par.get(v, ()):
        if o in par and o not in seen:
            seen.add(o); anc.append(o); st.append(o)

# a0: r alone
dump("inst_a0.json", [inst("D", "a0:r", vals, frozenset([r]), 1, 120, "K = D minus the dead y19 representative; y19 must be one XOR of the pool")])

# a1: singletons h + r, wiring closure; any-pair variant when it is smaller
a1 = []; seenW = set()
for h in helpers:
    for ap in (False, True):
        W = window(order, [h, r], ap)
        if W in seenW:
            continue
        seenW.add(W)
        a1.append(inst("D", "a1:%s%s" % (nm(h), ":ap" if ap else ""), vals, W, len(W), 120,
                       "W = closure of {h, r}" + (" (any-pair minimal)" if ap else " (wiring closure)")))
a1.sort(key=lambda x: x["k"])
dump("inst_a1.json", [x for x in a1 if x["k"] <= 13])
a4 = [dict(x, limit=600) for x in a1 if x["k"] > 13]
dump("inst_a4.json", a4)

# a2: cones around y19
p1, p2 = par[r]
cones = {"a2:parents": [r, p1, p2]}
for p in (p1, p2):
    if p in par:
        cones["a2:cone(%s)" % nm(p)] = [r, p] + [o for o in par[p] if o in par]
cones["a2:anc1"] = [r] + [a for a in anc if dep[a] >= 2]
cones["a2:anc_all"] = [r] + anc
a2 = []
for name, seeds in cones.items():
    for ap in (False, True):
        W = window(order, seeds, ap)
        if W in seenW:
            continue
        seenW.add(W)
        a2.append(inst("D", name + (":ap" if ap else ""), vals, W, len(W), 120 if len(W) <= 13 else 600,
                       "seeds " + ",".join(nm(s) for s in seeds)))
a2.sort(key=lambda x: x["k"])
dump("inst_a2.json", a2)

# a3: pairs of helpers near y19: ancestors of r, and helpers sharing >= 3 support bits with y19 or
# feeding the outputs of bit 3 of other bytes (y3, y11, y27) -- the rotation images of y19
y19 = TARGETS[19]
def supp(v): return bin(v).count("1")
near = set(anc)
for h in helpers:
    if supp(h & y19) >= 3:
        near.add(h)
    for t in (TARGETS[3], TARGETS[11], TARGETS[27]):
        if h in par.get(t, ()):
            near.add(h)
near = sorted(near)
print("neighbourhood helpers:", len(near), [nm(h) for h in near])
a3 = []
for h1, h2 in itertools.combinations(near, 2):
    W = window(order, [h1, h2, r], True)
    if W in seenW or len(W) > 10:
        continue
    seenW.add(W)
    a3.append(inst("D", "a3:%s,%s:ap" % (nm(h1), nm(h2)), vals, W, len(W), 60, "pair, any-pair minimal closure"))
a3.sort(key=lambda x: x["k"])
dump("inst_a3.json", a3)

# ---------------- (b) 18-pair foundation
o88, K84, miss, pv, rich = foundation18()
assert sorted(tidx[v] for v in miss) == [9, 10, 18]
par88 = parents(o88)
b = [inst("P18", "b:r0", K84, frozenset(), 3, 120, "K = 18 pairs + 66 regenerated rich values")]
# seeds: rich helpers in K84 that are ancestors (within 2 levels) of y9, y10, y18 in the 88 wiring
seeds = set()
for t in miss:
    for p in par88[t]:
        if p in K84 and p not in TSET:
            seeds.add(p)
            for q in par88.get(p, ()):
                if q in K84 and q not in TSET:
                    seeds.add(q)
seeds = sorted(seeds)
print("18-pair seeds:", [nm(s) for s in seeds])
wK = sat87.wiring_from_values(K84)
seenB = set()
for n in (1, 2):
    for S in itertools.combinations(seeds, n):
        for ap in (True, False):
            W = window(wK, list(S), ap)
            if W in seenB or len(W) > 6:
                continue
            seenB.add(W)
            b.append(inst("P18", "b:" + ",".join(nm(s) for s in S) + (":ap" if ap else ""), K84, W, 3 + len(W), 120,
                          "K = 84 minus r=%d values; m = 3 + r" % len(W)))
b.sort(key=lambda x: x["k"])
dump("inst_b.json", b)

# ---------------- (c) A75 / A76
c = []
for tag, ng, m in (("b75_most_exact", 75, 12), ("b76_nested", 76, 11), ("b76_most_exact", 76, 11)):
    o, mis, pr = load_deep(tag, ng)
    v = sat87.values_of(o)
    assert len(set(v)) == ng and sat87.split_closed(v)
    c.append(inst(tag, "c:%s" % tag, v, frozenset(), m, 900, "missing outputs " + ",".join("y%d" % x for x in mis)))
dump("inst_c.json", c)
