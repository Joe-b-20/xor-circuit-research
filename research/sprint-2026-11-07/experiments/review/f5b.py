#!/usr/bin/env python3
"""Review check for F5 (part 2): cluster catalogued plateaus by value-set similarity modulo
rotation (union-find at Jaccard thresholds), count hunt plateaus with a pre-sprint neighbour,
and report the value-difference sizes of the closest pairs. Usage: f5b.py HUNT_DIR"""
import json, os, sys, collections

HUNT = sys.argv[1]
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402

sp = pes_lib.make_space("mc", None)
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
P = store["plateaus"]


def allvals(pj):
    vals = set(pj.get("core") or [])
    for fac in pj.get("factors") or []:
        for ch in fac["choices"]:
            vals |= set(ch)
    for s in pj.get("states") or []:
        vals |= set(s)
    return vals


def core(pj):
    if pj.get("core"):
        return set(pj["core"])
    sts = pj.get("states") or []
    return set.intersection(*[set(s) for s in sts]) if sts else set()


keys = list(P)
V = {k: allvals(P[k]["plateau"]) for k in keys}
C = {k: core(P[k]["plateau"]) for k in keys}
rotV = {k: [set(sp.rot(tuple(V[k]), s)) if s else V[k] for s in sp.shifts] for k in keys}
rotC = {k: [set(sp.rot(tuple(C[k]), s)) if s else C[k] for s in sp.shifts] for k in keys}
grp = {k: ("pre" if P[k]["first"]["arm"] == "pre" else "hunt") for k in keys}

pairs = []  # (jaccard, core_jaccard, a, b, |A-B|, |B-A|)
for i, a in enumerate(keys):
    A = V[a]
    CA = C[a]
    for b in keys[i + 1:]:
        best = (0.0, 0.0, 0, 0)
        for B, CB in zip(rotV[b], rotC[b]):
            inter = len(A & B)
            if inter == 0:
                continue
            j = inter / len(A | B)
            if j > best[0]:
                cj = len(CA & CB) / len(CA | CB) if (CA | CB) else 0.0
                best = (j, cj, len(A - B), len(B - A))
        if best[0] >= 0.8:
            pairs.append((best[0], best[1], a, b, best[2], best[3]))

print(f"plateaus {len(keys)}; pairs with Jaccard >= 0.8: {len(pairs)}")
diffs = collections.Counter((p[4], p[5]) for p in pairs if p[0] >= 0.9)
print("value-difference sizes (|A-B|,|B-A|) among pairs with Jaccard >= 0.9:", dict(sorted(diffs.items())))
cj = sorted(p[1] for p in pairs if p[0] >= 0.9)
print(f"core Jaccard of those pairs: min {cj[0]:.2f} median {cj[len(cj)//2]:.2f} max {cj[-1]:.2f}" if cj else "none")


def components(th):
    par = {k: k for k in keys}

    def f(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for j, _, a, b, _, _ in pairs:
        if j >= th:
            par[f(a)] = f(b)
    comp = collections.defaultdict(list)
    for k in keys:
        comp[f(k)].append(k)
    return list(comp.values())


for th in (0.95, 0.9, 0.85, 0.8):
    comps = components(th)
    hunt_only = [c for c in comps if all(grp[k] == "hunt" for k in c)]
    pre_only = [c for c in comps if all(grp[k] == "pre" for k in c)]
    mixed = [c for c in comps if len({grp[k] for k in c}) > 1]
    sizes = collections.Counter(len(c) for c in comps)
    print(f"threshold {th}: components {len(comps)} (hunt-only {len(hunt_only)}, pre-only {len(pre_only)}, mixed {len(mixed)}); "
          f"component sizes {dict(sorted(sizes.items()))}")
    if mixed:
        for c in mixed[:5]:
            print("    mixed:", [(k[:10], grp[k], P[k]['size']) for k in c])

# hunt plateaus with a pre-sprint neighbour at any threshold >= 0.8
near_pre = collections.Counter()
for j, _, a, b, _, _ in pairs:
    if grp[a] != grp[b]:
        near_pre[round(j, 2)] += 1
print("hunt-pre pairs by Jaccard (>= 0.8):", dict(sorted(near_pre.items())))

# ordering of duplicates: giant/closure seen before or after the product that contains its state
for k in keys:
    if P[k]["kind"] != "product":
        s0 = (P[k]["plateau"].get("states") or [None])[0]
        if s0 is None:
            continue
        for pk in keys:
            if P[pk]["kind"] != "product":
                continue
            pl = pes_lib.Plateau.from_json(P[pk]["plateau"])
            for sh in sp.shifts:
                S = frozenset(sp.rot(tuple(s0), sh) if sh else s0)
                if pl.contains(S):
                    print(f"  duplicate: {k} (first {P[k]['first']['arm']} wall {P[k]['first']['wall']:.0f}) state lies in "
                          f"{pk} (first {P[pk]['first']['arm']} wall {P[pk]['first']['wall']:.0f}, size {P[pk]['size']}, members {P[pk]['members_seen']})")
                    break
