#!/usr/bin/env python3
"""Review check for F5: is the plateau catalogue's 'zero overlap' robust?
(a) counts by kind, members per plateau, arms; (b) depth of pre-sprint vs hunt plateaus;
(c) pairwise similarity of plateau value sets modulo byte rotation (near-duplicates);
(d) giants: are their enumerated states members of any product plateau?
Usage: f5.py HUNT_DIR"""
import json, os, sys, collections

HUNT = sys.argv[1]
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402

sp = pes_lib.make_space("mc", None)
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
P = store["plateaus"]
states = store["states"]

print(f"plateaus {len(P)}, catalogued states {len(states)} ({sum(1 for v in states.values() if v is None)} with key None)")
kinds = collections.Counter(v["kind"] for v in P.values())
print("kinds:", dict(kinds))
arms_first = collections.Counter(v["first"]["arm"] for v in P.values())
print("first seen by arm:", dict(arms_first))
members = collections.Counter(v["members_seen"] for v in P.values() if v["first"]["arm"] != "pre")
print("members_seen distribution (hunt plateaus):", dict(sorted(members.items())))
multi_arm = sum(1 for v in P.values() if len(v["arms"]) > 1)
print("plateaus seen by more than one arm:", multi_arm)
print("pre-sprint plateaus with members_seen>0:", sum(1 for v in P.values() if v["first"]["arm"] == "pre" and v["members_seen"] > 0))


def allvals(pj):
    vals = set(pj.get("core") or [])
    for fac in pj.get("factors") or []:
        for ch in fac["choices"]:
            vals |= set(ch)
    for s in pj.get("states") or []:
        vals |= set(s)
    return vals


def rep_state(pj):
    """one member: core + first choice of each factor, or the first enumerated state"""
    if pj.get("states"):
        return list(pj["states"][0])
    s = list(pj.get("core") or [])
    for fac in pj.get("factors") or []:
        s += list(fac["choices"][0])
    return s


# (b) depth
dep = collections.defaultdict(collections.Counter)
for k, v in P.items():
    pj = v["plateau"]
    try:
        st = sp.state(rep_state(pj))
        d = st.depth() if st.count() == 88 else None
    except Exception as ex:
        d = f"err:{type(ex).__name__}"
    grp = "pre" if v["first"]["arm"] == "pre" else v["first"]["arm"]
    dep[grp][d] += 1
for grp, c in sorted(dep.items()):
    print(f"depth of a representative member, {grp}: {dict(sorted(c.items(), key=lambda kv: str(kv[0])))}")

# (c) pairwise similarity modulo rotation
keys = list(P)
V = {k: allvals(P[k]["plateau"]) for k in keys}
rotV = {k: [set(sp.rot(tuple(V[k]), s)) if s else V[k] for s in sp.shifts] for k in keys}
best = {}
pairs_hi = []
for i, a in enumerate(keys):
    A = V[a]
    for b in keys[i + 1:]:
        m = 0.0
        for B in rotV[b]:
            inter = len(A & B)
            if inter == 0:
                continue
            j = inter / len(A | B)
            if j > m:
                m = j
        best[a] = max(best.get(a, 0), m)
        best[b] = max(best.get(b, 0), m)
        if m >= 0.7:
            pairs_hi.append((m, a, b))
hist = collections.Counter(round(x, 1) for x in best.values())
print("max Jaccard similarity of each plateau's value set to any other (mod rotation), histogram:",
      dict(sorted(hist.items())))
pairs_hi.sort(reverse=True)
print(f"pairs with Jaccard >= 0.7: {len(pairs_hi)}")
for m, a, b in pairs_hi[:25]:
    print(f"   {m:.2f} {a} ({P[a]['kind']},{P[a]['size']},{P[a]['first']['arm']})  {b} ({P[b]['kind']},{P[b]['size']},{P[b]['first']['arm']})")

# (d) giants / closures: membership of their states in product plateaus
prods = {k: pes_lib.Plateau.from_json(P[k]["plateau"]) for k in keys if P[k]["kind"] == "product"}
for k in keys:
    if P[k]["kind"] == "product":
        continue
    pj = P[k]["plateau"]
    sts = pj.get("states") or [rep_state(pj)]
    hits = set()
    for s in sts[:50]:
        for sh in sp.shifts:
            S = frozenset(sp.rot(tuple(s), sh) if sh else s)
            for pk, pl in prods.items():
                if pl.contains(S):
                    hits.add(pk)
    print(f"  {P[k]['kind']} {k}: {len(sts)} states stored, first {P[k]['first']['arm']}/{P[k]['first']['worker']}, "
          f"members_seen {P[k]['members_seen']}, states in product plateaus: {sorted(hits)}")
