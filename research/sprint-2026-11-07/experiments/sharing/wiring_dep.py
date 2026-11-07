"""Wiring dependence of S and delta: for the repo circuits and a subset of samples, take many random
legal wirings of the same value set and report min/max S (delta = S - (108 - G) follows).
Also: triple cone unions (min over samples) for the k=3 sub-map upper bounds, and the sharing
pattern of the shared gates (which group pairs, masks inside which supports)."""
import json
import os
import random
import sys
import statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

HERE = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(7)
res = {}

def wiring_range(vals, trials):
    Ss = []
    distinct = set()
    for _ in range(trials):
        o = lib.wiring_from_values(vals, rng)
        distinct.add(frozenset(o))
        Ss.append(lib.sharing_stats(o)["S_mult"])
    return min(Ss), max(Ss), len(distinct)

for name, path in lib.CIRC.items():
    order = lib.load_repo_circ(path)
    vals = [v for v, _, _ in order]
    lo, hi, nd = wiring_range(vals, 200)
    print(f"repo {name}: file-wiring S={lib.sharing_stats(order)['S_mult']}; over 200 random wirings S in [{lo},{hi}], {nd} distinct wirings")
    res[name] = {"S_min": lo, "S_max": hi, "distinct": nd}

samples = lib.load_samples(88)
rng.shuffle(samples)
sub = samples[:300]
mins, greedy = [], []
for smp in sub:
    o = lib.wiring_from_values(smp["values"])
    g = lib.sharing_stats(o)["S_mult"]
    lo, hi, nd = wiring_range(smp["values"], 30)
    mins.append(min(lo, g)); greedy.append(g)
c = {}
for x in mins:
    c[x] = c.get(x, 0) + 1
print(f"300 random samples: greedy S mean {st.mean(greedy):.2f}; min-over-31-wirings S: min {min(mins)} median {st.median(mins)} mean {st.mean(mins):.2f} max {max(mins)} hist {dict(sorted(c.items()))}")
print(f"   => min-wiring delta = S_min - 20: min {min(mins)-20} median {st.median(mins)-20} mean {st.mean(mins)-20:.2f}")
res["samples_min_wiring_S"] = mins

# triple unions
trip = {}
for K in [(5, 6, 7), (0, 6, 7), (0, 1, 7), (0, 1, 2), (2, 3, 4), (3, 4, 5), (0, 2, 5), (1, 3, 4)]:
    best = 10 ** 9
    for smp in samples:
        o = lib.wiring_from_values(smp["values"])
        _, cone = lib.cones(o)
        u = set()
        for g in K:
            u |= cone[g]
        best = min(best, len(u))
    for name, path in lib.CIRC.items():
        _, cone = lib.cones(lib.load_repo_circ(path))
        u = set()
        for g in K:
            u |= cone[g]
        best = min(best, len(u))
    trip[str(K)] = best
    print(f"triple {K}: min |union of cones| over all samples+repo = {best}  (sum of minima {sum(lib.M_GROUP[g] for g in K)})")
res["triple_min_union"] = trip

# sharing pattern on the repo 88: for each shared gate, its mask support, groups, depth
order = lib.load_repo_circ(lib.CIRC["88@5"])
stt = lib.sharing_stats(order)
print("\nrepo 88@5 shared gates (k>=2): mask bits | groups | inside supp of all its groups?")
inside_all = 0
for v, a, b in order:
    k = stt["k"][v]
    if k >= 2:
        gs = [g for g in range(8) if v in stt["cone"][g]]
        sup = lib.support(v)
        ins = all(set(sup) <= set(lib.group_support(g)) for g in gs)
        inside_all += ins
        tag = "y%d" % lib.TARGETS.index(v) if v in lib.TSET else ""
        print(f"  depth {stt['depth'][v]} mask {sup} groups {gs} inside={ins} {tag}")
print(f"  shared gates whose mask lies inside every sharing group's support: {inside_all} of {stt['S_cnt']}")

# across samples: fraction of shared gates with mask inside all sharing groups' supports; k>=3 masks
tot = ins_cnt = 0
k3 = {}
for smp in samples:
    o = lib.wiring_from_values(smp["values"])
    s = lib.sharing_stats(o)
    for v, _, _ in o:
        k = s["k"][v]
        if k >= 2:
            gs = [g for g in range(8) if v in s["cone"][g]]
            ins = all(set(lib.support(v)) <= set(lib.group_support(g)) for g in gs)
            tot += 1; ins_cnt += ins
            if k >= 3:
                key = (tuple(gs), tuple(lib.support(v)))
                k3[key] = k3.get(key, 0) + 1
print(f"\nall samples: shared gates {tot}, with mask inside all sharing groups' supports {ins_cnt} ({100*ins_cnt/tot:.1f}%)")
print("most common k>=3 shared gates (groups, mask bits): count")
for key, cnt in sorted(k3.items(), key=lambda x: -x[1])[:12]:
    print(f"  {key[0]} {key[1]}: {cnt}")
json.dump(res, open(os.path.join(HERE, "wiring_dep.json"), "w"))
